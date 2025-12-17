import frappe

def run():
	field_name = "Item-margin_profit_percent"
	
	if frappe.db.exists("Custom Field", field_name):
		frappe.db.set_value("Custom Field", field_name, "permlevel", 0)
		print(f"Updated {field_name}: Set permlevel to 0")
		frappe.db.commit()
		frappe.clear_cache()
	else:
		print(f"Custom Field {field_name} not found.")
