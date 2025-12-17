import frappe
from frappe.utils import flt

def run():
	# Find an enabled item with foreign purchase rate
	item = frappe.db.sql("""
		SELECT item_code 
		FROM `tabItem` 
		WHERE disabled=0 AND item_foreign_purchase_rate > 0 
		LIMIT 1
	""", as_dict=True)
	
	if not item:
		print("No enabled items found with foreign purchase rate")
		return
		
	item_code = item[0].item_code
	doc = frappe.get_doc("Item", item_code)
	
	print(f"Testing with ENABLED item: {item_code}")
	print(f"Disabled status: {doc.disabled}")
	print(f"Current Margin: {doc.margin_profit_percent}")
	print(f"Current Price: {doc.sales_price_recommended}")
	
	# Update Margin
	doc.margin_profit_percent = 65
	doc.flags.ignore_mandatory = True
	doc.save()
	
	doc.reload()
	print(f"New Margin: {doc.margin_profit_percent}")
	print(f"New Price: {doc.sales_price_recommended}")
	
	# Verify
	rate = flt(doc.item_foreign_purchase_rate)
	charges = flt(doc.item_foreign_purchase_applicable_charges)
	expected = (rate + charges) * 1.65
	print(f"Expected: {expected}")
	
	if abs(flt(doc.sales_price_recommended) - expected) < 1:
		print("✓ SUCCESS: Bulk Edit logic is working!")
	else:
		print("✗ FAILURE")
