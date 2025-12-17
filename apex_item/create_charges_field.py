import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def run():
    print("--- Creating Applicable Charges Custom Field ---")
    
    # Define the security condition (same as section break)
    roles = ['Purchase User', 'CEO', 'General Accountant', 'Accounting Manager', 'System Manager', 'Administrator']
    depends_on_condition = f"eval:{' || '.join([f'frappe.user.has_role(\"{r}\")' for r in roles])}"

    # Create Custom Field on Item
    create_custom_field("Item", "item_foreign_purchase_applicable_charges", "Applicable Charges (Foreign Currency)", "Currency", "item_foreign_purchase_rate", read_only=1, permlevel=2, depends_on=depends_on_condition, description="Landed Cost charges converted to foreign currency")
    
    # Create Custom Field on Purchase Receipt Item and Purchase Invoice Item
    # This field holds the allocated charges in Company Currency
    for dt in ["Purchase Receipt Item", "Purchase Invoice Item"]:
        create_custom_field(dt, "applicable_charges", "Applicable Charges", "Currency", "amount", read_only=1)

    print("Custom Field 'item_foreign_purchase_applicable_charges' created successfully.")

def create_custom_field(dt, fieldname, label, fieldtype, insert_after, read_only=0, permlevel=0, depends_on=None, description=None):
    if not frappe.db.exists("Custom Field", {"dt": dt, "fieldname": fieldname}):
        custom_field_doc = frappe.get_doc({
            "doctype": "Custom Field",
            "dt": dt,
            "fieldname": fieldname,
            "label": label,
            "fieldtype": fieldtype,
            "insert_after": insert_after,
            "read_only": read_only,
            "permlevel": permlevel
        })
        if depends_on:
            custom_field_doc.depends_on = depends_on
        if description:
            custom_field_doc.description = description
        custom_field_doc.insert()
        print(f"Created Custom Field {fieldname} on {dt}")
    else:
        print(f"Custom Field {fieldname} on {dt} already exists")
