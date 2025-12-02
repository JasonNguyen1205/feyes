# Troubleshooting: "Failed to Fetch" Error After Golden Sample Save

**Date:** October 4, 2025  
**Issue:** Golden sample saves correctly but app shows "Failed to fetch..." error  
**Status:** 🔍 DEBUGGING ENHANCED

## Problem Description

User reports that:
- ✅ Golden sample IS saved correctly on server
- ❌ Client shows error: "Failed to save golden sample: Failed to fetch..."

This indicates the save operation succeeds but the client encounters an error during the process.

## Possible Causes

### 1. Image Fetch Error (Client-Side)

**Symptom:** Error occurs when fetching captured image from shared folder

**Error Message:**
```
Failed to save golden sample: Failed to fetch ROI image from /shared/sessions/xxx/roi_5.jpg: 404 Not Found
```

**Root Causes:**
- Image file doesn't exist at the path
- Path format is incorrect
- Permissions issue on shared folder
- Flask `/shared/` route not working

**Solution:**
Check console logs for:
```javascript
📸 Fetching captured image from: /shared/sessions/xxx/roi_5.jpg
Original path: /mnt/visual-aoi-shared/sessions/xxx/roi_5.jpg
Image fetch response: { status: 404, statusText: 'Not Found', ok: false }
```

### 2. CORS Error (Server-Side)

**Symptom:** Browser blocks request to server

**Error Message:**
```
Failed to save golden sample: Failed to fetch
Access to fetch at 'http://10.100.27.156:5000/api/golden-sample/save' has been blocked by CORS policy
```

**Root Causes:**
- Server doesn't allow CORS from client origin
- Missing CORS headers in server response

**Solution:**
Server needs to add CORS headers:
```python
from flask_cors import CORS
CORS(app)
```

Or manually:
```python
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    return response
```

### 3. Server Response Parse Error

**Symptom:** Server saves successfully but returns non-JSON response

**Error Message:**
```
Failed to save golden sample: Unexpected token < in JSON at position 0
```

**Root Causes:**
- Server returns HTML error page instead of JSON
- Server response is empty
- Server returns plain text instead of JSON

**Solution:**
Enhanced error handling now catches this:
```javascript
try {
    result = await response.json();
} catch (parseError) {
    // If status is 200, consider it success
    if (response.ok) {
        result = { message: 'Golden sample saved successfully' };
    }
}
```

### 4. Network Timeout

**Symptom:** Request times out for large images

**Error Message:**
```
Failed to save golden sample: Failed to fetch
```

**Root Causes:**
- Image file is very large
- Slow network connection
- Server is slow to respond

**Solution:**
Check image size in console:
```javascript
Image blob created: { size: 2500000, type: 'image/jpeg' }
```

If > 10MB, may need compression.

## Enhanced Debugging (NEW)

### Console Logs Added

The updated code now logs detailed information at each step:

#### 1. Image Fetching
```javascript
📸 Fetching captured image from: /shared/sessions/abc-123/output/roi_5.jpg
Original path: /mnt/visual-aoi-shared/sessions/abc-123/output/roi_5.jpg
Image fetch response: {
  status: 200,
  statusText: 'OK',
  ok: true,
  contentType: 'image/jpeg'
}
Image blob created: {
  size: 1847290,
  type: 'image/jpeg'
}
```

#### 2. Server Request
```javascript
📤 Sending to server: {
  product_name: '20003548',
  roi_id: '5',
  image_size: 1847290,
  image_type: 'image/jpeg',
  filename: 'roi_5.jpg'
}
Sending request to: http://10.100.27.156:5000/api/golden-sample/save
```

#### 3. Server Response
```javascript
Server response: {
  status: 200,
  statusText: 'OK',
  ok: true,
  headers: {
    contentType: 'application/json'
  }
}
Server result: {
  message: 'Golden sample saved successfully for ROI 5',
  backup_info: 'Previous sample backed up as golden_5_backup_20251004_123456.jpg'
}
✅ Golden sample saved successfully: { ... }
```

### Error Cases

#### Case 1: Image Not Found
```javascript
📸 Fetching captured image from: /shared/sessions/xxx/roi_5.jpg
Original path: /mnt/visual-aoi-shared/sessions/xxx/roi_5.jpg
Image fetch response: {
  status: 404,
  statusText: 'Not Found',
  ok: false,
  contentType: 'application/json'
}
❌ Error: Failed to fetch ROI image from /shared/sessions/xxx/roi_5.jpg: 404 Not Found
```

**Action:** Check if file exists:
```bash
ls -la /mnt/visual-aoi-shared/sessions/xxx/output/roi_5.jpg
```

#### Case 2: Server Error
```javascript
📤 Sending to server: { ... }
Sending request to: http://10.100.27.156:5000/api/golden-sample/save
Server response: {
  status: 500,
  statusText: 'Internal Server Error',
  ok: false
}
Server result: {
  error: 'Failed to save golden sample: Permission denied'
}
❌ Error: Failed to save golden sample: Permission denied
```

**Action:** Check server logs for details

#### Case 3: Network Error
```javascript
📤 Sending to server: { ... }
Sending request to: http://10.100.27.156:5000/api/golden-sample/save
❌ Error: Failed to fetch
```

**Action:** 
- Check if server is running
- Check network connectivity
- Check CORS settings

## Debugging Steps

### Step 1: Check Console Logs

1. Open browser DevTools (F12)
2. Go to Console tab
3. Clear console
4. Click "Save as Golden Sample"
5. Check logs for detailed information

### Step 2: Identify Error Stage

Look for the **last successful log** before error:

**If last log is:**
```javascript
📸 Fetching captured image from: ...
```
→ Problem is fetching image from client

**If last log is:**
```javascript
Image blob created: { ... }
```
→ Problem is sending to server

**If last log is:**
```javascript
Sending request to: http://...
```
→ Problem is network/CORS

**If last log is:**
```javascript
Server response: { status: 200 }
```
→ Problem is parsing response

### Step 3: Check Network Tab

1. Go to Network tab in DevTools
2. Filter by "Fetch/XHR"
3. Look for:
   - Request to `/shared/sessions/.../roi_X.jpg`
   - Request to `http://10.100.27.156:5000/api/golden-sample/save`

**Check each request:**
- Status code (200 = success, 404 = not found, 500 = server error)
- Response preview
- Response headers

### Step 4: Verify File Exists

```bash
# Check if captured image exists
ls -la /mnt/visual-aoi-shared/sessions/{session_id}/output/roi_5.jpg

# Check permissions
stat /mnt/visual-aoi-shared/sessions/{session_id}/output/roi_5.jpg

# Check if Flask can serve it
curl http://localhost:5100/shared/sessions/{session_id}/output/roi_5.jpg
```

### Step 5: Verify Server Endpoint

```bash
# Test server endpoint directly
curl -X POST \
  http://10.100.27.156:5000/api/golden-sample/save \
  -F "product_name=20003548" \
  -F "roi_id=5" \
  -F "golden_image=@/path/to/test.jpg"
```

Expected response:
```json
{
  "message": "Golden sample saved successfully for ROI 5",
  "backup_info": "..."
}
```

## Quick Fixes

### Fix 1: If Image Fetch Fails

**Add fallback to base64 from result:**

```javascript
// If fetching from shared folder fails, try base64 from result
if (!imageResponse.ok && roiData.roi_image) {
    // Use base64 image data directly
    const base64Data = roiData.roi_image.split(',')[1];
    const byteCharacters = atob(base64Data);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    imageBlob = new Blob([byteArray], { type: 'image/jpeg' });
}
```

### Fix 2: If CORS Error

**Configure server to allow client origin:**

```python
# In server app.py
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=['http://localhost:5100'])
```

### Fix 3: If Server Returns HTML

**Check response content-type:**

```javascript
const contentType = response.headers.get('content-type');
if (contentType && contentType.includes('application/json')) {
    result = await response.json();
} else {
    // Server returned non-JSON (probably HTML error page)
    const text = await response.text();
    console.error('Server returned non-JSON:', text);
    throw new Error('Server returned invalid response');
}
```

## Updated Code Changes

### File: `templates/professional_index.html`

**Enhanced Error Handling:**

1. ✅ Added detailed console logs at each step
2. ✅ Log image fetch details (URL, status, size)
3. ✅ Log server request details (endpoint, data)
4. ✅ Log server response details (status, headers)
5. ✅ Handle JSON parse errors gracefully
6. ✅ Show detailed error messages with context
7. ✅ Consider 200 OK as success even if JSON parsing fails

**New Logs:**
- `📸 Fetching captured image from: ...`
- `Image fetch response: { status, ok, contentType }`
- `Image blob created: { size, type }`
- `📤 Sending to server: { product_name, roi_id, image_size }`
- `Sending request to: {endpoint}`
- `Server response: { status, ok, headers }`
- `Server result: { ... }`
- `✅ Golden sample saved successfully`

## Testing Checklist

After applying enhanced debugging:

1. ☐ Refresh browser (Ctrl+F5)
2. ☐ Open DevTools Console (F12)
3. ☐ Run inspection
4. ☐ Click "Save as Golden Sample"
5. ☐ **Check console logs** - identify exact failure point
6. ☐ **Check Network tab** - verify all requests succeed
7. ☐ **Copy error logs** - share for further debugging

## Expected Behavior

### Success Case
```
1. User clicks "Save as Golden Sample"
2. Console shows:
   📸 Fetching captured image from: /shared/...
   Image fetch response: { status: 200, ok: true }
   Image blob created: { size: 1847290, type: 'image/jpeg' }
   📤 Sending to server: { ... }
   Sending request to: http://10.100.27.156:5000/...
   Server response: { status: 200, ok: true }
   Server result: { message: '...' }
   ✅ Golden sample saved successfully
3. Notification: "✅ Golden sample saved for ROI 5"
4. No errors
```

### Failure Case (Example)
```
1. User clicks "Save as Golden Sample"
2. Console shows:
   📸 Fetching captured image from: /shared/...
   Image fetch response: { status: 404, ok: false }
   ❌ Error: Failed to fetch ROI image from /shared/...: 404 Not Found
3. Notification: "Failed to save golden sample: Failed to fetch ROI image..."
4. → Action: Check if file exists at path
```

## Next Steps

1. **User:** Refresh browser and try again
2. **User:** Open Console and share all logs from error
3. **User:** Check Network tab for failed requests
4. **Dev:** Analyze logs to identify exact failure point
5. **Dev:** Apply appropriate fix based on cause

## Related Issues

- Missing `sessionProduct` - Fixed in `FIX_NO_PRODUCT_SELECTED_ERROR.md`
- Image loading from shared folder - `SHARED_FOLDER_IMAGE_LOADING.md`
- Server API spec - Server Swagger: `http://10.100.27.156:5000/apidocs/`

---

**Status:** 🔍 Enhanced debugging added  
**Next:** Waiting for user logs to identify exact cause  
**Last Updated:** October 4, 2025
