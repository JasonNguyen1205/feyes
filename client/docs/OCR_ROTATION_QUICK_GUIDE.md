# OCR Rotation - Quick Reference Guide

**Feature:** Image rotation for OCR ROIs  
**Purpose:** Read text at different orientations (0°, 90°, 180°, 270°)  
**Applies to:** **OCR ROI type ONLY**

---

## Quick Facts

✅ **Where:** ROI Editor → OCR type-specific fields  
✅ **Values:** 0° (normal), 90° (clockwise), 180° (upside down), 270° (counter-clockwise)  
✅ **Scope:** Only OCR ROIs have rotation - not barcode, compare, or text types  
✅ **Default:** 0° (no rotation)  

---

## How to Use

### Step 1: Open ROI Editor

```text
Navigate to: http://localhost:5000/roi-editor
```

### Step 2: Create or Edit OCR ROI

1. Select product and load configuration
2. Draw new ROI or select existing one
3. Set ROI Type to **"OCR (Text Recognition)"**

### Step 3: Configure Rotation

1. Look for **"Rotation Angle"** field in OCR-specific section
2. Select appropriate angle:
   - **0°** - Horizontal text (normal)
   - **90°** - Vertical text (rotated right)
   - **180°** - Upside down text
   - **270°** - Vertical text (rotated left)

### Step 4: Set Expected Text

1. Enter expected OCR result
2. Enable/disable case sensitivity
3. Save configuration

---

## Common Use Cases

### Case 1: PCB Component Labels (Vertical)

```text
Physical: C245 (printed vertically)
Setting: Rotation = 90° or 270° (try both)
Expected: "C245"
```

### Case 2: Upside-Down Serial Numbers

```text
Physical: SN123456 (upside down)
Setting: Rotation = 180°
Expected: "SN123456"
```

### Case 3: Rotated Product Codes

```text
Physical: PROD-2024 (rotated 90°)
Setting: Rotation = 90°
Expected: "PROD-2024"
```

---

## Visual Guide

### Text Orientation Examples

```text
0° Rotation (Normal):
  ┌─────┐
  │ PCB │
  └─────┘

90° Rotation (Clockwise from top):
  ┌─┐
  │P│
  │C│
  │B│
  └─┘

180° Rotation (Upside Down):
  ┌─────┐
  │ BCɅ │  (appears upside down)
  └─────┘

270° Rotation (Counter-Clockwise from top):
  ┌─┐
  │B│
  │C│
  │P│
  └─┘
```

---

## Important Notes

### ⚠️ OCR Type Only

- Rotation field **only appears** when ROI Type is set to "OCR"
- Other ROI types (barcode, compare, text) do NOT have rotation
- If you don't see rotation field, verify ROI Type is "OCR"

### 🔄 Rotation Copying

- When creating new OCR ROI, rotation copies from last OCR ROI
- Example: Last OCR had 90° → New OCR defaults to 90°
- Non-OCR ROIs do NOT copy or store rotation values

### 💾 Persistence

- Rotation value saves with ROI configuration
- Reloading configuration restores rotation setting
- Server applies rotation before OCR processing

---

## Troubleshooting

### Problem: Rotation Field Not Showing

**Solution:** Ensure ROI Type is set to "OCR (Text Recognition)"

### Problem: Text Still Unreadable

**Solution:** Try different rotation angle (90° vs 270° can be confusing)

### Problem: Rotation Not Saved

**Solution:**

1. Click "Save Configuration" button
2. Verify save confirmation message
3. Reload configuration to verify

### Problem: Wrong Rotation Direction

**Solution:**

- Clockwise/Counter-clockwise can be confusing
- Try opposite angle: 90° ↔ 270°
- Use 0° and 180° if text is only horizontal/upside-down

---

## Technical Details

### UI Location

- **File:** `templates/roi_editor.html`
- **Section:** OCR-specific fields template (line ~443)
- **Element ID:** `ocrRotation`

### JavaScript Handler

- **File:** `static/roi_editor.js`
- **Function:** `updateTypeSpecificFields()` (line ~1048)
- **Property:** `rotation` (stored as integer: 0, 90, 180, 270)

### Backend Processing

- **File:** `app.py`
- **Function:** `roi_from_server_format()`, `roi_to_server_format()`
- **Server:** Applies rotation using OpenCV before OCR

---

## API Format

### Client Format (Frontend)

```json
{
  "roi_id": 5,
  "roi_type_name": "ocr",
  "rotation": 90,
  "expected_text": "PCB",
  "coordinates": [100, 200, 300, 400]
}
```

### Server Format (Backend)

```json
{
  "idx": 5,
  "type": 3,
  "rotation": 90,
  "expected_text": "PCB",
  "coords": [100, 200, 300, 400]
}
```

---

## Testing Checklist

- [ ] Open ROI editor
- [ ] Create new ROI, set type to OCR
- [ ] Verify rotation dropdown appears in OCR section
- [ ] Set rotation to 90°
- [ ] Enter expected text
- [ ] Save configuration
- [ ] Reload page
- [ ] Verify rotation still shows 90°
- [ ] Create another OCR ROI
- [ ] Verify new ROI defaults to 90° (copied from last)
- [ ] Change ROI type to "barcode"
- [ ] Verify rotation field disappears

---

## Summary

### What Rotation Does

```text
Input: Rotated text image → Apply rotation → OCR reads corrected image → Match expected text
```

### Key Points

1. ✅ **OCR-specific only** - Not for other ROI types
2. ✅ **4 angles** - 0°, 90°, 180°, 270°
3. ✅ **Auto-copy** - New OCR ROIs inherit rotation from last OCR
4. ✅ **Server-side** - Rotation applied before OCR processing

### Expected Impact

- 📈 **Better OCR accuracy** for rotated text
- ⚡ **Faster setup** for multi-orientation products
- 🎯 **Automated inspection** of vertical/rotated labels
- ✅ **Pass/fail** based on correct text orientation
