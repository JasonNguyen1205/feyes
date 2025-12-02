#!/usr/bin/env python3
"""
Test barcode linking functionality with the external API.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.barcode_linking import (
    get_linked_barcode,
    get_linked_barcode_with_fallback,
    set_barcode_link_enabled
)


def test_barcode_linking():
    """Test barcode linking with real API."""
    print("=" * 60)
    print("Barcode Linking API Test")
    print("=" * 60)
    
    # Test cases
    test_barcodes = [
        "20003548-0000003-1019720-101",  # Valid barcode from your example
        "INVALID-BARCODE-12345",         # Invalid barcode
        "",                               # Empty barcode
        "TEST123",                        # Another test barcode
    ]
    
    for barcode in test_barcodes:
        print(f"\n{'─' * 60}")
        print(f"Testing barcode: '{barcode}'")
        print(f"{'─' * 60}")
        
        # Test get_linked_barcode
        linked = get_linked_barcode(barcode)
        if linked:
            print(f"✅ Linked data: {linked}")
        else:
            print(f"❌ Linking failed (will use original)")
        
        # Test get_linked_barcode_with_fallback
        result, is_linked = get_linked_barcode_with_fallback(barcode)
        print(f"\nFallback result:")
        print(f"  - Barcode to use: {result}")
        print(f"  - Is linked: {is_linked}")
        print(f"  - Status: {'✅ SUCCESS' if is_linked else '⚠️ FALLBACK'}")
    
    print("\n" + "=" * 60)
    print("Test complete")
    print("=" * 60)


def test_enable_disable():
    """Test enabling/disabling barcode linking."""
    print("\n" + "=" * 60)
    print("Testing Enable/Disable Functionality")
    print("=" * 60)
    
    test_barcode = "20003548-0000003-1019720-101"
    
    # Test with linking enabled
    print("\n1. Linking ENABLED:")
    set_barcode_link_enabled(True)
    result, is_linked = get_linked_barcode_with_fallback(test_barcode)
    print(f"   Result: {result}, Linked: {is_linked}")
    
    # Test with linking disabled
    print("\n2. Linking DISABLED:")
    set_barcode_link_enabled(False)
    result, is_linked = get_linked_barcode_with_fallback(test_barcode)
    print(f"   Result: {result}, Linked: {is_linked}")
    
    # Re-enable for other tests
    set_barcode_link_enabled(True)
    print("\n3. Linking RE-ENABLED:")
    result, is_linked = get_linked_barcode_with_fallback(test_barcode)
    print(f"   Result: {result}, Linked: {is_linked}")


if __name__ == "__main__":
    try:
        # Run tests
        test_barcode_linking()
        test_enable_disable()
        
        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
