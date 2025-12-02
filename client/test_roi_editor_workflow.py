#!/usr/bin/env python3
"""
Test ROI Editor Workflow - Add, Modify, Delete, Save
Tests the complete workflow from client UI to server storage
"""

import json
import sys
sys.path.insert(0, '/home/jason_nguyen/visual-aoi-client')

from app import (
    roi_from_server_format,
    roi_to_server_format,
    normalize_roi,
    validate_roi
)


def test_add_roi_workflow():
    """Test adding a new ROI (simulating canvas draw)"""
    print("\n" + "="*60)
    print("TEST 1: Add ROI Workflow")
    print("="*60)
    
    # Simulate createROI() from roi_editor.js
    new_roi = {
        'roi_id': 1,
        'roi_type_name': 'barcode',
        'device_id': 1,
        'coordinates': [100, 200, 300, 400],
        'ai_threshold': 0.8,
        'focus': 305,
        'exposure': 1200,
        'model': 'opencv',
        'rotation': 0,
        'enabled': True,
        'notes': 'Test barcode ROI'
    }
    
    print(f"✅ Created new ROI in client format:")
    print(f"   ROI ID: {new_roi['roi_id']}")
    print(f"   Type: {new_roi['roi_type_name']}")
    print(f"   Coordinates: {new_roi['coordinates']}")
    
    # Validate
    is_valid, errors = validate_roi(new_roi, format_type='client')
    if is_valid:
        print(f"✅ ROI validation: PASS")
    else:
        print(f"❌ ROI validation: FAIL - {errors}")
        return False
    
    # Convert to server format for saving
    server_roi = roi_to_server_format(new_roi)
    print(f"✅ Converted to server format:")
    print(f"   idx: {server_roi['idx']}")
    print(f"   type: {server_roi['type']}")
    print(f"   coords: {server_roi['coords']}")
    print(f"   device_location: {server_roi['device_location']}")
    
    # Validate server format
    is_valid, errors = validate_roi(server_roi, format_type='server')
    if is_valid:
        print(f"✅ Server format validation: PASS")
    else:
        print(f"❌ Server format validation: FAIL - {errors}")
        return False
    
    return True


def test_modify_roi_workflow():
    """Test modifying an existing ROI"""
    print("\n" + "="*60)
    print("TEST 2: Modify ROI Workflow")
    print("="*60)
    
    # Start with an existing ROI
    roi = {
        'roi_id': 1,
        'roi_type_name': 'barcode',
        'device_id': 1,
        'coordinates': [100, 200, 300, 400],
        'ai_threshold': 0.8,
        'focus': 305,
        'exposure': 1200,
        'model': 'opencv',
        'rotation': 0,
        'enabled': True,
        'notes': ''
    }
    
    print(f"📝 Original ROI:")
    print(f"   Type: {roi['roi_type_name']}")
    print(f"   Device: {roi['device_id']}")
    print(f"   Threshold: {roi['ai_threshold']}")
    
    # Simulate updateROIProperty() from roi_editor.js
    roi['roi_type_name'] = 'ocr'  # Change type
    roi['device_id'] = 2  # Change device
    roi['ai_threshold'] = 0.9  # Change threshold
    roi['notes'] = 'Updated to OCR type'
    
    print(f"✏️  Modified ROI:")
    print(f"   Type: {roi['roi_type_name']}")
    print(f"   Device: {roi['device_id']}")
    print(f"   Threshold: {roi['ai_threshold']}")
    print(f"   Notes: {roi['notes']}")
    
    # Validate modified ROI
    is_valid, errors = validate_roi(roi, format_type='client')
    if is_valid:
        print(f"✅ Modified ROI validation: PASS")
    else:
        print(f"❌ Modified ROI validation: FAIL - {errors}")
        return False
    
    # Simulate updateCoordinates()
    roi['coordinates'] = [150, 250, 350, 450]
    print(f"📐 Updated coordinates: {roi['coordinates']}")
    
    # Convert to server format
    server_roi = roi_to_server_format(roi)
    print(f"✅ Converted to server format: type={server_roi['type']}, device_location={server_roi['device_location']}")
    
    return True


def test_delete_roi_workflow():
    """Test deleting an ROI"""
    print("\n" + "="*60)
    print("TEST 3: Delete ROI Workflow")
    print("="*60)
    
    # Simulate editorState.rois array
    rois = [
        {'roi_id': 1, 'roi_type_name': 'barcode', 'device_id': 1, 'coordinates': [100, 200, 300, 400], 'ai_threshold': 0.8, 'focus': 305, 'exposure': 1200, 'enabled': True, 'notes': ''},
        {'roi_id': 2, 'roi_type_name': 'ocr', 'device_id': 1, 'coordinates': [400, 200, 600, 400], 'ai_threshold': 0.8, 'focus': 305, 'exposure': 1200, 'enabled': True, 'notes': ''},
        {'roi_id': 3, 'roi_type_name': 'compare', 'device_id': 2, 'coordinates': [100, 500, 300, 700], 'ai_threshold': 0.8, 'focus': 305, 'exposure': 1200, 'enabled': True, 'notes': ''}
    ]
    
    print(f"📋 ROI list before delete: {len(rois)} ROIs")
    for roi in rois:
        print(f"   - ROI {roi['roi_id']}: {roi['roi_type_name']} (device {roi['device_id']})")
    
    # Simulate deleteSelectedROI() - delete ROI 2
    selected_roi = rois[1]  # ROI 2
    print(f"\n🗑️  Deleting ROI {selected_roi['roi_id']} ({selected_roi['roi_type_name']})")
    
    rois.remove(selected_roi)
    
    print(f"📋 ROI list after delete: {len(rois)} ROIs")
    for roi in rois:
        print(f"   - ROI {roi['roi_id']}: {roi['roi_type_name']} (device {roi['device_id']})")
    
    if len(rois) == 2:
        print(f"✅ Delete operation: SUCCESS")
    else:
        print(f"❌ Delete operation: FAIL - Expected 2 ROIs, got {len(rois)}")
        return False
    
    return True


def test_save_to_server_workflow():
    """Test saving configuration to server (conversion)"""
    print("\n" + "="*60)
    print("TEST 4: Save to Server Workflow")
    print("="*60)
    
    # Simulate editor state with multiple ROIs
    client_rois = [
        {
            'roi_id': 1,
            'roi_type_name': 'barcode',
            'device_id': 1,
            'coordinates': [100, 200, 300, 400],
            'ai_threshold': 0.8,
            'focus': 305,
            'exposure': 1200,
            'model': 'opencv',
            'rotation': 0,
            'enabled': True,
            'notes': 'Device barcode',
            'is_device_barcode': True
        },
        {
            'roi_id': 2,
            'roi_type_name': 'ocr',
            'device_id': 1,
            'coordinates': [400, 200, 600, 400],
            'ai_threshold': 0.85,
            'focus': 305,
            'exposure': 1200,
            'model': 'tesseract',
            'rotation': 0,
            'enabled': True,
            'notes': 'Serial number'
        },
        {
            'roi_id': 3,
            'roi_type_name': 'compare',
            'device_id': 2,
            'coordinates': [100, 500, 300, 700],
            'ai_threshold': 0.9,
            'focus': 310,
            'exposure': 1000,
            'model': 'opencv',
            'rotation': 0,
            'enabled': True,
            'notes': 'Component check'
        }
    ]
    
    print(f"📤 Preparing to save {len(client_rois)} ROIs to server")
    
    # Step 1: Validate all ROIs (client format)
    print(f"\n1️⃣  Validating client format ROIs...")
    validation_errors = []
    for i, roi in enumerate(client_rois):
        is_valid, errors = validate_roi(roi, format_type='client')
        if not is_valid:
            validation_errors.extend([f"ROI {i+1}: {err}" for err in errors])
    
    if validation_errors:
        print(f"❌ Validation failed: {validation_errors}")
        return False
    print(f"✅ All ROIs valid (client format)")
    
    # Step 2: Convert to server format
    print(f"\n2️⃣  Converting to server format...")
    server_rois = []
    for roi in client_rois:
        server_roi = roi_to_server_format(roi)
        server_rois.append(server_roi)
        print(f"   ROI {roi['roi_id']}: {roi['roi_type_name']} → type={server_roi['type']}, idx={server_roi['idx']}")
    
    print(f"✅ Converted {len(server_rois)} ROIs to server format")
    
    # Step 3: Validate server format
    print(f"\n3️⃣  Validating server format ROIs...")
    for i, roi in enumerate(server_rois):
        is_valid, errors = validate_roi(roi, format_type='server')
        if not is_valid:
            print(f"❌ Server ROI {i+1} validation failed: {errors}")
            return False
    print(f"✅ All ROIs valid (server format)")
    
    # Step 4: Show server payload
    print(f"\n4️⃣  Server payload preview:")
    print(json.dumps(server_rois[0], indent=2))
    
    print(f"\n✅ Ready to send to server: POST /api/products/{{product}}/config")
    print(f"   Payload: Array of {len(server_rois)} server-format ROIs")
    
    return True


def test_load_from_server_workflow():
    """Test loading configuration from server (conversion)"""
    print("\n" + "="*60)
    print("TEST 5: Load from Server Workflow")
    print("="*60)
    
    # Simulate server response (server format)
    server_response = [
        {
            'idx': 1,
            'type': 1,  # barcode
            'coords': [100, 200, 300, 400],
            'focus': 305,
            'exposure': 1200,
            'ai_threshold': None,
            'feature_method': 'opencv',
            'rotation': 0,
            'device_location': 1,
            'sample_text': None,
            'is_device_barcode': None
        },
        {
            'idx': 2,
            'type': 3,  # ocr
            'coords': [400, 200, 600, 400],
            'focus': 305,
            'exposure': 1200,
            'ai_threshold': 0.85,
            'feature_method': 'tesseract',
            'rotation': 0,
            'device_location': 1,
            'sample_text': None,
            'is_device_barcode': False
        }
    ]
    
    print(f"📥 Received {len(server_response)} ROIs from server (server format)")
    
    # Convert to client format
    print(f"\n🔄 Converting to client format...")
    client_rois = []
    for server_roi in server_response:
        client_roi = roi_from_server_format(server_roi)
        client_rois.append(client_roi)
        print(f"   idx={server_roi['idx']}, type={server_roi['type']} → ROI {client_roi['roi_id']}: {client_roi['roi_type_name']}")
    
    print(f"✅ Converted {len(client_rois)} ROIs to client format")
    
    # Validate converted ROIs
    print(f"\n✅ Validating converted ROIs...")
    for roi in client_rois:
        is_valid, errors = validate_roi(roi, format_type='client')
        if not is_valid:
            print(f"❌ Validation failed for ROI {roi['roi_id']}: {errors}")
            return False
    
    print(f"✅ All converted ROIs valid")
    
    # Show client format
    print(f"\n📋 Client format preview:")
    print(f"   ROI {client_rois[0]['roi_id']}: {client_rois[0]['roi_type_name']}")
    print(f"   Device: {client_rois[0]['device_id']}")
    print(f"   Coordinates: {client_rois[0]['coordinates']}")
    print(f"   AI Threshold: {client_rois[0]['ai_threshold']}")
    print(f"   Model: {client_rois[0]['model']}")
    
    return True


def run_all_tests():
    """Run all workflow tests"""
    print("\n" + "🧪"*30)
    print("ROI EDITOR WORKFLOW TEST SUITE")
    print("🧪"*30)
    
    tests = [
        ("Add ROI", test_add_roi_workflow),
        ("Modify ROI", test_modify_roi_workflow),
        ("Delete ROI", test_delete_roi_workflow),
        ("Save to Server", test_save_to_server_workflow),
        ("Load from Server", test_load_from_server_workflow)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ TEST EXCEPTION: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! ROI editor workflow is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the errors above.")
        return 1


if __name__ == '__main__':
    exit_code = run_all_tests()
    sys.exit(exit_code)
