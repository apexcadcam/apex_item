import frappe

def run():
	# 1. Create Expense Calculation Method
	method_field_name = "Item-expense_calculation_method"
	if frappe.db.exists("Custom Field", method_field_name):
		frappe.delete_doc("Custom Field", method_field_name)
		
	method_field = frappe.get_doc({
		"doctype": "Custom Field",
		"dt": "Item",
		"fieldname": "expense_calculation_method",
		"label": "Expense Calculation Method",
		"fieldtype": "Select",
		"options": "Fixed Amount\nPercentage",
		"default": "Fixed Amount",
		"insert_after": "margin_profit_percent",
		"module": "Apex Item",
		"permlevel": 0
	})
	method_field.insert()
	print(f"Created {method_field_name}")

	# 2. Create Expense Percentage
	percent_field_name = "Item-expense_percentage"
	if frappe.db.exists("Custom Field", percent_field_name):
		frappe.delete_doc("Custom Field", percent_field_name)
		
	percent_field = frappe.get_doc({
		"doctype": "Custom Field",
		"dt": "Item",
		"fieldname": "expense_percentage",
		"label": "Expense Percentage",
		"fieldtype": "Percent",
		"insert_after": "expense_calculation_method",
		"depends_on": "eval:doc.expense_calculation_method == 'Percentage'",
		"module": "Apex Item",
		"permlevel": 0
	})
	percent_field.insert()
	print(f"Created {percent_field_name}")
	
	frappe.db.commit()
