# Inspection Result Schema Update - Version 2.0

**Date:** October 3, 2025  
**Server API:** http://10.100.27.156:5000/apidocs/  
**Schema Endpoint:** http://10.100.27.156:5000/api/schema/result

## 🚨 BREAKING CHANGES

The server has updated to **Schema Version 2.0** with significant structural changes that break compatibility with the current client implementation.

---

## Schema Comparison

### 1. Top-Level Structure

#### ❌ OLD CLIENT EXPECTATION:
```json
{
  "summary": {
    "overall_result": "PASS",      // ← String
    "total_devices": 2,
    "pass_count": 2,
    "fail_count": 0
  },
  "device_summaries": { ... }
}
```

#### ✅ NEW SERVER SCHEMA:
```json
{
  "overall_result": {               // ← Now an object, not inside "summary"
    "passed": true,                 // ← Boolean, not string
    "passed_rois": 6,
    "failed_rois": 0,
    "total_rois": 6
  },
  "device_summaries": { ... },
  "processing_time": 1.234,         // ← NEW
  "roi_results": [ ... ],           // ← NEW: All ROI results at top level
  "product_name": "20003548",       // ← NEW (optional)
  "session_id": "uuid-here",        // ← NEW (optional)
  "timestamp": 1696363200.5         // ← NEW (optional)
}
```

**Key Changes:**
- ❌ `summary` object removed
- ✅ `overall_result` is now a top-level object (not nested)
- ✅ `overall_result.passed` is boolean (was string "PASS"/"FAIL")
- ✅ No more `total_devices`, `pass_count`, `fail_count` at top level
- ✅ New top-level `roi_results` array contains ALL ROI results
- ✅ New metadata fields: `processing_time`, `product_name`, `session_id`, `timestamp`

---

### 2. Device Summary Structure

#### ❌ OLD CLIENT EXPECTATION:
```json
"device_summaries": {
  "1": {
    "device_id": 1,
    "device_passed": false,
    "barcode": "ABC123",
    "passed_rois": 2,
    "total_rois": 3,
    "roi_results": [ ... ]          // ← Per-device array
  }
}
```

#### ✅ NEW SERVER SCHEMA:
```json
"device_summaries": {
  "1": {
    "barcode": "ABC123",
    "device_passed": true,
    "passed_rois": 2,
    "failed_rois": 0,               // ← NEW
    "total_rois": 2,
    "results": [ ... ]              // ← Field renamed from "roi_results"
  }
}
```

**Key Changes:**
- ❌ `device_id` field removed (already in key)
- ✅ `failed_rois` added
- ⚠️ `roi_results` renamed to `results`
- ✅ `results` array still contains per-device ROI results

---

### 3. ROI Result Structure

#### ❌ OLD CLIENT EXPECTATION:
```json
{
  "roi_id": 1,
  "passed": true,
  "ai_similarity": 0.92,
  "roi_type_name": "compare",
  "coordinates": [50, 50, 150, 100],
  "barcode_values": ["ABC"],
  "ocr_text": "Sample",
  "golden_image": "data:image/jpeg;base64,...",      // ← Base64 data
  "capture_image_file": "group_305_1200.jpg"        // ← Filename only
}
```

#### ✅ NEW SERVER SCHEMA:
```json
{
  "roi_id": 1,
  "device_id": 1,                                    // ← NEW (required)
  "passed": true,
  "roi_type_name": "compare",
  "coordinates": [50, 50, 150, 100],
  "ai_similarity": 0.92,
  "threshold": 0.85,                                 // ← NEW (for compare ROIs)
  "match_result": "Match",                           // ← NEW (for compare ROIs)
  "barcode_values": ["ABC"],                         // ← For barcode ROIs
  "ocr_text": "Sample",                              // ← For OCR ROIs
  "roi_image_path": "sessions/{uuid}/output/roi_1.jpg",      // ← Path, not filename
  "golden_image_path": "sessions/{uuid}/output/golden_1.jpg", // ← Path, not base64
  "error": "Optional error message"                  // ← NEW (optional)
}
```

**Key Changes:**
- ✅ `device_id` is now required in each ROI result
- ✅ `threshold` added (for compare ROIs)
- ✅ `match_result` added (for compare ROIs): "Match" or "Different"
- ⚠️ `golden_image` removed (was base64) → now `golden_image_path` (file path)
- ⚠️ `capture_image_file` removed → now `roi_image_path` (full path)
- ✅ `error` field added (optional, for failure reasons)

---

## Barcode Priority Logic

New in v3.0: Server uses priority order for device barcode selection:

1. **Priority 0:** ROI Barcode with `is_device_barcode=True` (highest)
2. **Priority 1:** First valid barcode from any barcode ROI
3. **Priority 2:** Manual `device_barcodes[device_id]` parameter
4. **Priority 3:** Legacy `device_barcode` parameter
5. **Priority 4:** Default "N/A"

---

## Validation Rules

### Type Validation:
- `roi_results` must be array
- `device_summaries` must be object with string keys
- `overall_result` must be object
- `processing_time` must be number ≥ 0
- `roi_id` must be positive integer
- `device_id` must be 1, 2, 3, or 4
- `coordinates` must be array of 4 integers
- `passed` must be boolean

### Consistency Rules:
- `total_rois` must equal `len(roi_results)`
- `total_rois` must equal `passed_rois + failed_rois`
- `overall_result.passed` must equal `(passed_rois == total_rois AND total_rois > 0)`
- For each device: `total_rois` must equal `len(results)`
- For each device: `device_passed` must equal `(passed_rois == total_rois)`

### Type-Specific Validation:
- **Barcode:** `barcode_values` must be array
- **Compare:** `ai_similarity` and `threshold` must be 0.0 to 1.0
- **Compare:** `match_result` must be "Match" or "Different"
- **OCR:** `ocr_text` must be string

---

## Migration Strategy

### Option 1: Full Update (Recommended)
Update client to use new schema exclusively. Removes technical debt.

**Pros:**
- Clean codebase
- Better performance
- Uses latest features

**Cons:**
- Breaks compatibility with old server versions
- Requires full testing

### Option 2: Backward Compatible
Support both old and new schemas with detection and fallback.

**Pros:**
- Works with both server versions
- Graceful migration

**Cons:**
- More complex code
- Higher maintenance burden
- Performance overhead

---

## Required Client Updates

### 1. Update displayResults() Function

**Location:** `templates/professional_index.html` ~line 800-850

**Changes:**
```javascript
// OLD:
const summary = result.summary || {};
const overallResult = summary.overall_result || 'Unknown';
const totalDevices = summary.total_devices || 0;
const passCount = summary.pass_count || 0;
const failCount = summary.fail_count || 0;

// NEW:
const overallResult = result.overall_result || {};
const passed = overallResult.passed !== undefined ? overallResult.passed : false;
const overallStatus = passed ? 'PASS' : 'FAIL';
const totalRois = overallResult.total_rois || 0;
const passedRois = overallResult.passed_rois || 0;
const failedRois = overallResult.failed_rois || 0;

// Calculate device statistics from device_summaries
const deviceSummaries = result.device_summaries || {};
const totalDevices = Object.keys(deviceSummaries).length;
const passCount = Object.values(deviceSummaries).filter(d => d.device_passed).length;
const failCount = totalDevices - passCount;

// Display new metadata
const processingTime = result.processing_time ? result.processing_time.toFixed(2) + 's' : 'N/A';
const productName = result.product_name || 'Unknown';
```

### 2. Update renderDeviceResults() Function

**Location:** `templates/professional_index.html` ~line 1229-1290

**Changes:**
```javascript
// OLD:
const roiResults = deviceData.roi_results || [];
const totalRois = roiResults.length;

// NEW:
const roiResults = deviceData.results || [];  // ← Field renamed
const totalRois = deviceData.total_rois || 0;
const failedRois = deviceData.failed_rois || 0;
```

### 3. Update renderROIResults() Function

**Location:** `templates/professional_index.html` ~line 1292-1415

**Changes:**
```javascript
// Add threshold and match_result for compare ROIs
${roi.roi_type_name === 'compare' ? `
    <div class="roi-detail-item">
        <div class="roi-detail-label">Match Result</div>
        <div class="roi-detail-value">${roi.match_result || 'N/A'}</div>
    </div>
    <div class="roi-detail-item">
        <div class="roi-detail-label">Threshold</div>
        <div class="roi-detail-value">${roi.threshold ? (roi.threshold * 100).toFixed(2) + '%' : 'N/A'}</div>
    </div>
` : ''}

// Add error message if present
${roi.error ? `
    <div class="roi-detail-item error">
        <div class="roi-detail-label">Error</div>
        <div class="roi-detail-value">${escapeHtml(roi.error)}</div>
    </div>
` : ''}
```

### 4. Update Image Display

**Changes:**
```javascript
// OLD:
const goldenSrc = roi.golden_image || '';  // Base64 data
const captureSrc = roi.capture_image_file 
    ? `/static/captures/${roi.capture_image_file}` 
    : '';

// NEW:
// Server provides full paths relative to mount point
const goldenSrc = roi.golden_image_path 
    ? `/api/images/${encodeURIComponent(roi.golden_image_path)}` 
    : '';
const captureSrc = roi.roi_image_path 
    ? `/api/images/${encodeURIComponent(roi.roi_image_path)}` 
    : '';

// Note: Need new backend endpoint to serve images from shared folder
```

### 5. Add Schema Validation Function

**Add before displayResults():**
```javascript
function validateSchemaV2(result) {
    const errors = [];
    const warnings = [];
    
    // Check required top-level fields
    if (!result.overall_result) {
        errors.push('Missing overall_result object');
    } else {
        if (result.overall_result.passed === undefined) {
            errors.push('Missing overall_result.passed boolean');
        }
        if (result.overall_result.total_rois === undefined) {
            errors.push('Missing overall_result.total_rois');
        }
    }
    
    if (!result.device_summaries) {
        warnings.push('Missing device_summaries');
    }
    
    if (!result.roi_results || !Array.isArray(result.roi_results)) {
        warnings.push('Missing or invalid roi_results array');
    }
    
    // Validate device summaries
    if (result.device_summaries) {
        for (const [deviceId, device] of Object.entries(result.device_summaries)) {
            if (!device.results || !Array.isArray(device.results)) {
                errors.push(`Device ${deviceId}: "results" field must be an array`);
            }
            if (device.device_passed === undefined) {
                warnings.push(`Device ${deviceId}: Missing device_passed`);
            }
            if (device.total_rois === undefined) {
                warnings.push(`Device ${deviceId}: Missing total_rois`);
            }
        }
    }
    
    // Validate ROI results
    if (result.roi_results) {
        result.roi_results.forEach((roi, index) => {
            if (roi.device_id === undefined) {
                errors.push(`ROI ${index}: Missing device_id`);
            }
            if (roi.roi_id === undefined) {
                errors.push(`ROI ${index}: Missing roi_id`);
            }
            if (roi.passed === undefined) {
                warnings.push(`ROI ${roi.roi_id || index}: Missing passed field`);
            }
        });
    }
    
    return {
        valid: errors.length === 0,
        errors,
        warnings
    };
}
```

### 6. Add Backward Compatibility (Optional)

**Add schema detection:**
```javascript
function detectSchemaVersion(result) {
    // v2.0 has overall_result as object with "passed" field
    if (result.overall_result && typeof result.overall_result === 'object' && 
        result.overall_result.passed !== undefined) {
        return '2.0';
    }
    
    // v1.0 has summary.overall_result as string
    if (result.summary && result.summary.overall_result) {
        return '1.0';
    }
    
    return 'unknown';
}

function normalizeToV2(result) {
    const version = detectSchemaVersion(result);
    
    if (version === '2.0') {
        return result;  // Already v2
    }
    
    if (version === '1.0') {
        // Convert v1 to v2 structure
        const normalized = {
            overall_result: {
                passed: result.summary.overall_result === 'PASS',
                passed_rois: result.summary.pass_count || 0,
                failed_rois: result.summary.fail_count || 0,
                total_rois: (result.summary.pass_count || 0) + (result.summary.fail_count || 0)
            },
            device_summaries: {},
            roi_results: []
        };
        
        // Convert device summaries
        if (result.device_summaries) {
            for (const [deviceId, device] of Object.entries(result.device_summaries)) {
                normalized.device_summaries[deviceId] = {
                    barcode: device.barcode,
                    device_passed: device.device_passed,
                    passed_rois: device.passed_rois,
                    failed_rois: device.total_rois - device.passed_rois,
                    total_rois: device.total_rois,
                    results: device.roi_results || []  // Rename roi_results → results
                };
                
                // Add to top-level roi_results
                if (device.roi_results) {
                    normalized.roi_results.push(...device.roi_results);
                }
            }
        }
        
        return normalized;
    }
    
    return result;  // Unknown version, return as-is
}
```

---

## Testing Checklist

After implementing updates:

- [ ] Test with Schema v2.0 response
- [ ] Verify overall_result.passed boolean handling
- [ ] Check device.results array rendering
- [ ] Validate failed_rois display
- [ ] Test threshold and match_result display for compare ROIs
- [ ] Verify error message display
- [ ] Test processing_time display
- [ ] Check image paths (roi_image_path, golden_image_path)
- [ ] Test with missing optional fields
- [ ] Verify backward compatibility (if implemented)
- [ ] Test validation function with malformed data
- [ ] Check console for warnings/errors

---

## Backend API Updates Required

If implementing new image serving:

```python
# app.py - Add new endpoint
@app.route('/api/images/<path:filepath>')
def serve_inspection_image(filepath):
    """Serve images from shared inspection folder"""
    try:
        # Construct full path from shared folder mount point
        base_path = "/mnt/shared/inspections"  # Adjust to your mount point
        full_path = os.path.join(base_path, filepath)
        
        # Security: Ensure path is within base_path
        if not os.path.abspath(full_path).startswith(os.path.abspath(base_path)):
            return jsonify({'error': 'Invalid path'}), 403
        
        if not os.path.exists(full_path):
            return jsonify({'error': 'Image not found'}), 404
        
        return send_file(full_path, mimetype='image/jpeg')
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

---

## Summary

| Category | Count |
|----------|-------|
| Breaking Changes | 3 major |
| New Fields | 10+ |
| Removed Fields | 2 |
| Renamed Fields | 2 |
| Functions to Update | 5 |
| Validation Rules | 15+ |

**Recommended Action:** Implement full Schema v2.0 support with validation.

**Timeline:** 
- Update code: 2-3 hours
- Testing: 1-2 hours
- Documentation: 30 minutes

**Risk Level:** Medium (breaking changes require thorough testing)

---

**Last Updated:** October 3, 2025  
**Server Schema Version:** 2.0  
**Client Support:** Not yet implemented  
**Status:** ⚠️ REQUIRES URGENT UPDATE
