#!/usr/bin/env python3
"""
Test script to verify Color ROI v3.2 schema conversion between client and server formats.
"""

import sys
sys.path.insert(0, '/home/pi/visual-aoi-client')

from app import roi_to_server_format, roi_from_server_format

def test_color_roi_conversion():
    """Test color ROI conversion in both directions."""
    
    print("=" * 70)
    print("Color ROI v3.2 Schema Conversion Test")
    print("=" * 70)
    
    # Test 1: Client format → Server format (Simple format v3.2)
    print("\n1. Testing Client → Server Conversion (Simple Format)")
    print("-" * 70)
    
    client_roi = {
        'roi_id': 5,
        'roi_type_name': 'color',
        'coordinates': [100, 100, 300, 300],
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
    
    print("Client ROI Input:")
    for key, value in client_roi.items():
        print(f"  {key}: {value}")
    
    server_roi = roi_to_server_format(client_roi)
    
    print("\nServer ROI Output:")
    for key, value in server_roi.items():
        print(f"  {key}: {value}")
    
    # Verify color_config is wrapped
    assert 'color_config' in server_roi, "❌ Missing color_config in server format"
    assert 'expected_color' in server_roi['color_config'], "❌ Missing expected_color in color_config"
    assert server_roi['color_config']['expected_color'] == [255, 0, 0], "❌ expected_color mismatch"
    assert server_roi['color_config']['color_tolerance'] == 10, "❌ color_tolerance mismatch"
    assert server_roi['color_config']['min_pixel_percentage'] == 5.0, "❌ min_pixel_percentage mismatch"
    
    print("\n✅ Client → Server conversion: PASS")
    
    # Test 2: Server format → Client format (Unwrap color_config)
    print("\n2. Testing Server → Client Conversion")
    print("-" * 70)
    
    server_roi_with_color = {
        'idx': 5,
        'type': 4,
        'coords': [100, 100, 300, 300],
        'focus': 305,
        'exposure_time': 1200,
        'ai_threshold': None,
        'feature_method': 'color',
        'rotation': 0,
        'device_location': 1,
        'expected_text': None,
        'is_device_barcode': None,
        'color_config': {
            'expected_color': [0, 255, 0],      # Green
            'color_tolerance': 15,
            'min_pixel_percentage': 8.5
        }
    }
    
    print("Server ROI Input:")
    for key, value in server_roi_with_color.items():
        print(f"  {key}: {value}")
    
    client_roi_result = roi_from_server_format(server_roi_with_color)
    
    print("\nClient ROI Output:")
    for key, value in client_roi_result.items():
        print(f"  {key}: {value}")
    
    # Verify color_config is unwrapped
    assert 'expected_color' in client_roi_result, "❌ Missing expected_color in client format"
    assert 'color_tolerance' in client_roi_result, "❌ Missing color_tolerance in client format"
    assert 'min_pixel_percentage' in client_roi_result, "❌ Missing min_pixel_percentage in client format"
    assert client_roi_result['expected_color'] == [0, 255, 0], "❌ expected_color mismatch"
    assert client_roi_result['color_tolerance'] == 15, "❌ color_tolerance mismatch"
    assert client_roi_result['min_pixel_percentage'] == 8.5, "❌ min_pixel_percentage mismatch"
    
    print("\n✅ Server → Client conversion: PASS")
    
    # Test 3: Round-trip conversion
    print("\n3. Testing Round-Trip Conversion")
    print("-" * 70)
    
    original_client = {
        'roi_id': 10,
        'roi_type_name': 'color',
        'coordinates': [50, 50, 150, 150],
        'focus': 305,
        'exposure': 1200,
        'detection_method': 'color',
        'rotation': 0,
        'device_id': 2,
        'ai_threshold': None,
        'expected_color': [0, 0, 255],      # Blue
        'color_tolerance': 20,
        'min_pixel_percentage': 10.0
    }
    
    print("Original Client ROI:")
    print(f"  expected_color: {original_client['expected_color']}")
    print(f"  color_tolerance: {original_client['color_tolerance']}")
    print(f"  min_pixel_percentage: {original_client['min_pixel_percentage']}")
    
    # Client → Server
    server_intermediate = roi_to_server_format(original_client)
    print("\n→ Converted to Server Format")
    print(f"  color_config: {server_intermediate.get('color_config')}")
    
    # Server → Client
    final_client = roi_from_server_format(server_intermediate)
    print("\n→ Converted back to Client Format")
    print(f"  expected_color: {final_client['expected_color']}")
    print(f"  color_tolerance: {final_client['color_tolerance']}")
    print(f"  min_pixel_percentage: {final_client['min_pixel_percentage']}")
    
    # Verify round-trip preserves data
    assert final_client['expected_color'] == original_client['expected_color'], "❌ expected_color lost in round-trip"
    assert final_client['color_tolerance'] == original_client['color_tolerance'], "❌ color_tolerance lost in round-trip"
    assert final_client['min_pixel_percentage'] == original_client['min_pixel_percentage'], "❌ min_pixel_percentage lost in round-trip"
    
    print("\n✅ Round-trip conversion: PASS")
    
    # Test 4: Legacy format support (color_ranges)
    print("\n4. Testing Legacy Format (color_ranges) Support")
    print("-" * 70)
    
    server_roi_legacy = {
        'idx': 7,
        'type': 4,
        'coords': [200, 200, 400, 400],
        'focus': 305,
        'exposure_time': 1200,
        'ai_threshold': None,
        'feature_method': 'color',
        'rotation': 0,
        'device_location': 1,
        'expected_text': None,
        'is_device_barcode': None,
        'color_config': {
            'color_ranges': [
                {
                    'name': 'red',
                    'color_space': 'RGB',
                    'lower': [200, 0, 0],
                    'upper': [255, 50, 50],
                    'threshold': 5.0
                }
            ]
        }
    }
    
    print("Server ROI with Legacy color_ranges:")
    print(f"  color_config: {server_roi_legacy['color_config']}")
    
    client_roi_legacy = roi_from_server_format(server_roi_legacy)
    
    print("\nClient ROI Output:")
    print(f"  color_ranges: {client_roi_legacy.get('color_ranges')}")
    
    # Verify color_ranges preserved
    assert 'color_ranges' in client_roi_legacy, "❌ color_ranges not preserved"
    assert len(client_roi_legacy['color_ranges']) == 1, "❌ color_ranges count mismatch"
    
    print("\n✅ Legacy format support: PASS")
    
    print("\n" + "=" * 70)
    print("✅ ALL TESTS PASSED - Color ROI v3.2 schema conversion working!")
    print("=" * 70)

if __name__ == '__main__':
    try:
        test_color_roi_conversion()
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
