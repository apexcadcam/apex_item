import frappe

def run():
	"""
	Remove depends_on from expense_percentage to make it bulk-editable
	"""
	field_name = "Item-expense_percentage"
	
	if frappe.db.exists("Custom Field", field_name):
		# Remove the depends_on condition
		frappe.db.set_value("Custom Field", field_name, "depends_on", None)
		print(f"✓ Removed depends_on from expense_percentage")
		print("  Now the field will be available in bulk edit")
		
		frappe.db.commit()
		frappe.clear_cache()
		print("\n✓ Cache cleared!")
		print("Please reload the page and try bulk edit again")
	else:
		print(f"Field {field_name} not found")
