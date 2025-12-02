#!/usr/bin/env python3
"""
Test script to verify ROI loading returns client-friendly format for UI display.
"""

import requests
import json
import sys

CLIENT_URL = "http://localhost:5000"
TEST_PRODUCT = "20003548"


def test_load_config_format():
    """Test that GET /api/products/{product}/config returns client format."""
    print(f"\n{'='*60}")
    print("TEST: Load ROI Configuration via Client Proxy")
    print(f"{'='*60}")
    
    url = f"{CLIENT_URL}/api/products/{TEST_PRODUCT}/config"
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            rois = data.get('rois', [])
            print(f"✅ Retrieved {len(rois)} ROIs")
            
            if not rois:
                print("⚠️  No ROIs in response")
                return False
            
            # Check first ROI has client format fields
            roi = rois[0]
            print(f"\nFirst ROI structure:")
            print(json.dumps(roi, indent=2))
            
            # Verify client format fields exist
            required_fields = ['roi_id', 'roi_type_name', 'coordinates', 'device_id']
            missing_fields = [f for f in required_fields if f not in roi]
            
            if missing_fields:
                print(f"\n❌ FAILED: Missing client format fields: {missing_fields}")
                return False
            
            # Check field types
            checks = [
                (isinstance(roi.get('roi_id'), int), "roi_id should be int"),
                (isinstance(roi.get('roi_type_name'), str), "roi_type_name should be string"),
                (isinstance(roi.get('coordinates'), list), "coordinates should be list"),
                (len(roi.get('coordinates', [])) == 4, "coordinates should have 4 values"),
                (isinstance(roi.get('device_id'), int), "device_id should be int"),
            ]
            
            all_passed = True
            for passed, msg in checks:
                status = "✅" if passed else "❌"
                print(f"{status} {msg}")
                if not passed:
                    all_passed = False
            
            if all_passed:
                print(f"\n✅ SUCCESS: ROI format is client-friendly and ready for UI display")
                print(f"\nROI Summary:")
                print(f"  - ROI ID: {roi.get('roi_id')}")
                print(f"  - Type: {roi.get('roi_type_name')}")
                print(f"  - Device: {roi.get('device_id')}")
                print(f"  - Coordinates: {roi.get('coordinates')}")
                return True
            else:
                print(f"\n❌ FAILED: Some format checks failed")
                return False
            
        else:
            print(f"❌ FAILED: Status {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run test."""
    print("\n" + "="*60)
    print("ROI DISPLAY FORMAT VERIFICATION")
    print("="*60)
    print(f"Client: {CLIENT_URL}")
    print(f"Product: {TEST_PRODUCT}")
    print(f"\nNote: Client app must be running on port 5000")
    
    test_passed = test_load_config_format()
    
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"ROI Load Format Test: {'✅ PASS' if test_passed else '❌ FAIL'}")
    print("="*60)
    
    return 0 if test_passed else 1


if __name__ == "__main__":
    sys.exit(main())
