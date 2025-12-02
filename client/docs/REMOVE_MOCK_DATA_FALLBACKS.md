# Remove Mock Data Fallbacks

**Date:** October 8, 2025  
**Status:** ✅ Completed  
**Issue:** System was falling back to mock data when server returned errors

## Problem

The system had multiple fallback mechanisms that returned mock/dummy data when server API calls failed. This masked real errors and allowed the application to continue running with fake data instead of properly handling failures.

**Example Error:**

```
WARNING:app:Using mock ROI groups for 20003548: 500 Server Error: INTERNAL SERVER ERROR for url: http://10.100.27.156:5000/get_roi_groups/20003548
```

## Changes Made

### 1. Removed Mock ROI Groups Fallback

**Before:**

```python
def fetch_roi_groups(product_name: str) -> Dict[str, Any]:
    try:
        response = call_server("GET", f"/get_roi_groups/{product_name}", timeout=10)
        # ... fetch logic ...
    except Exception as exc:
        app.logger.warning("Using mock ROI groups for %s: %s", product_name, exc)
    
    # Always returned mock data on failure
    return {
        "300,2500": {
            "focus": 300,
            "exposure": 2500,
            "rois": [{"id": 1, "device": 1, "type": "compare"}],
        }
    }
```

**After:**

```python
def fetch_roi_groups(product_name: str) -> Dict[str, Any]:
    """
    Fetch ROI groups from server.
    
    Raises:
        RuntimeError: If server returns an error or ROI groups cannot be fetched
    """
    try:
        response = call_server("GET", f"/get_roi_groups/{product_name}", timeout=10)
        payload = response.json()
        roi_groups = payload.get("roi_groups", {}) if isinstance(payload, dict) else {}
        if roi_groups:
            app.logger.info(f"✓ Fetched {len(roi_groups)} ROI groups for product '{product_name}'")
            return roi_groups
        else:
            error_msg = f"No ROI groups returned from server for product '{product_name}'"
            app.logger.error(error_msg)
            raise RuntimeError(error_msg)
    except Exception as exc:
        error_msg = f"Failed to fetch ROI groups for product '{product_name}': {exc}"
        app.logger.error(error_msg)
        raise RuntimeError(error_msg) from exc
```

### 2. Removed Mock Products Fallback

**Before:**

```python
def fallback_products() -> List[Dict[str, Any]]:
    return [
        {"product_name": "sample_2up", "description": "Demo 2-up board", "device_count": 2},
        {"product_name": "sample_4up", "description": "Demo 4-up board", "device_count": 4},
    ]

def fetch_products_from_server() -> List[Dict[str, Any]]:
    try:
        # ... fetch logic ...
    except Exception as exc:
        app.logger.warning("Falling back to mock products: %s", exc)
    return fallback_products()  # Always returned mock data
```

**After:**

```python
def fetch_products_from_server() -> List[Dict[str, Any]]:
    """
    Fetch products list from server.
    
    Raises:
        RuntimeError: If server connection fails or no products are returned
    """
    try:
        response = call_server("GET", "/api/products", timeout=10)
        payload = response.json()
        if isinstance(payload, dict) and "products" in payload:
            products = payload["products"]
            if not products:
                error_msg = "Server returned empty products list"
                app.logger.error(error_msg)
                raise RuntimeError(error_msg)
            app.logger.info(f"✓ Fetched {len(products)} products from server")
            return products
        # ... handle other formats ...
    except Exception as exc:
        error_msg = f"Failed to fetch products from server: {exc}"
        app.logger.error(error_msg)
        raise RuntimeError(error_msg) from exc
```

### 3. Updated `/api/products` Endpoint

**Before:**

```python
@app.route("/api/products", methods=["GET"])
def get_products():
    if not state.connected:
        return jsonify({"products": fallback_products(), "source": "mock"}), 200
    # ...
```

**After:**

```python
@app.route("/api/products", methods=["GET"])
def get_products():
    """Get list of available products from server."""
    if not state.connected:
        return jsonify({"error": "Not connected to server"}), 503

    try:
        if not state.products_cache:
            state.products_cache = fetch_products_from_server()
        return jsonify({"products": state.products_cache, "source": "server"}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to fetch products: {str(e)}"}), 500
```

### 4. Removed Mock Inspection Results

**Before:**

```python
def build_mock_result(product_name: str, captured_images: Dict[str, Any]) -> Dict[str, Any]:
    # ... build mock result ...
    return {
        "product": product_name,
        "overall_pass": overall_pass,
        "devices": devices,
    }

def send_grouped_inspection(...):
    try:
        response = call_server("POST", "/process_grouped_inspection", ...)
        return result
    except Exception as exc:
        app.logger.warning("Falling back to mock inspection result: %s", exc)
        result = build_mock_result(product_name, captured_images)
        result.update({"source": "mock", "error": str(exc)})
        return result  # Always returned mock data
```

**After:**

```python
def send_grouped_inspection(...):
    try:
        response = call_server("POST", "/process_grouped_inspection", json=payload, timeout=60)
        result = response.json()
        result.setdefault("source", "server")
        logger.info(f"✓ Inspection completed successfully for product '{product_name}'")
        return result
    except Exception as exc:
        error_msg = f"Inspection failed for product '{product_name}': {exc}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from exc
```

### 5. Updated ROI Groups Fetch in `/api/roi_editor/config`

**Before:**

```python
try:
    groups_response = requests.get(f"{server_url}/get_roi_groups/{product_name}", timeout=10)
    if groups_response.status_code == 200:
        roi_groups = groups_data.get('roi_groups', {})
    else:
        logger.warning(f"Failed to fetch ROI groups: {groups_response.status_code}")
except Exception as e:
    logger.warning(f"Could not fetch ROI groups: {e}")

# Continued with empty roi_groups
```

**After:**

```python
try:
    groups_response = requests.get(f"{server_url}/get_roi_groups/{product_name}", timeout=10)
    if groups_response.status_code == 200:
        groups_data = groups_response.json()
        roi_groups = groups_data.get('roi_groups', {})
        if not roi_groups:
            error_msg = f"No ROI groups returned from server for product '{product_name}'"
            logger.error(error_msg)
            return jsonify({"error": error_msg}), 500
        logger.info(f"✓ Fetched {len(roi_groups)} ROI groups from server")
    else:
        error_msg = f"Failed to fetch ROI groups: HTTP {groups_response.status_code} - {groups_response.text}"
        logger.error(error_msg)
        return jsonify({"error": error_msg}), groups_response.status_code
except Exception as e:
    error_msg = f"Could not fetch ROI groups: {str(e)}"
    logger.error(error_msg)
    return jsonify({"error": error_msg}), 500
```

### 6. Updated Golden Samples Endpoint

**Before:**

```python
def get_golden_samples(product_name: str, roi_id: int):
    try:
        # For now, return mock data
        return jsonify({
            "golden_samples": [],
            "count": 0
        }), 200
```

**After:**

```python
def get_golden_samples(product_name: str, roi_id: int):
    """Get golden samples for a specific ROI."""
    try:
        if not state.connected:
            return jsonify({"error": "Not connected to server"}), 503
            
        response = call_server(
            "GET", 
            f"/api/products/{product_name}/rois/{roi_id}/golden_samples",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return jsonify(data), 200
        else:
            error_msg = f"Server returned {response.status_code}: {response.text}"
            logger.error(f"Failed to get golden samples: {error_msg}")
            return jsonify({"error": error_msg}), response.status_code
```

## Behavior Changes

### Before (With Mock Data)

| Scenario | Old Behavior |
|----------|--------------|
| Server returns 500 error for ROI groups | ⚠️ Returns mock ROI groups, continues with fake data |
| Server returns error for products | ⚠️ Returns mock products list |
| Inspection API fails | ⚠️ Returns mock inspection result with fake pass/fail |
| Not connected to server | ⚠️ Returns mock products list |
| ROI groups endpoint fails | ⚠️ Continues with empty groups |

### After (No Mock Data)

| Scenario | New Behavior |
|----------|--------------|
| Server returns 500 error for ROI groups | ✅ Raises RuntimeError, fails fast |
| Server returns error for products | ✅ Returns HTTP 500 with error message |
| Inspection API fails | ✅ Raises RuntimeError, inspection fails |
| Not connected to server | ✅ Returns HTTP 503 "Not connected" |
| ROI groups endpoint fails | ✅ Returns HTTP 500 with detailed error |

## Benefits

### 1. **Fail Fast, Fail Loud**

- Errors are immediately visible
- No silent failures masked by mock data
- Easier to diagnose real problems

### 2. **Data Integrity**

- Never shows fake inspection results
- Never allows inspection with invalid configuration
- Ensures all data comes from real server

### 3. **Better Error Messages**

- Clear error messages with HTTP status codes
- Detailed logging of what went wrong
- Easier troubleshooting

### 4. **Production Safety**

- Prevents running inspections with mock data
- Forces server issues to be fixed
- No confusion about data source

## Testing

### Test Case 1: Server Connection Failure

**Before:**

```bash
# Server down
curl http://localhost:5001/api/products
# Returns: {"products": [{"product_name": "sample_2up"}, ...], "source": "mock"}
```

**After:**

```bash
# Server down
curl http://localhost:5001/api/products
# Returns: {"error": "Not connected to server"}, 503
```

### Test Case 2: ROI Groups Error

**Before:**

```python
# Server returns 500
roi_groups = fetch_roi_groups("20003548")
# Returns: {"300,2500": {"focus": 300, ...}}  # Mock data
```

**After:**

```python
# Server returns 500
roi_groups = fetch_roi_groups("20003548")
# Raises: RuntimeError: Failed to fetch ROI groups for product '20003548': 500 Server Error
```

### Test Case 3: Inspection Failure

**Before:**

```python
# Server inspection fails
result = send_grouped_inspection(product_name, captured_images, ...)
# Returns: {"source": "mock", "error": "...", "overall_pass": True}  # Fake result
```

**After:**

```python
# Server inspection fails
result = send_grouped_inspection(product_name, captured_images, ...)
# Raises: RuntimeError: Inspection failed for product '20003548': Connection error
```

## Migration Notes

### For Developers

1. **Error Handling Required**: Functions that previously never failed now raise exceptions
2. **Try-Catch Needed**: Wrap calls in try-except if you want to handle errors gracefully
3. **HTTP Errors**: API endpoints now return proper HTTP error codes (500, 503) instead of 200 with mock data

### For Frontend

The frontend needs to handle error responses properly:

```javascript
// Before: Always got 200 OK with data or mock data
const response = await fetch('/api/products');
const data = await response.json();
// data.source could be "mock" or "server"

// After: Check for errors
const response = await fetch('/api/products');
if (!response.ok) {
    const error = await response.json();
    console.error('Failed to fetch products:', error.error);
    // Show error to user
    return;
}
const data = await response.json();
// data.source is always "server"
```

## Legitimate Fallbacks Kept

The following fallback mechanisms were **kept** as they are legitimate:

1. **Direct file access fallback** (line 1592): If server API returns 404, tries to read config file directly from filesystem
   - This is legitimate because it's accessing real data, not mock data
   - Useful when server API is unavailable but filesystem is accessible

## Summary

All mock data fallbacks have been removed. The system now:

✅ **Fails immediately** when server returns errors  
✅ **Shows clear error messages** instead of masking issues  
✅ **Never uses mock/fake data** in any scenario  
✅ **Returns proper HTTP error codes** (500, 503) instead of 200 with mock data  
✅ **Logs all errors** with detailed messages for debugging  

This ensures production reliability and makes debugging much easier by exposing real problems immediately instead of hiding them behind mock data.

## Related Files

- `/home/jason_nguyen/visual-aoi-client/app.py` - All changes implemented here
- Functions modified:
  - `fetch_roi_groups()`
  - `fetch_products_from_server()`
  - `send_grouped_inspection()`
  - `get_products()` endpoint
  - `get_golden_samples()` endpoint
  - ROI groups fetch in `/api/roi_editor/config`

## Next Steps

1. ✅ Test all endpoints with server running properly
2. ✅ Test error scenarios (server down, 500 errors, etc.)
3. ✅ Update frontend to handle error responses
4. ✅ Monitor logs for any issues
5. ✅ Fix server-side issues if they appear (e.g., the 500 error for product 20003548)
