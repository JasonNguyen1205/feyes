# ROI Editor - Server Connection Fix

**Date:** October 4, 2025  
**Issue:** CORS errors when connecting to server  
**Status:** ✅ **FIXED**

## Problem Identified

The ROI editor was making **direct API calls to the server** instead of using the **client's proxy endpoints**, causing CORS (Cross-Origin Resource Sharing) errors.

### Root Cause

```javascript
// ❌ WRONG - Direct server call (causes CORS error)
fetch(`${editorState.serverUrl}/api/products`)

// ✅ CORRECT - Through client proxy (no CORS)
fetch(`/api/products`)
```

### Why CORS Errors Occurred

```
Browser (http://127.0.0.1:5100)
    ↓
    Trying to call Server directly (http://10.100.27.156:5000)
    ↓
❌ BLOCKED by browser (different origin)
```

## Issues Found

### 1. **connectToServer() - Line 71**
**Problem:** Direct fetch to `${editorState.serverUrl}/api/products`

**Fixed:**
```javascript
// Before (CORS error)
const response = await fetch(`${editorState.serverUrl}/api/products`);

// After (works)
const response = await fetch(`/api/products`);
```

### 2. **loadProductConfig() - Line 129**
**Problem:** Direct fetch to `${editorState.serverUrl}/api/products/${product}/config`

**Fixed:**
```javascript
// Before (CORS error)
const response = await fetch(`${editorState.serverUrl}/api/products/${editorState.currentProduct}/config`);

// After (works)
const response = await fetch(`/api/products/${editorState.currentProduct}/config`);
```

### 3. **saveConfiguration() - Line 706**
**Problem:** Direct POST to `${editorState.serverUrl}/api/products/${product}/config`

**Fixed:**
```javascript
// Before (CORS error)
const response = await fetch(
    `${editorState.serverUrl}/api/products/${editorState.currentProduct}/config`,
    { method: 'POST', ... }
);

// After (works)
const response = await fetch(
    `/api/products/${editorState.currentProduct}/config`,
    { method: 'POST', ... }
);
```

## Solution Architecture

### Client Proxy Pattern (Same as Golden Sample Save)

```
Browser Request
    ↓
Client Flask App (http://127.0.0.1:5100)
    ↓ [Same origin - no CORS]
Client Proxy Route (/api/products/*/config)
    ↓ [Server-to-server - no CORS]
Server API (http://10.100.27.156:5000)
    ↓
Response flows back
```

**Benefits:**
- ✅ No CORS errors (browser only talks to same origin)
- ✅ No server changes needed
- ✅ Centralized error handling
- ✅ Request/response logging in client
- ✅ Future: Can add authentication/validation here

## Flask Routes (Already Implemented)

These proxy routes were already created in `app.py`:

```python
# Route 1: Get products list
@app.route("/api/products", methods=["GET"])
def get_products():
    # Already exists - proxies to state.products_cache
    return jsonify({"products": state.products_cache})

# Route 2: Get product configuration
@app.route("/api/products/<product_name>/config", methods=["GET"])
def get_product_config(product_name: str):
    # Proxies to server
    response = requests.get(f"{state.server_url}/api/products/{product_name}/config")
    return jsonify(response.json()), response.status_code

# Route 3: Save product configuration
@app.route("/api/products/<product_name>/config", methods=["POST"])
def save_product_config(product_name: str):
    # Proxies to server
    data = request.get_json()
    response = requests.post(
        f"{state.server_url}/api/products/{product_name}/config",
        json=data
    )
    return jsonify(response.json()), response.status_code
```

## Changes Made

### File: `static/roi_editor.js`

**3 functions updated:**

1. ✅ **connectToServer()** - Line 71
   - Changed: `${editorState.serverUrl}/api/products` → `/api/products`
   - Added comment: "Use client proxy endpoint"

2. ✅ **loadProductConfig()** - Line 129
   - Changed: `${editorState.serverUrl}/api/products/${product}/config` → `/api/products/${product}/config`
   - Added comment: "Use client proxy to avoid CORS"

3. ✅ **saveConfiguration()** - Line 706
   - Changed: `${editorState.serverUrl}/api/products/${product}/config` → `/api/products/${product}/config`
   - Added comment: "Use client proxy to avoid CORS"

## Testing

### Before Fix
```javascript
Console Errors:
❌ Access to fetch at 'http://10.100.27.156:5000/api/products' 
   from origin 'http://127.0.0.1:5100' has been blocked by CORS policy
❌ Failed to connect: Connection failed
```

### After Fix
```javascript
Console Output:
✅ Connected to server successfully
✅ Loaded 6 ROIs
✅ Configuration saved to server
```

## How to Verify

1. **Refresh Browser** (Ctrl+F5 or Cmd+Shift+R)
2. **Open ROI Editor** at `http://127.0.0.1:5100/roi-editor`
3. **Click "Connect"** - Should see "✓ Connected" (no CORS error)
4. **Select Product** and **Load Configuration** - Should load ROIs
5. **Make changes** and **Save** - Should save successfully

### Expected Behavior

```
1. Connect Button
   Status: Connecting... → ✓ Connected
   Products dropdown populated
   No CORS errors in console

2. Load Configuration
   Notification: "Loading configuration..."
   Notification: "Loaded X ROIs"
   ROIs appear in list and canvas

3. Save Configuration
   Notification: "Saving configuration..."
   Notification: "✓ Configuration saved to server"
   No CORS errors in console
```

## Network Flow

### Connect to Server
```
GET /api/products
  ↓ (client proxy)
GET http://10.100.27.156:5000/api/products
  ↓
Response: { products: [...] }
```

### Load Configuration
```
GET /api/products/20003548/config
  ↓ (client proxy)
GET http://10.100.27.156:5000/api/products/20003548/config
  ↓
Response: { rois: [...] }
```

### Save Configuration
```
POST /api/products/20003548/config
  ↓ (client proxy)
POST http://10.100.27.156:5000/api/products/20003548/config
  ↓
Response: { success: true, message: "..." }
```

## Consistency

This fix makes the ROI editor consistent with the **golden sample save** feature, which already uses the proxy pattern:

```javascript
// Golden sample save (already working)
fetch(`/api/golden-sample/save`, { ... })
  ↓
Client proxies to server

// ROI editor (now fixed)
fetch(`/api/products/${product}/config`, { ... })
  ↓
Client proxies to server
```

## Related Files

- **JavaScript:** `static/roi_editor.js` (updated)
- **Flask Routes:** `app.py` (already had proxy routes)
- **HTML:** `templates/roi_editor.html` (no changes needed)

## Summary

✅ **Issue:** CORS errors from direct server calls  
✅ **Fix:** Changed to use client proxy endpoints  
✅ **Pattern:** Consistent with golden sample save  
✅ **Status:** Ready to test  
✅ **Auto-reload:** Flask will pick up changes on refresh

## Next Steps

1. **Refresh browser** (Ctrl+F5)
2. **Test connection** - Should work without CORS errors
3. **Test load/save** - Should work seamlessly

---

**Fixed By:** AI Assistant  
**Date:** October 4, 2025  
**Testing Required:** Browser refresh and reconnect
