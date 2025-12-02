# ROI (Region of Interest) Definition Specification

**Version:** 3.0 (11-Field Format)  
**Last Updated:** October 3, 2025  
**Status:** OFFICIAL SPECIFICATION - ALL CODE MUST COMPLY

---

## 🎯 Purpose

This document is the **single source of truth** for ROI structure definition in the Visual AOI Server. All functions that parse, create, or manipulate ROIs **MUST** follow this specification exactly.

**⚠️ CRITICAL:** When the ROI structure changes, this document MUST be updated FIRST before any code changes.

---

## 📐 Current ROI Structure (11-Field Format)

### Canonical Format

```python
roi = (
    idx,              # Field 0: ROI index (int, 1-based)
    typ,              # Field 1: ROI type (int: 1=Barcode, 2=Compare, 3=OCR, 4=Color)
    coords,           # Field 2: Coordinates tuple (x1, y1, x2, y2) as tuple of 4 ints
    focus,            # Field 3: Focus value (int, e.g., 305)
    exposure_time,    # Field 4: Exposure time in microseconds (int, e.g., 3000)
    ai_threshold,     # Field 5: AI similarity threshold (float or None, e.g., 0.85)
    feature_method,   # Field 6: Feature extraction method (str: "mobilenet", "sift", "orb", "opencv", "barcode", "ocr", None for color)
    rotation,         # Field 7: Rotation angle in degrees (int, 0/90/180/270)
    device_location,  # Field 8: Device identifier (int, 1-based: 1, 2, 3, or 4)
    expected_text,      # Field 9: Expected text for OCR comparison (str or None)
    is_device_barcode # Field 10: Flag indicating if this barcode is the device's main barcode (bool or None)
)
```

### Example ROIs

```python
# Barcode ROI (Type 1) - Device Main Barcode
barcode_roi = (
    1,                    # idx
    1,                    # type: barcode
    (50, 50, 150, 100),   # coords
    305,                  # focus
    3000,                 # exposure
    None,                 # ai_threshold (not used for barcode)
    "barcode",            # feature_method
    0,                    # rotation
    1,                    # device_location
    None,                 # expected_text (not used for barcode)
    True                  # is_device_barcode (marks this as device's main barcode)
)

# Compare ROI (Type 2)
compare_roi = (
    2,                    # idx
    2,                    # type: compare
    (200, 50, 300, 150),  # coords
    305,                  # focus
    3000,                 # exposure
    0.85,                 # ai_threshold
    "mobilenet",          # feature_method
    0,                    # rotation
    1,                    # device_location
    None,                 # expected_text (not used for compare)
    None                  # is_device_barcode (not applicable for compare ROIs)
)

# OCR ROI (Type 3)
ocr_roi = (
    3,                    # idx
    3,                    # type: ocr
    (350, 50, 450, 100),  # coords
    305,                  # focus
    3000,                 # exposure
    None,                 # ai_threshold (not used for OCR)
    "ocr",                # feature_method
    0,                    # rotation
    1,                    # device_location
    "EXPECTED_TEXT",      # expected_text for validation
    None                  # is_device_barcode (not applicable for OCR ROIs)
)

# Color ROI (Type 4) - NEW in October 2025
color_roi = (
    4,                    # idx
    4,                    # type: color
    (500, 50, 600, 150),  # coords
    305,                  # focus
    3000,                 # exposure
    None,                 # ai_threshold (not used for color)
    None,                 # feature_method (not used for color)
    0,                    # rotation
    1,                    # device_location
    None,                 # expected_text (not used for color)
    None                  # is_device_barcode (not applicable for color ROIs)
)
```

---

## 📋 Field Specifications

### Field 0: idx (ROI Index)

- **Type:** `int`
- **Range:** 1 to N (1-based indexing)
- **Required:** YES
- **Constraints:**
  - Must be unique within a product configuration
  - Must be positive integer
  - Should be sequential but gaps are allowed
- **Usage:** Identifies ROI uniquely, used for golden image storage

### Field 1: typ (ROI Type)

- **Type:** `int`
- **Values:**
  - `1` = Barcode ROI
  - `2` = Compare/AI ROI
  - `3` = OCR ROI
  - `4` = Color ROI (NEW - October 2025)
- **Required:** YES
- **Constraints:**
  - Must be exactly 1, 2, 3, or 4
  - Determines processing method and required fields
- **Usage:** Dispatches to appropriate processing function

### Field 2: coords (Coordinates)

- **Type:** `tuple` of 4 `int` values
- **Format:** `(x1, y1, x2, y2)`
- **Required:** YES
- **Constraints:**
  - x1 < x2 (left < right)
  - y1 < y2 (top < bottom)
  - All values must be non-negative
  - Coordinates must be within image bounds
- **Usage:** Defines rectangular region to process
- **Note:** Stored as tuple, not list

### Field 3: focus (Focus Value)

- **Type:** `int`
- **Range:** Typically 100-500 (camera-dependent)
- **Required:** YES
- **Default:** 305 (for legacy compatibility)
- **Constraints:**
  - Must be positive integer
  - Value depends on camera hardware
- **Usage:** Groups ROIs for camera capture optimization

### Field 4: exposure_time (Exposure Time)

- **Type:** `int`
- **Unit:** Microseconds
- **Range:** Typically 100-10000
- **Required:** YES
- **Default:** 3000 (for legacy compatibility)
- **Constraints:**
  - Must be positive integer
  - Value depends on lighting conditions
- **Usage:** Groups ROIs for camera capture optimization

### Field 5: ai_threshold (AI Similarity Threshold)

- **Type:** `float` or `None`
- **Range:** 0.0 to 1.0 (when not None)
- **Required:** Only for Compare ROIs (Type 2)
- **Default:** 0.9 for Compare, None for others
- **Constraints:**
  - Must be None for Barcode (Type 1) and OCR (Type 3)
  - Must be float between 0.0 and 1.0 for Compare (Type 2)
- **Usage:** Determines pass threshold for AI similarity comparison

### Field 6: feature_method (Feature Extraction Method)

- **Type:** `str`
- **Values:**
  - `"mobilenet"` - PyTorch MobileNetV2 (1280-dim features)
  - `"sift"` - SIFT descriptors (384-dim features)
  - `"orb"` - ORB descriptors (variable length)
  - `"opencv"` - Generic OpenCV fallback
  - `"barcode"` - For Barcode ROIs
  - `"ocr"` - For OCR ROIs
- **Required:** YES
- **Default:**
  - Type 1 (Barcode): `"barcode"`
  - Type 2 (Compare): `"mobilenet"`
  - Type 3 (OCR): `"ocr"`
- **Constraints:**
  - Must be lowercase string
  - Should match ROI type requirements
- **Usage:** Selects algorithm for feature extraction

### Field 7: rotation (Rotation Angle)

- **Type:** `int`
- **Values:** 0, 90, 180, 270 (degrees clockwise)
- **Required:** YES
- **Default:** 0 (no rotation)
- **Constraints:**
  - Must be one of: 0, 90, 180, 270
  - Primarily used for OCR ROIs
- **Usage:** Rotates ROI image before processing (mainly OCR)

### Field 8: device_location (Device Identifier)

- **Type:** `int`
- **Range:** 1 to 4
- **Required:** YES
- **Default:** 1 (for legacy compatibility)
- **Constraints:**
  - Must be integer 1, 2, 3, or 4
  - All ROIs assigned to same device_location are processed together
- **Usage:** Groups ROIs by physical device in multi-device inspections

### Field 9: expected_text (Expected Text for OCR)

- **Type:** `str` or `None`
- **Required:** Only for OCR ROIs with validation
- **Default:** None
- **Constraints:**
  - Should be None for Barcode (Type 1) and Compare (Type 2)
  - Can be None or string for OCR (Type 3)
  - If provided, enables substring matching validation
- **Usage:** Validates OCR result against expected text

### Field 10: is_device_barcode (Device Main Barcode Flag) ⚠️ **NEW in v3.0**

- **Type:** `bool` or `None`
- **Required:** Only for Barcode ROIs (Type 1) that should be used as device identifier
- **Default:** None
- **Constraints:**
  - Should be True, False, or None
  - Only meaningful for Barcode ROIs (Type 1)
  - Should be None for Compare (Type 2) and OCR (Type 3)
  - Only ONE barcode ROI per device_location should have is_device_barcode=True
- **Usage:**
  - Marks this barcode as the device's primary identifier
  - When True, this barcode takes **highest priority** in device_summaries barcode field
  - Overrides the standard barcode priority logic (ROI → Manual → Legacy)
  - Used for multi-barcode scenarios where one specific barcode identifies the device

**Priority Logic with is_device_barcode:**

```
Priority 0: ROI Barcode with is_device_barcode=True (HIGHEST)
  ↓ (if not found)
Priority 1: Any ROI Barcode with valid value
  ↓ (if invalid/missing)
Priority 2: Manual Multi-Device Barcode (device_barcodes[device_id])
  ↓ (if not provided)
Priority 3: Legacy Single Barcode (device_barcode)
  ↓ (if not provided)
Priority 4: Default ("N/A")
```

---

## 🔄 Backward Compatibility & Migration

### Legacy Format Support

The system supports automatic migration from legacy formats:

#### 10-Field Format (v2.0 - Current Legacy)

```python
(idx, typ, coords, focus, exposure, ai_threshold, feature_method, rotation, device_location, expected_text)
# Missing: is_device_barcode
# Migration: Add is_device_barcode=None
```

#### 9-Field Format (Legacy v1.0)

```python
(idx, typ, coords, focus, exposure, ai_threshold, feature_method, rotation, device_location)
# Missing: expected_text, is_device_barcode
# Migration: Add expected_text=None, is_device_barcode=None
```

#### 8-Field Format (Pre-multi-device)

```python
(idx, typ, coords, focus, exposure, ai_threshold, feature_method, rotation)
# Missing: device_location, expected_text
# Migration: Add device_location=1, expected_text=None
```

#### 7-Field Format (Pre-rotation)

```python
(idx, typ, coords, focus, exposure, ai_threshold, feature_method)
# Missing: rotation, device_location, expected_text
# Migration: Add rotation=0, device_location=1, expected_text=None
```

#### 6-Field Format

```python
(idx, typ, coords, focus, exposure, ai_threshold)
# Missing: feature_method, rotation, device_location, expected_text
# Migration: Infer feature_method from type, add defaults
```

#### 5-Field Format

```python
(idx, typ, coords, focus, ai_threshold)
# Missing: exposure, feature_method, rotation, device_location, expected_text
# Migration: Add exposure=3000, infer feature_method, add defaults
```

#### 4-Field Format

```python
(idx, typ, coords, focus)
# Missing: ai_threshold, exposure, feature_method, rotation, device_location, expected_text
# Migration: Add ai_threshold based on type, exposure=3000, infer feature_method, add defaults
```

#### 3-Field Format

```python
(idx, typ, coords)
# Missing: focus, ai_threshold, exposure, feature_method, rotation, device_location, expected_text
# Migration: Add focus=305, ai_threshold based on type, exposure=3000, infer feature_method, add defaults
```

### Migration Rules ⚠️ **CRITICAL**

```python
def normalize_roi(r):
    """Normalize any legacy ROI format to current 11-field format."""
    
    # Target format: (idx, typ, coords, focus, exposure, ai_threshold, 
    #                 feature_method, rotation, device_location, expected_text, is_device_barcode)
    
    # Type-specific defaults
    if typ == 1:  # Barcode
        default_ai_threshold = None
        default_feature_method = "barcode"
        default_expected_text = None
    elif typ == 2:  # Compare
        default_ai_threshold = 0.9
        default_feature_method = "mobilenet"
        default_expected_text = None
    elif typ == 3:  # OCR
        default_ai_threshold = None
        default_feature_method = "ocr"
        default_expected_text = None
    
    # Universal defaults
    default_focus = 305
    default_exposure = 3000
    default_rotation = 0
    default_device_location = 1
    
    # Apply defaults and return normalized tuple
```

**⚠️ IMPORTANT:** All ROI normalization MUST happen in `src/roi.py::normalize_roi()` function.

---

## 📝 JSON Configuration Format

### File Format

ROIs are stored as JSON arrays in product configuration files:

**File Path:** `config/products/{product_name}/rois_config_{product_name}.json`

### JSON Structure (Array Format)

```json
[
  [
    1,
    2,
    [100, 100, 200, 200],
    305,
    3000,
    0.85,
    "mobilenet",
    0,
    1,
    null,
    null
  ],
  [
    2,
    1,
    [300, 100, 400, 200],
    305,
    3000,
    null,
    "barcode",
    0,
    1,
    null,
    true
    null
  ],
  [
    3,
    3,
    [500, 100, 600, 200],
    305,
    3000,
    null,
    "ocr",
    0,
    1,
    "EXPECTED"
  ]
]
```

### JSON Structure (Object Format)

```json
{
  "description": "Product configuration description",
  "rois": [
    {
      "index": 1,
      "type": 2,
      "coordinates": [100, 100, 200, 200],
      "focus": 305,
      "exposure_time": 3000,
      "ai_threshold": 0.85,
      "feature_method": "mobilenet",
      "rotation": 0,
      "device_location": 1,
      "expected_text": null
    }
  ]
}
```

**Note:** Both formats are supported. Array format is more compact, object format is more readable.

---

## 🔧 Implementation Requirements

### All Functions Must Comply

Every function that handles ROIs MUST follow these rules:

#### 1. ROI Creation ⚠️ **MANDATORY**

```python
def create_roi(idx, typ, coords, focus=305, exposure=3000, 
               ai_threshold=None, feature_method="mobilenet",
               rotation=0, device_location=1, expected_text=None):
    """
    Create a normalized ROI tuple.
    
    Returns: 10-field tuple in canonical format
    """
    # Set type-specific defaults
    if typ == 1:  # Barcode
        ai_threshold = None
        feature_method = "barcode"
        expected_text = None
    elif typ == 2:  # Compare
        ai_threshold = ai_threshold if ai_threshold is not None else 0.9
        feature_method = feature_method or "mobilenet"
        expected_text = None
    elif typ == 3:  # OCR
        ai_threshold = None
        feature_method = "ocr"
        # expected_text can be provided or None
    
    # Ensure coords is tuple
    if isinstance(coords, list):
        coords = tuple(coords)
    
    return (
        int(idx),
        int(typ),
        tuple(coords),
        int(focus),
        int(exposure),
        float(ai_threshold) if ai_threshold is not None else None,
        str(feature_method),
        int(rotation),
        int(device_location),
        str(expected_text) if expected_text is not None else None
    )
```

#### 2. ROI Parsing ⚠️ **MANDATORY**

```python
def parse_roi(roi):
    """
    Parse ROI tuple and extract fields.
    
    Input: ROI tuple (any legacy format or current 10-field)
    Returns: Normalized 10-field tuple
    """
    # ALWAYS normalize first
    from src.roi import normalize_roi
    normalized = normalize_roi(roi)
    
    if normalized is None:
        raise ValueError(f"Invalid ROI format: {roi}")
    
    # Extract fields by index
    idx = normalized[0]
    typ = normalized[1]
    coords = normalized[2]
    focus = normalized[3]
    exposure = normalized[4]
    ai_threshold = normalized[5]
    feature_method = normalized[6]
    rotation = normalized[7]
    device_location = normalized[8]
    expected_text = normalized[9]
    
    return normalized
```

#### 3. ROI Field Access ⚠️ **MANDATORY**

```python
# ✅ CORRECT: Use normalize_roi() first
from src.roi import normalize_roi
roi = normalize_roi(raw_roi)
if roi:
    idx = roi[0]
    typ = roi[1]
    coords = roi[2]
    # ... etc

# ✅ CORRECT: Handle legacy formats
def get_device_location(roi):
    normalized = normalize_roi(roi)
    return normalized[8] if normalized else 1

# ❌ WRONG: Direct access without normalization
idx = roi[0]
device_location = roi[8]  # May fail for legacy formats!

# ❌ WRONG: Assuming fixed length
if len(roi) == 10:
    # This excludes legacy formats!
```

#### 4. ROI Type-Specific Processing ⚠️ **MANDATORY**

```python
def process_roi(roi, image, product_name):
    """Process ROI based on type."""
    # Always normalize first
    from src.roi import normalize_roi
    roi = normalize_roi(roi)
    
    if not roi:
        return None
    
    idx, typ, coords, focus, exposure, ai_threshold, feature_method, rotation, device_location, expected_text = roi
    x1, y1, x2, y2 = coords
    
    if typ == 1:  # Barcode
        return process_barcode_roi(image, x1, y1, x2, y2, idx)
    
    elif typ == 2:  # Compare
        return process_compare_roi(image, x1, y1, x2, y2, idx, 
                                   ai_threshold, feature_method, product_name)
    
    elif typ == 3:  # OCR
        return process_ocr_roi(image, x1, y1, x2, y2, idx, 
                              rotation, expected_text)
    
    else:
        raise ValueError(f"Unknown ROI type: {typ}")
```

---

## ✅ Validation Rules

### ROI Validation Checklist

All ROI data MUST pass these validations:

```python
def validate_roi(roi):
    """Validate ROI structure and values."""
    
    # 1. Check tuple/list
    if not isinstance(roi, (tuple, list)):
        raise ValueError("ROI must be tuple or list")
    
    # 2. Check minimum length
    if len(roi) < 3:
        raise ValueError("ROI must have at least 3 fields")
    
    # 3. Normalize to 10-field format
    normalized = normalize_roi(roi)
    if normalized is None:
        raise ValueError("ROI normalization failed")
    
    idx, typ, coords, focus, exposure, ai_threshold, feature_method, rotation, device_location, expected_text = normalized
    
    # 4. Validate idx
    if not isinstance(idx, int) or idx < 1:
        raise ValueError(f"Invalid idx: {idx} (must be positive int)")
    
    # 5. Validate type
    if typ not in [1, 2, 3]:
        raise ValueError(f"Invalid type: {typ} (must be 1, 2, or 3)")
    
    # 6. Validate coordinates
    if not isinstance(coords, tuple) or len(coords) != 4:
        raise ValueError(f"Invalid coords: {coords} (must be 4-element tuple)")
    
    x1, y1, x2, y2 = coords
    if not all(isinstance(c, int) for c in coords):
        raise ValueError("Coordinates must be integers")
    
    if x1 >= x2 or y1 >= y2:
        raise ValueError(f"Invalid coords: x1 < x2 and y1 < y2 required")
    
    if any(c < 0 for c in coords):
        raise ValueError("Coordinates must be non-negative")
    
    # 7. Validate focus
    if not isinstance(focus, int) or focus < 0:
        raise ValueError(f"Invalid focus: {focus}")
    
    # 8. Validate exposure
    if not isinstance(exposure, int) or exposure < 0:
        raise ValueError(f"Invalid exposure: {exposure}")
    
    # 9. Validate ai_threshold
    if ai_threshold is not None:
        if typ != 2:
            raise ValueError(f"ai_threshold must be None for type {typ}")
        if not isinstance(ai_threshold, float) or not (0.0 <= ai_threshold <= 1.0):
            raise ValueError(f"Invalid ai_threshold: {ai_threshold}")
    elif typ == 2:
        raise ValueError("ai_threshold required for Compare ROI (type 2)")
    
    # 10. Validate feature_method
    valid_methods = ["mobilenet", "sift", "orb", "opencv", "barcode", "ocr"]
    if feature_method not in valid_methods:
        raise ValueError(f"Invalid feature_method: {feature_method}")
    
    # 11. Validate rotation
    if rotation not in [0, 90, 180, 270]:
        raise ValueError(f"Invalid rotation: {rotation} (must be 0, 90, 180, or 270)")
    
    # 12. Validate device_location
    if not isinstance(device_location, int) or not (1 <= device_location <= 4):
        raise ValueError(f"Invalid device_location: {device_location} (must be 1-4)")
    
    # 13. Validate expected_text
    if expected_text is not None and not isinstance(expected_text, str):
        raise ValueError(f"Invalid expected_text: {expected_text} (must be str or None)")
    
    return True
```

---

## 🚨 Common Mistakes to Avoid

### ❌ DON'T: Access Fields Without Normalization

```python
# WRONG - May fail for legacy formats
def bad_example(roi):
    device_location = roi[8]  # Crashes if roi has < 9 fields!
    return device_location
```

### ✅ DO: Always Normalize First

```python
# CORRECT
def good_example(roi):
    from src.roi import normalize_roi
    normalized = normalize_roi(roi)
    if normalized:
        device_location = normalized[8]
        return device_location
    return 1  # default
```

### ❌ DON'T: Assume Fixed Format

```python
# WRONG - Assumes 10-field format
if len(roi) != 10:
    raise ValueError("Invalid ROI")
```

### ✅ DO: Support All Legacy Formats

```python
# CORRECT - Normalize handles all formats
normalized = normalize_roi(roi)
if not normalized:
    raise ValueError("Invalid ROI")
```

### ❌ DON'T: Modify ROI Tuples Directly

```python
# WRONG - Tuples are immutable
roi[8] = 2  # Error!
```

### ✅ DO: Create New Normalized Tuple

```python
# CORRECT
roi = normalize_roi(roi)
roi_list = list(roi)
roi_list[8] = 2
new_roi = tuple(roi_list)
```

### ❌ DON'T: Use List for Coordinates in Tuple

```python
# WRONG - Coordinates should be tuple
roi = (1, 2, [100, 100, 200, 200], 305, 3000, 0.9, "mobilenet", 0, 1, None)
```

### ✅ DO: Use Tuple for Coordinates

```python
# CORRECT
roi = (1, 2, (100, 100, 200, 200), 305, 3000, 0.9, "mobilenet", 0, 1, None)
```

---

## 📚 Reference Implementations

### Location of Official Implementation

**Primary Implementation:** `src/roi.py`

#### Key Functions

1. **`normalize_roi(r)`** - Converts any ROI format to canonical 10-field format
2. **`get_rois()`** - Returns global ROI list
3. **`set_rois(new_rois)`** - Sets global ROI list
4. **`save_rois_to_config(product_name)`** - Saves ROIs to JSON
5. **`load_rois_from_config(product_name)`** - Loads and normalizes ROIs from JSON

#### Processing Functions

**Location:** `src/inspection.py`

- **`process_roi(roi, img, product_name)`** - Main ROI processing dispatcher

**Location:** `src/roi.py`

- **`process_compare_roi(...)`** - Compare ROI processing

**Location:** `src/barcode.py`

- **`process_barcode_roi(...)`** - Barcode ROI processing

**Location:** `src/ocr.py`

- **`process_ocr_roi(...)`** - OCR ROI processing

---

## 🔄 Change Management

### When ROI Structure Changes

⚠️ **CRITICAL PROCEDURE:** If the ROI structure needs to be modified:

1. **Update This Document FIRST**
   - Modify field definitions
   - Update canonical format
   - Add new validation rules
   - Update examples

2. **Update `normalize_roi()` Function**
   - Add new field to return tuple
   - Update legacy format migrations
   - Add default values for new field

3. **Update All Processing Functions**
   - `process_roi()` in `src/inspection.py`
   - `process_compare_roi()` in `src/roi.py`
   - `process_barcode_roi()` in `src/barcode.py`
   - `process_ocr_roi()` in `src/ocr.py`

4. **Update Configuration Files**
   - Update sample configs
   - Document new field in JSON format
   - Provide migration guide

5. **Update Tests**
   - Add tests for new field
   - Test legacy format migration
   - Test validation rules

6. **Update Documentation**
   - PROJECT_INSTRUCTIONS.md
   - API documentation
   - Client documentation

### Version History

| Version | Date | Fields | Changes |
|---------|------|--------|---------|
| 2.0 | Oct 3, 2025 | 10 | Added `expected_text` field for OCR validation |
| 1.0 | Earlier | 9 | Added `device_location` field for multi-device |
| 0.x | Earlier | 3-8 | Legacy formats (pre-standardization) |

---

## 🧪 Testing Requirements

### Required Tests for ROI Handling

All ROI-related code changes MUST include these tests:

```python
def test_roi_normalization_all_formats():
    """Test normalization of all legacy formats."""
    # Test 10-field (current)
    # Test 9-field (legacy v1.0)
    # Test 8-field (pre-multi-device)
    # Test 7-field (pre-rotation)
    # Test 6-field, 5-field, 4-field, 3-field
    pass

def test_roi_type_specific_defaults():
    """Test that defaults are applied correctly by type."""
    # Test Barcode (Type 1) defaults
    # Test Compare (Type 2) defaults
    # Test OCR (Type 3) defaults
    pass

def test_roi_validation():
    """Test validation of all ROI fields."""
    # Test valid ROIs pass
    # Test invalid values fail appropriately
    pass

def test_roi_json_serialization():
    """Test ROI save/load from JSON."""
    # Test array format
    # Test object format
    # Test round-trip preservation
    pass

def test_roi_processing_by_type():
    """Test processing dispatches correctly by type."""
    # Test Type 1 → process_barcode_roi
    # Test Type 2 → process_compare_roi
    # Test Type 3 → process_ocr_roi
    pass
```

---

## 📖 Summary

### Key Takeaways

1. **Current Format:** 10 fields `(idx, typ, coords, focus, exposure, ai_threshold, feature_method, rotation, device_location, expected_text)`

2. **Always Normalize:** Use `normalize_roi()` before accessing fields

3. **Support Legacy:** All code must handle 3-10 field legacy formats

4. **Type-Specific:** Different ROI types have different required fields

5. **Validation Required:** All ROI creation/parsing must validate

6. **Document First:** Update this spec BEFORE changing ROI structure

7. **Test Thoroughly:** All format variations must be tested

---

**⚠️ COMPLIANCE STATEMENT:**

All code that handles ROIs in the Visual AOI Server MUST comply with this specification. Non-compliant code will cause system failures, data corruption, and backward compatibility issues.

When in doubt, consult this document and the reference implementation in `src/roi.py`.
