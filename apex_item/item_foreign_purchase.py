"""
API لجلب آخر سعر شراء بالعملة الأجنبية
"""
import frappe
from frappe.utils import flt
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
	
	# أولاً: البحث عن آخر Landed Cost Voucher للصنف
	# هذا مهم لأننا نريد أن يكون السعر والرسوم من نفس الوثيقة
	lcv_result = _get_last_lcv_charges_for_item(item_code)
	lcv_name = lcv_result.get("lcv_name")
	total_charges_egp = lcv_result.get("charges", 0)
	
	# إذا وجدنا LCV، نستخدم الوثيقة المرتبطة به
	last_purchase = None
	voucher_type = None
	voucher_no = None
	purchase_date = None
	
	if lcv_name:
		# جلب الوثيقة المرتبطة بـ LCV
		lcv_doc = frappe.get_doc("Landed Cost Voucher", lcv_name)
		if lcv_doc.items:
			# البحث عن الصنف في LCV
			for lcv_item in lcv_doc.items:
				if lcv_item.item_code == item_code:
					receipt_doc_type = lcv_item.receipt_document_type
					receipt_doc_name = lcv_item.receipt_document
					
					if receipt_doc_type == "Purchase Invoice":
						pi = _get_purchase_document("Purchase Invoice", receipt_doc_name, item_code)
						if pi:
							last_purchase = pi
							voucher_type = "Purchase Invoice"
							voucher_no = receipt_doc_name
							purchase_date = getdate(pi.get("posting_date"))
							break
					elif receipt_doc_type == "Purchase Receipt":
						pr = _get_purchase_document("Purchase Receipt", receipt_doc_name, item_code)
						if pr:
							pr_date = getdate(pr.get("posting_date"))
							if not purchase_date or pr_date > purchase_date:
								last_purchase = pr
								voucher_type = "Purchase Receipt"
								voucher_no = receipt_doc_name
								purchase_date = pr_date
	
	# Fallback: إذا لم نجد وثيقة مرتبطة بـ LCV، نبحث عن آخر وثيقة شراء
	if not last_purchase:
		last_pi = _get_last_purchase_invoice(item_code)
		last_pr = _get_last_purchase_receipt(item_code)
		last_po = _get_last_purchase_order(item_code)
		
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
		
		# إذا لم نجد LCV، نبحث عن LCV مرتبط بالوثيقة الحالية
		if last_purchase and total_charges_egp == 0:
			result = _get_lcv_charges(voucher_type, voucher_no, item_code)
			total_charges_egp = result.get("charges", 0)
			if not lcv_name:
				lcv_name = result.get("lcv_name")
	
	if not last_purchase:
		return {}
	
	conversion_rate = flt(last_purchase.get("conversion_rate")) or 1.0
	conversion_factor = flt(last_purchase.get("conversion_factor")) or 1.0
	base_net_rate = flt(last_purchase.get("base_net_rate")) or 0
	
	# حساب السعر بالعملة الأجنبية
	# إذا كانت العملة هي العملة الأساسية (EGP)، لا نحتاج للتحويل
	currency = last_purchase.get("currency") or frappe.db.get_value("Company", last_purchase.get("company"), "default_currency")
	company_currency = frappe.db.get_value("Company", last_purchase.get("company"), "default_currency")
	
	if currency == company_currency:
		# العملة الأساسية - السعر هو base_net_rate
		rate_in_currency = base_net_rate / conversion_factor if conversion_factor > 0 else 0
	else:
		# عملة أجنبية - نحتاج للتحويل
		rate_in_currency = (base_net_rate / conversion_rate) / conversion_factor if conversion_rate > 0 and conversion_factor > 0 else 0
	
	# تحويل الرسوم إلى العملة الأجنبية
	# مهم: يجب استخدام سعر الصرف من Purchase Invoice/Receipt نفسه (conversion_rate)
	# وليس سعر الصرف من تاريخ LCV
	applicable_charges = 0.0
	if total_charges_egp > 0:
		if currency == company_currency:
			# إذا كانت العملة الأساسية، الرسوم كما هي
			applicable_charges = total_charges_egp
		else:
			# استخدام سعر الصرف من Purchase Invoice/Receipt نفسه
			# هذا هو سعر الصرف الذي تم استخدامه في الفاتورة
			if conversion_rate and conversion_rate > 0:
				applicable_charges = total_charges_egp / conversion_rate

	return {
		"rate": rate_in_currency,
		"currency": last_purchase.get("currency") or frappe.db.get_value("Company", last_purchase.get("company"), "default_currency"),
		"base_rate": base_net_rate / conversion_factor if conversion_factor > 0 else 0,
		"conversion_rate": conversion_rate,
		"purchase_date": purchase_date.strftime("%Y-%m-%d") if purchase_date else "",
		"voucher_type": voucher_type,
		"voucher_no": voucher_no,
		"supplier": last_purchase.get("supplier") or "",
		"applicable_charges": applicable_charges,
		"lcv_name": lcv_name
	}


def _get_lcv_charges(receipt_document_type, receipt_document, item_code):
	"""
	جلب Applicable Charges ورقم LCV من Landed Cost Voucher لصنف محدد في وثيقة شراء.
	
	Args:
		receipt_document_type: نوع الوثيقة (Purchase Receipt أو Purchase Invoice)
		receipt_document: رقم الوثيقة
		item_code: كود الصنف
	
	Returns:
		dict: {
			"charges": float,  # Applicable Charges بالعملة المحلية (EGP)
			"lcv_name": str   # رقم Landed Cost Voucher
		}
	"""
	# البحث عن Landed Cost Voucher المرتبط بالوثيقة
	LCV = DocType("Landed Cost Voucher")
	LCItem = DocType("Landed Cost Item")
	
	query = (
		frappe.qb.from_(LCV)
		.join(LCItem).on(LCV.name == LCItem.parent)
		.select(LCItem.applicable_charges, LCV.name.as_("lcv_name"))
		.where(
			(LCItem.receipt_document_type == receipt_document_type)
			& (LCItem.receipt_document == receipt_document)
			& (LCItem.item_code == item_code)
			& (LCV.docstatus == 1)
		)
		.orderby(LCV.posting_date, order=Order.desc)
		.orderby(LCV.creation, order=Order.desc)
		.limit(1)
	)
	
	result = query.run(as_dict=True)
	
	if result and result[0].get("applicable_charges"):
		return {
			"charges": flt(result[0].get("applicable_charges")),
			"lcv_name": result[0].get("lcv_name")
		}
	
	# Fallback: البحث في جميع Landed Cost Vouchers التي تحتوي على الصنف
	# (في حالة عدم وجود receipt_document محدد)
	fallback_query = (
		frappe.qb.from_(LCV)
		.join(LCItem).on(LCV.name == LCItem.parent)
		.select(LCItem.applicable_charges, LCV.name.as_("lcv_name"))
		.where(
			(LCItem.item_code == item_code)
			& (LCV.docstatus == 1)
		)
		.orderby(LCV.posting_date, order=Order.desc)
		.orderby(LCV.creation, order=Order.desc)
		.limit(1)
	)
	
	fallback_result = fallback_query.run(as_dict=True)
	
	if fallback_result and fallback_result[0].get("applicable_charges"):
		return {
			"charges": flt(fallback_result[0].get("applicable_charges")),
			"lcv_name": fallback_result[0].get("lcv_name")
		}
	
	return {"charges": 0.0, "lcv_name": None}


def _get_last_lcv_charges_for_item(item_code):
	"""
	جلب آخر Applicable Charges ورقم LCV من Landed Cost Voucher للصنف (بغض النظر عن الوثيقة).
	
	هذه الدالة مفيدة عندما لا تكون الوثيقة الحالية مرتبطة بـ Landed Cost Voucher،
	لكن نريد عرض آخر رسوم تم توزيعها على الصنف.
	
	Args:
		item_code: كود الصنف
	
	Returns:
		dict: {
			"charges": float,  # Applicable Charges بالعملة المحلية (EGP)
			"lcv_name": str   # رقم Landed Cost Voucher
		}
	"""
	LCV = DocType("Landed Cost Voucher")
	LCItem = DocType("Landed Cost Item")
	
	query = (
		frappe.qb.from_(LCV)
		.join(LCItem).on(LCV.name == LCItem.parent)
		.select(LCItem.applicable_charges, LCV.name.as_("lcv_name"))
		.where(
			(LCItem.item_code == item_code)
			& (LCV.docstatus == 1)
		)
		.orderby(LCV.posting_date, order=Order.desc)
		.orderby(LCV.creation, order=Order.desc)
		.limit(1)
	)
	
	result = query.run(as_dict=True)
	
	if result and result[0].get("applicable_charges"):
		return {
			"charges": flt(result[0].get("applicable_charges")),
			"lcv_name": result[0].get("lcv_name")
		}
	
	return {"charges": 0.0, "lcv_name": None}

	return {
		"rate": rate_in_currency,
		"currency": last_purchase.get("currency") or frappe.db.get_value("Company", last_purchase.get("company"), "default_currency"),
		"base_rate": base_net_rate / conversion_factor if conversion_factor > 0 else 0,
		"conversion_rate": conversion_rate,
		"purchase_date": purchase_date.strftime("%Y-%m-%d") if purchase_date else "",
		"voucher_type": voucher_type,
		"voucher_no": voucher_no,
		"supplier": last_purchase.get("supplier") or "",
		"applicable_charges": applicable_charges
	}


def _get_purchase_document(doctype, doc_name, item_code):
	"""
	جلب بيانات وثيقة شراء مع السعر للصنف.
	
	Args:
		doctype: نوع الوثيقة (Purchase Invoice, Purchase Receipt, Purchase Order)
		doc_name: رقم الوثيقة
		item_code: كود الصنف
	
	Returns:
		dict: بيانات الوثيقة مع السعر
	"""
	if doctype == "Purchase Invoice":
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
				(PI.name == doc_name)
				& (PIItem.item_code == item_code)
				& (PI.docstatus == 1)
			)
			.limit(1)
		)
		
		result = query.run(as_dict=True)
		return result[0] if result else None
	
	elif doctype == "Purchase Receipt":
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
				(PR.name == doc_name)
				& (PRItem.item_code == item_code)
				& (PR.docstatus == 1)
			)
			.limit(1)
		)
		
		result = query.run(as_dict=True)
		return result[0] if result else None
	
	return None


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


def calculate_sales_price_recommended(doc):
	"""
	Calculate Sales Price Recommended based on Foreign Purchase Rate, Charges, and Margin.
	This mirrors the client-side logic in item_foreign_purchase.js
	"""
	if doc.item_foreign_purchase_rate:
		rate = flt(doc.item_foreign_purchase_rate)
		charges = 0.0
		
		if doc.expense_calculation_method == 'Percentage':
			expense_pct = flt(doc.expense_percentage)
			charges = rate * (expense_pct / 100.0)
		else:
			# Default to Fixed Amount (Applicable Charges from LCV)
			charges = flt(doc.item_foreign_purchase_applicable_charges)
			
		margin_percent = flt(doc.margin_profit_percent)
		total_cost = rate + charges
		recommended_price = total_cost * (1 + margin_percent / 100.0)
		
		doc.sales_price_recommended = recommended_price
