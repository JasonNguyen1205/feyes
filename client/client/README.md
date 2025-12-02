# Visual AOI Client

Client application for the Visual Automated Optical Inspection (AOI) system.

## Overview

The Visual AOI Client connects to a central API server to perform automated inspection of products using computer vision techniques including barcode detection, image comparison, and OCR text recognition.

## Architecture

```
┌─────────────────┐         API          ┌─────────────────┐
│  CLIENT APP     │◄───────────────────►│  SERVER API     │
│  (This folder)  │    HTTP/JSON        │  (10.100.27.156)│
└────────┬────────┘                      └────────┬────────┘
         │                                        │
         │ Captures Images                        │ Processes
         │ Sends for Inspection                   │ Returns Results
         │                                        │
         ▼                                        ▼
┌─────────────────────────────────────────────────────────┐
│           SHARED FOLDER (File System)                   │
│  /mnt/visual-aoi-shared/                  │
│                                                          │
│  ├── sessions/{session_id}/                             │
│  │   ├── input/   (captured images from client)        │
│  │   └── output/  (results & processed images)         │
│  ├── golden_samples/{product_name}/                     │
│  └── temp/                                              │
└─────────────────────────────────────────────────────────┘
```

## Files in This Directory

### Main Applications

- **`client_app_simple.py`** (4889 lines)
  - Full-featured Visual AOI client with GUI
  - TIS camera integration
  - Multi-device inspection support
  - ROI management
  - Golden sample management
  - Auto-inspect workflow

### Core Modules

- **`shared_folder_manager.py`** ✨ NEW (650+ lines)
  - Centralized shared folder access API
  - Session directory management
  - Image save/read operations
  - Golden sample management
  - Disk usage monitoring
  - Automatic cleanup utilities
  - **100% test coverage** ✅
  - See: `../docs/SHARED_FOLDER_ACCESS.md`

### Examples & Documentation

- **`example_integration.py`** (450+ lines)
  - Integration examples for SharedFolderManager
  - Migration guide from old code to new
  - Side-by-side comparisons
  - Quick start tutorial

## Key Features

### 1. Camera Support
- **TIS (The Imaging Source)** cameras
  - High-resolution capture (7716x5360)
  - Dynamic focus and exposure control
  - Grouped ROI capture optimization
- **Raspberry Pi** cameras (libcamera)

### 2. Inspection Capabilities
- **Multi-device inspection** (up to 4 devices per session)
- **Three ROI types:**
  - Barcode detection (1D/2D codes)
  - Image comparison (AI-based similarity)
  - OCR text recognition
- **Device barcode management** with priority logic
- **Real-time results display**

### 3. Shared Folder Access ✨
- Clean API for all file operations
- Automatic directory management
- Type-safe path operations
- Comprehensive error handling
- Disk usage monitoring
- Automatic cleanup

### 4. Workflow Optimization
- **Fast capture mode** with ROI grouping
- **Parallel processing** (capture + server processing)
- **Auto-inspect mode** with keyboard shortcuts
- **Barcode scanning workflow** optimized for speed

## Quick Start

### Basic Usage

```python
from client.shared_folder_manager import SharedFolderManager

# Initialize
sfm = SharedFolderManager()

# Check server connection
if sfm.check_server_connection():
    print("✅ Shared folder accessible")
else:
    print("❌ Cannot access shared folder")

# Create session
session_id = "session_20251003_103000"
input_dir, output_dir = sfm.create_session_directories(session_id)

# Save captured image
import cv2
image = cv2.imread("test.jpg")
_, encoded = cv2.imencode('.jpg', image)

sfm.save_captured_image(
    session_id=session_id,
    image_data=encoded.tobytes(),
    filename="capture.jpg",
    metadata={'focus': 325, 'exposure': 1500}
)

# Read results
results = sfm.read_results_json(session_id)
if results:
    print(f"Overall: {results['overall_result']['passed']}")
```

### Running the Client Application

```bash
# Basic launch
python3 client_app_simple.py

# Or use the launcher script
cd ..
./start_client.sh
```

## Configuration

### Server Connection
Default server URL: `http://10.100.27.156:5000`

Can be changed in the UI or configured via:
```python
self.server_url = "http://your-server-ip:5000"
```

### Shared Folder Path
Default: `/mnt/visual-aoi-shared`

Can be customized:
```python
sfm = SharedFolderManager(base_path="/custom/path/to/shared")
```

### Camera Settings
Configured via:
- `../config/system/camera.json` - Camera hardware settings
- Product ROI configuration files - Per-product focus/exposure

## API Documentation

### SharedFolderManager API

For complete API documentation, see: `../docs/SHARED_FOLDER_ACCESS.md`

**Common Operations:**

```python
# Session management
sfm.create_session_directories(session_id)
sfm.cleanup_session(session_id, keep_output=True)

# Image operations
sfm.save_captured_image(session_id, image_data, filename, metadata)
sfm.get_roi_image_path(session_id, filename)
sfm.list_session_images(session_id, directory="input")

# Golden samples
sfm.list_golden_samples(product_name, roi_id=None)
sfm.get_golden_samples_directory(product_name)

# Maintenance
sfm.cleanup_temp_directories(max_age_hours=24)
sfm.get_disk_usage()
```

## Testing

### Run Unit Tests

```bash
# Test SharedFolderManager
python3 ../tests/test_shared_folder_manager.py

# Expected output:
# Ran 32 tests in 0.005s
# OK ✅
```

### Test Coverage

| Module | Tests | Status |
|--------|-------|--------|
| SharedFolderManager | 32 | ✅ 100% |

## Development

### Project Structure

```
client/
├── client_app_simple.py       # Main client application
├── shared_folder_manager.py   # Shared folder API (NEW)
├── example_integration.py     # Integration examples
└── README.md                  # This file

../docs/
├── SHARED_FOLDER_ACCESS.md    # Full API documentation
├── SHARED_FOLDER_IMPLEMENTATION_SUMMARY.md
└── ...

../tests/
└── test_shared_folder_manager.py  # Unit tests
```

### Adding New Features

1. **For shared folder operations:**
   - Add methods to `SharedFolderManager`
   - Add unit tests
   - Update documentation

2. **For UI features:**
   - Modify `client_app_simple.py`
   - Use SharedFolderManager for file operations
   - Follow existing patterns

### Code Standards

- **Type hints** on all function signatures
- **Docstrings** for all public methods
- **Error handling** with try/except and logging
- **Path operations** using `pathlib.Path`
- **No hardcoded paths** - use SharedFolderManager

## Migration Guide

### Updating Existing Code

**Step 1:** Import SharedFolderManager
```python
from client.shared_folder_manager import SharedFolderManager
```

**Step 2:** Initialize in `__init__`
```python
self.shared_folder = SharedFolderManager()
```

**Step 3:** Replace hardcoded paths
```python
# BEFORE:
session_dir = f"/home/.../shared/sessions/{self.session_id}"
output_dir = os.path.join(session_dir, "output")

# AFTER:
output_dir = self.shared_folder.get_session_output_directory(self.session_id)
```

**Complete examples:** See `example_integration.py`

## Troubleshooting

### Issue: Shared folder not accessible

**Symptoms:** `check_server_connection()` returns `False`

**Solutions:**
1. Check if server is running
2. Verify shared folder path exists
3. Check file permissions: `ls -la /mnt/visual-aoi-shared`
4. Ensure network connectivity to server

### Issue: Image files not found

**Symptoms:** `get_roi_image_path()` returns `None`

**Solutions:**
1. Verify session ID is correct
2. Check if server processing completed
3. List available images: `sfm.list_session_images(session_id, "output")`
4. Check server logs for processing errors

### Issue: Disk space full

**Symptoms:** `OSError` when saving images

**Solutions:**
1. Run maintenance: `sfm.cleanup_temp_directories()`
2. Check disk usage: `sfm.get_disk_usage()`
3. Clean old sessions: `sfm.cleanup_session(old_session_id, keep_output=False)`
4. Verify disk space: `df -h /mnt/visual-aoi-shared`

## Performance Tips

1. **Use grouped ROI capture** - captures multiple ROIs with same settings together
2. **Enable auto-inspect mode** - faster workflow with keyboard shortcuts
3. **Regular cleanup** - run `cleanup_temp_directories()` daily
4. **Monitor disk usage** - check `get_disk_usage()` periodically

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `F1` or `Ctrl+B` | Focus first barcode entry |
| `F2` or `Ctrl+Shift+C` | Clear all barcodes |
| `Enter` | Move to next device (or trigger inspection on last device) |
| `↑` / `↓` | Navigate between device entries |
| `Tab` | Move to next device |

## Dependencies

### Python Packages
```
tkinter          # GUI (standard library)
cv2 (opencv)     # Image processing
PIL (Pillow)     # Image display
requests         # HTTP client
numpy            # Array operations
```

### System Requirements
- Python 3.6+
- TIS GStreamer plugins (for TIS cameras)
- libcamera (for Raspberry Pi cameras)

## Server API Compatibility

**Compatible with:**
- ROI Structure v3.0 (with `is_device_barcode` field)
- Result Structure v2.0 (with device_summaries)
- Server API v1.0

**Server endpoints used:**
- `GET /api/health` - Health check
- `POST /api/session/create` - Create session
- `POST /api/session/{id}/inspect` - Run inspection
- `GET /api/products` - List products
- `GET /get_roi_groups/{product}` - Get ROI configuration
- `GET /api/schema/roi` - ROI structure
- `GET /api/schema/result` - Result structure

## Contributing

When adding features:

1. ✅ Use SharedFolderManager for file operations
2. ✅ Add unit tests for new functionality
3. ✅ Update documentation
4. ✅ Follow existing code style
5. ✅ Add logging for debugging
6. ✅ Handle errors gracefully

## Support

For issues or questions:
- Check `../docs/SHARED_FOLDER_ACCESS.md` for API details
- Review `example_integration.py` for usage examples
- Run unit tests to verify functionality
- Check server logs at `http://10.100.27.156:5000/logs`

## Change Log

### 2025-10-03
- ✅ Added SharedFolderManager module
- ✅ Implemented complete shared folder API
- ✅ Added 32 unit tests (100% coverage)
- ✅ Created comprehensive documentation
- ✅ Added integration examples

### Previous
- See `../docs/` for full change history

---

**Status:** Production Ready ✅  
**Version:** 1.0  
**Last Updated:** October 3, 2025
