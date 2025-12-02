# Inspection Result Structure Specification

**Version:** 2.0  
**Last Updated:** October 3, 2025  
**Status:** OFFICIAL SPECIFICATION - ALL CODE MUST COMPLY

---

## 🎯 Purpose

This document is the **single source of truth** for inspection result structure returned to clients after image processing. All API endpoints that return inspection results **MUST** follow this specification exactly.

**⚠️ CRITICAL:** When the result structure changes, this document MUST be updated FIRST before any code changes.

---

## 📋 Table of Contents

1. [Result Structure Overview](#result-structure-overview)
2. [Top-Level Result Object](#top-level-result-object)
3. [ROI Results Array](#roi-results-array)
4. [Device Summaries Object](#device-summaries-object)
5. [Overall Result Object](#overall-result-object)
6. [Processing Metadata](#processing-metadata)
7. [Error Response Format](#error-response-format)
8. [API Endpoint Responses](#api-endpoint-responses)
9. [Validation Rules](#validation-rules)
10. [Implementation Requirements](#implementation-requirements)
11. [Change Management](#change-management)

---

## 📐 Result Structure Overview

### Canonical Format

```json
{
  "roi_results": [...],           // Array of individual ROI processing results
  "device_summaries": {...},      // Dictionary of per-device summary statistics
  "overall_result": {...},        // Overall inspection pass/fail and statistics
  "processing_time": 1.234,       // Processing duration in seconds
  "timestamp": 1696348800.123     // Unix timestamp (optional)
}
```

### Visual Hierarchy

```
Inspection Result
├── roi_results[]              (Individual ROI details)
│   ├── ROI 1 (Device 1)
│   ├── ROI 2 (Device 1)
│   ├── ROI 3 (Device 2)
│   └── ROI 4 (Device 2)
├── device_summaries{}         (Per-device aggregation)
│   ├── Device 1 Summary
│   └── Device 2 Summary
├── overall_result{}           (Global aggregation)
└── processing_time           (Performance metric)
```

---

## 📦 Top-Level Result Object

### Structure ⚠️ **CRITICAL**

```typescript
interface InspectionResult {
  roi_results: ROIResult[];           // REQUIRED - Array of ROI results
  device_summaries: DeviceSummaries;  // REQUIRED - Device-grouped summaries
  overall_result: OverallResult;      // REQUIRED - Global pass/fail
  processing_time: number;            // REQUIRED - Seconds (float)
  timestamp?: number;                 // OPTIONAL - Unix timestamp
  session_id?: string;                // OPTIONAL - Session UUID
  product_name?: string;              // OPTIONAL - Product identifier
  group_results?: GroupResults;       // OPTIONAL - For grouped inspection
}
```

### Field Specifications

#### `roi_results` (REQUIRED)
- **Type:** Array of ROIResult objects
- **Description:** Individual processing results for each ROI
- **Constraints:**
  - Must be an array (can be empty for no ROIs)
  - Order should match ROI processing order
  - Each element must be valid ROIResult object
- **Usage:** Detailed per-ROI inspection data

#### `device_summaries` (REQUIRED)
- **Type:** Object (dictionary) with integer keys
- **Description:** Summary statistics grouped by device_location
- **Constraints:**
  - Keys are device IDs (integers 1-4 as strings)
  - Values are DeviceSummary objects
  - Must include all devices that have ROIs
- **Usage:** Per-device pass/fail determination

#### `overall_result` (REQUIRED)
- **Type:** OverallResult object
- **Description:** Aggregate inspection statistics
- **Constraints:**
  - Must include passed, total_rois, passed_rois, failed_rois
  - Counts must be consistent with roi_results
- **Usage:** Overall inspection pass/fail decision

#### `processing_time` (REQUIRED)
- **Type:** Number (float)
- **Unit:** Seconds
- **Description:** Total inspection processing duration
- **Constraints:**
  - Must be non-negative
  - Includes image decoding + ROI processing + aggregation
- **Usage:** Performance monitoring

#### `timestamp` (OPTIONAL)
- **Type:** Number (float)
- **Unit:** Unix timestamp (seconds since epoch)
- **Description:** When inspection completed
- **Usage:** Logging and correlation

#### `session_id` (OPTIONAL)
- **Type:** String (UUID format)
- **Description:** Session identifier for grouped inspections
- **Usage:** Tracking multiple inspections in same session

#### `product_name` (OPTIONAL)
- **Type:** String
- **Description:** Product configuration name used
- **Usage:** Result tracking and reporting

---

## 🔍 ROI Results Array

### ROI Result Object Structure

```typescript
interface ROIResult {
  // Common fields (ALL ROI types)
  roi_id: number;                    // REQUIRED - ROI index (1-based)
  device_id: number;                 // REQUIRED - Device location (1-4)
  roi_type_name: string;             // REQUIRED - "barcode"|"compare"|"ocr"
  passed: boolean;                   // REQUIRED - Pass/fail status
  coordinates: [number, number, number, number];  // REQUIRED - [x1, y1, x2, y2]
  
  // Optional common fields
  roi_image?: string;                // OPTIONAL - Base64 encoded ROI image
  golden_image?: string;             // OPTIONAL - Base64 encoded golden image
  error?: string;                    // OPTIONAL - Error message if failed
  
  // Type-specific fields (see below)
  // ... barcode_values, match_result, ocr_text, etc.
}
```

### Type-Specific Fields

#### Barcode ROI (Type 1) ⚠️ **CRITICAL**

```typescript
interface BarcodeROIResult extends ROIResult {
  roi_type_name: "barcode";
  barcode_values: string[];          // REQUIRED - Array of detected barcodes
  passed: boolean;                   // true if any barcode detected
}
```

**Example:**
```json
{
  "roi_id": 1,
  "device_id": 1,
  "roi_type_name": "barcode",
  "passed": true,
  "coordinates": [50, 50, 150, 100],
  "barcode_values": ["ABC123456"],
  "roi_image": "data:image/jpeg;base64,/9j/4AAQ..."
}
```

**Field Rules:**
- `barcode_values` MUST be array (even if empty)
- Empty array `[]` means no barcode detected (failed)
- Multiple values possible if multiple barcodes in ROI
- Each string in array is one detected barcode

#### Compare ROI (Type 2) ⚠️ **CRITICAL**

```typescript
interface CompareROIResult extends ROIResult {
  roi_type_name: "compare";
  match_result: string;              // REQUIRED - "Match"|"Different"
  ai_similarity: number;             // REQUIRED - Similarity score (0.0-1.0)
  threshold: number;                 // REQUIRED - Threshold used (0.0-1.0)
  passed: boolean;                   // true if ai_similarity >= threshold
  golden_image?: string;             // OPTIONAL - Best matching golden
}
```

**Example:**
```json
{
  "roi_id": 2,
  "device_id": 1,
  "roi_type_name": "compare",
  "passed": true,
  "coordinates": [200, 50, 300, 150],
  "match_result": "Match",
  "ai_similarity": 0.92,
  "threshold": 0.85,
  "roi_image": "data:image/jpeg;base64,/9j/4AAQ...",
  "golden_image": "data:image/jpeg;base64,/9j/4AAQ..."
}
```

**Field Rules:**
- `match_result` MUST be "Match" or "Different"
- `ai_similarity` MUST be 0.0 to 1.0
- `threshold` MUST be 0.0 to 1.0
- `passed` = `(ai_similarity >= threshold)`
- `golden_image` is the best matching golden sample

#### OCR ROI (Type 3) ⚠️ **CRITICAL**

```typescript
interface OCRROIResult extends ROIResult {
  roi_type_name: "ocr";
  ocr_text: string;                  // REQUIRED - Recognized text
  passed: boolean;                   // Based on validation logic
}
```

**Example:**
```json
{
  "roi_id": 3,
  "device_id": 1,
  "roi_type_name": "ocr",
  "passed": true,
  "coordinates": [350, 50, 450, 100],
  "ocr_text": "[PASS: Expected text found]",
  "roi_image": "data:image/jpeg;base64,/9j/4AAQ..."
}
```

**Field Rules:**
- `ocr_text` contains recognized text (may be empty string)
- Pass/fail logic:
  - Contains `[FAIL:` → `passed = false`
  - Contains `[PASS:` → `passed = true`
  - Otherwise → `passed = bool(ocr_text)` (has text detected)
- Sample text comparison results embedded in `ocr_text`

### Common Field Constraints

#### `roi_id`
- **Type:** Integer
- **Range:** 1 to N (matches ROI configuration)
- **Required:** YES
- **Purpose:** Identifies which ROI this result is for

#### `device_id`
- **Type:** Integer
- **Range:** 1 to 4
- **Required:** YES
- **Purpose:** Groups results by physical device

#### `roi_type_name`
- **Type:** String
- **Values:** "barcode", "compare", "ocr"
- **Required:** YES
- **Note:** Normalized (e.g., "different" → "compare")

#### `passed`
- **Type:** Boolean
- **Required:** YES
- **Logic:** Type-specific determination
- **Purpose:** Individual ROI pass/fail

#### `coordinates`
- **Type:** Array of 4 integers `[x1, y1, x2, y2]`
- **Required:** YES
- **Constraints:** x1 < x2, y1 < y2, all non-negative
- **Purpose:** ROI position in image

#### `roi_image` (Optional)
- **Type:** String (Base64 data URL)
- **Format:** `"data:image/jpeg;base64,..."`
- **Purpose:** Extracted ROI for display/debugging

#### `golden_image` (Optional)
- **Type:** String (Base64 data URL)
- **Format:** `"data:image/jpeg;base64,..."`
- **Purpose:** Reference image used for comparison

#### `error` (Optional)
- **Type:** String
- **Purpose:** Error message if ROI processing failed
- **Example:** `"Processing failed: Invalid coordinates"`

---

## 📊 Device Summaries Object

### Structure ⚠️ **CRITICAL**

```typescript
interface DeviceSummaries {
  [device_id: string]: DeviceSummary;  // Keys: "1", "2", "3", "4"
}

interface DeviceSummary {
  total_rois: number;           // REQUIRED - Total ROIs for this device
  passed_rois: number;          // REQUIRED - Number that passed
  failed_rois: number;          // REQUIRED - Number that failed
  device_passed: boolean;       // REQUIRED - Device overall pass/fail
  barcode: string;              // REQUIRED - Device barcode (or "N/A")
  results: ROIResult[];         // REQUIRED - ROI results for this device
}
```

### Complete Example

```json
{
  "device_summaries": {
    "1": {
      "total_rois": 3,
      "passed_rois": 3,
      "failed_rois": 0,
      "device_passed": true,
      "barcode": "ABC123456",
      "results": [
        { "roi_id": 1, "passed": true, ... },
        { "roi_id": 2, "passed": true, ... },
        { "roi_id": 3, "passed": true, ... }
      ]
    },
    "2": {
      "total_rois": 2,
      "passed_rois": 1,
      "failed_rois": 1,
      "device_passed": false,
      "barcode": "XYZ789012",
      "results": [
        { "roi_id": 4, "passed": true, ... },
        { "roi_id": 5, "passed": false, ... }
      ]
    }
  }
}
```

### Field Specifications

#### `total_rois` (REQUIRED)
- **Type:** Integer (non-negative)
- **Calculation:** Count of ROIs assigned to this device
- **Constraint:** Must equal `len(results)`

#### `passed_rois` (REQUIRED)
- **Type:** Integer (non-negative)
- **Calculation:** Count where `passed == true`
- **Constraint:** `passed_rois <= total_rois`

#### `failed_rois` (REQUIRED)
- **Type:** Integer (non-negative)
- **Calculation:** Count where `passed == false`
- **Constraint:** `passed_rois + failed_rois == total_rois`

#### `device_passed` (REQUIRED) ⚠️ **CRITICAL LOGIC**
- **Type:** Boolean
- **Logic:** `device_passed = (passed_rois == total_rois)`
- **Rule:** ALL ROIs must pass for device to pass
- **Usage:** Per-device quality gate

#### `barcode` (REQUIRED)
- **Type:** String
- **Default:** "N/A" if no barcode available
- **Priority:** (See Barcode Priority Logic below)
- **Purpose:** Primary identifier for this device

#### `results` (REQUIRED)
- **Type:** Array of ROIResult objects
- **Content:** All ROIs where `device_id` matches
- **Order:** Typically by `roi_id` ascending
- **Purpose:** Detailed results for this device

### Barcode Priority Logic ⚠️ **CRITICAL**

The `barcode` field follows strict priority rules:

```
Priority 0: ROI Barcode with is_device_barcode=True (HIGHEST - NEW in v3.0)
  ↓ (if not found/invalid)
Priority 1: Any ROI Barcode (Detected)
  ↓ (if invalid/missing)
Priority 2: Manual Multi-Device Barcode (device_barcodes[device_id])
  ↓ (if not provided)
Priority 3: Legacy Single Barcode (device_barcode)
  ↓ (if not provided)
Priority 4: Default ("N/A")
```

**New in v3.0:** ROI configurations can include `is_device_barcode=True` (Field 10) to explicitly mark which barcode ROI should be used as the device's primary identifier, giving it highest priority.

**Implementation:**
```python
# Priority 1: Check barcode ROI results
if barcode_roi_valid:
    device_summaries[device_id]['barcode'] = barcode_from_roi

# Priority 2: Use manual device-specific barcode
elif device_barcodes and device_id in device_barcodes:
    device_summaries[device_id]['barcode'] = device_barcodes[device_id]

# Priority 3: Use legacy single barcode for all devices
elif device_barcode:
    device_summaries[device_id]['barcode'] = device_barcode

# Priority 4: Default fallback
else:
    device_summaries[device_id]['barcode'] = 'N/A'
```

---

## 🎯 Overall Result Object

### Structure ⚠️ **CRITICAL**

```typescript
interface OverallResult {
  passed: boolean;         // REQUIRED - Overall inspection pass/fail
  total_rois: number;      // REQUIRED - Total ROIs processed
  passed_rois: number;     // REQUIRED - Total ROIs that passed
  failed_rois: number;     // REQUIRED - Total ROIs that failed
}
```

### Complete Example

```json
{
  "overall_result": {
    "passed": false,
    "total_rois": 5,
    "passed_rois": 4,
    "failed_rois": 1
  }
}
```

### Field Specifications

#### `passed` (REQUIRED) ⚠️ **CRITICAL LOGIC**
- **Type:** Boolean
- **Logic:** `passed = (passed_rois == total_rois) AND (total_rois > 0)`
- **Rule:** ALL ROIs must pass for overall pass
- **Special:** If `total_rois == 0`, result is `false`

#### `total_rois` (REQUIRED)
- **Type:** Integer (non-negative)
- **Calculation:** Total number of ROIs processed
- **Constraint:** `total_rois == len(roi_results)`

#### `passed_rois` (REQUIRED)
- **Type:** Integer (non-negative)
- **Calculation:** Count of ROIs where `passed == true`
- **Constraint:** `passed_rois <= total_rois`

#### `failed_rois` (REQUIRED)
- **Type:** Integer (non-negative)
- **Calculation:** Count of ROIs where `passed == false`
- **Constraint:** `passed_rois + failed_rois == total_rois`

### Validation Formula

```python
# All these must be true
assert total_rois == len(roi_results)
assert total_rois == passed_rois + failed_rois
assert passed == (passed_rois == total_rois and total_rois > 0)
assert passed_rois == sum(1 for roi in roi_results if roi['passed'])
```

---

## ⏱️ Processing Metadata

### `processing_time` (REQUIRED)

- **Type:** Number (float)
- **Unit:** Seconds
- **Precision:** Typically 2-3 decimal places
- **Measurement:** From image decode start to result return
- **Includes:**
  - Image base64 decoding
  - ROI processing (all types)
  - Feature extraction and AI inference
  - Result aggregation
  - Device summary calculation
- **Excludes:**
  - Network transmission time
  - Client-side processing
  - Image capture time

**Example Values:**
```json
{
  "processing_time": 1.234,    // 1.234 seconds
  "processing_time": 0.567,    // 567 milliseconds
  "processing_time": 2.891     // 2.891 seconds
}
```

### `timestamp` (OPTIONAL)

- **Type:** Number (float)
- **Unit:** Unix timestamp (seconds since Jan 1, 1970 UTC)
- **Precision:** Typically includes milliseconds
- **Purpose:** When inspection completed
- **Usage:** Logging, auditing, correlation

**Example:**
```json
{
  "timestamp": 1696348800.123  // Oct 3, 2025, 10:00:00.123 UTC
}
```

---

## ❌ Error Response Format

### Structure for Errors

When inspection fails, return error response:

```typescript
interface ErrorResponse {
  error: string;                  // REQUIRED - Error message
  status?: string;                // OPTIONAL - "error"
  code?: number;                  // OPTIONAL - Error code
  details?: any;                  // OPTIONAL - Additional context
}
```

### HTTP Status Codes

| Status | Meaning | Example |
|--------|---------|---------|
| 400 | Bad Request | Invalid image data, missing parameters |
| 404 | Not Found | Session not found, product not found |
| 409 | Conflict | Another inspection in progress |
| 500 | Internal Server Error | Processing exception, AI model failure |
| 503 | Service Unavailable | System not initialized |

### Example Error Responses

#### 400 Bad Request
```json
{
  "error": "Image data is required"
}
```

#### 404 Not Found
```json
{
  "error": "Session not found"
}
```

#### 409 Conflict
```json
{
  "error": "Another inspection is in progress"
}
```

#### 500 Internal Server Error
```json
{
  "error": "Inspection failed: Could not process ROI 3"
}
```

---

## 🔌 API Endpoint Responses

### `/api/session/{id}/inspect` - Single Image Inspection

**Request:**
```json
{
  "image": "data:image/jpeg;base64,/9j/4AAQ...",
  "device_barcode": "ABC123",           // Optional - legacy single
  "device_barcodes": {                  // Optional - multi-device
    "1": "ABC123",
    "2": "XYZ789"
  }
}
```

**Response (200 OK):**
```json
{
  "roi_results": [
    {
      "roi_id": 1,
      "device_id": 1,
      "roi_type_name": "barcode",
      "passed": true,
      "coordinates": [50, 50, 150, 100],
      "barcode_values": ["ABC123"],
      "roi_image": "data:image/jpeg;base64,..."
    },
    {
      "roi_id": 2,
      "device_id": 1,
      "roi_type_name": "compare",
      "passed": true,
      "coordinates": [200, 50, 300, 150],
      "match_result": "Match",
      "ai_similarity": 0.92,
      "threshold": 0.85,
      "roi_image": "data:image/jpeg;base64,...",
      "golden_image": "data:image/jpeg;base64,..."
    }
  ],
  "device_summaries": {
    "1": {
      "total_rois": 2,
      "passed_rois": 2,
      "failed_rois": 0,
      "device_passed": true,
      "barcode": "ABC123",
      "results": [...]
    }
  },
  "overall_result": {
    "passed": true,
    "total_rois": 2,
    "passed_rois": 2,
    "failed_rois": 0
  },
  "processing_time": 1.234
}
```

### `/process_grouped_inspection` - Multi-Image Grouped Inspection

**Request:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "captured_images": {
    "305,3000": {
      "focus": 305,
      "exposure": 3000,
      "image_filename": "capture_305_3000.jpg",
      "rois": [1, 2, 3]
    }
  },
  "device_barcodes": {
    "1": "ABC123",
    "2": "XYZ789"
  }
}
```

**Response (200 OK):**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "product_name": "test_product",
  "overall_result": {
    "passed": true,
    "total_rois": 3,
    "passed_rois": 3,
    "failed_rois": 0
  },
  "group_results": {
    "305,3000": {
      "focus": 305,
      "exposure": 3000,
      "roi_results": [...],
      "processing_time": 0.8
    }
  },
  "roi_results": [...],
  "device_summaries": {
    "1": {...},
    "2": {...}
  },
  "processing_time": 1.234,
  "timestamp": 1696348800.123
}
```

---

## ✅ Validation Rules

### Result Integrity Checks

All inspection results MUST pass these validations:

```python
def validate_inspection_result(result):
    """Validate inspection result structure."""
    
    # 1. Required top-level fields
    assert 'roi_results' in result
    assert 'device_summaries' in result
    assert 'overall_result' in result
    assert 'processing_time' in result
    
    # 2. Type checks
    assert isinstance(result['roi_results'], list)
    assert isinstance(result['device_summaries'], dict)
    assert isinstance(result['overall_result'], dict)
    assert isinstance(result['processing_time'], (int, float))
    assert result['processing_time'] >= 0
    
    # 3. ROI Results validation
    roi_results = result['roi_results']
    for roi in roi_results:
        # Required fields
        assert 'roi_id' in roi
        assert 'device_id' in roi
        assert 'roi_type_name' in roi
        assert 'passed' in roi
        assert 'coordinates' in roi
        
        # Type validation
        assert isinstance(roi['roi_id'], int) and roi['roi_id'] > 0
        assert isinstance(roi['device_id'], int) and 1 <= roi['device_id'] <= 4
        assert roi['roi_type_name'] in ['barcode', 'compare', 'ocr']
        assert isinstance(roi['passed'], bool)
        assert isinstance(roi['coordinates'], list) and len(roi['coordinates']) == 4
        
        # Type-specific validation
        if roi['roi_type_name'] == 'barcode':
            assert 'barcode_values' in roi
            assert isinstance(roi['barcode_values'], list)
        elif roi['roi_type_name'] == 'compare':
            assert 'match_result' in roi
            assert 'ai_similarity' in roi
            assert 'threshold' in roi
            assert 0.0 <= roi['ai_similarity'] <= 1.0
            assert 0.0 <= roi['threshold'] <= 1.0
        elif roi['roi_type_name'] == 'ocr':
            assert 'ocr_text' in roi
            assert isinstance(roi['ocr_text'], str)
    
    # 4. Device Summaries validation
    device_summaries = result['device_summaries']
    for device_id, summary in device_summaries.items():
        assert device_id in ['1', '2', '3', '4']
        assert 'total_rois' in summary
        assert 'passed_rois' in summary
        assert 'failed_rois' in summary
        assert 'device_passed' in summary
        assert 'barcode' in summary
        assert 'results' in summary
        
        # Consistency checks
        assert summary['total_rois'] == len(summary['results'])
        assert summary['passed_rois'] + summary['failed_rois'] == summary['total_rois']
        assert summary['device_passed'] == (summary['passed_rois'] == summary['total_rois'])
        
        # Barcode check
        assert isinstance(summary['barcode'], str)
    
    # 5. Overall Result validation
    overall = result['overall_result']
    assert 'passed' in overall
    assert 'total_rois' in overall
    assert 'passed_rois' in overall
    assert 'failed_rois' in overall
    
    # Consistency checks
    assert overall['total_rois'] == len(roi_results)
    assert overall['passed_rois'] + overall['failed_rois'] == overall['total_rois']
    assert overall['passed'] == (overall['passed_rois'] == overall['total_rois'] and overall['total_rois'] > 0)
    
    # Cross-validation
    total_passed = sum(1 for roi in roi_results if roi['passed'])
    assert overall['passed_rois'] == total_passed
    
    return True
```

---

## 🔧 Implementation Requirements

### All Functions Must Comply

Every function that creates or returns inspection results MUST follow these rules:

#### 1. Result Construction ⚠️ **MANDATORY**

```python
def create_inspection_result(roi_results: List[Dict], 
                            device_barcodes: Dict = None,
                            processing_time: float = 0.0) -> Dict:
    """
    Create standardized inspection result.
    
    Args:
        roi_results: List of ROI result dictionaries
        device_barcodes: Optional manual barcodes per device
        processing_time: Processing duration in seconds
        
    Returns:
        Complete inspection result dictionary
    """
    # Group by device
    device_summaries = {}
    for roi in roi_results:
        device_id = roi.get('device_id', 1)
        
        if device_id not in device_summaries:
            device_summaries[device_id] = {
                'total_rois': 0,
                'passed_rois': 0,
                'failed_rois': 0,
                'device_passed': True,
                'barcode': 'N/A',
                'results': []
            }
        
        device_summaries[device_id]['results'].append(roi)
        device_summaries[device_id]['total_rois'] += 1
        
        if roi.get('passed', False):
            device_summaries[device_id]['passed_rois'] += 1
        else:
            device_summaries[device_id]['failed_rois'] += 1
            device_summaries[device_id]['device_passed'] = False
    
    # Apply barcode priority logic
    for device_id in device_summaries:
        # Priority 0: ROI barcode with is_device_barcode=True (NEW in v3.0)
        barcode_rois = [r for r in device_summaries[device_id]['results'] 
                       if r.get('roi_type_name') == 'barcode']
        for barcode_roi in barcode_rois:
            # Check if ROI config marks this as device barcode (requires ROI config access)
            # In practice, this is checked in server code with access to ROI definitions
            if barcode_roi.get('is_device_barcode') == True:
                if barcode_roi.get('barcode_values'):
                    barcodes = barcode_roi['barcode_values']
                    if barcodes and barcodes[0]:
                        device_summaries[device_id]['barcode'] = barcodes[0]
                        break
        
        # Priority 1: Any ROI barcode
        if device_summaries[device_id]['barcode'] == 'N/A':
            if barcode_rois and barcode_rois[0].get('barcode_values'):
                barcodes = barcode_rois[0]['barcode_values']
                if barcodes and barcodes[0]:
                    device_summaries[device_id]['barcode'] = barcodes[0]
                    continue
        
        # Priority 2: Manual device barcode
        if device_summaries[device_id]['barcode'] == 'N/A':
            if device_barcodes and str(device_id) in device_barcodes:
                device_summaries[device_id]['barcode'] = device_barcodes[str(device_id)]
    
    # Calculate overall result
    total_rois = len(roi_results)
    passed_rois = sum(1 for roi in roi_results if roi.get('passed', False))
    
    return {
        'roi_results': roi_results,
        'device_summaries': {str(k): v for k, v in device_summaries.items()},
        'overall_result': {
            'passed': passed_rois == total_rois and total_rois > 0,
            'total_rois': total_rois,
            'passed_rois': passed_rois,
            'failed_rois': total_rois - passed_rois
        },
        'processing_time': float(processing_time)
    }
```

#### 2. ROI Result Creation ⚠️ **MANDATORY**

```python
def create_barcode_result(roi_id: int, device_id: int, coords: List[int],
                         barcode_values: List[str], roi_image: str = None) -> Dict:
    """Create barcode ROI result."""
    return {
        'roi_id': int(roi_id),
        'device_id': int(device_id),
        'roi_type_name': 'barcode',
        'passed': bool(barcode_values and barcode_values[0]),
        'coordinates': coords,
        'barcode_values': barcode_values or [],
        'roi_image': roi_image
    }

def create_compare_result(roi_id: int, device_id: int, coords: List[int],
                         similarity: float, threshold: float,
                         roi_image: str = None, golden_image: str = None) -> Dict:
    """Create compare ROI result."""
    return {
        'roi_id': int(roi_id),
        'device_id': int(device_id),
        'roi_type_name': 'compare',
        'passed': float(similarity) >= float(threshold),
        'coordinates': coords,
        'match_result': 'Match' if similarity >= threshold else 'Different',
        'ai_similarity': float(similarity),
        'threshold': float(threshold),
        'roi_image': roi_image,
        'golden_image': golden_image
    }

def create_ocr_result(roi_id: int, device_id: int, coords: List[int],
                     ocr_text: str, roi_image: str = None) -> Dict:
    """Create OCR ROI result."""
    # Determine pass/fail
    if '[FAIL:' in ocr_text:
        passed = False
    elif '[PASS:' in ocr_text:
        passed = True
    else:
        passed = bool(ocr_text)
    
    return {
        'roi_id': int(roi_id),
        'device_id': int(device_id),
        'roi_type_name': 'ocr',
        'passed': passed,
        'coordinates': coords,
        'ocr_text': str(ocr_text),
        'roi_image': roi_image
    }
```

---

## 🚨 Common Mistakes to Avoid

### ❌ DON'T: Return Inconsistent Counts

```python
# WRONG - Counts don't match
{
  "overall_result": {
    "total_rois": 5,
    "passed_rois": 3,
    "failed_rois": 1  # Should be 2!
  }
}
```

### ✅ DO: Ensure Count Consistency

```python
# CORRECT
passed = sum(1 for roi in roi_results if roi['passed'])
total = len(roi_results)
{
  "overall_result": {
    "total_rois": total,
    "passed_rois": passed,
    "failed_rois": total - passed
  }
}
```

### ❌ DON'T: Use Integer Keys in JSON

```python
# WRONG - JSON doesn't support integer keys
{
  "device_summaries": {
    1: {...},  # Will become "1" anyway
    2: {...}
  }
}
```

### ✅ DO: Use String Keys

```python
# CORRECT
{
  "device_summaries": {
    "1": {...},
    "2": {...}
  }
}
```

### ❌ DON'T: Omit Required Fields

```python
# WRONG - Missing barcode field
{
  "device_summaries": {
    "1": {
      "total_rois": 3,
      "passed_rois": 3,
      "device_passed": true
      # Missing: "barcode", "failed_rois", "results"
    }
  }
}
```

### ✅ DO: Include All Required Fields

```python
# CORRECT
{
  "device_summaries": {
    "1": {
      "total_rois": 3,
      "passed_rois": 3,
      "failed_rois": 0,
      "device_passed": true,
      "barcode": "ABC123",
      "results": [...]
    }
  }
}
```

---

## 🔄 Change Management

### When Result Structure Changes

⚠️ **CRITICAL PROCEDURE:** If the result structure needs to be modified:

1. **Update This Document FIRST**
   - Modify field definitions
   - Update TypeScript interfaces
   - Add examples
   - Update validation rules

2. **Update Result Construction Functions**
   - `create_inspection_result()` in inspection modules
   - Type-specific result creators
   - Device summary aggregation logic

3. **Update API Endpoints**
   - `/api/session/{id}/inspect`
   - `/process_grouped_inspection`
   - Any custom inspection endpoints

4. **Update API Documentation**
   - Swagger/OpenAPI specs
   - Example responses
   - Error response formats

5. **Update Client Code**
   - Result parsing logic
   - Display components
   - Validation on client side

6. **Update Tests**
   - Result structure tests
   - Validation tests
   - Integration tests
   - API response tests

7. **Update Other Documentation**
   - PROJECT_INSTRUCTIONS.md
   - API documentation
   - Client integration guides

### Version History

| Version | Date | Changes | Breaking |
|---------|------|---------|----------|
| 2.0 | Oct 3, 2025 | Initial comprehensive specification | N/A |
| 1.x | Earlier | Implicit structure (not documented) | N/A |

---

## 📚 Reference Implementations

### Location of Official Implementation

**Primary Implementation:** `server/simple_api_server.py`

#### Key Functions

1. **`run_real_inspection()`** - Creates inspection results from real processing
2. **`simulate_inspection()`** - Creates results in simulation mode
3. **`run_inspection()`** - API endpoint that returns results
4. **`process_grouped_inspection()`** - Grouped inspection results

#### Result Processing

**Location:** `server/simple_api_server.py`

- **Result Construction**: Lines ~360-610 (varies by mode)
- **Device Aggregation**: Lines ~530-590
- **Barcode Priority Logic**: Lines ~560-590
- **Overall Calculation**: Lines ~595-605

---

## 📖 Summary

### Key Takeaways

1. **Current Structure:** 4 main sections (roi_results, device_summaries, overall_result, processing_time)
2. **Type Safety:** Strict types for all fields
3. **Consistency:** Counts must always match across sections
4. **Barcode Priority:** ROI → Manual Multi → Legacy Single → Default
5. **Validation Required:** All results must pass validation
6. **Document First:** Update this spec BEFORE changing code
7. **Test Thoroughly:** All variations must be tested

---

**⚠️ COMPLIANCE STATEMENT:**

All API endpoints that return inspection results MUST comply with this specification. Non-compliant responses will cause client failures, integration issues, and data inconsistencies.

When in doubt, consult this document and the reference implementation in `server/simple_api_server.py`.