import frappe
from frappe.utils.formatters import format_value

def run():
	item_code = "ITEM-00451"
	doc = frappe.get_doc("Item", item_code)
	
	print(f"Item: {item_code}")
	print(f"Foreign Currency Field: {doc.item_foreign_purchase_currency}")
	print(f"Sales Price Recommended: {doc.sales_price_recommended}")
	
	# Get field definition
	df = doc.meta.get_field("sales_price_recommended")
	print(f"Field Options: {df.options}")
	
	# Format value
	formatted = format_value(doc.sales_price_recommended, df, doc)
	print(f"Formatted Value: {formatted}")
