# Professional Camera Initialization System

## Overview

The Visual AOI Client now implements a professional camera initialization system that handles webpage refreshes gracefully, automatically resets pipelines when needed, and provides comprehensive status checking and logging.

## Key Features

✅ **Status Checking on Page Load** - Detects existing camera pipelines from previous sessions  
✅ **Automatic Pipeline Reset** - Cleans up existing pipelines before re-initialization  
✅ **Professional Logging** - Visual separators and step-by-step progress tracking  
✅ **Pipeline State Display** - Shows GStreamer pipeline state (NULL/READY/PAUSED/PLAYING)  
✅ **Webpage Refresh Handling** - No manual disconnect needed when refreshing page  

---

## Architecture

### Backend Components

#### 1. Camera Status Checking (`src/camera.py`)

```python
def get_camera_status():
    """Get current camera and pipeline status.
    
    Returns:
        dict: {
            'initialized': bool,
            'pipeline_active': bool,
            'pipeline_state': str,  # NULL/READY/PAUSED/PLAYING
            'serial': str or None
        }
    """
```

**Purpose:** Check if camera is initialized and get current pipeline state  
**Location:** `src/camera.py`, lines ~710-760  
**Returns:** Dictionary with camera/pipeline status  

#### 2. Pipeline Reset (`src/camera.py`)

```python
def reset_camera_pipeline():
    """Reset camera pipeline - stop existing pipeline and prepare for reinitialization.
    
    Steps:
        1. Check if Tis exists
        2. Get current pipeline state
        3. Stop pipeline if active
        4. Wait 0.5s for graceful shutdown
        5. Clear global Tis reference
    
    Returns:
        bool: True if reset successful
    """
```

**Purpose:** Clean up existing pipeline for fresh initialization  
**Location:** `src/camera.py`, lines ~763-810  
**Wait Time:** 0.5 seconds for pipeline to stop completely  

#### 3. Enhanced Initialization Endpoint (`app.py`)

```python
@app.route("/api/camera/initialize", methods=["POST"])
def init_camera():
    """Professional 5-step initialization flow.
    
    Steps:
        1. Check existing camera status
        2. Reset pipeline if already initialized (webpage refresh)
        3. Initialize camera hardware
        4. Apply product-specific settings or defaults
        5. Verify final pipeline state
    
    Parameters (JSON body):
        - serial (str): Camera serial number
        - product_name (str, optional): Product for settings
        - force_reset (bool, default True): Force pipeline reset
    
    Returns:
        JSON: {
            'status': 'initialized',
            'serial': str,
            'product': str (optional),
            'settings': dict (optional),
            'pipeline_state': str
        }
    """
```

**Purpose:** Initialize camera with professional flow  
**Location:** `app.py`, lines ~1120-1235  
**Logging:** Visual separators (=== lines) and step markers  

### API Endpoints

#### GET `/api/camera/status`

**Description:** Get current camera and pipeline status  
**Parameters:** None  
**Returns:**

```json
{
  "initialized": false,
  "pipeline_active": false,
  "pipeline_state": "NONE",
  "serial": null,
  "app_initialized": false,
  "app_serial": null
}
```

**Status Codes:**

- `200 OK` - Status retrieved successfully

**Usage:**

```javascript
const response = await fetch('/api/camera/status');
const status = await response.json();
console.log('Camera status:', status);
```

#### POST `/api/camera/reset`

**Description:** Reset camera pipeline (stop and clear)  
**Parameters:** None  
**Returns:**

```json
{
  "status": "reset",
  "message": "Camera pipeline reset successfully"
}
```

**Status Codes:**

- `200 OK` - Reset successful
- `500 Internal Server Error` - Reset failed

**Side Effects:**

- Stops GStreamer pipeline
- Clears global Tis reference
- Clears application state (camera_initialized, camera_serial, live_view_active)

**Usage:**

```javascript
const response = await fetch('/api/camera/reset', { method: 'POST' });
const result = await response.json();
console.log('Reset result:', result);
```

#### POST `/api/camera/initialize`

**Description:** Initialize camera with professional 5-step flow  
**Parameters (JSON body):**

```json
{
  "serial": "12345678",
  "product_name": "20003548",
  "force_reset": true
}
```

**Returns:**

```json
{
  "status": "initialized",
  "serial": "12345678",
  "product": "20003548",
  "settings": {
    "focus": 305,
    "exposure": 1200
  },
  "pipeline_state": "PLAYING"
}
```

**Status Codes:**

- `200 OK` - Initialization successful
- `500 Internal Server Error` - Initialization failed

**Usage:**

```javascript
const response = await fetch('/api/camera/initialize', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    serial: '12345678',
    product_name: '20003548',
    force_reset: true
  })
});
const result = await response.json();
console.log('Initialization result:', result);
```

---

### Frontend Components

#### 1. Page Load Status Check (`templates/professional_index.html`)

**Location:** DOMContentLoaded event handler, lines ~2342-2380  
**Purpose:** Check camera status on page load to detect existing pipelines  

**Implementation:**

```javascript
document.addEventListener('DOMContentLoaded', async function () {
    // ... existing code ...
    
    // NEW: Check camera status on page load
    try {
        const statusResponse = await fetch('/api/camera/status');
        if (statusResponse.ok) {
            const cameraStatus = await statusResponse.json();
            
            console.log('📷 Camera status on page load:', cameraStatus);
            
            if (cameraStatus.app_initialized) {
                appState.cameraInitialized = true;
                console.log(`⚠️  Camera pipeline active from previous session (State: ${cameraStatus.pipeline_state})`);
                
                const statusMsg = `Pipeline active (${cameraStatus.pipeline_state})`;
                updateCameraStatus('warning', statusMsg);
                updateSystemStatus('Camera pipeline active - re-initialize to reset');
            } else {
                console.log('✓ No active camera pipeline detected');
                updateCameraStatus('disconnected', 'Camera not initialized');
            }
        }
    } catch (error) {
        console.error('Failed to check camera status:', error);
    }
    
    // ... rest of initialization ...
});
```

**Console Output Examples:**

**Fresh Page Load (No Camera):**

```
📷 Camera status on page load: {initialized: false, pipeline_active: false, pipeline_state: 'NONE', ...}
✓ No active camera pipeline detected
```

**Page Refresh (Camera Active):**

```
📷 Camera status on page load: {initialized: true, pipeline_active: true, pipeline_state: 'PLAYING', ...}
⚠️  Camera pipeline active from previous session (State: PLAYING)
```

#### 2. Enhanced Camera Initialization (`templates/professional_index.html`)

**Location:** `initializeCamera()` function, lines ~625-705  
**Purpose:** Initialize camera with automatic reset and professional logging  

**Implementation:**

```javascript
async function initializeCamera() {
    // ... validation ...
    
    try {
        // PROFESSIONAL CAMERA INITIALIZATION FLOW
        console.log('=' .repeat(70));
        console.log('📷 CAMERA INITIALIZATION REQUEST');
        
        // Step 1: Check existing camera status
        updateSystemStatus('Checking camera status...');
        const statusResponse = await fetch('/api/camera/status');
        const cameraStatus = await statusResponse.json();
        console.log(`  Current Status:`, cameraStatus);
        
        // Step 2: Reset pipeline if already initialized
        if (cameraStatus.app_initialized || cameraStatus.pipeline_active) {
            console.log(`⚠️  Camera already initialized - resetting pipeline (State: ${cameraStatus.pipeline_state})`);
            updateSystemStatus('Resetting camera pipeline...');
            updateCameraStatus('warning', 'Resetting pipeline...');
            
            const resetResponse = await fetch('/api/camera/reset', { method: 'POST' });
            if (!resetResponse.ok) {
                throw new Error('Failed to reset camera pipeline');
            }
            
            console.log('✓ Pipeline reset successful');
            await new Promise(resolve => setTimeout(resolve, 500)); // Wait 0.5s
        }
        
        // Step 3: Initialize camera
        updateSystemStatus('Initializing camera with product settings...');
        console.log(`🔧 Initializing camera hardware with product: ${product}`);
        
        const payload = { 
            serial: cameraSerial,
            product_name: product,
            force_reset: true
        };
        
        const result = await apiCall('POST', '/api/camera/initialize', payload);
        
        // Step 4: Display results
        let statusMsg = 'Camera initialized';
        if (result.product) {
            statusMsg += ` for ${result.product}`;
            if (result.settings) {
                statusMsg += ` (F:${result.settings.focus}, E:${result.settings.exposure})`;
            }
        }
        if (result.pipeline_state) {
            statusMsg += ` - Pipeline: ${result.pipeline_state}`;
        }
        
        updateCameraStatus('connected', statusMsg);
        appState.cameraInitialized = true;
        
        console.log('✅ Camera initialization successful:', result);
        console.log('=' .repeat(70));
    } catch (error) {
        console.error('❌ Camera initialization error:', error);
        console.log('=' .repeat(70));
    }
}
```

**Console Output Example:**

```
======================================================================
📷 CAMERA INITIALIZATION REQUEST
  Current Status: {app_initialized: true, pipeline_active: true, pipeline_state: 'PLAYING', ...}
⚠️  Camera already initialized - resetting pipeline (State: PLAYING)
✓ Pipeline reset successful
🔧 Initializing camera hardware with product: 20003548
✅ Camera initialization successful: {status: 'initialized', serial: '12345678', ...}
======================================================================
```

---

## User Workflows

### Scenario 1: Fresh Page Load (No Camera Initialized)

1. **Page Load:** Browser loads `professional_index.html`
2. **Status Check:** GET `/api/camera/status` → Returns `app_initialized: false`
3. **Console Output:** `✓ No active camera pipeline detected`
4. **UI Status:** "Camera not initialized"
5. **User Action:** Clicks "Initialize Camera"
6. **Initialization:** POST `/api/camera/initialize` with product settings
7. **Result:** Camera initialized successfully with pipeline state PLAYING

**Expected UI:**

```
Camera Status: 🔴 Camera not initialized
→ User clicks Initialize
Camera Status: 🟢 Camera initialized for 20003548 (F:305, E:1200) - Pipeline: PLAYING
```

### Scenario 2: Webpage Refresh (Camera Already Active)

1. **Page Refresh:** User presses F5 or clicks refresh button
2. **Status Check:** GET `/api/camera/status` → Returns `app_initialized: true, pipeline_state: 'PLAYING'`
3. **Console Output:** `⚠️  Camera pipeline active from previous session (State: PLAYING)`
4. **UI Status:** "Pipeline active (PLAYING)"
5. **User Action:** Clicks "Initialize Camera"
6. **Auto-Reset:** POST `/api/camera/reset` → Stops existing pipeline
7. **Wait Period:** 0.5 seconds for graceful shutdown
8. **Initialization:** POST `/api/camera/initialize` with fresh pipeline
9. **Result:** Camera initialized successfully without errors

**Expected UI:**

```
Camera Status: ⚠️  Pipeline active (PLAYING)
→ User clicks Initialize
Camera Status: ⚠️  Resetting pipeline...
Camera Status: 🟢 Camera initialized for 20003548 (F:305, E:1200) - Pipeline: PLAYING
```

### Scenario 3: Multiple Webpage Refreshes

1. **First Refresh:** Pipeline detected → Auto-reset → Re-initialize → Success
2. **Second Refresh:** Pipeline detected → Auto-reset → Re-initialize → Success
3. **Third Refresh:** Pipeline detected → Auto-reset → Re-initialize → Success

**Key Benefit:** Each refresh automatically cleans up and re-initializes without errors

---

## GStreamer Pipeline States

The system tracks and displays GStreamer pipeline states for transparency:

| State | Code | Description | When It Occurs |
|-------|------|-------------|----------------|
| **NONE** | - | No pipeline exists | Camera not initialized |
| **NULL** | 1 | Pipeline created but not configured | Initial creation |
| **READY** | 2 | Resources allocated, not streaming | After configuration |
| **PAUSED** | 3 | Streaming but paused | Rarely used in this app |
| **PLAYING** | 4 | Active streaming | Normal operation |

**Normal Flow:**

```
NONE → NULL → READY → PLAYING
```

**Reset Flow:**

```
PLAYING → (stop_pipeline) → NONE
```

---

## Logging Examples

### Backend Logs (Flask Console)

**Successful Initialization:**

```
======================================================================
CAMERA INITIALIZATION REQUEST
  Current Status: {'initialized': False, 'pipeline_active': False, 'pipeline_state': 'NONE', 'serial': None}
Initializing camera hardware...
Camera object created successfully
TIS camera initialized successfully with serial: 12345678
✓ Camera initialized successfully
Product settings loaded: focus=305, exposure=1200
Final Status: {'initialized': True, 'pipeline_active': True, 'pipeline_state': 'PLAYING', 'serial': '12345678'}
======================================================================
```

**Webpage Refresh with Auto-Reset:**

```
======================================================================
CAMERA INITIALIZATION REQUEST
  Current Status: {'initialized': True, 'pipeline_active': True, 'pipeline_state': 'PLAYING', 'serial': '12345678'}
⚠ Camera already initialized - resetting pipeline
Pipeline stopped successfully
Global Tis reference cleared
✓ Pipeline reset successful
Initializing camera hardware...
Camera object created successfully
TIS camera initialized successfully with serial: 12345678
✓ Camera initialized successfully
Final Status: {'initialized': True, 'pipeline_active': True, 'pipeline_state': 'PLAYING', 'serial': '12345678'}
======================================================================
```

### Frontend Logs (Browser Console)

**Page Load with Active Pipeline:**

```
📷 Camera status on page load: {app_initialized: true, pipeline_active: true, pipeline_state: "PLAYING", serial: "12345678"}
⚠️  Camera pipeline active from previous session (State: PLAYING)
```

**Initialization Flow:**

```
======================================================================
📷 CAMERA INITIALIZATION REQUEST
  Current Status: {app_initialized: true, pipeline_active: true, pipeline_state: "PLAYING"}
⚠️  Camera already initialized - resetting pipeline (State: PLAYING)
✓ Pipeline reset successful
🔧 Initializing camera hardware with product: 20003548
✅ Camera initialization successful: {status: "initialized", serial: "12345678", product: "20003548", ...}
======================================================================
```

---

## Error Handling

### Backend Error Scenarios

**Camera Hardware Failure:**

```python
try:
    initialized = tis_camera.initialize_camera(serial=serial)
    if not initialized:
        logger.error("❌ Camera initialization failed")
        return jsonify({"error": "Failed to initialize camera"}), 500
except Exception as e:
    logger.error(f"Camera exception: {str(e)}")
    return jsonify({"error": str(e)}), 500
```

**Pipeline Reset Failure:**

```python
reset_success = tis_camera.reset_camera_pipeline()
if not reset_success:
    logger.warning("Pipeline reset returned false - continuing anyway")
```

### Frontend Error Scenarios

**Status Check Failure:**

```javascript
try {
    const statusResponse = await fetch('/api/camera/status');
    if (statusResponse.ok) {
        // ... handle status ...
    }
} catch (error) {
    console.error('Failed to check camera status:', error);
    // Non-critical error - continue with normal startup
}
```

**Reset Failure:**

```javascript
const resetResponse = await fetch('/api/camera/reset', { method: 'POST' });
if (!resetResponse.ok) {
    throw new Error('Failed to reset camera pipeline');
}
```

**Initialization Failure:**

```javascript
catch (error) {
    updateCameraStatus('disconnected', `Camera initialization failed: ${error.message}`);
    updateSystemStatus('Camera initialization failed');
    showNotification(`Camera initialization failed: ${error.message}`, 'error');
    console.error('❌ Camera initialization error:', error);
}
```

---

## Testing

### Manual Testing Checklist

- [ ] **Fresh Page Load**
  - Open application in browser
  - Check console for "No active camera pipeline detected"
  - Verify camera status shows "Camera not initialized"
  - Initialize camera
  - Verify initialization successful

- [ ] **Single Webpage Refresh**
  - Initialize camera
  - Wait for pipeline to reach PLAYING state
  - Press F5 to refresh page
  - Check console for "Camera pipeline active from previous session"
  - Verify camera status shows warning
  - Re-initialize camera
  - Verify no errors and successful re-initialization

- [ ] **Multiple Webpage Refreshes**
  - Repeat refresh test 5 times
  - Verify each refresh auto-resets and re-initializes successfully
  - Check for memory leaks or resource issues

- [ ] **Product-Specific Settings**
  - Initialize with product "20003548"
  - Verify settings (F:305, E:1200) applied
  - Check pipeline state shows PLAYING
  - Verify status message shows all details

- [ ] **Error Recovery**
  - Disconnect camera physically (if possible)
  - Attempt initialization
  - Verify error message displayed
  - Reconnect camera
  - Verify successful initialization after reconnect

### Automated Testing (Future)

```python
# Test camera status checking
def test_camera_status():
    response = client.get('/api/camera/status')
    assert response.status_code == 200
    data = response.get_json()
    assert 'initialized' in data
    assert 'pipeline_active' in data
    assert 'pipeline_state' in data

# Test camera reset
def test_camera_reset():
    response = client.post('/api/camera/reset')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'reset'

# Test initialization with reset
def test_initialization_flow():
    # Initialize first time
    response1 = client.post('/api/camera/initialize', json={'serial': '12345678'})
    assert response1.status_code == 200
    
    # Initialize again (should auto-reset)
    response2 = client.post('/api/camera/initialize', json={'serial': '12345678', 'force_reset': True})
    assert response2.status_code == 200
    data = response2.get_json()
    assert data['pipeline_state'] == 'PLAYING'
```

---

## Troubleshooting

### Issue: Pipeline State Shows NULL After Initialization

**Symptoms:** Camera initializes but pipeline state is NULL instead of PLAYING

**Solution:**

1. Check if `Tis.Start_pipeline()` was called
2. Verify 2-second stabilization delay after starting pipeline
3. Check for GStreamer errors in backend logs
4. Verify camera settings (focus, exposure) are valid

**Code to Check:**

```python
# In src/camera.py
if not Tis.Start_pipeline():
    logger.error("Failed to start camera pipeline")
    return False
time.sleep(2)  # CRITICAL: Wait for pipeline to stabilize
```

### Issue: Multiple Pipelines Active After Refresh

**Symptoms:** Camera initialization fails with "pipeline already active" error

**Solution:**

1. Verify auto-reset is working (check console logs)
2. Ensure 0.5s wait period after reset
3. Check if `Tis.stop_pipeline()` is being called
4. Clear global `Tis` reference after stopping

**Code to Check:**

```python
# In src/camera.py
def reset_camera_pipeline():
    global Tis
    if Tis is not None:
        Tis.stop_pipeline()
        time.sleep(0.5)  # CRITICAL: Wait for pipeline to stop
    Tis = None
```

### Issue: Status Check Fails on Page Load

**Symptoms:** Console shows "Failed to check camera status" error

**Solution:**

1. Verify Flask backend is running
2. Check if `/api/camera/status` endpoint exists
3. Verify CORS settings if accessing from different origin
4. Check for network errors in browser DevTools

**Code to Check:**

```javascript
// In professional_index.html
try {
    const statusResponse = await fetch('/api/camera/status');
    if (statusResponse.ok) {
        const cameraStatus = await statusResponse.json();
        console.log('Status:', cameraStatus);
    } else {
        console.error('Status check failed:', statusResponse.status);
    }
} catch (error) {
    console.error('Network error:', error);
}
```

### Issue: UI Status Not Updating After Initialization

**Symptoms:** Camera initializes successfully but UI still shows "Camera not initialized"

**Solution:**

1. Verify `updateCameraStatus()` is called after initialization
2. Check if `appState.cameraInitialized` is set to true
3. Verify status message includes pipeline state
4. Check browser console for JavaScript errors

**Code to Check:**

```javascript
// In professional_index.html
updateCameraStatus('connected', statusMsg);
appState.cameraInitialized = true;
console.log('Camera initialized:', result);
```

---

## Best Practices

### For Developers

1. **Always Check Status Before Operations**

   ```javascript
   const status = await fetch('/api/camera/status');
   if (status.app_initialized) {
       // Reset before re-initializing
       await fetch('/api/camera/reset', { method: 'POST' });
   }
   ```

2. **Wait After Pipeline Operations**

   ```python
   Tis.stop_pipeline()
   time.sleep(0.5)  # Wait for graceful shutdown
   ```

3. **Log with Visual Separators**

   ```python
   logger.info("=" * 70)
   logger.info("CAMERA INITIALIZATION REQUEST")
   # ... operations ...
   logger.info("=" * 70)
   ```

4. **Include Pipeline State in Status Messages**

   ```javascript
   statusMsg += ` - Pipeline: ${result.pipeline_state}`;
   updateCameraStatus('connected', statusMsg);
   ```

5. **Handle Errors Gracefully**

   ```python
   try:
       result = operation()
   except Exception as e:
       logger.error(f"❌ Operation failed: {str(e)}")
       return error_response()
   ```

### For Users

1. **Refresh Page Anytime** - No need to manually disconnect camera before refreshing
2. **Check Console Logs** - Open DevTools (F12) to see detailed initialization progress
3. **Verify Pipeline State** - Status should show "Pipeline: PLAYING" after successful init
4. **Wait for Status Updates** - System status updates show current operation progress

---

## Future Enhancements

### Planned Features

- [ ] **Automatic Recovery** - Auto-retry initialization on failure
- [ ] **Pipeline Health Monitoring** - Periodic checks for pipeline state
- [ ] **Graceful Degradation** - Handle camera disconnects during operation
- [ ] **Multiple Camera Support** - Track multiple pipelines simultaneously
- [ ] **WebSocket Status Updates** - Real-time pipeline state updates without polling

### Potential Improvements

- [ ] **Timeout Handling** - Add timeouts to pipeline operations
- [ ] **Resource Cleanup** - More aggressive memory cleanup after reset
- [ ] **State Persistence** - Remember camera settings across sessions
- [ ] **Performance Metrics** - Track initialization time and success rate
- [ ] **Error Recovery UI** - Show suggested actions when errors occur

---

## Related Documentation

- [CLIENT_SERVER_ARCHITECTURE.md](./CLIENT_SERVER_ARCHITECTURE.md) - Overall system architecture
- [CAMERA_IMPROVEMENTS.md](./CAMERA_IMPROVEMENTS.md) - Camera-specific improvements
- [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md) - Project organization

---

## Change Log

| Date | Version | Changes |
|------|---------|---------|
| 2025-01-XX | 1.0.0 | Initial implementation of professional camera initialization system |

---

## Contact

For questions or issues related to camera initialization, please refer to the main project README or contact the development team.
