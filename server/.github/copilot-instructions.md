# Visual AOI Server - AI Coding Agent Instructions

## Project Architecture

This is a **distributed client-server Visual AOI (Automated Optical Inspection) system** with a Flask REST API backend (`server/simple_api_server.py`) that handles AI/ML inspection processing for multiple client applications. The server is completely camera-agnostic - all camera operations are deferred to clients to avoid resource conflicts.

### Key Architectural Patterns

- **Session-based workflow**: Each inspection creates a UUID session with product context and client info
- **Multi-device support**: ROIs have device_location field (1-4), results grouped by device with individual pass/fail
- **Flexible image transmission** (optimized October 2025, path conversion added November 2025):
  - **Input**: Prioritizes file paths over Base64 (99% smaller payloads, 195x faster)
    - **PREFERRED**: `image_filename` or `image_path` - client saves to shared folder, sends filename only
    - **LEGACY**: `image` (Base64) - supported for backward compatibility but discouraged
    - Three methods supported (priority order):
      1. `image_path` - absolute file path (client mount path automatically converted to server path)
      2. `image_filename` - relative to `/home/jason_nguyen/visual-aoi-server/shared/sessions/{uuid}/input/`
      3. `image` - Base64 data (backward compatibility)
    - **Path Conversion**: Client paths `/mnt/visual-aoi-shared/...` automatically converted to server paths `/home/jason_nguyen/visual-aoi-server/shared/...`
  - **Output**: Returns file paths (NOT base64) for ROI/golden images
    - Server saves images to `/home/jason_nguyen/visual-aoi-server/shared/sessions/{uuid}/output/`
    - Client accesses via CIFS mount: `/mnt/visual-aoi-shared/sessions/{uuid}/output/`
    - Response contains `roi_image_path` and `golden_image_path` fields (99% smaller responses)
- **ROI-driven processing**: Inspection configs use object-based ROI format with named properties: `{"idx": 1, "type": 2, "coords": [...], "focus": 305, "exposure": 1200, "ai_threshold": 0.93, "feature_method": "mobilenet", "rotation": 0, "device_location": 1, "sample_text": null, "is_device_barcode": null}`. Internally normalized to 11-field tuples for processing.
- **Parallel ROI processing** (October 2025): ROIs processed simultaneously using ThreadPoolExecutor for 2-10x speedup
- **Enhanced golden matching**: Uses `best_golden.jpg` with automatic promotion of better-matching alternatives
- **Barcode linking** (October 2025): Device barcodes validated/transformed through external API (`http://10.100.10.83:5000/api/ProcessLock/FA/GetLinkData`) with graceful fallback. Supports two input methods: ROI-scanned barcodes and client-provided barcodes (both apply linking)

## Core Modules & Data Flow

```
Client → API Server → ROI Processing → AI/OCR/Barcode → Device Results → Save Images
  (file path preferred)  (src/inspection.py)  (src/ai_pytorch.py)  (grouped by device_location)  (paths out)
  (Base64 legacy)
```

### Critical Processing Pipeline

1. **Session creation** (`/api/session/create`) - links product config to session UUID
2. **Image inspection** (`/api/session/{id}/inspect`) - processes Base64 image through ROI pipeline
3. **Parallel ROI dispatch** (`server/simple_api_server.py::run_real_inspection`) - processes all ROIs simultaneously via ThreadPoolExecutor
4. **ROI processing** (`src/inspection.py::process_roi`) - routes to compare/barcode/OCR by roi[1] type
5. **Barcode linking** (`src/barcode_linking.py`) - validates device barcodes through external API with 3s timeout and fallback
6. **Feature extraction** (`src/ai_pytorch.py`) - PyTorch MobileNetV2 for RTX 5080 compatibility
7. **Device grouping** - results aggregated by ROI device_location field

## Development Patterns

### Configuration Management

- **Product configs**: `config/products/{product_id}/rois_config_{product_id}.json` - uses object-based format with named properties (see ROI_FORMAT_MIGRATION.md)
- **Camera config**: `config/system/camera.json` (client-side only)
- **Golden samples**: `config/products/{product}/golden_rois/roi_{idx}/best_golden.jpg`
- **Shared folder**: `/home/jason_nguyen/visual-aoi-server/shared/` - CIFS/Samba share for client-server file exchange
- Use `src/config.py` functions (`get_camera_config()`) instead of constants

### ROI Configuration Format

ROIs are stored in object format with named properties for better readability:

**Type 1 (Barcode), Type 2 (Compare), Type 3 (OCR):**

```json
{
  "idx": 1,
  "type": 2,
  "coords": [x1, y1, x2, y2],
  "focus": 305,
  "exposure": 1200,
  "ai_threshold": 0.93,
  "feature_method": "mobilenet",
  "rotation": 0,
  "device_location": 1,
  "expected_text": null,
  "is_device_barcode": null
}
```

**Type 4 (Color) - November 2025 Update:**

```json
{
  "idx": 21,
  "type": 4,
  "coords": [x1, y1, x2, y2],
  "focus": 245,
  "exposure": 800,
  "rotation": 0,
  "device_location": 1,
  "expected_color": [0, 0, 0],
  "color_tolerance": 50,
  "min_pixel_percentage": 70.0,
  "ai_threshold": null,
  "feature_method": null,
  "expected_text": null,
  "is_device_barcode": null
}
```

**Color Detection Uses Predefined Ranges:**

- Black: RGB(0-50, 0-50, 0-50)
- White: RGB(230-255, 230-255, 230-255)
- Red, Green, Blue, Yellow, Orange, Purple, Pink, Brown, Cyan, Gray
- System automatically maps `expected_color` to standard ranges
- Includes color normalization for lighting variations

The `normalize_roi()` function supports both object and legacy array formats for backward compatibility.

### ROI Processing Types

```python
# Type 1: Barcode → src/barcode.py::process_barcode_roi()
# Type 2: Compare → src/roi.py::process_compare_roi()
# Type 3: OCR → src/ocr.py::process_ocr_roi()
```

### AI/ML Integration

- **Primary**: PyTorch MobileNetV2 (`src/ai_pytorch.py`) for RTX 5080 support
- **Fallback**: OpenCV SIFT/ORB features when PyTorch unavailable
- **Feature extraction**: `extract_features_from_array(img, feature_method="mobilenet")`
- **GPU detection**: Automatic CUDA detection with CPU fallback

### Testing Infrastructure

- **Pytest with markers**: `@pytest.mark.{unit,integration,slow,camera,ai,barcode,ui}`
- **Test runner**: `tests/test_runner.py` with mock factories for missing dependencies
- **Coverage**: Run `pytest --cov=src --cov-report=html`
- **Hardware mocking**: Tests automatically skip/mock camera/GPU dependencies

## Essential Commands

```bash
# Server development
python server/simple_api_server.py --debug --host 0.0.0.0 --port 5000

# Testing
pytest tests/ -m "unit"                    # Unit tests only
pytest tests/ -m "not slow"                # Skip slow tests
pytest tests/test_ai.py -k "mobilenet"     # Specific test pattern

# Dependencies
pip install -r requirements.txt            # Core runtime deps
pip install -r requirements-system.txt     # System-level deps
```

## Common Gotchas

1. **Camera operations on server**: Server should NEVER do camera operations - always client-side
2. **Image output format**: API returns `roi_image_path` and `golden_image_path` (file paths with `/mnt/visual-aoi-shared/` prefix), NOT base64 data
3. **Image path format**: Returned paths include full client mount prefix: `/mnt/visual-aoi-shared/sessions/{uuid}/output/roi_5.jpg` (directly usable by client)
4. **Client/Server path conversion**: Client mount paths `/mnt/visual-aoi-shared/...` automatically converted to server paths `/home/jason_nguyen/visual-aoi-server/shared/...` by API
5. **ROI normalization**: Use `roi.normalize_roi()` when loading configs to handle legacy formats
6. **Device barcodes format**: `device_barcodes` accepts both dict `{'1': 'barcode'}` and list `[{'device_id': 1, 'barcode': '...'}]` formats via `normalize_device_barcodes()`
7. **Golden image promotion**: `process_compare_roi()` automatically promotes better-matching alternatives to `best_golden.jpg`
8. **Session cleanup**: Server runs background thread to cleanup expired sessions (1 hour timeout)
9. **PyTorch RTX 5080**: Better compatibility than TensorFlow for RTX 5080 - prefer PyTorch implementations
10. **Color ROI validation**: Server validates Color ROIs on save, adds defaults (color_tolerance, min_pixel_percentage), and ensures correct v3.2 format
11. **Field naming**: Always use `exposure` (not `exposure_time`) in configs and code

## Product-Specific Conventions

- **Multi-device configs**: ROI device_location determines which device processes which ROIs
- **Golden sample management**: Each ROI has dedicated `golden_rois/roi_{idx}/` directory with versioned samples
- **OCR sample text**: ROI[9] field contains expected text for pass/fail comparison
- **Feature methods**: "mobilenet" (PyTorch), "opencv" (SIFT/ORB), "barcode" (Dynamsoft)
- **Result format**: Always include device_summaries with per-device pass/fail and barcode info. Images are saved to shared folder and paths returned (NOT base64)

Focus on the session-based API workflow, multi-device ROI processing, and PyTorch AI integration when making changes. The codebase heavily emphasizes graceful degradation when dependencies are missing.

## Golden Sample Management API

The server provides comprehensive golden sample management endpoints for uploading, managing, and accessing reference images used in ROI comparison. **All endpoints follow the architecture pattern of returning file paths instead of Base64 data** (99.6% smaller responses).

### Golden Sample Directory Structure

```
config/products/{product_name}/golden_rois/
  ├── roi_1/
  │   ├── best_golden.jpg              # Current best golden sample
  │   └── original_1696377600_old_best.jpg  # Timestamped backup
  ├── roi_2/
  │   └── best_golden.jpg
  └── ...
```

### Client Access via CIFS Mount

- **Server path**: `/home/jason_nguyen/visual-aoi-server/config/products/{product}/golden_rois/`
- **Client mount**: `/mnt/visual-aoi-shared/golden/{product}/golden_rois/`
- **Symlink**: `shared/golden` → `../config/products` (created for client access)

### API Endpoints

#### 1. **List All Products with Golden Samples**

```http
GET /api/golden-sample/products
```

Returns all products that have golden samples with summary statistics.

**Response:**

```json
{
  "products": [
    {
      "product_name": "20003548",
      "total_rois": 2,
      "total_samples": 2,
      "total_size": 110148,
      "rois": [3, 5]
    }
  ],
  "total_products": 1
}
```

#### 2. **Get Golden Samples for ROI (File Paths)**

```http
GET /api/golden-sample/{product_name}/{roi_id}
GET /api/golden-sample/{product_name}/{roi_id}?include_images=true  # Backward compat
```

Returns golden samples with client-accessible file paths (99.6% smaller than Base64).

**Response (default):**

```json
{
  "golden_samples": [
    {
      "name": "best_golden.jpg",
      "type": "best_golden",
      "is_best": true,
      "created_time": "2025-10-04 00:20:42",
      "file_size": 40375,
      "file_path": "/mnt/visual-aoi-shared/golden/20003548/roi_3/best_golden.jpg"
    }
  ]
}
```

**Query Parameters:**

- `include_images=true` - Include Base64 data for backward compatibility (adds `image_data` field)

#### 3. **Get Golden Sample Metadata (Lightweight)**

```http
GET /api/golden-sample/{product_name}/{roi_id}/metadata
```

Returns metadata without image data or file paths. Perfect for quick queries.

**Response:**

```json
{
  "product_name": "20003548",
  "roi_id": 3,
  "golden_samples": [
    {
      "name": "best_golden.jpg",
      "type": "best_golden",
      "is_best": true,
      "created_time": "2025-10-04 00:20:42",
      "file_size": 40375
    }
  ],
  "total_samples": 1,
  "total_size": 40375
}
```

#### 4. **Download Golden Sample Image**

```http
GET /api/golden-sample/{product_name}/{roi_id}/download/{filename}
```

Streams a golden sample image file for download. Includes path traversal protection.

**Response:** Binary JPEG image with `Content-Disposition: attachment`

**Security:** Blocks filenames with `..`, `/`, or `\\` characters

#### 5. **Upload/Save Golden Sample**

```http
POST /api/golden-sample/save
Content-Type: multipart/form-data
```

Upload a new golden sample image. Automatically backs up existing `best_golden.jpg`.

**Form Data:**

- `product_name` (string, required)
- `roi_id` (string, required)
- `golden_image` (file, required)

**Response:**

```json
{
  "message": "Golden sample saved as 'best_golden.jpg' for ROI 3. Old golden sample backed up as 'original_1759512042_old_best.jpg'",
  "backup_info": "Old golden sample backed up as 'original_1759512042_old_best.jpg'"
}
```

#### 6. **Promote Alternative to Best Golden**

```http
POST /api/golden-sample/promote
Content-Type: application/json
```

Manually promote an alternative golden sample to become `best_golden.jpg`.

**Request Body:**

```json
{
  "product_name": "20003548",
  "roi_id": 3,
  "sample_name": "original_1696377600_old_best.jpg"
}
```

**Response:**

```json
{
  "message": "'original_1696377600_old_best.jpg' promoted to best golden sample"
}
```

**Note:** Automatic promotion also happens during inspection when a better-matching alternative is found.

#### 7. **Restore from Backup**

```http
POST /api/golden-sample/restore
Content-Type: application/json
```

Restore a previously backed-up golden sample to become the current best.

**Request Body:**

```json
{
  "product_name": "20003548",
  "roi_id": 3,
  "backup_filename": "original_1696377600_old_best.jpg"
}
```

**Response:**

```json
{
  "message": "Successfully restored 'original_1696377600_old_best.jpg' to best golden sample",
  "restored_from": "original_1696377600_old_best.jpg",
  "backed_up_current": "Current best golden backed up as 'original_1759513245_old_best.jpg'"
}
```

**Security:** Only accepts filenames matching pattern `original_*_old_best.jpg`

#### 8. **Delete Golden Sample**

```http
DELETE /api/golden-sample/delete
Content-Type: application/json
```

Delete a specific golden sample. Prevents deletion of `best_golden.jpg` if it's the only sample.

**Request Body:**

```json
{
  "product_name": "20003548",
  "roi_id": 3,
  "sample_name": "original_1696377600_old_best.jpg"
}
```

**Response:**

```json
{
  "message": "Golden sample 'original_1696377600_old_best.jpg' deleted successfully"
}
```

**Protection:** Cannot delete `best_golden.jpg` if it's the only golden sample in the ROI.

#### 9. **Rename ROI Folders (Internal)**

```http
POST /api/golden-sample/rename-folders
Content-Type: application/json
```

Rename golden sample folders when ROI indices change after ROI deletion/reordering.

**Request Body:**

```json
{
  "product_name": "20003548",
  "roi_mapping": {
    "5": 4,
    "6": 5
  }
}
```

### Usage Examples

**Python Client Example:**

```python
import requests

# List all products
response = requests.get('http://server:5000/api/golden-sample/products')
products = response.json()['products']

# Get golden samples with file paths
response = requests.get('http://server:5000/api/golden-sample/20003548/3')
samples = response.json()['golden_samples']
best_golden_path = samples[0]['file_path']  # /mnt/visual-aoi-shared/golden/20003548/roi_3/best_golden.jpg

# Download golden image
response = requests.get('http://server:5000/api/golden-sample/20003548/3/download/best_golden.jpg')
with open('best_golden.jpg', 'wb') as f:
    f.write(response.content)

# Upload new golden sample
files = {'golden_image': open('new_golden.jpg', 'rb')}
data = {'product_name': '20003548', 'roi_id': '3'}
response = requests.post('http://server:5000/api/golden-sample/save', files=files, data=data)

# Restore from backup
data = {
    'product_name': '20003548',
    'roi_id': 3,
    'backup_filename': 'original_1696377600_old_best.jpg'
}
response = requests.post('http://server:5000/api/golden-sample/restore', json=data)
```

### Performance Benefits

**Response Size Comparison** (tested with product 20003548, ROI 3):

- **With file paths only**: 214 bytes
- **With Base64 image data**: 54,089 bytes
- **Size reduction**: 99.6% (53,875 bytes saved per request)

**Recommendations:**

1. Always use default GET endpoint (file paths) unless you need Base64 data
2. Use metadata endpoint for quick queries without downloading images
3. Use download endpoint when you need the actual image file
4. Client should access images directly via CIFS mount at `/mnt/visual-aoi-shared/golden/`

### Testing

Run the golden sample API test suite:

```bash
pytest tests/test_golden_sample_api.py -v
```

Tests verify:

- ✅ File path format instead of Base64 data (99.6% size reduction)
- ✅ Metadata endpoint returns lightweight summaries
- ✅ Download endpoint streams images correctly
- ✅ Path traversal protection works
- ✅ Restore endpoint validates backup filenames
- ✅ Error handling for missing products/files

## Required Behaviors for agent

- When generating or modifying code, ensure it adheres to the established architecture patterns and coding conventions outlined in this document.
- Ensure all new features integrate seamlessly with existing modules and maintain the modular structure.
- Prioritize error handling and user experience in all UI components.

## API Documentation Generation

### Swagger/OpenAPI Documentation

The server automatically generates Swagger/OpenAPI documentation from code docstrings using Flasgger. Key steps:

1. Add new endpoint to `server/simple_api_server.py`
2. Include docstring with `---` separator
3. Define tags, parameters, responses
4. Restart server
5. Documentation auto-generated

### For Integrators

1. Download spec: http://<server_ip>:5000/apispec_1.json
2. Generate client code using OpenAPI generator
3. Import into API testing tools
4. Use for contract testing

---

## 🎯 Benefit

Streamlined API integration and testing process
