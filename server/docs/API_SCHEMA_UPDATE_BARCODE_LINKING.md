# API Schema Update - Barcode Linking Documentation

**Date**: October 20, 2025  
**Status**: ✅ Complete  
**Impact**: Documentation update for client developers

---

## Overview

Updated the Swagger/OpenAPI schema for the `/api/session/{session_id}/inspect` endpoint to clearly document the barcode linking behavior for client-side developers.

### What Changed

Added comprehensive documentation to the API schema explaining:

1. How barcode parameters are processed (priority order)
2. External API validation/transformation
3. Where to find linked barcodes in the response
4. Complete request/response examples

---

## Updated API Documentation

### Request Parameters

#### `device_barcode` (string)

```yaml
type: string
description: |
  (LEGACY) Single barcode applied to all devices.
  Priority 3: Used only if no ROI barcode detected.
  NOTE: Barcode will be validated/transformed via external API.
  Example: "1897848 S/N: 65514 3969 1006 V" → "1897848-0001555-118714"
```

#### `device_barcodes` (object)

```yaml
type: object
description: |
  (RECOMMENDED) Dictionary mapping device IDs to barcodes.
  Priority 2: Used only if no ROI barcode detected for that device.
  NOTE: All barcodes will be validated/transformed via external API.
  Supports both dict format {"1": "barcode"} and list format
  [{"device_id": 1, "barcode": "..."}].
  Example: {"1": "1897848 S/N: 65514 3969 1006 V"}
  Returns: {"1": {"barcode": "1897848-0001555-118714"}}
additionalProperties:
  type: string
```

### Barcode Processing Note

```yaml
note: |
  Either image_filename (preferred) or image (legacy) must be provided.
  
  BARCODE PROCESSING (Priority Order):
  - Priority 0: ROI with is_device_barcode=true (scanned from image) → Linked
  - Priority 1: Any barcode ROI (fallback) → Linked
  - Priority 2: device_barcodes parameter (manual input) → Linked
  - Priority 3: device_barcode parameter (legacy) → Linked
  
  All barcodes are validated/transformed via external linking API:
  POST http://10.100.10.83:5000/api/ProcessLock/FA/GetLinkData
  
  The linked barcode is returned in device_summaries[device_id]["barcode"].
  Original scanned barcode (if any) is preserved in roi_results[]["barcode_values"].
```

---

## Response Schema Updates

### `roi_results` Array

```yaml
roi_results:
  type: array
  description: |
    Individual ROI inspection results.
    For barcode ROIs, barcode_values contains original scanned data.
  items:
    type: object
    properties:
      roi_id:
        type: integer
      roi_type_name:
        type: string
      passed:
        type: boolean
      barcode_values:
        type: array
        description: |
          Original barcode values scanned from ROI (if barcode ROI).
          Note: This is the raw scanned value, NOT the linked barcode.
          Use device_summaries[device_id]["barcode"] for linked value.
        items:
          type: string
```

### `device_summaries` Object

```yaml
device_summaries:
  type: object
  description: |
    Summary per device with linked barcodes.
    Key is device ID (e.g., "1", "2"), value is device summary object.
  additionalProperties:
    type: object
    properties:
      device_id:
        type: integer
      barcode:
        type: string
        description: |
          LINKED/VALIDATED barcode for this device.
          This is the transformed barcode from external API.
          Example: "1897848-0001555-118714"
          Use this field for device identification/tracking.
      device_passed:
        type: boolean
      passed_rois:
        type: integer
      total_rois:
        type: integer
```

---

## Complete Example

### Request

```json
POST /api/session/d34614ce-104e-4f31-8bbc-2402134fbc6a/inspect
Content-Type: application/json

{
  "image_filename": "device_image.jpg",
  "device_barcodes": {
    "1": "1897848 S/N: 65514 3969 1006 V"
  }
}
```

### Response

```json
{
  "roi_results": [
    {
      "roi_id": 3,
      "roi_type_name": "barcode",
      "passed": true,
      "barcode_values": [
        "1897848 S/N: 65514 3969 1006 V"
      ]
    }
  ],
  "device_summaries": {
    "1": {
      "device_id": 1,
      "barcode": "1897848-0001555-118714",
      "device_passed": true,
      "passed_rois": 17,
      "total_rois": 17
    }
  },
  "overall_result": {
    "passed": true,
    "total_rois": 17,
    "passed_rois": 17,
    "failed_rois": 0
  },
  "processing_time": 2.45
}
```

### Key Observation

```
Client Sent:     "1897848 S/N: 65514 3969 1006 V"
                              ↓
                    External API Linking
                              ↓
Server Returned: "1897848-0001555-118714"
```

**Notice**: The barcode was transformed by the external API. Always use `device_summaries[device_id]["barcode"]` for device tracking/identification.

---

## Visual Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ Client Request                                              │
│ POST /api/session/{id}/inspect                             │
│                                                             │
│ {                                                           │
│   "image_filename": "device.jpg",                          │
│   "device_barcodes": {                                     │
│     "1": "1897848 S/N: 65514 3969 1006 V"  ← Original     │
│   }                                                         │
│ }                                                           │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ Server Processing                                           │
│                                                             │
│ 1. Receive barcode: "1897848 S/N: 65514 3969 1006 V"      │
│ 2. Call external API:                                      │
│    POST http://10.100.10.83:5000/api/ProcessLock/FA/...   │
│ 3. Get linked barcode: "1897848-0001555-118714"           │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ Server Response                                             │
│                                                             │
│ {                                                           │
│   "roi_results": [                                         │
│     {                                                       │
│       "barcode_values": [                                  │
│         "1897848 S/N: 65514 3969 1006 V"  ← Original (audit)
│       ]                                                     │
│     }                                                       │
│   ],                                                        │
│   "device_summaries": {                                    │
│     "1": {                                                 │
│       "barcode": "1897848-0001555-118714"  ← Linked (USE!) │
│     }                                                       │
│   }                                                         │
│ }                                                           │
└─────────────────────────────────────────────────────────────┘
```

---

## Client Implementation Guide

### ✅ Correct Usage

```python
# Send request with barcode
response = requests.post(
    'http://server:5000/api/session/SESSION_ID/inspect',
    json={
        'image_filename': 'device.jpg',
        'device_barcodes': {
            '1': '1897848 S/N: 65514 3969 1006 V'
        }
    }
)

result = response.json()

# ✅ CORRECT: Use linked barcode from device_summaries
linked_barcode = result['device_summaries']['1']['barcode']
print(f"Device Barcode: {linked_barcode}")
# Output: Device Barcode: 1897848-0001555-118714

# Store this value in database, display to user, etc.
save_to_database(device_id=1, barcode=linked_barcode)
```

### ❌ Incorrect Usage

```python
# ❌ WRONG: Reading from roi_results (original value)
original_barcode = result['roi_results'][0]['barcode_values'][0]
print(f"Device Barcode: {original_barcode}")
# Output: Device Barcode: 1897848 S/N: 65514 3969 1006 V

# This is the ORIGINAL scanned value, not the linked one!
# Don't use this for device identification.
```

---

## Accessing the Documentation

### Swagger UI

1. Start the server:

   ```bash
   ./start_server.sh
   ```

2. Open browser to:

   ```
   http://10.100.27.156:5000/apidocs/
   ```

3. Find the endpoint:

   ```
   POST /api/session/{session_id}/inspect
   ```

4. Expand to see full documentation including:
   - Parameter descriptions
   - Barcode processing priority order
   - External API linking information
   - Request/response examples

### OpenAPI JSON Spec

Download the complete API specification:

```bash
curl http://10.100.27.156:5000/apispec_1.json > visual-aoi-api.json
```

Use with:

- Postman (import OpenAPI spec)
- Swagger Editor (<https://editor.swagger.io/>)
- OpenAPI Generator (generate client SDKs)
- API testing tools

---

## What Clients Need to Know

### 1. Barcode Transformation is Automatic

When you send a barcode via `device_barcodes` or `device_barcode`, it automatically goes through the external linking API. You don't need to call the linking API yourself.

### 2. Use the Right Field

**Always read from**: `device_summaries[device_id]["barcode"]`  
**Don't read from**: `roi_results[]["barcode_values"]` (audit only)

### 3. Priority Order Matters

If you both:

- Scan a barcode from the image (ROI)
- Send a barcode via parameters

The ROI-scanned barcode takes priority. Your parameter barcode is used as fallback.

### 4. Graceful Fallback

If the external linking API fails (timeout, connection error, returns "null"):

- The system falls back to the original barcode
- Inspection continues normally
- Check logs for linking errors

### 5. Both Formats Supported

```python
# Dict format (recommended)
{"device_barcodes": {"1": "barcode", "2": "barcode"}}

# List format (alternative)
{"device_barcodes": [
    {"device_id": 1, "barcode": "barcode"},
    {"device_id": 2, "barcode": "barcode"}
]}
```

---

## Testing the API

### Quick Test with cURL

```bash
# Create session
SESSION_ID=$(curl -X POST "http://10.100.27.156:5000/api/session/create" \
  -H "Content-Type: application/json" \
  -d '{"product_name": "20003548"}' | jq -r '.session_id')

# Run inspection with barcode
curl -X POST "http://10.100.27.156:5000/api/session/$SESSION_ID/inspect" \
  -H "Content-Type: application/json" \
  -d '{
    "image_filename": "test.jpg",
    "device_barcodes": {
      "1": "1897848 S/N: 65514 3969 1006 V"
    }
  }' | jq '.device_summaries["1"].barcode'

# Expected output: "1897848-0001555-118714"
```

### Test with Python

```python
import requests

# Create session
response = requests.post(
    'http://10.100.27.156:5000/api/session/create',
    json={'product_name': '20003548'}
)
session_id = response.json()['session_id']

# Run inspection
response = requests.post(
    f'http://10.100.27.156:5000/api/session/{session_id}/inspect',
    json={
        'image_filename': 'test.jpg',
        'device_barcodes': {
            '1': '1897848 S/N: 65514 3969 1006 V'
        }
    }
)

# Check linked barcode
result = response.json()
linked_barcode = result['device_summaries']['1']['barcode']
print(f"Linked Barcode: {linked_barcode}")
# Output: Linked Barcode: 1897848-0001555-118714
```

---

## Migration Checklist for Existing Clients

- [ ] Review current code that reads barcode from API response
- [ ] Update to read from `device_summaries[device_id]["barcode"]` instead of `roi_results[]["barcode_values"]`
- [ ] Test with various barcode formats (original, already-linked, invalid)
- [ ] Update any barcode validation/format checking logic
- [ ] Update UI displays to show linked barcode format
- [ ] Update database schema if needed (barcode field length, format)
- [ ] Test error handling (API timeout, connection failure)
- [ ] Update integration tests with new response structure
- [ ] Document the change in your client-side code comments
- [ ] Update any API mocking/testing fixtures

---

## FAQ

### Q: Do I need to change my client code?

**A**: If you're already reading from `device_summaries[device_id]["barcode"]`, no changes needed. If you were reading from `roi_results[]["barcode_values"]`, you should update to use the linked barcode.

### Q: What if I don't want barcode linking?

**A**: The feature is always enabled, but if the external API fails, the system gracefully falls back to the original barcode. You can disable it server-side by calling `set_barcode_link_enabled(False)` in the barcode_linking module.

### Q: Can I send a barcode that's already linked?

**A**: Yes! The external API validates already-linked barcodes and returns them unchanged. Example: `"20003548-0000003-1019720-101"` → `"20003548-0000003-1019720-101"`

### Q: What happens if my barcode is invalid?

**A**: The external API returns "null" for invalid barcodes, and the system falls back to your original barcode. The inspection continues normally.

### Q: How do I know if a barcode was linked or fell back?

**A**: Check the server logs. You'll see either:

- `[Priority X] Using linked barcode: ORIGINAL -> LINKED`
- `[Priority X] Using barcode: ORIGINAL (linking not applied)`

---

## Summary

✅ **Updated**: Swagger/OpenAPI documentation for `/api/session/{id}/inspect`  
✅ **Added**: Barcode linking behavior documentation  
✅ **Added**: Request/response examples with barcode transformation  
✅ **Added**: Clear guidance on which field to use  
✅ **Result**: Client developers now have complete documentation on barcode linking

**Next Steps**: Review the updated API documentation at `http://10.100.27.156:5000/apidocs/` and update client code accordingly.
