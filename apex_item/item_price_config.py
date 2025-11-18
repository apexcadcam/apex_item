from __future__ import annotations

from copy import deepcopy
from typing import Dict, List

import frappe
from frappe import _

_FIELD_DEFINITIONS: Dict[str, Dict[str, object]] = {
	"price_list_rate": {
		"label": "Price",
		"css_class": "price",
		"hide_if_zero": 0,
	},
	"currency": {
		"label": "Currency",
		"css_class": "info",
		"hide_if_zero": 0,
	},
	"available_qty": {
		"label": "Available",
		"css_class": "available",
		"hide_if_zero": 0,
	},
	"actual_qty": {
		"label": "Actual",
		"css_class": "actual",
		"hide_if_zero": 0,
	},
	"reserved_qty": {
		"label": "Reserved",
		"css_class": "reserved",
		"hide_if_zero": 0,
	},
	"waiting_qty": {
		"label": "Waiting (PO)",
		"css_class": "waiting",
		"hide_if_zero": 1,
	},
	"brand": {
		"label": "Brand",
		"css_class": "info",
		"hide_if_zero": 0,
	},
	"item_group": {
		"label": "Group",
		"css_class": "info",
		"hide_if_zero": 0,
	},
	"item_code": {
		"label": "Item Code",
		"css_class": "code",
		"hide_if_zero": 0,
	},
	"item_name": {
		"label": "Item Name",
		"css_class": "name",
		"hide_if_zero": 0,
	},
	"uom": {
		"label": "UOM",
		"css_class": "info",
		"hide_if_zero": 0,
	},
	"stock_warehouse": {
		"label": "Warehouse",
		"css_class": "info",
		"hide_if_zero": 0,
	},
}


def get_allowed_fieldnames() -> List[str]:
	"""Return the list of fieldnames that can be displayed inside the mobile card."""
	return list(_FIELD_DEFINITIONS.keys())


def get_field_definition(fieldname: str) -> Dict[str, object]:
	"""Return the field definition with translated label."""
	definition = _FIELD_DEFINITIONS.get(fieldname)
	if not definition:
		return {}

	translated = deepcopy(definition)
	translated["label"] = _(definition["label"])
	return translated


def get_default_card_fields() -> List[Dict[str, object]]:
	"""Return the default ordered list of card field configurations."""
	fields: List[Dict[str, object]] = []

	_DEFAULT_FIELD_ORDER: List[str] = [
		"price_list_rate",
		"available_qty",
		"actual_qty",
		"reserved_qty",
		"brand",
		"item_group",
		"waiting_qty",
	]

	for fieldname in _DEFAULT_FIELD_ORDER:
		definition = get_field_definition(fieldname)
		if not definition:
			continue

		fields.append(
			{
				"fieldname": fieldname,
				"label": definition.get("label"),
				"css_class": definition.get("css_class"),
				"is_full_width": 1 if fieldname == "waiting_qty" else 0,
				"hide_if_zero": definition.get("hide_if_zero", 0),
			}
		)

	return fields


def get_default_card_config() -> Dict[str, object]:
	"""Return the default configuration dictionary for the mobile card."""
	return {
		"show_item_image": 0,
		"empty_state_text": _("لا توجد أصناف مطابقة"),
		"fields": get_default_card_fields(),
	}

