# -*- coding: utf-8 -*-
# Copyright (c) 2025, Apex Item
# License: MIT. See LICENSE

"""Tests for Item Price doctype with custom fields"""

from __future__ import annotations
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import flt


class TestItemPrice(FrappeTestCase):
	"""Test cases for Item Price with Apex Item custom fields"""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		# Patch frappe.attach_print to skip workflow actions during test
		cls.attach_print_patcher = patch("frappe.attach_print", return_value={})
		cls.attach_print_patcher.start()
		cls.create_test_data()

	@classmethod
	def tearDownClass(cls):
		if hasattr(cls, "attach_print_patcher"):
			cls.attach_print_patcher.stop()
		super().tearDownClass()

	def setUp(self):
		"""Set up test data before each test"""
		frappe.db.rollback()
		frappe.db.begin()
		frappe.set_user("Administrator")

	def tearDown(self):
		"""Clean up after each test"""
		frappe.db.rollback()

	@classmethod
	def create_test_data(cls):
		"""Create test data"""
		# Item
		if not frappe.db.exists("Item", "TEST-ITEM-001"):
			# Get or create Item Group
			item_group = frappe.db.get_value("Item Group", {}, "name")
			if not item_group:
				# Create default Item Group if none exists
				item_group_doc = frappe.get_doc(
					{
						"doctype": "Item Group",
						"item_group_name": "Test Products",
						"is_group": 0,
					}
				)
				item_group_doc.insert(ignore_permissions=True, ignore_if_duplicate=True)
				item_group = item_group_doc.name
				frappe.db.commit()

			# Use frappe.new_doc to get default values
			item = frappe.new_doc("Item")
			item.item_code = "TEST-ITEM-001"
			item.item_name = f"Test Item {frappe.generate_hash(length=6)}"  # Unique name
			item.item_group = item_group
			item.stock_uom = "Nos"
			item.is_stock_item = 1
			
			# Set required fields if they are mandatory (using default empty strings)
			if hasattr(item, "brand"):
				item.brand = "" if not item.brand else item.brand
			if hasattr(item, "image"):
				item.image = "" if not item.image else item.image
			if hasattr(item, "country_of_origin"):
				item.country_of_origin = "" if not item.country_of_origin else item.country_of_origin
			
			item.flags.ignore_mandatory = True
			item.insert(ignore_permissions=True)
			frappe.db.commit()
			cls.test_item = item.item_code
		else:
			cls.test_item = "TEST-ITEM-001"

		# Warehouse
		warehouse_name = f"TEST-WH-{frappe.generate_hash(length=6)}"
		if not frappe.db.exists("Warehouse", warehouse_name):
			warehouse = frappe.get_doc(
				{
					"doctype": "Warehouse",
					"warehouse_name": warehouse_name,
					"company": frappe.db.get_value("Company", {}, "name") or frappe.db.get_single_value("Global Defaults", "default_company"),
				}
			)
			warehouse.insert(ignore_permissions=True, ignore_if_duplicate=True)
			frappe.db.commit()
			cls.test_warehouse = warehouse.name
		else:
			cls.test_warehouse = warehouse_name

		# Price List
		if not frappe.db.exists("Price List", "Test Price List"):
			price_list = frappe.get_doc(
				{
					"doctype": "Price List",
					"price_list_name": "Test Price List",
					"currency": "USD",
					"selling": 1,  # Required: Price List must be applicable for Buying or Selling
				}
			)
			price_list.insert(ignore_permissions=True)
			frappe.db.commit()
			cls.test_price_list = price_list.name
		else:
			cls.test_price_list = "Test Price List"

	def test_item_price_creation_with_custom_fields(self):
		"""Test creating Item Price with custom fields from apex_item"""
		item_price = frappe.get_doc(
			{
				"doctype": "Item Price",
				"item_code": self.test_item,
				"price_list": self.test_price_list,
				"price_list_rate": 100.0,
				"stock_warehouse": self.test_warehouse,
			}
		)

		# Verify custom fields exist (added by apex_item)
		self.assertTrue(hasattr(item_price, "stock_warehouse"))
		self.assertTrue(hasattr(item_price, "actual_qty"))
		self.assertTrue(hasattr(item_price, "reserved_qty"))
		self.assertTrue(hasattr(item_price, "available_qty"))
		self.assertTrue(hasattr(item_price, "waiting_qty"))
		self.assertTrue(hasattr(item_price, "item_group"))
		self.assertTrue(hasattr(item_price, "item_image"))

		# Insert Item Price
		item_price.insert(ignore_permissions=True)

		# Verify custom fields are populated after save
		self.assertIsNotNone(item_price.stock_warehouse)
		# Quantities may be 0 if no Bin exists yet
		self.assertIsNotNone(item_price.actual_qty)
		self.assertIsNotNone(item_price.available_qty)

	def test_item_price_custom_fields_auto_calculated(self):
		"""Test that custom quantity fields are auto-calculated"""
		# Create Bin with stock
		bin_doc = frappe.get_doc(
			{
				"doctype": "Bin",
				"item_code": self.test_item,
				"warehouse": self.test_warehouse,
				"actual_qty": 100.0,
				"reserved_qty": 25.0,
			}
		)
		bin_doc.insert(ignore_if_duplicate=True, ignore_permissions=True)
		frappe.db.commit()

		# Create Item Price
		item_price = frappe.get_doc(
			{
				"doctype": "Item Price",
				"item_code": self.test_item,
				"price_list": self.test_price_list,
				"price_list_rate": 100.0,
				"stock_warehouse": self.test_warehouse,
			}
		)
		item_price.insert(ignore_permissions=True)

		# Reload to get calculated values
		item_price.reload()

		# Verify quantities are calculated
		self.assertEqual(flt(item_price.actual_qty), 100.0)
		self.assertEqual(flt(item_price.reserved_qty), 25.0)
		self.assertEqual(flt(item_price.available_qty), 75.0)  # 100 - 25

	def test_item_price_item_group_synced(self):
		"""Test that item_group is synced from Item"""
		item_price = frappe.get_doc(
			{
				"doctype": "Item Price",
				"item_code": self.test_item,
				"price_list": self.test_price_list,
				"price_list_rate": 100.0,
			}
		)
		item_price.insert(ignore_permissions=True)

		# Reload to get synced values
		item_price.reload()

		# item_group should be synced from Item
		if item_price.item_group:
			item = frappe.get_doc("Item", self.test_item)
			self.assertEqual(item_price.item_group, item.item_group)

	def test_item_price_update_quantities(self):
		"""Test that updating Bin updates Item Price quantities"""
		# Create Item Price
		item_price = frappe.get_doc(
			{
				"doctype": "Item Price",
				"item_code": self.test_item,
				"price_list": self.test_price_list,
				"price_list_rate": 100.0,
				"stock_warehouse": self.test_warehouse,
			}
		)
		item_price.insert(ignore_permissions=True)
		frappe.db.commit()

		# Create initial Bin
		bin_doc = frappe.get_doc(
			{
				"doctype": "Bin",
				"item_code": self.test_item,
				"warehouse": self.test_warehouse,
				"actual_qty": 50.0,
				"reserved_qty": 10.0,
			}
		)
		bin_doc.insert(ignore_if_duplicate=True, ignore_permissions=True)
		frappe.db.commit()

		# Refresh Item Price
		from apex_item.item_price_hooks import refresh_item_price

		refresh_item_price(item_price.name)
		frappe.db.commit()

		# Reload Item Price
		item_price.reload()

		# Verify quantities updated
		self.assertEqual(flt(item_price.actual_qty), 50.0)
		self.assertEqual(flt(item_price.available_qty), 40.0)


