# Compare ROI Type Name Fix

**Date:** October 6, 2025  
**Status:** ✅ Complete and Deployed  
**Issue:** Compare ROI `roi_type_name` was showing as `'match'` instead of `'compare'`

## Problem Description

User reported that API responses showed inconsistent `roi_type_name` values:

```json
{
  "roi_id": 5,
  "roi_type_name": "match",  // ❌ Should be "compare"
  "match_result": "Match"
}
```

**Expected:**

- Barcode ROIs: `roi_type_name: "barcode"`
- OCR ROIs: `roi_type_name: "ocr"`
- Compare ROIs: `roi_type_name: "compare"` ✅

## Root Cause Analysis

### Inconsistent Return Format Across ROI Types

**Barcode and OCR** include type name in position 5:

```python
# Barcode returns:
(idx, 1, roi_img, None, coords, "Barcode", data)
#                                ↑ Position 5 = Type name

# OCR returns:
(idx, 3, roi_img, None, coords, "OCR", data, rotation)
#                                ↑ Position 5 = Type name
```

**Compare ROI** was missing type name - position 5 had match result instead:

```python
# Compare returned (OLD - BROKEN):
(idx, 2, roi_img, golden_img, coords, result, color, similarity, threshold)
#                                      ↑ Position 5 = "Match"/"Different" (NOT type name!)
```

### API Server Was Using Position 5

The API server unpacks position 5 as `type_name`:

```python
roi_id, roi_type, roi_img, golden_img, coordinates, type_name, data, *extra = result
#                                                    ↑ Position 5
```

For Compare ROIs, this grabbed the match result (`"Match"` or `"Different"`) instead of the type name.

The server then had a **normalization hack** to fix this:

```python
# Normalize type_name: convert "different" to "compare" for consistency
normalized_type_name = 'compare' if type_name and type_name.lower() == 'different' else type_name
```

But this only caught `"different"` (lowercase), not `"Match"`, so responses showed `"match"`.

## The Fix

### 1. Updated Compare ROI Return Format

**File:** `src/roi.py`  
**Function:** `process_compare_roi()`

Added `"Compare"` type name to position 5, shifting other fields right:

**Before:**

```python
return (idx, 2, crop2, best_golden_img, (x1, y1, x2, y2), result, color, similarity, threshold)
#                                                          ↑ Position 5 = "Match"/"Different"
```

**After:**

```python
return (idx, 2, crop2, best_golden_img, (x1, y1, x2, y2), "Compare", result, color, similarity, threshold)
#                                                          ↑ Position 5 = "Compare"
#                                                                      ↑ Position 6 = "Match"/"Different"
```

**Lines modified:** 371, 425

### 2. Updated API Server Tuple Unpacking

**File:** `server/simple_api_server.py`

Updated comments to document the new format:

```python
# Barcode: (idx, 1, roi_img, None, coords, "Barcode", data)
# OCR: (idx, 3, roi_img, None, coords, "OCR", data, rotation)
# Compare: (idx, 2, roi_img, golden_img, coords, "Compare", result, color, similarity, threshold)
roi_id, roi_type, roi_img, golden_img, coordinates, type_name, data, *extra = result
```

**Line modified:** 500-503

### 3. Removed Normalization Hack

**File:** `server/simple_api_server.py`

Removed the workaround since Compare ROI now returns correct type name:

**Before:**

```python
# Normalize type_name: convert "different" to "compare" for consistency
normalized_type_name = 'compare' if type_name and type_name.lower() == 'different' else type_name
roi_result['roi_type_name'] = normalized_type_name.lower() if normalized_type_name else 'unknown'
```

**After:**

```python
roi_result['roi_type_name'] = type_name.lower() if type_name else 'unknown'
```

**Lines modified:** 518-523

### 4. Updated Compare ROI Result Parsing

**File:** `server/simple_api_server.py`

Adjusted index for extracting color/similarity/threshold from `extra`:

**Before:**

```python
elif roi_type == 2:  # Compare
    similarity = extra[0] if extra and len(extra) > 0 else 0.0
    threshold = extra[1] if extra and len(extra) > 1 else 0.9
    # extra[0] was similarity (WRONG - now it's color)
```

**After:**

```python
elif roi_type == 2:  # Compare
    # data is now the match result ("Match"/"Different"), extra contains [color, similarity, threshold]
    color = extra[0] if extra and len(extra) > 0 else (0, 0, 0)
    similarity = extra[1] if extra and len(extra) > 1 else 0.0
    threshold = extra[2] if extra and len(extra) > 2 else 0.9
```

**Lines modified:** 574-578

## Validation

### Test Results

```bash
Testing Updated Compare ROI Tuple Format
======================================================================

Compare ROI Result:
  type_name: "Compare" ✓
  result: "Different"
  color: (0, 0, 255)
  similarity: 0.6315
  threshold: 0.9

✓ SUCCESS: Compare ROI now returns "Compare" as type_name!
✓ API server will set roi_type_name to "compare" (lowercase)
```

### Production Logs Confirmation

After server restart, real inspection results show:

```
'roi_type_name': 'compare' ✅✅✅
```

**Examples from live inspection:**

```json
{
  "roi_id": 5,
  "roi_type_name": "compare",
  "match_result": "Match",
  "ai_similarity": 0.9954
}
```

```json
{
  "roi_id": 3,
  "roi_type_name": "compare",
  "match_result": "Match",
  "ai_similarity": 0.9919
}
```

## API Response Format

### Before Fix

```json
{
  "roi_id": 5,
  "roi_type_name": "match",    // ❌ Wrong!
  "match_result": "Match"
}
```

### After Fix

```json
{
  "roi_id": 5,
  "roi_type_name": "compare",  // ✅ Correct!
  "match_result": "Match"
}
```

## Impact

### Fixed Issues

- ✅ Compare ROIs now have correct `roi_type_name: "compare"`
- ✅ Consistent naming across all ROI types
- ✅ Removed hacky normalization code
- ✅ Cleaner API server logic

### Client Impact

- **Breaking Change:** Clients filtering by `roi_type_name == "match"` must update to `"compare"`
- **Recommendation:** Use `roi_type` (integer) instead of `roi_type_name` for filtering:
  - Type 1 = Barcode
  - Type 2 = Compare
  - Type 3 = OCR

## Files Modified

1. ✅ `src/roi.py` - Added "Compare" type name to return tuples (lines 371, 425)
2. ✅ `server/simple_api_server.py` - Updated unpacking and parsing (lines 500-503, 518-523, 574-578)

## Related Fixes

This fix completes the ROI tuple format standardization:

1. **OCR validation** - Added expected_text matching
2. **Field rename** - sample_text → expected_text
3. **Image paths** - Fixed roi_image_path for all ROI types
4. **Tuple unpacking** - Fixed API server unpacking order
5. **Type name** - **This fix** - Standardized type name in position 5

## Deployment

- ✅ Code changes committed
- ✅ Server restarted
- ✅ Production validation complete
- ✅ Live inspections showing correct type names

---

**Status: Production Ready** ✅  
**Type Name Standardized** ✅  
**All ROI Types Consistent** ✅
