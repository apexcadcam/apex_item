import frappe

def run():
	field_name = "Item-margin_profit_percent"
	
	if frappe.db.exists("Custom Field", field_name):
		frappe.db.set_value("Custom Field", field_name, {
			"insert_after": "max_discount",
			"module": "Apex Item"
		})
		frappe.db.commit()
		print(f"Updated {field_name}: Moved after max_discount and assigned to Apex Item.")
	else:
		print(f"Custom Field {field_name} not found.")
