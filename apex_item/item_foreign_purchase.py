"""
API لجلب آخر سعر شراء بالعملة الأجنبية
"""
import frappe
from frappe.utils import flt, getdate
from frappe.query_builder import DocType, Order


@frappe.whitelist()
def get_item_foreign_purchase_info(item_code):
	"""
	جلب آخر سعر شراء للصنف بالعملة الأجنبية
	
	Args:
		item_code (str): كود الصنف
	
	Returns:
		dict: {
			"rate": float,           # السعر بالعملة الأجنبية
			"currency": str,         # كود العملة (USD, EUR, etc.)
			"base_rate": float,      # السعر بالعملة الأساسية
			"conversion_rate": float,    # سعر الصرف
			"purchase_date": str,    # تاريخ الشراء
			"voucher_type": str,     # نوع الوثيقة
			"voucher_no": str,       # رقم الوثيقة
			"supplier": str          # المورد
		}
	"""
	if not item_code:
		return {}
	
	# جلب آخر Purchase Invoice
	last_pi = _get_last_purchase_invoice(item_code)
	last_pr = _get_last_purchase_receipt(item_code)
	last_po = _get_last_purchase_order(item_code)
	
	# تحديد أحدث وثيقة
	last_purchase = None
	voucher_type = None
	voucher_no = None
	purchase_date = None
	
	if last_pi:
		last_purchase = last_pi
		voucher_type = "Purchase Invoice"
		voucher_no = last_pi.get("name")
		purchase_date = getdate(last_pi.get("posting_date"))
	
	if last_pr:
		pr_date = getdate(last_pr.get("posting_date"))
		if not purchase_date or pr_date > purchase_date:
			last_purchase = last_pr
			voucher_type = "Purchase Receipt"
			voucher_no = last_pr.get("name")
			purchase_date = pr_date
			
	if last_po:
		po_date = getdate(last_po.get("transaction_date"))
		if not purchase_date or po_date > purchase_date:
			last_purchase = last_po
			voucher_type = "Purchase Order"
			voucher_no = last_po.get("name")
			purchase_date = po_date
	
	if not last_purchase:
		return {}
	
	conversion_rate = flt(last_purchase.get("conversion_rate")) or 1.0
	conversion_factor = flt(last_purchase.get("conversion_factor")) or 1.0
	base_net_rate = flt(last_purchase.get("base_net_rate")) or 0
	
	# حساب السعر بالعملة الأجنبية
	rate_in_currency = (base_net_rate / conversion_rate) / conversion_factor if conversion_rate > 0 and conversion_factor > 0 else 0
	
	return {
		"rate": rate_in_currency,
		"currency": last_purchase.get("currency") or frappe.db.get_value("Company", last_purchase.get("company"), "default_currency"),
		"base_rate": base_net_rate / conversion_factor if conversion_factor > 0 else 0,
		"conversion_rate": conversion_rate,
		"purchase_date": purchase_date.strftime("%Y-%m-%d") if purchase_date else "",
		"voucher_type": voucher_type,
		"voucher_no": voucher_no,
		"supplier": last_purchase.get("supplier") or "",
	}


def _get_last_purchase_order(item_code):
	"""جلب آخر Purchase Order للصنف"""
	PO = DocType("Purchase Order")
	POItem = DocType("Purchase Order Item")
	
	query = (
		frappe.qb.from_(PO)
		.join(POItem).on(PO.name == POItem.parent)
		.select(
			PO.name,
			PO.transaction_date,
			PO.currency,
			PO.conversion_rate,
			PO.supplier,
			PO.company,
			POItem.base_net_rate,
			POItem.conversion_factor
		)
		.where(
			(POItem.item_code == item_code)
			& (PO.docstatus == 1)
		)
		.orderby(PO.transaction_date, order=Order.desc)
		.orderby(PO.creation, order=Order.desc)
		.limit(1)
	)
	
	result = query.run(as_dict=True)
	return result[0] if result else None


def _get_last_purchase_receipt(item_code):
	"""جلب آخر Purchase Receipt للصنف"""
	PR = DocType("Purchase Receipt")
	PRItem = DocType("Purchase Receipt Item")
	
	query = (
		frappe.qb.from_(PR)
		.join(PRItem).on(PR.name == PRItem.parent)
		.select(
			PR.name,
			PR.posting_date,
			PR.currency,
			PR.conversion_rate,
			PR.supplier,
			PR.company,
			PRItem.base_net_rate,
			PRItem.conversion_factor
		)
		.where(
			(PRItem.item_code == item_code)
			& (PR.docstatus == 1)
		)
		.orderby(PR.posting_date, order=Order.desc)
		.orderby(PR.creation, order=Order.desc)
		.limit(1)
	)
	
	result = query.run(as_dict=True)
	return result[0] if result else None


def _get_last_purchase_invoice(item_code):
	"""جلب آخر Purchase Invoice للصنف"""
	PI = DocType("Purchase Invoice")
	PIItem = DocType("Purchase Invoice Item")
	
	query = (
		frappe.qb.from_(PI)
		.join(PIItem).on(PI.name == PIItem.parent)
		.select(
			PI.name,
			PI.posting_date,
			PI.currency,
			PI.conversion_rate,
			PI.supplier,
			PI.company,
			PIItem.base_net_rate,
			PIItem.conversion_factor
		)
		.where(
			(PIItem.item_code == item_code)
			& (PI.docstatus == 1)
		)
		.orderby(PI.posting_date, order=Order.desc)
		.orderby(PI.creation, order=Order.desc)
		.limit(1)
	)
	
	result = query.run(as_dict=True)
	return result[0] if result else None
