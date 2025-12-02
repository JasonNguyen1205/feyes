# Server-Client ROI Schema Integration

## Document Information

- **Created**: 2025-01-06
- **Purpose**: Document bidirectional conversion between server and client ROI schemas
- **Related Files**: `app.py` (lines 240-580)

## Overview

The Visual AOI client and server use **different field names** for ROI configurations. This document describes the field mapping, conversion functions, and validation rules for seamless integration.

---

## Schema Comparison

### Server Schema (Compact Format)

Used in server config files: `/home/jason_nguyen/visual-aoi-server/config/products/{product_name}/rois_config_{product_name}.json`

```json
{
  "idx": 1,
  "type": 1,
  "coords": [3459, 2959, 4058, 3318],
  "focus": 305,
  "exposure": 1200,
  "ai_threshold": null,
  "feature_method": "opencv",
  "rotation": 0,
  "device_location": 1,
  "sample_text": null,
  "is_device_barcode": null
}
```

**Field Types:**

- `idx` (int): ROI identifier
- `type` (int): ROI type (1=barcode, 2=compare, 3=ocr, 4=text)
- `coords` (array[int]): Bounding box [x1, y1, x2, y2]
- `focus` (int): Camera focus value (0-1000)
- `exposure` (int): Camera exposure in microseconds (0-10000)
- `ai_threshold` (float|null): AI similarity threshold (0.0-1.0) or null
- `feature_method` (string): AI model name ("opencv", "tesseract", etc.)
- `rotation` (int): Image rotation angle in degrees
- `device_location` (int): Device number (1-4)
- `sample_text` (string|null): Expected text for text-type ROIs or null
- `is_device_barcode` (boolean|null): Whether this is device identifier barcode or null

### Client Schema (Human-Readable Format)

Used internally in client application and ROI editor

```json
{
  "roi_id": 1,
  "roi_type_name": "barcode",
  "coordinates": [3459, 2959, 4058, 3318],
  "device_id": 1,
  "model": "opencv",
  "focus": 305,
  "exposure": 1200,
  "ai_threshold": 0.8,
  "rotation": 0,
  "is_device_barcode": true,
  "enabled": true,
  "notes": ""
}
```

**Field Types:**

- `roi_id` (int): ROI identifier
- `roi_type_name` (string): ROI type ("barcode", "compare", "ocr", "text")
- `coordinates` (array[int]): Bounding box [x1, y1, x2, y2]
- `device_id` (int): Device number (1-4)
- `model` (string): AI model name
- `focus` (int): Camera focus value (0-1000)
- `exposure` (int): Camera exposure in microseconds (0-10000)
- `ai_threshold` (float): AI similarity threshold (0.0-1.0, defaults to 0.8)
- `rotation` (int): Image rotation angle in degrees
- `is_device_barcode` (boolean): Whether this is device identifier barcode (defaults to True)
- `enabled` (boolean): Whether ROI is active (client-only field)
- `notes` (string): User notes about ROI (client-only field)

---

## Field Mapping

| Server Field | Client Field | Type Conversion | Default/Notes |
|--------------|--------------|-----------------|---------------|
| `idx` | `roi_id` | int → int | Direct mapping |
| `type` (1-4) | `roi_type_name` (string) | int → string | 1→barcode, 2→compare, 3→ocr, 4→text |
| `coords` | `coordinates` | array → array | Direct mapping |
| `device_location` | `device_id` | int → int | Direct mapping |
| `feature_method` | `model` | string → string | Direct mapping |
| `ai_threshold` (null) | `ai_threshold` | null → float | null converts to 0.8 default |
| `is_device_barcode` (null) | `is_device_barcode` | null → bool | null converts to True default |
| `sample_text` | `sample_text` | string/null → string/null | Preserved for text ROIs |
| `focus` | `focus` | int → int | Direct mapping |
| `exposure` | `exposure` | int → int | Direct mapping |
| `rotation` | `rotation` | int → int | Direct mapping |
| - | `enabled` | - | Client-only, defaults to True |
| - | `notes` | - | Client-only, defaults to "" |

---

## Conversion Functions

### 1. `roi_from_server_format(server_roi)` → Client Format

**Purpose**: Convert server's compact schema to client's human-readable schema

**Input** (Server Format):

```python
{
    "idx": 1,
    "type": 1,
    "coords": [3459, 2959, 4058, 3318],
    "device_location": 1,
    "feature_method": "opencv",
    "focus": 305,
    "exposure": 1200,
    "ai_threshold": None,
    "is_device_barcode": None
}
```

**Output** (Client Format):

```python
{
    "roi_id": 1,
    "roi_type_name": "barcode",
    "coordinates": [3459, 2959, 4058, 3318],
    "device_id": 1,
    "model": "opencv",
    "focus": 305,
    "exposure": 1200,
    "ai_threshold": 0.8,  # null → 0.8
    "is_device_barcode": True,  # null → True
    "enabled": True,
    "notes": ""
}
```

**Usage**:

```python
from app import roi_from_server_format

server_data = load_from_server()
client_roi = roi_from_server_format(server_data)
# Now use client_roi in ROI editor
```

### 2. `roi_to_server_format(client_roi)` → Server Format

**Purpose**: Convert client's human-readable schema back to server's compact schema

**Input** (Client Format):

```python
{
    "roi_id": 1,
    "roi_type_name": "barcode",
    "coordinates": [3459, 2959, 4058, 3318],
    "device_id": 1,
    "model": "opencv",
    "focus": 305,
    "exposure": 1200,
    "ai_threshold": 0.8,
    "is_device_barcode": True,
    "enabled": True,
    "notes": "Device barcode"
}
```

**Output** (Server Format):

```python
{
    "idx": 1,
    "type": 1,
    "coords": [3459, 2959, 4058, 3318],
    "device_location": 1,
    "feature_method": "opencv",
    "focus": 305,
    "exposure": 1200,
    "ai_threshold": 0.8,
    "rotation": 0,
    "sample_text": None,
    "is_device_barcode": True
}
```

**Usage**:

```python
from app import roi_to_server_format

# User edited ROI in client
edited_roi = get_roi_from_editor()

# Convert before sending to server
server_roi = roi_to_server_format(edited_roi)
send_to_server(server_roi)
```

### 3. `normalize_roi(roi_data)` → Client Format (Auto-Detect)

**Purpose**: Universal normalization that auto-detects format and converts to client format

**Auto-Detection Logic**:

```python
is_server_format = 'idx' in roi_data or 'coords' in roi_data or 'device_location' in roi_data
```

**Supported Input Formats**:

1. **Server dict format** (auto-detected) → Converts to client format
2. **Client dict format** → Normalizes field names and types
3. **Legacy array format** `[roi_id, device_id, [coords], ...]` → Converts to client format

**Usage**:

```python
from app import normalize_roi

# Works with any format!
server_roi = {"idx": 1, "type": 1, "coords": [100,200,300,400], ...}
client_roi_a = normalize_roi(server_roi)  # Auto-detects server format

client_roi = {"roi_id": 1, "roi_type_name": "barcode", ...}
client_roi_b = normalize_roi(client_roi)  # Normalizes client format

legacy_roi = [1, 1, [100,200,300,400], 305, 1200, 0.8, "opencv", 0]
client_roi_c = normalize_roi(legacy_roi)  # Converts legacy format
```

---

## Validation Rules

### `validate_roi(roi, format_type='client')` → (bool, [errors])

**Purpose**: Validate ROI data against schema requirements

**Format Types**:

- `format_type='server'` - Validate against server schema
- `format_type='client'` - Validate against client schema (default)

### Server Format Validation

**Required Fields**:

- `idx` (int)
- `type` (int, 1-4)
- `coords` (array[4])
- `focus` (int, 0-1000)
- `exposure` (int, 0-10000)
- `device_location` (int, 1-4)

**Optional Fields**:

- `ai_threshold` (float 0.0-1.0 or null)
- `feature_method` (string)
- `rotation` (int)
- `sample_text` (string or null)
- `is_device_barcode` (boolean or null)

**Example**:

```python
from app import validate_roi

server_roi = {"idx": 1, "type": 1, "coords": [100,200,300,400], "focus": 305, "exposure": 1200, "device_location": 1}
is_valid, errors = validate_roi(server_roi, format_type='server')

if not is_valid:
    print(f"Validation errors: {errors}")
```

### Client Format Validation

**Required Fields**:

- `roi_id` (int)
- `roi_type_name` (string: "barcode", "compare", "ocr", "text")
- `coordinates` (array[4])
- `device_id` (int, 1-4)

**Optional Fields**:

- `ai_threshold` (float 0.0-1.0)
- `model` (string)
- `focus` (int, 0-1000)
- `exposure` (int, 0-10000)
- `rotation` (int)
- `is_device_barcode` (boolean)
- `enabled` (boolean)
- `notes` (string)

**Example**:

```python
from app import validate_roi

client_roi = {"roi_id": 1, "roi_type_name": "barcode", "coordinates": [100,200,300,400], "device_id": 1}
is_valid, errors = validate_roi(client_roi, format_type='client')

if not is_valid:
    print(f"Validation errors: {errors}")
```

---

## Integration Workflow

### Loading Config from Server

```python
# Step 1: Fetch from server (server format)
server_rois = requests.get(f"{server_url}/api/products/{product}/config").json()

# Step 2: Normalize to client format
client_rois = [normalize_roi(roi) for roi in server_rois]

# Step 3: Validate client format
for roi in client_rois:
    is_valid, errors = validate_roi(roi, format_type='client')
    if not is_valid:
        logger.error(f"Invalid ROI {roi['roi_id']}: {errors}")

# Step 4: Use in ROI editor
display_rois_in_editor(client_rois)
```

### Saving Config to Server

```python
# Step 1: Get edited ROIs from editor (client format)
edited_rois = get_rois_from_editor()

# Step 2: Validate client format
for roi in edited_rois:
    is_valid, errors = validate_roi(roi, format_type='client')
    if not is_valid:
        raise ValueError(f"Invalid ROI {roi['roi_id']}: {errors}")

# Step 3: Convert to server format
server_rois = [roi_to_server_format(roi) for roi in edited_rois]

# Step 4: Validate server format
for roi in server_rois:
    is_valid, errors = validate_roi(roi, format_type='server')
    if not is_valid:
        logger.warning(f"Server format issue for ROI {roi['idx']}: {errors}")

# Step 5: Send to server
response = requests.post(
    f"{server_url}/api/products/{product}/config",
    json=server_rois
)
```

---

## Null Handling

Server allows null values for certain fields, but client uses concrete defaults:

| Server Field | Null Value | Client Default | Rationale |
|--------------|------------|----------------|-----------|
| `ai_threshold` | `null` | `0.8` | Common AI threshold |
| `is_device_barcode` | `null` | `True` | Conservative default (treat as device barcode) |
| `sample_text` | `null` | No field added | Only relevant for text ROIs |

**Conversion Behavior**:

```python
# Server → Client (null → default)
server_roi = {"idx": 1, "ai_threshold": None, "is_device_barcode": None}
client_roi = roi_from_server_format(server_roi)
# Result: {"roi_id": 1, "ai_threshold": 0.8, "is_device_barcode": True}

# Client → Server (preserve user values)
client_roi = {"roi_id": 1, "ai_threshold": 0.9, "is_device_barcode": False}
server_roi = roi_to_server_format(client_roi)
# Result: {"idx": 1, "ai_threshold": 0.9, "is_device_barcode": False}
```

---

## Testing

### Test Round-Trip Conversion

```bash
cd /home/jason_nguyen/visual-aoi-client
python3 -c "
from app import roi_from_server_format, roi_to_server_format
import json

# Original server data
server_roi = {
    'idx': 1, 'type': 1, 'coords': [100,200,300,400],
    'focus': 305, 'exposure': 1200, 'device_location': 1,
    'ai_threshold': None, 'feature_method': 'opencv',
    'rotation': 0, 'sample_text': None, 'is_device_barcode': None
}

# Convert to client
client_roi = roi_from_server_format(server_roi)
print('Client format:', json.dumps(client_roi, indent=2))

# Convert back to server
back_to_server = roi_to_server_format(client_roi)
print('Back to server:', json.dumps(back_to_server, indent=2))
"
```

### Test Validation

```bash
python3 -c "
from app import validate_roi

# Valid server format
server_roi = {'idx': 1, 'type': 1, 'coords': [100,200,300,400], 'focus': 305, 'exposure': 1200, 'device_location': 1}
valid, errors = validate_roi(server_roi, 'server')
print(f'Server validation: {valid}, errors: {errors}')

# Invalid client format (bad device_id)
client_roi = {'roi_id': 1, 'roi_type_name': 'barcode', 'coordinates': [100,200,300,400], 'device_id': 5}
valid, errors = validate_roi(client_roi, 'client')
print(f'Client validation: {valid}, errors: {errors}')
"
```

### Test Auto-Detection

```bash
python3 -c "
from app import normalize_roi

# Server format (has 'idx', 'coords')
server_roi = {'idx': 1, 'type': 1, 'coords': [100,200,300,400], 'device_location': 1, 'focus': 305, 'exposure': 1200}
result = normalize_roi(server_roi)
print(f'Detected server format, converted to: roi_id={result[\"roi_id\"]}, roi_type_name={result[\"roi_type_name\"]}')
"
```

---

## Troubleshooting

### Issue: "Missing required field: idx" when saving to server

**Cause**: Trying to send client format to server  
**Solution**: Use `roi_to_server_format()` before sending

```python
# ❌ Wrong
requests.post(url, json=client_rois)

# ✅ Correct
server_rois = [roi_to_server_format(roi) for roi in client_rois]
requests.post(url, json=server_rois)
```

### Issue: "roi_id must be int, got str"

**Cause**: Field types not properly converted  
**Solution**: Use `normalize_roi()` to fix types

```python
# ❌ Wrong
roi = {"roi_id": "1", "coordinates": "[100,200,300,400]"}

# ✅ Correct
roi = normalize_roi({"roi_id": "1", "coordinates": "[100,200,300,400]"})
# Result: {"roi_id": 1, "coordinates": [100, 200, 300, 400], ...}
```

### Issue: Auto-detection not working

**Cause**: ROI has both server and client fields mixed  
**Solution**: Clean data before normalization

```python
# ❌ Mixed format
mixed_roi = {"idx": 1, "roi_id": 1, "coords": [...], "coordinates": [...]}

# ✅ Use only one format
server_roi = {"idx": 1, "coords": [...], "device_location": 1, ...}
client_roi = normalize_roi(server_roi)
```

---

## Future Enhancements

1. **Server API Schema Endpoint**: Add `/api/schema/roi` endpoint for programmatic schema discovery
2. **Versioning**: Add schema version field for future compatibility
3. **Migration Scripts**: Create tools to bulk-convert existing configs
4. **Type Hints**: Add Python type hints for better IDE support

---

## Related Documentation

- `ROI_NORMALIZATION_REFERENCE.md` - Original normalization documentation
- `ROI_EDITOR_FOCUS_EXPOSURE_FIELDS.md` - Camera parameter fields
- `CAMERA_CAPTURE_RACE_CONDITION_FIX.md` - Camera threading fixes
- `.github/copilot-instructions.md` - Project architecture overview

---

**Last Updated**: 2025-01-06  
**Version**: 1.0  
**Author**: Visual AOI Development Team
