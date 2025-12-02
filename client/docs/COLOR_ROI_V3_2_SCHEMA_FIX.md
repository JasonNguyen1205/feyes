# Color ROI v3.2 Schema Alignment Fix

**Date**: October 29, 2025  
**Server Version**: v3.2 (updated November 1, 2025)  
**Issue**: Client was sending color parameters as individual fields instead of wrapped in `color_config` dict

---

## Server v3.2 Schema Structure

### ROI Type 4: Color Checking

**Field 11: `color_config`** (dict | None)
- **Type**: Dictionary containing color validation parameters
- **Added in**: v3.1
- **Updated in**: v3.2 (added simple format)

### Two Supported Formats:

#### 1. Simple Format (v3.2 - Recommended)
```json
{
  "color_config": {
    "expected_color": [255, 0, 0],      // RGB array [r, g, b]
    "color_tolerance": 10,               // int - deviation allowed (±)
    "min_pixel_percentage": 5.0          // float - minimum match % for pass
  }
}
```

**Logic**: Creates color range `[expected_color ± color_tolerance]`. Pass if `>= min_pixel_percentage` of pixels match.

**Example**: 
- `expected_color: [255, 0, 0]` (red)
- `color_tolerance: 10`
- Creates range: RGB [245-255, 0-10, 0-10]

#### 2. Legacy Format (v3.1 - For advanced cases)
```json
{
  "color_config": {
    "color_ranges": [
      {
        "name": "red",
        "color_space": "RGB",
        "lower": [200, 0, 0],
        "upper": [255, 50, 50],
        "threshold": 5.0
      }
    ]
  }
}
```

**Use case**: Multiple ranges, custom bounds, HSV color space

---

## Client Changes Made

### 1. Flask App: `roi_from_server_format()` (app.py lines 390-413)

**Before**: Extracted individual fields directly from server_roi
```python
if 'expected_color' in server_roi:
    client_roi['expected_color'] = server_roi['expected_color']
```

**After**: Extracts from `color_config` dict
```python
color_config = server_roi.get('color_config', {})

if color_config:
    # Simple format (v3.2)
    if 'expected_color' in color_config:
        client_roi['expected_color'] = color_config['expected_color']
    if 'color_tolerance' in color_config:
        client_roi['color_tolerance'] = int(color_config['color_tolerance'])
    if 'min_pixel_percentage' in color_config:
        client_roi['min_pixel_percentage'] = float(color_config['min_pixel_percentage'])
    
    # Legacy format (v3.1) - preserve color_ranges if present
    if 'color_ranges' in color_config:
        client_roi['color_ranges'] = color_config['color_ranges']
```

### 2. Flask App: `roi_to_server_format()` (app.py lines 436-465)

**Before**: Added individual fields to server_roi
```python
if 'expected_color' in client_roi:
    server_roi['expected_color'] = client_roi['expected_color']
```

**After**: Wraps in `color_config` dict
```python
if roi_type_name == 'color':
    color_config = {}
    
    # Simple format (v3.2) - preferred
    if 'expected_color' in client_roi:
        color_config['expected_color'] = client_roi['expected_color']
    if 'color_tolerance' in client_roi:
        color_config['color_tolerance'] = int(client_roi['color_tolerance'])
    if 'min_pixel_percentage' in client_roi:
        color_config['min_pixel_percentage'] = float(client_roi['min_pixel_percentage'])
    
    # Legacy format (v3.1) - if color_ranges provided
    if 'color_ranges' in client_roi:
        color_config['color_ranges'] = client_roi['color_ranges']
    
    # Only add color_config if not empty
    if color_config:
        server_roi['color_config'] = color_config
```

---

## Client-Side JavaScript

**No changes needed** - `roi_editor.js` already handles individual fields correctly:
- Extracts `expected_color`, `color_tolerance`, `min_pixel_percentage` from ROI object
- Converts RGB arrays ↔ hex color for UI display
- Stores as individual properties in client ROI object

Flask app handles the wrapping/unwrapping of `color_config` during server communication.

---

## Complete ROI Flow

### 1. User Creates Color ROI in Editor
```javascript
// roi_editor.js stores:
{
  roi_type_name: "color",
  expected_color: [255, 0, 0],       // from color picker
  color_tolerance: 10,                // from slider
  min_pixel_percentage: 5.0           // from input
}
```

### 2. Client → Flask → Server (Save Configuration)
```python
# Flask roi_to_server_format() wraps into color_config:
{
  "idx": 1,
  "type": 4,
  "coords": [100, 100, 200, 200],
  "focus": 305,
  "exposure": 3000,
  "color_config": {
    "expected_color": [255, 0, 0],
    "color_tolerance": 10,
    "min_pixel_percentage": 5.0
  }
}
```

### 3. Server → Flask → Client (Load Configuration)
```python
# Flask roi_from_server_format() unwraps from color_config:
{
  "roi_id": 1,
  "roi_type_name": "color",
  "coordinates": [100, 100, 200, 200],
  "expected_color": [255, 0, 0],      // extracted from color_config
  "color_tolerance": 10,               // extracted from color_config
  "min_pixel_percentage": 5.0          // extracted from color_config
}
```

---

## Testing Checklist

- [x] Server v3.2 schema verified with Type 4 and field 11 (color_config)
- [x] Flask conversion functions updated to wrap/unwrap color_config
- [x] Validation allows 'color' in roi_type_name
- [ ] **TODO**: Test creating new color ROI in editor
- [ ] **TODO**: Test saving color ROI to server
- [ ] **TODO**: Test loading existing color ROI from server
- [ ] **TODO**: Test inspection with color ROI
- [ ] **TODO**: Verify color results display correctly

---

## API Verification Commands

```bash
# Check server schema version
curl -s http://10.100.27.156:5000/api/schema/roi | python3 -c "import json, sys; data=json.load(sys.stdin); print('Version:', data['version'])"

# Verify Type 4 exists
curl -s http://10.100.27.156:5000/api/schema/roi | python3 -c "import json, sys; data=json.load(sys.stdin); print('ROI Types:', list(data['roi_types'].keys()))"

# Check field 11 (color_config)
curl -s http://10.100.27.156:5000/api/schema/roi | python3 -c "import json, sys; data=json.load(sys.stdin); print('Field 11:', data['fields'][11]['name'])"

# View color type details
curl -s http://10.100.27.156:5000/api/schema/roi | python3 -c "import json, sys; data=json.load(sys.stdin); import pprint; pprint.pprint(data['roi_types']['4'])"
```

---

## References

- **Server API**: http://10.100.27.156:5000/apidocs/
- **ROI Schema**: http://10.100.27.156:5000/api/schema/roi
- **Schema Version**: v3.2 (updated November 1, 2025)
- **Related Docs**: 
  - `docs/CLIENT_SERVER_SCHEMA_FIX.md` - General schema alignment
  - `docs/SCHEMA_V2_QUICK_REFERENCE.md` - Schema versioning overview
