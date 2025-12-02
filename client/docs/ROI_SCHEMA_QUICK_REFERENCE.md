# ROI Schema Conversion - Quick Reference Card

## 🔄 Bidirectional Conversion Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SERVER-CLIENT ROI CONVERSION                       │
└─────────────────────────────────────────────────────────────────────┘

SERVER FORMAT                      CLIENT FORMAT
(Compact Schema)                   (Human-Readable Schema)
┌────────────────┐                 ┌──────────────────┐
│ idx: 1         │ ───────────────> │ roi_id: 1        │
│ type: 1        │ roi_from_server  │ roi_type_name:   │
│ coords: [...]  │                  │   "barcode"      │
│ device_        │                  │ coordinates:     │
│   location: 1  │                  │   [...]          │
│ feature_       │                  │ device_id: 1     │
│   method:      │                  │ model: "opencv"  │
│   "opencv"     │                  │ ai_threshold:    │
│ ai_threshold:  │                  │   0.8            │
│   null         │                  │ enabled: true    │
│ focus: 305     │                  │ notes: ""        │
│ exposure: 1200 │                  │ focus: 305       │
└────────────────┘                 │ exposure: 1200   │
        ↑                           └──────────────────┘
        │ roi_to_server_format              │
        └───────────────────────────────────┘
```

## 📋 Field Mapping Cheat Sheet

### ID & Type

```
Server              Client
──────────────────────────────────
idx                 roi_id
type (1-4)   ─────> roi_type_name
  1          ─────>   "barcode"
  2          ─────>   "compare"
  3          ─────>   "ocr"
  4          ─────>   "text"
```

### Coordinates & Device

```
Server              Client
──────────────────────────────────
coords              coordinates
device_location     device_id
```

### AI & Model

```
Server              Client
──────────────────────────────────
feature_method      model
ai_threshold        ai_threshold
  null       ─────>   0.8 (default)
```

### Camera Settings

```
Server              Client
──────────────────────────────────
focus               focus
exposure            exposure
rotation            rotation
```

### Special Fields

```
Server              Client
──────────────────────────────────
sample_text         sample_text
is_device_barcode   is_device_barcode
  null       ─────>   true (default)
-                    enabled (true)
-                    notes ("")
```

## 🔍 Format Detection

### Server Format Indicators

```python
has 'idx' field          ✓ Server format
has 'coords' field       ✓ Server format  
has 'device_location'    ✓ Server format
has 'type' as integer    ✓ Server format
```

### Client Format Indicators

```python
has 'roi_id' field       ✓ Client format
has 'coordinates' field  ✓ Client format
has 'device_id' field    ✓ Client format
has 'roi_type_name'      ✓ Client format
```

## 🚀 Quick Usage Examples

### 1. Load from Server

```python
# Server returns: [{"idx": 1, "type": 1, "coords": [...], ...}]
server_rois = requests.get(f"{server_url}/api/products/{product}/config").json()

# Auto-convert to client format
client_rois = normalize_roi_list(server_rois)

# Use in editor: [{"roi_id": 1, "roi_type_name": "barcode", ...}]
```

### 2. Save to Server

```python
# Editor returns: [{"roi_id": 1, "roi_type_name": "barcode", ...}]
edited_rois = get_rois_from_editor()

# Convert to server format
server_rois = [roi_to_server_format(roi) for roi in edited_rois]

# Send to server: [{"idx": 1, "type": 1, "coords": [...], ...}]
requests.post(f"{server_url}/api/products/{product}/config", json=server_rois)
```

### 3. Validate ROI

```python
# Validate server format
valid, errors = validate_roi(server_roi, format_type='server')

# Validate client format (default)
valid, errors = validate_roi(client_roi)
```

## 📊 Validation Requirements

### Server Format

```
REQUIRED:
  ✓ idx (int)
  ✓ type (int, 1-4)
  ✓ coords (array[4])
  ✓ focus (int, 0-1000)
  ✓ exposure (int, 0-10000)
  ✓ device_location (int, 1-4)

OPTIONAL:
  • ai_threshold (float 0.0-1.0 or null)
  • feature_method (string)
  • rotation (int)
  • sample_text (string or null)
  • is_device_barcode (boolean or null)
```

### Client Format

```
REQUIRED:
  ✓ roi_id (int)
  ✓ roi_type_name (string: barcode/compare/ocr/text)
  ✓ coordinates (array[4])
  ✓ device_id (int, 1-4)

OPTIONAL:
  • ai_threshold (float 0.0-1.0)
  • model (string)
  • focus (int, 0-1000)
  • exposure (int, 0-10000)
  • rotation (int)
  • is_device_barcode (boolean)
  • enabled (boolean)
  • notes (string)
```

## ⚠️ Common Pitfalls

### ❌ Wrong: Send client format to server

```python
requests.post(url, json=client_rois)  # Server won't understand!
```

### ✅ Correct: Convert before sending

```python
server_rois = [roi_to_server_format(roi) for roi in client_rois]
requests.post(url, json=server_rois)
```

### ❌ Wrong: Manual format detection

```python
if 'idx' in roi:  # Fragile!
    # handle server format
```

### ✅ Correct: Use auto-detection

```python
normalized = normalize_roi(roi)  # Handles all formats automatically
```

### ❌ Wrong: Ignore validation

```python
roi_to_server_format(roi)  # What if roi is invalid?
```

### ✅ Correct: Validate first

```python
is_valid, errors = validate_roi(roi)
if is_valid:
    server_roi = roi_to_server_format(roi)
```

## 🎯 Function Reference

| Function | Input | Output | Use Case |
|----------|-------|--------|----------|
| `roi_from_server_format()` | Server dict | Client dict | Load from server |
| `roi_to_server_format()` | Client dict | Server dict | Save to server |
| `normalize_roi()` | Any format | Client dict | Universal conversion |
| `validate_roi()` | ROI dict + format | (bool, errors) | Data validation |
| `normalize_roi_list()` | List of any | List of client | Batch conversion |

## 📖 Documentation Links

**Full Details**: `docs/SERVER_CLIENT_ROI_SCHEMA_INTEGRATION.md`  
**Implementation Summary**: `docs/ROI_SERVER_SCHEMA_INTEGRATION_SUMMARY.md`  
**Original Normalization**: `docs/ROI_NORMALIZATION_REFERENCE.md`

## 🧪 Test Commands

### Test Conversion

```bash
python3 -c "
from app import roi_from_server_format, roi_to_server_format
server = {'idx': 1, 'type': 1, 'coords': [100,200,300,400], 'device_location': 1, 'focus': 305, 'exposure': 1200}
client = roi_from_server_format(server)
print('Client:', client)
back = roi_to_server_format(client)
print('Back to server:', back)
"
```

### Test Validation

```bash
python3 -c "
from app import validate_roi
roi = {'idx': 1, 'type': 1, 'coords': [100,200,300,400], 'focus': 305, 'exposure': 1200, 'device_location': 1}
valid, errors = validate_roi(roi, 'server')
print(f'Valid: {valid}, Errors: {errors}')
"
```

### Test Auto-Detection

```bash
python3 -c "
from app import normalize_roi
server_roi = {'idx': 1, 'type': 1, 'coords': [100,200,300,400], 'device_location': 1, 'focus': 305, 'exposure': 1200}
result = normalize_roi(server_roi)
print(f'Detected and converted: roi_id={result[\"roi_id\"]}, roi_type_name={result[\"roi_type_name\"]}')
"
```

---

**Version**: 1.0  
**Date**: January 6, 2025  
**Status**: Production Ready ✅
