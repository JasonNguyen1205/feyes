# Detection Method Field Name Fix

**Date:** October 9, 2025  
**Issue:** ROI detection method not being saved to server (always defaulting to opencv)  
**Type:** Bug Fix - Field Name Mismatch  

## Problem

User created ROI with MobileNet detection method selected in the UI, but the server-side application still used OpenCV. The detection method selection was not being properly transmitted from client to server.

## Root Cause

**Field Name Inconsistency:**

- **Client UI** sends: `detection_method`
- **Server expects**: `feature_method`
- **Client-to-server conversion** looked for: `model` (legacy field name)

The `roi_to_server_format()` function in `app.py` was using:

```python
"feature_method": str(client_roi.get('model', 'opencv'))  # Always defaulted to 'opencv'!
```

Since the client sends `detection_method` but the converter looked for `model`, it always defaulted to `'opencv'`.

## Solution

Updated all ROI conversion functions in `app.py` to properly handle the `detection_method` field name and maintain backward compatibility with legacy `model` field.

### 1. Updated `roi_to_server_format()` (Client → Server)

**File:** `app.py` lines 402-412

**Before:**

```python
server_roi = {
    "idx": int(client_roi.get('roi_id', 0)),
    "type": roi_type,
    "coords": client_roi.get('coordinates', [0, 0, 0, 0]),
    "feature_method": str(client_roi.get('model', 'opencv')),  # ❌ Wrong field!
    ...
}
```

**After:**

```python
# Support both 'detection_method' (new) and 'model' (legacy) field names
detection_method = client_roi.get('detection_method') or client_roi.get('model', 'opencv')

server_roi = {
    "idx": int(client_roi.get('roi_id', 0)),
    "type": roi_type,
    "coords": client_roi.get('coordinates', [0, 0, 0, 0]),
    "feature_method": str(detection_method),  # ✅ Correct!
    ...
}
```

### 2. Updated `roi_from_server_format()` (Server → Client)

**File:** `app.py` line 360

**Before:**

```python
client_roi = {
    "roi_id": int(server_roi.get('idx', 0)),
    "model": str(server_roi.get('feature_method', 'opencv')),  # ❌ Old field name
    ...
}
```

**After:**

```python
client_roi = {
    "roi_id": int(server_roi.get('idx', 0)),
    "detection_method": str(server_roi.get('feature_method', 'opencv')),  # ✅ New field name
    ...
}
```

### 3. Updated `normalize_roi()` - Dict Format

**File:** `app.py` lines 522-527

**Before:**

```python
model = roi_data.get('model') or roi_data.get('feature_method', 'opencv')

normalized = {
    "roi_id": int(roi_id),
    "model": str(model),  # ❌ Old field name
    ...
}
```

**After:**

```python
# Support detection_method (new), model (legacy), or feature_method (server)
detection_method = roi_data.get('detection_method') or roi_data.get('model') or roi_data.get('feature_method', 'opencv')

normalized = {
    "roi_id": int(roi_id),
    "detection_method": str(detection_method),  # ✅ New field name
    ...
}
```

### 4. Updated `normalize_roi()` - Legacy Array Format

**File:** `app.py` line 484

**Before:**

```python
normalized = {
    "roi_id": int(roi_data[0]),
    "model": str(roi_data[6]) if len(roi_data) > 6 and roi_data[6] else "opencv",  # ❌ Old field name
    ...
}
```

**After:**

```python
normalized = {
    "roi_id": int(roi_data[0]),
    "detection_method": str(roi_data[6]) if len(roi_data) > 6 and roi_data[6] else "opencv",  # ✅ New field name
    ...
}
```

### 5. Updated Documentation Comments

Updated all docstrings to reflect the new field name:

- `feature_method -> detection_method` in client format
- `detection_method -> feature_method` in server format

---

## Field Name Mapping

### Client Format (UI, ROI Editor, Frontend)

```javascript
{
  "roi_id": 5,
  "roi_type_name": "compare",
  "detection_method": "mobilenet",  // ← Field name used in client
  "coordinates": [100, 100, 200, 200],
  ...
}
```

### Server Format (Visual AOI Server API)

```javascript
{
  "idx": 5,
  "type": 2,
  "feature_method": "mobilenet",  // ← Field name used in server
  "coords": [100, 100, 200, 200],
  ...
}
```

### Conversion Logic

```python
# Client → Server (roi_to_server_format)
detection_method = client_roi.get('detection_method') or client_roi.get('model', 'opencv')
server_roi['feature_method'] = str(detection_method)

# Server → Client (roi_from_server_format)
client_roi['detection_method'] = str(server_roi.get('feature_method', 'opencv'))
```

---

## Backward Compatibility

The fix maintains backward compatibility with legacy configurations:

1. **Legacy `model` field**: Still supported in client format
   - `client_roi.get('detection_method') or client_roi.get('model', 'opencv')`

2. **Server `feature_method`**: Properly converted to/from `detection_method`
   - Server always receives correct `feature_method` value
   - Client always uses `detection_method` internally

3. **Array format**: Updated to use `detection_method` in normalized output
   - Legacy arrays still work (index [6] is detection method)

---

## Testing

### Test Case: Save MobileNet ROI

1. Open ROI Editor: `http://localhost:5100/roi-editor`
2. Create Compare ROI with MobileNet selected
3. Save configuration
4. Check server logs for `feature_method: mobilenet`
5. Reload configuration
6. Verify Detection Method dropdown shows "MobileNet"

### Expected Behavior

- ✅ Client sends `detection_method: "mobilenet"`
- ✅ Converter reads `detection_method` field
- ✅ Server receives `feature_method: "mobilenet"`
- ✅ Server processes inspection with MobileNet
- ✅ Client loads `feature_method` as `detection_method`
- ✅ UI displays correct detection method

### Before Fix

- ❌ Client sent `detection_method: "mobilenet"`
- ❌ Converter looked for `model` field (not found)
- ❌ Server received `feature_method: "opencv"` (default)
- ❌ Inspection always used OpenCV regardless of selection

---

## Related Files

- **Backend Converter:** `app.py` lines 320-550
- **Frontend UI:** `static/roi_editor.js` lines 720-830
- **Template:** `templates/roi_editor.html` lines 458-472
- **Documentation:**
  - `docs/DETECTION_METHOD_SELECTION_FIX.md` (UI feature)
  - This document (field name fix)

---

## Summary

**Problem:** Detection method selected in UI (mobilenet) wasn't being saved to server due to field name mismatch.

**Root Cause:** Client used `detection_method` but converter looked for legacy `model` field.

**Solution:** Updated all conversion functions to:

1. Check `detection_method` first (new field)
2. Fall back to `model` (legacy field)
3. Convert to `feature_method` for server
4. Maintain backward compatibility

**Result:** Detection method selection now properly flows from UI → Client → Server → Inspection Engine.

---

## Benefits

- ✅ **MobileNet selection works** - User's selected detection method is now used
- ✅ **Backward compatible** - Legacy `model` field still supported
- ✅ **Consistent naming** - All client code uses `detection_method`
- ✅ **Proper conversion** - Server receives correct `feature_method` value
- ✅ **No breaking changes** - Existing configurations still work
