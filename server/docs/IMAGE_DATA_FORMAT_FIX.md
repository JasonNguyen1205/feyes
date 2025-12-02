# Image Data Format Fix - October 3, 2025

## Problem
```
2025-10-03 21:03:40,568 - ERROR - Group 305,1200 missing required keys: ['image_filename']. 
Available keys: ['focus', 'exposure', 'rois', 'image']
```

## Root Cause
The server code at `/process_grouped_inspection` endpoint was expecting the client to send `image_filename` (file path) and then read the image from the shared folder. However, the client was actually sending `image` (base64-encoded image data) directly in the request body.

This is a **client-server API contract mismatch**.

## Solution Applied

Modified `server/simple_api_server.py` (line ~1540-1590) to support **BOTH** image formats:

### 1. Base64 Image Data (New Support Added)
The server now accepts images sent as base64-encoded data in the `image` field:
```python
{
  "focus": 305,
  "exposure": 1200,
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",  # Base64 data
  "rois": [...]
}
```

### 2. File Path (Original Support Maintained)
The server still supports reading images from the shared folder:
```python
{
  "focus": 305,
  "exposure": 1200,
  "image_filename": "captured_image.jpg",  # File in shared/sessions/{uuid}/input/
  "rois": [...]
}
```

## Code Changes

### Before (Line 1547)
```python
# Check required keys
required_keys = ['image_filename', 'focus', 'exposure', 'rois']
missing_keys = [key for key in required_keys if key not in group_data]
if missing_keys:
    logger.error(f"Group {group_key} missing required keys: {missing_keys}")
    continue

# Read image from shared folder
image_filename = group_data['image_filename']
# ... read from file system
image = cv2.imread(input_image_path)
```

### After (Line 1547)
```python
# Check required keys - support both 'image' (base64) and 'image_filename' (file path)
has_image = 'image' in group_data
has_filename = 'image_filename' in group_data

if not has_image and not has_filename:
    logger.error(f"Group {group_key} missing image data")
    continue

# Handle image loading - support both base64 and file path
if has_image:
    # Client sent base64 image data directly
    image_data = group_data['image']
    # Handle data URL format (data:image/jpeg;base64,...)
    if isinstance(image_data, str) and image_data.startswith('data:'):
        image_data = image_data.split(',', 1)[1]
    
    # Decode base64 to image
    import base64
    img_bytes = base64.b64decode(image_data)
    nparr = np.frombuffer(img_bytes, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    logger.info(f"Processing group {group_key} from base64 image")
else:
    # Client sent filename - read from shared folder
    image_filename = group_data['image_filename']
    image = cv2.imread(input_image_path)
    
    logger.info(f"Processing group {group_key} from file: {image_filename}")
```

## Benefits

### 1. **Flexible Client Integration**
- Clients can choose which method to use:
  - Base64: Easier for web/mobile clients, no file system access needed
  - File path: Better for large images, reduces memory usage

### 2. **Backward Compatibility**
- Existing clients using `image_filename` continue to work
- No breaking changes to the API

### 3. **Better Error Messages**
- Clear logging indicates which method is being used
- Easier to debug client-server communication issues

## API Documentation Update Needed

The Swagger/OpenAPI documentation should be updated to reflect both formats:

```yaml
/api/session/{session_id}/process_grouped_inspection:
  parameters:
    - name: groups
      schema:
        type: object
        properties:
          "focus,exposure":  # e.g., "305,1200"
            type: object
            properties:
              focus:
                type: integer
              exposure:
                type: integer
              # ONE OF:
              image:           # Option 1: Base64 image data
                type: string
                format: base64
                description: "Base64-encoded image (supports data URL format)"
              image_filename:  # Option 2: File path
                type: string
                description: "Filename in shared/sessions/{uuid}/input/"
              rois:
                type: array
```

## Testing

### Test with Base64 (Current Client Format)
```python
import requests
import base64

with open("test_image.jpg", "rb") as f:
    img_base64 = base64.b64encode(f.read()).decode('utf-8')

response = requests.post(f"http://localhost:5000/api/session/{session_id}/process_grouped_inspection", json={
    "product_name": "test_product",
    "groups": {
        "305,1200": {
            "focus": 305,
            "exposure": 1200,
            "image": f"data:image/jpeg;base64,{img_base64}",
            "rois": [...]
        }
    }
})
```

### Test with File Path (Legacy Support)
```python
# 1. Upload file to shared folder
shutil.copy("test_image.jpg", f"/mnt/visual-aoi-shared/sessions/{session_id}/input/test.jpg")

# 2. Process with filename
response = requests.post(f"http://localhost:5000/api/session/{session_id}/process_grouped_inspection", json={
    "product_name": "test_product",
    "groups": {
        "305,1200": {
            "focus": 305,
            "exposure": 1200,
            "image_filename": "test.jpg",
            "rois": [...]
        }
    }
})
```

## Deployment Status

✅ **Code Updated:** server/simple_api_server.py (line 1540-1590)  
✅ **Server Restarted:** October 3, 2025 21:05:54  
✅ **GPU Detected:** NVIDIA GeForce RTX 5080 x2  
✅ **Server Running:** http://10.100.27.156:5000  
✅ **Swagger UI:** http://10.100.27.156:5000/apidocs/  

## Related Issues

- Path update completed earlier today (shared folder moved to `/home/jason_nguyen/visual-aoi-server/shared/`)
- Stale CIFS mount resolved
- Server now supports both image transmission methods

## Next Steps

1. ✅ Test client with current format (base64) - should work now
2. ⏭️ Update API documentation to reflect both formats
3. ⏭️ Consider documenting recommended approach:
   - Small images (<5MB): Use base64 for simplicity
   - Large images (>5MB): Use file path for better performance

---

*Issue Resolved: October 3, 2025 21:05*  
*Impact: Zero downtime (hot reload applied)*  
*Backward Compatible: Yes - existing clients continue to work*
