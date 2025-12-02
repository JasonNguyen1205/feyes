# Image Path Prefix Fix - October 3, 2025

## Problem
After implementing the schema change to return image file paths instead of base64 data (99% response size reduction), the returned paths were relative: `sessions/{uuid}/output/roi_5.jpg`

Clients mounting the shared folder via CIFS at `/mnt/visual-aoi-shared/` couldn't directly use these paths without manual string manipulation.

## Solution
Updated `run_real_inspection()` in `server/simple_api_server.py` to return full client-accessible paths with the CIFS mount prefix.

### Changes Made

#### Code Updates (Lines 538 and 553)

**Before:**
```python
# Line 538
roi_result['roi_image_path'] = f"sessions/{session_id}/output/{roi_image_filename}"

# Line 553
roi_result['golden_image_path'] = f"sessions/{session_id}/output/{golden_image_filename}"
```

**After:**
```python
# Line 538 - Return full client-accessible path with mount prefix
roi_result['roi_image_path'] = f"/mnt/visual-aoi-shared/sessions/{session_id}/output/{roi_image_filename}"

# Line 553 - Return full client-accessible path with mount prefix
roi_result['golden_image_path'] = f"/mnt/visual-aoi-shared/sessions/{session_id}/output/{golden_image_filename}"
```

#### Documentation Updates (Lines 2714, 2725-2726)

Updated API documentation examples to show the new format:
```python
'roi_image_path': '/mnt/visual-aoi-shared/sessions/{uuid}/output/roi_1.jpg'
'golden_image_path': '/mnt/visual-aoi-shared/sessions/{uuid}/output/golden_1.jpg'
```

## Impact

### Benefits
1. **Direct file access**: Clients can use returned paths immediately without modification
2. **Reduced client complexity**: No need for path manipulation logic
3. **Better abstraction**: Server provides full path abstraction
4. **Consistency**: Path format matches client's mount point structure

### Breaking Changes
**Minor breaking change** for clients that were adding the `/mnt/visual-aoi-shared/` prefix themselves:
- **Old client code**: `full_path = f"/mnt/visual-aoi-shared/{api_response['roi_image_path']}"`
- **New client code**: `full_path = api_response['roi_image_path']` (direct use)

Clients using paths directly without manipulation will work immediately.

## Path Architecture

```
Server-side (actual storage):
  /home/jason_nguyen/visual-aoi-server/shared/sessions/{uuid}/output/roi_5.jpg

Client-side (CIFS mount):
  /mnt/visual-aoi-shared/sessions/{uuid}/output/roi_5.jpg

API Response (returned path):
  /mnt/visual-aoi-shared/sessions/{uuid}/output/roi_5.jpg  ✓ Direct client access
```

## Example API Response

### Before Fix
```json
{
  "device_summaries": {
    "1": {
      "roi_results": [
        {
          "roi_id": 5,
          "roi_image_path": "sessions/b3b2d641-8994-4c0d-86bd-193fd89994c0/output/roi_5.jpg",
          "golden_image_path": "sessions/b3b2d641-8994-4c0d-86bd-193fd89994c0/output/golden_5.jpg"
        }
      ]
    }
  }
}
```

### After Fix
```json
{
  "device_summaries": {
    "1": {
      "roi_results": [
        {
          "roi_id": 5,
          "roi_image_path": "/mnt/visual-aoi-shared/sessions/b3b2d641-8994-4c0d-86bd-193fd89994c0/output/roi_5.jpg",
          "golden_image_path": "/mnt/visual-aoi-shared/sessions/b3b2d641-8994-4c0d-86bd-193fd89994c0/output/golden_5.jpg"
        }
      ]
    }
  }
}
```

## Testing
Test that returned paths are directly accessible:
```bash
# From client machine
ls -la /mnt/visual-aoi-shared/sessions/{uuid}/output/
cv2.imread(response['roi_image_path'])  # Should work directly
```

## Related Documentation
- [IMAGE_SCHEMA_CHANGE_OCT_2025.md](IMAGE_SCHEMA_CHANGE_OCT_2025.md) - Original schema change to path-based responses
- [CLIENT_SERVER_ARCHITECTURE.md](CLIENT_SERVER_ARCHITECTURE.md) - Overall architecture
- [DEVICE_BARCODES_FORMAT_FIX.md](DEVICE_BARCODES_FORMAT_FIX.md) - Recent device barcodes compatibility fix

## Implementation Details

### Files Modified
- **server/simple_api_server.py**:
  - Lines 538, 553: Updated path assignments with `/mnt/visual-aoi-shared/` prefix
  - Lines 2714, 2725-2726: Updated API documentation examples

### Server Restart
Server restarted on October 3, 2025 at 22:55 to apply changes.

## Migration Guide for Clients

### If your client was doing this (BREAKING):
```python
# OLD - Will now have double prefix!
api_path = response['roi_image_path']  # "sessions/{uuid}/output/roi_5.jpg"
full_path = f"/mnt/visual-aoi-shared/{api_path}"
image = cv2.imread(full_path)
```

**Fix:** Remove prefix addition:
```python
# NEW - Direct use
api_path = response['roi_image_path']  # "/mnt/visual-aoi-shared/sessions/{uuid}/output/roi_5.jpg"
image = cv2.imread(api_path)  # Works directly
```

### If your client was doing this (NO CHANGE NEEDED):
```python
# COMPATIBLE - Already working
image = cv2.imread(response['roi_image_path'])
```

This will now work even better since the path is complete.

## Verification Checklist
- [x] Code updated in `run_real_inspection()`
- [x] API documentation examples updated
- [x] Server restarted successfully
- [ ] End-to-end test with actual client
- [ ] Verify images accessible via returned paths
- [ ] Update INSPECTION_RESULT_SPECIFICATION.md if needed
- [ ] Notify client developers of path format change

## Timeline
- **October 3, 2025 22:30**: Issue identified (relative paths returned)
- **October 3, 2025 22:45**: Code updated (4 locations)
- **October 3, 2025 22:55**: Server restarted with new code
- **October 3, 2025 22:56**: Documentation created

## Notes
- This completes the IMAGE_SCHEMA_CHANGE by ensuring returned paths are immediately usable
- Combined with base64 removal, this achieves 99% response size reduction with optimal client convenience
- Path format decision prioritizes client simplicity over server abstraction
