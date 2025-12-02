# Visual AOI Server - Project Instructions & Core Logic Documentation

**Version:** 1.0  
**Last Updated:** October 3, 2025  
**Purpose:** Define core application logic that must be preserved during code modifications

## Related Documentation

- **ROI Definition Specification** (`ROI_DEFINITION_SPECIFICATION.md`) - Official ROI structure format
- **Inspection Result Specification** (`INSPECTION_RESULT_SPECIFICATION.md`) - Official result structure format
- **Change Management Guidelines** (`CHANGE_MANAGEMENT_GUIDELINES.md`) - Safe modification procedures
- **API Documentation** (`/api/docs`) - Swagger/OpenAPI specifications
- **Camera Improvements** (`CAMERA_IMPROVEMENTS.md`) - Camera capture and configuration
- **Multi-Device Implementation** (`MULTI_DEVICE_IMPLEMENTATION.md`) - Multi-device inspection logic

---

## 🎯 System Overview

The Visual AOI (Automated Optical Inspection) Server is a Flask-based REST API that processes images for industrial quality control inspection. It supports multiple inspection types (barcode reading, AI comparison, OCR text recognition) and manages multi-device inspection workflows.

### Core Architecture Principles
1. **Client-Server Separation**: Server handles processing only, client handles camera operations
2. **Session-Based Processing**: Each inspection session is isolated with UUID-based tracking
3. **Multi-Device Support**: Each inspection can process multiple devices in a single image
4. **Graceful Fallbacks**: System works with or without AI models, with simulation modes
5. **Product Configuration**: Inspection logic driven by configurable ROI (Region of Interest) definitions

---

## 🔧 Critical Application Logic

### 1. Session Management Logic

#### Session Lifecycle ⚠️ **CRITICAL LOGIC**
```
CREATE SESSION → LOAD PRODUCT → RUN INSPECTIONS → CLOSE SESSION
```

**Core Rules:**
- **Session Isolation**: Each session must maintain independent state
- **UUID Generation**: All session IDs must be unique UUIDs
- **Product Binding**: Once created, session product cannot be changed
- **Automatic Cleanup**: Sessions expire after 1 hour of inactivity
- **Concurrency Control**: Only one inspection per session at a time

**Implementation Requirements:**
- Session state stored in `server_state['sessions']` dictionary
- Session must update `last_activity` on every operation
- Session must track `inspection_count` for statistics
- Session must store `last_results` for result retrieval

### 2. Inspection Processing Logic

#### ROI Processing Pipeline ⚠️ **CRITICAL LOGIC**
```
IMAGE → DECODE → LOAD ROIS → PROCESS BY TYPE → AGGREGATE RESULTS → DEVICE SUMMARIES
```

**ROI Types and Processing:**
1. **Type 1 (Barcode)**: Extract barcode values using Dynamsoft library
2. **Type 2 (Compare)**: AI similarity comparison against golden images  
3. **Type 3 (OCR)**: Text recognition using EasyOCR

**Critical Processing Rules:**
- **ROI Structure**: `(idx, type, coords, focus, exposure, ai_threshold, feature_method, rotation, device_location, expected_text)` - See [ROI_DEFINITION_SPECIFICATION.md](./ROI_DEFINITION_SPECIFICATION.md) for complete specification
- **Device Assignment**: Each ROI must have a `device_location` field (1-based indexing)
- **Coordinate Format**: `[x1, y1, x2, y2]` - always 4 integers
- **Result Aggregation**: Group results by device_id for device summaries
- **Format Compatibility**: All code must support legacy 3-11 field ROI formats via `normalize_roi()`

#### Device Summary Logic ⚠️ **CRITICAL LOGIC**
```python
device_summaries[device_id] = {
    'total_rois': len(device_rois),
    'passed_rois': passed_count,
    'failed_rois': failed_count,
    'device_passed': passed_count == total_count,
    'barcode': barcode_value,  # Must be determined by priority logic
    'results': device_rois
}
```

**Barcode Priority Logic (MUST PRESERVE):**
0. **Device Main Barcode (NEW)**: Use barcode from ROI with `is_device_barcode=True` (HIGHEST PRIORITY)
1. **ROI Barcode First**: Use barcode detected from any barcode ROI if valid
2. **Manual Multi-Device**: Use `device_barcodes[device_id]` if ROI barcode invalid/missing
3. **Legacy Single**: Use `device_barcode` for all devices (backward compatibility)
4. **Default Fallback**: Use 'N/A' if no barcode source available

**New in v3.0:** Field 10 (`is_device_barcode`) allows marking specific barcode ROI as device identifier, giving it highest priority over other barcode ROIs on same device.

### 3. AI Model Integration Logic

#### PyTorch MobileNetV2 Pipeline ⚠️ **CRITICAL LOGIC**
```
Initialize → GPU Detection → Model Loading → Feature Extraction → Similarity Comparison
```

**Critical Requirements:**
- **GPU Priority**: Try CUDA first, fallback to CPU automatically
- **Model Singleton**: Only one model instance globally with thread locks
- **Feature Dimensions**: MobileNetV2 produces 1280-dimensional features
- **OpenCV Fallback**: Use SIFT descriptors (384-dim) if PyTorch unavailable
- **Error Handling**: Never crash the server due to AI failures

#### Golden Image Matching Logic ⚠️ **CRITICAL LOGIC**
```python
# Enhanced golden image matching with promotion
1. Try best_golden.jpg first (highest priority)
2. If no match, try all other golden images
3. If alternative matches above threshold, promote it to best_golden.jpg
4. Always track best similarity for result reporting
```

**File Management Rules:**
- `best_golden.jpg` - Current best reference image
- `original_TIMESTAMP.jpg` - Historical golden images
- Auto-promotion when better match found above threshold
- Backup old best golden before replacement

### 4. Base64 Image Handling Logic

#### Image Encoding/Decoding ⚠️ **CRITICAL LOGIC**
```python
# Input: data:image/jpeg;base64,<data> OR just <base64_data>
# Output: OpenCV BGR format numpy array
def decode_base64_image(base64_data: str) -> np.ndarray:
    # Strip data URL prefix if present
    if base64_data.startswith('data:image/'):
        base64_data = base64_data.split(',')[1]
    # Decode and convert to OpenCV format
```

**Encoding Rules:**
- Always include proper MIME type prefix
- Default to JPEG with 85% quality for size optimization
- Support PNG for lossless when needed
- Handle both ROI images and full images consistently

---

## 🏗️ API Endpoint Logic Requirements

### Core Endpoints - Logic Preservation Rules

#### `/api/session/create` ⚠️ **CRITICAL LOGIC**
- **Input Validation**: `product_name` is required and must exist
- **Product Loading**: Must call `set_product_name()` and load ROI config
- **Session Creation**: Generate UUID, create InspectionSession object
- **State Update**: Set `server_state['current_product']`

#### `/api/session/{id}/inspect` ⚠️ **CRITICAL LOGIC**
- **Concurrency Control**: Check `inspection_in_progress` flag
- **Image Processing**: Base64 decode → ROI processing → Device aggregation
- **Barcode Handling**: Support both legacy single and new multi-device barcodes
- **Result Format**: Must include `roi_results`, `device_summaries`, `overall_result`
- **Session Update**: Increment `inspection_count`, store `last_results`

#### `/api/products` ⚠️ **CRITICAL LOGIC**
- **Discovery Logic**: Scan `config/products/` for both direct JSON files and subdirectories
- **Config Formats**: Support both new JSON format and legacy ROI array format
- **Path Resolution**: Handle relative paths correctly from server directory

#### `/process_grouped_inspection` ⚠️ **CRITICAL LOGIC**
- **File System Access**: Read images from shared session directories
  - **Server Path**: `/home/jason_nguyen/visual-aoi-server/shared/sessions/<uuid>/` (absolute path in code)
  - **Input Folder**: `sessions/<uuid>/input/` - Client writes captured images
  - **Output Folder**: `sessions/<uuid>/output/` - Server writes ROI/golden images
  - **Client Access**: Via CIFS mount at `/mnt/visual-aoi-shared/` (same physical directory)
- **Group Processing**: Process multiple focus/exposure groups sequentially
- **Device Aggregation**: Combine results across all groups by device_id
- **Manual Barcode Integration**: Apply device_barcodes across all groups consistently
- **Output Generation**: Save ROI and golden images to output folder for client access

### Shared Folder Architecture
- **Type**: CIFS/SMB Network Share
- **Server Path**: `/home/jason_nguyen/visual-aoi-server/shared/` (absolute path used in server code)
- **Client Mount**: `/mnt/visual-aoi-shared/` (CIFS network mount for clients)
- **Physical Location**: Both paths point to same directory (inode 58335949)
- **Protocol**: SMB 2.0 with credentials at `/etc/samba/visual-aoi-credentials`
- **Permissions**: Read/Write for jason_nguyen (uid=1000)
- **Performance**: Server uses local path for direct access (no network overhead)
- **Session Cleanup**: 63 active sessions (consider implementing auto-cleanup)

### Swagger Documentation Requirements
- All endpoints must have complete OpenAPI 2.0 documentation
- Include request/response schemas with examples
- Document all error codes and conditions
- Maintain backward compatibility notes
- Swagger UI accessible at `/apidocs/` (local and network)
- Dynamic hostname resolution for external access

---

## 🔬 Inspection Module Logic

### ROI Processing Core Logic ⚠️ **CRITICAL LOGIC**

#### Compare ROI Processing
```python
def process_compare_roi(image, x1, y1, x2, y2, idx, ai_threshold, feature_method, product_name):
    # 1. Extract ROI from image: crop = image[y1:y2, x1:x2]
    # 2. Normalize illumination for consistent comparison
    # 3. Load golden images with best_golden.jpg priority
    # 4. Extract features using specified method (mobilenet/sift/orb)
    # 5. Calculate cosine similarity against all golden images
    # 6. Return result tuple: (idx, type, golden_img, roi_img, coords, result, color, similarity, threshold)
```

#### Barcode ROI Processing
```python
def process_barcode_roi(image, x1, y1, x2, y2, idx):
    # 1. Extract ROI from image
    # 2. Use Dynamsoft barcode reader
    # 3. Return barcode strings as list format for client compatibility
    # 4. Mark as passed if any barcode detected
```

#### OCR ROI Processing
```python
def process_ocr_roi(image, x1, y1, x2, y2, idx, rotation, expected_text):
    # 1. Extract and optionally rotate ROI
    # 2. Use EasyOCR with GPU priority, CPU fallback
    # 3. Compare against expected_text if provided
    # 4. Apply pass/fail logic: [PASS:], [FAIL:], or text presence
```

### Pass/Fail Determination Logic ⚠️ **CRITICAL LOGIC**
```python
def is_roi_passed(roi_result):
    # Compare ROI: similarity >= threshold
    # Barcode ROI: any barcode detected (non-empty string)
    # OCR ROI: 
    #   - [FAIL:] in text → False
    #   - [PASS:] in text → True  
    #   - Otherwise → bool(text_detected)
```

---

## 📁 Configuration Management Logic

### Product Configuration Structure ⚠️ **CRITICAL LOGIC**
```
config/products/{product_name}/
├── rois_config_{product_name}.json    # ROI definitions
└── golden_rois/                       # Golden reference images
    └── roi_{idx}/
        ├── best_golden.jpg           # Primary reference
        └── original_*.jpg            # Historical references
```

### ROI Configuration Format ⚠️ **CRITICAL LOGIC**

**⚠️ IMPORTANT:** Complete ROI structure specification is documented in [ROI_DEFINITION_SPECIFICATION.md](./ROI_DEFINITION_SPECIFICATION.md)

```json
[
  {
    "index": 1,
    "type": 2,                    // 1=barcode, 2=compare, 3=ocr
    "coordinates": [x1, y1, x2, y2],
    "focus": 305,
    "exposure_time": 3000,
    "ai_threshold": 0.85,         // For compare ROIs only
    "feature_method": "mobilenet", // mobilenet/sift/orb
    "rotation": 0,                // For OCR ROIs
    "device_location": 1,         // 1-based device index
    "expected_text": "EXPECTED"     // For OCR comparison
  }
]
```

**Current Format:** 11-field tuple - See [ROI_DEFINITION_SPECIFICATION.md](./ROI_DEFINITION_SPECIFICATION.md) for:
- Complete field definitions and constraints
- Legacy format migration rules (3-field through 10-field)
- Validation requirements
- Type-specific defaults

**Field 10 (New):** `is_device_barcode` - Boolean flag for device main barcode identification
- When `True`, this barcode ROI takes highest priority for device identifier
- Only meaningful for Type 1 (Barcode) ROIs
- Default: `None` (for backward compatibility)

### Legacy Compatibility Requirements
- Support old tuple formats: `(idx, type, coords, focus, exposure)` through 10-field
- Auto-upgrade to 11-field format with defaults
- Handle missing fields gracefully with sensible defaults

---

## 🚨 Critical Preservation Rules

### 1. State Management Rules ⚠️ **NEVER CHANGE**
- `server_state` global dictionary structure
- Session dictionary key-value mapping
- `inspection_in_progress` concurrency flag
- Session cleanup 1-hour timeout logic

### 2. Data Flow Rules ⚠️ **NEVER CHANGE**
- Base64 image input format handling
- ROI coordinate system (x1,y1,x2,y2)
- Device ID 1-based indexing
- Result aggregation by device_id

### 3. Backward Compatibility Rules ⚠️ **NEVER CHANGE**
- Support legacy single `device_barcode` parameter
- Support old ROI tuple formats with auto-upgrade
- Maintain existing API response structures
- Preserve simulation mode functionality

### 4. Error Handling Rules ⚠️ **NEVER CHANGE**
- Server must never crash due to AI model failures
- Graceful fallback to simulation mode
- CPU fallback for GPU initialization failures
- Continue processing on individual ROI failures

### 5. Security Rules ⚠️ **NEVER CHANGE**
- No file system operations outside `config/` directory
- Input validation on all parameters
- Session-based access control
- No direct file upload endpoints

---

## 🔄 Change Management Protocol

### Before Making ANY Code Changes:

1. **Review This Document**: Ensure changes don't violate critical logic rules
2. **Identify Impact Areas**: Map changes to affected logical components
3. **Plan Fallback Strategy**: Ensure existing functionality remains intact
4. **Update Tests**: Modify or add tests for changed logic
5. **Update Documentation**: Modify this document if logic changes

### Types of Changes by Risk Level:

#### 🟢 Safe Changes (Low Risk)
- Adding new optional API parameters
- Adding new product configuration fields with defaults
- Improving error messages and logging
- Adding new non-critical endpoints
- UI/presentation layer changes

#### 🟡 Moderate Changes (Medium Risk)
- Modifying ROI processing algorithms (with fallbacks)
- Adding new ROI types
- Changing database/file storage formats (with migration)
- Modifying AI model parameters
- Adding new device support

#### 🔴 Dangerous Changes (High Risk) ⚠️
- Changing session management logic
- Modifying barcode priority logic
- Changing device aggregation logic
- Altering API response structures
- Removing backward compatibility

### Required Actions for High-Risk Changes:
1. **Create backup branch**
2. **Write comprehensive tests**
3. **Update this documentation FIRST**
4. **Get peer review**
5. **Test with multiple product configurations**
6. **Verify backward compatibility**

---

## 📋 Quality Assurance Checklist

### For Every Code Change:

#### Core Functionality ✅
- [ ] Session creation/management works
- [ ] Image processing pipeline intact
- [ ] Device barcode priority logic preserved
- [ ] ROI processing by type functional
- [ ] Golden image matching logic intact
- [ ] Device result aggregation correct

#### API Compatibility ✅
- [ ] All existing endpoints respond correctly
- [ ] Request/response formats unchanged
- [ ] Error codes and messages consistent
- [ ] Swagger documentation updated
- [ ] Backward compatibility maintained

#### Performance & Reliability ✅
- [ ] No new memory leaks
- [ ] Proper error handling and logging
- [ ] Graceful degradation on failures
- [ ] Resource cleanup on session close
- [ ] Thread safety preserved

#### Configuration Management ✅
- [ ] Product loading works with all formats
- [ ] ROI configuration validation intact
- [ ] Golden image file operations safe
- [ ] Configuration backward compatibility

---

## 📞 Emergency Procedures

### If Core Logic is Broken:

1. **Immediate Rollback**: Revert to last working commit
2. **Check This Document**: Compare current implementation against documented logic
3. **Run Test Suite**: Execute all tests to identify specific failures
4. **Review Session State**: Check if server state corruption occurred
5. **Restart Server**: Clear any corrupted in-memory state

### Recovery Commands:
```bash
# Stop server
pkill -f simple_api_server.py

# Clear any corrupted session files
rm -rf /tmp/visual-aoi-sessions/*

# Restart with clean state
./start_server.sh
```

---

## 📚 Reference Implementation

### Critical Function Signatures ⚠️ **DO NOT CHANGE**

```python
# Session Management
class InspectionSession:
    def __init__(self, session_id: str, product_name: str, client_info: dict = None)
    def update_activity(self) -> None
    def to_dict(self) -> Dict

# Image Processing
def decode_base64_image(base64_data: str) -> np.ndarray
def encode_image_to_base64(image: np.ndarray, format: str = 'JPEG') -> str

# Inspection Logic
def run_real_inspection(image: np.ndarray, product_name: Optional[str], 
                       device_barcode: Optional[str], device_barcodes: Optional[Dict]) -> Dict
def simulate_inspection(image: np.ndarray, device_barcode: Optional[str], 
                       device_barcodes: Optional[Dict]) -> Dict

# ROI Processing
def process_roi(roi, img, product_name) -> Tuple
def is_roi_passed(roi_result: Tuple) -> bool

# Configuration
def get_available_products() -> List[Dict]
def load_rois_from_config(product_name: str) -> None
def save_rois_to_config(product_name: str) -> None
```

---

## 🏷️ Version History

| Version | Date | Changes | Critical Logic Modified |
|---------|------|---------|------------------------|
| 1.0 | Oct 3, 2025 | Initial documentation | N/A |

---

**⚠️ IMPORTANT NOTICE:**
This document defines the core application logic that powers the Visual AOI inspection system. ANY modifications to the logic described here must be accompanied by updates to this document. Failure to maintain this documentation may result in broken production systems and data loss.

**🔒 PRESERVATION GUARANTEE:**
The logic patterns, data flows, and API contracts documented here must be preserved across all future modifications to ensure system stability and backward compatibility.