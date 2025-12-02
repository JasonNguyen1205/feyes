# Chromium Optimizations - Quick Testing Guide

## 🚀 Quick Start

### 1. Restart the Web Client
```bash
cd /home/pi/visual-aoi-client
./start_web_client.sh
```

### 2. Open in Chromium Browser
```bash
chromium-browser http://localhost:5100
```

### 3. Open DevTools
Press `F12` or `Ctrl+Shift+I`

---

## ✅ Visual Checks (30 seconds)

### Check 1: Glass Effects (Backdrop Blur)
1. Look at the top navigation bar
2. It should have a **frosted glass** appearance with blur
3. Scroll the page - the blur should stay smooth

**Expected:** ✅ Blurred background behind header  
**Fallback:** ⚠️ Solid background if backdrop-filter not supported

---

### Check 2: Smooth Scrolling
1. Scroll down the page rapidly
2. Should feel **buttery smooth** at 60fps
3. No stuttering or lag

**Expected:** ✅ Instant response, no jank  
**Bad:** ❌ Stuttering or delayed scroll

---

### Check 3: Image Lazy Loading
1. Open DevTools → **Network** tab
2. Reload the page
3. Scroll down slowly
4. Watch images load **only when they come into view**

**Expected:** ✅ Images load progressively as you scroll  
**Bad:** ❌ All images load at once

---

### Check 4: Animations
1. Hover over any **button**
2. Should have smooth transitions
3. Click a device card - should expand smoothly

**Expected:** ✅ 60fps animations, no flicker  
**Bad:** ❌ Choppy or laggy animations

---

## 🔍 Performance Tests (2 minutes)

### Test 1: Page Load Speed
1. Open DevTools → **Performance** tab
2. Click the **Record** button (circle)
3. Reload the page (`Ctrl+R`)
4. Stop recording after page loads

**What to check:**
- FCP (First Contentful Paint): Should be < 1.8s
- LCP (Largest Contentful Paint): Should be < 2.5s
- Look for **green bars** (GPU-accelerated)
- Avoid **red bars** (main thread blocking)

**Expected:**  
✅ Mostly green bars in timeline  
✅ No long tasks (> 50ms)  
✅ Smooth FPS line at 60

---

### Test 2: Memory Usage
1. Open DevTools → **Memory** tab
2. Select "**Heap snapshot**"
3. Click "**Take snapshot**"
4. Perform some actions (click buttons, scroll, open modals)
5. Take another snapshot
6. Compare the two snapshots

**What to check:**
- Total heap size should be < 150MB
- No significant growth between snapshots (< 10MB)

**Expected:**  
✅ Stable memory usage  
✅ No memory leaks

**Check console for automatic monitoring:**
```
💾 Memory: 45.23MB / 128.00MB
```

---

### Test 3: Scroll Performance
1. Open DevTools → **Rendering** tab
2. Enable "**FPS meter**"
3. Scroll the page up and down rapidly
4. Watch the FPS counter

**Expected:**  
✅ Solid 60 FPS during scroll  
✅ Green line (good)  
❌ Red spikes or drops below 30fps (bad)

---

## 🌐 Network Tests (1 minute)

### Test 1: Service Worker Registration
1. Open DevTools → **Application** tab
2. Click "**Service Workers**" in left sidebar
3. Look for `sw.js` with status "**activated and running**"

**Expected:**  
✅ Service worker registered  
✅ Status: "activated and is running"  
✅ Can click "Update" to refresh

---

### Test 2: Cache Storage
1. Still in **Application** tab
2. Click "**Cache Storage**" in left sidebar
3. Expand the `visual-aoi-v1.0.0` cache
4. Should see cached files:
   - `/`
   - `/static/professional.css`
   - `/static/chromium-optimizations.css`
   - `/static/script.js`

**Expected:**  
✅ Files are cached  
✅ Can click to preview them

---

### Test 3: Offline Mode
1. In **Application** tab → Service Workers
2. Check "**Offline**" checkbox
3. Reload the page
4. Page should still load (from cache)
5. Uncheck "Offline" to go back online

**Expected:**  
✅ Page loads offline (static assets)  
⚠️ API calls will fail (expected)

---

## 📊 Console Checks (10 seconds)

Open the **Console** tab and look for these messages:

### On Page Load:
```
✅ Running on Chromium - optimizations active
⚡ Performance Metrics:
   Page Load: 1234ms
   DOM Ready: 567ms
   Render: 345ms
💾 Memory: 45.23MB / 128.00MB
```

### Service Worker (if enabled):
```
[Service Worker] Installing...
[Service Worker] Caching static assets
[Service Worker] Installed successfully
[Service Worker] Activating...
[Service Worker] Activated successfully
```

---

## 🐛 Troubleshooting

### Issue: No glass effects visible
**Cause:** Backdrop-filter not supported or GPU disabled  
**Fix:**
1. Check Chromium version (need 76+)
2. Enable GPU: `chrome://gpu` → Check for errors
3. Try: `chromium-browser --enable-features=BackdropFilter`

---

### Issue: Service worker not registering
**Cause:** HTTPS required or disabled  
**Fix:**
1. Localhost should work without HTTPS
2. Check console for errors
3. Try clearing cache: DevTools → Application → Clear storage

---

### Issue: Images not lazy loading
**Cause:** loading="lazy" not supported (old Chromium)  
**Fix:**
1. Check Chromium version (need 77+)
2. Update browser: `sudo apt update && sudo apt upgrade chromium-browser`
3. Fallback: IntersectionObserver will still work

---

### Issue: Poor performance on Raspberry Pi
**Cause:** Limited GPU/memory  
**Fix:**
1. Close other applications
2. Check memory: DevTools → Memory tab
3. Reduce quality:
   - Manually add `slow-connection` class to `<html>`
   - This disables heavy effects

---

## 🎯 Performance Targets

| Metric | Target | How to Check |
|--------|--------|--------------|
| **Page Load** | < 2s | DevTools → Network → DOMContentLoaded |
| **First Paint** | < 1.8s | DevTools → Performance → FCP marker |
| **Scroll FPS** | 60fps | DevTools → Rendering → FPS meter |
| **Memory** | < 150MB | Console log or DevTools → Memory |
| **Cache Hit** | > 80% | DevTools → Network → "from ServiceWorker" |

---

## 📝 Quick Test Checklist

Print this and check off as you test:

- [ ] Page loads in Chromium without errors
- [ ] Glass effects visible on header/modals
- [ ] Scrolling is smooth (60fps)
- [ ] Images lazy load as you scroll
- [ ] Buttons have smooth hover animations
- [ ] Console shows "✅ Running on Chromium"
- [ ] Console shows performance metrics
- [ ] Console shows memory usage
- [ ] Service worker registered (Application tab)
- [ ] Static assets cached (Cache Storage)
- [ ] Page works offline (basic functionality)
- [ ] FPS meter shows 60fps during scroll
- [ ] No memory leaks (stable heap size)
- [ ] No console errors or warnings

---

## 🚨 Red Flags (Report These!)

❌ **Console errors** - Should be clean  
❌ **FPS drops below 30** - Performance issue  
❌ **Memory > 200MB** - Memory leak  
❌ **Page doesn't load offline** - Service worker issue  
❌ **Images all load at once** - Lazy loading broken  
❌ **Scroll stutters** - Missing optimizations  

---

## 📊 Advanced: Lighthouse Audit

For comprehensive testing:

1. Open DevTools → **Lighthouse** tab
2. Select:
   - ✅ Performance
   - ✅ Best Practices
   - ✅ Accessibility
   - ✅ PWA
3. Click "**Analyze page load**"
4. Wait for report

**Target Scores:**
- Performance: > 85 🟢
- Best Practices: > 90 🟢
- Accessibility: > 80 🟡
- PWA: > 70 🟡

---

## 🎉 Success Criteria

If you see all of these, optimizations are working:

✅ Console shows "Running on Chromium - optimizations active"  
✅ Glass effects visible and smooth  
✅ Scrolling at 60fps with no jank  
✅ Images lazy load progressively  
✅ Service worker registered and caching  
✅ Page partially works offline  
✅ Memory usage stable (< 150MB)  
✅ No console errors  

**Status:** 🎯 Production Ready!

---

## 📞 Need Help?

Check these resources:
1. `/home/pi/visual-aoi-client/docs/CHROMIUM_OPTIMIZATIONS.md` - Full documentation
2. Chromium DevTools documentation
3. Console error messages (screenshot and report)

---

**Last Updated:** January 2025  
**Version:** 1.0.0  
**Test Duration:** ~5 minutes for full checklist
