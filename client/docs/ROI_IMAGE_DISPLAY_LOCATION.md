# Device ROI Result Cards - Image Display Location Guide

**Date:** October 3, 2025

## 📍 Image Location in UI

The **related images** (golden sample and captured image) are displayed **at the bottom of each ROI card**, after all the ROI details.

---

## 🏗️ Complete ROI Card Structure

```
┌─────────────────────────────────────────────────────┐
│  📱 Device 1                          ✓ PASS        │  ← Device Card Header
├─────────────────────────────────────────────────────┤
│  Barcode: 20003548-0000003-1019720-101              │
│  ROI Status: 2 / 3 Passed (1 Failed)                │  ← Device Info
│  Success Rate: 66.7%                                 │
├─────────────────────────────────────────────────────┤
│  🔍 ROI Inspection Details                          │  ← ROI Section Title
│                                                      │
│  ┌──────────────────────────────────────────────┐  │
│  │ ROI 1 [barcode]               ✓ PASS        │  │  ← ROI Header
│  ├──────────────────────────────────────────────┤  │
│  │ Barcode Value: ABC123                        │  │
│  │ Position: [3459, 2959, 4058, 3318]           │  │  ← ROI Details
│  ├──────────────────────────────────────────────┤  │
│  │ 🌟 Golden Sample    📸 Captured Image       │  │
│  │ [Golden Image]      [Captured Image]         │  │  ← IMAGES HERE!
│  │ Click to enlarge    Click to enlarge         │  │
│  └──────────────────────────────────────────────┘  │
│                                                      │
│  ┌──────────────────────────────────────────────┐  │
│  │ ROI 5 [compare]               ✗ FAIL        │  │
│  ├──────────────────────────────────────────────┤  │
│  │ AI Similarity: 88.35%                        │  │
│  │ [Progress Bar: ▓▓▓▓▓▓▓▓░░]                  │  │
│  │ Threshold: 90.00%                            │  │
│  │ Match Result: ✗ Different                    │  │
│  │ Position: [3301, 3876, 3721, 4459]           │  │
│  ├──────────────────────────────────────────────┤  │
│  │ 🌟 Golden Sample    📸 Captured Image       │  │
│  │ [Golden Image]      [Captured Image]         │  │  ← IMAGES HERE!
│  │ Click to enlarge    Click to enlarge         │  │
│  └──────────────────────────────────────────────┘  │
│                                                      │
│  ┌──────────────────────────────────────────────┐  │
│  │ ROI 6 [ocr]                   ✓ PASS        │  │
│  ├──────────────────────────────────────────────┤  │
│  │ OCR Text: PCB                                │  │
│  │ Position: [3727, 4294, 3953, 4485]           │  │
│  ├──────────────────────────────────────────────┤  │
│  │ 🌟 Golden Sample    📸 Captured Image       │  │
│  │ [Golden Image]      [Captured Image]         │  │  ← IMAGES HERE!
│  │ Click to enlarge    Click to enlarge         │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

---

## 📂 Code Location

### File: `templates/professional_index.html`

### Function: `renderROIResults(roiResults)`
**Lines:** ~1457-1610

### Image Section: **Lines ~1558-1605**

```javascript
<!-- ROI Images Section -->
${(() => {
    // Handle both old and new image path formats
    const goldenSrc = roi.golden_image_path
        ? `/api/images/${encodeURIComponent(roi.golden_image_path)}`
        : roi.golden_image || '';

    const captureSrc = roi.roi_image_path
        ? `/api/images/${encodeURIComponent(roi.roi_image_path)}`
        : (roi.capture_image_file ? `/static/captures/${roi.capture_image_file}` : '');

    if (goldenSrc || captureSrc) {
        return `
            <div class="roi-images">
                ${goldenSrc ? `
                    <div class="roi-image-container">
                        <div class="roi-image-label">🌟 Golden Sample</div>
                        <img src="${goldenSrc}" 
                             alt="Golden sample for ROI ${roi.roi_id}"
                             class="roi-image"
                             onclick="openImageModal(this.src, 'Golden Sample - ROI ${roi.roi_id}')"
                             onerror="[fallback SVG]">
                        <div class="roi-image-hint">Click to enlarge</div>
                    </div>
                ` : ''}
                ${captureSrc ? `
                    <div class="roi-image-container">
                        <div class="roi-image-label">📸 Captured Image</div>
                        <img src="${captureSrc}" 
                             alt="Captured image for ROI ${roi.roi_id}"
                             class="roi-image"
                             onclick="openImageModal(this.src, 'Captured Image - ROI ${roi.roi_id}')"
                             onerror="[fallback SVG]">
                        <div class="roi-image-hint">Click to enlarge</div>
                    </div>
                ` : ''}
            </div>
        `;
    }
    return '';
})()}
```

---

## 🎨 CSS Styling

### Classes Used:

**`.roi-images`**
- Container for both images
- Uses CSS Grid (2 columns)
- Gap: 16px between images

**`.roi-image-container`**
- Individual image wrapper
- Hover effects
- Border and shadow styling

**`.roi-image-label`**
- Text label above image
- Shows "🌟 Golden Sample" or "📸 Captured Image"

**`.roi-image`**
- The actual `<img>` element
- Max height: 200px
- Clickable (opens modal)
- Rounded corners

**`.roi-image-hint`**
- "Click to enlarge" text
- Appears on hover

---

## 🖼️ Image Sources

### Two Image Formats Supported:

#### Old Format (Schema v1.0):
```javascript
golden_image: "data:image/jpeg;base64,/9j/4AAQ..."  // Base64 embedded
capture_image_file: "group_305_1200.jpg"            // Filename only
```

#### New Format (Schema v2.0):
```javascript
golden_image_path: "sessions/uuid/output/golden_1.jpg"  // Full path
roi_image_path: "sessions/uuid/output/roi_1.jpg"        // Full path
```

### Path Construction:

```javascript
// Golden Image
goldenSrc = roi.golden_image_path
    ? `/api/images/${encodeURIComponent(roi.golden_image_path)}`  // New format
    : roi.golden_image || '';                                      // Old format

// Captured Image  
captureSrc = roi.roi_image_path
    ? `/api/images/${encodeURIComponent(roi.roi_image_path)}`     // New format
    : (roi.capture_image_file 
        ? `/static/captures/${roi.capture_image_file}`             // Old format
        : '');
```

---

## 🔍 Image Modal (Zoom Feature)

### Function: `openImageModal(src, caption)`
**Lines:** ~1620-1631

When user clicks an image:
1. Modal overlay appears (full screen)
2. Image displayed at larger size
3. Caption shows ROI info
4. Click outside or press ESC to close

```javascript
function openImageModal(src, caption) {
    const modal = document.getElementById('imageModal');
    const modalImg = document.getElementById('modalImage');
    const captionText = document.getElementById('modalCaption');

    modal.style.display = 'flex';
    modalImg.src = src;
    captionText.textContent = caption || '';
    
    document.body.style.overflow = 'hidden';  // Prevent background scroll
}
```

---

## 📱 Responsive Behavior

### Desktop (> 768px):
```
┌─────────────────────┬─────────────────────┐
│  🌟 Golden Sample   │  📸 Captured Image  │
│  [Image]            │  [Image]            │
└─────────────────────┴─────────────────────┘
```

### Mobile (< 768px):
```
┌─────────────────────┐
│  🌟 Golden Sample   │
│  [Image]            │
├─────────────────────┤
│  📸 Captured Image  │
│  [Image]            │
└─────────────────────┘
```

---

## 🎯 Display Logic

### Images Show When:
✅ ROI has `golden_image_path` OR `golden_image` (base64)  
✅ ROI has `roi_image_path` OR `capture_image_file`  

### Images Hidden When:
❌ Both image sources are empty/null  
❌ Image fails to load (shows "Image Unavailable" placeholder)

### Conditional Display:
```javascript
if (goldenSrc || captureSrc) {
    // Display image section
} else {
    return '';  // Skip image section entirely
}
```

---

## 🛠️ Error Handling

### Image Load Failure:
When an image fails to load, the `onerror` handler:
1. Replaces image with SVG placeholder
2. Shows "Image Unavailable" text
3. Adds `.image-error` class to container

```javascript
onerror="this.onerror=null; 
         this.src='data:image/svg+xml,...[SVG placeholder]...'; 
         this.parentElement.classList.add('image-error');"
```

---

## 📊 Example ROI Types with Images

### Barcode ROI:
- **Details:** Barcode value, position
- **Images:** Golden barcode + Captured barcode
- **Use Case:** Verify barcode readability

### Compare ROI:
- **Details:** Similarity %, threshold, match result
- **Images:** Golden reference + Captured comparison
- **Use Case:** Visual defect detection

### OCR ROI:
- **Details:** OCR text, position
- **Images:** Golden text + Captured text
- **Use Case:** Text verification

---

## 🔄 Data Flow

```
1. Server Response
   └─> device_summaries[1].results[]
       └─> roi_results[] with image paths

2. normalizeToV2()
   └─> Converts v1.0 to v2.0 format

3. renderDeviceResults()
   └─> Loops through devices
       └─> Calls renderROIResults()

4. renderROIResults()
   └─> Loops through ROIs
       └─> Renders ROI card
           └─> Renders image section (if images exist)
               ├─> Golden image
               └─> Captured image

5. User clicks image
   └─> openImageModal()
       └─> Shows full-size image
```

---

## 📝 Quick Reference

| Element | Location | Description |
|---------|----------|-------------|
| **ROI Card** | Lines 1475-1605 | Complete ROI item |
| **ROI Details** | Lines 1490-1556 | Text details (similarity, barcode, etc.) |
| **Image Section** | Lines 1558-1605 | Golden + Captured images |
| **Golden Image** | Lines 1572-1581 | Left image |
| **Captured Image** | Lines 1582-1591 | Right image |
| **Modal Zoom** | Lines 1620-1644 | Click-to-enlarge handler |

---

## 🎨 Visual Example

**Actual rendered output:**

```html
<div class="roi-images">
    <div class="roi-image-container">
        <div class="roi-image-label">🌟 Golden Sample</div>
        <img src="/api/images/sessions%2Fuuid%2Foutput%2Fgolden_1.jpg" 
             alt="Golden sample for ROI 1"
             class="roi-image"
             onclick="openImageModal(this.src, 'Golden Sample - ROI 1')">
        <div class="roi-image-hint">Click to enlarge</div>
    </div>
    
    <div class="roi-image-container">
        <div class="roi-image-label">📸 Captured Image</div>
        <img src="/static/captures/group_305_1200.jpg" 
             alt="Captured image for ROI 1"
             class="roi-image"
             onclick="openImageModal(this.src, 'Captured Image - ROI 1')">
        <div class="roi-image-hint">Click to enlarge</div>
    </div>
</div>
```

---

## ✅ Summary

**Location:** Inside each ROI card, at the bottom after all text details  
**Display:** Side-by-side (desktop) or stacked (mobile)  
**Interaction:** Click to open full-screen modal zoom  
**Fallback:** SVG placeholder if image fails to load  
**Format Support:** Both old (base64) and new (file paths)  

**Code File:** `templates/professional_index.html`  
**Function:** `renderROIResults(roiResults)`  
**Lines:** ~1558-1605 (Image Section)

---

**Last Updated:** October 3, 2025  
**Feature:** ROI Image Display  
**Status:** ✅ Fully Implemented
