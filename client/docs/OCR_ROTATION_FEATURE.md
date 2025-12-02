# OCR ROI Rotation Feature Implementation

**Date:** October 10, 2025  
**Feature:** Image rotation for OCR ROIs to read text correctly  
**Purpose:** Enable OCR processing of rotated text on products

---

## Problem Statement

### Why Rotation is Needed

Many products have text printed in different orientations:

```
Examples:
┌─────────────────────────────┐
│ PCB Component Labels:       │
│   - Horizontal text: "R1"   │
│   - Vertical text: "C245"   │
│   - Upside down: "U3"       │
│   - 270° rotated: "J4"      │
└─────────────────────────────┘
```

**Without Rotation:**

```
Original Image (90° rotated text):
  ───
  P│
  C│
  B│
  ───

OCR Result: "❌ Unable to read" or garbage
```

**With Rotation:**

```
Rotated Image (corrected to 0°):
  ─────
  │PCB│
  ─────

OCR Result: "✅ PCB"
```

---

## Solution Overview

### Server API Support

According to the server's Swagger API documentation:

**ROI Schema includes `rotation` field:**

```json
{
  "idx": 1,
  "type": 3,  // OCR type
  "coords": [100, 200, 300, 400],
  "rotation": 90,  // 0, 90, 180, or 270 degrees
  "expected_text": "PCB"
}
```

**Rotation Values:**

- `0` - No rotation (default)
- `90` - Rotate 90° clockwise
- `180` - Rotate 180° (upside down)
- `270` - Rotate 270° clockwise (or 90° counter-clockwise)

### Implementation

**Frontend Enhancement:**

1. ✅ Added rotation dropdown to ROI editor UI
2. ✅ Added rotation field to OCR-specific fields
3. ✅ Updated JavaScript to handle rotation property
4. ✅ Ensured rotation persists when saving configuration

**Backend Support:**

- ✅ Already implemented in `app.py` (rotation field in ROI normalization)
- ✅ Server processes rotated images before OCR

---

## UI Changes

### OCR-Specific Fields Template

**Location:** `templates/roi_editor.html` - OCR template section

**Added:**

```html
<div class="form-group">
  <label>Rotation Angle:</label>
  <select
    id="ocrRotation"
    class="glass-input"
    onchange="updateROIProperty('rotation', parseInt(this.value))"
  >
    <option value="0">0° (No Rotation)</option>
    <option value="90">90° (Clockwise)</option>
    <option value="180">180° (Upside Down)</option>
    <option value="270">270° (Counter-Clockwise)</option>
  </select>
  <small>Rotate image before OCR processing</small>
</div>
```

**Benefits:**

- **OCR-specific only** - Rotation only applies to OCR ROI type
- Clear visual description of rotation direction
- Dropdown prevents invalid values
- Appears in type-specific fields section when OCR type is selected

---

## JavaScript Updates

### 1. OCR-Specific Field Population

**File:** `static/roi_editor.js`

**Added rotation loading for OCR template:**

```javascript
case 'ocr':
    if (document.getElementById('expectedText')) {
        document.getElementById('expectedText').value = roi.expected_text || '';
    }
    if (document.getElementById('ocrRotation')) {
        document.getElementById('ocrRotation').value = roi.rotation || 0;
    }
    if (document.getElementById('caseSensitive')) {
        document.getElementById('caseSensitive').checked = roi.case_sensitive || false;
    }
    break;
```

**Location:** `updateTypeSpecificFields()` function (line ~1045)

### 2. OCR Type-Specific Rotation Copying

**Added rotation copying only for OCR ROIs:**

```javascript
// Copy type-specific attributes
if (lastROI.roi_type_name === 'barcode' && lastROI.expected_pattern) {
    defaultAttributes.expected_pattern = lastROI.expected_pattern;
} else if (lastROI.roi_type_name === 'ocr') {
    if (lastROI.expected_text) defaultAttributes.expected_text = lastROI.expected_text;
    if (lastROI.rotation !== undefined) defaultAttributes.rotation = lastROI.rotation;  // Only for OCR
    if (lastROI.case_sensitive !== undefined) defaultAttributes.case_sensitive = lastROI.case_sensitive;
} else if (lastROI.roi_type_name === 'text' && lastROI.expected_text) {
    defaultAttributes.expected_text = lastROI.expected_text;
}
```

**Location:** `createROI()` function (line ~760)

**Note:** Rotation is NOT included in default attributes anymore - it's only added when copying from an OCR-type ROI.

---

## Usage Guide

### Creating OCR ROI with Rotation

**Step-by-Step:**

1. **Open ROI Editor**

   ```
   Navigate to: http://localhost:5000/roi-editor
   ```

2. **Load Product Configuration**
   - Select product from dropdown
   - Click "Load Configuration"

3. **Create New ROI**
   - Select "Draw" tool
   - Draw rectangle around text area
   - Select "OCR (Text Recognition)" as ROI Type

4. **Configure Rotation**
   - In main properties: Set "Rotation" dropdown
   - In OCR fields: Set "Rotation Angle" dropdown
   - Choose appropriate angle:
     - `0°` - Text is horizontal (normal)
     - `90°` - Text is vertical (rotated clockwise)
     - `180°` - Text is upside down
     - `270°` - Text is vertical (rotated counter-clockwise)

5. **Set Expected Text**
   - Enter expected OCR result in "Expected Text" field
   - Enable/disable "Case Sensitive" as needed

6. **Save Configuration**
   - Click "Save Configuration"
   - Server will apply rotation during OCR processing

---

## Use Cases

### Case 1: PCB Component Labels

**Scenario:** Component designators printed vertically

```
Physical Layout:
     C
     2
     4
     5

Configuration:
- ROI Type: OCR
- Rotation: 90° (Clockwise)
- Expected Text: "C245"
```

### Case 2: Upside-Down Serial Numbers

**Scenario:** Serial number on bottom of product

```
Physical Layout:
  (upside down) 123456789

Configuration:
- ROI Type: OCR
- Rotation: 180° (Upside Down)
- Expected Text: "123456789"
```

### Case 3: Vertical Barcode Text

**Scenario:** Text accompanying vertical barcode

```
Physical Layout:
  P
  R
  O
  D
  U
  C
  T

Configuration:
- ROI Type: OCR
- Rotation: 90° or 270° (depending on direction)
- Expected Text: "PRODUCT"
```

### Case 4: Multi-Device Products

**Scenario:** 4-device PCB with different text orientations

```
Device 1: Horizontal text (0°)
Device 2: 90° rotated text
Device 3: 180° rotated text
Device 4: 270° rotated text

Configuration:
- Create separate ROI for each device
- Set appropriate rotation for each ROI
- Each ROI can have different rotation value
```

---

## Backend Processing Flow

### Server-Side Rotation

**When inspection is performed:**

1. **Receive ROI Configuration**

   ```json
   {
     "roi_id": 5,
     "roi_type_name": "ocr",
     "rotation": 90,
     "expected_text": "PCB"
   }
   ```

2. **Image Cropping**

   ```python
   # Crop ROI from full image
   roi_image = full_image[y1:y2, x1:x2]
   ```

3. **Apply Rotation**

   ```python
   # Rotate image before OCR
   if rotation == 90:
       roi_image = cv2.rotate(roi_image, cv2.ROTATE_90_CLOCKWISE)
   elif rotation == 180:
       roi_image = cv2.rotate(roi_image, cv2.ROTATE_180)
   elif rotation == 270:
       roi_image = cv2.rotate(roi_image, cv2.ROTATE_90_COUNTERCLOCKWISE)
   ```

4. **OCR Processing**

   ```python
   # Now text is correctly oriented
   ocr_result = easyocr_reader.readtext(roi_image)
   ```

5. **Compare with Expected Text**

   ```python
   # Validate result
   if ocr_result == expected_text:
       passed = True
   ```

---

## Testing Checklist

### Functional Testing

- [ ] **Rotation Field Appears**

  ```
  ✓ Main ROI properties form shows rotation dropdown
  ✓ OCR-specific fields show rotation dropdown
  ✓ All 4 rotation options available (0°, 90°, 180°, 270°)
  ```

- [ ] **Rotation Saves Correctly**

  ```
  ✓ Set rotation to 90°
  ✓ Save configuration
  ✓ Reload configuration
  ✓ Verify rotation is still 90°
  ```

- [ ] **Rotation Copies to New ROIs**

  ```
  ✓ Create ROI with rotation 90°
  ✓ Draw another ROI
  ✓ Verify new ROI inherits rotation 90°
  ```

- [ ] **OCR Processing with Rotation**

  ```
  ✓ Create OCR ROI with vertical text
  ✓ Set rotation to 90°
  ✓ Perform inspection
  ✓ Verify OCR reads text correctly
  ```

### Visual Verification

**Test Product Setup:**

```
Create test image with:
- Horizontal text: "PASS"
- 90° rotated text: "TEST"
- 180° rotated text: "OKAY"
- 270° rotated text: "DONE"
```

**Expected Results:**

```
ROI 1 (0° rotation):   "PASS" ✓
ROI 2 (90° rotation):  "TEST" ✓
ROI 3 (180° rotation): "OKAY" ✓
ROI 4 (270° rotation): "DONE" ✓
```

---

## Troubleshooting

### Issue: Rotation Not Applied

**Symptoms:**

- Text still not recognized
- OCR returns empty or incorrect results

**Checks:**

1. Verify rotation value saved in configuration
2. Check server logs for rotation application
3. Ensure image crop is correct before rotation

**Solution:**

```javascript
// Check ROI object
console.log('ROI rotation:', roi.rotation);

// Should output: 90, 180, 270, or 0
```

### Issue: Wrong Rotation Direction

**Symptoms:**

- Text still unreadable after rotation
- Need opposite rotation

**Solution:**

```
If using 90°, try 270° instead
If using 270°, try 90° instead

Clockwise vs Counter-Clockwise can be confusing
```

### Issue: Rotation Not Showing in UI

**Symptoms:**

- Rotation dropdown missing
- Rotation value not populated

**Checks:**

1. Clear browser cache
2. Verify template changes deployed
3. Check JavaScript console for errors

**Solution:**

```bash
# Hard refresh browser
Ctrl + Shift + R (Windows/Linux)
Cmd + Shift + R (Mac)
```

---

## API Integration

### ROI Configuration Format

**Client Format (Frontend):**

```javascript
{
  roi_id: 5,
  roi_type_name: "ocr",
  device_id: 1,
  coordinates: [100, 200, 300, 400],
  rotation: 90,  // Degrees
  expected_text: "PCB",
  focus: 305,
  exposure: 1200,
  ai_threshold: 0.8
}
```

**Server Format (Backend API):**

```json
{
  "idx": 5,
  "type": 3,
  "device_location": 1,
  "coords": [100, 200, 300, 400],
  "rotation": 90,
  "expected_text": "PCB",
  "focus": 305,
  "exposure": 1200,
  "ai_threshold": 0.8
}
```

**Conversion:**

- `roi_id` ↔ `idx`
- `roi_type_name: "ocr"` ↔ `type: 3`
- `device_id` ↔ `device_location`
- `coordinates` ↔ `coords`
- `rotation` ↔ `rotation` (same name, both int)

---

## Files Modified

### Frontend Files

1. **`templates/roi_editor.html`**
   - Added rotation field to OCR-specific template ONLY
   - Line ~443 (OCR template)
   - **Note:** Rotation dropdown removed from main properties form

2. **`static/roi_editor.js`**
   - Added OCR rotation field population (line ~1048)
   - Added rotation copying for OCR type only (line ~760)
   - **Note:** Removed rotation from default attributes (no longer in general ROI properties)

### Backend Files

**No changes needed** - `app.py` already supports rotation:

- Line 383: `roi_from_server_format()` includes rotation
- Line 435: `roi_to_server_format()` includes rotation
- Line 464: Documentation mentions rotation (0, 90, 180, 270)
- Line 558: `normalize_roi()` handles rotation

---

## Future Enhancements

### Potential Improvements

1. **Visual Rotation Preview**

   ```javascript
   // Show rotated ROI on canvas
   function drawRotatedROI(roi) {
       ctx.save();
       ctx.rotate(roi.rotation * Math.PI / 180);
       ctx.strokeRect(...);
       ctx.restore();
   }
   ```

2. **Auto-Rotation Detection**

   ```python
   # AI-based text orientation detection
   detected_angle = detect_text_orientation(image)
   if detected_angle != 0:
       suggest_rotation(detected_angle)
   ```

3. **Rotation Testing Tool**

   ```html
   <!-- Try different rotations visually -->
   <button onclick="testRotation(0)">Test 0°</button>
   <button onclick="testRotation(90)">Test 90°</button>
   <button onclick="testRotation(180)">Test 180°</button>
   <button onclick="testRotation(270)">Test 270°</button>
   ```

---

## Related Documentation

- Server Swagger API: `http://10.100.27.156:5000/apidocs/`
- ROI Schema: `/api/schema/roi`
- App.py normalization: `roi_from_server_format()`, `roi_to_server_format()`

---

## Summary

### What Was Added

✅ **Rotation dropdown in OCR-specific fields only**  
✅ **JavaScript handling for rotation property (OCR type only)**  
✅ **Rotation persistence in configuration**  
✅ **Rotation copying when creating new OCR ROIs**

### Why It Matters

🎯 **Critical for reading rotated text on products:**

- PCB component labels (often vertical)
- Product serial numbers (may be upside down)
- Multi-orientation text layouts
- Improves OCR accuracy significantly

### Expected Behavior

```
User selects rotation → Server rotates image → OCR processes correctly → Text recognized ✅
```

### User Experience

**Before:**

```
Vertical text → OCR fails → Manual verification needed
```

**After:**

```
Vertical text → Set rotation 90° → OCR succeeds → Automated inspection ✅
```
