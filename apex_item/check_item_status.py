import frappe

def run():
	"""
	Check the status of items that might be in your bulk edit selection
	"""
	# Get items from the screenshot (Nacera Pearl items)
	items = frappe.db.sql("""
		SELECT name, item_name, disabled, expense_calculation_method, expense_percentage
		FROM `tabItem`
		WHERE item_name LIKE '%Nacera Pearl%'
		ORDER BY name
		LIMIT 20
	""", as_dict=True)
	
	print(f"Found {len(items)} Nacera Pearl items\n")
	
	enabled_count = 0
	disabled_count = 0
	
	print("Item Status:")
	print("-" * 80)
	for item in items:
		status = "✓ ENABLED" if not item.disabled else "✗ DISABLED"
		if not item.disabled:
			enabled_count += 1
		else:
			disabled_count += 1
		print(f"{item.name:15} {status:12} Method: {item.expense_calculation_method or 'None':15} Percentage: {item.expense_percentage or 0}")
	
	print("-" * 80)
	print(f"\nSummary:")
	print(f"  Enabled items:  {enabled_count} (will be updated)")
	print(f"  Disabled items: {disabled_count} (will be SKIPPED)")
	print(f"\nThis is why only {enabled_count} items were updated!")
