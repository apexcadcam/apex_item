// Custom Item Price List - Configurable Mobile Cards / Desktop List

const ITEM_PRICE_ALLOWED_FIELDNAMES = [
	"price_list_rate",
	"currency",
	"available_qty",
	"actual_qty",
	"reserved_qty",
	"waiting_qty",
	"brand",
	"item_group",
	"stock_warehouse",
	"item_code",
	"item_name",
	"uom",
];

const ITEM_PRICE_DEFAULT_FIELD_ORDER = [
	"price_list_rate",
	"available_qty",
	"actual_qty",
	"reserved_qty",
	"brand",
	"stock_warehouse",
	"item_group",
	"waiting_qty",
];

const fltValue = (value) => (frappe.utils && frappe.utils.flt ? frappe.utils.flt(value) : parseFloat(value) || 0);
const cintValue = (value) => (frappe.utils && frappe.utils.cint ? frappe.utils.cint(value) : parseInt(value, 10) || 0);
const formatNumber = (value, precision = 2) => {
	if (frappe && typeof frappe.format === "function") {
		return frappe.format(value, { fieldtype: "Float", precision });
	}
	const number = Number(value || 0);
	return Number.isFinite(number) ? number.toFixed(precision) : "0.00";
};

let itemPriceCardConfigPromise = null;

frappe.listview_settings["Item Price"] = {
	hide_name_column: true,

	add_fields: [
		"item_name",
		"item_code",
		"price_list_rate",
		"currency",
		"available_qty",
		"reserved_qty",
		"actual_qty",
		"waiting_qty",
		"brand",
		"item_group",
		"item_image",
		"uom",
	],

	get_indicator: function (doc) {
		const available = fltValue(doc.available_qty || 0);
		if (available > 0) {
			return [__("Available: {0}", [available]), "green", "available_qty,>,0"];
		}
		return [__("Available: {0}", [available]), "red", "available_qty,=,0"];
	},

	onload(listview) {
		addCustomStyles();
		setupItemPriceView(listview);

		// Add bulk refresh action in list view menu
		if (listview && listview.page) {
			// Refresh all results in current view (respecting filters and limit on server)
			const refreshAllInView = async () => {
				// Collect current filters array from listview
				let filters = [];
				try {
					if (listview.filter_area && typeof listview.filter_area.get === "function") {
						filters = listview.filter_area.get() || [];
					} else if (typeof listview.get_filters_for_args === "function") {
						filters = listview.get_filters_for_args() || [];
					}
				} catch (e) {
					console.warn("Failed to read filters from listview", e);
				}

				frappe.dom.freeze(__("Refreshing all items in current view..."));
				try {
					await frappe.call({
						method: "apex_item.item_price_hooks.refresh_item_prices_by_filters",
						args: { filters },
					});
					frappe.show_alert({ message: __("Refreshed current view"), indicator: "green" });
					listview.refresh();
				} catch (e) {
					console.error(e);
					frappe.msgprint({ message: __("Failed to refresh current view."), indicator: "red" });
				} finally {
					frappe.dom.unfreeze();
				}
			};

			// Add prominent toolbar button
			if (typeof listview.page.add_inner_button === "function") {
				listview.page.add_inner_button(__("Refresh Stock (Current View)"), refreshAllInView);
			} else {
				// Fallback to menu item if button API unavailable
				listview.page.add_menu_item(__("Refresh Stock (Current View)"), refreshAllInView);
			}

			// Auto-refresh on first open/route change with throttling (60s per route+filter)
			let autoSyncInProgress = false;
			const readCurrentFilters = () => {
				let filters = [];
				try {
					if (listview.filter_area && typeof listview.filter_area.get === "function") {
						filters = listview.filter_area.get() || [];
					} else if (typeof listview.get_filters_for_args === "function") {
						filters = listview.get_filters_for_args() || [];
					}
				} catch (e) {
					console.warn("Failed to read filters from listview", e);
				}
				return filters;
			};

			const scheduleAutoRefresh = () => {
				try {
					const route = (frappe.get_route && frappe.get_route().join("/")) || "Item Price";
					const filters = readCurrentFilters();
					const key = `apex_item_ip_auto_sync:${route}:${JSON.stringify(filters)}`;
					const last = Number(sessionStorage.getItem(key) || "0");
					const now = Date.now();
					// 60 seconds throttle
					if (now - last < 60000) return;

					// Run in background without freezing UI; show a subtle alert when done
					autoSyncInProgress = true;
					frappe.call({
						method: "apex_item.item_price_hooks.refresh_item_prices_by_filters",
						args: { filters },
					}).then(() => {
						sessionStorage.setItem(key, String(Date.now()));
						// soft refresh: re-fetch data
						const original = listview.render.bind(listview);
						original(); // re-render without reentering the refresh wrapper
						frappe.show_alert({ message: __("Stock synced"), indicator: "green" });
					}).catch((e) => {
						console.warn("Auto refresh failed", e);
					}).finally(() => {
						autoSyncInProgress = false;
					});
				} catch (e) {
					console.warn("Auto refresh scheduling failed", e);
				}
			};

			// Trigger once shortly after load to allow filters to render
			setTimeout(scheduleAutoRefresh, 400);

			// Hook normal list view refresh (toolbar refresh) to auto-sync before rendering
			if (typeof listview.refresh === "function") {
				const originalRefresh = listview.refresh.bind(listview);
				listview.refresh = function (...args) {
					if (autoSyncInProgress) {
						return originalRefresh(...args);
					}
					const route = (frappe.get_route && frappe.get_route().join("/")) || "Item Price";
					const filters = readCurrentFilters();
					const key = `apex_item_ip_auto_sync:${route}:${JSON.stringify(filters)}`;
					const last = Number(sessionStorage.getItem(key) || "0");
					const now = Date.now();
					// If throttled, just refresh normally
					if (now - last < 60000) {
						return originalRefresh(...args);
					}
					autoSyncInProgress = true;
					return frappe
						.call({
							method: "apex_item.item_price_hooks.refresh_item_prices_by_filters",
							args: { filters },
						})
						.then(() => {
							sessionStorage.setItem(key, String(Date.now()));
						})
						.catch((e) => {
							console.warn("Refresh hook auto-sync failed", e);
						})
						.finally(() => {
							autoSyncInProgress = false;
							originalRefresh(...args);
						});
				};
			}
		}
	},
};

function getFieldDefinitions() {
	return {
		price_list_rate: { label: __("Price"), css_class: "price", hide_if_zero: 0, icon: "💰" },
		currency: { label: __("Currency"), css_class: "info", hide_if_zero: 0 },
		available_qty: { label: __("Available"), css_class: "available", hide_if_zero: 0, icon: "✅" },
		actual_qty: { label: __("Actual"), css_class: "actual", hide_if_zero: 0, icon: "📊" },
		reserved_qty: { label: __("Reserved"), css_class: "reserved", hide_if_zero: 0, icon: "🔒" },
		waiting_qty: { label: __("Waiting (PO)"), css_class: "waiting", hide_if_zero: 1, icon: "⏳" },
		brand: { label: __("Brand"), css_class: "info", hide_if_zero: 0, icon: "🏷️" },
		item_group: { label: __("Group"), css_class: "info", hide_if_zero: 0, icon: "📂" },
		stock_warehouse: { label: __("Warehouse"), css_class: "info", hide_if_zero: 0, icon: "🏬" },
		item_code: { label: __("Item Code"), css_class: "info", hide_if_zero: 0, icon: "#" },
		item_name: { label: __("Item Name"), css_class: "info", hide_if_zero: 0 },
		uom: { label: __("UOM"), css_class: "info", hide_if_zero: 0, icon: "📏" },
	};
}

function getDefaultCardConfig() {
	const definitions = getFieldDefinitions();

	return {
		show_item_image: 1,
		empty_state_text: __("لا توجد أصناف مطابقة"),
		fields: ITEM_PRICE_DEFAULT_FIELD_ORDER.map((fieldname) => {
			const fieldDef = definitions[fieldname] || {};
			return {
				fieldname,
				label: fieldDef.label || toTitleCase(fieldname),
				css_class: fieldDef.css_class || "info",
				is_full_width: fieldname === "waiting_qty" ? 1 : 0,
				hide_if_zero: fieldDef.hide_if_zero || 0,
				icon: fieldDef.icon || "",
			};
		}),
	};
}

function fetchItemPriceCardConfig() {
	if (!itemPriceCardConfigPromise) {
		itemPriceCardConfigPromise = frappe
			.call({
				method: "apex_item.api.get_item_price_card_config",
				freeze: false,
			})
			.then((response) => normalizeCardConfig(response.message))
			.catch(() => normalizeCardConfig());
	}

	return itemPriceCardConfigPromise;
}

function normalizeCardConfig(rawConfig) {
	const base = getDefaultCardConfig();
	const config = rawConfig || {};
	const definitions = getFieldDefinitions();
	const allowed = new Set(ITEM_PRICE_ALLOWED_FIELDNAMES);
	const seen = new Set();

	const normalizedFields = Array.isArray(config.fields)
		? config.fields
			.map((field) => normalizeField(field, definitions))
			.filter((field) => field && allowed.has(field.fieldname))
			.filter((field) => {
				if (seen.has(field.fieldname)) {
					return false;
				}
				seen.add(field.fieldname);
				return true;
			})
		: [];

	return {
		show_item_image: cintValue(config.show_item_image) || base.show_item_image,
		empty_state_text: config.empty_state_text || base.empty_state_text,
		fields: normalizedFields.length ? normalizedFields : base.fields,
	};
}

function normalizeField(field, definitions) {
	if (!field || !field.fieldname) {
		return null;
	}

	const definition = definitions[field.fieldname] || {};
	const label = field.label || definition.label || toTitleCase(field.fieldname);
	const icon = field.icon || definition.icon || "";

	return {
		fieldname: field.fieldname,
		label,
		css_class: field.css_class || definition.css_class || "info",
		is_full_width: cintValue(field.is_full_width) ? 1 : 0,
		hide_if_zero:
			field.hide_if_zero !== undefined && field.hide_if_zero !== null
				? cintValue(field.hide_if_zero)
				: cintValue(definition.hide_if_zero || 0),
		icon,
	};
}

function setupItemPriceView(listview) {
	fetchItemPriceCardConfig().then((config) => initializeItemPriceView(listview, config));
}

function initializeItemPriceView(listview, config) {
	const isMobile = () => window.innerWidth <= 768;
	let $cardsContainer = null;
	const debounce = (fn, wait = 300) => {
		let t = null;
		return (...args) => {
			clearTimeout(t);
			t = setTimeout(() => fn(...args), wait);
		};
	};

	const ensureCardsContainer = () => {
		if ($cardsContainer && $cardsContainer.length) {
			return $cardsContainer;
		}

		$cardsContainer = $("#item-price-cards-container");
		if (!$cardsContainer.length) {
			$cardsContainer = $('<div id="item-price-cards-container"></div>');

			if (listview.$result && listview.$result.length) {
				listview.$result.before($cardsContainer);
			} else if (listview.$result && listview.$result.parent && listview.$result.parent().length) {
				listview.$result.parent().append($cardsContainer);
			} else if (listview.$container) {
				listview.$container.append($cardsContainer);
			} else {
				$(listview.wrapper || document.body).append($cardsContainer);
			}
		}
		return $cardsContainer;
	};

	const renderCards = () => {
		if (!isMobile()) {
			return;
		}

		const container = ensureCardsContainer();
		container.empty();

		const data = listview.data || [];
		if (!data.length) {
			const emptyText = frappe.utils.escape_html(
				config.empty_state_text || __("لا توجد أصناف مطابقة")
			);
			container.html(
				`<div class="item-price-empty">${emptyText}</div>`
			);
			return;
		}

		data.forEach((item) => {
			const cardHtml = createItemPriceCard(item, config);
			if (cardHtml) {
				container.append(cardHtml);
			}
		});
	};

	const originalRender = listview.render.bind(listview);
	listview.render = function () {
		originalRender();
		if (isMobile()) {
			setTimeout(renderCards, 60);
		}
		// Auto-sync after render (debounced) so it works on normal refresh and first load
		if (typeof listview._apex_ip_auto_sync !== "function") {
			// define once
			const readFilters = () => {
				try {
					if (listview.filter_area && typeof listview.filter_area.get === "function") {
						return listview.filter_area.get() || [];
					}
					if (typeof listview.get_filters_for_args === "function") {
						return listview.get_filters_for_args() || [];
					}
				} catch (e) {}
				return [];
			};
			listview._apex_ip_auto_sync = debounce(() => {
				try {
					const route = (frappe.get_route && frappe.get_route().join("/")) || "Item Price";
					const filters = readFilters();
					const key = `apex_item_ip_auto_sync:${route}:${JSON.stringify(filters)}`;
					const last = Number(sessionStorage.getItem(key) || "0");
					const now = Date.now();
					if (now - last < 60000) return; // throttle 60s

					frappe.call({
						method: "apex_item.item_price_hooks.refresh_item_prices_by_filters",
						args: { filters },
					}).then(() => {
						sessionStorage.setItem(key, String(Date.now()));
						// re-render quietly
						originalRender();
					}).catch(() => {});
				} catch (e) {}
			}, 1000);
		}
		listview._apex_ip_auto_sync();
	};

	let resizeTimer = null;
	$(window).on("resize.item-price-view", () => {
		clearTimeout(resizeTimer);
		resizeTimer = setTimeout(() => {
			if (isMobile()) {
				renderCards();
			} else if ($cardsContainer) {
				$cardsContainer.empty();
			}
		}, 200);
	});

	const teardown = () => {
		$(window).off("resize.item-price-view");
	};

	if (listview.page) {
		if (typeof listview.page.once === "function") {
			listview.page.once("hide", teardown);
		} else if (typeof listview.page.on === "function") {
			const handler = () => {
				teardown();
				listview.page.off("hide", handler);
			};
			listview.page.on("hide", handler);
		}
	}

	$(document).one("app_route_changed.item-price-view", teardown);

	setTimeout(renderCards, 80);
}

function createItemPriceCard(data, config) {
	const itemName = frappe.utils.escape_html(data.item_name || __("Unnamed Item"));
	const itemCode = data.item_code ? frappe.utils.escape_html(data.item_code) : "";

	const rowsHtml = (config.fields || [])
		.map((field) => buildCardRow(field, data))
		.filter(Boolean)
		.join("");

	if (!rowsHtml) {
		return null;
	}

	const showImage = cintValue(config.show_item_image) && data.item_image;
	const imageSrc = showImage ? frappe.utils.escape_html(data.item_image) : "";
	const headerClass = showImage ? "card-header has-thumb" : "card-header";
	const thumbHtml = showImage
		? `<div class="card-thumb-wrap thumb-cover"><img src="${imageSrc}" alt="${itemName}" class="card-item-thumb" loading="lazy" /></div>`
		: "";

	const $card = $(
		`<div class="item-price-card">
			<div class="${headerClass}">
				${thumbHtml}
				<div class="card-header-text">
					<div class="card-item-name">${itemName}</div>
					${itemCode ? `<div class="card-item-code">${itemCode}</div>` : ""}
				</div>
			</div>
			<div class="card-body">${rowsHtml}</div>
		</div>`
	);

	if (data.name) {
		$card.addClass("card-clickable");
		$card.on("click", () => {
			frappe.set_route("Form", "Item Price", data.name);
		});
	}

	if (showImage) {
		const $img = $card.find(".card-item-thumb");
		const adjustFit = (imgEl) => {
			const ratio = imgEl.naturalWidth / (imgEl.naturalHeight || 1);
			const $wrap = $(imgEl).closest(".card-thumb-wrap");
			$wrap.removeClass("thumb-cover thumb-contain");
			if (ratio < 0.75) {
				$wrap.addClass("thumb-contain");
			} else {
				$wrap.addClass("thumb-cover");
			}
		};

		$img.on("load", function () {
			adjustFit(this);
		});

		if ($img[0] && $img[0].complete) {
			adjustFit($img[0]);
		}
	}

	return $card;
}

function buildCardRow(field, data) {
	const resolved = resolveFieldValue(field, data);
	if (!resolved) {
		return "";
	}

	const hideIfZero = cintValue(field.hide_if_zero) || cintValue(resolved.hide_if_zero);
	if (hideIfZero && isNumericZero(resolved.raw_value)) {
		return "";
	}

	const label = frappe.utils.escape_html(field.label || resolved.label || "");
	if (!label) {
		return "";
	}

	const classes = ["card-row"];
	if (field.css_class) {
		classes.push(field.css_class);
	}
	if (resolved.css_class) {
		classes.push(resolved.css_class);
	}
	if (resolved.state) {
		classes.push(resolved.state);
	}
	if (cintValue(field.is_full_width)) {
		classes.push("full-width");
	}

	const iconHtml = field.icon ? `<span class="card-icon">${frappe.utils.escape_html(field.icon)}</span>` : "";

	return `
		<div class="${classes.join(" ").trim()}">
			<span class="card-label">${iconHtml}${label}</span>
			<span class="card-value">${resolved.value}</span>
		</div>
	`;
}

function resolveFieldValue(field, data) {
	const definitions = getFieldDefinitions();
	const definition = definitions[field.fieldname] || {};
	const fieldname = field.fieldname;

	switch (fieldname) {
		case "price_list_rate":
			return formatPriceRow(data, definition);
		case "available_qty":
			return formatQuantityRow(data.available_qty, definition, {
				stateForValue: true,
			});
		case "actual_qty":
			return formatQuantityRow(data.actual_qty, definition);
		case "reserved_qty":
			return formatQuantityRow(data.reserved_qty, definition);
		case "waiting_qty":
			return formatQuantityRow(data.waiting_qty, definition, {
				hide_if_zero: true,
				stateForValue: true,
			});
		case "currency":
		case "brand":
		case "item_group":
		case "stock_warehouse":
		case "item_code":
		case "item_name":
		case "uom":
			return formatTextRow(data[fieldname], definition);
		default:
			if (!ITEM_PRICE_ALLOWED_FIELDNAMES.includes(fieldname)) {
				return null;
			}
			return formatTextRow(data[fieldname], definition);
	}
}

function formatPriceRow(data, definition) {
	const amount = fltValue(data.price_list_rate || 0);
	const currency = data.currency;
	let formatted = "0.00";

	if (typeof format_currency === "function") {
		formatted = format_currency(amount, currency);
	} else {
		formatted = formatNumber(amount, 2);
	}

	return {
		value: frappe.utils.escape_html(formatted),
		raw_value: amount,
		css_class: definition.css_class,
		label: definition.label,
		hide_if_zero: cintValue(definition.hide_if_zero || 0),
	};
}

function formatQuantityRow(value, definition, options = {}) {
	const number = fltValue(value || 0);
	const formatted = formatNumber(number, 2);
	const extra = {};

	if (options.stateForValue) {
		extra.state = number > 0 ? "state-positive" : "state-zero";
	}

	return {
		value: formatted,
		raw_value: number,
		css_class: definition.css_class,
		label: definition.label,
		hide_if_zero: options.hide_if_zero ? 1 : cintValue(definition.hide_if_zero || 0),
		...extra,
	};
}

function formatTextRow(value, definition) {
	const safeValue = value ? frappe.utils.escape_html(value) : __("N/A");
	return {
		value: safeValue,
		raw_value: value,
		css_class: definition.css_class,
		label: definition.label,
		hide_if_zero: cintValue(definition.hide_if_zero || 0),
	};
}

function isNumericZero(value) {
	if (typeof value !== "number") {
		return false;
	}
	return Math.abs(value) < 1e-9;
}

function toTitleCase(value) {
	if (!value) {
		return "";
	}
	const base = value.replace(/_/g, " ");
	if (frappe.utils && frappe.utils.to_title_case) {
		return frappe.utils.to_title_case(base);
	}
	return base.replace(/\w\S*/g, (txt) => txt.charAt(0).toUpperCase() + txt.substring(1).toLowerCase());
}

function addCustomStyles() {
	if (document.getElementById("item-price-view-style")) return;

	const style = document.createElement("style");
	style.id = "item-price-view-style";
	style.textContent = `
		/* Hide name/ID column always */
		body[data-route^="List/Item Price"] .list-row-col[data-fieldname="name"],
		body[data-route^="List/Item Price"] .list-header-col[data-fieldname="name"] {
			display: none !important;
		}

		/* Hide cards on desktop by default */
		#item-price-cards-container {
			display: none;
		}

		/* Mobile Card View */
		@media (max-width: 768px) {
			/* Hide list on mobile ONLY */
			body[data-route^="List/Item Price"] .list-row-checkbox,
			body[data-route^="List/Item Price"] .list-check,
			body[data-route^="List/Item Price"] .level.list-row,
			body[data-route^="List/Item Price"] .list-row-head {
				display: none !important;
			}

			body[data-route^="List/Item Price"] .frappe-list .result {
				display: none !important;
			}

			/* Show cards container on mobile */
			#item-price-cards-container {
				display: block !important;
				padding: 8px;
			}

			/* Single Card Style */
			.item-price-card {
				background: #fff;
				border: 1px solid #e5e7eb;
				border-radius: 10px;
				padding: 14px 16px 12px;
				margin-bottom: 10px;
				box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08);
			}

			.card-header {
				display: flex;
				align-items: center;
				gap: 12px;
				margin-bottom: 10px;
			}

			.card-thumb-wrap {
				width: 56px;
				height: 56px;
				display: flex;
				align-items: center;
				justify-content: center;
				border-radius: 8px;
				overflow: hidden;
				border: 1px solid #e5e7eb;
				background: #f1f5f9;
				padding: 2px;
			}

			.card-item-thumb {
				width: 100%;
				height: 100%;
			}

			.card-thumb-wrap.thumb-cover .card-item-thumb {
				object-fit: cover;
			}

			.card-thumb-wrap.thumb-contain .card-item-thumb {
				object-fit: contain;
			}

			.card-header-text {
				display: flex;
				flex-direction: column;
				gap: 2px;
			}

			.card-item-name {
				font-size: 16px;
				font-weight: 600;
				color: #0f172a;
				line-height: 1.2;
			}

			.card-item-code {
				font-size: 12px;
				color: #94a3b8;
			}

			.card-body {
				display: grid;
				grid-template-columns: repeat(3, minmax(0, 1fr));
				gap: 10px 12px;
			}

			.card-row {
				display: flex;
				flex-direction: column;
				align-items: center;
				gap: 4px;
				padding: 0;
			}

			.card-row.full-width {
				grid-column: span 3;
			}

			.card-label {
				display: inline-flex;
				align-items: center;
				justify-content: center;
				gap: 4px;
				font-size: 11px;
				color: #475569;
				font-weight: 600;
				text-transform: uppercase;
				letter-spacing: 0.3px;
				text-align: center;
			}

			.card-icon {
				font-size: 12px;
			}

			.card-value {
				font-size: 15px;
				font-weight: 700;
				color: #1f2937;
				text-align: center;
			}

			.card-row.price .card-value {
				color: #2563eb;
			}

			.card-row.available.state-positive .card-value {
				color: #059669;
			}

			.card-row.available.state-zero .card-value {
				color: #dc2626;
			}

			.card-row.actual .card-value {
				color: #7c3aed;
			}

			.card-row.reserved .card-value {
				color: #d97706;
			}

			.card-row.waiting .card-value {
				color: #0891b2;
			}

			.card-row.info .card-value {
				color: #475569;
			}

			.item-price-empty {
				text-align: center;
				padding: 40px 18px;
				color: #94a3b8;
				font-size: 15px;
			}
		}

		/* Desktop - Hide cards, show list normally */
		@media (min-width: 769px) {
			#item-price-cards-container {
				display: none !important;
			}

			body[data-route^="List/Item Price"] .frappe-list,
			body[data-route^="List/Item Price"] .result,
			body[data-route^="List/Item Price"] .list-row-container {
				display: block !important;
			}

			body[data-route^="List/Item Price"] .list-row,
			body[data-route^="List/Item Price"] .list-row-head {
				display: flex !important;
			}
		}
	`;
	document.head.appendChild(style);
}
