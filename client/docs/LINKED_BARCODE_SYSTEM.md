# Linked Barcode System Documentation

**Date:** October 20, 2025  
**API Schema:** http://10.100.10.156:5000/apispec_1.json  
**Status:** ✅ DOCUMENTED & IMPLEMENTED

## Overview

The Visual AOI Server implements a **linked barcode system** that transforms scanned barcodes into standardized format via an external linking API. This ensures consistent device identification and tracking across the system.

## API Schema Reference

### Inspection Endpoint

**POST** `/api/session/{session_id}/inspect`

### Barcode Processing Priority

The server processes barcodes in the following priority order:

| Priority | Source | Description | Status |
|----------|--------|-------------|--------|
| **0** | ROI with `is_device_barcode=true` | Scanned from image | **Linked** ✓ |
| **1** | Any barcode ROI (fallback) | Scanned from image | **Linked** ✓ |
| **2** | `device_barcodes` parameter | Manual input per device | **Linked** ✓ |
| **3** | `device_barcode` parameter (legacy) | Manual input for all devices | **Linked** ✓ |

**All barcodes are validated/transformed via external linking API:**
- **Endpoint:** `POST http://10.100.10.83:5000/api/ProcessLock/FA/GetLinkData`
- **Purpose:** Transform raw barcode to standardized format
- **Example:** `"1897848 S/N: 65514 3969 1006 V"` → `"1897848-0001555-118714"`

## Response Schema

### Device Summaries (Linked Barcodes)

```javascript
{
  "device_summaries": {
    "1": {
      "device_id": 1,
      "device_passed": true,
      "barcode": "1897848-0001555-118714",  // ← LINKED/VALIDATED barcode
      "passed_rois": 5,
      "total_rois": 5
    },
    "2": {
      "device_id": 2,
      "device_passed": false,
      "barcode": "2000354-8000003-1019720-101",  // ← LINKED/VALIDATED barcode
      "passed_rois": 4,
      "total_rois": 5
    }
  }
}
```

**Key Points:**
- ✅ `device_summaries[device_id]["barcode"]` is the **LINKED/VALIDATED** barcode
- ✅ Transformed by external API for standardization
- ✅ Use this field for device identification and tracking
- ✅ **Should be** a clean string (e.g., `"1897848-0001555-118714"`)
- ⚠️ May return as Python list string in legacy format: `"['1897848-0001555-118714']"`

### ROI Results (Original Scanned Barcodes)

```javascript
{
  "roi_results": [
    {
      "roi_id": 1,
      "roi_type_name": "barcode",
      "passed": true,
      "barcode_values": [
        "1897848 S/N: 65514 3969 1006 V"  // ← ORIGINAL SCANNED value
      ],
      "ai_similarity": 0.95
    },
    {
      "roi_id": 2,
      "roi_type_name": "compare",
      "passed": true,
      "ai_similarity": 0.87
    }
  ]
}
```

**Key Points:**
- ✅ `roi_results[]["barcode_values"]` contains **ORIGINAL SCANNED** values
- ✅ Already a proper JSON array (no cleaning needed)
- ✅ Preserved for audit trail and debugging
- ✅ Use `device_summaries[device_id]["barcode"]` for linked value

## Barcode Types

### 1. Linked Barcode (Device Level)

**Location:** `device_summaries[device_id]["barcode"]`

**Format:** Clean string (standardized)
```
"1897848-0001555-118714"
"20003548-0000003-1019720-101"
```

**Purpose:**
- Device identification
- Tracking and traceability
- Database lookups
- QA reporting

**Transformation Example:**
```
Input (Scanned):  "1897848 S/N: 65514 3969 1006 V"
                   ↓ (External API)
Output (Linked):  "1897848-0001555-118714"
```

### 2. Original Barcode (ROI Level)

**Location:** `roi_results[]["barcode_values"]`

**Format:** Array of strings (raw)
```javascript
["1897848 S/N: 65514 3969 1006 V"]
["20003548-0000003-1019720-101"]
["Barcode1", "Barcode2"]  // Multiple scans
```

**Purpose:**
- Audit trail
- Debugging
- Verification
- Raw data preservation

## Client Implementation

### Current cleanBarcode() Function

**File:** `templates/professional_index.html`

```javascript
// Clean barcode format - handles both linked and legacy formats
// API Schema Reference: http://10.100.10.156:5000/apispec_1.json
// 
// device_summaries[device_id]["barcode"]: LINKED/VALIDATED barcode (string)
//   - Transformed by external API
//   - Example: "1897848-0001555-118714"
//   - Should be clean string, but may come as Python list string in legacy format
//
// roi_results[]["barcode_values"]: ORIGINAL SCANNED barcodes (array)
//   - Raw scanned values from image
//   - Already proper JSON array (no cleaning needed)
//
function cleanBarcode(barcode) {
    if (!barcode || barcode === '-') return barcode;
    
    let cleaned = String(barcode).trim();
    
    // Handle legacy Python list string format: ['value'] -> value
    if (cleaned.startsWith('[') && cleaned.endsWith(']')) {
        cleaned = cleaned.slice(1, -1).trim();
        
        if ((cleaned.startsWith("'") && cleaned.endsWith("'")) ||
            (cleaned.startsWith('"') && cleaned.endsWith('"'))) {
            cleaned = cleaned.slice(1, -1);
        }
        
        if (cleaned.includes(',')) {
            cleaned = cleaned.split(',')[0].trim();
            if ((cleaned.startsWith("'") && cleaned.endsWith("'")) ||
                (cleaned.startsWith('"') && cleaned.endsWith('"'))) {
                cleaned = cleaned.slice(1, -1);
            }
        }
    }
    
    return cleaned;
}
```

### Usage in Client

#### 1. Device Cards - Display Linked Barcode

```javascript
const barcode = cleanBarcode(deviceData.barcode) || '-';
```

**Shows:** `"1897848-0001555-118714"` (Linked)

#### 2. Modal Header - Display Linked Barcode

```javascript
${deviceData.barcode ? `📱 Barcode: ${escapeHtml(cleanBarcode(deviceData.barcode))}` : ''}
```

**Shows:** `📱 Barcode: 1897848-0001555-118714` (Linked)

#### 3. ROI Details - Display Original Scanned Values

```javascript
${roi.barcode_values && roi.barcode_values.length > 0 ? `
    <div>
        <strong>Barcode:</strong>
        ${escapeHtml(roi.barcode_values.join(', '))}
    </div>
` : ''}
```

**Shows:** `Barcode: 1897848 S/N: 65514 3969 1006 V` (Original)

## External Linking API

### Endpoint Details

**URL:** `http://10.100.10.83:5000/api/ProcessLock/FA/GetLinkData`  
**Method:** POST  
**Purpose:** Transform raw barcode to standardized format

### Request Format

```json
{
  "barcode": "1897848 S/N: 65514 3969 1006 V"
}
```

### Response Format

```json
{
  "linked_barcode": "1897848-0001555-118714",
  "status": "success"
}
```

### Transformation Rules

The external API applies business logic to transform barcodes:

| Input Format | Output Format | Example |
|--------------|---------------|---------|
| `"1897848 S/N: 65514 3969 1006 V"` | `"1897848-0001555-118714"` | Format A |
| `"20003548-0000003-1019720-101"` | `"20003548-0000003-1019720-101"` | Already clean |
| Custom format | Standardized format | Various |

**Note:** Exact transformation logic is implemented by the external API server.

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Image Capture                                                 │
│    Camera captures image with barcode                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. Barcode Scanning (Server)                                    │
│    OCR/Barcode detection                                         │
│    Result: "1897848 S/N: 65514 3969 1006 V"                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. External Linking API Call                                    │
│    POST http://10.100.10.83:5000/api/ProcessLock/FA/GetLinkData│
│    Input:  "1897848 S/N: 65514 3969 1006 V"                     │
│    Output: "1897848-0001555-118714"                             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. Server Response                                               │
│    device_summaries[1]["barcode"] = "1897848-0001555-118714"   │
│    roi_results[0]["barcode_values"] = ["1897848 S/N: ..."]     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. Client Display                                                │
│    Device Card: "1897848-0001555-118714" (Linked)              │
│    ROI Detail: "1897848 S/N: 65514 3969 1006 V" (Original)     │
└─────────────────────────────────────────────────────────────────┘
```

## Why Two Barcode Fields?

### device_summaries[]["barcode"] (Linked)

**Purpose:** Standardized identification
- ✅ Consistent format across system
- ✅ Database-friendly format
- ✅ Easy to query and match
- ✅ Business logic applied

**Use Cases:**
- Device tracking
- QA reporting
- Database lookups
- Cross-reference with ERP/MES

### roi_results[]["barcode_values"] (Original)

**Purpose:** Audit trail and debugging
- ✅ Preserves raw scan data
- ✅ Debugging OCR issues
- ✅ Verification of transformation
- ✅ Compliance/traceability

**Use Cases:**
- Troubleshooting scan issues
- Verifying OCR accuracy
- Audit requirements
- Manual verification

## Legacy Format Handling

### Problem

Some server versions return linked barcode as Python list string:
```python
# Server returns (incorrect):
"barcode": "['1897848-0001555-118714']"

# Should return (correct):
"barcode": "1897848-0001555-118714"
```

### Solution

The `cleanBarcode()` function handles both formats:

```javascript
// Input: "['1897848-0001555-118714']"
// Output: "1897848-0001555-118714"

// Input: "1897848-0001555-118714"
// Output: "1897848-0001555-118714" (unchanged)
```

**Status:** ✅ Client handles both legacy and current formats

## Best Practices

### For Developers

1. **Always use linked barcode for identification:**
   ```javascript
   const linkedBarcode = cleanBarcode(deviceData.barcode);
   // Use linkedBarcode for tracking
   ```

2. **Display original for debugging:**
   ```javascript
   const originalBarcodes = roi.barcode_values;
   // Show originalBarcodes in detailed view
   ```

3. **Don't mix linked and original:**
   ```javascript
   // ❌ WRONG: Using original for device ID
   deviceId = roi.barcode_values[0];
   
   // ✅ CORRECT: Using linked for device ID
   deviceId = cleanBarcode(deviceData.barcode);
   ```

### For Users

1. **Device tracking:** Use the barcode shown in device card (linked)
2. **Verification:** Check ROI details to see original scanned value
3. **Reporting:** Reference linked barcode in reports and tickets

## Testing

### Test Cases

| Input Type | Input Value | Expected Output | Status |
|------------|-------------|-----------------|--------|
| Clean linked | `"1897848-0001555-118714"` | `"1897848-0001555-118714"` | ✅ |
| Legacy format | `"['1897848-0001555-118714']"` | `"1897848-0001555-118714"` | ✅ |
| Original array | `["1897848 S/N: 65514 3969 1006 V"]` | Display as-is | ✅ |
| Empty | `""` or `null` | `"-"` | ✅ |

### Verification Steps

1. **Scan barcode with spaces/special chars**
2. **Check device card shows linked format** (clean, standardized)
3. **Open modal and check ROI details show original format** (with spaces)
4. **Verify both formats are preserved in data**

## API Endpoints Reference

### Get API Schema

```bash
curl http://10.100.10.156:5000/apispec_1.json
```

### Inspect Endpoint

```bash
POST /api/session/{session_id}/inspect
```

**Request:**
```json
{
  "image_filename": "captured_305_1200.jpg",
  "device_barcodes": {
    "1": "1897848 S/N: 65514 3969 1006 V",
    "2": "20003548-0000003-1019720-101"
  }
}
```

**Response:**
```json
{
  "device_summaries": {
    "1": {
      "barcode": "1897848-0001555-118714",  // Linked
      "device_passed": true
    },
    "2": {
      "barcode": "20003548-0000003-1019720-101",  // Linked
      "device_passed": false
    }
  },
  "roi_results": [
    {
      "roi_id": 1,
      "barcode_values": ["1897848 S/N: 65514 3969 1006 V"]  // Original
    }
  ]
}
```

## Related Documentation

- **Barcode Format Fix:** `docs/BARCODE_FORMAT_FIX.md`
- **API Schema:** http://10.100.10.156:5000/apispec_1.json
- **Server Documentation:** Visual AOI Server docs

## Conclusion

The linked barcode system provides:
- ✅ **Standardized format** for device identification
- ✅ **External API integration** for transformation
- ✅ **Audit trail** via original barcode preservation
- ✅ **Flexibility** to handle various input formats
- ✅ **Traceability** from scan to standardized format

**Client implementation:** Fully compliant with API schema ✨

**Status:** Production-ready with comprehensive documentation ✓
