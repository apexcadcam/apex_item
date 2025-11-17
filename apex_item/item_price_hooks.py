# -*- coding: utf-8 -*-
# Item Price Hooks - Auto-calculate available quantity

import frappe
from functools import lru_cache
from typing import Iterable, Optional

from frappe.utils import flt


def set_stock_fields(doc, method=None):
	"""Calculate and set available/reserved quantities for the item price"""
	if not doc.item_code:
		_apply_snapshot_to_doc(doc, _empty_snapshot())
		return
	warehouse = getattr(doc, "stock_warehouse", None) or _get_item_default_warehouse(doc.item_code)
	if warehouse and not getattr(doc, "stock_warehouse", None):
		doc.stock_warehouse = warehouse

	snapshot = _get_stock_snapshot(doc.item_code, warehouse)
	_apply_snapshot_to_doc(doc, snapshot)


def update_available_qty_on_save(doc, method=None):
	"""
	Update available/reserved fields in database after save
	"""
	if doc.item_code:
		set_stock_fields(doc, method)
		_update_item_price_row(doc.name, doc)


def update_item_prices_for_item(item_code, target_warehouse=None):
	"""Refresh Item Price rows for a specific item code (optionally filtered by warehouse)."""
	if not item_code:
		return

	item_prices = frappe.db.get_all(
		"Item Price",
		filters={"item_code": item_code},
		fields=["name", "stock_warehouse"],
	)
	if not item_prices:
		return

	# Defer resolving fallback warehouse until needed to avoid errors on sites
	# where Item.default_warehouse column may not exist.
	fallback_warehouse = None
	snapshots: dict[str | None, dict] = {}

	for row in item_prices:
		# Resolve fallback lazily only if the row has no explicit warehouse
		if not row.stock_warehouse and fallback_warehouse is None:
			try:
				fallback_warehouse = _get_item_default_warehouse(item_code)
			except Exception:
				# If unavailable (e.g. missing column), keep None and proceed with all-warehouses snapshot
				fallback_warehouse = None

		row_warehouse = row.stock_warehouse or fallback_warehouse
		if target_warehouse and row_warehouse and row_warehouse != target_warehouse:
			continue

		snapshot_key = row_warehouse or "__all__"
		if snapshot_key not in snapshots:
			snapshots[snapshot_key] = _get_stock_snapshot(item_code, row_warehouse)

		extra_values = {}
		if not row.stock_warehouse and row_warehouse:
			extra_values["stock_warehouse"] = row_warehouse

		_update_item_price_row(row.name, snapshots[snapshot_key], extra_values)


def update_item_price_from_bin(doc, method=None):
	"""Doc event helper to refresh Item Price whenever Bin values change."""
	item_code = getattr(doc, "item_code", None)
	if not item_code:
		return
	_enqueue_item_price_refresh(
		[{"item_code": item_code, "warehouse": getattr(doc, "warehouse", None)}]
	)


def update_item_prices_from_stock_ledger(doc, method=None):
	item_code = getattr(doc, "item_code", None)
	if not item_code:
		return
	_enqueue_item_price_refresh(
		[{"item_code": item_code, "warehouse": getattr(doc, "warehouse", None)}]
	)


def update_item_prices_from_sales_order(doc, method=None):
	_enqueue_item_price_refresh(_collect_item_warehouse_pairs(doc, "items"))


def update_item_prices_from_purchase_order(doc, method=None):
	_enqueue_item_price_refresh(_collect_item_warehouse_pairs(doc, "items"))


def update_item_prices_from_purchase_receipt(doc, method=None):
	_enqueue_item_price_refresh(_collect_item_warehouse_pairs(doc, "items"))


def _get_stock_snapshot(item_code, warehouse=None):
	snapshot = _empty_snapshot()
	if not item_code:
		return snapshot

	try:
		bin_conditions = ["item_code = %s"]
		bin_params = [item_code]
		if warehouse:
			bin_conditions.append("warehouse = %s")
			bin_params.append(warehouse)

		stock_data = frappe.db.sql(
			"""
			SELECT 
				SUM(actual_qty) as actual_qty,
				SUM(reserved_qty + reserved_qty_for_production + reserved_qty_for_sub_contract) as reserved_qty
			FROM `tabBin`
			WHERE {conditions}
		""".format(
				conditions=" AND ".join(bin_conditions)
			),
			tuple(bin_params),
			as_dict=True,
		)

		waiting_conditions = [
			"POI.item_code = %s",
			"PO.docstatus = 1",
			"POI.qty > POI.received_qty",
		]
		waiting_params = [item_code]
		if warehouse:
			waiting_conditions.append("POI.warehouse = %s")
			waiting_params.append(warehouse)

		waiting_data = frappe.db.sql(
			"""
			SELECT SUM(POI.qty - POI.received_qty) AS waiting
			FROM `tabPurchase Order Item` POI
			INNER JOIN `tabPurchase Order` PO ON PO.name = POI.parent
			WHERE {conditions}
		""".format(
				conditions=" AND ".join(waiting_conditions)
			),
			tuple(waiting_params),
			as_dict=True,
		)

		item_data = frappe.db.get_value(
			"Item",
			item_code,
			["item_group", "image", "website_image", "thumbnail"],
			as_dict=True,
		)

		if stock_data and stock_data[0]:
			actual = flt(stock_data[0].get("actual_qty", 0))
			reserved = flt(stock_data[0].get("reserved_qty", 0))
			available = actual - reserved
		else:
			actual = reserved = available = 0

		waiting = flt(waiting_data[0].get("waiting", 0)) if waiting_data and waiting_data[0] else 0

		item_group = item_data.get("item_group") if item_data else None
		item_image = None
		if item_data:
			item_image = item_data.get("image") or item_data.get("website_image") or item_data.get("thumbnail")

		snapshot.update(
			{
				"actual_qty": actual,
				"available_qty": available,
				"reserved_qty": reserved,
				"waiting_qty": waiting,
				"item_group": item_group,
				"item_image": item_image,
			}
		)
	except Exception as e:
		frappe.log_error(
			f"Error calculating stock fields for {item_code}: {str(e)}",
			"Item Price - Stock Calculation",
		)

	return snapshot


def _apply_snapshot_to_doc(doc, snapshot):
	doc.actual_qty = snapshot["actual_qty"]
	doc.available_qty = snapshot["available_qty"]
	doc.reserved_qty = snapshot["reserved_qty"]
	doc.waiting_qty = snapshot["waiting_qty"]
	doc.item_group = snapshot["item_group"]
	doc.item_image = snapshot["item_image"]


def _update_item_price_row(name, doc_or_snapshot, extra_values=None):
	if isinstance(doc_or_snapshot, dict):
		payload = doc_or_snapshot
	else:
		payload = {
			"available_qty": getattr(doc_or_snapshot, "available_qty", 0),
			"reserved_qty": getattr(doc_or_snapshot, "reserved_qty", 0),
			"actual_qty": getattr(doc_or_snapshot, "actual_qty", 0),
			"waiting_qty": getattr(doc_or_snapshot, "waiting_qty", 0),
			"item_group": getattr(doc_or_snapshot, "item_group", None),
			"item_image": getattr(doc_or_snapshot, "item_image", None),
		}

	if extra_values:
		payload.update(extra_values)

	frappe.db.set_value(
		"Item Price",
		name,
		payload,
		update_modified=False,
	)


def _empty_snapshot():
	return {
		"actual_qty": 0,
		"available_qty": 0,
		"reserved_qty": 0,
		"waiting_qty": 0,
		"item_group": None,
		"item_image": None,
	}


@lru_cache(maxsize=None)
def _get_item_default_warehouse(item_code):
	if not item_code:
		return None

	# Some sites may not have Item.default_warehouse column; guard defensively
	try:
		if hasattr(frappe.db, "has_column") and frappe.db.has_column("Item", "default_warehouse"):
			warehouse = frappe.db.get_value("Item", item_code, "default_warehouse")
		else:
			warehouse = None
	except Exception:
		warehouse = None

	if warehouse:
		return warehouse

	return frappe.db.get_value(
		"Item Default",
		{"parent": item_code},
		"default_warehouse",
		order_by="idx asc",
	)


def _collect_item_warehouse_pairs(doc, child_table):
	item_rows = getattr(doc, child_table, []) or []
	pairs: list[dict] = []
	for row in item_rows:
		if not row:
			continue

		if isinstance(row, dict):
			item_code = row.get("item_code")
			warehouse = row.get("warehouse") or row.get("reserved_warehouse") or row.get("warehouse_for_delivery")
		else:
			item_code = getattr(row, "item_code", None)
			warehouse = (
				getattr(row, "warehouse", None)
				or getattr(row, "reserved_warehouse", None)
				or getattr(row, "warehouse_for_delivery", None)
			)

		if not item_code:
			continue

		pairs.append({"item_code": item_code, "warehouse": warehouse})
	return pairs


def refresh_item_prices_for_items(item_pairs: Optional[Iterable[dict]] = None):
	if not item_pairs:
		return

	for item_code, warehouse in _deduplicate_pairs(item_pairs):
		update_item_prices_for_item(item_code, warehouse)


def _enqueue_item_price_refresh(item_pairs):
	normalized = list(_deduplicate_pairs(item_pairs or []))
	if not normalized:
		return

	if frappe.flags.in_test or frappe.flags.in_install:
		for pair in normalized:
			update_item_prices_for_item(*pair)
		return

	frappe.enqueue(
		"apex_item.item_price_hooks.refresh_item_prices_for_items",
		item_pairs=[{"item_code": item_code, "warehouse": warehouse} for item_code, warehouse in normalized],
		queue="short",
		timeout=300,
		now=False,
	)


def _deduplicate_pairs(item_pairs: Iterable[dict | tuple | list]):
	seen = set()
	for pair in item_pairs:
		if not pair:
			continue
		if isinstance(pair, (tuple, list)) and len(pair) >= 2:
			item_code, warehouse = pair[0], pair[1]
		elif isinstance(pair, dict):
			item_code = pair.get("item_code")
			warehouse = pair.get("warehouse")
		else:
			continue

		if not item_code:
			continue

		key = (item_code, warehouse)
		if key in seen:
			continue
		seen.add(key)
		yield key


def _iter_recent_bin_changes(minutes: int = 15, limit: int = 500):
	"""
	Yield (item_code, warehouse) pairs for Bins modified recently.
	Used by the scheduler to reconcile Item Price quantities in case
	background jobs were not running at the time of earlier events.
	"""
	try:
		# use fallback to limit to recent changes without heavy scans
		rows = frappe.db.sql(
			"""
			SELECT item_code, warehouse
			FROM `tabBin`
			WHERE modified >= NOW() - INTERVAL %s MINUTE
			ORDER BY modified DESC
			LIMIT %s
		""",
			(minutes, limit),
			as_dict=True,
		)
	except Exception:
		# If DB doesn't support INTERVAL in this dialect, fallback to latest rows
		rows = frappe.db.sql(
			"""
			SELECT item_code, warehouse
			FROM `tabBin`
			ORDER BY modified DESC
			LIMIT %s
		""",
			(limit,),
			as_dict=True,
		)

	for r in rows or []:
		item_code = r.get("item_code")
		warehouse = r.get("warehouse")
		if item_code:
			yield {"item_code": item_code, "warehouse": warehouse}


def scheduled_reconcile_item_price():
	"""
	Scheduled task: reconcile Item Price stock fields for items
	with recently modified Bin rows. This provides a self-healing
	mechanism if workers were down when events fired.
	
	Safe to call even if scheduler/workers are not running - will
	simply do nothing if database is not available.
	"""
	try:
		# Ensure we have a database connection
		if not frappe.db:
			return
		
		item_pairs = list(_iter_recent_bin_changes())
		if not item_pairs:
			return
		refresh_item_prices_for_items(item_pairs)
	except Exception as e:
		# Log but don't fail - scheduler tasks should be resilient
		frappe.log_error(
			f"Error in scheduled_reconcile_item_price: {str(e)}",
			"Apex Item - Scheduled Reconcile Error"
		)
		# Don't re-raise - allow scheduler to continue with other tasks


@frappe.whitelist()
def refresh_item_price(name: str) -> dict:
	"""
	Refresh a single Item Price row's stock fields from tabBin.
	Returns the updated snapshot for UI usage.
	"""
	if not name:
		frappe.throw("Missing Item Price name")
	doc = frappe.get_doc("Item Price", name)
	if not getattr(doc, "item_code", None):
		frappe.throw("Item Price has no Item Code")
	# Determine warehouse scope from row or item defaults
	warehouse = getattr(doc, "stock_warehouse", None) or _get_item_default_warehouse(doc.item_code)
	snapshot = _get_stock_snapshot(doc.item_code, warehouse)
	# Apply to doc and persist
	_apply_snapshot_to_doc(doc, snapshot)
	_update_item_price_row(doc.name, doc, {"stock_warehouse": warehouse} if warehouse and not getattr(doc, "stock_warehouse", None) else None)
	return {
		"actual_qty": snapshot.get("actual_qty", 0),
		"reserved_qty": snapshot.get("reserved_qty", 0),
		"available_qty": snapshot.get("available_qty", 0),
		"waiting_qty": snapshot.get("waiting_qty", 0),
		"stock_warehouse": warehouse,
	}


@frappe.whitelist()
def refresh_item_prices(names: list[str] | str) -> int:
	"""
	Bulk refresh for multiple Item Price rows by name.
	Returns the count of rows updated.
	"""
	if not names:
		return 0
	if isinstance(names, str):
		try:
			# accept JSON or comma-separated
			import json
			names = json.loads(names)
		except Exception:
			names = [n.strip() for n in names.split(",") if n.strip()]

	updated = 0
	for name in names:
		try:
			refresh_item_price(name)
			updated += 1
		except Exception:
			# continue with others; log for debugging
			frappe.log_error(f"Failed to refresh Item Price {name}", "Apex Item: refresh_item_prices")
	frappe.db.commit()
	return updated


@frappe.whitelist()
def refresh_item_prices_by_filters(filters=None, limit: int = 1000) -> int:
	"""
	Refresh Item Price rows matching list filters (current view).
	- filters: can be a JSON string (from list view) or a python structure.
	- limit: safety cap to avoid refreshing an extremely large dataset at once.
	Returns the number of rows updated.
	"""
	try:
		parsed = frappe.parse_json(filters) if isinstance(filters, str) else (filters or [])
	except Exception:
		parsed = []

	# Get matching names within limit
	names = frappe.get_all(
		"Item Price",
		filters=parsed or None,
		fields=["name"],
		limit_page_length=limit,
		order_by="modified desc",
	)
	name_list = [r["name"] for r in names]
	return refresh_item_prices(name_list)

