# Server-Side Implementation Instructions for Barcode Logic Update
## Date: October 3, 2025

## Overview
The client has been updated to handle device barcode inputs more intelligently. The barcode input panel now only shows for devices that do NOT have barcode ROIs defined in their configuration. This document provides instructions for implementing the corresponding server-side changes.

## Client Changes Summary

### What Was Changed on Client:
1. **Session Creation Response**: Now expects `devices_need_barcode` array
2. **Barcode Panel Logic**: Only shows when `devices_need_barcode.length > 0`
3. **Sequential Scanning**: Implements disable/enable/focus flow for one-at-a-time scanning
4. **Device Analysis**: Client expects server to analyze ROI groups and identify devices without barcode ROIs

## Required Server-Side Changes

### 1. Update Session Creation Endpoint

**File**: Server's session creation handler (typically `create_session` or similar)

**Required Changes**:

```python
def create_session(product_name: str) -> dict:
    """
    Create a new inspection session.
    
    UPDATED: Must now analyze ROI groups and return devices_need_barcode list.
    """
    # ... existing session creation logic ...
    
    # NEW: Analyze which devices need manual barcode input
    roi_groups = load_roi_groups(product_name)
    devices_need_barcode = analyze_devices_needing_barcodes(roi_groups)
    
    return {
        "session_id": session_id,
        "product": product_name,
        "roi_groups_count": len(roi_groups),
        "devices_need_barcode": devices_need_barcode  # NEW FIELD
    }
```

### 2. Implement Device Barcode Analysis Function

**Purpose**: Determine which devices lack barcode ROIs

**Logic**:
- Scan all ROI groups for the product
- Track which devices have barcode ROIs (roi_type = 1 or roi_type_name = "barcode")
- Return list of device IDs that have NO barcode ROIs

**Implementation Example**:

```python
def analyze_devices_needing_barcodes(roi_groups: dict) -> list[int]:
    """
    Analyze ROI groups to determine which devices need manual barcode input.
    
    UPDATED October 3, 2025: Now checks is_device_barcode field to distinguish
    main barcodes from auxiliary barcodes (serial numbers, QR codes, etc.).
    
    A device needs manual barcode input if it has NO MAIN barcode ROIs defined.
    
    Args:
        roi_groups: Dictionary of ROI groups from product config
        Format: {
            "focus,exposure": {
                "focus": int,
                "exposure": int,
                "rois": [
                    {"id": int, "device": int, "type": str, "is_device_barcode": bool, ...},
                    # OR array format: [id, type, bbox, focus, exp, golden, name, thresh, device, expected, is_main]
                    ...
                ]
            },
            ...
        }
        
    Returns:
        List of device IDs (integers) that need manual barcode input
        
    Examples:
        - Device 1 has main barcode ROI → NOT in list
        - Device 2 has auxiliary barcode only → IN list [2] (no main barcode)
        - Device 3 has compare/OCR ROIs only → IN list [3]
    """
    device_has_main_barcode = {}  # {device_id: bool}
    
    # Analyze all ROI groups
    for group_key, group_data in roi_groups.items():
        if not isinstance(group_data, dict) or 'rois' not in group_data:
            continue
            
        rois = group_data.get('rois', [])
        for roi in rois:
            if not isinstance(roi, dict):
                continue
                
            # Handle both dict and array formats
            if isinstance(roi, dict):
                # Dictionary format
                device_id = roi.get('device', 1)
                roi_type = (
                    roi.get('type') or 
                    roi.get('roi_type') or 
                    roi.get('roi_type_name')
                )
                is_barcode = roi_type in ['barcode', 1, '1']
                # NEW: Check is_device_barcode field (defaults to True for backward compatibility)
                is_main = roi.get('is_device_barcode', True)
            elif isinstance(roi, list):
                # Array format: [id, type, bbox, focus, exp, golden, name, thresh, device, expected, is_main]
                device_id = roi[8] if len(roi) > 8 else 1
                roi_type = roi[1] if len(roi) > 1 else None
                is_barcode = roi_type in [1, '1'] or (len(roi) > 6 and roi[6] == 'barcode')
                # NEW: Check field [10] for is_device_barcode (defaults to True for backward compatibility)
                is_main = roi[10] if len(roi) > 10 else True
            else:
                continue
            
            # Initialize device tracking
            if device_id not in device_has_main_barcode:
                device_has_main_barcode[device_id] = False
            
            # NEW: Only mark device as having barcode if it's a MAIN barcode
            if is_barcode and is_main:
                device_has_main_barcode[device_id] = True
    
    # Return devices that do NOT have MAIN barcode ROIs
    devices_need_manual = [
        dev_id 
        for dev_id, has_barcode in device_has_main_barcode.items() 
        if not has_barcode
    ]
    
    logger.info(
        f"Device barcode analysis: {len(device_has_barcode)} total devices, "
        f"{len(devices_need_manual)} need manual input: {devices_need_manual}"
    )
    
    return sorted(devices_need_manual)
```

### 3. Update ROI Groups Loading (if needed)

**File**: ROI groups loader/parser

**Verify**:
- ROI data includes device ID field
- ROI type field is properly set (1 for barcode or "barcode" string)
- ROI structure matches expected format

**Expected ROI Structure**:

```python
# From JSON config file
roi_groups = {
    "305,1200": {
        "focus": 305,
        "exposure": 1200,
        "rois": [
            {
                "id": 1,
                "device": 1,              # Device this ROI belongs to
                "type": "barcode",        # or roi_type: 1
                "bbox": [x1, y1, x2, y2],
                # ... other fields
            },
            {
                "id": 2,
                "device": 2,
                "type": "compare",        # Not a barcode
                # ...
            }
        ]
    }
}
```

### 4. Update Inspection Endpoint (Important!)

**File**: Inspection/capture handler

**Required Changes**:

The inspection endpoint must now handle TWO sources of barcodes:

1. **Manual barcodes**: From client barcode input panel (devices_need_barcode)
2. **Scanned barcodes**: From barcode ROIs during inspection

**Implementation Strategy**:

```python
def perform_inspection(session_id: str, device_barcodes: list[dict]) -> dict:
    """
    Perform inspection with manual barcode support.
    
    Args:
        device_barcodes: Manual barcodes from client
            Format: [{"device_id": 1, "barcode": "ABC123"}, ...]
    """
    # Get session and ROI groups
    session = get_session(session_id)
    roi_groups = load_roi_groups(session.product)
    
    # Collect manual barcodes by device
    manual_barcodes = {
        entry["device_id"]: entry["barcode"] 
        for entry in device_barcodes
    }
    
    # Perform capture and inspection
    results = {}
    for device_id in get_all_device_ids(roi_groups):
        device_result = {
            "device_id": device_id,
            "rois": [],
            "barcode": None,
            "pass": True
        }
        
        # Check if this device has manual barcode
        if device_id in manual_barcodes:
            device_result["barcode"] = manual_barcodes[device_id]
            device_result["barcode_source"] = "manual"
        
        # Capture and process ROIs for this device
        for roi in get_device_rois(roi_groups, device_id):
            roi_result = process_roi(roi, captured_image)
            
            # If this is a barcode ROI, use scanned result
            if roi.type == "barcode" and roi_result.get("barcode"):
                device_result["barcode"] = roi_result["barcode"]
                device_result["barcode_source"] = "scanned"
            
            device_result["rois"].append(roi_result)
        
        results[device_id] = device_result
    
    return results
```

**Key Points**:
- Manual barcodes are used for devices without barcode ROIs
- Scanned barcodes override manual input (if ROI exists)
- Track barcode source ("manual" vs "scanned") for debugging

### 5. Backward Compatibility

**Important**: Ensure backward compatibility with existing clients

```python
def create_session_response(session_id, product, roi_groups):
    """Generate session response with backward compatibility."""
    response = {
        "session_id": session_id,
        "product": product,
        "roi_groups_count": len(roi_groups)
    }
    
    # NEW FIELD - old clients will ignore this
    try:
        response["devices_need_barcode"] = analyze_devices_needing_barcodes(roi_groups)
    except Exception as e:
        logger.warning(f"Failed to analyze devices needing barcodes: {e}")
        response["devices_need_barcode"] = []
    
    return response
```

## Testing Requirements

### Test Case 1: All Devices Have Barcode ROIs
**Setup**: Product with barcode ROIs for all devices
**Expected**:
- `devices_need_barcode` = []
- Client does NOT show barcode input panel
- Inspection uses only scanned barcodes

### Test Case 2: Some Devices Need Manual Barcodes
**Setup**: Product where Device 1 has barcode ROI, Device 2 does not
**Expected**:
- `devices_need_barcode` = [2]
- Client shows panel with input for Device 2 only
- Inspection merges: Device 1 scanned, Device 2 manual

### Test Case 3: All Devices Need Manual Barcodes
**Setup**: Product with no barcode ROIs
**Expected**:
- `devices_need_barcode` = [1, 2, 3, ...]
- Client shows panel with all device inputs
- Inspection uses only manual barcodes

### Test Case 4: Sequential Scanning Flow
**Setup**: 3 devices need manual barcodes [1, 2, 3]
**Expected Client Behavior**:
1. Only Device 1 input enabled
2. User scans → Device 1 disabled, Device 2 enabled
3. User scans → Device 2 disabled, Device 3 enabled  
4. User scans → All complete, inspection auto-triggered

## API Contract

### Session Creation Response

```typescript
interface SessionResponse {
    session_id: string;
    product: string;
    roi_groups_count: number;
    devices_need_barcode: number[];  // NEW FIELD
}
```

### Inspection Request

```typescript
interface InspectionRequest {
    device_barcodes: Array<{
        device_id: number;
        barcode: string;
    }>;
}
```

**Note**: `device_barcodes` array will only contain entries for devices in `devices_need_barcode` list.

## Migration Path

### Phase 1: Server Updates (Do First)
1. Add `analyze_devices_needing_barcodes()` function
2. Update session creation to return `devices_need_barcode`
3. Update inspection to handle manual barcodes
4. Test with existing client (should still work)

### Phase 2: Client Deployment
1. Deploy updated client with new logic
2. Client will start using `devices_need_barcode` field
3. Old behavior (show all devices) will stop

### Phase 3: Validation
1. Test various product configurations
2. Verify barcode sources are correctly tracked
3. Validate inspection results match expected behavior

## Common Issues and Solutions

### Issue 1: ROI Type Field Name Inconsistency
**Problem**: ROI type stored as different field names across products
**Solution**: Check multiple possible field names (type, roi_type, roi_type_name)

### Issue 2: Device ID Missing
**Problem**: Some ROIs don't have device field
**Solution**: Default to device ID = 1 if not specified

### Issue 3: Empty ROI Groups
**Problem**: Product has no ROI groups defined
**Solution**: Return empty array `[]` for devices_need_barcode

### Issue 4: Manual and Scanned Conflict
**Problem**: Both manual and scanned barcode exist for same device
**Solution**: Scanned barcode takes precedence (ROI-based is more reliable)

## Performance Considerations

- `analyze_devices_needing_barcodes()` runs once per session creation
- Minimal performance impact (simple dictionary traversal)
- Cache result if product config doesn't change during session

## Security Considerations

- Validate device IDs in manual barcode list match session's device IDs
- Sanitize barcode input strings
- Log barcode source for audit trail

## Logging Recommendations

```python
# At session creation
logger.info(f"Session {session_id}: {len(devices_need_barcode)} devices need manual barcodes: {devices_need_barcode}")

# At inspection
logger.info(f"Inspection {session_id}: Received {len(manual_barcodes)} manual barcodes")
for device_id, barcode in manual_barcodes.items():
    logger.debug(f"  Device {device_id}: {barcode} (manual)")
```

## Summary Checklist

Server-side implementation checklist:

- [ ] Add `analyze_devices_needing_barcodes()` function
- [ ] Update session creation endpoint to return `devices_need_barcode`
- [ ] Update inspection endpoint to accept and merge manual barcodes
- [ ] Add tests for all device barcode scenarios
- [ ] Verify ROI type field names are correctly checked
- [ ] Implement barcode source tracking (manual vs scanned)
- [ ] Add appropriate logging
- [ ] Update API documentation
- [ ] Test backward compatibility with old clients
- [ ] Deploy and validate with updated client

## Questions or Issues

Contact: Development Team
Reference: BARCODE_INPUT_PANEL.md (client-side implementation)
