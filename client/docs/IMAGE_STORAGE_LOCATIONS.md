# Image Storage Locations

**Date:** October 6, 2025  
**Status:** ✅ Documentation  
**Version:** 1.0

## Overview

This document explains where captured images are stored in the Visual AOI Client system, how to access them, and what each storage location is used for.

## Main Storage Location

### Shared Folder Base Path

**Location:** `/mnt/visual-aoi-shared/`

This is a shared network folder that both the client and server can access. All captured images are stored here.

**Structure:**

```
/mnt/visual-aoi-shared/
├── roi_editor/          # Images captured from ROI Editor
├── sessions/            # Inspection session images (organized by session ID)
│   ├── {session_id_1}/
│   │   └── output/
│   │       ├── golden_{roi_id}.jpg    # Golden sample images
│   │       └── roi_{roi_id}.jpg       # Captured ROI images
│   ├── {session_id_2}/
│   └── ...
└── .Trash-1000/         # Deleted files
```

## Storage Types

### 1. ROI Editor Images

**Location:** `/mnt/visual-aoi-shared/roi_editor/`

**Purpose:** Test captures and ROI configuration images

**Naming Convention:** `roi_editor_YYYYMMDD_HHMMSS.jpg`

**Example Files:**

```bash
roi_editor_20251006_135508.jpg  # Captured on Oct 6, 2025 at 13:55:08
roi_editor_20251006_135521.jpg  # Captured on Oct 6, 2025 at 13:55:21
```

**Characteristics:**

- **Size:** ~8-11 MB per image (full resolution: 7716x5360)
- **Usage:** ROI configuration, testing, calibration
- **Lifespan:** Permanent (manual cleanup needed)
- **Access:** Via `/shared/roi_editor/{filename}` route

**Code Reference:**

```python
# File: app.py, Line ~1730
shared_path = "/mnt/visual-aoi-shared/roi_editor"
filename = f"roi_editor_{timestamp}.jpg"
filepath = os.path.join(shared_path, filename)
cv2.imwrite(filepath, image)
```

**API Endpoint:**

- `POST /api/camera/capture` - Captures and saves image
- Returns: `{"image_path": "roi_editor/roi_editor_20251006_135508.jpg"}`

**Viewing Images:**

- URL: `http://127.0.0.1:5100/shared/roi_editor/roi_editor_20251006_135508.jpg`

### 2. Inspection Session Images

**Location:** `/mnt/visual-aoi-shared/sessions/{session_id}/output/`

**Purpose:** Images from actual product inspections

**Structure:**

```
/mnt/visual-aoi-shared/sessions/
└── 058ecb7f-a961-40de-832d-20588313a3cf/    # Session UUID
    └── output/
        ├── golden_1.jpg      # Golden sample for ROI 1
        ├── golden_3.jpg      # Golden sample for ROI 3
        ├── golden_5.jpg      # Golden sample for ROI 5
        ├── roi_1.jpg         # Captured ROI 1 image
        ├── roi_2.jpg         # Captured ROI 2 image
        ├── roi_3.jpg         # Captured ROI 3 image
        └── ...
```

**File Types:**

1. **Golden Sample Images** (`golden_{roi_id}.jpg`)
   - Reference images for comparison
   - Created during inspection or saved via golden sample API
   - Used for AI similarity matching
   - Size: 13KB - 138KB (cropped ROI regions)

2. **Captured ROI Images** (`roi_{roi_id}.jpg`)
   - Current inspection capture for each ROI
   - Extracted from full-frame capture
   - Size: 13KB - 138KB (cropped ROI regions)
   - Used for barcode reading, OCR, AI comparison

**Characteristics:**

- **Organization:** One folder per inspection session
- **Session ID:** UUID format (e.g., `058ecb7f-a961-40de-832d-20588313a3cf`)
- **Lifespan:** Persists until session cleanup or manual deletion
- **Access:** Via `/shared/sessions/{session_id}/output/{filename}` route

**API Response Format:**

```json
{
  "roi_id": 1,
  "passed": true,
  "ai_similarity": 0.8819,
  "golden_image_path": "/mnt/visual-aoi-shared/sessions/xxx/output/golden_5.jpg",
  "roi_image_path": "/mnt/visual-aoi-shared/sessions/xxx/output/roi_5.jpg",
  "coordinates": [3459, 2959, 4058, 3318]
}
```

**Viewing Images:**

- Golden: `http://127.0.0.1:5100/shared/sessions/{session_id}/output/golden_5.jpg`
- ROI: `http://127.0.0.1:5100/shared/sessions/{session_id}/output/roi_5.jpg`

## Access Methods

### 1. Direct File System Access

**Command Line:**

```bash
# List ROI editor images
ls -lh /mnt/visual-aoi-shared/roi_editor/

# List sessions
ls -lh /mnt/visual-aoi-shared/sessions/

# View specific session images
ls -lh /mnt/visual-aoi-shared/sessions/058ecb7f-a961-40de-832d-20588313a3cf/output/

# Count total images
find /mnt/visual-aoi-shared -name "*.jpg" | wc -l

# Get total storage size
du -sh /mnt/visual-aoi-shared/
```

### 2. HTTP API Access

**Flask Route:** `GET /shared/<path:filename>`

**Code:**

```python
@app.route("/shared/<path:filename>")
def serve_shared_file(filename):
    shared_base = "/mnt/visual-aoi-shared"
    safe_path = os.path.normpath(filename)
    full_path = os.path.join(shared_base, safe_path)
    return send_from_directory(directory, file_name)
```

**Examples:**

```bash
# Get ROI editor image
curl http://127.0.0.1:5100/shared/roi_editor/roi_editor_20251006_135508.jpg -o test.jpg

# Get session golden image
curl http://127.0.0.1:5100/shared/sessions/058ecb7f-a961-40de-832d-20588313a3cf/output/golden_5.jpg -o golden.jpg

# Get captured ROI image
curl http://127.0.0.1:5100/shared/sessions/058ecb7f-a961-40de-832d-20588313a3cf/output/roi_1.jpg -o roi.jpg
```

### 3. Web Browser Access

**ROI Editor:**

- Open: `http://127.0.0.1:5100/roi-editor`
- Capture image → automatically loads from `/shared/roi_editor/`

**Inspection Results:**

- Results display shows thumbnails from `/shared/sessions/{session_id}/output/`
- Click to zoom for full-size view

### 4. JavaScript Client Access

**ROI Editor (roi_editor.js):**

```javascript
// Capture image
const response = await fetch('/api/camera/capture', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ focus: 305, exposure: 1200 })
});

const data = await response.json();
// data.image_path = "roi_editor/roi_editor_20251006_135508.jpg"

// Display image
const imgUrl = `/shared/${data.image_path}`;
imageElement.src = imgUrl;
```

**Inspection Results (professional_index.html):**

```javascript
// Server returns absolute paths
const roi = {
    golden_image_path: "/mnt/visual-aoi-shared/sessions/xxx/output/golden_5.jpg",
    roi_image_path: "/mnt/visual-aoi-shared/sessions/xxx/output/roi_5.jpg"
};

// Convert to URL
const goldenUrl = roi.golden_image_path.replace('/mnt/visual-aoi-shared/', '/shared/');
// Result: "/shared/sessions/xxx/output/golden_5.jpg"
```

## Storage Management

### Current Storage Usage

**Check Storage:**

```bash
# Total size
du -sh /mnt/visual-aoi-shared/
# Example output: 328M

# ROI editor images
du -sh /mnt/visual-aoi-shared/roi_editor/
# Example output: 328M (30 images x ~11MB each)

# Session images
du -sh /mnt/visual-aoi-shared/sessions/
# Example output: varies (small cropped ROIs)
```

### Cleanup Strategies

#### 1. Manual Cleanup

**Remove old ROI editor images:**

```bash
# Delete images older than 7 days
find /mnt/visual-aoi-shared/roi_editor/ -name "*.jpg" -mtime +7 -delete

# Delete all ROI editor images (be careful!)
rm /mnt/visual-aoi-shared/roi_editor/*.jpg

# Keep only last 10 images
ls -t /mnt/visual-aoi-shared/roi_editor/*.jpg | tail -n +11 | xargs rm
```

**Remove old session folders:**

```bash
# Delete sessions older than 30 days
find /mnt/visual-aoi-shared/sessions/ -maxdepth 1 -type d -mtime +30 -exec rm -rf {} \;

# List sessions by size
du -sh /mnt/visual-aoi-shared/sessions/*/ | sort -h

# Delete specific session
rm -rf /mnt/visual-aoi-shared/sessions/058ecb7f-a961-40de-832d-20588313a3cf/
```

#### 2. Automated Cleanup (Future Enhancement)

**Cron Job Example:**

```bash
# Edit crontab
crontab -e

# Add cleanup job (runs daily at 2 AM)
0 2 * * * find /mnt/visual-aoi-shared/roi_editor/ -name "*.jpg" -mtime +7 -delete
0 2 * * * find /mnt/visual-aoi-shared/sessions/ -maxdepth 1 -type d -mtime +30 -exec rm -rf {} \;
```

**Python Script (Future):**

```python
# cleanup_images.py
import os
import time
from datetime import datetime, timedelta

def cleanup_old_images(path, days=7):
    """Remove images older than specified days."""
    cutoff = time.time() - (days * 86400)
    for filename in os.listdir(path):
        filepath = os.path.join(path, filename)
        if os.path.isfile(filepath) and os.path.getmtime(filepath) < cutoff:
            os.remove(filepath)
            print(f"Deleted: {filename}")

if __name__ == "__main__":
    cleanup_old_images("/mnt/visual-aoi-shared/roi_editor/", days=7)
```

## Image Properties

### ROI Editor Images (Full Resolution)

- **Resolution:** 7716 x 5360 pixels (41.3 megapixels)
- **Format:** JPEG
- **Quality:** 95% (OpenCV default)
- **Size:** 8-11 MB per image
- **Color Space:** BGR (OpenCV default)
- **Bit Depth:** 8-bit per channel

### Session ROI Images (Cropped)

- **Resolution:** Varies per ROI (e.g., 599×359, 226×191)
- **Format:** JPEG
- **Quality:** 95%
- **Size:** 13KB - 138KB per ROI
- **Source:** Extracted from full frame capture
- **Processing:** Cropped using ROI coordinates

## Security Considerations

### Path Traversal Protection

**Code (app.py, Line ~1761):**

```python
@app.route("/shared/<path:filename>")
def serve_shared_file(filename):
    # Security: prevent directory traversal
    safe_path = os.path.normpath(filename)
    if safe_path.startswith('..'):
        logger.warning(f"Attempted directory traversal: {filename}")
        return jsonify({"error": "Invalid path"}), 403
    
    full_path = os.path.join(shared_base, safe_path)
    
    # Check if file exists
    if not os.path.exists(full_path):
        return jsonify({"error": "File not found"}), 404
```

**Protection Against:**

- `../../../etc/passwd` - Blocked by `normpath()` check
- `/etc/passwd` - Outside shared base path
- `..%2F..%2Fetc%2Fpasswd` - URL encoding handled by Flask

### Access Control

**Current:** No authentication required (trusted local network)

**Future Enhancements:**

- Add API key authentication
- Implement per-session access tokens
- Add rate limiting for image serving

## Troubleshooting

### Image Not Found (404)

**Check:**

1. Verify file exists: `ls /mnt/visual-aoi-shared/roi_editor/roi_editor_20251006_135508.jpg`
2. Check permissions: `ls -l /mnt/visual-aoi-shared/roi_editor/`
3. Verify path in URL matches filesystem path

### Large Storage Usage

**Solutions:**

1. Run cleanup scripts (see Cleanup Strategies above)
2. Reduce capture frequency in ROI editor
3. Implement automatic session cleanup after inspection

### Permission Denied

**Check:**

```bash
# Verify ownership
ls -ld /mnt/visual-aoi-shared/

# Fix permissions if needed
sudo chown -R jason_nguyen:jason_nguyen /mnt/visual-aoi-shared/
sudo chmod -R 775 /mnt/visual-aoi-shared/
```

## Related Documentation

- [Client-Server Architecture](CLIENT_SERVER_ARCHITECTURE.md)
- [ROI Editor](PROJECT_STRUCTURE.md)
- [Camera Improvements](CAMERA_IMPROVEMENTS.md)
- [Session Management](SESSION_MANAGEMENT_FIX.md)

## Summary

### Quick Reference

| Type | Location | Size | Naming Pattern | Access URL |
|------|----------|------|----------------|------------|
| **ROI Editor** | `/mnt/visual-aoi-shared/roi_editor/` | 8-11 MB | `roi_editor_YYYYMMDD_HHMMSS.jpg` | `/shared/roi_editor/{filename}` |
| **Session Golden** | `/mnt/visual-aoi-shared/sessions/{session_id}/output/` | 13-138 KB | `golden_{roi_id}.jpg` | `/shared/sessions/{session_id}/output/golden_{roi_id}.jpg` |
| **Session ROI** | `/mnt/visual-aoi-shared/sessions/{session_id}/output/` | 13-138 KB | `roi_{roi_id}.jpg` | `/shared/sessions/{session_id}/output/roi_{roi_id}.jpg` |

### Key Points

✅ All images stored in shared folder: `/mnt/visual-aoi-shared/`  
✅ Access via HTTP: `http://127.0.0.1:5100/shared/{path}`  
✅ Path traversal protection implemented  
✅ ROI editor images: Full resolution (~11MB)  
✅ Session images: Cropped ROIs (13-138KB)  
✅ Manual cleanup recommended for old images  

### Next Steps

1. Implement automated cleanup scripts
2. Add image compression options
3. Create storage monitoring dashboard
4. Add image retention policies
