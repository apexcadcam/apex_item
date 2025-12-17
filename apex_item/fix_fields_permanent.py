import frappe

def run():
	"""
	Fix field visibility permanently by ensuring all properties are correct
	"""
	fields_to_fix = [
		{
			"fieldname": "margin_profit_percent",
			"label": "Margin Profit Percent",
			"fieldtype": "Percent",
			"insert_after": "max_discount",
			"hidden": 0,
			"read_only": 0,
			"permlevel": 0,
			"in_list_view": 0
		},
		{
			"fieldname": "expense_calculation_method",
			"label": "Expense Calculation Method",
			"fieldtype": "Select",
			"options": "Fixed Amount\nPercentage",
			"default": "Fixed Amount",
			"insert_after": "margin_profit_percent",
			"hidden": 0,
			"read_only": 0,
			"permlevel": 0
		},
		{
			"fieldname": "expense_percentage",
			"label": "Expense Percentage",
			"fieldtype": "Percent",
			"insert_after": "expense_calculation_method",
			"depends_on": "eval:doc.expense_calculation_method == 'Percentage'",
			"hidden": 0,
			"read_only": 0,
			"permlevel": 0
		},
		{
			"fieldname": "sales_price_recommended",
			"label": "Sales Price Recommended",
			"fieldtype": "Currency",
			"options": "item_foreign_purchase_currency",
			"insert_after": "expense_percentage",
			"hidden": 0,
			"read_only": 0,
			"permlevel": 0
		}
	]
	
	for field_data in fields_to_fix:
		field_name = f"Item-{field_data['fieldname']}"
		
		if frappe.db.exists("Custom Field", field_name):
			# Update existing field
			doc = frappe.get_doc("Custom Field", field_name)
			for key, value in field_data.items():
				if key != "fieldname":
					setattr(doc, key, value)
			doc.save()
			print(f"✓ Updated {field_data['fieldname']}")
		else:
			# Create new field
			field_data["dt"] = "Item"
			field_data["module"] = "Apex Item"
			doc = frappe.get_doc({
				"doctype": "Custom Field",
				**field_data
			})
			doc.insert()
			print(f"✓ Created {field_data['fieldname']}")
	
	frappe.db.commit()
	frappe.clear_cache()
	print("\n✓ All fields fixed and cache cleared!")
	print("Please reload the Item form (Ctrl+Shift+R)")
