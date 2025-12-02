# Quick Start: Testing ROI Image Display

**Target Audience:** QA Testers, Developers, Operators  
**Estimated Time:** 10-15 minutes  
**Prerequisites:** Running Visual AOI Client with server connection

## Setup

### 1. Ensure Static Directory Exists
```bash
# Create captures directory if it doesn't exist
mkdir -p /home/jason_nguyen/visual-aoi-client/static/captures

# Verify directory permissions
ls -la /home/jason_nguyen/visual-aoi-client/static/
```

### 2. Start the Client
```bash
cd /home/jason_nguyen/visual-aoi-client
./start_web_client.sh
```

### 3. Open Browser
```
Navigate to: http://localhost:5100
```

## Quick Test Scenarios

### Test 1: Golden Image Display (2 minutes)

**Objective:** Verify golden sample images display correctly

**Steps:**
1. Connect to server
2. Start inspection session
3. Run inspection on a product
4. Scroll to "Device-Separated Inspection Results"
5. Click "Show Device Details" button
6. Find an ROI card with golden image

**Expected Results:**
```
✓ 🌟 Golden Sample label appears
✓ Thumbnail image loads (base64 data)
✓ Image displays at max 200px height
✓ Hover shows lift effect + "Click to enlarge" hint
```

**Screenshot Checkpoint:**
```
┌──────────────────────────┐
│ 🌟 Golden Sample         │
│ ┌────────────────────────┐│
│ │ [Golden image visible] ││ ← Should see image
│ └────────────────────────┘│
│ Click to enlarge         │ ← Appears on hover
└──────────────────────────┘
```

---

### Test 2: Captured Image Display (2 minutes)

**Objective:** Verify captured images load from file system

**Steps:**
1. In same ROI card from Test 1
2. Look for second thumbnail (if available)
3. Check for "📸 Captured Image" label
4. Hover over thumbnail

**Expected Results:**
```
✓ 📸 Captured Image label appears
✓ Image loads from /static/captures/
✓ Image displays correctly
✓ Hover effects work
```

**Troubleshooting:**
If image shows "Image Unavailable":
```bash
# Check if file exists
ls -la /home/jason_nguyen/visual-aoi-client/static/captures/group_*.jpg

# Verify file permissions
chmod 644 /home/jason_nguyen/visual-aoi-client/static/captures/*.jpg
```

---

### Test 3: Modal Zoom (3 minutes)

**Objective:** Test full-screen image viewer

**Steps:**
1. Click on golden sample thumbnail
2. Modal should open immediately
3. Try all close methods:
   - Press Escape key
   - Click outside image
   - Click × button (top-right)

**Expected Results:**
```
✓ Modal opens with smooth animation (0.3s)
✓ Black background with blur effect
✓ Image centered and sized properly
✓ Caption shows "Golden Sample - ROI X"
✓ Close button visible (top-right)
✓ Escape key closes modal
✓ Click outside closes modal
✓ × button closes modal
✓ Body scroll locked when open
✓ Body scroll restored after close
```

**Visual Checkpoint:**
```
████████████████████████████████
██                        ✕   ██ ← Close button
██                            ██
██  ┌──────────────────────┐  ██
██  │                      │  ██
██  │  [Full-Size Image]   │  ██ ← Large centered image
██  │                      │  ██
██  └──────────────────────┘  ██
██                            ██
██  Golden Sample - ROI 1     ██ ← Caption
████████████████████████████████
```

---

### Test 4: Error Handling (2 minutes)

**Objective:** Test graceful degradation with missing images

**Method 1: Browser DevTools**
```javascript
// Open browser console (F12)
// Block image loading temporarily
// Reload inspection results
```

**Expected Results:**
```
✓ SVG placeholder appears
✓ "Image Unavailable" text visible
✓ Red border on container
✓ Container shows 60% opacity
✓ Layout doesn't break
```

**Visual Checkpoint:**
```
┌──────────────────────────┐
│ 📸 Captured Image        │ ← Red border
│ ┌────────────────────────┐│
│ │ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ ││
│ │ ▓  Image Unavailable  ▓││ ← Placeholder
│ │ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ ││
│ └────────────────────────┘│
└──────────────────────────┘
```

**Method 2: Simulate Missing File**
```bash
# Temporarily rename a capture file
mv static/captures/group_305_1200.jpg static/captures/group_305_1200.jpg.bak

# Run inspection again
# Check if placeholder appears

# Restore file
mv static/captures/group_305_1200.jpg.bak static/captures/group_305_1200.jpg
```

---

### Test 5: Responsive Design (3 minutes)

**Objective:** Verify layout adapts to different screen sizes

**Steps:**
1. Open browser DevTools (F12)
2. Enable device emulation (Ctrl+Shift+M)
3. Test these breakpoints:
   - Desktop: 1400px width
   - Tablet: 900px width
   - Mobile: 375px width

**Expected Results:**

**Desktop (>1200px):**
```
┌─────────────────────────────────┐
│ ┌───────────┐  ┌───────────┐   │ ← 2 columns
│ │ Golden    │  │ Captured  │   │
│ └───────────┘  └───────────┘   │
└─────────────────────────────────┘
```

**Tablet (768-1200px):**
```
┌───────────────────────────┐
│ ┌─────────┐  ┌─────────┐ │ ← 2 columns
│ │ Golden  │  │Captured │ │   (adjusted spacing)
│ └─────────┘  └─────────┘ │
└───────────────────────────┘
```

**Mobile (<768px):**
```
┌─────────────┐
│ ┌─────────┐ │ ← 1 column
│ │ Golden  │ │   (stacked)
│ └─────────┘ │
│ ┌─────────┐ │
│ │Captured │ │
│ └─────────┘ │
└─────────────┘
```

---

### Test 6: Multiple Devices (2 minutes)

**Objective:** Verify images work across multiple device cards

**Steps:**
1. Run inspection with 4 devices
2. Expand device details section
3. Check each device card
4. Verify images load for each device

**Expected Results:**
```
✓ Each device shows its own images
✓ Images don't duplicate across devices
✓ Modal shows correct ROI caption
✓ No performance issues with multiple images
```

---

## Performance Tests

### Load Time Test (Optional)

**Objective:** Measure image loading performance

**Steps:**
1. Open browser DevTools → Network tab
2. Run inspection
3. Observe image load times

**Expected Performance:**
```
✓ Golden images: <50ms (base64, instant)
✓ Captured images: <300ms (network request)
✓ Page doesn't freeze during load
✓ Thumbnails appear progressively
```

---

## Browser Compatibility Test

**Browsers to Test:**
- [ ] Chrome/Chromium 90+
- [ ] Firefox 88+
- [ ] Safari 14+ (if available)
- [ ] Edge 90+

**Test Matrix:**

| Feature | Chrome | Firefox | Safari | Edge |
|---------|--------|---------|--------|------|
| Thumbnails display | ✓ | ✓ | ✓ | ✓ |
| Hover effects | ✓ | ✓ | ✓ | ✓ |
| Modal opens | ✓ | ✓ | ✓ | ✓ |
| Backdrop blur | ✓ | ✓ | ✓ | ✓ |
| Escape key | ✓ | ✓ | ✓ | ✓ |
| Animations smooth | ✓ | ✓ | ✓ | ✓ |

---

## Accessibility Test (Optional)

### Keyboard Navigation
```
1. Tab to thumbnail image
2. Press Enter → Modal should open
3. Press Escape → Modal should close
4. Tab to next image
```

### Screen Reader Test
```
1. Enable screen reader (e.g., NVDA, JAWS)
2. Navigate to image
3. Verify alt text is read: "Golden sample for ROI 1"
4. Verify caption is read in modal
```

---

## Common Issues & Solutions

### Issue 1: Images Not Loading

**Symptoms:**
- All images show "Image Unavailable"
- Red borders on all containers

**Solutions:**
```bash
# Check static directory
ls -la /home/jason_nguyen/visual-aoi-client/static/captures/

# Verify web server is serving static files
curl http://localhost:5100/static/captures/group_305_1200.jpg

# Check browser console for 404 errors
# (F12 → Console tab)
```

---

### Issue 2: Modal Won't Open

**Symptoms:**
- Click on thumbnail does nothing
- No console errors

**Solutions:**
```javascript
// Open browser console (F12)
// Check if function exists
console.log(typeof openImageModal);
// Should output: "function"

// Check if modal element exists
console.log(document.getElementById('imageModal'));
// Should output: <div id="imageModal">...
```

---

### Issue 3: Blur Effect Missing

**Symptoms:**
- Modal background is solid black
- No blur behind modal

**Note:** This is expected in older browsers or when GPU acceleration is disabled. The feature gracefully degrades to solid background.

---

### Issue 4: Performance Issues

**Symptoms:**
- Page freezes when loading images
- Slow modal opening

**Solutions:**
```bash
# Reduce image sizes on server
# - Compress JPEGs to 80% quality
# - Resize golden samples to 800px max

# Check browser performance
# F12 → Performance tab → Record page load
```

---

## Test Report Template

```markdown
## ROI Image Display Test Report

**Date:** YYYY-MM-DD
**Tester:** [Your Name]
**Environment:** [Desktop/Tablet/Mobile]
**Browser:** [Chrome/Firefox/etc.] Version: XX

### Test Results

| Test | Status | Notes |
|------|--------|-------|
| Golden images display | ✓/✗ | |
| Captured images display | ✓/✗ | |
| Modal opens | ✓/✗ | |
| Modal closes (Escape) | ✓/✗ | |
| Modal closes (Click outside) | ✓/✗ | |
| Modal closes (× button) | ✓/✗ | |
| Error handling | ✓/✗ | |
| Responsive design | ✓/✗ | |
| Hover effects | ✓/✗ | |
| Animations smooth | ✓/✗ | |

### Issues Found
1. [Issue description]
2. [Issue description]

### Performance
- Page load: XXms
- Modal open: XXms
- Image load: XXms

### Recommendations
- [Improvement suggestion]
```

---

## Quick Checklist

**Before Testing:**
- [ ] Server is running
- [ ] Client is running
- [ ] Browser is updated
- [ ] Static directory exists

**During Testing:**
- [ ] Golden images display
- [ ] Captured images display
- [ ] Modal opens/closes
- [ ] All close methods work
- [ ] Error states work
- [ ] Responsive design works

**After Testing:**
- [ ] Document issues found
- [ ] Take screenshots if needed
- [ ] Test in multiple browsers
- [ ] Fill out test report

---

## Need Help?

**Documentation:**
- Full feature guide: `docs/ROI_IMAGE_DISPLAY_FEATURE.md`
- Visual guide: `docs/VISUAL_GUIDE_ROI_IMAGES.md`
- Implementation summary: `docs/ROI_IMAGE_IMPLEMENTATION_SUMMARY.md`

**Console Debug Commands:**
```javascript
// Check if modal exists
document.getElementById('imageModal')

// Check if function exists
typeof openImageModal

// Manually open modal (test)
openImageModal('data:image/svg+xml,...', 'Test Caption')

// Manually close modal (test)
closeImageModal()
```

---

**Testing Time:** ~15 minutes for complete test suite  
**Status:** ✅ Ready for testing  
**Last Updated:** October 3, 2025
