# Field Name Standardization: expected_text

## Change Summary

**Date:** October 6, 2025  
**Change:** Standardized on `expected_text` field name for both client and server (removed unnecessary conversion from `sample_text`).

## Problem

Previous implementation incorrectly assumed:

- Server uses `sample_text`
- Client uses `expected_text`
- Conversion needed between the two

## Reality

Both server and client actually use `expected_text`:

- ✅ Server API: Uses `expected_text` field
- ✅ Client UI: Uses `expected_text` field
- ❌ Conversion functions: Were unnecessarily converting between field names

## Solution

Removed all `sample_text` references and use `expected_text` consistently everywhere.

### Changes Made

#### 1. Updated `roi_from_server_format()` (app.py line 286-288)

**Before:**

```python
# Add expected_text for text-type and OCR ROIs (server uses 'sample_text')
if 'sample_text' in server_roi and server_roi['sample_text']:
    client_roi['expected_text'] = server_roi['sample_text']  # ❌ Wrong assumption
```

**After:**

```python
# Add expected_text for text-type and OCR ROIs
if 'expected_text' in server_roi and server_roi['expected_text']:
    client_roi['expected_text'] = server_roi['expected_text']  # ✅ Direct copy
```

#### 2. Updated `roi_to_server_format()` (app.py line 330)

**Before:**

```python
"sample_text": client_roi.get('expected_text', None),  # ❌ Wrong field name
```

**After:**

```python
"expected_text": client_roi.get('expected_text', None),  # ✅ Consistent
```

#### 3. Updated `normalize_roi()` (app.py line 457-459)

**Before:**

```python
# Handle both 'sample_text' (server) and 'expected_text' (client)
expected_text = roi_data.get('expected_text') or roi_data.get('sample_text')  # ❌ Unnecessary fallback
if expected_text:
    normalized['expected_text'] = str(expected_text)
```

**After:**

```python
# Add optional expected_text for text/OCR ROIs
if 'expected_text' in roi_data and roi_data['expected_text']:
    normalized['expected_text'] = str(roi_data['expected_text'])  # ✅ Simple and direct
```

#### 4. Updated Docstrings

Removed all references to `sample_text` from function documentation.

## Verification

### Server API Confirmation

```bash
curl -s http://10.100.27.156:5000/api/products/20003548/rois | jq '.rois[0] | keys'
```

Output shows:

```json
[
  "ai_threshold",
  "coords",
  "device_location",
  "expected_text",  ← Server uses this field
  "exposure",
  "feature_method",
  "focus",
  "idx",
  "is_device_barcode",
  "rotation",
  "type"
]
```

### Test Results

```bash
python3 test_expected_text_mapping.py
```

All tests pass:

```
============================================================
EXPECTED_TEXT FIELD CONSISTENCY TESTS
============================================================

Verifying expected_text field handling:
  - Client/UI uses: 'expected_text'
  - Server uses: 'expected_text' (consistent!)

✅ PASS: Server → Client
✅ PASS: Client → Server
✅ PASS: normalize with expected_text (dict)
✅ PASS: normalize preserves expected_text
✅ PASS: Round-trip conversion

✅ ALL TESTS PASSED - expected_text field handled consistently
============================================================
```

## Benefits

### 1. Simplified Code

- ❌ Before: `sample_text` → `expected_text` → `sample_text` (unnecessary conversions)
- ✅ After: `expected_text` → `expected_text` (direct pass-through)

### 2. Reduced Complexity

- No field name mapping logic needed
- Fewer potential bugs
- Easier to understand and maintain

### 3. Consistent Naming

- Same field name across entire stack
- UI, client code, and server all use `expected_text`
- No mental mapping required

### 4. Better Performance

- No string manipulation for field name conversion
- Direct property access

## Data Flow (Simplified)

```
┌─────────────────────────────────────────────────────────┐
│ Server API                                              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  {                                                      │
│    "idx": 5,                                            │
│    "type": 3,                                           │
│    "expected_text": "PCB-V1.2"  ← Server field         │
│  }                                                      │
│                                                         │
│         ↓ GET /api/products/{product}/rois              │
│         ↓ (no conversion needed)                        │
│         ↓                                               │
├─────────────────────────────────────────────────────────┤
│ Client Proxy (app.py)                                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  roi_from_server_format()                               │
│    - Direct copy: expected_text → expected_text         │
│                                                         │
│  {                                                      │
│    "roi_id": 5,                                         │
│    "roi_type_name": "ocr",                              │
│    "expected_text": "PCB-V1.2"  ← Same field name      │
│  }                                                      │
│                                                         │
│         ↓ GET /api/products/{product}/config            │
│         ↓ (no conversion needed)                        │
│         ↓                                               │
├─────────────────────────────────────────────────────────┤
│ Client UI (roi_editor.html)                             │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  <input id="expectedText"                               │
│         onchange="updateROIProperty('expected_text',    │
│                                      this.value)">      │
│                                                         │
│  expected_text: "PCB-V1.2" ✅ Same field name           │
│                                                         │
│         ↓ User saves                                    │
│         ↓ (no conversion needed)                        │
│         ↓                                               │
├─────────────────────────────────────────────────────────┤
│ Client Proxy (app.py)                                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  roi_to_server_format()                                 │
│    - Direct copy: expected_text → expected_text         │
│                                                         │
│         ↓ POST /api/products/{product}/rois             │
│         ↓ (no conversion needed)                        │
│         ↓                                               │
├─────────────────────────────────────────────────────────┤
│ Server API                                              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  {                                                      │
│    "idx": 5,                                            │
│    "type": 3,                                           │
│    "expected_text": "PCB-V1.2"  ← Same field name      │
│  }                                                      │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Field Reference

| Component | Field Name | Type | Usage |
|-----------|-----------|------|-------|
| Server API | `expected_text` | string/null | OCR/text match expected value |
| Client Code | `expected_text` | string/null | Internal representation |
| UI Forms | `expected_text` | string | User input field |
| Database | `expected_text` | string/null | Stored value |

**Everywhere uses the same field name!** ✅

## Migration Notes

### No Breaking Changes

This change is **fully backward compatible**:

- Server already used `expected_text` ✅
- Client UI already used `expected_text` ✅
- Only conversion functions were updated ✅
- No changes to stored data format ✅

### Removed Code

- Removed `sample_text` field name references
- Removed conversion logic between field names
- Removed fallback logic for `sample_text`

### Updated Tests

- Test file renamed concepts but still validates same functionality
- All tests updated to use `expected_text` consistently
- Added verification that field name is preserved through conversions

## Usage Examples

### Creating OCR ROI

```javascript
// UI code
const roi = {
  roi_id: 10,
  roi_type_name: "ocr",
  expected_text: "Serial: 12345",  // ✅ Direct field name
  ...
};

// Sent to server as-is (no conversion)
// Server receives: expected_text: "Serial: 12345" ✅
```

### Loading ROI from Server

```python
# Server returns
server_roi = {
    "idx": 10,
    "type": 3,
    "expected_text": "Serial: 12345",  # ✅ Direct field name
}

# Client receives
client_roi = roi_from_server_format(server_roi)
# client_roi['expected_text'] == "Serial: 12345" ✅
# Same field name, no conversion!
```

## Impact

### ✅ Benefits

1. Simpler, more maintainable code
2. Consistent field naming across entire stack
3. No unnecessary conversions
4. Reduced cognitive load
5. Fewer potential bugs

### ✅ No Downsides

1. Fully backward compatible
2. No data migration needed
3. No API changes
4. No UI changes

## Files Modified

- `app.py` - Updated 3 conversion functions
  - `roi_from_server_format()` - Use `expected_text` directly
  - `roi_to_server_format()` - Use `expected_text` directly
  - `normalize_roi()` - Removed `sample_text` fallback
  
- `test_expected_text_mapping.py` - Updated tests to verify consistency
  - All tests now verify `expected_text` is preserved
  - Removed `sample_text` references
  - Updated test descriptions

- `docs/EXPECTED_TEXT_STANDARDIZATION.md` - This documentation

## Related Documentation

- `docs/ROI_SERVER_SCHEMA_INTEGRATION.md` - General format conversion (needs update)
- `docs/ROI_SCHEMA_QUICK_REFERENCE.md` - Field reference guide (needs update)
- `docs/EXPECTED_TEXT_MAPPING_FIX.md` - Previous incorrect assumption (superseded)

---

**Status:** ✅ COMPLETE  
**Tested:** ✅ ALL TESTS PASS (5/5)  
**Breaking Changes:** ❌ NONE - Fully backward compatible  
**Benefits:** ✅ Simpler, more maintainable code
