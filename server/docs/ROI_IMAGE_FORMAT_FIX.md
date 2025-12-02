# ROI Return Format Fix

**Date:** October 6, 2025  
**Status:** ✅ Complete  
**Issue:** Inconsistent image positions in ROI return tuples

## Problem Statement

The ROI processing functions had inconsistent return formats where the positions of captured images and golden images were swapped or missing:

### Before (Incorrect Format)

| ROI Type | Position 2 | Position 3 | Issue |
|----------|------------|------------|-------|
| **Barcode** | `roi_barcode` (captured) ✅ | `None` ✅ | Correct |
| **Compare** | `best_golden_img` (golden) ❌ | `crop2` (captured) ❌ | **SWAPPED** |
| **OCR** | `None` ❌ | `None` ✅ | **MISSING captured image** |

### After (Correct Format)

| ROI Type | Position 2 | Position 3 | Status |
|----------|------------|------------|--------|
| **Barcode** | `roi_barcode` (captured) ✅ | `None` ✅ | No change needed |
| **Compare** | `crop2` (captured) ✅ | `best_golden_img` (golden) ✅ | **FIXED** |
| **OCR** | `roi_img` (captured) ✅ | `None` ✅ | **FIXED** |

## Expected Convention

All ROI processing functions should follow this convention:

- **Position 2:** Captured/inspected image from the current inspection
- **Position 3:** Golden/reference image (for compare ROI only, `None` for others)

This allows the API server to consistently:

1. Save the captured ROI image to `roi_{idx}.jpg`
2. Save the golden reference image (if present) to `golden_{idx}.jpg`

## Changes Made

### 1. Fixed Compare ROI (`src/roi.py`)

**Function:** `process_compare_roi()`

**Change:** Swapped positions of `crop2` (captured) and `best_golden_img` (golden)

**Before:**

```python
return (idx, 2, best_golden_img, crop2, (x1, y1, x2, y2), result, color, best_ai_similarity, ai_threshold)
```

**After:**

```python
# Return format: (idx, type, captured_image, golden_image, coords, result, color, similarity, threshold)
return (idx, 2, crop2, best_golden_img, (x1, y1, x2, y2), result, color, best_ai_similarity, ai_threshold)
```

**Locations changed:**

- Line 420: Main return statement
- Line 367: Early return when best golden matches

### 2. Fixed OCR ROI (`src/ocr.py`)

**Function:** `process_ocr_roi()`

**Change:** Return `roi_img` (captured image) instead of `None` in position 2

**Before:**

```python
return (idx, 3, None, None, (x1, y1, x2, y2), "OCR", final_text, rotation)
```

**After:**

```python
# Return format: (idx, type, captured_image, golden_image, coords, type_name, text, rotation)
return (idx, 3, roi_img, None, (x1, y1, x2, y2), "OCR", final_text, rotation)
```

**Locations changed:**

- Line 205: Normal return with OCR results
- Line 202: Error handling return
- Line 144: Empty/small ROI return
- Line 137: Invalid ROI size return (added empty image instead of None)

### 3. No Change Needed for Barcode ROI

**Function:** `process_barcode_roi()` in `src/barcode.py`

Already correct:

```python
return (idx, 1, roi_barcode, None, (x1, y1, x2, y2), "Barcode", barcode_values)
```

## Complete Return Format Specification

### Barcode ROI (Type 1)

```python
(
    idx,                    # ROI index
    1,                      # ROI type (barcode)
    roi_barcode,           # Position 2: Captured barcode image
    None,                   # Position 3: No golden image
    (x1, y1, x2, y2),      # ROI coordinates
    "Barcode",              # Type name
    barcode_values          # Detected barcode values (list)
)
```

### Compare ROI (Type 2)

```python
(
    idx,                    # ROI index
    2,                      # ROI type (compare)
    crop2,                 # Position 2: Captured image
    best_golden_img,       # Position 3: Golden reference image
    (x1, y1, x2, y2),      # ROI coordinates
    result,                 # "Match" or "Different"
    color,                  # RGB color tuple
    best_ai_similarity,     # Similarity score (float)
    ai_threshold            # Threshold value (float)
)
```

### OCR ROI (Type 3)

```python
(
    idx,                    # ROI index
    3,                      # ROI type (OCR)
    roi_img,               # Position 2: Captured OCR image
    None,                   # Position 3: No golden image
    (x1, y1, x2, y2),      # ROI coordinates
    "OCR",                  # Type name
    final_text,             # Detected text with [PASS]/[FAIL] tags
    rotation                # Rotation angle
)
```

## API Server Image Handling

The API server (`server/simple_api_server.py`) processes these return tuples at lines 510-590:

```python
# Extract images from tuple positions
roi_img = roi_result_tuple[2]      # Position 2: Captured image
golden_img = roi_result_tuple[3]   # Position 3: Golden image (or None)

# Save captured ROI image
if roi_img is not None:
    roi_image_path = f"/mnt/visual-aoi-shared/sessions/{session_id}/output/roi_{roi_id}.jpg"
    cv2.imwrite(roi_image_path, roi_img)
    roi_result['roi_image_path'] = roi_image_path

# Save golden reference image (compare ROI only)
if golden_img is not None:
    golden_image_path = f"/mnt/visual-aoi-shared/sessions/{session_id}/output/golden_{roi_id}.jpg"
    cv2.imwrite(golden_image_path, golden_img)
    roi_result['golden_image_path'] = golden_image_path
```

## Testing Results

```bash
Testing ROI Return Formats
============================================================

1. Barcode ROI Return Format:
   Position 2 (captured image): Image - shape (90, 90, 3) ✅
   Position 3 (golden image): None ✅

2. OCR ROI Return Format:
   Position 2 (captured image): Image - shape (90, 90, 3) ✅
   Position 3 (golden image): None ✅

3. Compare ROI Return Format:
   Position 2 (captured image): Image - shape (90, 90, 3) ✅
   Position 3 (golden image): Image - shape (90, 90, 3) ✅

============================================================
✓ All ROI types consistently return captured image in position 2!
```

## Benefits

1. ✅ **Consistent API:** All ROI types follow same position convention
2. ✅ **Correct Image Paths:** Captured images saved with correct filenames
3. ✅ **Client Access:** Clients can reliably access captured ROI images via CIFS mount
4. ✅ **Golden Image Access:** Compare ROI golden images properly saved and accessible
5. ✅ **Debug Friendly:** Clear position convention makes debugging easier

## API Response Format

After this fix, the API returns consistent image paths:

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "results": [
    {
      "roi_id": 1,
      "roi_type_name": "barcode",
      "roi_image_path": "/mnt/visual-aoi-shared/sessions/{uuid}/output/roi_1.jpg",
      "golden_image_path": null,
      "barcode_values": ["123456789"],
      "passed": true
    },
    {
      "roi_id": 2,
      "roi_type_name": "compare",
      "roi_image_path": "/mnt/visual-aoi-shared/sessions/{uuid}/output/roi_2.jpg",
      "golden_image_path": "/mnt/visual-aoi-shared/sessions/{uuid}/output/golden_2.jpg",
      "match_result": "Match",
      "ai_similarity": 0.95,
      "threshold": 0.93,
      "passed": true
    },
    {
      "roi_id": 3,
      "roi_type_name": "ocr",
      "roi_image_path": "/mnt/visual-aoi-shared/sessions/{uuid}/output/roi_3.jpg",
      "golden_image_path": null,
      "ocr_text": "SERIAL123 [PASS: Contains 'SERIAL']",
      "passed": true
    }
  ]
}
```

## Files Modified

- ✅ `src/roi.py` - Fixed compare ROI return format (2 locations)
- ✅ `src/ocr.py` - Fixed OCR ROI return format (4 locations)
- ✅ `src/barcode.py` - No changes needed (already correct)

## Validation

- [x] Python syntax check passed
- [x] Barcode ROI returns captured image in position 2
- [x] Compare ROI returns captured image in position 2, golden in position 3
- [x] OCR ROI returns captured image in position 2
- [x] API server correctly saves all images
- [x] Image paths returned to client are accessible via CIFS mount

## Backward Compatibility

⚠️ **Minor Breaking Change**

Code that directly accesses tuple positions may need updates:

**Before:**

```python
# Old compare ROI access
golden_img = compare_result[2]  # WRONG after fix
captured_img = compare_result[3]  # WRONG after fix
```

**After:**

```python
# New compare ROI access
captured_img = compare_result[2]  # Correct
golden_img = compare_result[3]    # Correct
```

**Mitigation:** The API server was already handling this correctly at the tuple extraction level, so API responses are unchanged. Only direct tuple access in internal code affected.

## Related Changes

This fix complements:

- OCR validation logic update (expected_text field)
- Field rename (sample_text → expected_text)
- Session-based image path return (99% smaller responses)

## Production Impact

✅ **Safe to deploy**

- API response format unchanged (same fields, same structure)
- Image files saved with correct content now
- Clients accessing via CIFS mount will get correct images
- No API contract breaking changes

---

**Fix Complete** ✅  
**All ROI Types Consistent** ✅  
**Image Paths Correct** ✅  
**Testing Passed** ✅
