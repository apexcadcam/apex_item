import frappe
from frappe.utils import flt

def run():
	item_code = "ITEM-00001"
	doc = frappe.get_doc("Item", item_code)
	
	print(f"Item: {item_code}")
	print(f"Current Margin: {doc.margin_profit_percent}")
	print(f"Current Price: {doc.sales_price_recommended}")
	
	# Update Margin
	doc.margin_profit_percent = 55
	doc.save()
	
	doc.reload()
	print(f"New Margin: {doc.margin_profit_percent}")
	print(f"New Price: {doc.sales_price_recommended}")
	
	# Verify
	rate = flt(doc.item_foreign_purchase_rate)
	expected = rate * 1.55
	print(f"Expected: {expected}")
	
	if abs(flt(doc.sales_price_recommended) - expected) < 0.1:
		print("SUCCESS")
	else:
		print("FAILURE")
