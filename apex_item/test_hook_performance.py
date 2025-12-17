import frappe
import time
from apex_item.item_foreign_purchase_hooks import update_item_on_save

def run():
	item_code = "ITEM-00001"
	doc = frappe.get_doc("Item", item_code)
	
	print(f"Testing update_item_on_save for {item_code}...")
	start_time = time.time()
	
	try:
		update_item_on_save(doc, "validate")
		print("Function executed successfully.")
	except Exception as e:
		print(f"Error: {e}")
		import traceback
		traceback.print_exc()
		
	end_time = time.time()
	print(f"Execution time: {end_time - start_time:.4f} seconds")
