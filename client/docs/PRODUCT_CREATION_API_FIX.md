# Product Creation API Endpoint Fix

**Date:** October 9, 2025  
**Priority:** 🐛 Bug Fix  
**Status:** ✅ Fixed

## Problem

Product creation was failing with 405 (Method Not Allowed) error:

```
INFO: Creating product '20004960' on server (devices: 1)
WARNING: Server returned 405 for product creation
ERROR: ❌ Failed to create product: Expecting value: line 1 column 1 (char 0)
```

## Root Cause

**Incorrect API Endpoint**

The client was sending POST requests to the wrong endpoint:

```python
# ❌ WRONG - Client was using:
response = requests.post(f"{server_url}/api/products", ...)

# ✅ CORRECT - Server expects:
response = requests.post(f"{server_url}/api/products/create", ...)
```

**Why 405 Error?**

- HTTP 405 = Method Not Allowed
- `/api/products` endpoint only accepts GET requests (to list products)
- `/api/products/create` endpoint accepts POST requests (to create new product)
- Client was POSTing to the GET-only endpoint

## Server API Documentation Reference

**Source:** <http://10.100.27.156:5000/apidocs/> (Swagger/Flasgger)

### Correct Endpoint: `/api/products/create`

**Method:** POST

**Request Body:**

```json
{
  "product_name": "string",      // Required
  "description": "string"         // Optional
}
```

**Response (200):**

```json
{
  "success": true,
  "message": "Product created successfully",
  "product_name": "string",
  "config_file": "path/to/config.json"
}
```

**Response (400):**

```json
{
  "error": "Invalid input"
}
```

**Response (500):**

```json
{
  "error": "Creation failed",
  "success": false
}
```

### Wrong Endpoint: `/api/products`

**Method:** GET (not POST)

**Purpose:** List all available products

**Response:**

```json
{
  "products": [
    {
      "product_name": "string",
      "description": "string",
      "config_file": "string"
    }
  ],
  "count": 0
}
```

## Solution Implemented

**File:** `app.py` line 1519-1530

### Before (Incorrect)

```python
response = requests.post(
    f"{server_url}/api/products",  # ❌ Wrong endpoint
    json={
        "product_name": product_name,
        "description": description,
        "device_count": device_count  # ❌ Not in server API
    },
    headers={'Content-Type': 'application/json'},
    timeout=30
)
```

### After (Correct)

```python
# CORRECT: Server API endpoint is /api/products/create (per Swagger docs)
response = requests.post(
    f"{server_url}/api/products/create",  # ✅ Correct endpoint
    json={
        "product_name": product_name,
        "description": description
        # device_count removed - not part of server API
    },
    headers={'Content-Type': 'application/json'},
    timeout=30
)
```

### Key Changes

1. ✅ **Endpoint:** `/api/products` → `/api/products/create`
2. ✅ **Payload:** Removed `device_count` field (not in server API spec)
3. ✅ **Matches:** Server Swagger documentation exactly

## Additional Improvements

The error handling was already improved in the previous fix to handle non-JSON responses:

```python
# Try to parse JSON error, fallback to text if not JSON
try:
    error_data = response.json()
    error_msg = error_data.get('error', f'Server error: {response.status_code}')
except Exception:
    error_msg = f'Server error {response.status_code}: {response.text[:100]}'
```

This now properly handles:

- ✅ 405 Method Not Allowed errors
- ✅ HTML error responses
- ✅ Empty responses
- ✅ JSON error responses

## Expected Behavior

### Before Fix

```
Client POSTs to: /api/products
Server Response: 405 Method Not Allowed (HTML page)
Client tries to parse HTML as JSON
Error: "Expecting value: line 1 column 1 (char 0)"
Result: ❌ Cryptic error, no product created
```

### After Fix

```
Client POSTs to: /api/products/create
Server Response: 200 OK with JSON
{
  "success": true,
  "message": "Product created successfully",
  "product_name": "20004960",
  "config_file": "config/products/20004960/config.json"
}
Result: ✅ Product created successfully
```

## Testing

### Test 1: Create New Product

**Steps:**

1. Open ROI Editor in web UI
2. Click "Create New Product"
3. Enter product name (e.g., "test_product_001")
4. Optional: Enter description
5. Click "Create"

**Expected:**

```
INFO: Creating product 'test_product_001' on server
INFO: ✅ Product 'test_product_001' created successfully
```

**Verify:**

- Product appears in product dropdown
- Config file created: `config/products/test_product_001/config.json`
- No 405 errors in logs

### Test 2: Duplicate Product Name

**Steps:**

1. Try to create product with existing name

**Expected:**

```
WARNING: Server returned 400 for product creation
ERROR: ❌ Failed to create product: Product already exists
```

### Test 3: Invalid Product Name

**Steps:**

1. Try to create product with empty name or special characters

**Expected:**

```
ERROR: product_name is required
OR
WARNING: Server returned 400 for product creation
ERROR: ❌ Failed to create product: Invalid product name
```

## API Endpoint Reference (Visual AOI Server)

**Base URL:** <http://10.100.27.156:5000>

**API Docs:** <http://10.100.27.156:5000/apidocs/>

### Product Management Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/products` | GET | List all products |
| `/api/products/create` | POST | Create new product |
| `/api/products/{name}/config` | GET | Get product ROI config |
| `/api/products/{name}/rois` | POST | Update product ROIs |
| `/api/products/{name}/rois/{id}/golden_samples` | GET | Get golden samples |

### Session Management Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/session/create` | POST | Create inspection session |
| `/api/session/{id}/status` | GET | Get session status |
| `/api/session/{id}/inspect` | POST | Run inspection |
| `/api/sessions` | GET | List all sessions |

### System Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/health` | GET | Health check |
| `/api/status` | GET | Server status |
| `/api/initialize` | POST | Initialize AI models |

### Schema Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/schema/roi` | GET | ROI structure spec |
| `/api/schema/result` | GET | Result structure spec |
| `/api/schema/version` | GET | Schema versions |

## Best Practices

### Always Check Swagger Docs

When implementing API calls:

1. ✅ Check server Swagger docs: <http://10.100.27.156:5000/apidocs/>
2. ✅ Verify endpoint path exactly
3. ✅ Verify HTTP method (GET/POST/PUT/DELETE)
4. ✅ Check request body schema
5. ✅ Check response schema
6. ✅ Handle all documented error codes

### Example Workflow

```python
# 1. Check Swagger for endpoint
# Swagger shows: POST /api/products/create

# 2. Check request schema
# {
#   "product_name": "string",  // required
#   "description": "string"    // optional
# }

# 3. Implement exactly as documented
response = requests.post(
    f"{server_url}/api/products/create",
    json={
        "product_name": product_name,
        "description": description
    },
    timeout=30
)

# 4. Handle documented responses
if response.status_code == 200:
    # Success
    result = response.json()
elif response.status_code == 400:
    # Invalid input
    error = response.json()['error']
elif response.status_code == 500:
    # Server error
    error = response.json()['error']
```

## Related Documentation

- **Server API Docs:** <http://10.100.27.156:5000/apidocs/>
- **Swagger Spec:** <http://10.100.27.156:5000/apispec_1.json>
- **Client Architecture:** `docs/CLIENT_SERVER_ARCHITECTURE.md`
- **Error Handling:** `docs/TIMEOUT_AND_ERROR_HANDLING_FIX.md`

## Summary

### Problem

❌ POSTing to wrong endpoint `/api/products` (GET-only)  
❌ Getting 405 Method Not Allowed error  
❌ Cryptic JSON parse error message  

### Solution

✅ Fixed endpoint: `/api/products/create` (POST)  
✅ Removed unsupported `device_count` field  
✅ Matches server Swagger API specification  
✅ Better error messages from previous fix  

### Result

🎯 **Product creation works correctly**  
📚 **API calls match server documentation**  
🛡️ **Robust error handling**  

**File Modified:** `app.py` line 1522 (endpoint changed to `/api/products/create`)

Always refer to the server Swagger documentation when implementing API integrations! 🚀
