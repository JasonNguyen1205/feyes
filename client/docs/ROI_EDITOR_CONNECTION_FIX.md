# ROI Editor - Server Connection Fix

**Date:** October 4, 2025  
**Issue:** Product dropdown showing mock data instead of real products from server  
**Status:** ✅ FIXED

---

## Problem Description

### Symptoms
- ROI Editor shows "✓ Connected" status
- Product dropdown only shows 2 mock products:
  - `sample_2up - Demo 2-up board`
  - `sample_4up - Demo 4-up board`
- Real products from server (12 products) not appearing
- Console shows `"source": "mock"` instead of `"source": "server"`

### Root Cause

**Two-Layer Connection Issue:**

1. **JavaScript Layer (Browser):**
   - ROI Editor's `connectToServer()` function only tested `/api/products` endpoint
   - Showed "Connected" if endpoint responded
   - Did NOT establish actual server connection

2. **Flask Layer (Backend):**
   - `/api/products` endpoint checks `state.connected` flag
   - If `state.connected = False`, returns mock/fallback data
   - Real server connection requires calling `/api/server/connect`

**Data Flow (Before Fix):**
```
Browser → GET /api/products (Flask)
           ↓
      state.connected = False
           ↓
      Return fallback_products()
           ↓
      Mock data: [sample_2up, sample_4up]
```

**Issue:** The JavaScript never called `/api/server/connect` to establish the backend connection to the AOI server.

---

## Solution

### Updated Connection Flow

**File:** `static/roi_editor.js`

**Function:** `connectToServer()`

**Changes:**

1. **Step 1: Establish Backend Connection**
   ```javascript
   // Connect Flask backend to the AOI server
   const connectResponse = await fetch('/api/server/connect', {
       method: 'POST',
       headers: { 'Content-Type': 'application/json' },
       body: JSON.stringify({ server_url: editorState.serverUrl })
   });
   ```

2. **Step 2: Fetch Products from Connected Server**
   ```javascript
   // Fetch products from connected server
   const productsResponse = await fetch(`/api/products`);
   const productsData = await productsResponse.json();
   ```

3. **Enhanced Logging**
   ```javascript
   console.log(`Connecting to server: ${editorState.serverUrl}`);
   console.log('Server connected:', connectData);
   console.log('Products data:', productsData);
   ```

4. **Better User Feedback**
   ```javascript
   showNotification(`Connected to server successfully. Source: ${productsData.source}`, 'success');
   ```

### Data Flow (After Fix)

```
Browser → POST /api/server/connect (Flask)
           ↓
      Call server /api/health
      Call server /api/initialize  
      Call server /api/products
           ↓
      state.connected = True
      state.products_cache = [12 products]
           ↓
      Return {"status": "connected", "products": [...]}
           
Browser → GET /api/products (Flask)
           ↓
      state.connected = True
           ↓
      Return state.products_cache
           ↓
      Real data: [test_product_golden, 20002810, ...]
```

---

## Results

### Before Fix

**Mock Products (2):**
```json
{
  "products": [
    {
      "product_name": "sample_2up",
      "description": "Demo 2-up board",
      "device_count": 2
    },
    {
      "product_name": "sample_4up",
      "description": "Demo 4-up board",
      "device_count": 4
    }
  ],
  "source": "mock"
}
```

### After Fix

**Server Products (12):**
```json
{
  "products": [
    {
      "product_name": "test_product_golden",
      "description": "Product configuration for test_product_golden",
      "config_file": "/home/jason_nguyen/visual-aoi-server/server/../config/products/test_product_golden.json"
    },
    {
      "product_name": "20002810",
      "description": "Legacy product configuration for 20002810",
      "config_file": "/home/jason_nguyen/visual-aoi-server/server/../config/products/20002810/rois_config_20002810.json"
    },
    {
      "product_name": "test_ocr_sample",
      "description": "Legacy product configuration for test_ocr_sample"
    },
    {
      "product_name": "20001234",
      "description": "Legacy product configuration for 20001234"
    },
    {
      "product_name": "knx",
      "description": "Legacy product configuration for knx"
    },
    {
      "product_name": "test_ocr_demo",
      "description": "Legacy product configuration for test_ocr_demo"
    },
    {
      "product_name": "20001111",
      "description": "Legacy product configuration for 20001111"
    },
    {
      "product_name": "test_sample_text_config",
      "description": "Legacy product configuration for test_sample_text_config"
    },
    {
      "product_name": "20003548",
      "description": "Legacy product configuration for 20003548"
    },
    {
      "product_name": "20004960",
      "description": "Legacy product configuration for 20004960"
    },
    {
      "product_name": "01961815",
      "description": "Legacy product configuration for 01961815"
    },
    {
      "product_name": "20003559",
      "description": "Legacy product configuration for 20003559"
    }
  ],
  "source": "server"
}
```

### UI Display

**Product Dropdown Options:**
```
-- Select Product --
test_product_golden - Product configuration for test_product_golden
20002810 - Legacy product configuration for 20002810
test_ocr_sample - Legacy product configuration for test_ocr_sample
20001234 - Legacy product configuration for 20001234
knx - Legacy product configuration for knx
test_ocr_demo - Legacy product configuration for test_ocr_demo
20001111 - Legacy product configuration for 20001111
test_sample_text_config - Legacy product configuration for test_sample_text_config
20003548 - Legacy product configuration for 20003548
20004960 - Legacy product configuration for 20004960
01961815 - Legacy product configuration for 01961815
20003559 - Legacy product configuration for 20003559
```

---

## Technical Details

### Backend State Management

**Flask `state` Object:**
```python
class ServerState:
    server_url: str = "http://10.100.27.156:5000"
    connected: bool = False  # ← Key flag
    products_cache: List[Dict[str, Any]] = []
    # ... other fields
```

**Connection Endpoint:** `POST /api/server/connect`

**Actions Performed:**
1. Test server health: `GET /api/health`
2. Initialize AI models: `POST /api/initialize`
3. Fetch products: `GET /api/products`
4. Set `state.connected = True`
5. Cache products in `state.products_cache`
6. Return connection status + products

**Product List Endpoint:** `GET /api/products`

**Logic:**
```python
@app.route("/api/products", methods=["GET"])
def get_products():
    if not state.connected:
        return jsonify({"products": fallback_products(), "source": "mock"}), 200
    
    if not state.products_cache:
        state.products_cache = fetch_products_from_server()
    
    return jsonify({"products": state.products_cache, "source": "server"}), 200
```

### Frontend State Management

**JavaScript `editorState` Object:**
```javascript
const editorState = {
    serverUrl: 'http://10.100.27.156:5000',
    connected: false,  // UI connection status
    currentProduct: null,
    // ... other fields
};
```

**Note:** `editorState.connected` tracks UI status, separate from backend `state.connected`

### Error Handling

**Connection Errors:**
```javascript
try {
    const connectResponse = await fetch('/api/server/connect', { ... });
    if (!connectResponse.ok) {
        const error = await connectResponse.json();
        throw new Error(error.error || 'Connection failed');
    }
} catch (error) {
    editorState.connected = false;
    statusEl.className = 'status-indicator disconnected';
    statusEl.textContent = '✗ Connection failed';
    showNotification(`Failed to connect: ${error.message}`, 'error');
}
```

**Server Response Errors:**
- 502 Bad Gateway: Server unreachable
- 500 Internal Error: Server API failure
- 400 Bad Request: Invalid server URL

---

## Testing

### Verification Steps

1. **Open ROI Editor:**
   ```
   http://localhost:5100/roi-editor
   ```

2. **Check Initial Status:**
   - Should show "Connecting..." briefly
   - Should auto-connect on page load

3. **Verify Connection:**
   - Status indicator: "✓ Connected" (green)
   - Notification: "Connected to server successfully. Source: server"
   - Console log: "✅ Populated 12 products in dropdown"

4. **Check Product Dropdown:**
   - Should show 12+ products (not just 2)
   - Should show real product names (20003548, etc.)
   - Should show descriptions alongside names

5. **Test Connection Failure:**
   - Stop server: `kill $(lsof -t -i:5000)`
   - Click "Connect" button
   - Should show: "✗ Connection failed" (red)
   - Should show fallback products (sample_2up, sample_4up)

### Console Verification

**Expected Console Output:**
```
Connecting to server: http://10.100.27.156:5000
Server connected: {status: "connected", health: {...}, products: [...]}
Products data: {products: [...], source: "server"}
✅ Populated 12 products in dropdown
```

### Backend Verification

**Test Server Connection:**
```bash
curl -X POST http://localhost:5100/api/server/connect \
  -H "Content-Type: application/json" \
  -d '{"server_url": "http://10.100.27.156:5000"}'
```

**Expected Response:**
```json
{
  "status": "connected",
  "health": { "status": "healthy", ... },
  "init": { "success": true, ... },
  "products": [ ... 12 products ... ]
}
```

**Test Product List:**
```bash
curl http://localhost:5100/api/products
```

**Expected Response:**
```json
{
  "products": [ ... 12 products ... ],
  "source": "server"
}
```

---

## Related Issues

### Issue 1: Mock Data Fallback

**When It Happens:**
- Server unreachable
- Server not initialized
- Connection not established

**Behavior:**
- Returns 2 fallback products
- Shows `"source": "mock"`
- Allows basic testing without server

**Solution:** Ensure `/api/server/connect` called before using editor

### Issue 2: Product List Not Refreshing

**Symptom:** Old products shown after server update

**Cause:** Products cached in `state.products_cache`

**Solution:**
```python
# Clear cache to force refresh
state.products_cache = None

# Or reconnect to server
POST /api/server/disconnect
POST /api/server/connect
```

### Issue 3: "[object Object]" in Dropdown

**Fixed In:** Previous update (October 4, 2025)

**Solution:** Parse `product.product_name` from product objects

---

## Best Practices

### For Developers

1. **Always Connect First:**
   - Call `/api/server/connect` before any product operations
   - Check `state.connected` in backend endpoints
   - Show connection status to users

2. **Cache Management:**
   - Clear `state.products_cache` after product creation/deletion
   - Refresh products list after reconnection
   - Handle stale cache scenarios

3. **Error Handling:**
   - Graceful degradation to mock data
   - Clear error messages to users
   - Log connection attempts for debugging

### For Users

1. **Check Connection Status:**
   - Green "✓ Connected" = real products
   - Red "✗ Connection failed" = mock products
   - Yellow "Connecting..." = in progress

2. **Verify Product Source:**
   - Success notification shows "Source: server" or "Source: mock"
   - Console shows product count
   - Dropdown shows real product names (not "sample_*")

3. **Troubleshooting:**
   - If only 2 products shown → Connection failed
   - Click "Connect" button to retry
   - Check server is running: `curl http://10.100.27.156:5000/api/health`

---

## Summary

**Root Cause:** ROI Editor tested `/api/products` endpoint but never called `/api/server/connect` to establish actual backend connection to AOI server.

**Solution:** Updated `connectToServer()` to call `/api/server/connect` first, then fetch products from connected server.

**Result:** Product dropdown now shows all 12 real products from server instead of 2 mock products.

**Verification:** Console logs show `"source": "server"` and product count matches server products.

**Files Modified:**
- `static/roi_editor.js` - Updated `connectToServer()` function

**Related Endpoints:**
- `POST /api/server/connect` - Establish backend connection
- `GET /api/products` - Fetch product list (requires connection)
- `POST /api/server/disconnect` - Close connection
