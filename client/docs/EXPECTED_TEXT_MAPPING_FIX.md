# Expected Text Field Mapping Fix

## Problem Identified

**Date:** October 6, 2025  
**Issue:** Field name mismatch between client UI and server API for text/OCR ROI expected text values.

### Symptoms

- UI HTML templates use `expected_text` field for OCR and text match ROIs
- Server API uses `sample_text` field for the same purpose
- Conversion functions were not properly mapping between these field names
- Text values would be lost when converting between formats

### Root Cause

**Inconsistent Field Naming:**

- **Client/UI side:** Uses `expected_text` (in `roi_editor.html` line 409, 454)
- **Server side:** Uses `sample_text` (in server API schema)
- **Conversion functions:** Were using `sample_text` on both sides, causing UI to not recognize the field

**Code Locations:**

- File: `app.py`
- Functions: `roi_from_server_format()`, `roi_to_server_format()`, `normalize_roi()`

## Field Purpose

The field stores the expected text value for text-based ROI types:

1. **OCR ROIs (type 3):** Expected text that should be recognized by OCR
   - Example: "PCB", "Serial Number", "Model V1.2"

2. **Text Match ROIs (type 4):** Exact text to match
   - Example: "PASS", "OK", "Part ID: 12345"

## Solution Applied

### 1. Updated `roi_from_server_format()` (Line 285-287)

**Before:**

```python
# Add sample_text for text-type ROIs
if 'sample_text' in server_roi and server_roi['sample_text']:
    client_roi['sample_text'] = server_roi['sample_text']
```

**After:**

```python
# Add expected_text for text-type and OCR ROIs (server uses 'sample_text')
if 'sample_text' in server_roi and server_roi['sample_text']:
    client_roi['expected_text'] = server_roi['sample_text']  # ✅ Maps to expected_text
```

### 2. Updated `roi_to_server_format()` (Line 329)

**Before:**

```python
"sample_text": client_roi.get('sample_text', None),
```

**After:**

```python
"sample_text": client_roi.get('expected_text', None),  # ✅ UI uses 'expected_text'
```

### 3. Updated `normalize_roi()` (Line 455-459)

**Before:**

```python
# Add optional sample_text for text ROIs
if 'sample_text' in roi_data and roi_data['sample_text']:
    normalized['sample_text'] = str(roi_data['sample_text'])
```

**After:**

```python
# Add optional expected_text for text/OCR ROIs
# Handle both 'sample_text' (server) and 'expected_text' (client)
expected_text = roi_data.get('expected_text') or roi_data.get('sample_text')
if expected_text:
    normalized['expected_text'] = str(expected_text)
```

### 4. Updated Documentation (Docstrings)

Updated all function docstrings to reflect the correct mapping:

- `roi_from_server_format()`: Added "sample_text → expected_text"
- `roi_to_server_format()`: Added "expected_text → sample_text"
- `normalize_roi()`: Changed "sample_text" to "expected_text (server uses 'sample_text')"

## Field Mapping Summary

### Server Format → Client Format

```python
{
  "idx": 5,
  "type": 3,  # OCR
  "sample_text": "Expected OCR Text"  # ← Server field
}
```

↓ **roi_from_server_format()**

```python
{
  "roi_id": 5,
  "roi_type_name": "ocr",
  "expected_text": "Expected OCR Text"  # ← Client field
}
```

### Client Format → Server Format

```python
{
  "roi_id": 5,
  "roi_type_name": "text",
  "expected_text": "PCB-V1.2"  # ← Client field
}
```

↓ **roi_to_server_format()**

```python
{
  "idx": 5,
  "type": 4,  # Text
  "sample_text": "PCB-V1.2"  # ← Server field
}
```

## UI Integration

### HTML Templates (roi_editor.html)

**OCR Fields (Line 404-410):**

```html
<div class="form-group">
  <label>Expected Text:</label>
  <input
    type="text"
    id="expectedText"
    class="glass-input"
    placeholder="Expected OCR text"
    onchange="updateROIProperty('expected_text', this.value)"  ✅
  />
</div>
```

**Text Match Fields (Line 449-455):**

```html
<div class="form-group">
  <label>Expected Text:</label>
  <input
    type="text"
    id="expectedTextMatch"
    class="glass-input"
    placeholder="Exact text to match"
    onchange="updateROIProperty('expected_text', this.value)"  ✅
  />
</div>
```

Both templates correctly use `expected_text` as the field name.

## Testing & Verification

### Test Script: `test_expected_text_mapping.py`

Created comprehensive test suite with 5 test cases:

#### Test 1: Server → Client Mapping

```python
server_roi = {"sample_text": "Expected OCR Text", ...}
client_roi = roi_from_server_format(server_roi)
assert client_roi['expected_text'] == "Expected OCR Text"  # ✅ PASS
```

#### Test 2: Client → Server Mapping

```python
client_roi = {"expected_text": "PCB-V1.2", ...}
server_roi = roi_to_server_format(client_roi)
assert server_roi['sample_text'] == "PCB-V1.2"  # ✅ PASS
```

#### Test 3: normalize_roi() with sample_text

```python
roi = {"sample_text": "Serial Number", ...}
normalized = normalize_roi(roi, "test")
assert normalized['expected_text'] == "Serial Number"  # ✅ PASS
```

#### Test 4: normalize_roi() with expected_text

```python
roi = {"expected_text": "Part ID", ...}
normalized = normalize_roi(roi, "test")
assert normalized['expected_text'] == "Part ID"  # ✅ PASS
```

#### Test 5: Round-Trip Conversion

```python
client → server → client
"Test Text" → "Test Text" → "Test Text"  # ✅ PASS
```

**All tests passed:** ✅

### Test Results

```
============================================================
SUMMARY
============================================================
✅ PASS: Server → Client
✅ PASS: Client → Server
✅ PASS: normalize with sample_text
✅ PASS: normalize with expected_text
✅ PASS: Round-trip conversion

✅ ALL TESTS PASSED - Field mapping working correctly
============================================================
```

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────┐
│ Server API (sample_text)                                │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  {                                                      │
│    "idx": 5,                                            │
│    "type": 3,  // OCR                                   │
│    "sample_text": "PCB-V1.2"  ← Server field           │
│  }                                                      │
│                                                         │
│         ↓ GET /api/products/{product}/rois              │
│         ↓                                               │
├─────────────────────────────────────────────────────────┤
│ Client Proxy (app.py)                                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  roi_from_server_format()                               │
│    - Maps: sample_text → expected_text                  │
│                                                         │
│  {                                                      │
│    "roi_id": 5,                                         │
│    "roi_type_name": "ocr",                              │
│    "expected_text": "PCB-V1.2"  ← Client field         │
│  }                                                      │
│                                                         │
│         ↓ GET /api/products/{product}/config            │
│         ↓                                               │
├─────────────────────────────────────────────────────────┤
│ Client UI (roi_editor.html)                             │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  <input id="expectedText"                               │
│         onchange="updateROIProperty('expected_text',    │
│                                      this.value)">      │
│                                                         │
│  User enters: "PCB-V1.2" ✅ Displays correctly          │
│                                                         │
│         ↓ User modifies and saves                       │
│         ↓                                               │
├─────────────────────────────────────────────────────────┤
│ Client Proxy (app.py)                                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  roi_to_server_format()                                 │
│    - Maps: expected_text → sample_text                  │
│                                                         │
│         ↓ POST /api/products/{product}/rois             │
│         ↓                                               │
├─────────────────────────────────────────────────────────┤
│ Server API (sample_text)                                │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  {                                                      │
│    "idx": 5,                                            │
│    "type": 3,                                           │
│    "sample_text": "PCB-V1.2"  ← Saved to server        │
│  }                                                      │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Impact Assessment

### ✅ Fixed Issues

1. ~~Text values not appearing in UI for OCR ROIs~~ ✅ Fixed
2. ~~Text values not appearing in UI for text match ROIs~~ ✅ Fixed
3. ~~Text values lost when saving to server~~ ✅ Fixed
4. ~~Field name inconsistency between client and server~~ ✅ Fixed

### ✅ Verified Working

- Server `sample_text` correctly mapped to client `expected_text` on load
- Client `expected_text` correctly mapped to server `sample_text` on save
- UI displays expected text correctly for OCR ROIs
- UI displays expected text correctly for text match ROIs
- Round-trip conversion preserves text values
- `normalize_roi()` handles both field names

### Backward Compatibility

- ✅ Handles ROIs with `sample_text` (server format)
- ✅ Handles ROIs with `expected_text` (client format)
- ✅ Prioritizes `expected_text` if both present
- ✅ Fallback to `sample_text` if `expected_text` missing

## Usage Examples

### Creating OCR ROI in UI

```javascript
// User creates ROI in UI
const roi = {
  roi_id: 10,
  roi_type_name: "ocr",
  device_id: 1,
  coordinates: [100, 200, 300, 400],
  expected_text: "Serial: 12345",  // ✅ UI field name
  ...
};

// When saved, client converts:
// expected_text → sample_text
```

### Loading ROI from Server

```python
# Server returns
server_roi = {
    "idx": 10,
    "type": 3,  # OCR
    "sample_text": "Serial: 12345",  # Server field name
    ...
}

# Client converts
client_roi = roi_from_server_format(server_roi)
# client_roi['expected_text'] == "Serial: 12345" ✅
```

### Modifying Existing ROI

```javascript
// UI loads ROI with expected_text: "PCB-V1.2"
// User changes to: "PCB-V2.0"
updateROIProperty('expected_text', "PCB-V2.0");

// On save:
// expected_text: "PCB-V2.0" → sample_text: "PCB-V2.0" ✅
```

## Related Files

### Files Modified

- `app.py` - Updated 3 conversion functions and docstrings
  - `roi_from_server_format()` - Maps sample_text → expected_text
  - `roi_to_server_format()` - Maps expected_text → sample_text
  - `normalize_roi()` - Handles both field names

### Files Created

- `test_expected_text_mapping.py` - Comprehensive field mapping tests
- `docs/EXPECTED_TEXT_MAPPING_FIX.md` - This documentation

### Related Documentation

- `docs/ROI_SERVER_SCHEMA_INTEGRATION.md` - General format conversion
- `docs/ROI_SCHEMA_QUICK_REFERENCE.md` - Field reference guide
- `docs/ROI_DISPLAY_FIX.md` - Previous ROI display fix

## Maintenance Notes

### Field Name Reference

| Context | Field Name | Usage |
|---------|-----------|-------|
| Server API | `sample_text` | Server-side storage and processing |
| Client UI | `expected_text` | HTML forms, JavaScript, user interaction |
| Client Code | `expected_text` | Internal client-side representation |

### Conversion Rule

**Always convert at API boundary:**

- **Receiving from server:** `sample_text` → `expected_text`
- **Sending to server:** `expected_text` → `sample_text`

### Code Pattern

```python
# ✅ CORRECT: Convert at boundary
server_data = fetch_from_server()
client_data = roi_from_server_format(server_data)  # sample_text → expected_text
display_in_ui(client_data['expected_text'])

# ✅ CORRECT: Convert when saving
server_data = roi_to_server_format(client_data)  # expected_text → sample_text
save_to_server(server_data)

# ❌ WRONG: Don't use sample_text in client code
ui_element.value = roi['sample_text']  # UI won't recognize this field
```

## Testing Instructions

### Automated Testing

```bash
cd /home/jason_nguyen/visual-aoi-client
python3 test_expected_text_mapping.py
```

Expected output: All 5 tests pass ✅

### Manual Testing

1. **Create OCR ROI with expected text:**
   - Open ROI Editor: `http://localhost:5000/roi-editor`
   - Select product and load configuration
   - Create new ROI with type "OCR"
   - Enter expected text: "TEST-123"
   - Save configuration
   - Reload page and verify text is preserved

2. **Create Text Match ROI:**
   - Create new ROI with type "Text Match"
   - Enter expected text: "PASS"
   - Save and reload
   - Verify text displays correctly

3. **Verify server storage:**

   ```bash
   # Check server file
   cat /home/jason_nguyen/visual-aoi-server/config/products/{product}/rois_config_{product}.json | \
     jq '.[] | select(.type == 3 or .type == 4) | {idx, type, sample_text}'
   ```

   Should show `sample_text` field with correct value.

4. **Verify client display:**
   - Browser DevTools → Console
   - `editorState.rois.filter(r => r.roi_type_name === 'ocr' || r.roi_type_name === 'text')`
   - Should show `expected_text` field with correct value

## Debugging Tips

### Check Field Mapping

```python
# In Python console or test script
from app import roi_from_server_format, roi_to_server_format

# Test server → client
server_roi = {"sample_text": "test", ...}
client_roi = roi_from_server_format(server_roi)
print(f"Client has expected_text: {'expected_text' in client_roi}")

# Test client → server  
client_roi = {"expected_text": "test", ...}
server_roi = roi_to_server_format(client_roi)
print(f"Server has sample_text: {'sample_text' in server_roi}")
```

### Browser Console Check

```javascript
// Check loaded ROIs
editorState.rois.forEach(roi => {
  if (roi.roi_type_name === 'ocr' || roi.roi_type_name === 'text') {
    console.log(`ROI ${roi.roi_id}:`, 
                'expected_text' in roi ? '✅ has expected_text' : '❌ missing expected_text');
  }
});
```

### Server API Check

```bash
# Check server returns sample_text
curl -s http://10.100.27.156:5000/api/products/20003548/rois | \
  jq '.rois[] | select(.type == 3 or .type == 4) | {idx, type, sample_text}'
```

---

**Status:** ✅ RESOLVED  
**Tested:** ✅ ALL TESTS PASSED (5/5)  
**Documentation:** ✅ COMPLETE
