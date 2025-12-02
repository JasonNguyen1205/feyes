#!/usr/bin/env python3
"""
Test script to verify the endpoint fix for ROI configuration.
Tests both GET and POST to /api/products/<product>/rois endpoint.
"""

import requests
import json
import sys

SERVER_URL = "http://10.100.27.156:5000"
TEST_PRODUCT = "20003548"


def test_get_rois():
    """Test GET /api/products/{product}/rois endpoint."""
    print(f"\n{'='*60}")
    print("TEST 1: GET /api/products/{product}/rois")
    print(f"{'='*60}")
    
    url = f"{SERVER_URL}/api/products/{TEST_PRODUCT}/rois"
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            rois = data.get('rois', [])
            print(f"✅ SUCCESS: Retrieved {len(rois)} ROIs")
            
            if rois:
                roi = rois[0]
                print(f"\nFirst ROI structure:")
                print(f"  - idx: {roi.get('idx')}")
                print(f"  - type: {roi.get('type')}")
                print(f"  - coords: {roi.get('coords')}")
                print(f"  - device_location: {roi.get('device_location')}")
            return True
        else:
            print(f"❌ FAILED: Status {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def test_post_rois():
    """Test POST /api/products/{product}/rois endpoint."""
    print(f"\n{'='*60}")
    print("TEST 2: POST /api/products/{product}/rois")
    print(f"{'='*60}")
    
    # First get current ROIs
    url_get = f"{SERVER_URL}/api/products/{TEST_PRODUCT}/rois"
    response = requests.get(url_get, timeout=10)
    
    if response.status_code != 200:
        print(f"❌ Cannot get current ROIs: {response.status_code}")
        return False
    
    current_rois = response.json().get('rois', [])
    print(f"Current ROI count: {len(current_rois)}")
    
    # Create test payload (save same ROIs back)
    test_payload = {'rois': current_rois}
    
    url_post = f"{SERVER_URL}/api/products/{TEST_PRODUCT}/rois"
    print(f"URL: {url_post}")
    print(f"Payload: {{'rois': [{len(current_rois)} items]}}")
    
    try:
        response = requests.post(
            url_post,
            json=test_payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS: {result.get('message', 'Saved')}")
            return True
        else:
            print(f"❌ FAILED: Status {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("ROI ENDPOINT FIX VERIFICATION")
    print("="*60)
    print(f"Server: {SERVER_URL}")
    print(f"Product: {TEST_PRODUCT}")
    
    test1 = test_get_rois()
    test2 = test_post_rois()
    
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"GET  /api/products/{{product}}/rois: {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"POST /api/products/{{product}}/rois: {'✅ PASS' if test2 else '❌ FAIL'}")
    print(f"\nOverall: {'✅ ALL TESTS PASSED' if test1 and test2 else '❌ SOME TESTS FAILED'}")
    print("="*60)
    
    return 0 if (test1 and test2) else 1


if __name__ == "__main__":
    sys.exit(main())
