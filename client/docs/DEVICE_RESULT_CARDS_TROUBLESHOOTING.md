# Device Result Cards Troubleshooting Guide

**Date:** October 9, 2025  
**Issue:** Device result cards not showing in Inspection Control panel  

## Quick Checks

### 1. Clear Browser Cache

The browser might be serving cached HTML/CSS/JS files.

**Chrome/Edge:**

- Press `Ctrl + Shift + Delete`
- Select "Cached images and files"
- Click "Clear data"
- **OR** Hard refresh: `Ctrl + Shift + R` (Windows) or `Cmd + Shift + R` (Mac)

**Firefox:**

- `Ctrl + Shift + Delete` → Clear "Cache" → Clear Now
- **OR** Hard refresh: `Ctrl + F5`

### 2. Check Browser Console

Open Developer Tools and check for errors:

- Press `F12` to open DevTools
- Click "Console" tab
- Run an inspection
- Look for these debug messages:

  ```
  🔧 updateDeviceResultCards called
  🔧 Container found: true
  🔧 Result structure: {...}
  🔧 device_summaries: {...}
  🔧 Found devices: 1 [...]
  ✅ Creating cards for 1 devices
  ```

### 3. Verify Container Exists

In the Console tab, type:

```javascript
document.getElementById('deviceResultsCards')
```

Should return: `<div id="deviceResultsCards" style="display: contents;">...</div>`

If it returns `null`, the HTML wasn't updated properly.

### 4. Check if Result Has device_summaries

In the Console, after running inspection, type:

```javascript
console.log(appState.currentResult)
```

Look for `device_summaries` object in the output.

---

## Common Issues

### Issue 1: Browser Cached Old HTML

**Symptom:** Code changes don't appear in browser

**Solution:**

1. Stop the Flask app (`Ctrl + C`)
2. Clear browser cache completely
3. Restart Flask: `python3 app.py`
4. Open page in **Incognito/Private mode**: `Ctrl + Shift + N`
5. Navigate to `http://localhost:5100/`

### Issue 2: Container Not Found

**Symptom:** Console shows `❌ deviceResultsCards container not found!`

**Check HTML:**

```bash
grep -n "deviceResultsCards" /home/jason_nguyen/visual-aoi-client/templates/professional_index.html
```

Should show line ~209 with: `<div id="deviceResultsCards" style="display: contents;">`

**Solution:** If not found, re-apply the HTML changes.

### Issue 3: No device_summaries in Result

**Symptom:** Console shows `⚠️ No devices found, showing overall result`

**Possible Causes:**

- Server not returning `device_summaries` structure
- Using old API response format
- Product has no devices configured

**Check Server Response:**

1. Open Network tab in DevTools
2. Run inspection
3. Find `/api/inspect` request
4. Check Response → Look for `device_summaries` object

**Expected Structure:**

```json
{
  "device_summaries": {
    "1": {
      "device_id": 1,
      "device_passed": true,
      "barcode": "ABC123",
      "passed_rois": 10,
      "total_rois": 10,
      "roi_results": [...]
    }
  },
  "summary": {
    "overall_result": "PASS"
  }
}
```

### Issue 4: Cards Created But Not Visible

**Symptom:** Console shows cards appended, but not visible on page

**Check CSS:**

```bash
grep -A10 "device-result-card" /home/jason_nguyen/visual-aoi-client/static/professional.css
```

**Verify Grid Display:**
In Console:

```javascript
const timingInfo = document.getElementById('timingInfo');
console.log(window.getComputedStyle(timingInfo).display); // Should be 'grid'
```

**Check Container Display:**

```javascript
const container = document.getElementById('deviceResultsCards');
console.log(window.getComputedStyle(container).display); // Should be 'contents'
```

---

## Debug Commands

### Check if Function Exists

```javascript
typeof updateDeviceResultCards
// Should return: "function"
```

### Manually Trigger Card Creation

```javascript
// Get last result
const result = appState.currentResult;

// Call function manually
updateDeviceResultCards(result);
```

### Inspect Container Children

```javascript
const container = document.getElementById('deviceResultsCards');
console.log('Children count:', container.children.length);
console.log('Children:', Array.from(container.children));
```

### Force Recreate Cards

```javascript
// Mock result for testing
const mockResult = {
  device_summaries: {
    "1": {
      device_id: 1,
      device_passed: true,
      barcode: "TEST123",
      passed_rois: 10,
      total_rois: 10
    },
    "2": {
      device_id: 2,
      device_passed: false,
      barcode: "TEST456",
      passed_rois: 8,
      total_rois: 10
    }
  },
  summary: {
    overall_result: "FAIL"
  }
};

// Create cards
updateDeviceResultCards(mockResult);
```

---

## Step-by-Step Verification

### Step 1: Verify HTML Update

```bash
cd /home/jason_nguyen/visual-aoi-client
grep -A5 "Device Results Cards - Dynamically Generated" templates/professional_index.html
```

**Expected Output:**

```html
<!-- Device Results Cards - Dynamically Generated -->
<div id="deviceResultsCards" style="display: contents;">
    <!-- Device cards will be inserted here -->
</div>
```

### Step 2: Verify JavaScript Update

```bash
grep -n "updateDeviceResultCards" templates/professional_index.html | head -5
```

**Should show multiple lines** (function definition, function call, console logs).

### Step 3: Verify CSS Update

```bash
grep -n "device-result-card" static/professional.css
```

**Should show line numbers** for CSS rules.

### Step 4: Restart Application

```bash
# Kill any running instance
pkill -f "python3 app.py"

# Restart
python3 app.py
```

### Step 5: Test in Browser

1. Open `http://localhost:5100/` in **Incognito mode**
2. Open DevTools (`F12`)
3. Go to Console tab
4. Connect to server
5. Select product "20004960"
6. Initialize camera
7. Create session
8. Click "Perform Inspection"
9. **Watch console for debug messages**

### Step 6: Check Visual Output

After inspection completes:

- Timing panel should show: `Capture Time | Processing Time | Total Time | Capture Groups | Device 1`
- Device card should show: `PASS` or `FAIL` with `X/Y ROIs`

---

## Manual Fix (If Needed)

If issues persist, manually verify these files:

### 1. Check HTML File

```bash
nano /home/jason_nguyen/visual-aoi-client/templates/professional_index.html
```

Search for line ~209, verify:

```html
<div id="deviceResultsCards" style="display: contents;">
```

### 2. Check JavaScript File

Search for `function updateDeviceResultCards`:

- Should have `console.log` statements
- Should create `card.className = 'timing-card device-result-card'`
- Should `container.appendChild(card)`

### 3. Check CSS File

```bash
nano /home/jason_nguyen/visual-aoi-client/static/professional.css
```

Search for `.device-result-card`, verify:

```css
.device-result-card {
    background: linear-gradient(135deg, var(--surface) 0%, rgba(255, 255, 255, 0.02) 100%);
    border: 2px solid var(--glass-border);
    ...
}
```

---

## Expected Console Output

**When working correctly:**

```
🔧 updateDeviceResultCards called
🔧 Container found: true
🔧 Result structure: {device_summaries: {…}, summary: {…}, ...}
🔧 device_summaries: {1: {…}}
🔧 Found devices: 1 [Array(2)]
✅ Creating cards for 1 devices
🔧 Creating card for Device 1: {device_id: 1, device_passed: true, ...}
✅ Device 1 card appended to container
✅ All device cards created and appended
```

**If no devices:**

```
🔧 updateDeviceResultCards called
🔧 Container found: true
🔧 Result structure: {summary: {…}, ...}
🔧 device_summaries: {}
🔧 Found devices: 0 []
⚠️ No devices found, showing overall result
✅ Fallback card appended
```

---

## Visual Verification

### What You Should See

**Timing Panel (5 cards total):**

```
┌─────────────┬─────────────┬─────────────┬─────────────┬──────────┐
│  Capture    │ Processing  │   Total     │   Capture   │ Device 1 │
│  Time (ms)  │  Time (ms)  │  Time (ms)  │   Groups    │   PASS   │
│     357     │     737     │     1178    │      1      │ 10/10    │
│             │             │             │             │   ROIs   │
└─────────────┴─────────────┴─────────────┴─────────────┴──────────┘
```

### What You're Currently Seeing (From Screenshot)

**Timing Panel (5 cards total):**

```
┌─────────────┬─────────────┬─────────────┬─────────────┬──────────┐
│  Capture    │ Processing  │   Total     │   Capture   │   PASS   │  ← Single overall result
│  Time (ms)  │  Time (ms)  │  Time (ms)  │   Groups    │ Device 1 │  ← Device label wrong?
│     357     │     737     │     1178    │      1      │ 10/10    │
│             │             │             │             │   ROIs   │
└─────────────┴─────────────┴─────────────┴─────────────┴──────────┘
```

**This suggests:**

- The HTML might not have updated
- Or browser is caching old version
- The 5th card shows "PASS" on top line but "Device 1" on label line (seems incorrect)

---

## Quick Test

Run this in browser console after inspection:

```javascript
// Check if container exists
const container = document.getElementById('deviceResultsCards');
console.log('Container:', container);

// Check children
console.log('Children:', container ? container.children.length : 'N/A');

// Check last result
console.log('Last result:', appState.currentResult);

// Check if it has device_summaries
console.log('Has device_summaries:', !!appState.currentResult?.device_summaries);
```

---

## Next Steps

1. **Clear browser cache** (most likely issue)
2. **Hard refresh** page (`Ctrl + Shift + R`)
3. **Check console** for debug messages
4. **Report back** what console shows

If still not working, paste the console output here and I'll help debug further!
