import frappe

def run():
	"""
	Test bulk update of expense_percentage for enabled items
	"""
	# Get 5 enabled items
	items = frappe.db.sql("""
		SELECT name, expense_calculation_method, expense_percentage, disabled
		FROM `tabItem`
		WHERE disabled = 0
		LIMIT 5
	""", as_dict=True)
	
	print(f"Found {len(items)} enabled items")
	print("\nBefore update:")
	for item in items:
		print(f"  {item.name}: method={item.expense_calculation_method}, percentage={item.expense_percentage}, disabled={item.disabled}")
	
	# Try to update expense_percentage to 10%
	print("\nUpdating expense_percentage to 10%...")
	updated_count = 0
	failed_count = 0
	
	for item in items:
		try:
			doc = frappe.get_doc("Item", item.name)
			doc.expense_percentage = 10
			doc.flags.ignore_mandatory = True
			doc.save()
			updated_count += 1
			print(f"  ✓ Updated {item.name}")
		except Exception as e:
			failed_count += 1
			print(f"  ✗ Failed {item.name}: {str(e)}")
	
	print(f"\n✓ Updated: {updated_count}")
	print(f"✗ Failed: {failed_count}")
	
	# Verify
	print("\nAfter update:")
	items_after = frappe.db.sql("""
		SELECT name, expense_percentage
		FROM `tabItem`
		WHERE name IN ({})
	""".format(','.join([f"'{i.name}'" for i in items])), as_dict=True)
	
	for item in items_after:
		print(f"  {item.name}: percentage={item.expense_percentage}")
