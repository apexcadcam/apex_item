"""
Fix Missing Custom Fields
==========================

This script imports custom fields from fixtures if they're missing
after installation. Use this if verify_custom_fields.py reports
missing fields.

Usage:
    bench --site your-site execute apex_item.fix_missing_fields.fix_missing_fields
"""

import frappe
import os
import json


def fix_missing_fields():
	"""Import custom fields from fixtures"""
	
	app_path = frappe.get_app_path("apex_item")
	fixture_path = os.path.join(app_path, "fixtures", "custom_field.json")
	
	print("=" * 70)
	print("APEX ITEM - FIX MISSING CUSTOM FIELDS")
	print("=" * 70)
	print(f"\nLoading fixtures from: {fixture_path}\n")
	
	if not os.path.exists(fixture_path):
		print(f"❌ ERROR: Fixture file not found!")
		print(f"Expected: {fixture_path}")
		return False
	
	with open(fixture_path, 'r') as f:
		fields = json.load(f)
	
	print(f"Found {len(fields)} custom fields in fixtures\n")
	print("Importing fields...\n")
	
	imported = 0
	skipped = 0
	errors = 0
	
	for field_data in fields:
		field_name = field_data.get('name')
		fieldname = field_data.get('fieldname')
		dt = field_data.get('dt')
		
		try:
			if frappe.db.exists("Custom Field", field_name):
				print(f"  ⊙ {dt}.{fieldname} - already exists")
				skipped += 1
			else:
				# Create new custom field
				doc = frappe.get_doc(field_data)
				doc.insert(ignore_permissions=True)
				print(f"  ✓ {dt}.{fieldname} - imported")
				imported += 1
		except Exception as e:
			print(f"  ✗ {dt}.{fieldname} - ERROR: {str(e)}")
			errors += 1
	
	frappe.db.commit()
	
	print(f"\n{'='*70}")
	print(f"Results:")
	print(f"  Imported: {imported}")
	print(f"  Skipped (already exist): {skipped}")
	print(f"  Errors: {errors}")
	print(f"{'='*70}")
	
	if imported > 0:
		print("\n✓ Fields imported successfully!")
		print("\nNext steps:")
		print("  1. bench --site {site} clear-cache")
		print("  2. Refresh your browser")
		print("  3. Check Item form for custom fields")
	elif skipped > 0 and errors == 0:
		print("\n✓ All fields already exist!")
	else:
		print("\n⚠ Some errors occurred. Check the output above.")
	
	print("=" * 70)
	
	return errors == 0


if __name__ == "__main__":
	fix_missing_fields()
