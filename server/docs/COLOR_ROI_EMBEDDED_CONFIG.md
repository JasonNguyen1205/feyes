# Color ROI with Embedded Configuration (v3.1)

**Date**: October 31, 2025  
**Version**: 3.1  
**Feature**: Embedded color_ranges in ROI configuration

---

## 🎯 Overview

Color ROIs now support **embedded color range configuration** directly in the ROI definition. This eliminates the need for a separate `colors_config_{product}.json` file and allows different color ROIs to have different color ranges.

### Key Benefits

- ✅ **Per-ROI configuration**: Each color ROI can have its own color ranges
- ✅ **No separate files**: Color ranges embedded directly in ROI config
- ✅ **Easier management**: All ROI data in one place
- ✅ **Backward compatible**: Falls back to product-level config if not specified

---

## 📐 ROI Structure v3.1 (12-Field Format)

### New Field: color_ranges (Field 11)

```python
roi = (
    idx,              # Field 0: ROI index (int, 1-based)
    typ,              # Field 1: ROI type (int: 1=Barcode, 2=Compare, 3=OCR, 4=Color)
    coords,           # Field 2: Coordinates tuple (x1, y1, x2, y2)
    focus,            # Field 3: Focus value (int)
    exposure_time,    # Field 4: Exposure time in microseconds (int)
    ai_threshold,     # Field 5: AI similarity threshold (float or None)
    feature_method,   # Field 6: Feature extraction method (str or None)
    rotation,         # Field 7: Rotation angle in degrees (int)
    device_location,  # Field 8: Device identifier (int, 1-4)
    expected_text,    # Field 9: Expected text for OCR (str or None)
    is_device_barcode,# Field 10: Device barcode flag (bool or None)
    color_ranges      # Field 11: Color ranges for Color ROI (array or None) - NEW in v3.1
)
```

---

## 🎨 Color Ranges Format

### Structure (Single Color ROI Example)

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
    }
  ]
}
```

**Important:** All ranges in one ROI must check for the SAME color (e.g., all "red"). To check different colors, create separate ROIs.

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Color name (e.g., "red", "blue", "green") |
| `lower` | array[int, int, int] | Yes | Lower bound RGB or HSV values |
| `upper` | array[int, int, int] | Yes | Upper bound RGB or HSV values |
| `color_space` | string | Yes | "RGB" or "HSV" |
| `threshold` | float | Yes | Match percentage threshold (0-100) |

### Important: One ROI = One Color

**Each color ROI checks for ONE specific color only.** If you need to check multiple colors, create multiple ROIs.

However, each color can have **multiple ranges** to handle variations in brightness, lighting, or material properties:

```json
{
  "color_ranges": [
    {"name": "red", "lower": [200, 0, 0], "upper": [255, 50, 50], "color_space": "RGB", "threshold": 50.0},
    {"name": "red", "lower": [150, 0, 0], "upper": [199, 30, 30], "color_space": "RGB", "threshold": 50.0},
    {"name": "red", "lower": [220, 50, 50], "upper": [255, 100, 100], "color_space": "RGB", "threshold": 50.0}
  ]
}
```

**All ranges must have the SAME color name.** During inspection:

- Bright red range matches: 30%
- Dark red range matches: 25%
- Pink red range matches: 10%
- **Total RED match: 65%** (summed)

**Example: Need to check RED and BLUE?**

- Create ROI #21 with red ranges only
- Create ROI #22 with blue ranges only

---

## 📝 Configuration Examples

### Object Format (Recommended)

```json
{
  "idx": 21,
  "type": 4,
  "coords": [4465, 2392, 4616, 2472],
  "focus": 245,
  "exposure": 800,
  "ai_threshold": null,
  "feature_method": null,
  "rotation": 0,
  "device_location": 1,
  "expected_text": null,
  "is_device_barcode": null,
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
    }
  ]
}
```

### Array Format (Legacy)

```json
[
  21,
  4,
  [4465, 2392, 4616, 2472],
  245,
  800,
  null,
  null,
  0,
  1,
  null,
  null,
  [
    {"name": "red", "lower": [200, 0, 0], "upper": [255, 50, 50], "color_space": "RGB", "threshold": 50.0},
    {"name": "red", "lower": [150, 0, 0], "upper": [199, 30, 30], "color_space": "RGB", "threshold": 50.0}
  ]
]
```

**Note:** All ranges in one ROI must have the SAME color name. For different colors, create separate ROIs.

---

## 🔄 Configuration Priority

The server checks for color ranges in this order:

1. **ROI embedded config** (`color_ranges` field in ROI) - **HIGHEST PRIORITY**
2. **Product-level config file** (`config/products/{product}/colors_config_{product}.json`) - **FALLBACK**

### Example Behavior

```python
# Scenario 1: ROI has embedded color_ranges
roi = {
    "idx": 21,
    "type": 4,
    "color_ranges": [...]  # ← Uses this (embedded config)
}

# Scenario 2: ROI without embedded color_ranges
roi = {
    "idx": 21,
    "type": 4,
    "color_ranges": null  # ← Falls back to colors_config_{product}.json
}

# Scenario 3: No embedded config, no product config
# Result: No color ranges available, ROI will fail or return Unknown color
```

---

## 📡 API Integration

### 1. Save ROI Configuration with Embedded Colors

```http
POST /api/products/{product_name}/config
Content-Type: application/json

{
  "rois": [
    {
      "idx": 21,
      "type": 4,
      "coords": [4465, 2392, 4616, 2472],
      "focus": 245,
      "exposure": 800,
      "ai_threshold": null,
      "feature_method": null,
      "rotation": 0,
      "device_location": 1,
      "expected_text": null,
      "is_device_barcode": null,
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
  ]
}
```

### 2. Inspection with Color ROI

```http
POST /api/session/{session_id}/inspect
Content-Type: application/json

{
  "image_path": "/path/to/image.jpg",
  "rois": [
    {
      "idx": 21,
      "type": 4,
      "coords": [4465, 2392, 4616, 2472],
      "focus": 245,
      "exposure": 800,
      "rotation": 0,
      "device_location": 1,
      "color_ranges": [
        {"name": "red", "lower": [200, 0, 0], "upper": [255, 50, 50], "color_space": "RGB", "threshold": 50.0},
        {"name": "red", "lower": [150, 0, 0], "upper": [199, 30, 30], "color_space": "RGB", "threshold": 50.0}
      ]
    },
    {
      "idx": 22,
      "type": 4,
      "coords": [4700, 2392, 4850, 2472],
      "focus": 245,
      "exposure": 800,
      "rotation": 0,
      "device_location": 1,
      "color_ranges": [
        {"name": "blue", "lower": [0, 0, 200], "upper": [50, 50, 255], "color_space": "RGB", "threshold": 50.0}
      ]
    }
  ]
}
```

**Note:** ROI #21 checks RED (2 ranges for brightness variations), ROI #22 checks BLUE (1 range).

```

### 3. Get ROI Schema

```http
GET /api/schema/roi
```

**Response** (abbreviated):

```json
{
  "version": "3.1",
  "format": "12-field",
  "updated": "2025-10-31",
  "fields": [
    {
      "index": 11,
      "name": "color_ranges",
      "type": "array[object] | None",
      "required": false,
      "description": "Color ranges for color validation (NEW in v3.1)",
      "constraints": "Only for Color ROIs (Type 4). Array of {name, lower, upper, color_space, threshold}",
      "format": {
        "name": "str - Color name (e.g., \"red\", \"blue\")",
        "lower": "array[int, int, int] - Lower bound RGB/HSV values",
        "upper": "array[int, int, int] - Upper bound RGB/HSV values",
        "color_space": "str - \"RGB\" or \"HSV\"",
        "threshold": "float - Match percentage threshold (0-100)"
      },
      "note": "Multiple ranges can have same name - matches are aggregated. Fallback to product-level config if not specified."
    }
  ],
  "roi_types": {
    "4": {
      "name": "Color",
      "description": "Color validation against defined color ranges",
      "relevant_fields": ["idx", "type", "coords", "focus", "exposure_time", "rotation", "device_location", "color_ranges"],
      "configuration": "Embedded color_ranges in ROI config (NEW in v3.1) or fallback to config/products/{product}/colors_config_{product}.json",
      "note": "Priority: ROI embedded config > product-level config file"
    }
  }
}
```

---

## ✅ Client Implementation Guide

### Step 1: Update ROI Validation

```python
# Add 'color' to validation list
VALID_ROI_TYPES = ['barcode', 'compare', 'ocr', 'color']
```

### Step 2: Create Color ROI with Embedded Config

```python
def create_color_roi(idx, coords, color_ranges):
    """Create a color ROI with embedded color configuration."""
    return {
        'idx': idx,
        'type': 4,
        'coords': coords,
        'focus': 245,
        'exposure': 800,
        'ai_threshold': None,
        'feature_method': None,
        'rotation': 0,
        'device_location': 1,
        'expected_text': None,
        'is_device_barcode': None,
        'color_ranges': color_ranges  # Embedded config
    }

# Example usage
roi = create_color_roi(
    idx=21,
    coords=[4465, 2392, 4616, 2472],
    color_ranges=[
        {
            'name': 'red',
            'lower': [200, 0, 0],
            'upper': [255, 50, 50],
            'color_space': 'RGB',
            'threshold': 50.0
        },
        {
            'name': 'blue',
            'lower': [0, 0, 200],
            'upper': [50, 50, 255],
            'color_space': 'RGB',
            'threshold': 50.0
        }
    ]
)
```

### Step 3: Send to Server

```python
import requests

# Save ROI configuration
response = requests.post(
    f'http://server:5000/api/products/{product_name}/config',
    json={'rois': [roi]}
)

# Or use directly in inspection
response = requests.post(
    f'http://server:5000/api/session/{session_id}/inspect',
    json={'image_path': '/path/to/image.jpg', 'rois': [roi]}
)
```

---

## 🧪 Testing

### Test Script

```python
import requests
import json

base_url = 'http://localhost:5000'
product_name = '20000803'

# Create color ROI with embedded config
color_roi = {
    'idx': 21,
    'type': 4,
    'coords': [4465, 2392, 4616, 2472],
    'focus': 245,
    'exposure': 800,
    'ai_threshold': None,
    'feature_method': None,
    'rotation': 0,
    'device_location': 1,
    'expected_text': None,
    'is_device_barcode': None,
    'color_ranges': [
        {
            'name': 'red',
            'lower': [200, 0, 0],
            'upper': [255, 50, 50],
            'color_space': 'RGB',
            'threshold': 50.0
        },
        {
            'name': 'red',
            'lower': [150, 0, 0],
            'upper': [199, 30, 30],
            'color_space': 'RGB',
            'threshold': 50.0
        }
    ]
}

# Create another color ROI for blue (separate ROI)
blue_roi = {
    'idx': 22,
    'type': 4,
    'coords': [4700, 2392, 4850, 2472],
    'focus': 245,
    'exposure': 800,
    'ai_threshold': None,
    'feature_method': None,
    'rotation': 0,
    'device_location': 1,
    'expected_text': None,
    'is_device_barcode': None,
    'color_ranges': [
        {
            'name': 'blue',
            'lower': [0, 0, 200],
            'upper': [50, 50, 255],
            'color_space': 'RGB',
            'threshold': 50.0
        }
    ]
}

# Test 1: Get schema
print('Test 1: Get ROI schema')
response = requests.get(f'{base_url}/api/schema/roi')
schema = response.json()
print(f'Version: {schema["version"]}')
print(f'Format: {schema["format"]}')
print(f'Color ranges field: {schema["fields"][11]}')

# Test 2: Create session with color ROI
print('\nTest 2: Create inspection session')
session_response = requests.post(
    f'{base_url}/api/session/create',
    json={'product_name': product_name}
)
session_id = session_response.json()['session_id']
print(f'Session ID: {session_id}')

# Test 3: Inspect with embedded color ranges (both red and blue ROIs)
print('\nTest 3: Inspect with color ROIs')
inspect_response = requests.post(
    f'{base_url}/api/session/{session_id}/inspect',
    json={
        'image_path': '/path/to/test/image.jpg',
        'rois': [color_roi, blue_roi]  # Two ROIs: red and blue
    }
)
result = inspect_response.json()
print(f'RED ROI Result: {json.dumps(result["roi_results"][0], indent=2)}')
print(f'BLUE ROI Result: {json.dumps(result["roi_results"][1], indent=2)}')
```

---

## 📖 Related Documentation

- `docs/COLOR_ROI_TYPE_4_COMPLETE_DOCUMENTATION.md` - Complete color ROI overview
- `docs/API_CLIENT_GUIDE.md` - Client integration guide
- `docs/ROI_DEFINITION_SPECIFICATION.md` - Official ROI structure spec
- `docs/SCHEMA_API_ENDPOINTS.md` - Schema endpoint documentation

---

## 🔄 Migration from v3.0 to v3.1

### Before (v3.0) - Separate Config File

```
config/products/20000803/
  ├── rois_config_20000803.json
  └── colors_config_20000803.json  ← Separate file
```

**rois_config_20000803.json:**

```json
[
  {
    "idx": 21,
    "type": 4,
    "coords": [4465, 2392, 4616, 2472],
    ...
  }
]
```

**colors_config_20000803.json:**

```json
{
  "color_ranges": [...]
}
```

### After (v3.1) - Embedded Config

```
config/products/20000803/
  └── rois_config_20000803.json  ← Everything in one file
```

**rois_config_20000803.json:**

```json
[
  {
    "idx": 21,
    "type": 4,
    "coords": [4465, 2392, 4616, 2472],
    ...
    "color_ranges": [...]  ← Embedded
  }
]
```

### Backward Compatibility

- ✅ v3.1 server supports both embedded and separate config files
- ✅ Priority: Embedded config > Product-level config file
- ✅ Existing v3.0 configs with separate files still work
- ✅ No breaking changes

---

**Last Updated**: October 31, 2025
