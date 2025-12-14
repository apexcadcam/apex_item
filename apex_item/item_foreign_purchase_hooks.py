"""
Hooks لتحديث حقول آخر شراء بالعملة الأجنبية تلقائياً
"""
import frappe
from apex_item.item_foreign_purchase import get_item_foreign_purchase_info


def update_item_foreign_purchase_fields(doc, method):
	"""
	تحديث حقول آخر شراء بالعملة الأجنبية في Item
	يتم استدعاؤها عند submit/cancel لـ Purchase Order/Receipt/Invoice
	"""
	for item_row in doc.get("items"):
		item_code = item_row.item_code
		if not item_code:
			continue
		
		try:
			purchase_info = get_item_foreign_purchase_info(item_code)
			
			if purchase_info:
				frappe.db.set_value(
					"Item",
					item_code,
					{
						"item_foreign_purchase_rate": purchase_info.get("rate"),
						"item_foreign_purchase_currency": purchase_info.get("currency"),
						"custom_item_foreign_purchase_date": purchase_info.get("purchase_date"),
						"item_foreign_purchase_voucher_type": purchase_info.get("voucher_type"),
						"item_foreign_purchase_voucher_no": purchase_info.get("voucher_no"),
						"item_foreign_purchase_supplier": purchase_info.get("supplier")
					},
					update_modified=False
				)
			else:
				# مسح القيم إذا لم يوجد شراء
				frappe.db.set_value(
					"Item",
					item_code,
					{
						"item_foreign_purchase_rate": 0,
						"item_foreign_purchase_currency": None,
						"custom_item_foreign_purchase_date": None,
						"item_foreign_purchase_voucher_type": None,
						"item_foreign_purchase_voucher_no": None,
						"item_foreign_purchase_supplier": None
					},
					update_modified=False
				)
			
			frappe.db.commit()
		except Exception as e:
			frappe.log_error(
				frappe.get_traceback(),
				"Apex Item - Update Foreign Purchase Fields Error"
			)


def update_item_on_save(doc, method):
	"""
	تحديث حقول آخر شراء عند حفظ الصنف (مثلاً عند تفعيله من جديد)
	"""
	if doc.disabled:
		return

	try:
		purchase_info = get_item_foreign_purchase_info(doc.name)
		
		if purchase_info:
			doc.item_foreign_purchase_rate = purchase_info.get("rate")
			doc.item_foreign_purchase_currency = purchase_info.get("currency")
			doc.custom_item_foreign_purchase_date = purchase_info.get("purchase_date")
			doc.item_foreign_purchase_voucher_type = purchase_info.get("voucher_type")
			doc.item_foreign_purchase_voucher_no = purchase_info.get("voucher_no")
			doc.item_foreign_purchase_supplier = purchase_info.get("supplier")
		else:
			doc.item_foreign_purchase_rate = 0
			doc.item_foreign_purchase_currency = None
			doc.custom_item_foreign_purchase_date = None
			doc.item_foreign_purchase_voucher_type = None
			doc.item_foreign_purchase_voucher_no = None
			doc.item_foreign_purchase_supplier = None
			
	except Exception as e:
		frappe.log_error(
			frappe.get_traceback(),
			f"Apex Item - Update Item On Save Error for {doc.name}"
		)
