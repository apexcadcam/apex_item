# -*- coding: utf-8 -*-
"""Apex Item API Methods"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from hashlib import md5

import frappe
from frappe import _
from frappe.utils import cint  # type: ignore

from apex_item.item_price_config import (
	get_allowed_fieldnames,
	get_default_card_config,
	get_field_definition,
)
from apex_item.item_price_hooks import set_stock_fields
from apex_item.item_foreign_purchase import get_item_foreign_purchase_info

_CARD_CONFIG_CACHE_KEY = "apex_item:item_price_card_config"
_EXCLUDED_CARD_FIELDS = {"item_name"}
_PRIMARY_PRICE_FIELD = "price_list_rate"


@frappe.whitelist()
def get_item_price_card_config(force: bool = False) -> Dict[str, Any]:
	"""Return the Item Price mobile card configuration, using Redis cache when possible."""

	if not force:
		cached = _get_cached_item_price_card_config()
		if cached:
			return cached

	config = _build_item_price_card_config()
	_cache_item_price_card_config(config)
	return config


def clear_item_price_card_config_cache() -> None:
	"""Remove the cached Item Price card configuration."""
	try:
		cache = frappe.cache()
		cache.delete_key(_CARD_CONFIG_CACHE_KEY)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Apex Item: Clear Card Config Cache")


def _get_cached_item_price_card_config() -> Optional[Dict[str, Any]]:
	cache = frappe.cache()
	cached = cache.hget(_CARD_CONFIG_CACHE_KEY, _get_cache_field_key())

	if not cached:
		return None

	try:
		return frappe.parse_json(cached)
	except Exception:
		# Corrupted cache entry, drop it and rebuild next time
		cache.hdel(_CARD_CONFIG_CACHE_KEY, frappe.local.site)
		return None


def _cache_item_price_card_config(config: Dict[str, Any]) -> None:
	cache = frappe.cache()
	cache.hset(_CARD_CONFIG_CACHE_KEY, _get_cache_field_key(), frappe.as_json(config))


def _build_item_price_card_config() -> Dict[str, Any]:
	default_config = get_default_card_config()

	show_item_image = default_config.get("show_item_image", 0)
	empty_state_text = default_config.get("empty_state_text")
	doc = None

	if frappe.db.exists("DocType", "Item Price Card Setting"):
		doc = frappe.get_single("Item Price Card Setting")
		show_item_image = int(doc.show_item_image or 0)
		empty_state_text = doc.empty_state_text or empty_state_text

	fields = _get_fields_from_list_view_settings()

	if not fields and doc:
		allowed = set(get_allowed_fieldnames())
		for row in doc.card_fields:
			if not row.fieldname or row.fieldname not in allowed:
				continue

			field_dict = _make_field_dict(row.fieldname, row)
			if field_dict:
				fields.append(field_dict)

	if not fields:
		fields = default_config.get("fields", [])

	return {
		"show_item_image": show_item_image,
		"empty_state_text": empty_state_text,
		"fields": fields,
	}


def _make_field_dict(fieldname: str, row: Any = None) -> Optional[Dict[str, Any]]:
	definition = get_field_definition(fieldname)
	if not definition:
		return None

	label = (row.label if row and row.label else definition.get("label")) or definition.get("label")
	css_class = (row.css_class if row and row.css_class else definition.get("css_class")) or ""

	hide_if_zero = (
		int(row.hide_if_zero)
		if row and row.hide_if_zero is not None
		else int(definition.get("hide_if_zero", 0))
	)

	is_full_width = int(getattr(row, "is_full_width", 0) or 0)

	return {
		"fieldname": fieldname,
		"label": label,
		"css_class": css_class,
		"is_full_width": is_full_width,
		"hide_if_zero": hide_if_zero,
	}


@frappe.whitelist()
def update_all_item_price_qty():
	"""Update available_qty for all Item Prices"""

	frappe.only_for("System Manager")

	item_prices = frappe.db.sql(
		"""
			SELECT name
			FROM `tabItem Price`
			WHERE item_code IS NOT NULL
		""",
		as_dict=True,
	)

	updated = 0
	item_price_columns = frappe.db.get_table_columns("Item Price")
	include_item_image = "item_image" in item_price_columns

	for ip in item_prices:
		try:
			item_price_doc = frappe.get_doc("Item Price", ip.name)
			set_stock_fields(item_price_doc)

			values = {
				"available_qty": item_price_doc.available_qty,
				"reserved_qty": item_price_doc.reserved_qty,
				"actual_qty": item_price_doc.actual_qty,
				"waiting_qty": item_price_doc.waiting_qty,
				"item_group": item_price_doc.item_group,
				"stock_warehouse": item_price_doc.stock_warehouse,
			}

			if include_item_image:
				values["item_image"] = item_price_doc.item_image

			frappe.db.set_value(
				"Item Price",
				ip.name,
				values,
				update_modified=False,
			)

			updated += 1

			if updated % 50 == 0:
				frappe.db.commit()
				frappe.publish_realtime(
					"progress",
					{"progress": updated, "total": len(item_prices)},
					user=frappe.session.user,
				)

		except Exception as exc:
			frappe.log_error(f"Error updating {ip.name}: {str(exc)}", "Update Item Price Qty")

	frappe.db.commit()

	return {
		"success": True,
		"updated": updated,
		"total": len(item_prices),
		"message": f"✓ Updated {updated} Item Prices successfully!",
	}


@frappe.whitelist()
def update_all_items_foreign_purchase_info():
	"""
	تحديث معلومات آخر شراء بالعملة الأجنبية لجميع الأصناف.
	
	هذه الدالة تحدث حقول:
	- item_foreign_purchase_rate
	- item_foreign_purchase_currency
	- custom_item_foreign_purchase_date
	- item_foreign_purchase_voucher_type
	- item_foreign_purchase_voucher_no
	- item_foreign_purchase_supplier
	- item_foreign_purchase_applicable_charges
	
	Returns:
		dict: {
			"success": bool,
			"updated": int,
			"total": int,
			"message": str
		}
	"""
	frappe.only_for("System Manager")
	
	# جلب جميع الأصناف التي لها وثائق شراء
	items = frappe.db.sql("""
		SELECT DISTINCT item_code
		FROM (
			SELECT DISTINCT poi.item_code
			FROM `tabPurchase Order Item` poi
			INNER JOIN `tabPurchase Order` po ON poi.parent = po.name
			WHERE po.docstatus = 1
			UNION
			SELECT DISTINCT pri.item_code
			FROM `tabPurchase Receipt Item` pri
			INNER JOIN `tabPurchase Receipt` pr ON pri.parent = pr.name
			WHERE pr.docstatus = 1
			UNION
			SELECT DISTINCT pii.item_code
			FROM `tabPurchase Invoice Item` pii
			INNER JOIN `tabPurchase Invoice` pi ON pii.parent = pi.name
			WHERE pi.docstatus = 1
		) AS all_items
		WHERE item_code IS NOT NULL
		ORDER BY item_code
	""", as_dict=True)
	
	updated = 0
	failed = 0
	total = len(items)
	
	print(f"\n🔄 تحديث {total} صنف...")
	
	for idx, item in enumerate(items, 1):
		item_code = item.item_code
		
		try:
			purchase_info = get_item_foreign_purchase_info(item_code)
			
			if purchase_info:
				frappe.db.set_value(
					"Item",
					item_code,
					{
						"item_foreign_purchase_rate": purchase_info.get("rate"),
						"item_foreign_purchase_currency": purchase_info.get("currency"),
						"custom_item_foreign_purchase_date": purchase_info.get("purchase_date"),
						"item_foreign_purchase_voucher_type": purchase_info.get("voucher_type"),
						"item_foreign_purchase_voucher_no": purchase_info.get("voucher_no"),
						"item_foreign_purchase_supplier": purchase_info.get("supplier"),
						"item_foreign_purchase_applicable_charges": purchase_info.get("applicable_charges"),
						"item_foreign_purchase_lcv": purchase_info.get("lcv_name")
					},
					update_modified=False
				)
				updated += 1
			else:
				# Clear values if no purchase info found
				frappe.db.set_value(
					"Item",
					item_code,
					{
						"item_foreign_purchase_rate": 0,
						"item_foreign_purchase_currency": None,
						"custom_item_foreign_purchase_date": None,
						"item_foreign_purchase_voucher_type": None,
						"item_foreign_purchase_voucher_no": None,
						"item_foreign_purchase_supplier": None,
						"item_foreign_purchase_applicable_charges": 0,
						"item_foreign_purchase_lcv": None
					},
					update_modified=False
				)
				updated += 1
			
			# Commit كل 50 صنف لتجنب timeout
			if updated % 50 == 0:
				frappe.db.commit()
				frappe.publish_realtime(
					"progress",
					{"progress": updated, "total": total},
					user=frappe.session.user,
				)
				print(f"  ✓ تم تحديث {updated}/{total} صنف...")
		
		except Exception as exc:
			failed += 1
			frappe.log_error(
				f"Error updating {item_code}: {str(exc)}\n{frappe.get_traceback()}",
				"Apex Item - Update All Items Foreign Purchase Info"
			)
	
	frappe.db.commit()
	
	return {
		"success": True,
		"updated": updated,
		"failed": failed,
		"total": total,
		"message": f"✓ تم تحديث {updated} صنف بنجاح! ({failed} فشل)",
	}


@frappe.whitelist()
def get_item_price_card_setting_debug() -> Dict[str, Any]:
	"""Return the raw Item Price Card Setting document for debugging purposes."""
	try:
		doc = frappe.get_doc("Item Price Card Setting", "Item Price Card Setting")
	except frappe.DoesNotExistError:
		return {}

	result: Dict[str, Any] = doc.as_dict()
	if "card_fields" in result:
		result["card_fields"] = [row.as_dict() for row in doc.card_fields]
	return result


@frappe.whitelist()
def ensure_item_price_card_setting() -> Dict[str, Any]:
	"""Ensure the Item Price Card Setting document exists and is populated with defaults."""
	from apex_item.install import setup_item_price_card_setting

	setup_item_price_card_setting()
	frappe.db.commit()
	return get_item_price_card_setting_debug()


@frappe.whitelist()
def reset_item_price_card_setting() -> Dict[str, Any]:
	"""Forcefully recreate the Item Price Card Setting document with default configuration."""
	default_config = get_default_card_config()

	frappe.db.sql("DELETE FROM `tabSingles` WHERE doctype = %s", "Item Price Card Setting")
	frappe.db.sql("DELETE FROM `tabItem Price Card Field` WHERE parent = %s", "Item Price Card Setting")

	now = frappe.utils.now()
	user = frappe.session.user if frappe.session else "Administrator"

	singles_values = [
		("Item Price Card Setting", "name", "Item Price Card Setting"),
		("Item Price Card Setting", "creation", now),
		("Item Price Card Setting", "modified", now),
		("Item Price Card Setting", "owner", user),
		("Item Price Card Setting", "modified_by", user),
		("Item Price Card Setting", "show_item_image", int(default_config.get("show_item_image", 0))),
		("Item Price Card Setting", "empty_state_text", default_config.get("empty_state_text") or ""),
	]

	for single in singles_values:
		frappe.db.sql(
			"""
			INSERT INTO `tabSingles` (doctype, field, value)
			VALUES (%s, %s, %s)
			ON DUPLICATE KEY UPDATE value = VALUES(value)
			""",
			single,
		)

	for idx, field in enumerate(default_config.get("fields", []), start=1):
		frappe.db.sql(
			"""
			INSERT INTO `tabItem Price Card Field`
			(name, creation, modified, owner, modified_by, parent, parenttype, parentfield, idx, fieldname, label, css_class, is_full_width, hide_if_zero)
			VALUES
			(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
			""",
			(
				frappe.generate_hash(length=12),
				now,
				now,
				user,
				user,
				"Item Price Card Setting",
				"Item Price Card Setting",
				"card_fields",
				idx,
				field.get("fieldname"),
				field.get("label"),
				field.get("css_class"),
				int(field.get("is_full_width", 0)),
				int(field.get("hide_if_zero", 0)),
			),
		)

	frappe.db.commit()

	return get_item_price_card_setting_debug()


def _get_cache_field_key() -> str:
	user = getattr(frappe.session, "user", None) or "Guest"
	signature = _get_settings_signature()
	return f"{frappe.local.site}:{user}:{signature}"


def _get_fields_from_list_view_settings() -> List[Dict[str, Any]]:
	settings = frappe.db.get_value(
		"List View Settings",
		"Item Price",
		["fields", "total_fields"],
		as_dict=True,
	)

	if not settings:
		return []

	allowed = set(get_allowed_fieldnames())
	fields_config: List[Dict[str, Any]] = []
	seen: set[str] = set()

	try:
		raw_fields = frappe.parse_json(settings.get("fields") or "[]")
	except Exception:
		raw_fields = []

	limit = cint(settings.get("total_fields") or 6)
	if limit <= 0:
		limit = 6
	limit = min(limit, 6)

	for entry in raw_fields:
		fieldname = (entry.get("fieldname") or "").strip()
		if not fieldname or fieldname == "status_field":
			continue
		if fieldname not in allowed:
			continue
		if fieldname in _EXCLUDED_CARD_FIELDS:
			continue
		if fieldname in seen:
			continue

		row = frappe._dict(
			{
				"label": entry.get("label"),
				"css_class": "",
				"hide_if_zero": None,
				"is_full_width": 0,
			}
		)
		field_dict = _make_field_dict(fieldname, row)
		if not field_dict:
			continue

		fields_config.append(field_dict)
		seen.add(fieldname)

		if len(fields_config) >= limit:
			break

	if len(fields_config) < limit:
		default_fields = get_default_card_config().get("fields", [])
		for fallback in default_fields:
			fieldname = fallback.get("fieldname")
			if not fieldname or fieldname not in allowed:
				continue
			if fieldname in _EXCLUDED_CARD_FIELDS or fieldname in seen:
				continue

			field_dict = _make_field_dict(fieldname, frappe._dict(fallback))
			if not field_dict:
				continue

			fields_config.append(field_dict)
			seen.add(fieldname)

			if len(fields_config) >= limit:
				break

	fields_config, seen = _ensure_primary_field_first(fields_config, seen, limit)

	# Ensure waiting_qty behaves consistently but keep the current order preference
	if "waiting_qty" in allowed:
		waiting_row = frappe._dict({"label": None, "css_class": "", "hide_if_zero": 1, "is_full_width": 1})
		if "waiting_qty" in seen:
			for field in fields_config:
				if field.get("fieldname") == "waiting_qty":
					field["is_full_width"] = 1
					field["hide_if_zero"] = 1
					break
		else:
			field_dict = _make_field_dict("waiting_qty", waiting_row)
			if field_dict:
				field_dict["is_full_width"] = 1
				field_dict["hide_if_zero"] = 1
				fields_config.append(field_dict)
				seen.add("waiting_qty")

	return fields_config


def _ensure_primary_field_first(
	fields_config: List[Dict[str, Any]], seen: set[str], limit: int
) -> tuple[List[Dict[str, Any]], set[str]]:
	price_fieldname = _PRIMARY_PRICE_FIELD
	if not price_fieldname:
		return fields_config, seen

	price_index = next(
		(idx for idx, field in enumerate(fields_config) if field.get("fieldname") == price_fieldname),
		None,
	)

	if price_index is not None:
		if price_index != 0:
			price_field = fields_config.pop(price_index)
			fields_config.insert(0, price_field)
		return fields_config, seen

	default_price_row = None
	for fallback in get_default_card_config().get("fields", []):
		if fallback.get("fieldname") == price_fieldname:
			default_price_row = frappe._dict(fallback)
			break

	if not default_price_row:
		return fields_config, seen

	price_field = _make_field_dict(price_fieldname, default_price_row)
	if not price_field:
		return fields_config, seen

	fields_config.insert(0, price_field)
	seen.add(price_fieldname)

	while limit > 0 and len(fields_config) > limit:
		removed = fields_config.pop()
		removed_fieldname = removed.get("fieldname")
		if removed_fieldname:
			seen.discard(removed_fieldname)

	return fields_config, seen


def _get_settings_signature() -> str:
	parts: List[str] = []

	settings = frappe.db.get_value(
		"List View Settings",
		"Item Price",
		["modified", "fields"],
		as_dict=True,
	)
	if settings:
		parts.append(str(settings.get("modified") or ""))
		parts.append(settings.get("fields") or "")

	card_modified = frappe.db.get_value(
		"Singles",
		{"doctype": "Item Price Card Setting", "field": "modified"},
		"value",
		order_by=None,
	)
	if card_modified:
		parts.append(str(card_modified))

	if not parts:
		return "default"

	payload = "|".join(parts)
	return md5(payload.encode("utf-8")).hexdigest()

