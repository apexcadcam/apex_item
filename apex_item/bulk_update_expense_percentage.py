import frappe

def run():
	"""
	Bulk update expense_percentage for all enabled Nacera Pearl items
	Set to whatever percentage you want
	"""
	# CHANGE THIS VALUE to your desired percentage
	target_percentage = 35  # Change this to whatever you need
	
	# Get all enabled Nacera Pearl items
	items = frappe.db.sql("""
		SELECT name
		FROM `tabItem`
		WHERE item_name LIKE '%Nacera Pearl%'
		AND disabled = 0
		ORDER BY name
	""", as_dict=True)
	
	print(f"Found {len(items)} enabled Nacera Pearl items")
	print(f"Setting expense_percentage to {target_percentage}%\n")
	
	updated_count = 0
	
	for item in items:
		try:
			doc = frappe.get_doc("Item", item.name)
			doc.expense_percentage = target_percentage
			doc.flags.ignore_mandatory = True
			doc.save()
			updated_count += 1
			
			if updated_count % 10 == 0:
				print(f"  Updated {updated_count} items...")
				frappe.db.commit()
		except Exception as e:
			print(f"  ✗ Failed {item.name}: {str(e)}")
	
	frappe.db.commit()
	print(f"\n✓ Successfully updated {updated_count} items!")
	print(f"All items now have expense_percentage = {target_percentage}%")
