# -*- coding: utf-8 -*-
# Copyright (c) 2025, Apex Item
# License: MIT. See LICENSE

"""Tests for Item Price Hooks and Stock Calculation"""

from __future__ import annotations
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import flt

from apex_item.item_price_hooks import (
	refresh_item_price,
	refresh_item_prices,
	refresh_item_prices_by_filters,
	set_stock_fields,
)


class TestItemPriceHooks(FrappeTestCase):
	"""Test cases for Item Price hooks and stock calculation"""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		# Patch frappe.attach_print to skip workflow actions during test
		cls.attach_print_patcher = patch("frappe.attach_print", return_value={})
		cls.attach_print_patcher.start()
		# Create test data
		cls.create_test_item()
		cls.create_test_warehouse()
		cls.create_test_price_list()

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
	def create_test_item(cls):
		"""Create a test item"""
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
			# These might be mandatory in some configurations
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

	@classmethod
	def create_test_warehouse(cls):
		"""Create a test warehouse"""
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

	@classmethod
	def create_test_price_list(cls):
		"""Create a test price list"""
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

	def create_test_item_price(self, item_code=None, warehouse=None, price_list=None):
		"""Create a test Item Price"""
		item_price = frappe.get_doc(
			{
				"doctype": "Item Price",
				"item_code": item_code or self.test_item,
				"price_list": price_list or self.test_price_list,
				"price_list_rate": 100.0,
				"stock_warehouse": warehouse or self.test_warehouse,
			}
		)
		item_price.insert(ignore_permissions=True)
		return item_price

	def create_test_bin(self, item_code=None, warehouse=None, actual_qty=0, reserved_qty=0):
		"""Create or update a test Bin"""
		item_code = item_code or self.test_item
		warehouse = warehouse or self.test_warehouse

		bin_doc = frappe.get_doc(
			{
				"doctype": "Bin",
				"item_code": item_code,
				"warehouse": warehouse,
				"actual_qty": actual_qty,
				"reserved_qty": reserved_qty,
			}
		)
		bin_doc.insert(ignore_if_duplicate=True, ignore_permissions=True)
		return bin_doc

	def test_set_stock_fields(self):
		"""Test that set_stock_fields calculates stock quantities correctly"""
		# Create Bin with stock
		self.create_test_bin(actual_qty=100.0, reserved_qty=20.0)

		# Create Item Price
		item_price = self.create_test_item_price()

		# Set stock fields
		set_stock_fields(item_price)

		# Verify quantities
		self.assertEqual(flt(item_price.actual_qty), 100.0)
		self.assertEqual(flt(item_price.reserved_qty), 20.0)
		self.assertEqual(flt(item_price.available_qty), 80.0)  # 100 - 20
		self.assertIsNotNone(item_price.stock_warehouse)

	def test_available_qty_calculation(self):
		"""Test that available_qty = actual_qty - reserved_qty"""
		# Create Bin with specific quantities
		actual = 150.0
		reserved = 30.0
		expected_available = 120.0

		self.create_test_bin(actual_qty=actual, reserved_qty=reserved)

		item_price = self.create_test_item_price()
		set_stock_fields(item_price)

		self.assertEqual(flt(item_price.available_qty), expected_available)

	def test_refresh_item_price(self):
		"""Test refresh_item_price API method"""
		# Create Bin with stock
		self.create_test_bin(actual_qty=200.0, reserved_qty=50.0)

		# Create Item Price
		item_price = self.create_test_item_price()

		# Refresh via API
		result = refresh_item_price(item_price.name)

		# Verify response structure
		self.assertIn("actual_qty", result)
		self.assertIn("reserved_qty", result)
		self.assertIn("available_qty", result)
		self.assertIn("waiting_qty", result)

		# Verify quantities
		self.assertEqual(flt(result["actual_qty"]), 200.0)
		self.assertEqual(flt(result["reserved_qty"]), 50.0)
		self.assertEqual(flt(result["available_qty"]), 150.0)

	def test_refresh_item_prices(self):
		"""Test refresh_item_prices for multiple Item Prices"""
		# Create Bins
		self.create_test_bin(actual_qty=100.0, reserved_qty=10.0)

		# Create multiple Item Prices
		item_price1 = self.create_test_item_price()
		item_price2 = self.create_test_item_price()

		# Refresh both
		updated = refresh_item_prices([item_price1.name, item_price2.name])

		# Verify count
		self.assertEqual(updated, 2)

		# Verify quantities updated
		frappe.db.commit()
		item_price1.reload()
		item_price2.reload()

		self.assertEqual(flt(item_price1.actual_qty), 100.0)
		self.assertEqual(flt(item_price2.actual_qty), 100.0)

	def test_refresh_item_prices_by_filters(self):
		"""Test refresh_item_prices_by_filters API method"""
		# Create Bin
		self.create_test_bin(actual_qty=75.0, reserved_qty=15.0)

		# Create Item Price
		item_price = self.create_test_item_price()

		# Refresh by filters
		filters = [["item_code", "=", self.test_item]]
		updated = refresh_item_prices_by_filters(filters, limit=1000)

		# Verify count
		self.assertGreaterEqual(updated, 1)

	def test_stock_fields_read_only(self):
		"""Test that stock quantity fields are read-only"""
		item_price = self.create_test_item_price()
		set_stock_fields(item_price)

		# Try to manually set a read-only field (should not raise error, but value will be recalculated)
		original_available = item_price.available_qty
		item_price.available_qty = 999

		# Recalculate
		set_stock_fields(item_price)

		# Value should be recalculated, not the manually set value
		self.assertNotEqual(item_price.available_qty, 999)

	def test_item_price_without_warehouse(self):
		"""Test Item Price without explicit warehouse"""
		# Create Bin without warehouse filter
		self.create_test_bin(actual_qty=50.0, reserved_qty=5.0)

		item_price = frappe.get_doc(
			{
				"doctype": "Item Price",
				"item_code": self.test_item,
				"price_list": self.test_price_list,
				"price_list_rate": 100.0,
				# No stock_warehouse
			}
		)
		item_price.insert(ignore_permissions=True)

		# Set stock fields - should use item default or aggregate
		set_stock_fields(item_price)

		# Should have calculated quantities
		self.assertIsNotNone(item_price.actual_qty)
		self.assertIsNotNone(item_price.available_qty)

	def test_empty_stock_snapshot(self):
		"""Test stock snapshot when item has no stock"""
		# Create Item Price without Bin (no stock)
		item_price = self.create_test_item_price()

		# Set stock fields
		set_stock_fields(item_price)

		# Verify empty snapshot
		self.assertEqual(flt(item_price.actual_qty), 0.0)
		self.assertEqual(flt(item_price.reserved_qty), 0.0)
		self.assertEqual(flt(item_price.available_qty), 0.0)
		self.assertEqual(flt(item_price.waiting_qty), 0.0)


