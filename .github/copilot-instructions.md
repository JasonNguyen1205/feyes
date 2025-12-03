# Visual AOI System - AI Coding Agent Instructions

## Project Overview

**Friwo Eyes** is a distributed Visual AOI (Automated Optical Inspection) system for industrial quality control. The system uses a **client-server architecture** where:
- **Client** (`client/`): Flask web app running on Raspberry Pi that controls TIS industrial cameras (7716x5360), captures images, and displays results
- **Server** (`server/`): Flask REST API that processes images using PyTorch MobileNetV2, Dynamsoft barcode reading, and EasyOCR

**Critical separation**: Client handles ALL camera operations; server is 100% camera-agnostic and processes only.

## Architecture Deep Dive

### Session-Based Workflow
Every inspection follows this lifecycle:
```
POST /api/session/create → GET /api/session/{id}/status → POST /api/session/{id}/inspect → POST /api/session/{id}/close
```
- Sessions use UUID tracking and store state in `server_state['sessions']`
- Auto-cleanup after 1 hour inactivity via background thread
- Product binding is immutable once session created

### Multi-Device Processing
The system inspects 1-4 devices simultaneously in a single image:
- **ROI structure** (12-field tuple): `(idx, type, coords, focus, exposure, ai_threshold, feature_method, rotation, device_location, expected_text, is_device_barcode, color_config)`
- Each ROI has `device_location` field (1-4) determining device assignment
- Results grouped by device with independent pass/fail status
- Device passes ONLY if ALL its ROIs pass

**Barcode priority logic** (MUST preserve):
1. ROI with `is_device_barcode=True` (highest priority, v3.0+)
2. Any barcode ROI detected value
3. Manual `device_barcodes` dict from client
4. Legacy single `device_barcode` (backward compatibility)
5. Fallback: 'N/A'

### File Exchange Architecture
Uses CIFS/SMB shared folder to avoid Base64 overhead:
- **Server path**: `/home/jason_nguyen/visual-aoi-server/shared/`
- **Client mount**: `/mnt/visual-aoi-shared/`
- API **automatically converts** client paths to server paths
- Responses return file paths (NOT Base64): `roi_image_path`, `golden_image_path`
- Result: 99% smaller payloads, 195x faster transmission

### ROI Processing Pipeline
```
Image → Decode → Parallel ROI Processing (ThreadPoolExecutor) → Device Grouping → Results
                    ↓
        Type 1 (Barcode) → src/barcode.py
        Type 2 (Compare) → src/roi.py (PyTorch MobileNetV2)
        Type 3 (OCR) → src/ocr.py (EasyOCR)
        Type 4 (Color) → src/color_check.py
```
- **Parallel processing** (Oct 2025): All ROIs processed simultaneously for 2-10x speedup
- **Golden matching**: Compares against `best_golden.jpg` with auto-promotion of better matches
- **Barcode linking**: External API validation (`http://10.100.10.83:5000/api/ProcessLock/FA/GetLinkData`) with 3s timeout

## Critical Conventions

### Configuration Management
**ALWAYS read these docs before making structural changes**:
- `server/docs/PROJECT_INSTRUCTIONS.md` - Core application logic
- `server/docs/ROI_DEFINITION_SPECIFICATION.md` - Official ROI structure (v3.0, 12-field)
- `server/docs/INSPECTION_RESULT_SPECIFICATION.md` - Official result structure (v2.0)
- `server/docs/CHANGE_MANAGEMENT_GUIDELINES.md` - Safe modification procedures

**Product configs**: `config/products/{product_id}/rois_config_{product_id}.json`
- Stored in **object format** (JSON) with named properties for readability
- Use `normalize_roi()` in `src/roi.py` to handle legacy array formats
- Example: `{"idx": 1, "type": 2, "coords": [x1, y1, x2, y2], "focus": 305, "exposure": 1200, "ai_threshold": 0.93, ...}`

### Camera Integration (Client Only)
```python
# ALWAYS use BGRA format for TIS cameras
import TIS
camera.Set_Image_Format(TIS.SinkFormats.BGRA)
```
- Manual mode enforced - all auto modes disabled for stability
- Camera module: `client/src/camera.py`
- **Never** implement camera ops in server

### Testing Patterns
```bash
# Server tests
cd server/
pytest tests/ -m "unit"                    # Unit tests only
pytest tests/ -m "not slow"                # Skip slow tests
pytest tests/ --cov=src --cov-report=html  # Coverage report

# Client tests
cd client/
pytest tests/ -m "not camera"              # Skip hardware-dependent tests
```
- Test markers: `unit`, `integration`, `slow`, `camera`, `ai`, `barcode`, `ui`
- Graceful degradation: Tests auto-skip when dependencies missing
- Mock factories in `tests/test_runner.py`

## Essential Commands

```bash
# Server (port 5000)
cd server/
python server/simple_api_server.py --debug --host 0.0.0.0 --port 5000

# Client (port 5100)
cd client/
python app.py
# OR
./start_web_client.sh

# Mount shared folder (client side)
./client/setup_shared_folder.sh

# Test specific pattern
pytest tests/test_ai.py -k "mobilenet"
```

## Development Workflows

### Adding a New ROI Type
1. Update `ROI_DEFINITION_SPECIFICATION.md` FIRST with new type definition
2. Extend `normalize_roi()` in `src/roi.py` to handle new fields
3. Add processing logic in appropriate module (`src/barcode.py`, `src/roi.py`, etc.)
4. Update client UI in `templates/professional_index.html` for result display
5. Add tests with appropriate markers

### Modifying Result Structure
1. Update `INSPECTION_RESULT_SPECIFICATION.md` with new schema
2. Modify `run_real_inspection()` in `server/simple_api_server.py`
3. Update Swagger docs (decorators use `@app.route` with docstrings)
4. Adjust client parsing in `createResultsSummary()` (professional_index.html)
5. Verify with `./verify_swagger.sh`

### Working with Images
**Input** (3 methods, priority order):
1. `image_path` - absolute file path (auto-converted from client to server paths)
2. `image_filename` - relative to `/home/jason_nguyen/visual-aoi-server/shared/sessions/{uuid}/input/`
3. `image` - Base64 (legacy, discouraged)

**Output**:
- Server saves to `/home/jason_nguyen/visual-aoi-server/shared/sessions/{uuid}/output/`
- Response includes `roi_image_path` and `golden_image_path` with `/mnt/visual-aoi-shared/` prefix
- Client accesses directly via CIFS mount

## Common Gotchas

1. **Path conversions**: Client sends `/mnt/visual-aoi-shared/...`, server uses `/home/jason_nguyen/visual-aoi-server/shared/...` - API handles conversion
2. **Field naming**: Always use `exposure` (NOT `exposure_time`) in configs and code
3. **Device barcodes format**: Accepts both dict `{'1': 'barcode'}` and list `[{'device_id': 1, 'barcode': '...'}]` via `normalize_device_barcodes()`
4. **RTX 5080 compatibility**: Use PyTorch (not TensorFlow) - better GPU support
5. **ROI normalization**: ALWAYS call `normalize_roi()` when loading configs to handle legacy formats
6. **Parallel processing safety**: Use `golden_update_lock` in `src/roi.py` when modifying golden samples
7. **Session state**: Never use global variables for request state - always use session objects
8. **Color ROI validation**: Server validates Color ROIs on save, adds defaults (color_tolerance=50, min_pixel_percentage=70.0)

## UI/UX Patterns (Client)

### Raspberry Pi Performance Optimizations
- **Modal-based lazy loading**: Images load on-demand only (80% faster page load)
- **Zero animations**: Removed for stability on weak hardware
- **Chromium flags**: 16 categories of optimizations (see `CHROMIUM_READY.md`)
- **Theme system**: iOS-inspired with Liquid Glass effects
  ```javascript
  // Apply theme after widget creation
  widget = tk.Frame()
  apply_theme(widget)
  ```

### Result Display
Results parsed by device in `createResultsSummary()`:
```javascript
device_summaries[device_id] = {
  device_id: 1,
  device_passed: false,
  barcode: "['20003548-0000003-1019720-101']",
  passed_rois: 2,
  total_rois: 3,
  roi_results: [...]
}
```
- Click "View Detailed Results" to open modal per device
- Shows ROI thumbnails (golden + captured) with click-to-zoom
- Visual indicators: ✓ (pass) / ✗ (fail)

## Integration Points

### External Barcode API
- Endpoint: `http://10.100.10.83:5000/api/ProcessLock/FA/GetLinkData`
- Module: `server/src/barcode_linking.py`
- Timeout: 3 seconds with graceful fallback
- Validates/transforms device barcodes

### Swagger/OpenAPI
- **Swagger UI**: `http://localhost:5000/apidocs/`
- **OpenAPI spec**: `http://localhost:5000/apispec_1.json`
- Dynamic hostname support (works for local and network access)
- Verify: `./verify_swagger.sh`

### Schema API (Programmatic Access)
- `GET /api/schema/roi` - ROI structure specification (v3.0)
- `GET /api/schema/result` - Inspection result structure (v2.0)
- `GET /api/schema/version` - Version info and change history
- Enables client auto-adaptation to structure changes

## File Structure Quick Reference

```
client/
  app.py                      # Flask web server (port 5100)
  src/
    camera.py                 # TIS camera control
    ui.py                     # Theme system & UI helpers
    config.py                 # Config loading functions
  templates/
    professional_index.html   # Main web UI
    roi_editor.html          # ROI configuration editor
  docs/                       # 150+ detailed implementation docs

server/
  server/simple_api_server.py # Main Flask API (port 5000)
  src/
    inspection.py             # Core ROI processing logic
    roi.py                    # normalize_roi(), compare processing
    ai_pytorch.py             # PyTorch MobileNetV2 features
    barcode.py                # Dynamsoft barcode reading
    ocr.py                    # EasyOCR text recognition
    color_check.py            # Color detection (v3.2+)
    barcode_linking.py        # External API integration
  docs/
    PROJECT_INSTRUCTIONS.md   # MUST READ before code changes
    ROI_DEFINITION_SPECIFICATION.md
    INSPECTION_RESULT_SPECIFICATION.md
```

## Version-Specific Notes

- **ROI v3.0** (Oct 2025): Added `is_device_barcode` field (field 10) for device barcode priority
- **ROI v3.2** (Nov 2025): Added Color detection (type 4) with `color_config` field (field 11)
- **Result v2.0** (Oct 2025): Device-grouped results with `device_summaries` structure
- **Image optimization** (Oct 2025): File paths replace Base64, parallel ROI processing
- **Barcode linking** (Oct 2025): External API integration with timeout handling

Focus on the session-based API workflow, multi-device ROI processing with parallel execution, and PyTorch AI integration when making changes. The codebase emphasizes graceful degradation, backward compatibility, and performance optimization for Raspberry Pi deployment.
