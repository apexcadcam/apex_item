import frappe

def run():
	# Delete Property Setter
	frappe.db.sql("DELETE FROM `tabProperty Setter` WHERE doc_type='Item' AND field_name='sales_price_recommended'")
	print("Deleted Property Setter.")
	
	# Update Custom Field
	frappe.db.set_value("Custom Field", "Item-sales_price_recommended", "options", "item_foreign_purchase_currency")
	print("Updated Custom Field options.")
	
	frappe.db.commit()
	frappe.clear_cache()
	print("Cache cleared.")
	
	# Verify Meta
	meta = frappe.get_meta("Item")
	field = meta.get_field("sales_price_recommended")
	print(f"Field Options in Meta after fix: {field.options}")
