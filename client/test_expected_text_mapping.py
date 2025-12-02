#!/usr/bin/env python3
"""
Test script to verify expected_text field handling (consistent across client and server).
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Import from app.py
from app import roi_from_server_format, roi_to_server_format, normalize_roi


def test_server_to_client_mapping():
    """Test expected_text preserved from server to client"""
    print("\n" + "="*60)
    print("TEST 1: Server Format → Client Format")
    print("="*60)
    
    server_roi = {
        "idx": 5,
        "type": 3,  # OCR
        "coords": [100, 200, 300, 400],
        "device_location": 1,
        "focus": 305,
        "exposure": 1200,
        "feature_method": "opencv",
        "rotation": 0,
        "ai_threshold": 0.85,
        "expected_text": "Expected OCR Text",  # Server uses 'expected_text'
        "is_device_barcode": False
    }
    
    print("\nInput (Server Format):")
    print(f"  - expected_text: '{server_roi['expected_text']}'")
    
    client_roi = roi_from_server_format(server_roi)
    
    print("\nOutput (Client Format):")
    print(f"  - expected_text: '{client_roi.get('expected_text', 'NOT FOUND')}'")
    
    if 'expected_text' in client_roi and client_roi['expected_text'] == "Expected OCR Text":
        print("\n✅ PASS: expected_text correctly preserved")
        return True
    else:
        print("\n❌ FAIL: expected_text not found or incorrect")
        return False


def test_client_to_server_mapping():
    """Test expected_text preserved from client to server"""
    print("\n" + "="*60)
    print("TEST 2: Client Format → Server Format")
    print("="*60)
    
    client_roi = {
        "roi_id": 5,
        "roi_type_name": "text",
        "coordinates": [100, 200, 300, 400],
        "device_id": 1,
        "focus": 305,
        "exposure": 1200,
        "model": "opencv",
        "rotation": 0,
        "ai_threshold": 0.85,
        "expected_text": "PCB-V1.2",  # Client uses 'expected_text'
        "is_device_barcode": False,
        "enabled": True,
        "notes": ""
    }
    
    print("\nInput (Client Format):")
    print(f"  - expected_text: '{client_roi['expected_text']}'")
    
    server_roi = roi_to_server_format(client_roi)
    
    print("\nOutput (Server Format):")
    print(f"  - expected_text: '{server_roi.get('expected_text', 'NOT FOUND')}'")
    
    if 'expected_text' in server_roi and server_roi['expected_text'] == "PCB-V1.2":
        print("\n✅ PASS: expected_text correctly preserved")
        return True
    else:
        print("\n❌ FAIL: expected_text not found or incorrect")
        return False


def test_normalize_roi_with_expected_text_from_dict():
    """Test normalize_roi handles expected_text from dict format"""
    print("\n" + "="*60)
    print("TEST 3: normalize_roi() with expected_text")
    print("="*60)
    
    roi_with_expected_text = {
        "roi_id": 10,
        "roi_type_name": "ocr",
        "device_id": 2,
        "coordinates": [500, 600, 700, 800],
        "focus": 305,
        "exposure": 1200,
        "model": "easyocr",
        "expected_text": "Serial Number"
    }
    
    print("\nInput (has expected_text):")
    print(f"  - expected_text: '{roi_with_expected_text['expected_text']}'")
    
    normalized = normalize_roi(roi_with_expected_text, "test_product")
    
    print("\nOutput (normalized):")
    print(f"  - expected_text: '{normalized.get('expected_text', 'NOT FOUND')}'")
    
    if 'expected_text' in normalized and normalized['expected_text'] == "Serial Number":
        print("\n✅ PASS: expected_text preserved")
        return True
    else:
        print("\n❌ FAIL: expected_text not found or incorrect")
        return False


def test_normalize_roi_with_expected_text():
    """Test normalize_roi preserves expected_text"""
    print("\n" + "="*60)
    print("TEST 4: normalize_roi() with expected_text (client)")
    print("="*60)
    
    roi_with_expected_text = {
        "roi_id": 11,
        "roi_type_name": "text",
        "device_id": 3,
        "coordinates": [900, 1000, 1100, 1200],
        "focus": 305,
        "exposure": 1200,
        "model": "opencv",
        "expected_text": "Part ID"  # Client format field
    }
    
    print("\nInput (has expected_text):")
    print(f"  - expected_text: '{roi_with_expected_text['expected_text']}'")
    
    normalized = normalize_roi(roi_with_expected_text, "test_product")
    
    print("\nOutput (normalized):")
    print(f"  - expected_text: '{normalized.get('expected_text', 'NOT FOUND')}'")
    
    if 'expected_text' in normalized and normalized['expected_text'] == "Part ID":
        print("\n✅ PASS: expected_text preserved")
        return True
    else:
        print("\n❌ FAIL: expected_text not preserved")
        return False


def test_round_trip():
    """Test complete round-trip conversion"""
    print("\n" + "="*60)
    print("TEST 5: Round-Trip Conversion")
    print("="*60)
    
    original_text = "Test Round Trip"
    
    # Start with client format
    client_roi = {
        "roi_id": 20,
        "roi_type_name": "ocr",
        "coordinates": [1, 2, 3, 4],
        "device_id": 1,
        "focus": 305,
        "exposure": 1200,
        "model": "opencv",
        "rotation": 0,
        "ai_threshold": 0.8,
        "expected_text": original_text,
        "is_device_barcode": False,
        "enabled": True,
        "notes": ""
    }
    
    print(f"\n1. Client format: expected_text = '{client_roi['expected_text']}'")
    
    # Convert to server format
    server_roi = roi_to_server_format(client_roi)
    print(f"2. Server format: expected_text = '{server_roi.get('expected_text')}'")
    
    # Convert back to client format
    client_roi_back = roi_from_server_format(server_roi)
    print(f"3. Client format: expected_text = '{client_roi_back.get('expected_text')}'")
    
    if (server_roi.get('expected_text') == original_text and 
        client_roi_back.get('expected_text') == original_text):
        print("\n✅ PASS: Round-trip successful, text preserved")
        return True
    else:
        print("\n❌ FAIL: Text lost or corrupted in round-trip")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("EXPECTED_TEXT FIELD CONSISTENCY TESTS")
    print("="*60)
    print("\nVerifying expected_text field handling:")
    print("  - Client/UI uses: 'expected_text'")
    print("  - Server uses: 'expected_text' (consistent!)")
    
    results = []
    
    results.append(("Server → Client", test_server_to_client_mapping()))
    results.append(("Client → Server", test_client_to_server_mapping()))
    results.append(("normalize with expected_text (dict)", test_normalize_roi_with_expected_text_from_dict()))
    results.append(("normalize preserves expected_text", test_normalize_roi_with_expected_text()))
    results.append(("Round-trip conversion", test_round_trip()))
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ ALL TESTS PASSED - expected_text field handled consistently")
    else:
        print("❌ SOME TESTS FAILED - expected_text handling needs fixes")
    print("="*60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
