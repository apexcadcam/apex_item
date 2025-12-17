import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

def run():
	# Create Property Setter to force the options
	make_property_setter(
		"Item",
		"sales_price_recommended",
		"options",
		"item_foreign_purchase_currency",
		"Currency"
	)
	print("Created Property Setter for sales_price_recommended options.")
	frappe.db.commit()
