import frappe

def run():
	field_name = "Item-margin_profit_percent"
	
	# Delete existing field
	if frappe.db.exists("Custom Field", field_name):
		frappe.delete_doc("Custom Field", field_name)
		print(f"Deleted existing Custom Field: {field_name}")
	
	# Create new field
	new_field = frappe.get_doc({
		"doctype": "Custom Field",
		"dt": "Item",
		"fieldname": "margin_profit_percent",
		"label": "Margin Profit Percent",
		"fieldtype": "Float",
		"insert_after": "max_discount",
		"module": "Apex Item",
		"non_negative": 1,
		"permlevel": 0,
		"print_hide": 1
	})
	new_field.insert()
	print(f"Created new Custom Field: {field_name} after max_discount")
	
	frappe.db.commit()
