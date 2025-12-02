# API Server Tuple Unpacking Fix

**Date:** October 6, 2025  
**Status:** ✅ Complete  
**Issue:** API server was unpacking ROI result tuples in the old format

## Problem Root Cause

After fixing the ROI processing functions to return images in the correct positions (captured first, golden second), the API server was still unpacking tuples using the **old format**:

### The Mismatch

**ROI Functions Return (NEW - Fixed):**

```python
# Barcode, OCR, Compare all return:
(idx, type, captured_img, golden_img, coords, ...)
#           ↑ Position 2   ↑ Position 3
```

**API Server Unpacked (OLD - Broken):**

```python
roi_id, roi_type, golden_img, roi_img, coordinates, type_name, data, *extra = result
#                 ↑ Position 2  ↑ Position 3
#                 SWAPPED!
```

### Result of Mismatch

This caused:

- ❌ `roi_img` variable got the golden image (position 3)
- ❌ `golden_img` variable got the captured image (position 2)
- ❌ Barcode ROI: `roi_image_path` was `None` (because golden_img is None for barcode)
- ❌ OCR ROI: `roi_image_path` was `None`, but `golden_image_path` was set incorrectly
- ❌ Compare ROI: Images were swapped

## The Fix

**File:** `server/simple_api_server.py`  
**Line:** 500-503

**Before:**

```python
if result:
    # Parse the result tuple based on ROI type
    roi_id, roi_type, golden_img, roi_img, coordinates, type_name, data, *extra = result
```

**After:**

```python
if result:
    # Parse the result tuple based on ROI type
    # Format: (idx, type, captured_img, golden_img, coords, type_name, data, *extra)
    roi_id, roi_type, roi_img, golden_img, coordinates, type_name, data, *extra = result
```

## Validation

### Test Results

```
Testing API Server Tuple Unpacking
======================================================================

1. Barcode ROI:
   roi_img (captured): Image (90, 90, 3) ✅
   golden_img: None ✅
   ✓ Barcode ROI unpacked correctly - captured image available

2. OCR ROI:
   roi_img (captured): Image (90, 90, 3) ✅
   golden_img: None ✅
   ✓ OCR ROI unpacked correctly - captured image available

3. Compare ROI:
   roi_img (captured): Image (90, 90, 3) ✅
   golden_img: Image (90, 90, 3) ✅
   ✓ Compare ROI unpacked correctly - both images available

======================================================================
✓ All ROI types unpack correctly with NEW format!
```

## Expected API Response (After Fix)

Now all ROI types will have their `roi_image_path` correctly set:

```json
{
  "device_summaries": {
    "1": {
      "device_id": 1,
      "roi_results": [
        {
          "roi_id": 1,
          "roi_type_name": "barcode",
          "roi_image_path": "/mnt/visual-aoi-shared/sessions/{uuid}/output/roi_1.jpg",
          "golden_image_path": null,
          "barcode_values": ["20003548-0000003-1019720-101"],
          "passed": true
        },
        {
          "roi_id": 5,
          "roi_type_name": "compare",
          "roi_image_path": "/mnt/visual-aoi-shared/sessions/{uuid}/output/roi_5.jpg",
          "golden_image_path": "/mnt/visual-aoi-shared/sessions/{uuid}/output/golden_5.jpg",
          "match_result": "Match",
          "ai_similarity": 0.945,
          "threshold": 0.93,
          "passed": true
        },
        {
          "roi_id": 6,
          "roi_type_name": "ocr",
          "roi_image_path": "/mnt/visual-aoi-shared/sessions/{uuid}/output/roi_6.jpg",
          "golden_image_path": null,
          "ocr_text": "PCB 5 [PASS: Contains 'PCB']",
          "passed": true
        }
      ]
    }
  }
}
```

### Key Differences (Before vs After)

| ROI Type | Field | Before | After |
|----------|-------|--------|-------|
| **Barcode** | `roi_image_path` | `None` ❌ | `"/mnt/.../roi_1.jpg"` ✅ |
| **Barcode** | `golden_image_path` | `None` ✅ | `None` ✅ |
| **OCR** | `roi_image_path` | `None` ❌ | `"/mnt/.../roi_6.jpg"` ✅ |
| **OCR** | `golden_image_path` | `"/mnt/.../golden_6.jpg"` ❌ | `None` ✅ |
| **Compare** | `roi_image_path` | `"/mnt/.../golden_5.jpg"` ❌ | `"/mnt/.../roi_5.jpg"` ✅ |
| **Compare** | `golden_image_path` | `"/mnt/.../roi_5.jpg"` ❌ | `"/mnt/.../golden_5.jpg"` ✅ |

## Complete Fix Chain

This fix completes a 3-part correction:

### 1. ROI Function Returns (First Fix)

✅ Fixed `src/roi.py::process_compare_roi()` - Swapped image positions  
✅ Fixed `src/ocr.py::process_ocr_roi()` - Return captured image instead of None

### 2. API Server Unpacking (This Fix)

✅ Fixed `server/simple_api_server.py` - Corrected tuple unpacking order

### 3. Image Saving Logic (Already Correct)

✅ API server saves `roi_img` to `roi_{idx}.jpg`  
✅ API server saves `golden_img` to `golden_{idx}.jpg`

## Impact

### Before Fix

- Client couldn't access barcode ROI images (path was None)
- Client couldn't access OCR ROI images (path was None)
- OCR ROIs incorrectly had golden_image_path set
- Compare ROIs had swapped image paths

### After Fix

- ✅ All ROI types return captured image path in `roi_image_path`
- ✅ Only Compare ROI returns golden image path in `golden_image_path`
- ✅ Clients can download all captured ROI images via CIFS mount
- ✅ Clients can download golden reference images for Compare ROIs

## Files Modified

1. ✅ `src/roi.py` - Fixed compare ROI return format
2. ✅ `src/ocr.py` - Fixed OCR ROI return format
3. ✅ `server/simple_api_server.py` - Fixed tuple unpacking (THIS FIX)

## Deployment Notes

**Server Restart Required:** Yes

```bash
# Stop current server
pkill -f "simple_api_server.py"

# Start updated server
./start_server.sh

# Or manually
python3 server/simple_api_server.py --host 0.0.0.0 --port 5000
```

**Client Impact:** None - API response format unchanged, just correct image paths now

**Risk Level:** Low - Bug fix only, no new features

## Testing Checklist

- [x] Python syntax validation passed
- [x] Barcode ROI unpacks correctly
- [x] OCR ROI unpacks correctly
- [x] Compare ROI unpacks correctly
- [x] All ROI types have captured image available
- [x] Compare ROI has both captured and golden images
- [x] Server starts successfully
- [ ] Integration test: Actual inspection returns correct paths (requires server restart)

## Related Documentation

- `docs/ROI_IMAGE_FORMAT_FIX.md` - Original ROI return format fix
- `docs/FIELD_RENAME_SUMMARY.md` - expected_text field rename
- `docs/OCR_PASS_FAIL_LOGIC.md` - OCR validation logic

---

**Fix Complete** ✅  
**Tuple Unpacking Corrected** ✅  
**Image Paths Will Be Set** ✅  
**Ready for Server Restart** ✅
