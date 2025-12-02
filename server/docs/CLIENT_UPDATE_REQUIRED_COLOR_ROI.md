# Client Update Required: Color ROI Type Support

**Date**: October 2025  
**Priority**: HIGH  
**Impact**: Client-side validation rejecting new color ROI type

## Problem

The server has implemented color checking ROI (type 4), but the client-side validation is rejecting it with this error:

```
roi_type_name must be one of ['barcode', 'compare', 'ocr', 'text'], got 'color'
```

**IMPORTANT**: The client's validation list is **incorrect** - there is no ROI type called 'text'. The correct ROI types are:

- Type 1: **barcode**
- Type 2: **compare**  
- Type 3: **ocr**
- Type 4: **color** (NEW - October 2025)

The client has a bug where 'text' appears in the validation list instead of 'color'.

**Current Client Validation:**

```python
allowed_types = ['barcode', 'compare', 'ocr', 'text']
```

**Required Update:**

```python
allowed_types = ['barcode', 'compare', 'ocr', 'text', 'color']
```

## ✅ Server-Side Status

The server-side has been fully updated to support color ROI type:

- ✅ ROI Type 4 processing implemented (`src/color_check.py`)
- ✅ Inspection pipeline handles type 4 (`src/inspection.py`)
- ✅ API result formatting includes color fields (`server/simple_api_server.py`)
- ✅ Schema documentation updated (line 4152, 4196-4220)
- ✅ Configuration endpoints created (`/api/products/{product}/colors`)

## Required Client-Side Changes

### 1. Update ROI Type Validation

**File**: Client-side ROI validation code (location TBD)

**Change**: Replace 'text' with 'color' in the validation list (and add 'color' if 'text' was correct)

```python
# Current (INCORRECT - 'text' does not exist as ROI type)
VALID_ROI_TYPES = ['barcode', 'compare', 'ocr', 'text']

# Correct (Replace 'text' with 'color')
VALID_ROI_TYPES = ['barcode', 'compare', 'ocr', 'color']
```

**Note**: If the client has both 'text' and needs 'color', the list should be:

```python
VALID_ROI_TYPES = ['barcode', 'compare', 'ocr', 'color']  # NO 'text'
```

### 2. Handle Color ROI Response Fields

When processing inspection results, handle the new color-specific fields:

```python
if roi_result['roi_type_name'] == 'color':
    detected_color = roi_result['detected_color']      # e.g., "red"
    match_percentage = roi_result['match_percentage']  # e.g., 87.5
    dominant_color = roi_result['dominant_color']      # e.g., [220, 45, 32]
    threshold = roi_result['threshold']                # e.g., 50.0
    passed = roi_result['passed']                      # True/False
```

### 3. Add Color Configuration UI (Optional)

If the client has a configuration UI, add support for managing color ranges:

```python
# Get color configuration
response = requests.get(f'{server_url}/api/products/{product_name}/colors')
color_ranges = response.json()['color_ranges']

# Save color configuration
color_config = {
    'color_ranges': [
        {
            'name': 'red',
            'lower': [200, 0, 0],
            'upper': [255, 100, 100],
            'color_space': 'RGB',
            'threshold': 50.0
        }
    ]
}
response = requests.post(
    f'{server_url}/api/products/{product_name}/colors',
    json=color_config
)
```

## 🎨 Color ROI Type Specifications

### ROI Configuration Format

```json
{
  "idx": 19,
  "type": 4,
  "coords": [100, 100, 200, 200],
  "focus": 305,
  "exposure": 1200,
  "device_location": 1
}
```

**Note:** Color ranges are configured separately via `/api/products/{product}/colors` endpoint, not in the ROI configuration.

### Response Format

```json
{
  "roi_id": 19,
  "device_id": 1,
  "roi_type_name": "color",
  "passed": true,
  "coordinates": [100, 100, 200, 200],
  "detected_color": "red",
  "match_percentage": 87.5,
  "match_percentage_raw": 95.3,
  "dominant_color": [220, 45, 32],
  "threshold": 50.0,
  "roi_image_path": "/mnt/visual-aoi-shared/sessions/{uuid}/output/roi_19.jpg"
}
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `detected_color` | string | Name of the color with highest match |
| `match_percentage` | float | Total match percentage (capped at 100%) |
| `match_percentage_raw` | float | Raw sum of all matches (can exceed 100%) |
| `dominant_color` | array[int] | RGB values [R, G, B] |
| `threshold` | float | Threshold percentage for pass/fail |
| `passed` | bool | True if match_percentage >= threshold |

## 🔧 Testing the Update

### 1. Update Client Validation

Make the change to allow 'color' in the validation list.

### 2. Create Test Color Configuration

```bash
curl -X POST http://10.100.10.83:5000/api/products/20000803/colors \
  -H "Content-Type: application/json" \
  -d '{
    "color_ranges": [
      {
        "name": "green",
        "lower": [0, 200, 0],
        "upper": [100, 255, 100],
        "color_space": "RGB",
        "threshold": 50.0
      }
    ]
  }'
```

### 3. Add Color ROI to Product

Edit `config/products/20000803/rois_config_20000803.json`:

```json
{
  "idx": 19,
  "type": 4,
  "coords": [100, 100, 200, 200],
  "focus": 305,
  "exposure": 1200,
  "device_location": 1
}
```

### 4. Run Inspection

The server will now process the color ROI and return color-specific results.

## 📊 ROI Type Mapping Reference

| ROI Type | Type Number | Type Name | Description |
|----------|-------------|-----------|-------------|
| Barcode | 1 | `barcode` | Barcode detection using Dynamsoft SDK |
| Compare | 2 | `compare` | Image comparison with golden sample |
| OCR | 3 | `ocr` or `text` | Text recognition using EasyOCR |
| **Color** | **4** | **`color`** | **Color validation (NEW)** |

**Note:** The client validation shows both 'ocr' and 'text' are accepted for OCR ROIs. The server normalizes these to lowercase.

## 🚀 Implementation Priority

**Priority: HIGH** - This is blocking the use of color ROI type 4 in product 20000803.

**Estimated Effort:** 15-30 minutes

- Update validation list: 5 minutes
- Add response field handling: 10 minutes
- Testing: 10 minutes

## 📞 Support

For questions about the color ROI feature, see:

- `docs/API_CLIENT_GUIDE.md` - Complete API documentation
- `docs/MULTIPLE_COLOR_RANGES_FEATURE.md` - Multi-range color support
- `docs/COLOR_CHECK_AND_API_DOCS_IMPLEMENTATION.md` - Implementation summary

The server is ready and waiting for the client update!
