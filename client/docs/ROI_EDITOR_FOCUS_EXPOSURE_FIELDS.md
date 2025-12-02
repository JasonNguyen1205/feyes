# ROI Editor - Focus & Exposure Fields

**Date:** October 4, 2025  
**Feature:** Add camera focus and exposure input fields to ROI properties  
**Status:** ✅ IMPLEMENTED

---

## Overview

Added **focus** and **exposure** camera parameter input fields to the ROI Editor's properties panel. These fields allow users to configure camera settings for each ROI, which is essential for multi-ROI inspection with different focus/exposure requirements.

---

## Implementation Details

### 1. HTML Template Updates

**File:** `templates/roi_editor.html`

**Added Fields (after AI Threshold):**

```html
<div class="form-group">
    <label>Focus:</label>
    <input type="number" id="focus" class="glass-input" 
           min="0" max="1000" step="1" value="305"
           onchange="updateROIProperty('focus', parseInt(this.value))">
    <small>Camera focus value (0 - 1000)</small>
</div>

<div class="form-group">
    <label>Exposure:</label>
    <input type="number" id="exposure" class="glass-input" 
           min="0" max="10000" step="10" value="1200"
           onchange="updateROIProperty('exposure', parseInt(this.value))">
    <small>Camera exposure time (μs)</small>
</div>
```

**Field Specifications:**

| Field | Type | Range | Step | Default | Unit |
|-------|------|-------|------|---------|------|
| Focus | number | 0-1000 | 1 | 305 | dimensionless |
| Exposure | number | 0-10000 | 10 | 1200 | microseconds (μs) |

### 2. JavaScript Updates

**File:** `static/roi_editor.js`

#### A. createROI() Function

**Added default values for new ROIs:**

```javascript
return {
    roi_id: maxId + 1,
    roi_type_name: 'compare',
    device_id: 1,
    coordinates: [...],
    ai_threshold: 0.8,
    focus: 305,           // NEW: Default focus
    exposure: 1200,       // NEW: Default exposure
    enabled: true,
    notes: ''
};
```

#### B. updatePropertiesPanel() Function

**Populate focus and exposure fields when ROI selected:**

```javascript
// Populate form with ROI data
document.getElementById('focus').value = roi.focus || 305;
document.getElementById('exposure').value = roi.exposure || 1200;
```

**Default Values:**

- If ROI has no `focus` value → defaults to 305
- If ROI has no `exposure` value → defaults to 1200

### 3. Backend Legacy Config Conversion

**File:** `app.py`

**Updated ROI conversion to include focus and exposure:**

```python
roi = {
    "roi_id": roi_data[0],
    "roi_type_name": roi_type_name,
    "device_id": roi_data[1],
    "coordinates": roi_data[2],
    "ai_threshold": roi_data[5] if roi_data[5] is not None else 0.8,
    "focus": roi_data[3],      # NEW: Extract focus value
    "exposure": roi_data[4],   # NEW: Extract exposure value
    "enabled": True,
    "notes": f"Legacy config - Model: {roi_data[6]}, Rotation: {roi_data[7]}"
}
```

**Before:**

- Focus and exposure stored only in notes: `"Legacy config - Focus: 305, Exposure: 1200, Model: opencv"`

**After:**

- Focus and exposure as proper fields
- Notes show only: `"Legacy config - Model: opencv, Rotation: 0"`

---

## UI Layout

### Properties Panel Order

```
⚙️ ROI Properties
├── ROI ID: [1]
├── ROI Type: [Barcode ▼]
├── Device ID: [Device 1 ▼]
├── Coordinates:
│   ├── X1: [3459]  Y1: [2959]
│   └── X2: [4058]  Y2: [3318]
├── AI Threshold: [0.8]
│   └── Similarity threshold (0.0 - 1.0)
├── Focus: [305]                    ← NEW
│   └── Camera focus value (0 - 1000)
├── Exposure: [1200]                ← NEW
│   └── Camera exposure time (μs)
├── [✓] Enabled
└── Notes: [____________]
```

---

## Data Format

### ROI Object Schema

**Complete ROI Structure:**

```json
{
  "roi_id": 1,
  "roi_type_name": "barcode",
  "device_id": 1,
  "coordinates": [3459, 2959, 4058, 3318],
  "ai_threshold": 0.8,
  "focus": 305,
  "exposure": 1200,
  "enabled": true,
  "notes": "Legacy config - Model: opencv, Rotation: 0"
}
```

**Field Descriptions:**

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `roi_id` | integer | Unique ROI identifier | 1 |
| `roi_type_name` | string | Type of inspection | "barcode" |
| `device_id` | integer | Device number (1-4) | 1 |
| `coordinates` | array | Bounding box [x1,y1,x2,y2] | [3459, 2959, 4058, 3318] |
| `ai_threshold` | float | AI match threshold (0-1) | 0.8 |
| `focus` | integer | **Camera focus setting** | **305** |
| `exposure` | integer | **Camera exposure (μs)** | **1200** |
| `enabled` | boolean | ROI active status | true |
| `notes` | string | Optional notes | "Model: opencv" |

---

## Use Cases

### 1. Different Focus Per Device

**Scenario:** Multi-layer PCB with components at different heights

**Example:**

```json
{
  "rois": [
    {
      "roi_id": 1,
      "device_id": 1,
      "focus": 305,      // Top layer components
      "exposure": 1200
    },
    {
      "roi_id": 2,
      "device_id": 2,
      "focus": 320,      // Mid-layer traces
      "exposure": 1200
    },
    {
      "roi_id": 3,
      "device_id": 3,
      "focus": 290,      // Bottom layer components
      "exposure": 1200
    }
  ]
}
```

### 2. Different Exposure Per ROI Type

**Scenario:** Barcode needs higher exposure than visual inspection

**Example:**

```json
{
  "rois": [
    {
      "roi_id": 1,
      "roi_type_name": "barcode",
      "focus": 305,
      "exposure": 1500    // Higher for barcode readability
    },
    {
      "roi_id": 2,
      "roi_type_name": "compare",
      "focus": 305,
      "exposure": 1000    // Lower for visual inspection
    }
  ]
}
```

### 3. Dark vs Bright Areas

**Scenario:** Product has both reflective and dark areas

**Example:**

```json
{
  "rois": [
    {
      "roi_id": 1,
      "notes": "Reflective metal surface",
      "focus": 305,
      "exposure": 800     // Lower exposure for bright areas
    },
    {
      "roi_id": 2,
      "notes": "Dark component cavity",
      "focus": 305,
      "exposure": 2000    // Higher exposure for dark areas
    }
  ]
}
```

---

## API Response

### GET /api/products/{product_name}/config

**Example Response:**

```json
{
  "product_name": "20003548",
  "rois": [
    {
      "roi_id": 1,
      "roi_type_name": "barcode",
      "device_id": 1,
      "coordinates": [3459, 2959, 4058, 3318],
      "ai_threshold": 0.8,
      "focus": 305,
      "exposure": 1200,
      "enabled": true,
      "notes": "Legacy config - Model: opencv, Rotation: 0"
    },
    {
      "roi_id": 2,
      "roi_type_name": "compare",
      "device_id": 1,
      "coordinates": [1691, 2959, 2572, 3473],
      "ai_threshold": 0.8,
      "focus": 305,
      "exposure": 1200,
      "enabled": true,
      "notes": "Legacy config - Model: opencv, Rotation: 0"
    }
  ]
}
```

---

## Testing

### Verification Steps

1. **Open ROI Editor:**

   ```
   http://localhost:5100/roi-editor
   ```

2. **Load Product:**
   - Select: "20003548"
   - Click: "Load Configuration"
   - Result: 6 ROIs loaded with focus and exposure

3. **View Properties:**
   - Click on any ROI in the list
   - Properties panel shows:
     - Focus: 305
     - Exposure: 1200

4. **Edit Values:**
   - Change focus: 305 → 310
   - Change exposure: 1200 → 1300
   - Values update in real-time

5. **Create New ROI:**
   - Draw new ROI on canvas
   - Check properties:
     - Focus: 305 (default)
     - Exposure: 1200 (default)

6. **Save Configuration:**
   - Modify focus/exposure values
   - Click "💾 Save to Server"
   - Reload configuration
   - Values persisted correctly

### Backend Testing

**Load Config API:**

```bash
curl -s http://localhost:5100/api/products/20003548/config | jq '.rois[0]'
```

**Expected Output:**

```json
{
  "roi_id": 1,
  "roi_type_name": "barcode",
  "device_id": 1,
  "coordinates": [3459, 2959, 4058, 3318],
  "ai_threshold": 0.8,
  "focus": 305,
  "exposure": 1200,
  "enabled": true,
  "notes": "Legacy config - Model: opencv, Rotation: 0"
}
```

**Verify Focus & Exposure:**

```bash
curl -s http://localhost:5100/api/products/20003548/config | \
  jq '.rois[0] | {roi_id, focus, exposure}'
```

**Expected Output:**

```json
{
  "roi_id": 1,
  "focus": 305,
  "exposure": 1200
}
```

---

## Backward Compatibility

### Legacy Configs

**Old Format (Array):**

```json
[
  [1, 1, [3459,2959,4058,3318], 305, 1200, null, "opencv", 0, 1]
]
```

**Converted to:**

```json
{
  "rois": [
    {
      "roi_id": 1,
      "focus": 305,       ← Extracted from [3]
      "exposure": 1200,   ← Extracted from [4]
      ...
    }
  ]
}
```

### Missing Values

**If ROI lacks focus/exposure:**

```javascript
document.getElementById('focus').value = roi.focus || 305;        // Default 305
document.getElementById('exposure').value = roi.exposure || 1200;  // Default 1200
```

---

## Camera Integration

### Future: Apply Settings on Capture

**Potential Enhancement:**

```javascript
async function captureWithROISettings(roi) {
    // Apply ROI-specific camera settings before capture
    await fetch('/api/camera/settings', {
        method: 'POST',
        body: JSON.stringify({
            focus: roi.focus,
            exposure: roi.exposure
        })
    });
    
    // Capture with applied settings
    const response = await fetch('/api/camera/capture');
    return response.json();
}
```

**Benefits:**

- Automatic camera adjustment per ROI
- Optimal image quality for each inspection area
- No manual camera setting changes

---

## Summary

### Changes Made

**Files Modified:**

1. `templates/roi_editor.html` - Added focus and exposure input fields
2. `static/roi_editor.js` - Added default values and property population
3. `app.py` - Updated legacy config conversion to extract focus/exposure

### Features Added

- ✅ Focus input field (0-1000, default 305)
- ✅ Exposure input field (0-10000 μs, default 1200)
- ✅ Real-time property updates
- ✅ Legacy config conversion
- ✅ Default value handling
- ✅ Proper data persistence

### User Benefits

1. **Precise Control:** Configure camera settings per ROI
2. **Flexibility:** Different settings for different inspection areas
3. **Visibility:** See exact focus/exposure values used
4. **Ease of Use:** Simple number inputs with clear labels
5. **Data Preservation:** Legacy configs retain original values

### Technical Benefits

1. **Clean Data Model:** Focus/exposure as proper fields, not embedded in notes
2. **Type Safety:** Integer validation and range constraints
3. **Backward Compatible:** Legacy configs automatically converted
4. **Default Values:** Sensible defaults for new ROIs
5. **Future Ready:** Ready for camera setting automation

---

## Related Documentation

- `docs/ROI_EDITOR_USER_GUIDE.md` - User guide with screenshots
- `docs/ROI_EDITOR_API_AUDIT.md` - Complete API documentation
- `docs/ROI_EDITOR_LEGACY_CONFIG_FIX.md` - Legacy format conversion details
