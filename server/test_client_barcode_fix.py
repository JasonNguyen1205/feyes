#!/usr/bin/env python3
"""
Quick test to verify client-provided barcode linking fix
Tests that device_barcodes parameter properly calls barcode linking
"""

import requests
import json

# Configuration
SERVER_URL = "http://10.100.27.156:5000"
PRODUCT_ID = "20003548"
TEST_BARCODE = "1897848 S/N: 65514 3969 1006 V"
EXPECTED_LINKED = "1897848-0001555-118714"  # Expected transformation

def test_client_barcode_linking():
    """Test that client-provided barcodes go through linking"""
    
    print("=" * 80)
    print("TESTING CLIENT-PROVIDED BARCODE LINKING FIX")
    print("=" * 80)
    
    # Step 1: Create a session
    print(f"\n1. Creating session for product: {PRODUCT_ID}")
    session_response = requests.post(
        f"{SERVER_URL}/api/session/create",
        json={"product_name": PRODUCT_ID}
    )
    
    if session_response.status_code != 200:
        print(f"❌ Failed to create session: {session_response.text}")
        return False
    
    session_data = session_response.json()
    session_id = session_data.get('session_id')
    print(f"✅ Session created: {session_id}")
    
    # Step 2: Run inspection with client-provided barcode
    print(f"\n2. Running inspection with device_barcodes parameter")
    print(f"   Input barcode: {TEST_BARCODE}")
    
    inspect_response = requests.post(
        f"{SERVER_URL}/api/session/{session_id}/inspect",
        json={
            "image_filename": "test_device.jpg",  # Dummy filename
            "device_barcodes": [
                {"device_id": 1, "barcode": TEST_BARCODE}
            ]
        }
    )
    
    if inspect_response.status_code != 200:
        print(f"❌ Inspection failed: {inspect_response.text}")
        return False
    
    result = inspect_response.json()
    
    # Step 3: Verify the barcode was linked
    print(f"\n3. Verifying barcode linking")
    device_summaries = result.get('device_summaries', {})
    
    if '1' not in device_summaries and 1 not in device_summaries:
        print(f"❌ Device 1 not found in device_summaries")
        print(f"   Available devices: {list(device_summaries.keys())}")
        return False
    
    # Try both string and int keys
    device_1 = device_summaries.get('1') or device_summaries.get(1)
    returned_barcode = device_1.get('barcode')
    
    print(f"   Returned barcode: {returned_barcode}")
    
    # Check if linking was applied
    if returned_barcode == TEST_BARCODE:
        print(f"❌ BARCODE NOT LINKED!")
        print(f"   Expected: {EXPECTED_LINKED}")
        print(f"   Got:      {returned_barcode}")
        print(f"\n   The barcode linking is NOT being applied to client-provided barcodes!")
        return False
    elif returned_barcode == EXPECTED_LINKED:
        print(f"✅ BARCODE LINKING SUCCESSFUL!")
        print(f"   Original: {TEST_BARCODE}")
        print(f"   Linked:   {returned_barcode}")
        return True
    else:
        print(f"⚠️  UNEXPECTED BARCODE VALUE")
        print(f"   Expected: {EXPECTED_LINKED}")
        print(f"   Got:      {returned_barcode}")
        print(f"   This may be a fallback value or different transformation")
        return False

if __name__ == "__main__":
    try:
        success = test_client_barcode_linking()
        print("\n" + "=" * 80)
        if success:
            print("✅ TEST PASSED: Client-provided barcode linking is working!")
        else:
            print("❌ TEST FAILED: Client-provided barcode linking is NOT working!")
        print("=" * 80)
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
