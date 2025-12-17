import frappe

def run():
	field_name = "Item-item_foreign_purchase_lcv"
	
	if frappe.db.exists("Custom Field", field_name):
		frappe.db.set_value("Custom Field", field_name, "read_only", 0)
		print(f"Updated {field_name}: Set read_only to 0")
		frappe.db.commit()
	else:
		print(f"Custom Field {field_name} not found.")
