
import frappe
from apex_item.item_foreign_purchase_hooks import update_item_on_save

@frappe.whitelist()
def trigger_update_foreign_purchase_info():
    """
    Trigger background job to update Foreign Purchase Info for all items.
    Can be called from Desk or Console.
    """
    frappe.enqueue(
        "apex_item.utils._update_items_foreign_purchase_info_job",
        queue="long",
        timeout=3600
    )
    frappe.msgprint("Started background job to update Foreign Purchase Info for all items.")

def _update_items_foreign_purchase_info_job():
    """
    Worker function to update items.
    """
    try:
        items = frappe.get_all("Item", filters={"is_stock_item": 1, "disabled": 0}, fields=["name"])
        total = len(items)
        print(f"Apex Item: Starting background update for {total} items...")
        
        count = 0
        for item in items:
            try:
                doc = frappe.get_doc("Item", item.name)
                # Pass 'validate' as method to simulate save event
                update_item_on_save(doc, "validate")
                doc.save(ignore_permissions=True)
                count += 1
                
                # Commit every 100 items to avoid large transaction logs
                if count % 100 == 0:
                    frappe.db.commit()
                    
            except Exception as e:
                print(f"Apex Item: Failed to update {item.name}: {e}")
                # Log error but continue
                frappe.log_error(f"Apex Item: Failed to update {item.name}: {e}", "Apex Item Background Update")
        
        frappe.db.commit()
        print(f"Apex Item: Background update completed. Updated {count}/{total} items.")
        
    except Exception as e:
        frappe.log_error(f"Apex Item: Job failed: {e}", "Apex Item Background Update Fatal Error")
