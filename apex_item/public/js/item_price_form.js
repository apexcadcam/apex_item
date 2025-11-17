frappe.ui.form.on("Item Price", {
	refresh(frm) {
		// Debug footprint to confirm script load
		try { console.debug("[Apex Item] Item Price form script loaded", { name: frm.doc && frm.doc.name }); } catch (e) {}

		if (frm.is_new()) {
			return;
		}

		const handler = async () => {
			if (!frm.doc.name) return;
			frm.disable_save();
			try {
				frappe.dom.freeze(__("Refreshing stock snapshot..."));
				const r = await frappe.call({
					method: "apex_item.item_price_hooks.refresh_item_price",
					args: { name: frm.doc.name },
				});
				const v = r && r.message ? r.message : {};
				frm.set_value("stock_warehouse", v.stock_warehouse || frm.doc.stock_warehouse);
				frm.set_value("actual_qty", v.actual_qty || 0);
				frm.set_value("reserved_qty", v.reserved_qty || 0);
				frm.set_value("available_qty", v.available_qty || 0);
				frm.set_value("waiting_qty", v.waiting_qty || 0);
				frm.refresh_fields(["stock_warehouse", "actual_qty", "reserved_qty", "available_qty", "waiting_qty"]);
				frappe.show_alert({ message: __("Stock fields refreshed"), indicator: "green" });
			} catch (e) {
				console.error(e);
				frappe.msgprint({ message: __("Failed to refresh stock. See browser console for details."), indicator: "red" });
			} finally {
				frappe.dom.unfreeze();
				frm.enable_save();
			}
		};

		// Toolbar button
		frm.add_custom_button(__("Refresh Stock"), handler);
		// Also add to the menu for visibility
		frm.page.add_menu_item(__("Refresh Stock"), handler);
	},
});

