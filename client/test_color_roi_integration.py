#!/usr/bin/env python3
"""
Integration test: Create a complete color ROI configuration and validate it.
"""

import sys
import json
sys.path.insert(0, '/home/pi/visual-aoi-client')

from app import roi_to_server_format, validate_roi

def test_color_roi_validation():
    """Test complete color ROI configuration validation."""
    
    print("=" * 70)
    print("Color ROI Configuration Validation Test")
    print("=" * 70)
    
    # Create a complete product configuration with color ROI
    product_config = {
        'product_name': 'test_product_with_color',
        'rois': [
            {
                'roi_id': 1,
                'roi_type_name': 'barcode',
                'coordinates': [50, 50, 200, 100],
                'focus': 305,
                'exposure': 1200,
                'detection_method': 'barcode',
                'rotation': 0,
                'device_id': 1,
                'ai_threshold': None,
                'is_device_barcode': True
            },
            {
                'roi_id': 2,
                'roi_type_name': 'compare',
                'coordinates': [250, 50, 400, 200],
                'focus': 305,
                'exposure': 1200,
                'detection_method': 'mobilenet',
                'rotation': 0,
                'device_id': 1,
                'ai_threshold': 0.85
            },
            {
                'roi_id': 3,
                'roi_type_name': 'ocr',
                'coordinates': [450, 50, 600, 100],
                'focus': 305,
                'exposure': 1200,
                'detection_method': 'ocr',
                'rotation': 0,
                'device_id': 1,
                'ai_threshold': None,
                'expected_text': 'PCB'
            },
            {
                'roi_id': 4,
                'roi_type_name': 'color',
                'coordinates': [50, 150, 200, 300],
                'focus': 305,
                'exposure': 1200,
                'detection_method': 'color',
                'rotation': 0,
                'device_id': 1,
                'ai_threshold': None,
                'expected_color': [255, 0, 0],      # Red
                'color_tolerance': 10,
                'min_pixel_percentage': 5.0
            }
        ]
    }
    
    print("\n1. Product Configuration with 4 ROI Types:")
    print("-" * 70)
    for roi in product_config['rois']:
        print(f"  ROI {roi['roi_id']}: {roi['roi_type_name']}")
    
    # Validate each ROI
    print("\n2. Validating Configuration:")
    print("-" * 70)
    
    all_valid = True
    all_errors = []
    for roi in product_config['rois']:
        is_valid, errors = validate_roi(roi, 'client')
        if is_valid:
            print(f"  ✅ ROI {roi['roi_id']} ({roi['roi_type_name']}): Valid")
        else:
            print(f"  ❌ ROI {roi['roi_id']} ({roi['roi_type_name']}): Validation failed")
            all_valid = False
            all_errors.extend(errors)
            for error in errors:
                print(f"    - {error}")
    
    assert all_valid, f"Configuration validation failed: {all_errors}"
    
    # Convert all ROIs to server format
    print("\n3. Converting to Server Format:")
    print("-" * 70)
    
    server_rois = []
    for client_roi in product_config['rois']:
        server_roi = roi_to_server_format(client_roi)
        server_rois.append(server_roi)
        
        print(f"\n  ROI {server_roi['idx']} (Type {server_roi['type']}):")
        if server_roi['type'] == 4:
            print(f"    color_config: {server_roi.get('color_config')}")
        else:
            print(f"    feature_method: {server_roi['feature_method']}")
    
    # Verify color ROI has color_config
    color_roi = next((roi for roi in server_rois if roi['type'] == 4), None)
    assert color_roi is not None, "Color ROI not found in server format"
    assert 'color_config' in color_roi, "color_config missing from color ROI"
    assert color_roi['color_config']['expected_color'] == [255, 0, 0], "expected_color mismatch"
    
    print("\n4. Server Format Verification:")
    print("-" * 70)
    print(f"  ✅ Color ROI (idx={color_roi['idx']}) properly formatted")
    print(f"  ✅ color_config present: {color_roi['color_config']}")
    
    # Pretty print the complete server ROI config
    print("\n5. Complete Server Configuration (JSON):")
    print("-" * 70)
    server_config = {
        'product_name': product_config['product_name'],
        'rois': server_rois
    }
    print(json.dumps(server_config, indent=2))
    
    print("\n" + "=" * 70)
    print("✅ ALL VALIDATION TESTS PASSED")
    print("=" * 70)
    print("\nReady to POST to server:")
    print(f"  POST http://10.100.27.156:5000/api/products/test_product_with_color/config")
    print(f"  Body: {json.dumps(server_config, indent=2)[:200]}...")

if __name__ == '__main__':
    try:
        test_color_roi_validation()
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
