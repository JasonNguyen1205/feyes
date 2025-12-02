# New Initialization Flow

**Date:** October 9, 2025  
**Change Type:** Architecture Improvement  
**Impact:** Better user experience, product-specific camera optimization

## Overview

Restructured the client initialization flow to ensure camera is initialized with product-specific settings BEFORE session creation. This improves setup clarity and ensures optimal camera configuration from the start.

---

## Old Flow (Before)

```
1. Connect to Server
2. Initialize Camera (generic/default settings)
3. Select Product
4. Create Session (re-initializes camera with product settings)
```

**Problems:**

- Camera initialized twice (wasteful)
- Default camera settings used initially (not optimal)
- Confusing user experience (why initialize before selecting product?)
- Product selection seemed arbitrary

---

## New Flow (After)

```
1. Connect to Server
2. Select/Create Product
3. Initialize Camera (with product-specific settings)
4. Create Session (camera already configured)
```

**Benefits:**

- Camera initialized ONCE with optimal settings
- Clear sequential workflow
- Product selection drives camera configuration
- Better user guidance with step numbers
- No duplicate initialization

---

## Technical Changes

### Backend Changes (app.py)

#### 1. Enhanced `/api/camera/initialize` Endpoint

**Before:**

```python
@app.route("/api/camera/initialize", methods=["POST"])
def init_camera():
    data = request.get_json(silent=True) or {}
    serial = data.get("serial")
    
    initialized = tis_camera.initialize_camera(serial=serial)
    # Always used default settings
```

**After:**

```python
@app.route("/api/camera/initialize", methods=["POST"])
def init_camera():
    data = request.get_json(silent=True) or {}
    serial = data.get("serial")
    product_name = data.get("product_name")  # NEW: Optional product
    
    # Initialize hardware
    initialized = tis_camera.initialize_camera(serial=serial)
    
    # NEW: Apply product-specific settings if product provided
    if product_name:
        roi_groups = fetch_roi_groups(product_name)
        if roi_groups:
            # Get first ROI group settings
            first_group_key = next(iter(roi_groups.keys()))
            focus, exposure = first_group_key.split(',')
            
            # Apply optimal settings
            tis_camera.set_camera_properties(
                focus=int(focus), 
                exposure_time=int(exposure)
            )
```

**Request Schema:**

```json
{
  "serial": "12345678",           // Required: Camera serial number
  "product_name": "20003548"      // Optional: For product-specific settings
}
```

**Response Schema:**

```json
{
  "status": "initialized",
  "serial": "12345678",
  "product": "20003548",
  "settings": {
    "focus": 450,
    "exposure": 5000
  }
}
```

#### 2. Modified `/api/session` Creation Endpoint

**Before:**

```python
@app.route("/api/session", methods=["POST"])
def create_session():
    # ... create session with server ...
    
    # Initialize camera with product settings (DUPLICATE)
    if state.camera_initialized and roi_groups:
        initialize_camera_for_product(product_name, roi_groups)
```

**After:**

```python
@app.route("/api/session", methods=["POST"])
def create_session():
    # NEW: Validate camera already initialized
    if not state.camera_initialized:
        return jsonify({
            "error": "Camera must be initialized before creating session",
            "hint": "Please initialize camera with product settings first"
        }), 409
    
    # ... create session with server ...
    
    # Load ROI groups (camera already configured)
    roi_groups = fetch_roi_groups(product_name)
```

**Key Change:** Session creation now **validates** camera is ready instead of initializing it.

---

### Frontend Changes (professional_index.html)

#### 1. UI Section Reordering

**Before:**

```html
<!-- Old order -->
<div id="serverSection">Server Connection</div>
<div id="cameraSection">Camera Controls</div>
<div id="sessionSection">Session Management (with product select)</div>
```

**After:**

```html
<!-- New order with step numbers -->
<div id="serverSection">Step 1: Server Connection</div>
<div id="productSection">Step 2: Product Selection</div>
<div id="cameraSection">Step 3: Camera Initialization</div>
<div id="sessionSection">Step 4: Session Management</div>
```

#### 2. Updated `initializeCamera()` Function

**Before:**

```javascript
async function initializeCamera() {
    const cameraSerial = document.getElementById('cameraSelect').value;
    
    // Initialized with default settings
    await apiCall('POST', '/api/camera/initialize', { serial: cameraSerial });
}
```

**After:**

```javascript
async function initializeCamera() {
    const cameraSerial = document.getElementById('cameraSelect').value;
    
    // NEW: Validate prerequisites
    if (!appState.connected) {
        showNotification('Please connect to server first', 'warning');
        return;
    }
    
    const product = document.getElementById('productSelect').value;
    if (!product) {
        showNotification('Please select a product first', 'warning');
        return;
    }
    
    // NEW: Pass product_name for optimal settings
    const payload = { 
        serial: cameraSerial,
        product_name: product
    };
    
    await apiCall('POST', '/api/camera/initialize', payload);
}
```

#### 3. Enhanced `createSession()` Validation

**Before:**

```javascript
async function createSession() {
    const product = document.getElementById('productSelect').value;
    
    // Just created session
    await apiCall('POST', '/api/session', { product });
}
```

**After:**

```javascript
async function createSession() {
    const product = document.getElementById('productSelect').value;
    
    // NEW: Validate flow order
    if (!appState.connected) {
        showNotification('Please connect to server first', 'warning');
        return;
    }
    
    if (!appState.cameraInitialized) {
        showNotification('Please initialize camera with product settings first', 'warning');
        return;
    }
    
    // NEW: Verify same product
    if (appState.sessionProduct !== product) {
        showNotification('Camera initialized for different product', 'warning');
        return;
    }
    
    await apiCall('POST', '/api/session', { product });
}
```

---

## User Experience

### Visual Flow Indicators

1. **Step Numbers:** Each section now shows step number (Step 1, Step 2, etc.)
2. **Helper Text:**
   - Product section: "Select a product to configure camera with optimal settings"
   - Camera section: "Camera will be initialized with optimal settings for selected product"
3. **Clear Error Messages:** Guides users through correct sequence

### Example User Journey

```
User Action                     → System Response
─────────────────────────────────────────────────────────────
1. Enter server URL             → 
2. Click "Connect"              → ✓ Connected, products loaded
3. Select product "20003548"    → Product selected
4. Click "Initialize Camera"    → ✓ Camera configured (F:450, E:5000)
5. Click "Create Session"       → ✓ Session ready for inspection
6. Click "Perform Inspection"   → Inspection runs with optimal settings
```

### Error Prevention

```
Scenario: User tries to initialize camera without product
Response: "Please select a product first"

Scenario: User tries to create session without camera
Response: "Please initialize camera with product settings first"

Scenario: User changes product after camera init
Response: "Camera initialized for different product. Please re-initialize."
```

---

## Configuration Details

### Product-Specific Camera Settings

When initializing camera with product, the system:

1. **Fetches ROI Groups:** Loads all ROI groups for product from server
2. **Selects First Group:** Uses first ROI group as initial settings
3. **Applies Settings:** Sets camera focus and exposure immediately
4. **Stores Settings:** Caches settings in `state.first_roi_group_settings`

**Example ROI Group Structure:**

```json
{
  "450,5000": {
    "focus": 450,
    "exposure": 5000,
    "rois": [
      {"roi_id": 1, "device_id": 1, ...},
      {"roi_id": 2, "device_id": 1, ...}
    ]
  },
  "450,8000": {
    "focus": 450,
    "exposure": 8000,
    "rois": [...]
  }
}
```

**Key:** `"focus,exposure"` (e.g., `"450,5000"`)  
**First Group:** Used for initial camera setup  
**Other Groups:** Applied dynamically during multi-ROI inspection

### Default Settings (New Products)

If product has no ROI groups or initialization fails:

- Camera uses default hardware settings
- User can manually adjust via TIS properties
- Settings can be configured later via ROI Editor

---

## State Management

### Backend State (app.py)

```python
class State:
    connected: bool = False               # Server connection
    camera_initialized: bool = False      # Camera ready
    session_id: Optional[str] = None      # Active session ID
    session_product: Optional[str] = None # Current product
    first_roi_group_settings: Optional[dict] = None  # Cached settings
```

**Flow State Transitions:**

```
connected=True → product selected → camera_initialized=True → session_id set
```

### Frontend State (professional_index.html)

```javascript
const appState = {
    connected: false,           // Server connected
    cameraInitialized: false,   // Camera ready
    sessionActive: false,       // Session created
    sessionProduct: null,       // Product name for validation
    serverUrl: null            // Server endpoint
};
```

---

## Testing Checklist

### Happy Path

- [x] Connect to server → products loaded
- [x] Select product → camera can be initialized
- [x] Initialize camera → receives product settings
- [x] Create session → validation passes
- [x] Perform inspection → uses correct settings

### Error Handling

- [x] Initialize camera without product → shows error
- [x] Create session without camera → shows error
- [x] Change product after camera init → warns user
- [x] Disconnect server → resets camera state

### Edge Cases

- [x] New product (no ROI groups) → uses defaults
- [x] Invalid product → falls back to defaults
- [x] Server disconnection during flow → proper cleanup
- [x] Multiple products testing → settings update correctly

---

## Migration Notes

### For Users

**No action required.** The new flow is self-explanatory with step numbers and helper text.

**Key Change:** Select product BEFORE initializing camera (step numbers guide you).

### For Developers

**Breaking Changes:**

- `/api/camera/initialize` now accepts optional `product_name` parameter
- `/api/session` now requires camera to be initialized (returns 409 if not)

**Backward Compatibility:**

- If `product_name` not provided to camera init, uses default settings (old behavior)
- Existing API clients without product parameter still work

**Update Your Code:**

```python
# OLD WAY (still works but not optimal)
response = requests.post('/api/camera/initialize', json={'serial': '12345'})

# NEW WAY (optimal with product settings)
response = requests.post('/api/camera/initialize', json={
    'serial': '12345',
    'product_name': '20003548'
})
```

---

## Related Files

**Backend:**

- `app.py` lines 1057-1133 (camera init endpoint)
- `app.py` lines 946-1021 (session creation)
- `app.py` lines 1292-1327 (helper function kept for reference)

**Frontend:**

- `templates/professional_index.html` lines 30-143 (UI sections)
- `templates/professional_index.html` lines 617-674 (initializeCamera)
- `templates/professional_index.html` lines 746-800 (createSession)

**Documentation:**

- `docs/NEW_INITIALIZATION_FLOW.md` (this file)
- `.github/copilot-instructions.md` (updated with new flow)

---

## Future Enhancements

1. **Auto-detect Product:** Use barcode scanning to auto-select product
2. **Setting Preview:** Show camera settings before applying
3. **Profile Management:** Save/load custom initialization profiles
4. **Validation Tests:** Add automated E2E tests for flow

---

## Summary

✅ Camera now initialized with product-specific optimal settings from the start  
✅ Clear step-by-step workflow (1→2→3→4)  
✅ Better error prevention with validation guards  
✅ No duplicate camera initialization  
✅ Improved user experience with helper text  

The new flow ensures users follow the logical sequence: Connect → Choose Product → Initialize Camera → Create Session → Inspect.
