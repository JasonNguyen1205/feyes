# Visual AOI Client - AI Coding Guidelines

## Project Overview
This is a Visual AOI (Automated Optical Inspection) **client application** that captures images from TIS industrial cameras and communicates with a separate server for processing. The client handles camera control, image capture, server communication, and result visualization with multi-device support.

## Architecture Patterns

### Client-Server Design
- **Client role**: Camera control, image capture, UI, result display
- **Communication**: REST API with base64 image encoding
- **Key insight**: Never implement inspection logic in client - it belongs on server

### Modular Structure
```
src/              # Core modules (camera, config, ui, roi)
app.py            # Main application entry point
tests/            # Comprehensive test suite with pytest
static/           # Static assets (CSS, JS)
templates/       # HTML templates for web UI
config/           # Configuration files (camera, theme)
docs/            # Documentation files - Updated instructions 
```


## Critical Conventions

### TIS Camera Integration
```python
# ALWAYS use BGRA format for TIS cameras
import TIS
camera.Set_Image_Format(TIS.SinkFormats.BGRA)

```

### Theme System
- UI uses iOS-inspired theme with "Liquid Glass" effects
- Theme switching: `set_theme('light')` or `set_theme('dark')`
- Apply themes: `apply_theme(widget)` after creating widgets
- Glass effects: `create_glass_frame()`, `apply_glass_effect()`

### Error Handling Patterns
- Graceful degradation when modules unavailable (TIS, AI libraries)
- Use try/except with fallback imports and mock classes
- Test suite automatically skips tests for missing dependencies

## Development Workflows

### Running the Client
```bash
# Legacy monolithic app (avoid)
python3 app.py
```

### Testing Strategy
```bash
# Install test dependencies first
pip3 install -r test-requirements.txt

# Quick validation
pytest tests/ -m "unit"

# Full test suite with coverage
pytest tests/ --cov=src --cov-report=html

# Test specific modules
pytest tests/test_camera.py -v
```

### Configuration Management
- Camera settings: `config/system/camera.json`
- Theme settings: `config/theme_settings.json`  
- Load via `src/config.py` functions: `get_camera_config()`, `load_camera_config()`

## Key Integration Points

### Server Communication Pattern
```python
# POST /api/session/{id}/inspect with base64 image
response = requests.post(f"{server_url}/api/session/{session_id}/inspect", 
                        json={"image": base64_image})

# Response structure includes device groupings:
```

### Multi-Device Result Processing
- Results grouped by device (1-4) not by ROI index
- Each device has independent pass/fail status
- Device passes only if ALL its ROIs pass
- Barcode tracking per device, not global

### UI Component Patterns
- Always apply theme after widget creation: `widget = tk.Frame(); apply_theme(widget)`
- Use glass effects for modern look: `frame = create_glass_frame(parent)`
- Status updates via `ui.set_status("message")`
- Result display uses device grouping format

## Performance Considerations

- Camera capture is blocking operation - use threading for UI responsiveness
- Base64 encoding/decoding for image transmission adds overhead
- Test suite includes performance markers: `@pytest.mark.slow`
- Memory management for large camera images (7716x5360 resolution)

## Common Gotchas

1. **Camera EBUSY errors**: Ensure only client accesses camera, never server
2. **Import resolution**: TIS module requires specific path setup
3. **Theme application**: Must apply after widget creation, not during
4. **Product selection**: Required at startup - affects all subsequent operations
5. **GTK dependencies**: Install via system package manager, not pip: `sudo apt-get install python3-gi`

## File Patterns to Follow

- Core logic in `src/` modules
- Tests mirror `src/` structure in `tests/`
- Documentation in `docs/` with descriptive filenames

## Updated Documentation
- `docs`: Contains all documentation files

## Inspection Results Display

### Server Response Schema
Server returns device-grouped results with detailed ROI information:

```json
{
  "device_summaries": {
    "1": {
      "device_id": 1,
      "device_passed": false,
      "barcode": "['20003548-0000003-1019720-101']",
      "passed_rois": 2,
      "total_rois": 3,
      "roi_results": [
        {
          "roi_id": 1,
          "passed": true,
          "ai_similarity": 0.8819,
          "roi_type_name": "barcode",
          "coordinates": [3459, 2959, 4058, 3318],
          "barcode_values": ["20003548-0000003-1019720-101"],
          "golden_image": "data:image/jpeg;base64,...",
          "capture_image_file": "group_305_1200.jpg"
        },
        {
          "roi_id": 6,
          "passed": true,
          "ai_similarity": 0.8819,
          "roi_type_name": "ocr",
          "coordinates": [3727, 4294, 3953, 4485],
          "ocr_text": "PCB"
        }
      ]
    }
  },
  "summary": {
    "overall_result": "PASS",
    "total_devices": 1,
    "pass_count": 1,
    "fail_count": 0
  }
}
```

### Client-Side Parsing (professional_index.html)

The `createResultsSummary()` function parses and displays:

1. **Device-Level Summary:**
   - Device ID, Pass/Fail status
   - Barcode identification
   - ROI counts (passed/total)

2. **ROI-Level Details:**
   - ROI ID and type (barcode, ocr, compare, etc.)
   - Pass/Fail status with visual indicators (✓/✗)
   - AI similarity percentage (0-100%)
   - Barcode values (for barcode ROIs)
   - OCR text (for OCR ROIs)
   - Bounding box coordinates [x1, y1, x2, y2]

3. **ROI Image Display (NEW):**
   - Golden sample images shown as inline thumbnails
   - Captured images displayed alongside golden samples
   - Click-to-zoom modal for full-size viewing
   - Graceful error handling for missing images
   - Smooth hover effects and animations

**Example Output:**
```
Device 1: FAIL
  Barcode: ['20003548-0000003-1019720-101']
  ROIs: 2/3 passed

  ROI Details:
    ROI 1 (barcode): ✓ PASS
      Similarity: 88.19%
      Barcode: ['20003548-0000003-1019720-101']
      Position: [3459, 2959, 4058, 3318]
    
    ROI 6 (ocr): ✓ PASS
      Similarity: 88.19%
      OCR Text: PCB
      Position: [3727, 4294, 3953, 4485]
```

### Schema Key Fields

**Device Summary Fields:**
- `device_passed` (boolean): Overall device pass/fail
- `barcode` (string): Device barcode identifier
- `passed_rois` (int): Count of passing ROIs
- `total_rois` (int): Total ROI count
- `roi_results` (array): Detailed ROI inspection results

**ROI Result Fields:**
- `roi_id` (int): ROI identifier from configuration
- `passed` (boolean): Individual ROI pass/fail
- `ai_similarity` (float): AI match score (0.0-1.0)
- `roi_type_name` (string): Type (barcode, ocr, compare, text)
- `coordinates` (array): Bounding box [x1, y1, x2, y2]
- `barcode_values` (array): Detected barcode strings
- `ocr_text` (string): Recognized text content
- `golden_image` (string): Base64 reference image
- `capture_image_file` (string): Captured image filename

## Server API for ROI configurations, Inspection Results schema:

- Server API: http://10.100.27.156:5000/apidocs/

Schema Endpoints:
- /api/schema/roi - ROI structure specification
- /api/schema/result - Inspection result structure (v2.0)
- /api/schema/version - Version compatibility info

**Schema Version:** v2.0 (as of October 3, 2025)  
**Client Support:** Full backward compatibility with v1.0 and v2.0  
**Documentation:** See docs/SCHEMA_V2_QUICK_REFERENCE.md


## Image Display Integration

### Image Loading Architecture
The client has **direct access** to the shared folder `/mnt/visual-aoi-shared/` and loads images from there, **NOT via API**.

### Image Path Handling

**Server Response Format:**
```json
{
  "roi_id": 1,
  "passed": true,
  "ai_similarity": 0.8819,
  "roi_type_name": "barcode",
  "golden_image_path": "/mnt/visual-aoi-shared/sessions/xxx/output/golden_5.jpg",
  "roi_image_path": "/mnt/visual-aoi-shared/sessions/xxx/output/roi_5.jpg",
  "coordinates": [3459, 2959, 4058, 3318],
  "barcode_values": ["20003548-0000003-1019720-101"]
}
```

**Client Path Conversion (professional_index.html):**
```javascript
// Server absolute path -> Client relative URL
// /mnt/visual-aoi-shared/sessions/xxx/output/golden_5.jpg
//   → /shared/sessions/xxx/output/golden_5.jpg

const relativePath = roi.golden_image_path.replace('/mnt/visual-aoi-shared/', '/shared/');
```

**Flask Route (app.py):**
```python
@app.route("/shared/<path:filename>")
def serve_shared_file(filename):
    """Serve files from /mnt/visual-aoi-shared/ folder."""
    shared_base = "/mnt/visual-aoi-shared"
    safe_path = os.path.normpath(filename)
    full_path = os.path.join(shared_base, safe_path)
    return send_from_directory(directory, file_name)
```

### Image Display Features

- **Golden Images**: Loaded from `golden_image_path` field via `/shared/` route
- **Captured Images**: Loaded from `roi_image_path` field via `/shared/` route
- **Fallback Support**: Base64-encoded images (e.g., `data:image/jpeg;base64,...`) still supported
- **Modal Zoom**: Click any thumbnail to open full-screen modal with backdrop blur
- **Error Fallback**: SVG placeholder with "Image Unavailable" if image fails to load
- **Responsive**: 2-column grid on desktop/tablet, single column on mobile

### Security Considerations

- **Directory Traversal Protection**: `os.path.normpath()` prevents `../` attacks
- **Path Validation**: Checks if file exists before serving
- **404 Handling**: Returns proper error if file not found
- **Access Control**: Only serves files from `/mnt/visual-aoi-shared/` base path

### Image Path Priority

1. **Base64 data** (starts with `data:image`) → Use directly
2. **File path from server** (`golden_image_path`, `roi_image_path`) → Convert to `/shared/` URL
3. **Legacy format** (`capture_image_file`) → Use `/static/captures/` path

**Example Implementation:**
```javascript
let goldenSrc = '';
if (roi.golden_image && roi.golden_image.startsWith('data:image')) {
    goldenSrc = roi.golden_image;  // Base64
} else if (roi.golden_image_path) {
    goldenSrc = roi.golden_image_path.replace('/mnt/visual-aoi-shared/', '/shared/');
}
```

## Custom Instructions for Agent
docs/*

## Critical: Shared Folder Image Loading
⚠️ **IMPORTANT**: The client has direct filesystem access to `/mnt/visual-aoi-shared/`. Images are served through Flask's `/shared/<path>` route, NOT through external APIs. Always convert absolute paths to relative `/shared/` URLs for client-side display.