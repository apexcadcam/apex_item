app_name = "apex_item"
app_title = "Apex Item"
app_publisher = "Gaber"
app_description = "Item pricing tools"
app_email = "gaber@example.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "apex_item",
# 		"logo": "/assets/apex_item/logo.png",
# 		"title": "Apex Item",
# 		"route": "/apex_item",
# 		"has_permission": "apex_item.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/apex_item/css/apex_item.css"
# app_include_js = "/assets/apex_item/js/apex_item.js"

# include js, css files in header of web template
# web_include_css = "/assets/apex_item/css/apex_item.css"
# web_include_js = "/assets/apex_item/js/apex_item.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "apex_item/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_list_js = {
	"Item Price": "public/js/item_price_list.js"
}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "apex_item/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "apex_item.utils.jinja_methods",
# 	"filters": "apex_item.utils.jinja_filters"
# }

# Installation
# ------------

after_install = "apex_item.install.after_install"
after_migrate = ["apex_item.install.after_migrate"]

# Uninstallation
# ------------

before_uninstall = "apex_item.install.before_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "apex_item.utils.before_app_install"
# after_app_install = "apex_item.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "apex_item.utils.before_app_uninstall"
# after_app_uninstall = "apex_item.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "apex_item.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Item Price": {
		"before_insert": "apex_item.item_price_hooks.set_stock_fields",
		"before_save": "apex_item.item_price_hooks.set_stock_fields",
		"after_insert": "apex_item.item_price_hooks.update_available_qty_on_save",
		"on_update": "apex_item.item_price_hooks.update_available_qty_on_save",
	},
	"Bin": {
		"on_update": "apex_item.item_price_hooks.update_item_price_from_bin",
	},
	"Stock Ledger Entry": {
		"on_submit": "apex_item.item_price_hooks.update_item_prices_from_stock_ledger",
		"on_cancel": "apex_item.item_price_hooks.update_item_prices_from_stock_ledger",
	},
	"Sales Order": {
		"on_submit": "apex_item.item_price_hooks.update_item_prices_from_sales_order",
		"on_cancel": "apex_item.item_price_hooks.update_item_prices_from_sales_order",
		"on_update_after_submit": "apex_item.item_price_hooks.update_item_prices_from_sales_order",
	},
	"Purchase Order": {
		"on_submit": "apex_item.item_price_hooks.update_item_prices_from_purchase_order",
		"on_cancel": "apex_item.item_price_hooks.update_item_prices_from_purchase_order",
		"on_update_after_submit": "apex_item.item_price_hooks.update_item_prices_from_purchase_order",
	},
	"Purchase Receipt": {
		"on_submit": "apex_item.item_price_hooks.update_item_prices_from_purchase_receipt",
		"on_cancel": "apex_item.item_price_hooks.update_item_prices_from_purchase_receipt",
	},
	"Item": {
		"validate": "apex_item.item_foreign_purchase_hooks.update_item_on_save",
	},
}

# DocType JavaScript
doctype_js = {
	"Item Price": "public/js/item_price_form.js",
}

# Scheduled Tasks
# ---------------
# Note: These tasks are optional and will only run if scheduler is enabled.
# The app works fine without scheduler - manual refresh buttons are always available.
# If scheduler/workers are not running, scheduled tasks simply won't execute.

scheduler_events = {
	"cron": {
		# reconcile Item Price quantities from recently changed Bins every 5 minutes
		# Safe to run even if workers are down - function has error handling
		"*/5 * * * *": [
			"apex_item.item_price_hooks.scheduled_reconcile_item_price",
		],
	}
}

# Testing
# -------

# before_tests = "apex_item.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "apex_item.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "apex_item.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["apex_item.utils.before_request"]
# after_request = ["apex_item.utils.after_request"]

# Job Events
# ----------
# before_job = ["apex_item.utils.before_job"]
# after_job = ["apex_item.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"apex_item.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

fixtures = [
	{
		"dt": "Custom Field",
		"filters": [
			["module", "=", "Apex Item"],
			["dt", "in", ["Item Price", "Item"]],
		],
	},
	{
		"dt": "Property Setter",
		"filters": [
			["doc_type", "=", "Item Price"],
			["property", "=", "image_field"],
		],
	},
]

