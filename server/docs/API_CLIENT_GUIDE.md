# Visual AOI Server - Client Integration Guide

**API Version:** 1.0.0  
**Last Updated:** October 31, 2025

## 🌐 API Documentation Access

### Quick Links

- **Swagger UI (Interactive):** `http://{server_ip}:5000/apidocs/`
- **OpenAPI Spec (JSON):** `http://{server_ip}:5000/apispec_1.json`
- **API Endpoints List:** `http://{server_ip}:5000/api/docs`
- **Health Check:** `http://{server_ip}:5000/api/health`

Replace `{server_ip}` with your actual server IP address (e.g., `10.100.10.83`).

## 🚀 Getting Started

### 1. Check Server Health

```bash
curl http://10.100.10.83:5000/api/health
```

**Response:**

```json
{
  "status": "healthy",
  "timestamp": "2025-10-31T10:30:00",
  "modules_available": true,
  "initialized": true,
  "active_sessions": 3
}
```

### 2. Get API Documentation

```bash
curl http://10.100.10.83:5000/api/docs
```

This returns a comprehensive JSON structure with all available endpoints, parameters, and usage examples.

### 3. Access Interactive Documentation

Open your web browser and navigate to:

```
http://10.100.10.83:5000/apidocs/
```

This provides an interactive Swagger UI where you can:

- Browse all API endpoints
- View request/response schemas
- Test endpoints directly from the browser
- See example requests and responses

## 📝 Common Workflows

### Workflow 1: Create Session and Run Inspection

```python
import requests
import base64

# 1. Create session
response = requests.post('http://10.100.10.83:5000/api/session/create', 
    json={
        'product_name': '20003548',
        'client_info': {'client_id': 'station_1', 'version': '1.0'}
    }
)
session_id = response.json()['session_id']

# 2. Run inspection (using file path - PREFERRED method)
response = requests.post(
    f'http://10.100.10.83:5000/api/session/{session_id}/grouped_inspect',
    json={
        'image_path': '/path/to/image.jpg',  # Absolute path (99% smaller!)
        'device_barcodes': []  # Empty if no manual barcodes
    }
)

# 3. Get results
results = response.json()
print(f"Overall Pass: {results['overall_result']['passed']}")
print(f"Device 1 Pass: {results['device_summaries']['1']['device_passed']}")

# 4. Access ROI images via CIFS mount
for roi in results['roi_results']:
    roi_image = roi['roi_image_path']  # e.g., /mnt/visual-aoi-shared/sessions/{uuid}/output/roi_1.jpg
    # Use this path directly in your client application
```

### Workflow 2: Configure Color Checking (NEW)

```python
import requests

product_name = '20003548'

# 1. Define color ranges
# NOTE: You can define MULTIPLE ranges for the SAME color name!
# This is useful for covering different brightness/saturation levels
color_config = {
    'color_ranges': [
        {
            'name': 'red',
            'lower': [200, 0, 0],
            'upper': [255, 100, 100],
            'color_space': 'RGB',
            'threshold': 50.0
        },
        {
            'name': 'red',  # Same color, different range (dark red)
            'lower': [150, 0, 0],
            'upper': [199, 50, 50],
            'color_space': 'RGB',
            'threshold': 50.0
        },
        {
            'name': 'green',
            'lower': [60, 50, 50],
            'upper': [90, 255, 255],
            'color_space': 'HSV',
            'threshold': 60.0
        }
    ]
}

# The system will:
# 1. Calculate match percentage for each range independently
# 2. SUM all match percentages for ranges with the same name
# 3. Return the color with the highest total match percentage

# 2. Save color configuration
response = requests.post(
    f'http://10.100.10.83:5000/api/products/{product_name}/colors',
    json=color_config
)
print(response.json()['message'])

# 3. Get color configuration
response = requests.get(
    f'http://10.100.10.83:5000/api/products/{product_name}/colors'
)
colors = response.json()['color_ranges']
```

### Workflow 3: Manage Golden Samples

```python
import requests

product_name = '20003548'
roi_id = 3

# 1. Upload new golden sample
files = {'golden_image': open('new_golden.jpg', 'rb')}
data = {'product_name': product_name, 'roi_id': roi_id}
response = requests.post(
    'http://10.100.10.83:5000/api/golden-sample/save',
    files=files,
    data=data
)

# 2. Get golden samples (returns file paths, NOT base64)
response = requests.get(
    f'http://10.100.10.83:5000/api/golden-sample/{product_name}/{roi_id}'
)
samples = response.json()['golden_samples']
best_golden_path = samples[0]['file_path']
# Path: /mnt/visual-aoi-shared/golden/20003548/roi_3/best_golden.jpg

# 3. Download golden image
response = requests.get(
    f'http://10.100.10.83:5000/api/golden-sample/{product_name}/{roi_id}/download/best_golden.jpg'
)
with open('downloaded_golden.jpg', 'wb') as f:
    f.write(response.content)
```

## 🎨 ROI Types

The server supports 4 types of ROI processing:

### Type 1: Barcode

- **Description:** Barcode detection using Dynamsoft SDK
- **Returns:** `barcode_values` (list of detected barcodes)
- **Pass Criteria:** At least one barcode detected

### Type 2: Compare (Image Matching)

- **Description:** Compare captured ROI with golden sample
- **Returns:** `ai_similarity`, `threshold`, `match_result`
- **Pass Criteria:** `similarity >= threshold`

### Type 3: OCR (Text Recognition)

- **Description:** Text recognition using EasyOCR
- **Returns:** `ocr_text` with [PASS]/[FAIL] tags
- **Pass Criteria:** Expected text found (if specified)

### Type 4: Color Check (NEW ✨)

- **Description:** Validates ROI color against defined ranges
- **Returns:** `detected_color`, `match_percentage`, `dominant_color`, `threshold`
- **Pass Criteria:** `match_percentage >= threshold`
- **Configuration:** Use `/api/products/{product}/colors` endpoints

**Advanced Feature: Multiple Ranges Per Color**

You can define **multiple color ranges with the same name** to cover variations:

```json
{
  "color_ranges": [
    {"name": "red", "lower": [200, 0, 0], "upper": [255, 50, 50]},   // Bright red
    {"name": "red", "lower": [150, 0, 0], "upper": [199, 30, 30]},   // Dark red
    {"name": "red", "lower": [220, 50, 50], "upper": [255, 100, 100]} // Pink/light red
  ]
}
```

**How it works:**

1. Each range is checked independently
2. Match percentages for ranges with the **same name** are **summed**
3. The color with the **highest total** is returned
4. Example: If 30% matches bright red + 25% matches dark red = 55% total red match

**Benefits:**

- Cover entire color spectrum (light to dark)
- Handle different saturation levels
- More robust color detection
- Reduce false negatives

**Example Color ROI Response:**

```json
{
  "roi_id": 5,
  "roi_type_name": "color",
  "passed": true,
  "detected_color": "red",
  "match_percentage": 87.5,
  "dominant_color": [220, 45, 32],
  "threshold": 50.0,
  "roi_image_path": "/mnt/visual-aoi-shared/sessions/{uuid}/output/roi_5.jpg"
}
```

## 📊 Image Transmission Methods

### Input (Priority Order)

1. **`image_path`** (PREFERRED ⭐)
   - Absolute file path to image
   - **Benefits:** 99% smaller payload, 195x faster
   - **Example:** `"/path/to/image.jpg"`

2. **`image_filename`**
   - Relative to `/home/jason_nguyen/visual-aoi-server/shared/sessions/{uuid}/input/`
   - **Example:** `"capture_001.jpg"`

3. **`image`** (LEGACY)
   - Base64 encoded image data
   - **Note:** Supported for backward compatibility only
   - **Not Recommended:** Large payload size

### Output (File Paths Only)

The server returns **file paths** to images, NOT base64 data:

```json
{
  "roi_image_path": "/mnt/visual-aoi-shared/sessions/{uuid}/output/roi_1.jpg",
  "golden_image_path": "/mnt/visual-aoi-shared/sessions/{uuid}/output/golden_1.jpg"
}
```

**Client Access:**

- Mount CIFS share at `/mnt/visual-aoi-shared/`
- Use paths directly in your application
- 99.6% smaller responses compared to base64

## 🗂️ File System Structure

```
Server Side:
/home/jason_nguyen/visual-aoi-server/
  ├── config/products/{product}/
  │   ├── rois_config_{product}.json        # ROI definitions
  │   ├── colors_config_{product}.json      # Color ranges (NEW)
  │   └── golden_rois/roi_{id}/
  │       ├── best_golden.jpg               # Current best
  │       └── original_*_old_best.jpg       # Backups
  └── shared/
      ├── sessions/{uuid}/
      │   ├── input/                        # Client uploads here
      │   └── output/                       # Server saves results
      └── golden/ → ../config/products/     # Symlink for client access

Client Side (CIFS Mount):
/mnt/visual-aoi-shared/
  ├── sessions/{uuid}/output/               # ROI result images
  └── golden/{product}/golden_rois/         # Golden sample images
```

## 🔑 Key Endpoints Reference

### System

- `GET /api/health` - Health check
- `POST /api/initialize` - Initialize AI models
- `GET /api/docs` - API documentation (this guide)

### Sessions

- `POST /api/session/create` - Create session
- `GET /api/session/{id}` - Get session info
- `POST /api/session/{id}/grouped_inspect` - Run inspection
- `DELETE /api/session/{id}` - Delete session

### Products

- `GET /api/products` - List products
- `GET /api/products/{product}/rois` - Get ROI config
- `POST /api/products/{product}/rois` - Save ROI config
- `GET /api/products/{product}/colors` - Get color config (NEW)
- `POST /api/products/{product}/colors` - Save color config (NEW)

### Golden Samples

- `GET /api/golden-sample/products` - List products
- `GET /api/golden-sample/{product}/{roi_id}` - Get samples (file paths)
- `GET /api/golden-sample/{product}/{roi_id}/metadata` - Lightweight metadata
- `GET /api/golden-sample/{product}/{roi_id}/download/{filename}` - Download image
- `POST /api/golden-sample/save` - Upload golden sample
- `POST /api/golden-sample/promote` - Promote alternative
- `POST /api/golden-sample/restore` - Restore backup
- `DELETE /api/golden-sample/delete` - Delete sample

## 🛠️ Code Generation Tools

### Generate Client Code from OpenAPI Spec

1. **Download OpenAPI spec:**

```bash
curl http://10.100.10.83:5000/apispec_1.json -o openapi.json
```

2. **Generate Python client:**

```bash
openapi-generator-cli generate \
  -i openapi.json \
  -g python \
  -o ./visual-aoi-client
```

3. **Generate C# client:**

```bash
openapi-generator-cli generate \
  -i openapi.json \
  -g csharp \
  -o ./visual-aoi-client-csharp
```

4. **Generate TypeScript/JavaScript client:**

```bash
openapi-generator-cli generate \
  -i openapi.json \
  -g typescript-axios \
  -o ./visual-aoi-client-ts
```

## 📞 Support

For detailed technical documentation, see:

- `/docs/CLIENT_SERVER_ARCHITECTURE.md`
- `/docs/GOLDEN_SAMPLE_MANAGEMENT.md`
- `/docs/MULTI_DEVICE_IMPLEMENTATION.md`

For API issues or questions, refer to the interactive Swagger UI at `/apidocs/`.
