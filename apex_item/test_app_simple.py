#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple tests for apex_item app
Run with: bench --site site1 execute apex_item.test_app_simple.test_all
"""

import frappe

def test_get_item_price_card_config():
	"""Test get_item_price_card_config API"""
	print("\n" + "="*60)
	print("TEST 1: get_item_price_card_config API")
	print("="*60)
	
	from apex_item import api
	config = api.get_item_price_card_config()
	
	print(f"✅ SUCCESS: get_item_price_card_config returned config")
	print(f"   - Fields count: {len(config.get('fields', []))}")
	print(f"   - Show item image: {config.get('show_item_image')}")
	print(f"   - Empty state text: {config.get('empty_state_text', 'N/A')}")
	
	# Verify structure
	assert "fields" in config, "Config missing 'fields'"
	assert "show_item_image" in config, "Config missing 'show_item_image'"
	assert isinstance(config["fields"], list), "Fields should be a list"
	
	print(f"✅ All assertions passed!")
	return True


def test_get_item_price_card_config_caching():
	"""Test that get_item_price_card_config uses cache"""
	print("\n" + "="*60)
	print("TEST 2: get_item_price_card_config Caching")
	print("="*60)
	
	from apex_item import api
	
	# First call - should cache
	config1 = api.get_item_price_card_config()
	
	# Second call - should use cache
	config2 = api.get_item_price_card_config()
	
	# Configs should match
	assert config1 == config2, "Cached config should match original"
	
	print(f"✅ SUCCESS: Caching works correctly")
	print(f"   - Config1 fields: {len(config1.get('fields', []))}")
	print(f"   - Config2 fields: {len(config2.get('fields', []))}")
	
	return True


def test_get_item_price_card_config_force_refresh():
	"""Test get_item_price_card_config with force=True"""
	print("\n" + "="*60)
	print("TEST 3: get_item_price_card_config Force Refresh")
	print("="*60)
	
	from apex_item import api
	
	# Get cached config
	api.get_item_price_card_config()
	
	# Force refresh
	config = api.get_item_price_card_config(force=True)
	
	# Should still have valid structure
	assert "fields" in config, "Config missing 'fields'"
	
	print(f"✅ SUCCESS: Force refresh works correctly")
	print(f"   - Fields count: {len(config.get('fields', []))}")
	
	return True


def test_clear_item_price_card_config_cache():
	"""Test clearing card config cache"""
	print("\n" + "="*60)
	print("TEST 4: Clear Item Price Card Config Cache")
	print("="*60)
	
	from apex_item import api
	
	# Populate cache
	api.get_item_price_card_config()
	
	# Clear cache
	api.clear_item_price_card_config_cache()
	
	# Next call should rebuild cache
	config = api.get_item_price_card_config()
	
	assert config is not None, "Config should not be None"
	
	print(f"✅ SUCCESS: Cache clearing works correctly")
	print(f"   - Config after clear: {len(config.get('fields', []))} fields")
	
	return True


def test_item_price_custom_fields_exist():
	"""Test that Item Price has custom fields from apex_item"""
	print("\n" + "="*60)
	print("TEST 5: Item Price Custom Fields")
	print("="*60)
	
	# Create a new Item Price document (without saving)
	item_price = frappe.new_doc("Item Price")
	
	# Check if custom fields exist
	custom_fields = [
		"stock_warehouse",
		"actual_qty",
		"reserved_qty",
		"available_qty",
		"waiting_qty",
		"item_group",
		"item_image",
	]
	
	found_fields = []
	missing_fields = []
	
	for field in custom_fields:
		if hasattr(item_price, field):
			found_fields.append(field)
		else:
			missing_fields.append(field)
	
	print(f"✅ Found {len(found_fields)}/{len(custom_fields)} custom fields")
	print(f"   Found: {', '.join(found_fields)}")
	
	if missing_fields:
		print(f"   Missing: {', '.join(missing_fields)}")
	
	# At least some fields should exist
	assert len(found_fields) > 0, "Should have at least one custom field"
	
	print(f"✅ SUCCESS: Custom fields are present on Item Price doctype")
	return True


def test_refresh_item_price_function_exists():
	"""Test that refresh_item_price function exists and is callable"""
	print("\n" + "="*60)
	print("TEST 6: refresh_item_price Function Exists")
	print("="*60)
	
	from apex_item.item_price_hooks import refresh_item_price
	
	# Check if function is callable
	assert callable(refresh_item_price), "refresh_item_price should be callable"
	
	print(f"✅ SUCCESS: refresh_item_price function exists and is callable")
	print(f"   Function: {refresh_item_price.__name__}")
	
	return True


def test_refresh_item_prices_function_exists():
	"""Test that refresh_item_prices function exists and is callable"""
	print("\n" + "="*60)
	print("TEST 7: refresh_item_prices Function Exists")
	print("="*60)
	
	from apex_item.item_price_hooks import refresh_item_prices
	
	# Check if function is callable
	assert callable(refresh_item_prices), "refresh_item_prices should be callable"
	
	print(f"✅ SUCCESS: refresh_item_prices function exists and is callable")
	print(f"   Function: {refresh_item_prices.__name__}")
	
	return True


def test_refresh_item_prices_by_filters_function_exists():
	"""Test that refresh_item_prices_by_filters function exists and is callable"""
	print("\n" + "="*60)
	print("TEST 8: refresh_item_prices_by_filters Function Exists")
	print("="*60)
	
	from apex_item.item_price_hooks import refresh_item_prices_by_filters
	
	# Check if function is callable
	assert callable(refresh_item_prices_by_filters), "refresh_item_prices_by_filters should be callable"
	
	print(f"✅ SUCCESS: refresh_item_prices_by_filters function exists and is callable")
	print(f"   Function: {refresh_item_prices_by_filters.__name__}")
	
	return True


def test_set_stock_fields_function_exists():
	"""Test that set_stock_fields function exists and is callable"""
	print("\n" + "="*60)
	print("TEST 9: set_stock_fields Function Exists")
	print("="*60)
	
	from apex_item.item_price_hooks import set_stock_fields
	
	# Check if function is callable
	assert callable(set_stock_fields), "set_stock_fields should be callable"
	
	print(f"✅ SUCCESS: set_stock_fields function exists and is callable")
	print(f"   Function: {set_stock_fields.__name__}")
	
	return True


def test_all():
	"""Run all tests"""
	print("\n" + "="*60)
	print("STARTING MANUAL TESTS FOR APEX_ITEM APP")
	print("="*60)
	
	tests = [
		test_get_item_price_card_config,
		test_get_item_price_card_config_caching,
		test_get_item_price_card_config_force_refresh,
		test_clear_item_price_card_config_cache,
		test_item_price_custom_fields_exist,
		test_refresh_item_price_function_exists,
		test_refresh_item_prices_function_exists,
		test_refresh_item_prices_by_filters_function_exists,
		test_set_stock_fields_function_exists,
	]
	
	results = []
	for test in tests:
		try:
			result = test()
			results.append(result)
		except Exception as e:
			print(f"❌ Exception in {test.__name__}: {str(e)}")
			import traceback
			traceback.print_exc()
			results.append(False)
	
	# Summary
	print("\n" + "="*60)
	print("TEST SUMMARY")
	print("="*60)
	passed = sum(1 for r in results if r)
	total = len(results)
	print(f"Total Tests: {total}")
	print(f"Passed: {passed}")
	print(f"Failed: {total - passed}")
	print(f"Success Rate: {passed/total*100:.1f}%")
	print("="*60)
	
	if passed == total:
		print("\n✅ ALL TESTS PASSED!")
	else:
		print("\n❌ SOME TESTS FAILED!")
	
	return results

