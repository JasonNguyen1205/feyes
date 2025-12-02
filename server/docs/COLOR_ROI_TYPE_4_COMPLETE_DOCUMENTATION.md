# Color ROI Type 4 - Complete Documentation

**Date**: October 31, 2025  
**Feature**: Color Checking ROI (Type 4)  
**Status**: ✅ FULLY IMPLEMENTED & DOCUMENTED

---

## 📋 Executive Summary

The Visual AOI Server now supports **Color ROI (Type 4)** for validating colors in specific regions of inspected images. This feature includes:

- ✅ Color range validation with RGB/HSV support
- ✅ Multiple color ranges per color name (aggregated matching)
- ✅ RESTful API for color configuration management
- ✅ Full integration with inspection pipeline
- ✅ Comprehensive API documentation and schema updates

---

## 🎯 ROI Type Overview

| Type | Name | Description | Configuration |
|------|------|-------------|---------------|
| 1 | Barcode | Barcode detection/reading | None (Dynamsoft SDK) |
| 2 | Compare | AI similarity matching | Golden samples in `golden_rois/` |
| 3 | OCR | Text recognition | Optional expected_text field |
| 4 | **Color** | **Color validation** | **`colors_config_{product}.json`** |

---

## 🔧 Implementation Details

### ROI Structure (11-Field Format)

```python
color_roi = (
    4,                    # idx: ROI index
    4,                    # type: color (NEW TYPE)
    (500, 50, 600, 150),  # coords: (x1, y1, x2, y2)
    305,                  # focus: camera focus value
    3000,                 # exposure: exposure time in microseconds
    None,                 # ai_threshold: not used for color
    None,                 # feature_method: not used for color
    0,                    # rotation: 0/90/180/270 degrees
    1,                    # device_location: 1-4
    None,                 # expected_text: not used for color
    None                  # is_device_barcode: not applicable
)
```

### Configuration File Format

**Location**: `config/products/{product_name}/colors_config_{product_name}.json`

```json
{
  "color_ranges": [
    {
      "name": "red",
      "lower": [200, 0, 0],
      "upper": [255, 50, 50],
      "color_space": "RGB",
      "threshold": 50.0
    },
    {
      "name": "red",
      "lower": [150, 0, 0],
      "upper": [199, 30, 30],
      "color_space": "RGB",
      "threshold": 50.0
    },
    {
      "name": "blue",
      "lower": [0, 0, 200],
      "upper": [50, 50, 255],
      "color_space": "RGB",
      "threshold": 50.0
    }
  ]
}
```

**Key Features**:

- Multiple ranges can share the same `name` (e.g., "red")
- Ranges with same name have match percentages **summed**
- Supports both `RGB` and `HSV` color spaces
- Each range has individual threshold (typically use same threshold per color)

---

## 🌈 Multiple Color Ranges Feature

### Important: One ROI = One Color

**Each color ROI checks for ONE specific color only.** All ranges in a single ROI must have the same color name.

To check multiple colors (e.g., red AND blue), create **separate ROIs**:

- ROI #1: Checks red with multiple ranges
- ROI #2: Checks blue with multiple ranges

### Why Multiple Ranges Per Color?

Real-world colors have variations due to:

- Different brightness levels (dark red vs bright red)
- Lighting conditions (shadows, reflections)
- Material properties (matte vs glossy)
- Manufacturing tolerances

### How It Works

**Example: One ROI checking RED with 3 ranges**

```
Range 1 (Bright Red):  [200-255, 0-50, 0-50]     → 30% match
Range 2 (Dark Red):    [150-199, 0-30, 0-30]     → 25% match  
Range 3 (Pink Red):    [220-255, 50-100, 50-100] → 10% match
                                          TOTAL RED = 65%

Result: RED detected with 65% match
```

**To check BLUE, create a separate ROI:**

```
ROI #21: RED check (3 ranges) → 65% match
ROI #22: BLUE check (1 range) → 20% match
```

### Algorithm

```python
# 1. Group ranges by color name
color_matches = {}  # {color_name: {'total_percentage': float, ...}}

# 2. Process each range independently
for color_range in color_ranges:
    color_name = color_range['name']
    match_percentage = calculate_match(image, color_range)
    
    # 3. Aggregate by name
    if color_name not in color_matches:
        color_matches[color_name] = {'total_percentage': 0.0, ...}
    color_matches[color_name]['total_percentage'] += match_percentage

# 4. Find winner
best_match = max(color_matches, key=lambda k: color_matches[k]['total_percentage'])
```

---

## 🔌 API Endpoints

### 1. Get Color Configuration

```http
GET /api/products/{product_name}/colors
```

**Response**:

```json
{
  "product_name": "20003548",
  "color_ranges": [
    {
      "name": "red",
      "lower": [200, 0, 0],
      "upper": [255, 50, 50],
      "color_space": "RGB",
      "threshold": 50.0
    }
  ]
}
```

### 2. Save Color Configuration

```http
POST /api/products/{product_name}/colors
Content-Type: application/json

{
  "color_ranges": [...]
}
```

**Response**:

```json
{
  "message": "Color configuration saved successfully",
  "product_name": "20003548",
  "saved_at": "2025-10-31 14:30:45",
  "ranges_count": 3
}
```

### 3. Inspection with Color ROI

```http
POST /api/session/{session_id}/inspect
Content-Type: application/json

{
  "image_path": "/path/to/image.jpg",
  "rois": [
    {
      "idx": 1,
      "type": 4,
      "coords": [100, 100, 200, 200],
      "focus": 305,
      "exposure": 3000,
      "rotation": 0,
      "device_location": 1
    }
  ]
}
```

**Response** (roi_results section):

```json
{
  "roi_id": 1,
  "roi_type": 4,
  "roi_type_name": "color",
  "passed": true,
  "detected_color": "red",
  "match_percentage": 65.0,
  "match_percentage_raw": 65.0,
  "dominant_color": [220, 45, 32],
  "threshold": 50.0
}
```

**Result Fields**:

- `detected_color`: Name of color with highest total match
- `match_percentage`: Total aggregated match percentage (0-100)
- `match_percentage_raw`: Same as match_percentage (can exceed 100% if many ranges)
- `dominant_color`: RGB values `[R, G, B]` of most common color
- `threshold`: Required match percentage to pass
- `passed`: `match_percentage >= threshold`

---

## 📊 Schema Documentation

### `/api/schema/roi` Endpoint

Updated to include Color ROI (Type 4):

```json
{
  "version": "3.0",
  "roi_types": {
    "4": {
      "name": "Color",
      "description": "Color validation against defined color ranges",
      "relevant_fields": ["idx", "type", "coords", "focus", "exposure_time", "rotation", "device_location"],
      "ignored_fields": ["ai_threshold", "feature_method", "expected_text", "is_device_barcode"],
      "configuration": "Color ranges defined in config/products/{product}/colors_config_{product}.json",
      "note": "Supports multiple color ranges with same name (aggregated match percentages)"
    }
  },
  "example": {
    "color_roi": [4, 4, [500, 50, 600, 150], 305, 3000, null, null, 0, 1, null, null]
  }
}
```

### `/api/schema/result` Endpoint

Color result structure:

```json
{
  "roi_result_types": {
    "color": {
      "detected_color": {
        "type": "string",
        "required": true,
        "description": "Name of detected color"
      },
      "match_percentage": {
        "type": "float",
        "required": true,
        "description": "Total match (0-100)",
        "range": [0.0, 100.0]
      },
      "match_percentage_raw": {
        "type": "float",
        "required": false,
        "description": "Raw sum (can exceed 100%)"
      },
      "dominant_color": {
        "type": "array[int]",
        "required": true,
        "description": "RGB values [R, G, B]"
      },
      "threshold": {
        "type": "float",
        "required": true,
        "range": [0.0, 100.0]
      },
      "pass_condition": "match_percentage >= threshold",
      "note": "Supports multiple color ranges with same name (aggregated)"
    }
  }
}
```

---

## 🐛 Known Issues & Client Updates

### ⚠️ Client-Side Validation Error

**Error Message**:

```
roi_type_name must be one of ['barcode', 'compare', 'ocr', 'text'], got 'color'
```

**Problem**:

- Client has hardcoded validation list with **incorrect** 'text' type
- There is **NO** ROI type called 'text' in the server
- Server supports: `barcode`, `compare`, `ocr`, `color`

**Solution**: Client must update validation list

```python
# INCORRECT (Current client code)
VALID_ROI_TYPES = ['barcode', 'compare', 'ocr', 'text']

# CORRECT (Required fix)
VALID_ROI_TYPES = ['barcode', 'compare', 'ocr', 'color']
```

**Reference**: See `docs/CLIENT_UPDATE_REQUIRED_COLOR_ROI.md` for detailed instructions

---

## ✅ Verification Checklist

- [x] Color processing module created (`src/color_check.py`)
- [x] Inspection pipeline integration (`src/inspection.py` lines 200-226)
- [x] API result formatting (`server/simple_api_server.py` lines 729-746)
- [x] Color configuration endpoints (GET/POST)
- [x] Multiple range aggregation algorithm implemented
- [x] Schema documentation updated (line 4152, lines 4196-4220)
- [x] `/api/schema/roi` endpoint includes type 4 (lines ~3918, ~4023-4030, ~4066)
- [x] `/api/schema/result` endpoint includes color result structure
- [x] ROI specification document updated (`docs/ROI_DEFINITION_SPECIFICATION.md`)
- [x] Schema endpoints document updated (`docs/SCHEMA_API_ENDPOINTS.md`)
- [x] Testing: Color config save/retrieve working
- [x] Testing: Multiple ranges per color verified
- [x] Testing: All documentation endpoints accessible

---

## 📖 Related Documentation

- `docs/API_CLIENT_GUIDE.md` - Client integration guide
- `docs/COLOR_CHECK_AND_API_DOCS_IMPLEMENTATION.md` - Implementation summary
- `docs/MULTIPLE_COLOR_RANGES_FEATURE.md` - Multi-range feature details
- `docs/CLIENT_UPDATE_REQUIRED_COLOR_ROI.md` - Required client changes
- `docs/ROI_DEFINITION_SPECIFICATION.md` - Official ROI structure spec
- `docs/SCHEMA_API_ENDPOINTS.md` - Schema endpoint documentation

---

## 🧪 Testing Examples

### Python Test Script

```python
import requests

base_url = 'http://localhost:5000'
product = 'test_product'

# 1. Save color configuration
config = {
    'color_ranges': [
        {
            'name': 'red',
            'lower': [200, 0, 0],
            'upper': [255, 50, 50],
            'color_space': 'RGB',
            'threshold': 50.0
        }
    ]
}
response = requests.post(f'{base_url}/api/products/{product}/colors', json=config)
print(response.json())

# 2. Get color configuration
response = requests.get(f'{base_url}/api/products/{product}/colors')
print(response.json())

# 3. Get ROI schema
response = requests.get(f'{base_url}/api/schema/roi')
schema = response.json()
print(schema['roi_types']['4'])  # Color type

# 4. Inspect with color ROI
session_response = requests.post(f'{base_url}/api/session/create', json={'product_name': product})
session_id = session_response.json()['session_id']

inspect_data = {
    'image_path': '/path/to/image.jpg',
    'rois': [
        {
            'idx': 1,
            'type': 4,
            'coords': [100, 100, 200, 200],
            'focus': 305,
            'exposure': 3000,
            'rotation': 0,
            'device_location': 1
        }
    ]
}
response = requests.post(f'{base_url}/api/session/{session_id}/inspect', json=inspect_data)
result = response.json()
print(result['roi_results'][0])  # Color result
```

---

## 🚀 Next Steps for Clients

1. **Update validation list** to include 'color' type (remove 'text' if present)
2. **Call `/api/schema/roi`** to verify color type is supported
3. **Implement color configuration UI** using GET/POST endpoints
4. **Test color inspection** with sample images
5. **Handle color results** in inspection response

---

## 📞 Support

For questions or issues:

- Review API documentation at `http://{server_ip}:5000/api/docs`
- Check Swagger UI at `http://{server_ip}:5000/apidocs/`
- Review schema at `http://{server_ip}:5000/api/schema/roi`

**Last Updated**: October 31, 2025
