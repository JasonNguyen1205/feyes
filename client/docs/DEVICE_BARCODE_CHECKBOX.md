# Device Barcode Checkbox in ROI Editor

**Date:** October 21, 2025  
**Feature:** Checkbox to mark barcode ROIs as device barcode for identification  
**Status:** ✅ IMPLEMENTED

## Overview

The ROI Editor now includes a **"Device Barcode" checkbox** for barcode-type ROIs, allowing users to designate which barcode should be used as the primary device identifier. This marking affects the barcode processing priority in the inspection system.

## Feature Details

### Checkbox Location

**Found in:** ROI Editor → Properties Panel → Barcode ROI Properties

**Appears when:** 
- ROI Type is set to "Barcode"
- In the type-specific fields section

### Visual Design

```
┌─────────────────────────────────────────────────────────┐
│ ☑ Device Barcode                                        │
│   Mark this as the primary barcode for device           │
│   identification. This barcode will be used for linking │
│   to external systems (Priority 0).                     │
└─────────────────────────────────────────────────────────┘
```

**Styling:**
- Large checkbox (18x18px) for easy clicking
- Bold label "Device Barcode"
- Descriptive help text below
- Cursor changes to pointer on hover

### API Schema Integration

According to the API schema (http://10.100.10.156:5000/apispec_1.json):

**Barcode Processing Priority:**
| Priority | Source | Description |
|----------|--------|-------------|
| **0** | ROI with `is_device_barcode=true` | **← This checkbox sets this!** |
| 1 | Any barcode ROI (fallback) | If no device barcode marked |
| 2 | `device_barcodes` parameter | Manual input |
| 3 | `device_barcode` parameter (legacy) | Legacy manual input |

**Effect:** Checking this box gives the barcode **highest priority** for device identification.

## Implementation

### 1. HTML Template Update

**File:** `templates/roi_editor.html`

**Added to `barcodeFieldsTemplate`:**

```html
<template id="barcodeFieldsTemplate">
  <div class="form-group">
    <label>Expected Barcode Pattern:</label>
    <input
      type="text"
      id="expectedPattern"
      class="glass-input"
      placeholder="e.g., ^\d{12}$"
      onchange="updateROIProperty('expected_pattern', this.value)"
    />
    <small>Regex pattern (optional)</small>
  </div>
  
  <!-- NEW: Device Barcode Checkbox -->
  <div class="form-group">
    <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
      <input
        type="checkbox"
        id="isDeviceBarcode"
        onchange="updateROIProperty('is_device_barcode', this.checked)"
        style="cursor: pointer; width: 18px; height: 18px;"
      />
      <span>
        <strong>Device Barcode</strong>
        <small style="display: block; color: var(--tertiary-fg); margin-top: 4px;">
          Mark this as the primary barcode for device identification.
          This barcode will be used for linking to external systems (Priority 0).
        </small>
      </span>
    </label>
  </div>
</template>
```

**Key Features:**
- Checkbox triggers `updateROIProperty('is_device_barcode', this.checked)`
- Large clickable area (label wraps checkbox)
- Inline help text explains purpose
- Responsive styling

### 2. JavaScript Update

**File:** `static/roi_editor.js`

**Updated `updateTypeSpecificFields()` function:**

```javascript
case 'barcode':
    if (document.getElementById('expectedPattern')) {
        document.getElementById('expectedPattern').value = roi.expected_pattern || '';
    }
    // NEW: Load device barcode checkbox state
    if (document.getElementById('isDeviceBarcode')) {
        document.getElementById('isDeviceBarcode').checked = roi.is_device_barcode || false;
    }
    break;
```

**Purpose:** Loads existing `is_device_barcode` value when selecting a barcode ROI

### 3. Visual Indicator in ROI List

**File:** `static/roi_editor.js`

**Updated `updateROIList()` function:**

```javascript
// Add device barcode badge if applicable
const deviceBarcodeBadge = (roi.roi_type_name === 'barcode' && roi.is_device_barcode) 
    ? '<span class="device-barcode-badge" title="Device Barcode (Priority 0)">📱</span>' 
    : '';

item.innerHTML = `
    <div class="roi-item-header">
        <span class="roi-item-id">ROI ${roi.roi_id}${deviceBarcodeBadge}</span>
        <span class="roi-item-type">${roi.roi_type_name}</span>
    </div>
    <div class="roi-item-device">Device ${roi.device_id}</div>
    <div class="roi-item-coords">[${roi.coordinates.join(', ')}]</div>
`;
```

**Effect:** Adds 📱 badge next to ROI ID for device barcodes

### 4. CSS Styling

**File:** `static/roi_editor.css`

```css
/* Device Barcode Badge */
.device-barcode-badge {
    display: inline-block;
    margin-left: 6px;
    font-size: 0.9em;
    vertical-align: middle;
    cursor: help;
    opacity: 0.9;
    transition: opacity 0.2s ease;
}

.device-barcode-badge:hover {
    opacity: 1;
}
```

**Features:**
- Phone emoji (📱) indicates device barcode
- Subtle opacity (0.9) at rest
- Full opacity (1.0) on hover
- Cursor shows "help" icon on hover
- Tooltip shows "Device Barcode (Priority 0)"

## User Experience

### ROI List Display

**Before:**
```
┌─────────────────────────┐
│ ROI 1     barcode       │
│ Device 1                │
│ [100, 200, 300, 400]    │
└─────────────────────────┘
```

**After (with device barcode):**
```
┌─────────────────────────┐
│ ROI 1 📱  barcode       │
│ Device 1                │
│ [100, 200, 300, 400]    │
└─────────────────────────┘
```

**Badge indicates:** This barcode is the device identifier (Priority 0)

### Properties Panel

**When editing barcode ROI:**

```
┌──────────────────────────────────────────────────────┐
│ ROI Properties                                       │
├──────────────────────────────────────────────────────┤
│ ROI Type: [Barcode ▼]                               │
│                                                      │
│ Expected Barcode Pattern:                           │
│ [                                 ]                  │
│ Regex pattern (optional)                            │
│                                                      │
│ ☑ Device Barcode                                    │
│   Mark this as the primary barcode for device       │
│   identification. This barcode will be used for     │
│   linking to external systems (Priority 0).         │
└──────────────────────────────────────────────────────┘
```

## Workflow

### Creating Device Barcode ROI

1. **Open ROI Editor**
2. **Load product configuration**
3. **Draw barcode ROI** on image
4. **Set properties:**
   - ROI Type: Barcode
   - Device ID: (select device)
   - Expected Pattern: (optional)
5. **Check "Device Barcode" checkbox** ✓
6. **Save configuration**

### Identifying Device Barcode

**In ROI List:**
- Look for 📱 badge next to ROI ID
- Only one ROI per device should have this badge

**In Properties Panel:**
- "Device Barcode" checkbox will be checked
- Help text explains Priority 0 status

## Data Structure

### ROI Configuration JSON

**Without device barcode flag:**
```json
{
  "roi_id": 1,
  "roi_type_name": "barcode",
  "device_id": 1,
  "coordinates": [100, 200, 300, 400],
  "expected_pattern": "^\\d{12}$"
}
```

**With device barcode flag:**
```json
{
  "roi_id": 1,
  "roi_type_name": "barcode",
  "device_id": 1,
  "coordinates": [100, 200, 300, 400],
  "expected_pattern": "^\\d{12}$",
  "is_device_barcode": true
}
```

**Field:** `is_device_barcode` (boolean)
- `true` → Priority 0 (highest) for device identification
- `false` or missing → Normal barcode ROI

## Server Processing

### When `is_device_barcode: true`

**Priority 0 Processing:**

1. **Scan barcode** from marked ROI
2. **Send to linking API:**
   ```
   POST http://10.100.10.83:5000/api/ProcessLock/FA/GetLinkData
   Input:  "1897848 S/N: 65514 3969 1006 V"
   Output: "1897848-0001555-118714"
   ```
3. **Return as device barcode:**
   ```json
   {
     "device_summaries": {
       "1": {
         "barcode": "1897848-0001555-118714"
       }
     }
   }
   ```

### When `is_device_barcode: false` or missing

**Fallback to Priority 1-3:**
- Check other barcode ROIs (Priority 1)
- Check `device_barcodes` parameter (Priority 2)
- Check `device_barcode` parameter (Priority 3)

## Best Practices

### When to Mark as Device Barcode

✅ **DO mark as device barcode:**
- Primary device identification barcode
- Serial number barcode
- Main tracking barcode
- One per device maximum

❌ **DON'T mark as device barcode:**
- Component barcodes
- Secondary tracking codes
- QR codes for documentation
- Multiple barcodes per device

### Configuration Guidelines

**Recommended Setup:**

**Device 1:**
- ROI 1: Barcode (is_device_barcode: true) ← Serial number
- ROI 2: Barcode (is_device_barcode: false) ← Component code
- ROI 3: OCR ← Version text

**Device 2:**
- ROI 4: Barcode (is_device_barcode: true) ← Serial number
- ROI 5: Compare ← Logo check

**Result:** Each device has one primary barcode for identification

## Validation

### Client-Side Validation

**Current:** No validation enforced (flexible design)

**Future Enhancement:** Could add validation:
- Warn if multiple device barcodes per device
- Suggest which barcode should be primary
- Highlight conflicts in UI

### Server-Side Validation

**Server handles priority automatically:**
- If multiple ROIs marked with `is_device_barcode: true`, uses first detected
- Falls back to Priority 1-3 if none marked

## Testing Checklist

- [x] Checkbox appears for barcode ROIs
- [x] Checkbox hidden for non-barcode ROIs (OCR, compare, text)
- [x] Checking box updates ROI property
- [x] Unchecking box updates ROI property
- [x] Checkbox state loads correctly when selecting existing ROI
- [x] Badge (📱) appears in ROI list for marked ROIs
- [x] Badge has tooltip "Device Barcode (Priority 0)"
- [x] Property saves to configuration JSON
- [x] Property loads from configuration JSON
- [x] Works across page refreshes
- [x] No console errors
- [x] Responsive on mobile/tablet

## API Integration

### Configuration Endpoint

**POST** `/api/products/{product_name}/config`

**Request Body:**
```json
{
  "product_name": "TestProduct",
  "rois": [
    {
      "roi_id": 1,
      "roi_type_name": "barcode",
      "device_id": 1,
      "coordinates": [100, 200, 300, 400],
      "is_device_barcode": true  // ← Saved to server
    }
  ]
}
```

### Inspection Endpoint

**Server uses `is_device_barcode` field:**

```python
# Server-side processing
if roi.is_device_barcode:
    # Priority 0: Use this barcode for device identification
    device_barcode = scan_barcode(roi)
    linked_barcode = call_linking_api(device_barcode)
    device_summaries[device_id]['barcode'] = linked_barcode
```

## Related Features

- **Linked Barcode System:** `docs/LINKED_BARCODE_SYSTEM.md`
- **Dual Barcode Display:** `docs/DUAL_BARCODE_DISPLAY.md`
- **API Schema:** http://10.100.10.156:5000/apispec_1.json

## Future Enhancements

### Potential Improvements

1. **Visual Priority Indicator:**
   - Different badge colors for priorities
   - Priority 0: 📱 (blue)
   - Priority 1: 📊 (gray)

2. **Conflict Detection:**
   - Warn if multiple device barcodes per device
   - Auto-suggest primary barcode
   - Show priority in tooltip

3. **Batch Operations:**
   - Mark multiple ROIs as device barcode
   - Copy device barcode flag between devices
   - Import/export device barcode mapping

4. **Advanced Configuration:**
   - Fallback priority configuration
   - Per-device barcode preferences
   - Conditional device barcode selection

## Troubleshooting

### Checkbox Not Appearing

**Cause:** ROI type is not "barcode"  
**Solution:** Change ROI Type to "Barcode" first

### Checkbox State Not Saving

**Cause:** Configuration not saved to server  
**Solution:** Click "Save Configuration" button after changes

### Badge Not Showing in List

**Cause:** Page not refreshed after changing checkbox  
**Solution:** ROI list updates automatically - check console for errors

### Multiple Badges on Same Device

**Cause:** Multiple ROIs marked as device barcode  
**Solution:** Only mark one barcode ROI per device as primary

## Accessibility

- ✅ **Keyboard:** Checkbox focusable with Tab key
- ✅ **Screen readers:** Label text announced
- ✅ **Visual:** Large clickable area
- ✅ **Tooltip:** Help text on badge hover
- ⚠️ **ARIA:** Could add aria-describedby for help text

## Browser Compatibility

✅ **All Modern Browsers:**
- Checkbox styling (standard HTML)
- Emoji badge (📱 Unicode U+1F4F1)
- CSS hover effects
- JavaScript event handlers

## Files Modified

| File | Changes |
|------|---------|
| `templates/roi_editor.html` | Added checkbox to barcode fields template |
| `static/roi_editor.js` | Updated `updateTypeSpecificFields()` to load checkbox state |
| `static/roi_editor.js` | Updated `updateROIList()` to show device barcode badge |
| `static/roi_editor.css` | Added `.device-barcode-badge` styling |

## Conclusion

The device barcode checkbox provides:
- ✅ **Clear designation** of primary device barcode
- ✅ **Visual indicator** in ROI list (📱 badge)
- ✅ **Priority control** for inspection processing
- ✅ **API compliance** with linked barcode system
- ✅ **User-friendly** with inline help text

**Result:** Users can now explicitly mark which barcode should be used for device identification! ✨

**Status:** Production-ready ✓
