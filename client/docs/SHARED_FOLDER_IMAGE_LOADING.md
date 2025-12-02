# Shared Folder Image Loading Implementation

**Date:** October 3, 2025  
**Status:** ✅ IMPLEMENTED  
**Component:** Client Image Display System

## Overview

The Visual AOI Client has direct filesystem access to the shared folder `/mnt/visual-aoi-shared/` and loads inspection result images (golden samples and captured ROI images) directly from there, not through external API calls.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Browser (Client UI)                       │
│  professional_index.html                                     │
│  - Receives inspection results with file paths              │
│  - Converts paths: /mnt/.../image.jpg → /shared/.../image.jpg│
│  - Displays images in device cards                          │
└──────────────────────────┬──────────────────────────────────┘
                           │ GET /shared/sessions/xxx/image.jpg
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   Flask Server (app.py)                      │
│  @app.route("/shared/<path:filename>")                      │
│  - Validates path (security check)                          │
│  - Maps /shared/* → /mnt/visual-aoi-shared/*                │
│  - Serves file with send_from_directory()                   │
└──────────────────────────┬──────────────────────────────────┘
                           │ Read file
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Shared Folder (Filesystem)                      │
│  /mnt/visual-aoi-shared/                                    │
│  └── sessions/                                              │
│      └── {session_id}/                                      │
│          └── output/                                        │
│              ├── golden_1.jpg                               │
│              ├── golden_2.jpg                               │
│              ├── roi_1.jpg                                  │
│              └── roi_2.jpg                                  │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Details

### 1. Server Response Format

The inspection server returns results with absolute file paths:

```json
{
  "device_summaries": {
    "1": {
      "results": [
        {
          "roi_id": 5,
          "passed": true,
          "ai_similarity": 0.8819,
          "roi_type_name": "barcode",
          "golden_image_path": "/mnt/visual-aoi-shared/sessions/92f82c5a-3805-48dd-85cb-e4124642d623/output/golden_5.jpg",
          "roi_image_path": "/mnt/visual-aoi-shared/sessions/92f82c5a-3805-48dd-85cb-e4124642d623/output/roi_5.jpg",
          "coordinates": [3459, 2959, 4058, 3318],
          "barcode_values": ["20003548-0000003-1019720-101"]
        }
      ]
    }
  }
}
```

### 2. Client-Side Path Conversion

**File:** `templates/professional_index.html`  
**Function:** `renderROIResults()`

```javascript
// Convert server absolute path to client relative URL
let goldenSrc = '';
if (roi.golden_image && roi.golden_image.startsWith('data:image')) {
    // Base64 encoded image (fallback)
    goldenSrc = roi.golden_image;
} else if (roi.golden_image_path) {
    // File path from shared folder - convert to relative URL
    // /mnt/visual-aoi-shared/sessions/xxx/output/golden_5.jpg 
    //   → /shared/sessions/xxx/output/golden_5.jpg
    const relativePath = roi.golden_image_path.replace('/mnt/visual-aoi-shared/', '/shared/');
    goldenSrc = relativePath;
}

// Same for captured images
let captureSrc = '';
if (roi.roi_image && roi.roi_image.startsWith('data:image')) {
    captureSrc = roi.roi_image;
} else if (roi.roi_image_path) {
    const relativePath = roi.roi_image_path.replace('/mnt/visual-aoi-shared/', '/shared/');
    captureSrc = relativePath;
}
```

### 3. Flask Route Implementation

**File:** `app.py`  
**Route:** `/shared/<path:filename>`

```python
from flask import Flask, send_from_directory
import os

@app.route("/shared/<path:filename>")
def serve_shared_file(filename):
    """Serve files from the shared folder."""
    try:
        # Base path for shared folder
        shared_base = "/mnt/visual-aoi-shared"
        
        # Security: prevent directory traversal
        safe_path = os.path.normpath(filename)
        if safe_path.startswith('..'):
            logger.warning(f"Attempted directory traversal: {filename}")
            return jsonify({"error": "Invalid path"}), 403
        
        full_path = os.path.join(shared_base, safe_path)
        
        # Check if file exists
        if not os.path.exists(full_path):
            logger.warning(f"File not found: {full_path}")
            return jsonify({"error": "File not found"}), 404
        
        # Serve the file
        directory = os.path.dirname(full_path)
        file_name = os.path.basename(full_path)
        return send_from_directory(directory, file_name)
        
    except Exception as e:
        logger.error(f"Failed to serve shared file: {e}")
        return jsonify({"error": str(e)}), 500
```

## Security Features

### 1. Directory Traversal Protection

```python
# Prevents attacks like: /shared/../../etc/passwd
safe_path = os.path.normpath(filename)
if safe_path.startswith('..'):
    return jsonify({"error": "Invalid path"}), 403
```

### 2. Path Validation

```python
# Only serves files that actually exist
if not os.path.exists(full_path):
    return jsonify({"error": "File not found"}), 404
```

### 3. Base Path Restriction

```python
# All paths must be under /mnt/visual-aoi-shared/
shared_base = "/mnt/visual-aoi-shared"
full_path = os.path.join(shared_base, safe_path)
```

## Image Display Features

### 1. Responsive Layout

```css
.roi-images {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
    margin-top: 16px;
}
```

- **Desktop/Tablet:** 2-column grid
- **Mobile:** Single column (auto-adjusts)

### 2. Click-to-Zoom Modal

```html
<img src="${goldenSrc}" 
     class="roi-image"
     onclick="openImageModal(this.src, 'Golden Sample - ROI ${roi.roi_id}')"
     alt="Golden sample for ROI ${roi.roi_id}">
```

- Click thumbnail → Full-screen modal
- Backdrop blur effect
- Close with X button or click outside

### 3. Error Fallback

```javascript
onerror="this.onerror=null; 
         this.src='data:image/svg+xml,%3Csvg xmlns=\\'http://www.w3.org/2000/svg\\' 
         width=\\'200\\' height=\\'150\\'%3E%3Crect fill=\\'%23f0f0f0\\' 
         width=\\'200\\' height=\\'150\\'/%3E%3Ctext x=\\'50%25\\' y=\\'50%25\\' 
         text-anchor=\\'middle\\' fill=\\'%23999\\' font-family=\\'Arial\\' 
         font-size=\\'14\\'%3EImage Unavailable%3C/text%3E%3C/svg%3E'; 
         this.parentElement.classList.add('image-error');"
```

Shows SVG placeholder if image fails to load.

## Path Priority Order

The client checks multiple possible image sources in priority order:

1. **Base64 Data** (highest priority)
   - Format: `data:image/jpeg;base64,...`
   - Use case: Embedded images in response
   - No file system access needed

2. **Server File Path** (normal case)
   - Format: `/mnt/visual-aoi-shared/sessions/xxx/output/golden_5.jpg`
   - Converted to: `/shared/sessions/xxx/output/golden_5.jpg`
   - Served via Flask route

3. **Legacy Static Path** (fallback)
   - Format: `group_305_1200.jpg`
   - Converted to: `/static/captures/group_305_1200.jpg`
   - For backward compatibility

## Example Flow

### Successful Image Load

```
1. Server returns inspection result:
   {
     "golden_image_path": "/mnt/visual-aoi-shared/sessions/abc-123/output/golden_5.jpg"
   }

2. Client converts path:
   "/mnt/visual-aoi-shared/sessions/abc-123/output/golden_5.jpg"
   → "/shared/sessions/abc-123/output/golden_5.jpg"

3. Browser requests:
   GET http://localhost:5100/shared/sessions/abc-123/output/golden_5.jpg

4. Flask route receives:
   filename = "sessions/abc-123/output/golden_5.jpg"

5. Flask constructs full path:
   full_path = "/mnt/visual-aoi-shared/sessions/abc-123/output/golden_5.jpg"

6. Flask serves file:
   send_from_directory("/mnt/visual-aoi-shared/sessions/abc-123/output", "golden_5.jpg")

7. Browser displays image ✅
```

### Failed Image Load (404)

```
1. Server returns path:
   "/mnt/visual-aoi-shared/sessions/xyz-456/output/missing.jpg"

2. Client converts:
   "/shared/sessions/xyz-456/output/missing.jpg"

3. Browser requests:
   GET http://localhost:5100/shared/sessions/xyz-456/output/missing.jpg

4. Flask checks file:
   os.path.exists("/mnt/visual-aoi-shared/sessions/xyz-456/output/missing.jpg")
   → False

5. Flask returns:
   {"error": "File not found"}, 404

6. Browser onerror handler:
   Shows SVG placeholder "Image Unavailable"
```

## Debugging

### Enable Detailed Logging

**In HTML (Browser Console):**
```javascript
console.log(`🔍 ROI ${roi.roi_id} image data:`, {
    golden_image: roi.golden_image ? (roi.golden_image.startsWith('data:') ? 'base64 data' : roi.golden_image) : 'none',
    golden_image_path: roi.golden_image_path || 'none',
    roi_image: roi.roi_image ? (roi.roi_image.startsWith('data:') ? 'base64 data' : roi.roi_image) : 'none',
    roi_image_path: roi.roi_image_path || 'none'
});
```

**In Flask (Server Logs):**
```python
logger.info(f"Serving shared file: {filename}")
logger.info(f"Full path: {full_path}")
logger.info(f"File exists: {os.path.exists(full_path)}")
```

### Common Issues

#### Issue 1: 404 Errors
**Symptom:**
```
Failed to load resource: the server responded with a status of 404 (NOT FOUND)
/shared/sessions/xxx/output/golden_5.jpg
```

**Causes:**
- File doesn't exist in shared folder
- Wrong session ID in path
- Server hasn't created output files yet
- Permission issues on shared folder

**Debug:**
```bash
# Check if file exists
ls -la /mnt/visual-aoi-shared/sessions/{session_id}/output/

# Check permissions
stat /mnt/visual-aoi-shared/sessions/{session_id}/output/golden_5.jpg
```

#### Issue 2: Directory Traversal Blocked
**Symptom:**
```
{"error": "Invalid path"}, 403
```

**Cause:**
- Path contains `..` attempting to access parent directories
- Security feature working correctly

**Solution:**
- Use proper paths without `..`
- Ensure server returns correct absolute paths

#### Issue 3: Images Not Displaying
**Symptom:**
- No images shown in device cards
- SVG placeholder displayed

**Debug Steps:**
1. Open browser DevTools (F12)
2. Check Console for logs:
   - `🔍 ROI X image data:` logs
   - Error messages
3. Check Network tab:
   - Look for `/shared/` requests
   - Check status codes (200, 404, 403)
4. Verify server response:
   - Contains `golden_image_path` or `roi_image_path` fields
   - Paths are absolute starting with `/mnt/visual-aoi-shared/`

## Testing

### Manual Testing

1. **Start Flask server:**
   ```bash
   ./start_web_client.sh
   ```

2. **Run inspection:**
   - Connect to server
   - Create session
   - Perform inspection

3. **Check results:**
   - Click "Show Device Details" button
   - Verify images display in ROI cards
   - Check browser console for logs

4. **Test zoom:**
   - Click image thumbnail
   - Modal should open with full-size image
   - Close modal with X or click outside

### Automated Testing

```bash
# Test file serving endpoint
curl http://localhost:5100/shared/sessions/test-session/output/test.jpg

# Expected responses:
# - 200: File served successfully
# - 404: File not found
# - 403: Invalid path (security)
```

## Performance Considerations

### File System Access

- **Direct read** from shared folder (fast)
- No database queries needed
- No external API calls
- Minimal CPU overhead

### Caching

Browser automatically caches images by URL:
```
/shared/sessions/abc-123/output/golden_5.jpg
```

Same URL → Served from browser cache (instant)

### Network Transfer

- Images served as regular files
- Browser handles compression (gzip/brotli)
- Supports HTTP range requests (partial content)
- Efficient for large images

## Migration Notes

### From API-Based Loading

**Old approach (REMOVED):**
```javascript
// Don't do this - /api/images/ doesn't exist on client
const goldenSrc = `/api/images/${encodeURIComponent(roi.golden_image_path)}`;
```

**New approach (CORRECT):**
```javascript
// Convert to /shared/ route
const goldenSrc = roi.golden_image_path.replace('/mnt/visual-aoi-shared/', '/shared/');
```

### From Static Folder

**Old approach (legacy):**
```javascript
// Only works for files copied to static/captures/
const captureSrc = `/static/captures/${roi.capture_image_file}`;
```

**New approach (preferred):**
```javascript
// Direct access to shared folder
const captureSrc = roi.roi_image_path.replace('/mnt/visual-aoi-shared/', '/shared/');
```

## Best Practices

### Server-Side (Inspection Server)

1. ✅ Return absolute paths starting with `/mnt/visual-aoi-shared/`
2. ✅ Save images to consistent locations
3. ✅ Use predictable naming: `golden_{roi_id}.jpg`, `roi_{roi_id}.jpg`
4. ✅ Include both `golden_image_path` and `roi_image_path` in response

### Client-Side (Flask App)

1. ✅ Validate all paths before serving
2. ✅ Log access attempts for debugging
3. ✅ Return proper HTTP status codes
4. ✅ Handle errors gracefully

### Frontend (HTML/JavaScript)

1. ✅ Check for multiple image source formats
2. ✅ Implement error fallbacks
3. ✅ Log image data for debugging
4. ✅ Show loading states

## Related Documentation

- `docs/SCHEMA_V2_QUICK_REFERENCE.md` - Response schema details
- `docs/UI_IMPROVEMENTS_IMPLEMENTATION.md` - UI enhancements
- `docs/ROI_IMAGE_DISPLAY_LOCATION.md` - Image display locations

## Version History

| Date | Version | Changes |
|------|---------|---------|
| 2025-10-03 | 1.0 | Initial implementation with `/shared/` route |

---

**Last Updated:** October 3, 2025  
**Status:** ✅ Production Ready  
**Maintainer:** Visual AOI Team
