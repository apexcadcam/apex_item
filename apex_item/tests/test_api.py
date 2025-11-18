# -*- coding: utf-8 -*-
# Copyright (c) 2025, Apex Item
# License: MIT. See LICENSE

"""Tests for Apex Item API endpoints"""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from apex_item import api


class TestApexItemAPI(FrappeTestCase):
	"""Test cases for Apex Item API endpoints"""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.create_test_data()

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
		# Create Item Price Card Setting if it doesn't exist
		if not frappe.db.exists("Item Price Card Setting", "Item Price Card Setting"):
			try:
				frappe.get_doc("Item Price Card Setting", "Item Price Card Setting")
			except frappe.DoesNotExistError:
				from apex_item.install import setup_item_price_card_setting

				setup_item_price_card_setting()
				frappe.db.commit()

	def test_get_item_price_card_config(self):
		"""Test get_item_price_card_config API"""
		config = api.get_item_price_card_config()

		# Verify response structure
		self.assertIn("show_item_image", config)
		self.assertIn("empty_state_text", config)
		self.assertIn("fields", config)

		# Verify fields is a list
		self.assertIsInstance(config["fields"], list)

		# Verify default fields if configured
		if config["fields"]:
			first_field = config["fields"][0]
			self.assertIn("fieldname", first_field)
			self.assertIn("label", first_field)

	def test_get_item_price_card_config_caching(self):
		"""Test that get_item_price_card_config uses cache"""
		# First call - should cache
		config1 = api.get_item_price_card_config()

		# Second call - should use cache (much faster)
		config2 = api.get_item_price_card_config()

		# Configs should match
		self.assertEqual(config1, config2)

	def test_get_item_price_card_config_force_refresh(self):
		"""Test get_item_price_card_config with force=True"""
		# Get cached config
		api.get_item_price_card_config()

		# Force refresh
		config = api.get_item_price_card_config(force=True)

		# Should still have valid structure
		self.assertIn("fields", config)

	def test_clear_item_price_card_config_cache(self):
		"""Test clearing card config cache"""
		# Populate cache
		api.get_item_price_card_config()

		# Clear cache
		api.clear_item_price_card_config_cache()

		# Next call should rebuild cache
		config = api.get_item_price_card_config()
		self.assertIsNotNone(config)

	def test_get_item_price_card_setting_debug(self):
		"""Test get_item_price_card_setting_debug API"""
		# Only test if DocType exists
		if not frappe.db.exists("DocType", "Item Price Card Setting"):
			self.skipTest("Item Price Card Setting DocType not available")

		debug_data = api.get_item_price_card_setting_debug()

		# Should return a dictionary
		self.assertIsInstance(debug_data, dict)

		# May be empty if setting doesn't exist
		if debug_data:
			# If exists, should have relevant fields
			pass

	def test_ensure_item_price_card_setting(self):
		"""Test ensure_item_price_card_setting API"""
		# Only test if DocType exists
		if not frappe.db.exists("DocType", "Item Price Card Setting"):
			self.skipTest("Item Price Card Setting DocType not available")

		result = api.ensure_item_price_card_setting()

		# Should return card setting data
		self.assertIsInstance(result, dict)

	def test_reset_item_price_card_setting(self):
		"""Test reset_item_price_card_setting API"""
		# Only test if DocType exists
		if not frappe.db.exists("DocType", "Item Price Card Setting"):
			self.skipTest("Item Price Card Setting DocType not available")

		result = api.reset_item_price_card_setting()

		# Should return card setting data
		self.assertIsInstance(result, dict)
		self.assertIn("card_fields", result)


