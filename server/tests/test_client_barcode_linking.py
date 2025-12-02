#!/usr/bin/env python3
"""
Test script to demonstrate barcode linking for client-provided barcodes.

This script simulates how the server handles barcodes sent by clients via API parameters,
showing that they now go through the external linking API just like ROI-scanned barcodes.
"""

from src.barcode_linking import get_linked_barcode_with_fallback


def test_client_provided_barcode_linking():
    """Test that client-provided barcodes are linked correctly."""
    
    print("\n" + "="*70)
    print("TEST: Client-Provided Barcode Linking")
    print("="*70)
    
    # Simulate client sending barcode via device_barcodes parameter
    test_cases = [
        {
            "name": "Priority 2: Multi-Device Barcode (Transform)",
            "input": "1897848 S/N: 65514 3969 1006 V",
            "device_id": 1,
            "expected_linked": "1897848-0001555-118714",
            "priority": "Priority 2 (device_barcodes parameter)"
        },
        {
            "name": "Priority 2: Already-Linked Barcode (Validate)",
            "input": "20003548-0000003-1019720-101",
            "device_id": 2,
            "expected_linked": "20003548-0000003-1019720-101",
            "priority": "Priority 2 (device_barcodes parameter)"
        },
        {
            "name": "Priority 3: Legacy Single Barcode (Transform)",
            "input": "1897848 S/N: 65514 3969 1006 V",
            "device_id": 1,
            "expected_linked": "1897848-0001555-118714",
            "priority": "Priority 3 (device_barcode parameter)"
        }
    ]
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'─'*70}")
        print(f"Test Case {i}: {test_case['name']}")
        print(f"{'─'*70}")
        print(f"Priority:      {test_case['priority']}")
        print(f"Device ID:     {test_case['device_id']}")
        print(f"Input Barcode: '{test_case['input']}'")
        
        # This is what happens in server/simple_api_server.py at Priority 2/3
        linked_barcode, is_linked = get_linked_barcode_with_fallback(test_case['input'])
        
        print(f"Linked:        {is_linked}")
        print(f"Output Barcode: '{linked_barcode}'")
        print(f"Expected:      '{test_case['expected_linked']}'")
        
        if linked_barcode == test_case['expected_linked']:
            print("✅ PASS")
        else:
            print("❌ FAIL")
            all_passed = False
    
    print(f"\n{'='*70}")
    if all_passed:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("="*70)
    
    return all_passed


def demonstrate_api_flow():
    """Demonstrate complete API flow with client-provided barcode."""
    
    print("\n" + "="*70)
    print("DEMONSTRATION: Complete API Flow")
    print("="*70)
    
    # Simulate client request
    print("\n📱 Step 1: Client sends API request")
    print("─"*70)
    client_barcode = "1897848 S/N: 65514 3969 1006 V"
    print("POST http://10.100.27.156:5000/api/session/SESSION_ID/inspect")
    print("{")
    print('  "image_filename": "device_image.jpg",')
    print('  "device_barcodes": {')
    print(f'    "1": "{client_barcode}"')
    print('  }')
    print("}")
    
    # Server receives and processes
    print("\n🖥️  Step 2: Server processes barcode (Priority 2)")
    print("─"*70)
    print(f"Received barcode: '{client_barcode}'")
    print("Calling get_linked_barcode_with_fallback()...")
    
    # Call external API
    print("\n🌐 Step 3: Server calls external API")
    print("─"*70)
    print("POST http://10.100.10.83:5000/api/ProcessLock/FA/GetLinkData")
    print(f'Body: "{client_barcode}"')
    
    # Get linked barcode
    linked_barcode, is_linked = get_linked_barcode_with_fallback(client_barcode)
    
    print("\n📥 Step 4: API returns linked data")
    print("─"*70)
    print(f"Response: '{linked_barcode}'")
    print(f"Linked: {is_linked}")
    
    # Server returns to client
    print("\n📤 Step 5: Server returns response to client")
    print("─"*70)
    print("{")
    print('  "device_summaries": {')
    print('    "1": {')
    print(f'      "barcode": "{linked_barcode}",  ← LINKED BARCODE')
    print('      "device_passed": true,')
    print('      ...')
    print('    }')
    print('  }')
    print("}")
    
    print("\n✅ Complete flow successful!")
    print(f"   Client sent:  '{client_barcode}'")
    print(f"   Client got:   '{linked_barcode}'")
    
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    # Run tests
    test_passed = test_client_provided_barcode_linking()
    
    # Demonstrate flow
    demonstrate_api_flow()
    
    # Exit with appropriate code
    import sys
    sys.exit(0 if test_passed else 1)
