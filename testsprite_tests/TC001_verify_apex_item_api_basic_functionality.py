import requests

BASE_URL = "http://localhost:8000"
API_KEY = "your_api_key"
API_SECRET = "your_api_secret"
TIMEOUT = 30

def test_verify_apex_item_api_basic_functionality():
    session = requests.Session()
    headers = {
        "Content-Type": "application/json",
        "api_key": API_KEY,
        "api_secret": API_SECRET
    }
    
    # Test creating apex_item document (POST)
    create_url = f"{BASE_URL}/api/resource/apex_item"
    new_apex_item = {
        "item_code": "TEST-ITEM-001",
        "item_name": "Test Apex Item",
        "description": "Item created during automated test",
    }
    create_resp = session.post(create_url, json=new_apex_item, timeout=TIMEOUT, headers=headers)
    assert create_resp.status_code == 200 or create_resp.status_code == 201, f"Create apex_item failed: {create_resp.text}"
    create_data = create_resp.json()
    apex_item_name = create_data.get("data", {}).get("name")
    assert apex_item_name, "Create apex_item response missing document name/id"
    
    try:
        # Retrieve apex_item document (GET)
        get_url = f"{BASE_URL}/api/resource/apex_item/{apex_item_name}"
        get_resp = session.get(get_url, timeout=TIMEOUT, headers=headers)
        assert get_resp.status_code == 200, f"Get apex_item failed: {get_resp.text}"
        get_data = get_resp.json()
        assert get_data.get("data", {}).get("item_name") == "Test Apex Item"
        
        # Update apex_item document (PUT)
        update_url = get_url
        update_payload = {"description": "Updated description via test"}
        update_resp = session.put(update_url, json=update_payload, timeout=TIMEOUT, headers=headers)
        assert update_resp.status_code == 200, f"Update apex_item failed: {update_resp.text}"
        updated_data = update_resp.json()
        assert updated_data.get("data", {}).get("description") == "Updated description via test"
        
        # Test stock calculation function endpoint if exposed via API
        stock_calc_url = f"{BASE_URL}/api/method/apex_item.calculate_stock"
        params = {"item_code": "TEST-ITEM-001"}
        stock_resp = session.get(stock_calc_url, params=params, timeout=TIMEOUT, headers=headers)
        if stock_resp.status_code == 200:
            stock_data = stock_resp.json()
            assert "message" in stock_data or "data" in stock_data, "Stock calculation response malformed"
        else:
            assert stock_resp.status_code in [404, 400], "Unexpected status for stock calculation endpoint"
        
        # Test integration with ERPNext modules endpoint, for example item's stock ledger entries
        stock_ledger_url = f"{BASE_URL}/api/resource/Stock Ledger Entry"
        params = {"item_code": "TEST-ITEM-001", "limit_page_length": 1}
        sle_resp = session.get(stock_ledger_url, params=params, timeout=TIMEOUT, headers=headers)
        assert sle_resp.status_code == 200, f"Stock Ledger Entry lookup failed: {sle_resp.text}"
        sle_data = sle_resp.json()
        assert "data" in sle_data, "Stock Ledger Entry response missing data"
        
        # Test document event handler simulation (e.g., on_update API call if exists)
        event_url = f"{BASE_URL}/api/method/apex_item.handle_doc_event"
        event_payload = {"docname": apex_item_name, "event": "on_update"}
        event_resp = session.post(event_url, json=event_payload, timeout=TIMEOUT, headers=headers)
        assert event_resp.status_code in (200, 404), f"Doc event handler response status unexpected: {event_resp.text}"
        
        # Test error handling by requesting non-existent apex_item
        bad_get_url = f"{BASE_URL}/api/resource/apex_item/INVALID-ID-NOT-EXIST"
        bad_get_resp = session.get(bad_get_url, timeout=TIMEOUT, headers=headers)
        assert bad_get_resp.status_code == 404, f"Expected 404 for non-existent apex_item, got {bad_get_resp.status_code}"
        
    finally:
        # Clean up - delete created apex_item document
        if apex_item_name:
            delete_url = f"{BASE_URL}/api/resource/apex_item/{apex_item_name}"
            delete_resp = session.delete(delete_url, timeout=TIMEOUT, headers=headers)
            assert delete_resp.status_code in (200, 204, 404), f"Delete apex_item failed: {delete_resp.text}"

test_verify_apex_item_api_basic_functionality()
