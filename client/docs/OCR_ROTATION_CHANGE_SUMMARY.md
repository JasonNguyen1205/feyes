# OCR Rotation Feature - Change Summary

**Date:** October 10, 2025  
**Change Type:** Bug Fix / Scope Correction  
**Issue:** Rotation should only apply to OCR ROI type, not all ROI types

---

## What Changed

### Before (Incorrect)

- ❌ Rotation field appeared in **main ROI properties form** (all ROI types)
- ❌ Rotation field appeared in **OCR-specific fields** (duplicate)
- ❌ Rotation copied to all new ROIs regardless of type
- ❌ Rotation included in default attributes for all ROI types

### After (Correct)

- ✅ Rotation field **ONLY** in OCR-specific fields section
- ✅ Rotation **ONLY** copies when creating new OCR ROIs
- ✅ Rotation **NOT** included in general default attributes
- ✅ Non-OCR ROIs have no rotation property

---

## Files Modified

### 1. `templates/roi_editor.html`

**Change:** Removed rotation dropdown from main properties form

**Lines Removed (~385-400):**

```html
<!-- REMOVED: This was in wrong location -->
<div class="form-group">
  <label>Rotation:</label>
  <select id="rotation" class="glass-input" 
          onchange="updateROIProperty('rotation', parseInt(this.value))">
    <option value="0">0° (No Rotation)</option>
    <option value="90">90° (Clockwise)</option>
    <option value="180">180° (Upside Down)</option>
    <option value="270">270° (Counter-Clockwise)</option>
  </select>
  <small>Image rotation for processing</small>
</div>
```

**Lines Kept (~443):**

```html
<!-- KEPT: OCR-specific rotation - correct location -->
<template id="ocrFieldsTemplate">
  <div class="form-group">
    <label>Rotation Angle:</label>
    <select id="ocrRotation" class="glass-input"
            onchange="updateROIProperty('rotation', parseInt(this.value))">
      <option value="0">0° (No Rotation)</option>
      <option value="90">90° (Clockwise)</option>
      <option value="180">180° (Upside Down)</option>
      <option value="270">270° (Counter-Clockwise)</option>
    </select>
    <small>Rotate image before OCR processing</small>
  </div>
</template>
```

---

### 2. `static/roi_editor.js`

#### Change A: Removed rotation from main form population

**Before (Line ~1007):**

```javascript
document.getElementById('focus').value = roi.focus || 305;
document.getElementById('exposure').value = roi.exposure || 1200;
document.getElementById('rotation').value = roi.rotation || 0;  // REMOVED
document.getElementById('enabled').checked = roi.enabled !== false;
```

**After:**

```javascript
document.getElementById('focus').value = roi.focus || 305;
document.getElementById('exposure').value = roi.exposure || 1200;
document.getElementById('enabled').checked = roi.enabled !== false;
// Rotation removed - only in OCR-specific section
```

#### Change B: Removed rotation from default attributes

**Before (Line ~737):**

```javascript
let defaultAttributes = {
    roi_type_name: 'compare',
    device_id: 1,
    ai_threshold: 0.8,
    focus: 305,
    exposure: 1200,
    rotation: 0,  // REMOVED - don't set for all types
    enabled: true,
    detection_method: 'mobilenet',
    notes: ''
};
```

**After:**

```javascript
let defaultAttributes = {
    roi_type_name: 'compare',
    device_id: 1,
    ai_threshold: 0.8,
    focus: 305,
    exposure: 1200,
    enabled: true,
    detection_method: 'mobilenet',
    notes: ''
    // Rotation NOT included - only added for OCR type
};
```

#### Change C: Removed rotation from general attribute copying

**Before (Line ~753):**

```javascript
defaultAttributes = {
    roi_type_name: lastROI.roi_type_name || 'compare',
    device_id: lastROI.device_id || 1,
    ai_threshold: lastROI.ai_threshold !== undefined ? lastROI.ai_threshold : 0.8,
    focus: lastROI.focus || 305,
    exposure: lastROI.exposure || 1200,
    rotation: lastROI.rotation || 0,  // REMOVED - only for OCR
    enabled: lastROI.enabled !== undefined ? lastROI.enabled : true,
    notes: ''
};
```

**After:**

```javascript
defaultAttributes = {
    roi_type_name: lastROI.roi_type_name || 'compare',
    device_id: lastROI.device_id || 1,
    ai_threshold: lastROI.ai_threshold !== undefined ? lastROI.ai_threshold : 0.8,
    focus: lastROI.focus || 305,
    exposure: lastROI.exposure || 1200,
    enabled: lastROI.enabled !== undefined ? lastROI.enabled : true,
    notes: ''
    // Rotation removed - added separately for OCR type only
};
```

#### Change D: Kept rotation copying for OCR type ONLY

**Kept (Line ~768):**

```javascript
// Copy type-specific attributes
if (lastROI.roi_type_name === 'barcode' && lastROI.expected_pattern) {
    defaultAttributes.expected_pattern = lastROI.expected_pattern;
} else if (lastROI.roi_type_name === 'ocr') {
    if (lastROI.expected_text) defaultAttributes.expected_text = lastROI.expected_text;
    if (lastROI.rotation !== undefined) defaultAttributes.rotation = lastROI.rotation;  // KEPT
    if (lastROI.case_sensitive !== undefined) defaultAttributes.case_sensitive = lastROI.case_sensitive;
} else if (lastROI.roi_type_name === 'text' && lastROI.expected_text) {
    defaultAttributes.expected_text = lastROI.expected_text;
}
```

**Note:** This section correctly keeps rotation ONLY when copying from OCR ROI to new OCR ROI.

---

### 3. Documentation Updates

**Updated Files:**

- `docs/OCR_ROTATION_FEATURE.md` - Corrected to show OCR-only scope
- `docs/OCR_ROTATION_QUICK_GUIDE.md` - Created quick reference guide (NEW)

**Key Documentation Changes:**

- Removed references to "all ROI types"
- Added clear statement: "OCR type ONLY"
- Updated code examples to show OCR-specific handling
- Added troubleshooting note about rotation field visibility

---

## Behavior Changes

### ROI Type: Barcode

**Before:** Rotation field appeared (incorrectly)  
**After:** No rotation field ✅

### ROI Type: Compare

**Before:** Rotation field appeared (incorrectly)  
**After:** No rotation field ✅

### ROI Type: Text

**Before:** Rotation field appeared (incorrectly)  
**After:** No rotation field ✅

### ROI Type: OCR

**Before:** Rotation field appeared in TWO places (main form + OCR section)  
**After:** Rotation field appears ONLY in OCR-specific section ✅

---

## User Impact

### What Users Will Notice

1. ✅ Rotation field **only shows** when ROI Type = "OCR"
2. ✅ Changing ROI type to non-OCR **hides** rotation field
3. ✅ Creating new barcode/compare/text ROI **does not** copy rotation
4. ✅ Creating new OCR ROI **does** copy rotation from last OCR ROI

### What Users Should Do

- **For OCR ROIs:** Set rotation in the OCR-specific fields section
- **For other ROI types:** Rotation is not available (and not needed)

---

## Testing Verification

### Test Case 1: OCR ROI

```text
1. Create new ROI
2. Set type to "OCR (Text Recognition)"
3. ✅ Verify rotation dropdown appears in OCR section
4. Set rotation to 90°
5. Save and reload
6. ✅ Verify rotation persists
```

### Test Case 2: Barcode ROI

```text
1. Create new ROI
2. Set type to "Barcode"
3. ✅ Verify NO rotation field appears
4. Check properties panel
5. ✅ Verify rotation not in ROI object
```

### Test Case 3: Type Switching

```text
1. Create OCR ROI with rotation 90°
2. ✅ Rotation field visible
3. Change type to "Compare"
4. ✅ Rotation field disappears
5. Change back to "OCR"
6. ✅ Rotation field reappears
7. ✅ Rotation value still 90°
```

### Test Case 4: ROI Copying

```text
1. Create OCR ROI with rotation 90°
2. Draw another ROI
3. Set type to "OCR"
4. ✅ Verify rotation defaults to 90° (copied)
5. Draw another ROI
6. Set type to "Barcode"
7. ✅ Verify rotation NOT copied (barcode has no rotation)
```

---

## Technical Summary

### Rotation Property Scope

| ROI Type | Has Rotation? | Where Shown? | Default Value |
|----------|--------------|--------------|---------------|
| Barcode  | ❌ No        | N/A          | N/A           |
| Compare  | ❌ No        | N/A          | N/A           |
| Text     | ❌ No        | N/A          | N/A           |
| OCR      | ✅ Yes       | OCR-specific fields | 0° (if not copied) |

### JavaScript Logic

```javascript
// Rotation is ONLY handled here:
case 'ocr':
    if (document.getElementById('expectedText')) {
        document.getElementById('expectedText').value = roi.expected_text || '';
    }
    if (document.getElementById('ocrRotation')) {
        document.getElementById('ocrRotation').value = roi.rotation || 0;  // OCR-specific
    }
    if (document.getElementById('caseSensitive')) {
        document.getElementById('caseSensitive').checked = roi.case_sensitive || false;
    }
    break;
```

### Backend Compatibility

**No backend changes needed:**

- Backend already supports rotation for OCR ROIs
- `app.py` handles rotation in ROI normalization
- Server applies rotation before OCR processing
- Non-OCR ROIs simply don't send rotation parameter

---

## Migration Notes

### For Existing Configurations

**Q: What happens to existing ROI configurations?**  
A: No impact - backend already supports this scope

**Q: What if non-OCR ROI has rotation value saved?**  
A: Backend ignores it - only applies rotation to OCR ROIs

**Q: Do I need to reconfigure existing ROIs?**  
A: No - OCR ROIs will continue working with saved rotation values

---

## Rationale

### Why OCR Only?

1. **Barcode ROIs:** Barcode readers handle rotation automatically
2. **Compare ROIs:** Image comparison is rotation-invariant with current AI models
3. **Text ROIs:** Simple text matching doesn't process images
4. **OCR ROIs:** EasyOCR requires correctly oriented text for accurate reading

### Why This Matters

- **Cleaner UI:** Only show relevant controls for each ROI type
- **Less confusion:** Users won't try to rotate non-OCR ROIs
- **Correct usage:** Rotation only where it's actually processed
- **Better UX:** Type-specific fields clearly indicate purpose

---

## Rollout

### Status

✅ **Completed** - Changes implemented and tested

### Deployment

- Changes are client-side only (HTML + JavaScript)
- No server restart needed
- No database migration needed
- Users will see changes on next page refresh

### Compatibility

- ✅ Backward compatible with existing configurations
- ✅ No breaking changes to API
- ✅ Server already handles OCR-only rotation correctly

---

## Summary

### What We Fixed

- ❌ Removed rotation from general ROI properties (all types)
- ✅ Kept rotation ONLY in OCR-specific fields
- ✅ Updated JavaScript to only handle rotation for OCR type
- ✅ Updated documentation to reflect OCR-only scope

### Expected Outcome

- Users see rotation field ONLY when editing OCR ROIs
- Other ROI types have simpler, cleaner property forms
- Rotation behavior matches server-side processing logic
- Less confusion about when to use rotation
