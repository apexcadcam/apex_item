// Client Script لإجبار Frappe على عرض حقول آخر شراء بالعملة الأجنبية
frappe.ui.form.on('Item', {
	refresh: function (frm) {
		// إجبار Frappe على عرض جميع الحقول بالترتيب الصحيح
		const fields_to_show = [
			'item_foreign_purchase_section',
			'item_foreign_purchase_currency',
			'item_foreign_purchase_rate',
			'item_foreign_purchase_applicable_charges',
			'item_foreign_purchase_lcv',  // ✅ إضافة LCV
			'item_foreign_purchase_column_break',
			'custom_item_foreign_purchase_date',
			'item_foreign_purchase_voucher_type',
			'item_foreign_purchase_voucher_no',
			'item_foreign_purchase_supplier'
		];

		fields_to_show.forEach(function (fieldname) {
			// إظهار الحقل
			frm.toggle_display(fieldname, true);

			// إزالة hidden class إذا كان موجوداً
			const field = frm.fields_dict[fieldname];
			if (field) {
				const $wrapper = $(field.wrapper || field.$wrapper);
				if ($wrapper) {
					$wrapper.removeClass('hidden');
					$wrapper.show();
				}
			}
		});

		// إعادة تحميل الـ form layout
		if (frm.layout) {
			frm.layout.refresh();
		}
	},

	margin_profit_percent: function (frm) {
		calculate_sales_price_recommended(frm);
	},

	item_foreign_purchase_rate: function (frm) {
		calculate_sales_price_recommended(frm);
	},

	item_foreign_purchase_applicable_charges: function (frm) {
		calculate_sales_price_recommended(frm);
	},

	expense_calculation_method: function (frm) {
		calculate_sales_price_recommended(frm);
	},

	expense_percentage: function (frm) {
		calculate_sales_price_recommended(frm);
	}
});

function calculate_sales_price_recommended(frm) {
	if (frm.doc.item_foreign_purchase_rate) {
		let rate = flt(frm.doc.item_foreign_purchase_rate);
		let charges = 0;

		if (frm.doc.expense_calculation_method === 'Percentage') {
			let expense_pct = flt(frm.doc.expense_percentage);
			charges = rate * (expense_pct / 100);
		} else {
			// Default to Fixed Amount (Applicable Charges from LCV)
			charges = flt(frm.doc.item_foreign_purchase_applicable_charges);
		}

		let margin_percent = flt(frm.doc.margin_profit_percent);

		let total_cost = rate + charges;
		let recommended_price = total_cost * (1 + margin_percent / 100);

		frm.set_value('sales_price_recommended', recommended_price);
	}
}
