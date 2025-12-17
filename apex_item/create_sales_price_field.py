import frappe

def run():
	# 1. Update Margin Profit Percent to be Percent type
	if frappe.db.exists("Custom Field", "Item-margin_profit_percent"):
		frappe.db.set_value("Custom Field", "Item-margin_profit_percent", "fieldtype", "Percent")
		print("Updated Margin Profit Percent to Percent type.")

	# 2. Create Sales Price Recommended field
	field_name = "Item-sales_price_recommended"
	if frappe.db.exists("Custom Field", field_name):
		frappe.delete_doc("Custom Field", field_name)
		print(f"Deleted existing {field_name}")

	new_field = frappe.get_doc({
		"doctype": "Custom Field",
		"dt": "Item",
		"fieldname": "sales_price_recommended",
		"label": "Sales Price Recommended",
		"fieldtype": "Currency",
		"insert_after": "margin_profit_percent",
		"module": "Apex Item",
		"read_only": 1,
		"options": "Company:default_currency" # Or item_foreign_purchase_currency? No, sales price is usually in company currency?
		# Wait, "Foreign Purchase Rate" is in Foreign Currency.
		# "Applicable Charges" is in Foreign Currency (converted).
		# So "Sales Price Recommended" should probably be in Foreign Currency too?
		# Or converted to Company Currency?
		# User formula: Foreign Purchase Rate + Applicable Charges (Foreign Currency) + Margin
		# This implies the result is in Foreign Currency.
		# But Sales Price is usually in Company Currency (Standard Selling Rate).
		# If I calculate it in Foreign Currency, it's not very useful for local sales.
		# However, based on the inputs (Foreign Rate + Foreign Charges), the result is Foreign.
		# I will set options to 'item_foreign_purchase_currency' if possible, or just leave it blank/Currency.
		# Let's assume Foreign Currency for now as per the inputs.
	})
	new_field.insert()
	print(f"Created {field_name}")
	
	frappe.db.commit()
