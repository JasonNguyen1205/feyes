# Grouped Inspection ROI Filtering Fix

**Date**: October 9, 2025  
**Issue**: ROI images were extracted from wrong capture group images  
**Product Affected**: 20003548 (ROI 4 and ROI 6 specifically)

## Problem Description

When processing grouped inspections with multiple capture groups (different focus/exposure combinations), **all ROIs were being processed against every capture group's image**, regardless of which group they belonged to.

### Example Issue

For product 20003548:

- **Group 1** (focus: 305, exposure: 700): ROIs 3, 7, 8, 9, 10, 11, 12, 13
- **Group 2** (focus: 305, exposure: 3000): ROIs 4, 6

**Before Fix**: When processing the exposure 700 image, the system would process ALL ROIs including ROI 4 and 6, extracting them from the wrong image (700 exposure instead of 3000 exposure).

**After Fix**: Each capture group only processes its matching ROIs based on focus and exposure values.

## Root Cause

In `server/simple_api_server.py`, the `process_grouped_inspection` endpoint called `run_real_inspection()` with each capture group's image, but `run_real_inspection()` was loading and processing **all ROIs from the product configuration** without filtering by capture group.

```python
# OLD CODE (PROBLEMATIC)
for group_key, group_data in captured_images.items():
    image = load_image(group_data)
    focus = group_data['focus']
    exposure = group_data['exposure']
    
    # ❌ This processes ALL ROIs, not just those matching this group
    results = run_real_inspection(image, product_name, ...)
```

## Solution

### 1. Modified `run_real_inspection()` Function

Added optional filtering parameters:

- `filter_focus: Optional[int]` - Only process ROIs with this focus value
- `filter_exposure: Optional[int]` - Only process ROIs with this exposure value

```python
def run_real_inspection(
    image: np.ndarray,
    product_name: Optional[str] = None,
    device_barcode: Optional[str] = None,
    device_barcodes: Optional[Dict] = None,
    session_id: Optional[str] = None,
    filter_focus: Optional[int] = None,      # NEW
    filter_exposure: Optional[int] = None     # NEW
) -> Dict:
```

### 2. ROI Filtering Logic

```python
# Filter ROIs by focus and exposure if specified
if filter_focus is not None or filter_exposure is not None:
    for roi in all_rois:
        # ROI structure: (idx, typ, coords, focus, exposure_time, ...)
        roi_focus = roi[3]
        roi_exposure = roi[4]
        
        # Match both focus and exposure
        if filter_focus is not None and filter_exposure is not None:
            if roi_focus == filter_focus and roi_exposure == filter_exposure:
                rois.append(roi)
        # Match only focus
        elif filter_focus is not None and roi_focus == filter_focus:
            rois.append(roi)
        # Match only exposure
        elif filter_exposure is not None and roi_exposure == filter_exposure:
            rois.append(roi)
    
    logger.info(f"Filtered to {len(rois)} ROIs matching focus={filter_focus}, exposure={filter_exposure}")
else:
    rois = all_rois  # No filtering, process all ROIs
```

### 3. Updated Grouped Inspection Call

```python
# NEW CODE (CORRECT)
for group_key, group_data in captured_images.items():
    image = load_image(group_data)
    focus = group_data['focus']
    exposure = group_data['exposure']
    
    # ✅ Only processes ROIs matching this group's focus/exposure
    results = run_real_inspection(
        image, product_name, 
        device_barcodes=device_barcodes, 
        session_id=session_id,
        filter_focus=focus,          # NEW
        filter_exposure=exposure     # NEW
    )
```

## Benefits

1. **Correct ROI Extraction**: Each ROI is extracted from its designated capture group image
2. **Faster Processing**: Only processes relevant ROIs for each image (fewer unnecessary operations)
3. **Accurate Results**: OCR, barcode, and comparison results now use the correct source images
4. **Backward Compatible**: When no filters are specified, processes all ROIs (legacy behavior)

## Example: Product 20003548

### Before Fix (Incorrect)

```
Processing Group 305,700:
  ✓ ROI 3 (exposure: 700) → extracted from 700 image ✅
  ✗ ROI 4 (exposure: 3000) → extracted from 700 image ❌ WRONG!
  ✗ ROI 6 (exposure: 3000) → extracted from 700 image ❌ WRONG!
  ✓ ROI 7-13 (exposure: 700) → extracted from 700 image ✅

Processing Group 305,3000:
  ✗ ROI 3 (exposure: 700) → extracted from 3000 image ❌ WRONG!
  ✓ ROI 4 (exposure: 3000) → extracted from 3000 image ✅
  ✓ ROI 6 (exposure: 3000) → extracted from 3000 image ✅
  ✗ ROI 7-13 (exposure: 700) → extracted from 3000 image ❌ WRONG!

Result: Each ROI processed TWICE with wrong images mixed in
```

### After Fix (Correct)

```
Processing Group 305,700:
  ✓ ROI 3 (exposure: 700) → extracted from 700 image ✅
  ✓ ROI 7 (exposure: 700) → extracted from 700 image ✅
  ✓ ROI 8 (exposure: 700) → extracted from 700 image ✅
  ✓ ROI 9 (exposure: 700) → extracted from 700 image ✅
  ✓ ROI 10 (exposure: 700) → extracted from 700 image ✅
  ✓ ROI 11 (exposure: 700) → extracted from 700 image ✅
  ✓ ROI 12 (exposure: 700) → extracted from 700 image ✅
  ✓ ROI 13 (exposure: 700) → extracted from 700 image ✅

Processing Group 305,3000:
  ✓ ROI 4 (exposure: 3000) → extracted from 3000 image ✅
  ✓ ROI 6 (exposure: 3000) → extracted from 3000 image ✅

Result: Each ROI processed ONCE with correct source image
```

## Testing

1. **Restart server** to apply changes
2. **Run grouped inspection** for product 20003548
3. **Verify ROI images**:
   - Check that ROI 4 image shows proper brightness for 3000 exposure
   - Check that ROI 6 image shows proper brightness for 3000 exposure
   - Check that ROI 3, 7-13 images show proper brightness for 700 exposure

## Log Output

With filtering enabled, you'll see logs like:

```
INFO - Running real inspection for product: 20003548, session: xxxx
INFO - Filtering ROIs by focus=305, exposure=700
INFO - Filtered to 8 ROIs matching focus=305, exposure=700 (from 10 total)
INFO - Processing 8 ROIs in parallel

INFO - Running real inspection for product: 20003548, session: xxxx
INFO - Filtering ROIs by focus=305, exposure=3000
INFO - Filtered to 2 ROIs matching focus=305, exposure=3000 (from 10 total)
INFO - Processing 2 ROIs in parallel
```

## Files Modified

- `server/simple_api_server.py`
  - Function `run_real_inspection()`: Added filter_focus and filter_exposure parameters with filtering logic
  - Function `process_grouped_inspection()`: Updated call to pass focus and exposure filters

## Related Issues

This fix resolves the issue where:

- OCR on ROI 4 would fail because it was reading from the wrong exposure image
- OCR on ROI 6 would fail for the same reason
- Any ROI with different capture settings than others would get incorrect results

## Impact

- **Low risk**: Only affects grouped inspection workflow
- **High benefit**: Ensures accurate inspection results for multi-exposure products
- **Backward compatible**: Non-grouped inspections work exactly as before
