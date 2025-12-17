import frappe

def run():
	meta = frappe.get_meta("Item")
	field = meta.get_field("sales_price_recommended")
	print(f"Field Options in Meta: {field.options}")
	
	# Check if the options field exists in meta
	opt_field = meta.get_field("item_foreign_purchase_currency")
	print(f"Options Field Exists: {opt_field is not None}")
	if opt_field:
		print(f"Options Field Type: {opt_field.fieldtype}")
