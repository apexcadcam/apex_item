import frappe
from apex_item.item_foreign_purchase import get_item_foreign_purchase_info

def run():
	# Find items with applicable charges but no LCV name
	items = frappe.db.sql("""
		SELECT name 
		FROM `tabItem` 
		WHERE item_foreign_purchase_applicable_charges > 0 
		AND (item_foreign_purchase_lcv IS NULL OR item_foreign_purchase_lcv = '')
	""", as_dict=True)
	
	print(f"Found {len(items)} items to update.")
	
	count = 0
	for item in items:
		try:
			item_code = item.name
			# Fetch info again (this will now include LCV name logic)
			purchase_info = get_item_foreign_purchase_info(item_code)
			
			if purchase_info and purchase_info.get("lcv_name"):
				frappe.db.set_value("Item", item_code, "item_foreign_purchase_lcv", purchase_info.get("lcv_name"))
				count += 1
				if count % 10 == 0:
					frappe.db.commit()
					print(f"Updated {count} items...")
		except Exception as e:
			print(f"Error updating {item.name}: {e}")
			
	frappe.db.commit()
	print(f"Total updated: {count}")
