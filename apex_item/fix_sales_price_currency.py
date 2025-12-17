import frappe

def run():
	field_name = "Item-sales_price_recommended"
	
	if frappe.db.exists("Custom Field", field_name):
		frappe.db.set_value("Custom Field", field_name, "options", "item_foreign_purchase_currency")
		print(f"Updated {field_name}: Set options to item_foreign_purchase_currency")
		frappe.db.commit()
	else:
		print(f"Custom Field {field_name} not found.")
