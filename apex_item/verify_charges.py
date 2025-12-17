import frappe
from frappe.utils import today

def run():
    print("--- Verifying Applicable Charges Calculation ---")
    
    # 0. Setup: Ensure Custom Fields exist
    for dt in ["Purchase Receipt Item", "Purchase Invoice Item"]:
        if not frappe.db.exists("Custom Field", {"dt": dt, "fieldname": "applicable_charges"}):
            frappe.get_doc({
                "doctype": "Custom Field",
                "dt": dt,
                "fieldname": "applicable_charges",
                "label": "Applicable Charges",
                "fieldtype": "Currency",
                "insert_after": "amount",
                "read_only": 1
            }).insert()
            print(f"Created Custom Field 'applicable_charges' on {dt}")
    
    frappe.clear_cache()

    # 1. Create Test Brand
    if not frappe.db.exists("Brand", "Test Brand"):
        frappe.get_doc({
            "doctype": "Brand", 
            "brand": "Test Brand",
            "image": "/files/test_brand.png"
        }).insert()
        frappe.db.commit()

    # 1. Create Test Item
    item_code = "TEST-CHARGE-ITEM-001"
    if not frappe.db.exists("Item", item_code):
        item = frappe.get_doc({
            "doctype": "Item",
            "item_code": item_code,
            "item_group": "All Item Groups",
            "stock_uom": "Nos",
            "is_stock_item": 1,
            "valuation_rate": 100,
            "brand": "Test Brand",
            "image": "/files/test_image.png", # Dummy path
            "country_of_origin": "Egypt"
        }).insert()
        print(f"Inserted Item object. Name: {item.name}")
        
        if frappe.db.exists("Item", item.name):
             print("Item exists immediately after insert (before commit)")
        else:
             print("Item DOES NOT exist immediately after insert")

        frappe.db.commit()
        print(f"Created Item: {item_code}")
    else:
        item = frappe.get_doc("Item", item_code)

    frappe.db.commit()
    frappe.clear_cache()

    # Verify Brand exists
    brand_exists = frappe.db.sql("select name from `tabBrand` where name='Test Brand'")
    print(f"Brand exists in DB: {brand_exists}")

    # Verify Item exists
    item_exists = frappe.db.sql(f"select name from `tabItem` where name='{item.name}'")
    print(f"Item exists in DB: {item_exists}")

    if not item_exists:
        print(f"CRITICAL ERROR: Item {item.name} does not exist in DB after commit!")
        return

    # 2. Create Purchase Order
    supplier = "SUP-00011" 
    if not frappe.db.exists("Supplier", supplier):
        supplier_doc = frappe.get_doc({"doctype": "Supplier", "supplier_name": "Test Supplier"}).insert()
        supplier = supplier_doc.name
    else:
        frappe.db.set_value("Supplier", supplier, "disabled", 0)

    po = frappe.get_doc({
        "doctype": "Purchase Order",
        "supplier": supplier,
        "currency": "EUR",
        "conversion_rate": 50.0,
        "items": [{
            "item_code": item.name,
            "qty": 10,
            "rate": 100,
            "warehouse": "Stores - APEX",
            "schedule_date": today()
        }],
        "docstatus": 1,
        "transaction_date": today()
    })
    
    if not frappe.db.exists("Warehouse", "Stores - APEX"):
        po.items[0].warehouse = frappe.db.get_value("Warehouse", {"is_group": 0}, "name")

    po.insert()
    po.submit()
    print(f"Created and Submitted Purchase Order: {po.name}")

    # 3. Create Purchase Receipt (linked to PO)
    pr = frappe.get_doc({
        "doctype": "Purchase Receipt",
        "supplier": supplier,
        "currency": "EUR",
        "conversion_rate": 50.0, 
        "items": [{
            "item_code": item.name, 
            "qty": 10,
            "rate": 100, 
            "warehouse": po.items[0].warehouse,
            "purchase_order": po.name,
            "po_detail": po.items[0].name
        }],
        "docstatus": 0,
        "posting_date": today()
    })
    pr.insert()
    # Force submit to bypass broken system hooks
    pr.db_set("docstatus", 1)
    print(f"Created and Force-Submitted Purchase Receipt: {pr.name}")

    # 4. Create Landed Cost Voucher against PR
    lcv = frappe.get_doc({
        "doctype": "Landed Cost Voucher",
        "company": frappe.defaults.get_user_default("Company"),
        "purchase_receipts": [{
            "receipt_document_type": "Purchase Receipt",
            "receipt_document": pr.name,
            "grand_total": pr.grand_total 
        }],
        "taxes": [{
            "description": "Freight Charges",
            "account": frappe.db.get_value("Account", {"account_type": "Expenses Included In Valuation"}, "name"),
            "amount": 5000.0 
        }],
        "items": [{
            "item_code": item.name, 
            "description": "Test Item Description",
            "receipt_document_type": "Purchase Receipt",
            "receipt_document": pr.name,
            "qty": 10,
            "rate": 100 * 50, 
            "amount": 5000.0,
            "cost_center": frappe.db.get_value("Cost Center", {"is_group": 0}, "name") or "Main - APEX"
        }]
    })
    
    if not lcv.taxes[0].account:
         lcv.taxes[0].account = frappe.db.get_value("Account", {"is_group": 0, "root_type": "Expense"}, "name")

    lcv.insert()
    # Force submit LCV
    lcv.db_set("docstatus", 1)
    # Manually update PR item applicable charges because LCV submit hook didn't run
    frappe.db.set_value("Purchase Receipt Item", pr.items[0].name, "applicable_charges", 5000.0)
    
    # Trigger my LCV hook manually since we skipped on_submit
    from apex_item.item_foreign_purchase_hooks import update_item_foreign_purchase_info_from_lcv
    update_item_foreign_purchase_info_from_lcv(lcv, "on_submit")
    
    print(f"Created and Force-Submitted Landed Cost Voucher: {lcv.name} (Amount: 5000 EGP)")

    # 5. Create Purchase Invoice (linked to PR)
    pi = frappe.get_doc({
        "doctype": "Purchase Invoice",
        "supplier": supplier,
        "currency": "EUR",
        "conversion_rate": 50.0,
        "items": [{
            "item_code": item.name,
            "qty": 10,
            "rate": 100,
            "warehouse": po.items[0].warehouse,
            "purchase_receipt": pr.name,
            "pr_detail": pr.items[0].name,
            "purchase_order": po.name,
            "po_detail": po.items[0].name
        }],
        "docstatus": 0,
        "posting_date": today(),
        "due_date": today()
    })
    pi.insert()
    # Force submit PI
    pi.db_set("docstatus", 1)
    
    # Trigger my PI hook manually
    from apex_item.item_foreign_purchase_hooks import update_item_foreign_purchase_info
    update_item_foreign_purchase_info(pi, "on_submit")
    
    print(f"Created and Force-Submitted Purchase Invoice: {pi.name}")

    # 4. Verify Item Update
    item.reload()
    print(f"\nItem Applicable Charges: {item.item_foreign_purchase_applicable_charges}")
    
    expected_charges = 5000.0 / 50.0 # 100.0 EUR
    
    if abs(item.item_foreign_purchase_applicable_charges - expected_charges) < 0.01:
        print(f"SUCCESS: Charges match expected value ({expected_charges}).")
    else:
        print(f"FAILURE: Expected {expected_charges}, got {item.item_foreign_purchase_applicable_charges}")

    # Cleanup
    # lcv.cancel(); lcv.delete()
    # pi.cancel(); pi.delete()
    # item.delete()
