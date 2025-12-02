# ROI Editor - Legacy Config Loading Fix

**Date:** October 4, 2025  
**Issue:** Cannot load existing ROI configurations for products (404 error)  
**Status:** ✅ FIXED with Direct File Access Fallback

---

## Problem Description

### Symptoms
- Product **20003548** selected in ROI editor
- Click "Load Configuration" button
- Browser console shows:
  ```
  Failed to load resource: the server responded with a status of 404 (NOT FOUND)
  api/products/20003548/config
  ```
- Message: "No existing config for product '20003548' - starting fresh"
- **BUT** the configuration file actually exists on the server!

### Root Cause

**Server API Gap:**
- Server has config files at: `/home/jason_nguyen/visual-aoi-server/config/products/{product}/rois_config_{product}.json`
- Server API endpoint `GET /api/products/{product}/config` **not implemented**
- Returns 404 even when config file exists

**Client-Server Mismatch:**
- Client expects: `GET /api/products/20003548/config` → Returns ROI configuration
- Server reality: Endpoint doesn't exist or not implemented yet
- Result: Cannot load existing configurations

---

## Solution

### Fallback Mechanism

Added **direct filesystem access** fallback when server API returns 404:

**File:** `app.py`

**Function:** `get_product_config(product_name)`

**Logic Flow:**

1. **Try Server API First** (future-proof):
   ```python
   response = requests.get(f"{server_url}/api/products/{product_name}/config")
   if response.status_code == 200:
       return response.json()  # Use server API if available
   ```

2. **Fallback to Direct File Access** (current solution):
   ```python
   elif response.status_code == 404:
       # Read config file directly from server filesystem
       config_file = f"/home/jason_nguyen/visual-aoi-server/config/products/{product_name}/rois_config_{product_name}.json"
       
       if os.path.exists(config_file):
           with open(config_file, 'r') as f:
               config_data = json.load(f)
           
           # Convert legacy format to ROI editor format
           rois = convert_legacy_format(config_data)
           return jsonify({"rois": rois, "product_name": product_name})
   ```

### Legacy Format Conversion

**Input Format** (Legacy Server Config):
```json
[
  [
    1,              // [0] roi_id
    1,              // [1] device_id
    [3459, 2959, 4058, 3318],  // [2] coordinates [x1,y1,x2,y2]
    305,            // [3] focus
    1200,           // [4] exposure
    null,           // [5] threshold
    "opencv",       // [6] model
    0,              // [7] rotation
    1               // [8] roi_type (1=barcode, 2=compare, 3=ocr, 4=text)
  ],
  ...
]
```

**Output Format** (ROI Editor):
```json
{
  "product_name": "20003548",
  "rois": [
    {
      "roi_id": 1,
      "roi_type_name": "barcode",
      "device_id": 1,
      "coordinates": [3459, 2959, 4058, 3318],
      "ai_threshold": 0.8,
      "enabled": true,
      "notes": "Legacy config - Focus: 305, Exposure: 1200, Model: opencv"
    },
    ...
  ]
}
```

### Type Mapping

**Legacy roi_type Numbers → ROI Editor Names:**
```python
roi_type_map = {
    1: "barcode",   # Barcode detection
    2: "compare",   # Visual comparison
    3: "ocr",       # OCR text recognition
    4: "text"       # Text matching
}
```

---

## Implementation Details

### File Access Path

**Client and Server on Same Machine:**
- Client: `http://localhost:5100` (Flask)
- Server: `http://10.100.27.156:5000` (AOI Server)
- Both access: `/home/jason_nguyen/visual-aoi-server/config/products/`

**Config File Pattern:**
```
/home/jason_nguyen/visual-aoi-server/config/products/
├── 20003548/
│   └── rois_config_20003548.json  ← Target file
├── 20002810/
│   └── rois_config_20002810.json
└── ...
```

### Conversion Logic

**Code Implementation:**
```python
if isinstance(config_data, list):
    roi_type_map = {1: "barcode", 2: "compare", 3: "ocr", 4: "text"}
    
    rois = []
    for roi_data in config_data:
        if len(roi_data) >= 9:
            roi_type_num = roi_data[8]
            roi_type_name = roi_type_map.get(roi_type_num, "compare")
            
            roi = {
                "roi_id": roi_data[0],
                "roi_type_name": roi_type_name,
                "device_id": roi_data[1],
                "coordinates": roi_data[2],
                "ai_threshold": roi_data[5] if roi_data[5] is not None else 0.8,
                "enabled": True,
                "notes": f"Legacy config - Focus: {roi_data[3]}, Exposure: {roi_data[4]}, Model: {roi_data[6]}"
            }
            rois.append(roi)
```

### Error Handling

**Case 1: Server API Available (Future)**
```python
if response.status_code == 200:
    # Use server API response directly
    return jsonify(response.json()), 200
```

**Case 2: Server API 404 + File Exists (Current)**
```python
elif response.status_code == 404:
    if os.path.exists(config_file):
        # Read and convert legacy format
        return jsonify(converted_config), 200
```

**Case 3: No Config Found (New Product)**
```python
# Neither server API nor file found
return jsonify({"error": "Configuration not found", "rois": []}), 404
```

**Case 4: Server Error**
```python
else:
    return jsonify({"error": f"Server error: {response.status_code}"}), response.status_code
```

---

## Results

### Before Fix

**API Response:**
```json
{
  "error": "Configuration not found",
  "rois": []
}
```

**ROI Editor:**
- ❌ Shows: "No existing config found. Starting with empty configuration."
- ❌ Empty canvas
- ❌ 0 ROIs loaded

### After Fix

**API Response:**
```json
{
  "product_name": "20003548",
  "rois": [
    {
      "roi_id": 1,
      "roi_type_name": "barcode",
      "device_id": 1,
      "coordinates": [3459, 2959, 4058, 3318],
      "ai_threshold": 0.8,
      "enabled": true,
      "notes": "Legacy config - Focus: 305, Exposure: 1200, Model: opencv"
    },
    {
      "roi_id": 2,
      "roi_type_name": "compare",
      "device_id": 1,
      "coordinates": [1691, 2959, 2572, 3473],
      "ai_threshold": 0.8,
      "enabled": true,
      "notes": "Legacy config - Focus: 305, Exposure: 1200, Model: opencv"
    },
    ... 4 more ROIs ...
  ]
}
```

**ROI Editor:**
- ✅ Shows: "Loaded 6 ROIs"
- ✅ ROIs displayed on canvas
- ✅ ROI list populated
- ✅ Can edit/modify existing ROIs

### Example: Product 20003548

**Configuration Loaded:**
- ✅ **6 ROIs** total
- ✅ **3 devices** (device 1, 2, 3)
- ✅ **ROI Types:**
  - 1x Barcode (ROI 1)
  - 4x Compare (ROI 2, 3, 4, 6)
  - 1x OCR (ROI 5)

**Legacy Metadata Preserved:**
- Focus: 305
- Exposure: 1200
- Models: opencv, mobilenet
- Thresholds: 0.8, 0.93

---

## Testing

### Verification Steps

1. **Open ROI Editor:**
   ```
   http://localhost:5100/roi-editor
   ```

2. **Connect to Server:**
   - Status shows: "✓ Connected"

3. **Select Product:**
   - Choose: "20003548"

4. **Load Configuration:**
   - Click: "Load Configuration" button
   - Expected: "Loaded 6 ROIs" notification (green)

5. **Verify ROIs Loaded:**
   - ROI list shows 6 items
   - Canvas displays ROI rectangles
   - Properties panel shows ROI details

### Backend Verification

**Test Config Endpoint:**
```bash
curl http://localhost:5100/api/products/20003548/config | jq '.'
```

**Expected Response:**
```json
{
  "product_name": "20003548",
  "rois": [
    { "roi_id": 1, "roi_type_name": "barcode", ... },
    { "roi_id": 2, "roi_type_name": "compare", ... },
    { "roi_id": 3, "roi_type_name": "compare", ... },
    { "roi_id": 4, "roi_type_name": "compare", ... },
    { "roi_id": 5, "roi_type_name": "ocr", ... },
    { "roi_id": 6, "roi_type_name": "compare", ... }
  ]
}
```

**Count ROIs:**
```bash
curl -s http://localhost:5100/api/products/20003548/config | jq '.rois | length'
# Output: 6
```

### Test Other Products

```bash
# Test product 20002810
curl -s http://localhost:5100/api/products/20002810/config | jq '.rois | length'

# Test product test_ocr_sample
curl -s http://localhost:5100/api/products/test_ocr_sample/config | jq '.rois | length'

# Test non-existent product
curl -s http://localhost:5100/api/products/nonexistent/config
# Expected: {"error": "Configuration not found", "rois": []}
```

---

## Future Improvements

### 1. Server API Implementation

**Recommended:** Implement proper server endpoint:

```python
# Server side (visual-aoi-server)
@app.route("/api/products/<product_name>/config", methods=["GET"])
def get_product_config(product_name):
    config = load_product_config(product_name)
    if config:
        return jsonify(convert_to_v2_format(config)), 200
    else:
        return jsonify({"error": "Not found"}), 404
```

**Benefits:**
- Proper API architecture
- Centralized config management
- Supports future enhancements
- No filesystem coupling

### 2. Config Format Migration

**Option A:** Keep legacy format, convert on-the-fly (current solution)
- ✅ Works with existing configs
- ✅ No migration needed
- ❌ Conversion overhead
- ❌ Limited metadata

**Option B:** Migrate to new format
- ✅ Rich metadata support
- ✅ Easier to edit
- ✅ Better validation
- ❌ Requires migration script
- ❌ May break existing tools

**Recommendation:** Keep current solution until server API ready

### 3. Caching

Add config caching to reduce file reads:

```python
config_cache = {}

def get_product_config_cached(product_name):
    if product_name not in config_cache:
        config_cache[product_name] = load_from_file(product_name)
    return config_cache[product_name]
```

### 4. Validation

Add schema validation for loaded configs:

```python
def validate_roi_config(config):
    required_fields = ["roi_id", "roi_type_name", "device_id", "coordinates"]
    for roi in config.get("rois", []):
        for field in required_fields:
            if field not in roi:
                raise ValueError(f"Missing field: {field}")
```

---

## Related Issues

### Issue: ROI Type Mapping

**Legacy Types:**
- 1 = Barcode
- 2 = Compare
- 3 = OCR
- 4 = Text

**ROI Editor Types:**
- "barcode"
- "compare"
- "ocr"
- "text"

**Solution:** Type mapping dictionary in conversion logic

### Issue: Missing Metadata

**Legacy Format Missing:**
- `enabled` flag
- `notes` field
- `ai_threshold` (sometimes null)

**Solution:**
- Default `enabled = true`
- Store legacy metadata in `notes`
- Default `ai_threshold = 0.8`

### Issue: Coordinate Format

**Both Use Same Format:** ✅
- Legacy: `[x1, y1, x2, y2]`
- ROI Editor: `[x1, y1, x2, y2]`
- No conversion needed!

---

## Summary

**Root Cause:** Server API endpoint `GET /api/products/{product}/config` not implemented, causing 404 errors even when config files exist.

**Solution:** Added direct filesystem access fallback that reads legacy config files and converts them to ROI editor format.

**Result:** Can now load existing product configurations with all ROIs, types, and metadata properly displayed in the ROI editor.

**Verification:** Tested with product 20003548 - successfully loaded 6 ROIs with correct types (barcode, compare, ocr) and coordinates.

**Files Modified:**
- `app.py` - Added fallback logic and legacy format conversion in `get_product_config()`

**Related Documentation:**
- `docs/ROI_EDITOR_CONNECTION_FIX.md` - Server connection fix
- `docs/ROI_EDITOR_CREATE_PRODUCT_FEATURE.md` - Product creation feature
