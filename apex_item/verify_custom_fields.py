"""
Verify Custom Fields Installation
==================================

This script verifies that all required custom fields are installed
on the current site. Run this after installing apex_item to ensure
all customizations are properly applied.

Usage:
    bench --site your-site execute apex_item.verify_custom_fields.verify_fields
"""

import frappe


def verify_fields():
	"""Verify all custom fields are installed"""
	
	required_fields = {
		'Item': [
			'margin_profit_percent',
			'expense_calculation_method',
			'expense_percentage',
			'sales_price_recommended',
			'item_foreign_purchase_rate',
			'item_foreign_purchase_currency',
			'item_foreign_purchase_applicable_charges',
			'item_foreign_purchase_section',
			'item_foreign_purchase_column_break',
			'item_foreign_purchase_supplier',
			'item_foreign_purchase_voucher_type',
			'item_foreign_purchase_voucher_no',
			'item_foreign_purchase_lcv',
			'custom_item_foreign_purchase_date',
		],
		'Item Price': [
			'actual_qty',
			'available_qty',
			'reserved_qty',
			'waiting_qty',
			'stock_warehouse',
			'item_group',
			'item_image',
		]
	}
	
	print("=" * 70)
	print("APEX ITEM - CUSTOM FIELDS VERIFICATION")
	print("=" * 70)
	
	all_ok = True
	total_checked = 0
	total_missing = 0
	
	for doctype, fields in required_fields.items():
		print(f"\n{doctype} ({len(fields)} fields):")
		meta = frappe.get_meta(doctype)
		
		for fname in fields:
			total_checked += 1
			field = meta.get_field(fname)
			if field:
				print(f"  ✓ {fname}")
			else:
				print(f"  ✗ {fname} - MISSING!")
				all_ok = False
				total_missing += 1
	
	print("\n" + "=" * 70)
	print(f"Total Fields Checked: {total_checked}")
	print(f"Missing Fields: {total_missing}")
	print("=" * 70)
	
	if all_ok:
		print("\n✅ ALL FIELDS VERIFIED SUCCESSFULLY")
		print("apex_item is properly installed!")
	else:
		print("\n❌ SOME FIELDS ARE MISSING")
		print("\nTo fix, run:")
		print("  bench --site {site} execute apex_item.fix_missing_fields.fix_missing_fields")
		print("\nOr manually import:")
		print("  bench --site {site} import-doc apps/apex_item/apex_item/fixtures/custom_field.json")
	
	print("=" * 70)
	
	return all_ok


if __name__ == "__main__":
	verify_fields()
