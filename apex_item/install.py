"""Install / uninstall helpers for Apex Item."""

from __future__ import annotations

import json
from pathlib import Path

import frappe

from apex_item.item_price_config import get_default_card_config


def after_install() -> None:
	"""Create custom fields and default Item Price card settings after install."""
	try:
		print("\n" + "=" * 70)
		print("📦 Installing Apex Item fixtures...")
		print("=" * 70)

		# Import custom fields with progress reporting
		import_custom_fields()
		
		# Setup card settings
		setup_item_price_card_setting()

		# Commit all changes atomically
		frappe.db.commit()

		# Verify installation completed successfully
		_verify_installation()

		print("=" * 70)
		print("✅ Apex Item installed successfully!")
		print("=" * 70 + "\n")
	except Exception as e:
		# Rollback on error to prevent partial installation
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "Apex Item Installation Error")
		print(f"\n❌ Error during installation: {str(e)}")
		print("   Installation rolled back. Check error logs for details.")
		print("   You may need to uninstall and reinstall the app.\n")
		# Re-raise to prevent app from being marked as installed
		raise


def after_migrate() -> None:
	"""Ensure defaults exist after migrations run."""
	try:
		# Import custom fields to ensure they exist after migration
		import_custom_fields()
		setup_item_price_card_setting()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Apex Item After Migrate")


def before_uninstall() -> None:
	"""Clean up customisations before uninstall."""
	try:
		print("\n" + "=" * 70)
		print("🗑️  Uninstalling Apex Item...")
		print("=" * 70)
		print("\n⚠️  WARNING: Item Price helper fields will be removed.\n")

		remove_custom_fields()
		remove_property_setters()
		remove_custom_columns()
		remove_item_price_card_settings()

		frappe.db.commit()

		print("=" * 70)
		print("✅ Apex Item uninstalled successfully!")
		print("=" * 70 + "\n")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Apex Item Uninstall Error")
		print("\n❌ Error during uninstall. Check error logs for details.\n")


def import_custom_fields() -> None:
	"""Ensure Item Price helper fields exist."""
	print("\n📋 Importing Item Price custom fields...")

	app_path = Path(frappe.get_app_path("apex_item"))
	fixtures_path = app_path / "fixtures" / "custom_field.json"

	if not fixtures_path.exists():
		print(f"  ⚠️  custom_field.json not found at: {fixtures_path}")
		return

	with fixtures_path.open("r", encoding="utf-8") as handle:
		custom_fields = json.load(handle)

	total = len(custom_fields)
	print(f"  Found {total} custom field(s) to process")

	created = 0
	updated = 0
	failed = 0

	# Process in batches to show progress and avoid timeout
	batch_size = 5
	for i in range(0, total, batch_size):
		batch = custom_fields[i:i + batch_size]
		batch_num = (i // batch_size) + 1
		total_batches = (total + batch_size - 1) // batch_size
		
		for field_data in batch:
			field_data["module"] = "Apex Item"
			field_name = field_data.get("name")
			dt = field_data.get("dt")
			fieldname = field_data.get("fieldname")

			if not field_name or not dt or not fieldname:
				print(f"  ❌ Invalid fixture entry, skipping...")
				failed += 1
				continue

			try:
				if frappe.db.exists("Custom Field", field_name):
					# Update existing field to ensure all properties match fixture
					existing_field = frappe.get_doc("Custom Field", field_name)
					# Update all properties from fixture
					for key, value in field_data.items():
						if key not in ["name", "doctype", "docstatus"]:
							existing_field.set(key, value)
					existing_field.module = "Apex Item"
					existing_field.save(ignore_permissions=True)
					updated += 1
					print(f"  🔄 Updated: {dt}.{fieldname} [{batch_num}/{total_batches}]")
					continue

				custom_field = frappe.get_doc(field_data)
				custom_field.insert(ignore_permissions=True, ignore_if_duplicate=True)
				print(f"  ✅ Created: {dt}.{fieldname} [{batch_num}/{total_batches}]")
				created += 1
			except Exception as exc:
				print(f"  ❌ Failed: {dt}.{fieldname} - {exc}")
				failed += 1
				# Continue with other fields instead of failing completely
		
		# Commit after each batch to prevent large transaction
		if i + batch_size < total:
			frappe.db.commit()

	print(f"\n  Summary: {created} created, {updated} updated, {failed} failed")
	if failed > 0:
		print(f"  ⚠️  {failed} field(s) failed. Check logs for details.")
	print("  ✓ Custom field installation complete!\n")


def remove_custom_fields() -> None:
	"""Remove Apex Item custom fields during uninstall."""
	print("\n📋 Removing Apex Item custom fields...")

	doctype_field_map = {
		"Item Price": [
			"available_qty",
			"reserved_qty",
			"actual_qty",
			"waiting_qty",
			"item_group",
			"item_image",
		],
	}

	custom_fields: list[dict[str, str]] = []

	for doctype, fieldnames in doctype_field_map.items():
		custom_fields.extend(
			frappe.get_all(
				"Custom Field",
				filters={"dt": doctype, "fieldname": ["in", fieldnames]},
				fields=["name", "dt", "fieldname"],
			)
		)

	if not custom_fields:
		print("  ℹ️  No Apex Item custom fields found to remove")
		return

	print(f"  Found {len(custom_fields)} custom field(s) to remove:")

	removed = 0
	failed = 0

	for field in custom_fields:
		field_label = f"{field.dt}.{field.fieldname}"
		try:
			if frappe.db.exists("Custom Field", field.name):
				frappe.delete_doc("Custom Field", field.name, force=True, ignore_permissions=True)
				print(f"  ✅ Removed: {field_label}")
				removed += 1
			else:
				print(f"  ⏭️  {field_label} not found, skipping...")
		except Exception as exc:
			print(f"  ❌ Failed to remove {field_label}: {exc}")
			failed += 1

	print(f"\n  Summary: {removed} removed, {failed} failed")
	print("  ✓ Custom field cleanup complete!\n")


def remove_property_setters() -> None:
	"""Remove property setters that belong to Apex Item."""
	print("\n🧾 Removing Apex Item property setters...")

	property_setter_names = [
		"Item Price-main-image_field",
	]

	if not property_setter_names:
		print("  ℹ️  No property setter names defined, skipping cleanup")
		return

	property_setters = frappe.get_all(
		"Property Setter",
		filters={"name": ["in", property_setter_names]},
		fields=["name", "doc_type", "property"],
	)

	if not property_setters:
		print("  ℹ️  No Apex Item property setters found to remove")
		return

	print(f"  Found {len(property_setters)} property setter(s) to remove:")

	removed = 0
	failed = 0

	for property_setter in property_setters:
		label = f"{property_setter.doc_type}.{property_setter.property}"
		try:
			frappe.delete_doc("Property Setter", property_setter.name, force=True, ignore_permissions=True)
			print(f"  ✅ Removed: {label}")
			removed += 1
		except Exception as exc:
			print(f"  ❌ Failed to remove {label}: {exc}")
			failed += 1

	print(f"\n  Summary: {removed} removed, {failed} failed")
	print("  ✓ Property setter cleanup complete!\n")


def remove_custom_columns() -> None:
	"""Drop database columns that were added by Apex Item."""
	print("\n🧹 Removing Apex Item database columns...")

	columns_to_drop = [
		("Item Price Card Field", "name"),  # placeholder to ensure child table check happens
		("Item Price", "available_qty"),
	]

	dropped = 0
	skipped = 0

	for doctype, column in columns_to_drop:
		table = f"tab{doctype}"
		try:
			if column == "name" and doctype == "Item Price Card Field":
				# child DocType cleanup handled elsewhere; skip dummy tuple
				continue
			if frappe.db.has_column(table, column):
				frappe.db.sql(f"ALTER TABLE `{table}` DROP COLUMN `{column}`")
				print(f"  ✅ Dropped column: {doctype}.{column}")
				dropped += 1
			else:
				print(f"  ⏭️  Column not found, skipping: {doctype}.{column}")
				skipped += 1
		except Exception as exc:
			frappe.log_error(frappe.get_traceback(), "Apex Item Uninstall - Drop Column Error")
			print(f"  ❌ Failed to drop {doctype}.{column}: {exc}")

	print(f"\n  Summary: {dropped} column(s) dropped, {skipped} skipped")
	print("  ✓ Database cleanup complete!\n")


def remove_item_price_card_settings() -> None:
	"""Remove Item Price Card settings documents and Singles data."""
	print("\n🗂️  Removing Item Price card settings data...")

	try:
		if frappe.db.exists("DocType", "Item Price Card Setting") and frappe.db.exists(
			"Item Price Card Setting", "Item Price Card Setting"
		):
			frappe.delete_doc(
				"Item Price Card Setting",
				"Item Price Card Setting",
				force=True,
				ignore_permissions=True,
			)
			print("  ✅ Deleted Item Price Card Setting document")
	except Exception as exc:
		print(f"  ❌ Failed to delete Item Price Card Setting document: {exc}")

	# Ensure Singles table entries are removed even if the document delete failed.
	try:
		frappe.db.sql(
			"DELETE FROM `tabSingles` WHERE `doctype` = %s",
			("Item Price Card Setting",),
		)
		print("  ✅ Cleared Singles data for Item Price Card Setting")
	except Exception as exc:
		print(f"  ❌ Failed to clear Singles data: {exc}")

	# Drop child table if it still exists (e.g., if uninstall previously failed).
	child_table = "tabItem Price Card Field"
	try:
		if frappe.db.table_exists(child_table):
			frappe.db.sql(f"DROP TABLE `{child_table}`")
			print("  ✅ Dropped table: tabItem Price Card Field")
	except Exception as exc:
		print(f"  ❌ Failed to drop table tabItem Price Card Field: {exc}")

	print("  ✓ Item Price card setting cleanup complete!\n")


def setup_item_price_card_setting() -> None:
	"""Create a default Item Price Card Setting document if none exists yet."""
	if not frappe.db.exists("DocType", "Item Price Card Setting"):
		return

	try:
		doc = frappe.get_single("Item Price Card Setting")
		is_new = False
	except frappe.DoesNotExistError:
		doc = frappe.new_doc("Item Price Card Setting")
		is_new = True

	default_config = get_default_card_config()

	if doc.card_fields and len(doc.card_fields) > 0 and not is_new:
		_ensure_item_price_card_single_values(doc)
		return

	doc.show_item_image = default_config.get("show_item_image", 0)
	doc.empty_state_text = default_config.get("empty_state_text")
	doc.set("card_fields", [])

	for field in default_config.get("fields", []):
		doc.append(
			"card_fields",
			{
				"fieldname": field.get("fieldname"),
				"label": field.get("label"),
				"css_class": field.get("css_class"),
				"is_full_width": field.get("is_full_width", 0),
				"hide_if_zero": field.get("hide_if_zero", 0),
			},
		)

	if is_new:
		doc.insert(ignore_permissions=True)
	else:
		doc.save(ignore_permissions=True)

	_ensure_item_price_card_single_values(doc)


def _ensure_item_price_card_single_values(doc) -> None:
	"""Persist single values so the document can be opened from the desk UI."""
	frappe.db.sql(
		"""
		INSERT INTO `tabSingles` (doctype, field, value)
		VALUES (%s, %s, %s)
		ON DUPLICATE KEY UPDATE value = VALUES(value)
		""",
		("Item Price Card Setting", "show_item_image", int(doc.show_item_image or 0)),
	)

	frappe.db.sql(
		"""
		INSERT INTO `tabSingles` (doctype, field, value)
		VALUES (%s, %s, %s)
		ON DUPLICATE KEY UPDATE value = VALUES(value)
		""",
		("Item Price Card Setting", "empty_state_text", doc.empty_state_text or ""),
	)


def _verify_installation() -> None:
	"""Verify that installation completed successfully."""
	# Check if critical custom fields exist
	critical_fields = [
		("Item Price", "stock_warehouse"),
		("Item Price", "actual_qty"),
		("Item Price", "available_qty"),
	]
	
	missing_fields = []
	for dt, fieldname in critical_fields:
		field_name = f"{dt}-{fieldname}"
		if not frappe.db.exists("Custom Field", field_name):
			missing_fields.append(f"{dt}.{fieldname}")
	
	if missing_fields:
		raise Exception(
			f"Installation incomplete: Missing critical fields: {', '.join(missing_fields)}"
		)
	
	# Verify app can be imported
	try:
		import apex_item
		assert hasattr(apex_item, "hooks")
	except (ImportError, AttributeError) as e:
		raise Exception(f"Installation incomplete: Cannot import apex_item module: {e}")
	
	print("  ✓ Installation verification passed")

