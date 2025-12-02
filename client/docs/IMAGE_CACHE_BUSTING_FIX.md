# Image Cache-Busting Fix - Prevent Browser Caching of Inspection Results

**Date:** October 8, 2025  
**Priority:** 🔴 **CRITICAL** - Display Accuracy  
**Status:** ✅ Implemented

## Problem Statement

The web UI was displaying **old/cached inspection result images** instead of the freshly captured images, even though the camera was capturing new frames correctly.

### User Report

> "The new captured image is used for processing but the web page still shows the old result image, is it cached?"

### Root Cause

**Browser Image Caching:**

- Inspection results reuse the same filenames (e.g., `roi_1.jpg`, `roi_2.jpg`)
- Browser sees same URL and uses cached version
- No cache-busting mechanism to force reload
- Server not sending no-cache headers

**Example Scenario:**

```
Inspection 1: /shared/sessions/abc123/output/roi_1.jpg (PCB with defect)
  → Browser loads and caches image

Inspection 2: /shared/sessions/abc123/output/roi_1.jpg (PCB without defect)
  → Same URL! Browser shows CACHED image from Inspection 1 ❌
  → User sees OLD defect, even though NEW image has no defect
```

### Impact

**CRITICAL for Inspection Accuracy:**

- ❌ Operators see wrong inspection results
- ❌ Confusion between pass/fail decisions
- ❌ Cannot trust displayed images
- ❌ May make incorrect production decisions

**This defeats the entire purpose of the visual inspection system.**

## Solution Implemented

### Two-Layer Defense Against Caching

**Layer 1: Client-Side Cache-Busting (URL Parameters)**
**Layer 2: Server-Side No-Cache Headers**

### Layer 1: URL Cache-Busting Parameters

**File:** `templates/professional_index.html`

Add timestamp query parameter to every image URL:

```javascript
// BEFORE (Cached):
captureSrc = '/shared/sessions/abc123/output/roi_1.jpg';

// AFTER (Fresh):
captureSrc = '/shared/sessions/abc123/output/roi_1.jpg?t=1728381234567';
```

**How It Works:**

- `Date.now()` returns current timestamp in milliseconds
- Each inspection gets unique timestamp
- Browser sees different URL → bypasses cache → loads fresh image

**Implementation:**

```javascript
// For captured images
if (roi.roi_image_path) {
    const relativePath = roi.roi_image_path.replace('/mnt/visual-aoi-shared/', '/shared/');
    // CRITICAL: Add cache-busting timestamp to force browser to load NEW image
    captureSrc = `${relativePath}?t=${Date.now()}`;
}

// For golden images
if (roi.golden_image_path) {
    const relativePath = roi.golden_image_path.replace('/mnt/visual-aoi-shared/', '/shared/');
    // Add cache-busting timestamp to ensure fresh images are loaded
    goldenSrc = `${relativePath}?t=${Date.now()}`;
}

// For fallback paths
captureSrc = `/shared/sessions/${appState.sessionId}/output/roi_${roi.roi_id}.jpg?t=${Date.now()}`;
```

**All Image Paths Fixed:**

1. ✅ `roi.roi_image_path` (primary captured image path)
2. ✅ `roi.golden_image_path` (golden sample reference)
3. ✅ `roi.capture_image_file` (legacy format)
4. ✅ Fallback constructed paths

### Layer 2: Server No-Cache Headers

**File:** `app.py`

**Route:** `/shared/<path:filename>`

Add HTTP headers to prevent any caching:

```python
@app.route("/shared/<path:filename>")
def serve_shared_file(filename):
    """Serve files from the shared folder with no-cache headers to ensure fresh images."""
    
    # ... existing path validation and file serving ...
    
    response = send_from_directory(directory, file_name)
    
    # CRITICAL: Send response with no-cache headers to prevent browser caching
    # This ensures inspection result images are always fresh
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response
```

**HTTP Headers Explained:**

1. **`Cache-Control: no-cache, no-store, must-revalidate`**
   - `no-cache`: Must revalidate with server before using cached version
   - `no-store`: Don't store in cache at all
   - `must-revalidate`: Can't use stale data

2. **`Pragma: no-cache`**
   - HTTP/1.0 backward compatibility
   - Ensures older browsers also don't cache

3. **`Expires: 0`**
   - Tells browser resource is already expired
   - Forces immediate reload

## How Cache-Busting Works

### URL Parameter Method

**Concept:**

- Browsers cache by full URL including query parameters
- Different parameter → different URL → new cache entry

**Example Flow:**

```
Time: 10:30:00 AM
  URL: /shared/sessions/abc/output/roi_1.jpg?t=1728381000000
  Status: Browser loads from server (not in cache)
  Result: Displays Image A ✓

Time: 10:30:05 AM (5 seconds later, new inspection)
  URL: /shared/sessions/abc/output/roi_1.jpg?t=1728381005000
  Status: Different URL! Browser loads from server
  Result: Displays Image B ✓

Time: 10:30:10 AM (Another inspection)
  URL: /shared/sessions/abc/output/roi_1.jpg?t=1728381010000
  Status: Different URL! Browser loads from server
  Result: Displays Image C ✓
```

**Key Insight:** Even though filename is same (`roi_1.jpg`), the `?t=` parameter makes each URL unique.

### HTTP Headers Method

**Concept:**

- Server tells browser "Don't cache this resource"
- Browser respects headers and always requests from server

**Header Decision Tree:**

```
Browser receives image with headers:
  Cache-Control: no-store
    ↓
  Should I cache this? → NO ❌
    ↓
  Next request for same URL → Always fetch from server ✓

Browser receives image without headers:
  (no cache headers)
    ↓
  Should I cache this? → YES ✓ (default behavior)
    ↓
  Next request for same URL → Use cached version ❌ STALE DATA
```

## Verification Methods

### Test 1: Inspect Network Traffic

Open browser DevTools → Network tab:

```
✅ CORRECT (Fresh Image):
Request: /shared/sessions/abc/output/roi_1.jpg?t=1728381234567
Status: 200 OK
Size: 456 KB (from server)
Cache-Control: no-cache, no-store, must-revalidate

✅ Next Inspection (Different Timestamp):
Request: /shared/sessions/abc/output/roi_1.jpg?t=1728381239876
Status: 200 OK
Size: 456 KB (from server)
Cache-Control: no-cache, no-store, must-revalidate

❌ WRONG (Cached - shouldn't happen now):
Request: /shared/sessions/abc/output/roi_1.jpg
Status: 200 OK (from cache)
Size: 456 KB (memory cache or disk cache)
```

**Look For:**

1. ✅ Every request has `?t=` parameter with unique timestamp
2. ✅ Status shows "200 OK" not "304 Not Modified"
3. ✅ Response headers show `Cache-Control: no-cache, no-store`
4. ✅ Size shows actual bytes, not "(from cache)"

### Test 2: Visual Inspection

Perform sequential inspections with different PCBs:

```
Step 1: Inspect PCB-A (with defect)
  → Take screenshot of displayed result
  → Note the defect is visible

Step 2: Inspect PCB-B (without defect)
  → Check if display updates immediately
  → Compare with screenshot from Step 1
  → Should show DIFFERENT image ✓

Step 3: Inspect PCB-A again
  → Should show same as Step 1 (cached is OK if file unchanged)
```

### Test 3: Console Logging

Check browser console for image URLs:

```javascript
console.log('Capture image URL:', captureSrc);
// Output should show: /shared/sessions/abc/output/roi_1.jpg?t=1728381234567

// Each inspection should show DIFFERENT timestamp:
// Inspection 1: ?t=1728381234567
// Inspection 2: ?t=1728381239123
// Inspection 3: ?t=1728381243789
```

### Test 4: Hard Refresh Test

```
Step 1: Complete inspection → Note displayed images
Step 2: Press Ctrl+F5 (hard refresh)
Step 3: Images should remain the same (cache cleared but same files)
Step 4: Run new inspection
Step 5: Images should update to NEW capture ✓
```

## Technical Details

### When Timestamps Are Generated

**Critical:** New timestamp for **each inspection result display**:

```javascript
// In createResultsSummary() function
// Called when inspection completes and results arrive

roi_results.forEach(roi => {
    // Generate fresh timestamp for THIS inspection
    const timestamp = Date.now();
    
    // Apply to captured image
    captureSrc = `${roi.roi_image_path}?t=${timestamp}`;
    
    // Apply to golden image
    goldenSrc = `${roi.golden_image_path}?t=${timestamp}`;
});
```

**Result:** Each inspection gets unique timestamps, forcing fresh image loads.

### Why Not Use Server Timestamp?

**Option A: Client-Side `Date.now()` (✅ Chosen)**

Pros:

- Simple implementation
- No server changes needed
- Works even if server doesn't send timestamp
- Guaranteed unique per inspection

Cons:

- Slight time drift if client clock wrong (not critical)

**Option B: Server Timestamp in Response**

Pros:

- Timestamp from authoritative source
- Matches actual file modification time

Cons:

- Requires server API changes
- More complex implementation
- Still need fallback for missing timestamp

**Decision:** Use `Date.now()` because it's simpler, works immediately, and is sufficient for cache-busting.

### Performance Impact

**Cache-Busting URL Parameters:**

- Performance: No measurable impact
- Memory: ~20 bytes per URL (timestamp string)
- Network: Same - still downloading images

**No-Cache Headers:**

- Performance: Minimal (~1ms header processing)
- Network: Forces server request each time
- Memory: No caching saves memory

**Trade-off:**

- ⚠️ Slightly more network requests (no cache reuse)
- ✅ But ensures accuracy (critical requirement)
- ✅ Images are ~500KB, network speed ~100MB/s → <10ms
- ✅ **Accuracy more important than speed**

### Browser Compatibility

**Cache-Busting URLs:**

- ✅ All browsers (Chrome, Firefox, Edge, Safari)
- ✅ All versions (universal support)
- ✅ Mobile browsers

**HTTP Cache Headers:**

- ✅ HTTP/1.1: `Cache-Control`
- ✅ HTTP/1.0: `Pragma` (fallback)
- ✅ All modern browsers
- ✅ CDNs and proxies

## Related Systems

### Camera Capture Freshness

**Separate but Related:**

- Camera capture freshness: `docs/ENSURE_FRESH_IMAGE_CAPTURE.md`
- This document: Display/browser freshness

**Full Pipeline:**

```
1. Camera Capture (TIS.py)
   └─ snap_image() → Clears old img_mat
   └─ Frame counter increments
   └─ Returns NEW image ✓

2. Server Processing
   └─ Receives fresh image from camera
   └─ Performs inspection
   └─ Saves result images to disk

3. Browser Display (This Fix)
   └─ Adds ?t= timestamp to URLs
   └─ Server sends no-cache headers
   └─ Browser loads fresh images ✓

4. User Sees Current Results ✓
```

**Both layers needed for complete freshness guarantee:**

- ✅ Camera layer ensures fresh capture
- ✅ Display layer ensures fresh display

## Testing Procedure

### Test 1: Sequential Inspections

```bash
# Terminal 1: Run client
cd /home/jason_nguyen/visual-aoi-client
python3 app.py

# Browser: Open DevTools (F12) → Network tab

# Perform inspections:
1. Capture image → Run inspection
   → Check Network tab for image URL
   → Should have ?t=XXXXX parameter
   → Response headers should show Cache-Control: no-cache

2. Capture another image → Run inspection
   → Check Network tab
   → Should have DIFFERENT ?t=YYYYY parameter
   → Should load from server (200 OK, not from cache)

3. Verify displayed images changed
```

### Test 2: Cache Verification

```javascript
// In browser console after inspection:

// Check all image elements
document.querySelectorAll('.roi-image').forEach(img => {
    console.log('Image src:', img.src);
    // Should show ?t= parameter in URL
});

// Should output:
// Image src: http://localhost:5100/shared/sessions/abc/output/roi_1.jpg?t=1728381234567
// Image src: http://localhost:5100/shared/sessions/abc/output/roi_2.jpg?t=1728381234568
```

### Test 3: Response Headers Check

```bash
# Use curl to check response headers
curl -I http://localhost:5100/shared/sessions/abc123/output/roi_1.jpg

# Should show:
# HTTP/1.1 200 OK
# Cache-Control: no-cache, no-store, must-revalidate
# Pragma: no-cache
# Expires: 0
```

## Edge Cases Handled

### 1. Base64 Encoded Images

**Scenario:** Server sends base64 data instead of file paths

**Handling:**

```javascript
if (roi.roi_image && roi.roi_image.startsWith('data:image')) {
    // Base64 data - no caching issue (data is embedded)
    captureSrc = roi.roi_image;  // No timestamp needed
}
```

**Why:** Base64 data is embedded in HTML, not a separate HTTP request. No caching possible.

### 2. Legacy Image Formats

**Scenario:** Old code uses `capture_image_file` field

**Handling:**

```javascript
else if (roi.capture_image_file) {
    // Legacy format - also add cache-busting
    captureSrc = `/static/captures/${roi.capture_image_file}?t=${Date.now()}`;
}
```

**Result:** Even legacy paths get cache-busting.

### 3. Fallback Constructed Paths

**Scenario:** Server doesn't provide image path

**Handling:**

```javascript
else if (appState.sessionId && roi.roi_id) {
    // Construct path and add cache-busting
    captureSrc = `/shared/sessions/${appState.sessionId}/output/roi_${roi.roi_id}.jpg?t=${Date.now()}`;
}
```

**Result:** Fallback paths also protected.

### 4. Modal Image Zoom

**Scenario:** User clicks image to zoom in modal

**Handling:**

```javascript
onclick="openImageModal(this.src, 'Captured Image - ROI ${roi.roi_id}')"
```

- Modal receives same URL with `?t=` parameter
- Same fresh image displayed in modal
- No separate caching issue

### 5. Multiple ROIs Same Time

**Scenario:** Inspection has 4 ROIs inspected simultaneously

**Handling:**

```javascript
// Each ROI gets same timestamp (inspected at same time)
roi_results.forEach(roi => {
    const timestamp = Date.now();  // Same for all ROIs in this inspection
    captureSrc = `${roi.roi_image_path}?t=${timestamp}`;
});
```

**Result:** All ROI images from same inspection get same timestamp (correct - they were captured at same moment).

## Common Issues and Solutions

### Issue 1: Still Seeing Cached Images

**Symptoms:**

- Image URLs have `?t=` parameter
- But still showing old images

**Diagnosis:**

```javascript
// Check if timestamp is actually changing between inspections
console.log('Current timestamp:', Date.now());
// Run inspection 1: Note the timestamp
// Run inspection 2: Compare timestamps - should be different
```

**Possible Causes:**

1. Browser aggressive caching (Chrome dev mode?)
2. Proxy/CDN caching (corporate network?)
3. Service worker caching (PWA?)

**Solutions:**

1. Hard refresh (Ctrl+F5)
2. Disable cache in DevTools (Network tab → Disable cache)
3. Check service workers: DevTools → Application → Service Workers
4. Clear browser cache completely

### Issue 2: No-Cache Headers Not Sent

**Symptoms:**

- Response headers don't show `Cache-Control`

**Diagnosis:**

```bash
curl -I http://localhost:5100/shared/sessions/abc/output/roi_1.jpg
# Should show Cache-Control header
```

**Possible Causes:**

1. Flask not applying headers
2. Reverse proxy stripping headers
3. Different route serving images

**Solutions:**

1. Check Flask route: `@app.route("/shared/<path:filename>")`
2. Verify `send_from_directory` returns response object
3. Check for reverse proxy (nginx, Apache) cache settings

### Issue 3: Timestamp Too Similar

**Symptoms:**

- Multiple requests getting same timestamp

**Diagnosis:**

```javascript
// Check if Date.now() changes fast enough
for (let i = 0; i < 5; i++) {
    console.log(Date.now());
}
// Should show different values (millisecond precision)
```

**Solution:** This shouldn't happen (Date.now() has millisecond precision), but if it does, add a counter:

```javascript
let timestampCounter = 0;
captureSrc = `${relativePath}?t=${Date.now()}_${timestampCounter++}`;
```

## Migration Notes

### For Existing Code

**Changes are backward compatible:**

- ✅ Old image paths still work (server still serves them)
- ✅ Just adds `?t=` parameter (server ignores it)
- ✅ No database changes needed
- ✅ No API changes needed

### For Testing

**Update test assertions:**

```python
# OLD:
assert image_url == "/shared/sessions/abc/output/roi_1.jpg"

# NEW:
assert image_url.startswith("/shared/sessions/abc/output/roi_1.jpg?t=")
assert "?t=" in image_url
```

## Summary

### Problem

❌ Browser cached inspection result images  
❌ Displayed old images instead of fresh captures  
❌ Operator confusion and incorrect decisions  

### Solution

✅ Added `?t=Date.now()` timestamp to all image URLs  
✅ Added `Cache-Control: no-cache, no-store` headers  
✅ Added `Pragma: no-cache` for HTTP/1.0 compatibility  
✅ Added `Expires: 0` for additional cache prevention  

### Result

🎯 **Every inspection displays fresh images**  
🔍 **Verifiable via Network tab (unique URLs)**  
🛡️ **Two-layer defense (URL + headers)**  
📊 **No performance impact (<10ms per image)**  

### Files Modified

1. `templates/professional_index.html` - Added cache-busting to image URLs
2. `app.py` - Added no-cache headers to `/shared/` route

### Related Documentation

- Camera capture freshness: `docs/ENSURE_FRESH_IMAGE_CAPTURE.md`
- Image path architecture: `docs/IMAGE_PATH_INSPECTION.md` (if exists)

This fix ensures operators always see **current, accurate inspection results**, which is critical for production quality control decisions.
