import frappe
from frappe.utils import flt

def run():
	item_code = "ITEM-00453"
	doc = frappe.get_doc("Item", item_code)
	
	print(f"Item: {item_code}")
	print(f"Old Margin: {doc.margin_profit_percent}")
	print(f"Old Sales Price: {doc.sales_price_recommended}")
	
	# Change margin to 60%
	doc.margin_profit_percent = 60
	doc.flags.ignore_mandatory = True
	doc.save()
	
	# Reload to get updated values from DB
	doc.reload()
	
	print(f"New Margin: {doc.margin_profit_percent}")
	print(f"New Sales Price: {doc.sales_price_recommended}")
	
	# Verify calculation
	rate = flt(doc.item_foreign_purchase_rate)
	charges = 0.0
	if doc.expense_calculation_method == 'Percentage':
		charges = rate * (flt(doc.expense_percentage) / 100.0)
	else:
		charges = flt(doc.item_foreign_purchase_applicable_charges)
		
	expected_price = (rate + charges) * 1.60
	print(f"Expected Price (calculated manually): {expected_price}")
	
	if abs(flt(doc.sales_price_recommended) - expected_price) < 0.01:
		print("SUCCESS: Sales Price updated correctly on save.")
	else:
		print("FAILURE: Sales Price did not update correctly.")
