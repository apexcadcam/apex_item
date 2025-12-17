import frappe
from apex_item.item_foreign_purchase import get_item_foreign_purchase_info

def run():
	item_code = "ITEM-00813"
	print(f"Fetching info for: {item_code}")
	
	purchase_info = get_item_foreign_purchase_info(item_code)
	print(f"Purchase Info: {purchase_info}")
	
	if purchase_info:
		frappe.db.set_value("Item", item_code, {
			"item_foreign_purchase_rate": purchase_info.get("rate"),
			"item_foreign_purchase_currency": purchase_info.get("currency"),
			"custom_item_foreign_purchase_date": purchase_info.get("purchase_date"),
			"item_foreign_purchase_voucher_type": purchase_info.get("voucher_type"),
			"item_foreign_purchase_voucher_no": purchase_info.get("voucher_no"),
			"item_foreign_purchase_supplier": purchase_info.get("supplier"),
			"item_foreign_purchase_applicable_charges": purchase_info.get("applicable_charges"),
			"item_foreign_purchase_lcv": purchase_info.get("lcv_name")
		})
		frappe.db.commit()
		print("Update complete.")
	
	# Verify value
	val = frappe.db.get_value("Item", item_code, "item_foreign_purchase_lcv")
	print(f"New item_foreign_purchase_lcv: {val}")
