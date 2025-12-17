"""
Hooks لتحديث حقول آخر شراء بالعملة الأجنبية تلقائياً
"""
import frappe
from apex_item.item_foreign_purchase import get_item_foreign_purchase_info, calculate_sales_price_recommended


def update_item_foreign_purchase_info(doc, method):
	"""
	Update Item Foreign Purchase Info fields.
	Triggered on submit/cancel of Purchase Order/Receipt/Invoice.
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
						"item_foreign_purchase_supplier": purchase_info.get("supplier"),
						"item_foreign_purchase_applicable_charges": purchase_info.get("applicable_charges"),
						"item_foreign_purchase_lcv": purchase_info.get("lcv_name")
					},
					update_modified=False
				)
			else:
				# Clear values if no purchase info found
				frappe.db.set_value(
					"Item",
					item_code,
					{
						"item_foreign_purchase_rate": 0,
						"item_foreign_purchase_currency": None,
						"custom_item_foreign_purchase_date": None,
						"item_foreign_purchase_voucher_type": None,
						"item_foreign_purchase_voucher_no": None,
						"item_foreign_purchase_supplier": None,
						"item_foreign_purchase_applicable_charges": 0,
						"item_foreign_purchase_lcv": None
					},
					update_modified=False
				)
			
			frappe.db.commit()
		except Exception as e:
			frappe.log_error(
				frappe.get_traceback(),
				"Apex Item - Update Foreign Purchase Fields Error"
			)


def update_item_foreign_purchase_info_from_lcv(doc, method):
	"""
	تحديث معلومات آخر شراء بالعملة الأجنبية عند submit/cancel Landed Cost Voucher.
	
	عند submit Landed Cost Voucher، يتم توزيع الرسوم على الأصناف وتحديث حقل
	applicable_charges في Purchase Receipt Item / Purchase Invoice Item.
	هذه الدالة تحدث حقل applicable_charges في Item بناءً على آخر وثيقة شراء.
	"""
	# جمع جميع الأصناف الفريدة من Landed Cost Voucher
	items_to_update = set()
	
	for item in doc.items:
		if item.item_code:
			items_to_update.add(item.item_code)
	
	# تحديث كل صنف
	for item_code in items_to_update:
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
						"item_foreign_purchase_supplier": purchase_info.get("supplier"),
						"item_foreign_purchase_applicable_charges": purchase_info.get("applicable_charges"),
						"item_foreign_purchase_lcv": purchase_info.get("lcv_name")
					},
					update_modified=False
				)
			else:
				# Clear values if no purchase info found
				frappe.db.set_value(
					"Item",
					item_code,
					{
						"item_foreign_purchase_rate": 0,
						"item_foreign_purchase_currency": None,
						"custom_item_foreign_purchase_date": None,
						"item_foreign_purchase_voucher_type": None,
						"item_foreign_purchase_voucher_no": None,
						"item_foreign_purchase_supplier": None,
						"item_foreign_purchase_applicable_charges": 0,
						"item_foreign_purchase_lcv": None
					},
					update_modified=False
				)
			
			frappe.db.commit()
		except Exception as e:
			frappe.log_error(
				frappe.get_traceback(),
				f"Apex Item - Update Foreign Purchase Fields from LCV Error for {item_code}"
			)


def update_item_on_save(doc, method):
	"""
	Update fields when Item is saved (e.g. re-enabled)
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
			doc.item_foreign_purchase_applicable_charges = purchase_info.get("applicable_charges")
			doc.item_foreign_purchase_lcv = purchase_info.get("lcv_name")
		else:
			doc.item_foreign_purchase_rate = 0
			doc.item_foreign_purchase_currency = None
			doc.custom_item_foreign_purchase_date = None
			doc.item_foreign_purchase_voucher_type = None
			doc.item_foreign_purchase_voucher_no = None
			doc.item_foreign_purchase_supplier = None
			doc.item_foreign_purchase_applicable_charges = 0
			doc.item_foreign_purchase_lcv = None
			
		# Calculate Sales Price Recommended
		calculate_sales_price_recommended(doc)
			
	except Exception as e:
		frappe.log_error(
			frappe.get_traceback(),
			f"Apex Item - Update Item On Save Error for {doc.name}"
		)
