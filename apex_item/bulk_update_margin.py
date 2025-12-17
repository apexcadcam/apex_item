import frappe
from frappe.utils import flt

def run():
	# 1. Update Margin Profit Percent for ALL items
	print("Updating Margin Profit Percent to 50% for all items...")
	frappe.db.sql("UPDATE `tabItem` SET margin_profit_percent = 50")
	frappe.db.commit()
	print("Margin Profit Percent updated.")

	# 2. Recalculate Sales Price Recommended for items with foreign purchase info
	print("Recalculating Sales Price Recommended...")
	
	items = frappe.db.sql("""
		SELECT name, item_foreign_purchase_rate, item_foreign_purchase_applicable_charges
		FROM `tabItem`
		WHERE item_foreign_purchase_rate > 0 OR item_foreign_purchase_applicable_charges > 0
	""", as_dict=True)
	
	count = 0
	for item in items:
		rate = flt(item.item_foreign_purchase_rate)
		charges = flt(item.item_foreign_purchase_applicable_charges)
		margin = 50.0
		
		total_cost = rate + charges
		recommended_price = total_cost * (1 + margin / 100.0)
		
		frappe.db.set_value("Item", item.name, "sales_price_recommended", recommended_price, update_modified=False)
		count += 1
		
		if count % 100 == 0:
			frappe.db.commit()
			print(f"Processed {count} items...")
			
	frappe.db.commit()
	print(f"Total items recalculated: {count}")
