# Visual Guide: ROI Image Display Feature

## Quick Overview

This guide shows the visual structure and interaction flow of the new ROI image display feature.

## Component Structure

### 1. ROI Card with Images

```
┌─────────────────────────────────────────────────────────────┐
│ ROI 1 [BARCODE]                            ✓ PASS          │ ← Header
├─────────────────────────────────────────────────────────────┤
│ AI Similarity: 88.19%  ██████████████████░░                │
│ Barcode: 20003548-0000003-1019720-101                      │ ← Details
│ Position: [3459, 2959, 4058, 3318]                         │
├─────────────────────────────────────────────────────────────┤
│ ┌──────────────────────────┐  ┌──────────────────────────┐ │
│ │ 🌟 Golden Sample         │  │ 📸 Captured Image        │ │ ← Labels
│ │ ┌────────────────────────┐│  │┌────────────────────────┐│ │
│ │ │                        ││  ││                        ││ │
│ │ │   [Golden Image]       ││  ││   [Captured Image]     ││ │ ← Images
│ │ │    200px max height    ││  ││    200px max height    ││ │
│ │ │                        ││  ││                        ││ │
│ │ └────────────────────────┘│  │└────────────────────────┘│ │
│ │ Click to enlarge         │  │ Click to enlarge         │ │ ← Hint (on hover)
│ └──────────────────────────┘  └──────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 2. Hover State

```
┌──────────────────────────┐
│ 🌟 Golden Sample         │
│ ┌────────────────────────┐│
│ │                        ││  ← Lifted -2px
│ │   [Golden Image]       ││  ← Opacity 85%
│ │   (slightly dimmed)    ││  ← Cursor: pointer
│ │                        ││
│ └────────────────────────┘│
│ Click to enlarge ←────────┤  ← Hint appears (opacity 1)
└──────────────────────────┘
```

### 3. Error State

```
┌──────────────────────────┐
│ 📸 Captured Image        │
│ ┌────────────────────────┐│  ← Red border (#FF3B30)
│ │ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ ││
│ │ ▓▓▓ Image Unavailable ▓││  ← SVG placeholder
│ │ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ ││  ← 60% opacity
│ │                        ││
│ └────────────────────────┘│
│ Click to enlarge         │
└──────────────────────────┘
```

### 4. Full-Screen Modal

```
████████████████████████████████████████████████████████████████
██                                                        ✕ ██  ← Close button
██                                                          ██     (48px, top-right)
██                                                          ██
██                                                          ██
██              ┌──────────────────────────┐                ██
██              │                          │                ██
██              │                          │                ██
██              │    Full-Size Image       │                ██  ← Image
██              │    (up to 90vw × 80vh)   │                ██     (max 90% viewport)
██              │    object-fit: contain   │                ██
██              │                          │                ██
██              │                          │                ██
██              └──────────────────────────┘                ██
██                                                          ██
██          Golden Sample - ROI 1 ←─────────────────────   ██  ← Caption
██          (white text on glass background)               ██
██                                                          ██
████████████████████████████████████████████████████████████████
        Black background (95% opacity)
        Backdrop blur (10px)
        Click anywhere to close
```

## Interaction Flow

### User Journey

```
Step 1: View ROI Card
┌─────────────────────┐
│ ROI 1 Details       │
│ [Golden] [Captured] │ ← User sees thumbnails
└─────────────────────┘
        ↓

Step 2: Hover Thumbnail
┌─────────────────────┐
│ ROI 1 Details       │
│ [Golden] [Captured] │ ← Lift effect + hint appears
│    ↑                │
│  "Click to enlarge" │
└─────────────────────┘
        ↓

Step 3: Click Thumbnail
[USER CLICKS]
        ↓
Step 4: Modal Opens
████████████████████
██               ✕ ██
██  [Full Image]   ██ ← Smooth fade-in (0.3s)
██  Caption        ██ ← Zoom-in effect (0.3s)
████████████████████
        ↓

Step 5: View Full Image
User can:
- View details
- Read caption
- Decide to close
        ↓

Step 6: Close Modal
Options:
1. Click outside image
2. Press Escape key
3. Click ✕ button
        ↓

Step 7: Return to ROI List
┌─────────────────────┐
│ ROI 1 Details       │
│ [Golden] [Captured] │ ← Back to normal view
└─────────────────────┘
```

## Responsive Behavior

### Desktop (>1200px)

```
┌─────────────────────────────────────────┐
│ ROI Card                                │
│ ┌──────────────┐  ┌──────────────┐     │
│ │ Golden       │  │ Captured     │     │  2 columns
│ │ [image]      │  │ [image]      │     │  Full width
│ └──────────────┘  └──────────────┘     │  All hover effects
└─────────────────────────────────────────┘
```

### Tablet (768-1200px)

```
┌───────────────────────────────────┐
│ ROI Card                          │
│ ┌────────────┐  ┌────────────┐   │
│ │ Golden     │  │ Captured   │   │  2 columns
│ │ [image]    │  │ [image]    │   │  Adjusted spacing
│ └────────────┘  └────────────┘   │  Simplified effects
└───────────────────────────────────┘
```

### Mobile (<768px)

```
┌─────────────────┐
│ ROI Card        │
│ ┌─────────────┐ │
│ │ Golden      │ │  1 column
│ │ [image]     │ │  Stacked
│ └─────────────┘ │  Full width
│ ┌─────────────┐ │
│ │ Captured    │ │
│ │ [image]     │ │
│ └─────────────┘ │
└─────────────────┘
```

## Animation Timeline

### Modal Open Sequence

```
Time: 0ms
┌─────────────┐
│ ROI Card    │
│ [Click]     │ ← User clicks thumbnail
└─────────────┘

Time: 0-50ms
[Processing]
- Get image src
- Get caption text
- Set modal display: flex
- Lock body scroll

Time: 50-350ms
████████████████
██             ██
██  [Image]    ██ ← Fade in (opacity 0 → 1)
██  [Caption]  ██ ← Zoom in (scale 0.8 → 1.0)
████████████████

Time: 350ms
████████████████
██           ✕ ██
██  [Image]    ██ ← Fully visible
██  Caption    ██ ← Fully scaled
████████████████
```

### Modal Close Sequence

```
Time: 0ms
████████████████
██           ✕ ██
██  [Image]    ██ ← Modal visible
██  Caption    ██
████████████████
      ↓ [User presses Escape]

Time: 0-50ms
[Processing]
- Set modal display: none
- Unlock body scroll

Time: 50ms
┌─────────────┐
│ ROI Card    │
│ [Images]    │ ← Back to normal
└─────────────┘
```

## CSS Class Hierarchy

```
.roi-images                    ← Grid container
├── .roi-image-container       ← Image wrapper
│   ├── .roi-image-label       ← Label text (🌟/📸)
│   ├── .roi-image             ← Thumbnail image
│   └── .roi-image-hint        ← "Click to enlarge"
│
├── .roi-image-container.image-error  ← Error state
│   └── [Same children, red border]
│
└── [Repeat for second image]

.image-modal                   ← Full-screen overlay
├── .image-modal-close         ← ✕ button
└── .image-modal-content-wrapper
    ├── .image-modal-content   ← Full-size image
    └── .image-modal-caption   ← Description text
```

## Data Flow Diagram

```
Server Response
      ↓
{
  "roi_id": 1,
  "golden_image": "data:image/jpeg;base64,...",
  "capture_image_file": "group_305_1200.jpg"
}
      ↓
renderROIResults()
      ↓
Check: golden_image OR capture_image_file exists?
      ↓
     YES                          NO
      ↓                           ↓
Create .roi-images section    Skip image section
      ↓
Generate HTML:
- .roi-image-container (golden)
- .roi-image-container (captured)
      ↓
Add to DOM
      ↓
Browser loads images
      ↓
    SUCCESS              ERROR
      ↓                    ↓
Display thumbnail    Show placeholder SVG
      ↓                    ↓
User clicks          User clicks
      ↓                    ↓
openImageModal()     openImageModal()
      ↓                    ↓
Show full image      Show placeholder (large)
```

## Color Coding

### Status Colors

```
✓ PASS    → Green  (#34C759)  ████████
✗ FAIL    → Red    (#FF3B30)  ████████
⚠ Warning → Orange (#FF9500)  ████████
ℹ Info    → Blue   (#007AFF)  ████████
```

### Image States

```
Normal:    Gray border   (#E0E0E0)  ───────
Hover:     Gray border   (#E0E0E0)  ▔▔▔▔▔▔▔ (lifted)
Error:     Red border    (#FF3B30)  ═══════ (60% opacity)
```

### Modal Colors

```
Background:  Black 95%      ████████ (blurred)
Close button: White         ○
Close hover:  Red           ○
Caption bg:   White 10%     ▒▒▒▒▒▒▒▒
```

## File Structure

```
visual-aoi-client/
├── templates/
│   └── professional_index.html
│       ├── renderROIResults() function    ← Modified
│       ├── openImageModal() function      ← Added
│       ├── closeImageModal() function     ← Added
│       └── <div id="imageModal">          ← Added
│
├── static/
│   ├── professional.css
│   │   ├── .roi-images                    ← Added
│   │   ├── .roi-image-container           ← Added
│   │   ├── .roi-image                     ← Added
│   │   ├── .image-modal                   ← Added
│   │   └── @keyframes fadeIn/zoomIn       ← Added
│   │
│   └── captures/
│       └── [captured image files]         ← Served from here
│
└── docs/
    ├── ROI_IMAGE_DISPLAY_FEATURE.md       ← New (detailed)
    ├── ROI_IMAGE_IMPLEMENTATION_SUMMARY.md ← New (summary)
    ├── VISUAL_GUIDE_ROI_IMAGES.md         ← This file
    └── DEVICE_SEPARATED_UI_IMPLEMENTATION.md ← Updated
```

## Quick Reference

### HTML Structure
```html
<div class="roi-images">
    <div class="roi-image-container">
        <div class="roi-image-label">🌟 Golden Sample</div>
        <img src="..." class="roi-image" onclick="openImageModal(...)">
        <div class="roi-image-hint">Click to enlarge</div>
    </div>
</div>
```

### JavaScript Usage
```javascript
// Open modal
openImageModal('data:image/jpeg;base64,...', 'Golden Sample - ROI 1');

// Close modal
closeImageModal();

// Auto-close on Escape
document.addEventListener('keydown', event => {
    if (event.key === 'Escape') closeImageModal();
});
```

### CSS Key Properties
```css
.roi-images {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
}

.roi-image {
    max-height: 200px;
    cursor: pointer;
}

.image-modal {
    position: fixed;
    z-index: 10000;
    background: rgba(0, 0, 0, 0.95);
    backdrop-filter: blur(10px);
}
```

## Testing Checklist (Visual)

```
□ Thumbnails display at correct size (max 200px)
□ Images maintain aspect ratio
□ Grid layout works (2 cols desktop, 1 col mobile)
□ Hover effects smooth (lift + opacity)
□ Hint text appears on hover
□ Click opens modal immediately
□ Modal animates in smoothly (0.3s)
□ Full image centered and sized correctly
□ Caption displays below image
□ Close button visible (top-right)
□ Click outside closes modal
□ Escape key closes modal
□ × button closes modal
□ Error images show red border + placeholder
□ No layout shift when images load
□ Body scroll locked when modal open
□ Body scroll restored on close
```

---

**Created:** October 3, 2025  
**Purpose:** Quick visual reference for ROI image display feature  
**Audience:** Developers, designers, testers, operators  
**Status:** ✅ Implementation complete, ready for testing
