# Visual AOI Client - Project Logic Instructions

## 📋 Overview
This document defines the **current application logic and architecture** for the Visual AOI Client project. Any code modifications must maintain consistency with these established patterns and workflows.

## 🏗️ System Architecture

### Core Components
1. **Flask Web Application** (`app.py`) - Main web server with RESTful API
2. **Professional Web Interface** (`templates/professional_index.html`) - Modern web-based UI
3. **TIS Camera Integration** (`src/camera.py`, `src/TIS.py`) - Hardware camera control
4. **Legacy Desktop Client** (`client/client_app_simple.py`) - Reference implementation
5. **Configuration Management** (`config/`) - Product and system configurations

### Data Flow Architecture
```
[Camera Hardware] → [TIS Module] → [Flask Backend] → [Web Frontend] → [User Interface]
                                      ↕
                                [Configuration Files]
                                      ↕
                                [Session Management]
```

## 🔄 Application Logic Patterns

### 1. Initialization Sequence (CRITICAL LOGIC)
```
1. Server Connection → 2. Product Selection → 3. Camera Initialization → 4. Session Creation
```

**Implementation Rules:**
- Server connection must be established before any operations
- Product selection loads ROI configurations automatically
- Camera initialization uses first ROI group settings for optimal setup
- Session creation auto-generates device barcode inputs based on ROI groups count
- Auto-collapse setup panels after successful initialization (2-second delay)

### 2. Session Management Logic
```python
# Data Classes (DO NOT MODIFY STRUCTURE)
@dataclass
class DeviceBarcodeEntry:
    device_id: int
    barcode: str

@dataclass  # MUST have @dataclass decorator
class ROIGroup:
    focus: int
    exposure: int
    rois: List[Dict[str, Any]]

@dataclass
class AOIState:
    server_url: str = "http://localhost:5000"
    connected: bool = False
    session_id: Optional[str] = None
    session_product: Optional[str] = None
    products_cache: List[Dict[str, Any]] = field(default_factory=list)
    last_result: Optional[Dict[str, Any]] = None
    camera_serial: Optional[str] = None
```

**Critical Rules:**
- Always use `getattr()` for ROIGroup attribute access (NOT dictionary `.get()`)
- Session ID must be UUID format for uniqueness
- Product selection automatically loads and caches ROI groups
- Camera settings derived from first ROI group in configuration

### 3. Device Barcode Management Logic

**Overview:**
The system intelligently determines which devices need manual barcode input by analyzing ROI configurations. Devices with barcode ROIs don't need manual input; devices without barcode ROIs require operator scanning.

**Current Implementation:**
```javascript
// Sequential barcode input generation
function generateDeviceBarcodeInputs(deviceIds) {
    // deviceIds = array of device IDs that need manual barcode input
    // Example: [2, 5, 7] means Device 2, 5, and 7 need manual scanning
    
    // Creates inputs with:
    // - Sequential enable/disable flow
    // - Auto-focus on active input
    // - Keyboard shortcuts (Enter, Arrow keys, F1, Ctrl+R, Ctrl+Shift+C)
    // - Visual states (active, completed, error)
}
```

**Server-Side Analysis:**
```python
def analyze_devices_needing_barcodes(roi_groups):
    device_has_main_barcode = {}
    
    for roi in rois:
        device_id = roi[8] if len(roi) > 8 else 1
        roi_type = roi[1] if len(roi) > 1 else None
        
        # Check if this is a barcode ROI
        is_barcode = roi_type in [1, '1'] or (
            len(roi) > 6 and roi[6] == 'barcode'
        )
        
        # NEW: Check if this is the MAIN barcode (defaults to True for backward compatibility)
        is_device_barcode = roi[10] if len(roi) > 10 else True
        
        # Only mark device as having barcode if it's the MAIN barcode
        if is_barcode and is_device_barcode:
            device_has_main_barcode[device_id] = True
    
    # Return devices that DON'T have MAIN barcode ROIs
    devices_need_manual = [
        dev_id for dev_id, has_barcode in device_has_main_barcode.items()
        if not has_barcode
    ]
    return sorted(devices_need_manual)
```

**Client-Side Logic:**
```javascript
// Session creation response includes devices_need_barcode array
function updateSessionInfo(sessionData) {
    const devicesNeedBarcode = sessionData.devices_need_barcode || [];
    
    if (devicesNeedBarcode.length > 0) {
        // Show barcode panel with inputs for these devices only
        generateDeviceBarcodeInputs(devicesNeedBarcode);
    } else {
        // Hide panel - all devices have barcode ROIs
        showNotification('All devices have barcode ROIs - no manual input needed', 'info');
    }
}
```

**Implementation Rules:**
- Device barcode inputs are **auto-generated** based on `devices_need_barcode` array from server
- Panel shows ONLY for devices without barcode ROIs
- Sequential scanning enforced: one device at a time
- Keyboard navigation: Enter (advance), Arrow keys (navigate), F1 (focus first)
- No manual add/remove barcode functionality
- Barcode inputs integrated into Inspection Control panel
- Input validation ensures ALL required barcodes entered before inspection

**Workflow:**
```
Session Created → Server analyzes ROI groups → Returns devices_need_barcode
    ↓
devices_need_barcode = [2, 5] → Panel shown with 2 inputs (Device 2, Device 5)
devices_need_barcode = []      → Panel hidden (all devices have barcode ROIs)
    ↓
User scans Device 2 → Press Enter → Device 5 enabled + focused
User scans Device 5 → Press Enter → Auto-trigger inspection
```

**Known Limitation:**
⚠️ **Main Barcode ROI Detection**
- Current logic: ANY barcode ROI on device → device doesn't need manual input
- Cannot distinguish "main" barcode from auxiliary barcodes (serial, QR codes, etc.)
- Workaround: Products should only define ONE barcode ROI per device (the main one)
- Future enhancement needed: Add `is_device_barcode` field to ROI structure (see Configuration section)

**Example Scenarios:**

**Scenario 1: Product with mixed devices**
```python
# Device 1: Has main barcode ROI → devices_need_barcode does NOT include 1
# Device 2: No barcode ROI → devices_need_barcode includes 2
# Device 3: Has main barcode ROI → devices_need_barcode does NOT include 3

# Result: Panel shows input for Device 2 only
devices_need_barcode = [2]
```

**Scenario 2: Product with no barcode ROIs**
```python
# All devices need manual scanning
devices_need_barcode = [1, 2, 3, 4]

# Panel shows 4 inputs, sequential scanning required
```

**Scenario 3: Product with all barcode ROIs**
```python
# No devices need manual scanning
devices_need_barcode = []

# Panel hidden, inspection uses scanned barcodes from ROIs
```

### 4. Camera Initialization Logic
```python
# TIS Camera Initialization Pattern
def initialize_camera(serial: str, product_config: Dict) -> bool:
    # 1. Get first ROI group settings
    first_roi_group = get_first_roi_group(product_config)
    focus = first_roi_group.focus
    exposure = first_roi_group.exposure
    
    # 2. Initialize with optimal settings
    success = tis_camera.initialize(
        serial=serial,
        width=7716, height=5360,  # Proven working resolution
        fps=7,                    # Proven working framerate
        initial_focus=focus,
        initial_exposure=exposure
    )
    
    # 3. Apply settle delay for stability
    time.sleep(3.0)  # Camera stabilization
    
    return success
```

**Critical Rules:**
- Always initialize camera with first ROI group settings
- Use proven working resolution (7716x5360) and framerate (7 fps)
- Apply 3-second settle delay after initialization
- Store first ROI group settings for revert after capture

### 5. Inspection Workflow Logic
```python
# Grouped Capture and Inspection Pattern
def perform_grouped_capture(product_name: str, roi_groups: Dict[str, Any]) -> Dict[str, Any]:
    captured_images = {}
    
    for group_key, group_info in roi_groups.items():
        # CRITICAL: Use getattr() for ROIGroup objects
        focus = int(getattr(group_info, "focus", None) or group_key.split(",")[0])
        exposure = int(getattr(group_info, "exposure", None) or group_key.split(",")[1])
        rois = getattr(group_info, "rois", [])
        
        # Apply settings and capture
        image = tis_camera.capture_image(focus=focus, exposure_time=exposure)
        captured_images[group_key] = {
            "focus": focus,
            "exposure": exposure, 
            "rois": rois,
            "image": encode_image(image)
        }
    
    return captured_images
```

**Implementation Rules:**
- Use grouped capture for efficiency (multiple settings per session)
- Always use `getattr()` for ROIGroup attribute access
- Apply camera settings before each capture group
- Revert to first ROI group settings after capture completion
- Parallel processing: inspection processing + camera revert

### 6. UI State Management Logic
```javascript
// Global State Pattern (DO NOT MODIFY STRUCTURE)
let appState = {
    collapsedSections: new Set(),
    setupComplete: { server: false, camera: false, session: false },
    connected: false,
    cameraInitialized: false,
    sessionActive: false,
    sessionId: null,
    liveViewActive: false,
    theme: 'light',
    refreshRate: 100,
    resultsFormat: 'detailed'
};
```

**Critical Rules:**
- Use persistent state management with localStorage
- Auto-collapse panels after setup completion
- Track setup completion to prevent duplicate auto-collapse
- Save theme and panel states across browser sessions

### 7. Collapsible Panel Logic
```javascript
// Panel Management Pattern
function toggleSection(sectionId) {
    // Smooth CSS transitions with height animation
    // Save state to localStorage
    // Visual feedback with icons (📁/📂)
}

function checkSetupComplete() {
    // Auto-collapse after 2-second delay
    // Only collapse once per setup item
    // Show notification when collapsed
}
```

**Implementation Rules:**
- Only three collapsible panels: Server, Camera, Session
- Auto-collapse triggers 2 seconds after successful setup
- Manual toggles override auto-collapse behavior
- Visual indicators show collapsed state

## 🔧 API Endpoint Logic

### Core Endpoints (DO NOT MODIFY SIGNATURES)
```python
# Server Management
@app.route('/api/server/connect', methods=['POST'])
@app.route('/api/server/disconnect', methods=['POST'])

# Camera Management  
@app.route('/api/cameras', methods=['GET'])
@app.route('/api/camera/initialize', methods=['POST'])
@app.route('/api/camera/start-live', methods=['POST'])
@app.route('/api/camera/stop-live', methods=['POST'])
@app.route('/api/camera/live-image', methods=['GET'])

# Session Management
@app.route('/api/session', methods=['POST'])
@app.route('/api/session/close', methods=['POST'])
@app.route('/api/products', methods=['GET'])

# Inspection Processing
@app.route('/api/inspect', methods=['POST'])
```

**Implementation Rules:**
- Maintain consistent error handling with JSON responses
- Use proper HTTP status codes (200, 400, 500)
- Include timing information in inspection responses
- Log all major operations for debugging

## 🎨 UI Design Patterns

### Glass Morphism Theme System
```css
/* Core Design Pattern (DO NOT MODIFY) */
:root {
    --glass-bg: transparent surfaces with backdrop-filter
    --glass-border: subtle borders with opacity
    --primary: #007AFF (iOS blue)
    --success: #34C759, --error: #FF3B30, --warning: #FF9500
}
```

**Design Rules:**
- Use iOS-inspired glass morphism effects
- Maintain light/dark theme consistency
- Smooth animations with cubic-bezier easing
- Professional spacing and typography
- Responsive grid layout for all screen sizes

### Component Hierarchy
```
Container → Grid → Section → Section-Header + Section-Content → Controls → Form Elements
```

**Layout Rules:**
- Full-width sections for major operations (Inspection Control)
- Grid layout for setup panels (2-3 columns responsive)
- Glass effect cards with hover interactions
- Status indicators with real-time updates

## 🚫 Critical Don'ts - Breaking These Rules Will Cause Issues

### 1. ROIGroup Object Access
```python
# ❌ NEVER DO THIS (Will cause AttributeError)
focus = group_info.get("focus")
exposure = group_info.get("exposure")

# ✅ ALWAYS DO THIS
focus = getattr(group_info, "focus", None)
exposure = getattr(group_info, "exposure", None)
```

### 2. Device Barcode Management
```javascript
// ❌ NEVER CREATE separate Device Barcodes panel
// ❌ NEVER add manual add/remove barcode functions
// ❌ NEVER use static barcode inputs

// ✅ ALWAYS auto-generate based on ROI groups count
// ✅ ALWAYS integrate into Session Management panel
```

### 3. Panel Structure
```html
<!-- ❌ NEVER add barcodeSection back -->
<!-- ❌ NEVER duplicate control buttons -->
<!-- ❌ NEVER remove section-header structure -->

<!-- ✅ ALWAYS maintain three setup panels: server, camera, session -->
<!-- ✅ ALWAYS use collapsible section-header pattern -->
```

### 4. State Management
```javascript
// ❌ NEVER modify appState structure without updating all dependencies
// ❌ NEVER bypass localStorage for persistent state
// ❌ NEVER mix setup completion tracking

// ✅ ALWAYS use established state patterns
// ✅ ALWAYS maintain backward compatibility
```

## 📝 Configuration File Patterns

### Product Configuration Structure

#### ROI Array Format (Updated - October 3, 2025)
```python
# Each ROI is represented as an array with fixed indices:
roi = [
    roi_id,          # [0] Unique identifier (integer)
    roi_type,        # [1] Type code: 1=barcode, 2=compare, 3=OCR (integer)
    bbox,            # [2] Bounding box [x, y, width, height] (list)
    focus,           # [3] Focus value (integer)
    exposure,        # [4] Exposure time (integer)
    golden,          # [5] Golden image path or None
    type_name,       # [6] Human-readable type: "barcode", "compare", "ocr" (string)
    threshold,       # [7] Comparison threshold (float)
    device_id,       # [8] Device number (integer, default: 1)
    expected_value,  # [9] Expected value for OCR/barcode (string or None)
    is_device_barcode  # [10] Boolean: True=main barcode, False=auxiliary (NEW)
]

# Examples:
[4, 1, [500, 100, 700, 200], 325, 1500, null, "barcode", 0, 1, null, true]   # Main barcode
[5, 1, [500, 300, 700, 400], 325, 1500, null, "barcode", 0, 1, null, false]  # Auxiliary barcode

# Backward compatibility: ROIs without field [10] default to is_device_barcode=True
[4, 1, [500, 100, 700, 200], 325, 1500, null, "barcode", 0, 1, null]  # Treated as main
```

#### JSON Configuration Structure
```json
{
    "product_name": "string",
    "roi_groups": {
        "focus,exposure": {
            "rois": [
                [1, 3, [100, 100, 400, 150], 325, 1500, null, "ocr", 0, 1, "PASS", false],
                [4, 1, [500, 100, 700, 200], 325, 1500, null, "barcode", 0, 1, null, true]
            ]
        }
    }
}
```

**Configuration Rules:**
- ROI groups keyed by "focus,exposure" string format
- Device IDs (index [8]) determine auto-generated barcode input count
- ROI types: 1=barcode, 2=compare (component), 3=OCR (text recognition)
- Type names (index [6]): "barcode", "compare", "ocr" (must match roi_type)
- Coordinates in absolute pixel values [x, y, width, height]
- Expected values (index [9]) used for OCR text validation

### ✅ RESOLVED: Main Barcode ROI Marking (Implemented October 3, 2025)

**Previous Issue (RESOLVED):**
The ROI structure did not include an attribute to distinguish a "main" barcode ROI from auxiliary barcodes.

**Solution Implemented:**
Added `is_device_barcode` field at index [10] to ROI array structure.

**Problem Scenario:**
```python
# Device with multiple barcode ROIs - ALL treated equally
[4, 1, [500, 100, 700, 200], 325, 1500, None, "barcode", 0, 1, None]  # Product barcode
[5, 1, [500, 300, 700, 400], 325, 1500, None, "barcode", 0, 1, None]  # Serial number
[6, 1, [500, 500, 700, 600], 325, 1500, None, "barcode", 0, 1, None]  # QR code

# Current logic: Device 1 has barcode? YES (found any roi_type=1)
# Reality: Cannot identify which is the "main" barcode for device identification
```

**Current Detection Logic:**
```python
# In analyze_devices_needing_barcodes():
is_barcode = roi_type in ['barcode', 1, '1']  # ANY barcode marks device as "has barcode"

# Problem: If device has 3 barcodes, logic assumes device doesn't need manual input
# But user's intent was: "Only main barcode ROI should count"
```

**Workaround (Current):**
- Assumes **ANY** barcode ROI on a device means device doesn't need manual input
- Operators must ensure only one barcode ROI per device, or first scanned barcode is used
- Cannot support products with multiple barcode types (product ID + serial + QR)

**Proposed Solution (Future Enhancement):**
Add new field to ROI array structure to mark main barcode:

**Option 1: Add is_device_barcode flag (index [10])**
```python
roi = [
    roi_id, roi_type, bbox, focus, exposure, golden, type_name, 
    threshold, device_id, expected_value,
    is_device_barcode  # [10] NEW: True if this is the main barcode for device ID
]

# Example:
[4, 1, [500, 100, 700, 200], 325, 1500, None, "barcode", 0, 1, None, True]   # Main
[5, 1, [500, 300, 700, 400], 325, 1500, None, "barcode", 0, 1, None, False]  # Aux
```

**Option 2: Extend type_name with role suffix**
```python
# type_name format: "barcode:<role>"
[4, 1, [500, 100, 700, 200], 325, 1500, None, "barcode:main", 0, 1, None]
[5, 1, [500, 300, 700, 400], 325, 1500, None, "barcode:serial", 0, 1, None]
[6, 1, [500, 500, 700, 600], 325, 1500, None, "barcode:qr", 0, 1, None]
```

**Option 3: Add barcode_role field (index [10])**
```python
roi = [
    roi_id, roi_type, bbox, focus, exposure, golden, type_name,
    threshold, device_id, expected_value,
    barcode_role  # [10] NEW: "main" | "auxiliary" | "qr" | None
]
```

**Recommended Approach:**
- **Option 1 (boolean flag)** - Simplest, backward compatible (defaults to True if not present)
- Update `analyze_devices_needing_barcodes()` logic to check `is_device_barcode == True`
- Existing configs without field [10] default to True (treat all barcodes as main)

**Implementation Impact:**
```python
# Updated detection logic:
def analyze_devices_needing_barcodes(roi_groups):
    for roi in rois:
        roi_type = roi[1] if len(roi) > 1 else None
        type_name = roi[6] if len(roi) > 6 else None
        device_id = roi[8] if len(roi) > 8 else 1
        is_device_barcode = roi[10] if len(roi) > 10 else True  # Default to True for backward compat
        
        is_barcode = roi_type in [1, '1'] or type_name == 'barcode'
        
        # Only count as "has barcode" if it's a main barcode
        if is_barcode and is_device_barcode:
            device_has_barcode[device_id] = True
```

**Migration Path:**
1. Add field [10] to new product configurations
2. Existing products work unchanged (field defaults to True)
3. Update ROI editor to support main barcode checkbox
4. Update documentation for config file format

## 🔄 Testing and Validation Patterns

### Workflow Testing Sequence
1. **Server Connection Test**: Verify connection and product loading
2. **Camera Initialization Test**: Test with real TIS hardware
3. **Session Creation Test**: Verify auto-generated barcode inputs
4. **Panel Collapse Test**: Verify auto-collapse behavior
5. **Inspection Test**: Full workflow with device barcodes
6. **State Persistence Test**: Reload page and verify saved states

### Error Handling Patterns
```python
# Standard Error Response Format
{
    "error": "Human-readable error message",
    "details": "Technical details for debugging",
    "timestamp": "ISO format timestamp",
    "status": "error"
}
```

## 📚 Modification Guidelines

### Before Making Changes:
1. **Read this document completely**
2. **Identify which logic patterns will be affected**
3. **Test with minimal changes first**
4. **Verify no regression in established workflows**

### After Making Changes:
1. **Update this document if logic patterns change**
2. **Test complete workflow end-to-end**
3. **Verify all three setup panels still function**
4. **Check auto-collapse and state persistence**

### When Adding New Features:
1. **Follow established patterns and naming conventions**
2. **Integrate with existing state management**
3. **Maintain glass morphism design consistency**
4. **Add appropriate error handling and logging**

## 🎯 Success Criteria

A modification is successful when:
- ✅ All existing workflows continue to function
- ✅ Auto-collapse behavior works correctly
- ✅ Device barcode auto-generation functions
- ✅ Camera initialization follows optimal patterns
- ✅ State persistence maintains user preferences
- ✅ UI maintains professional glass morphism theme
- ✅ No AttributeError or object access issues
- ✅ Inspection workflow completes successfully

---

**⚠️ IMPORTANT**: This document represents the current working state of the application. Any deviation from these patterns should be thoroughly tested and documented with updates to this instruction file.

---

## 📝 Change Log

### October 3, 2025 - ROI Structure Analysis & Main Barcode Limitation
**Updated Sections:**
- Added detailed ROI array structure documentation with field indices
- Documented CRITICAL LIMITATION: No attribute to mark "main" barcode ROI
- Added comprehensive device barcode management logic section
- Proposed 3 solutions for main barcode ROI marking (boolean flag, role suffix, role field)
- Updated configuration file patterns with array format specification
- Added example scenarios for device barcode logic
- Recommended implementation: Option 1 (is_device_barcode boolean at index [10])

**Key Finding:**
Current ROI structure cannot distinguish between main barcode and auxiliary barcodes (serial numbers, QR codes, etc.). If a device has ANY barcode ROI, the system assumes it doesn't need manual input, even if that barcode is not the main device identifier.

**Current Workaround:**
Products should only define ONE barcode ROI per device (the main/primary barcode). Additional barcodes (serial, QR) should be handled separately or through alternative mechanisms.

**Future Enhancement Required:**
Add `is_device_barcode` field at ROI array index [10] to explicitly mark which barcode ROI is the primary device identifier. This will enable proper handling of products with multiple barcode types per device.

---

**Last Updated**: October 3, 2025
**Current Version**: Visual AOI Client v2.0 - Professional Web Interface
**Documentation Status**: ✅ Updated with ROI structure analysis and main barcode limitation