# Shared Folder Access Feature

**Document Version:** 1.0  
**Date:** October 3, 2025  
**Status:** ✅ IMPLEMENTED

## Overview

The Shared Folder Access feature provides a centralized and robust interface for the Visual AOI client to interact with server-side shared folders. This eliminates the need for hardcoded paths throughout the codebase and provides a clean API for all file operations.

## Architecture

### Directory Structure

```
/mnt/visual-aoi-shared/
├── sessions/                      # Session-specific data
│   └── {session_id}/
│       ├── input/                # Client-captured images
│       │   ├── capture_F{focus}_E{exposure}.jpg
│       │   ├── capture_F{focus}_E{exposure}.jpg.metadata.json
│       │   └── metadata.json
│       └── output/               # Server processing results
│           ├── roi_{roi_id}_captured.jpg
│           ├── roi_{roi_id}_golden.jpg
│           └── results.json
├── golden_samples/               # Golden sample database
│   └── {product_name}/
│       ├── roi_{roi_id}_sample_1.jpg
│       ├── roi_{roi_id}_sample_2.jpg
│       └── ...
└── temp/                         # Temporary files
    └── client_{timestamp}/
```

### Data Flow

```
┌─────────────┐     Capture      ┌──────────────────┐
│   CLIENT    ├─────────────────>│ shared/sessions/ │
│             │    Images         │   /input/        │
└─────────────┘                   └──────────────────┘
      ^                                    │
      │                                    │ Process
      │                                    v
      │                           ┌──────────────────┐
      │    Results &              │     SERVER       │
      │    ROI Images             │   (Processing)   │
      └───────────────────────────┤                  │
                                  └──────────────────┘
                                           │
                                           │ Save Results
                                           v
                                  ┌──────────────────┐
                                  │ shared/sessions/ │
                                  │   /output/       │
                                  └──────────────────┘
```

## Implementation

### Core Module: `shared_folder_manager.py`

The `SharedFolderManager` class provides a comprehensive API for all shared folder operations:

```python
from client.shared_folder_manager import SharedFolderManager

# Initialize manager
sfm = SharedFolderManager(base_path="/mnt/visual-aoi-shared")

# Check server connection
if sfm.check_server_connection():
    print("Shared folder accessible")
```

### Key Features

#### 1. Session Management

```python
# Create session directories
input_dir, output_dir = sfm.create_session_directories(session_id)

# Save captured image
image_path = sfm.save_captured_image(
    session_id=session_id,
    image_data=image_bytes,
    filename="capture_F325_E1500.jpg",
    metadata={
        'focus': 325,
        'exposure': 1500,
        'timestamp': '2025-10-03T10:30:00',
        'rois': [1, 2, 3]
    }
)

# List images in session
input_images = sfm.list_session_images(session_id, directory="input")
output_images = sfm.list_session_images(session_id, directory="output")
```

#### 2. ROI Image Access

```python
# Get ROI image path for display
roi_image_path = sfm.get_roi_image_path(session_id, "roi_1_captured.jpg")
if roi_image_path:
    from PIL import Image
    img = Image.open(roi_image_path)
    img.show()

# Read ROI image data
roi_image_bytes = sfm.read_roi_image(session_id, "roi_1_captured.jpg")
if roi_image_bytes:
    # Process image bytes
    pass
```

#### 3. Golden Sample Management

```python
# Get golden samples directory
golden_dir = sfm.get_golden_samples_directory(product_name="20002810")

# List all golden samples for a product
all_samples = sfm.list_golden_samples(product_name="20002810")

# List golden samples for specific ROI
roi_samples = sfm.list_golden_samples(product_name="20002810", roi_id=3)
# Returns: ['roi_3_sample_1.jpg', 'roi_3_sample_2.jpg', ...]
```

#### 4. Results Access

```python
# Read results JSON
results = sfm.read_results_json(session_id, filename="results.json")
if results:
    print(f"Overall result: {results['overall_result']['passed']}")
    for roi_result in results['roi_results']:
        print(f"ROI {roi_result['roi_id']}: {roi_result['passed']}")
```

#### 5. Cleanup Operations

```python
# Cleanup session (keep output for history)
sfm.cleanup_session(session_id, keep_output=True)

# Cleanup session completely
sfm.cleanup_session(session_id, keep_output=False)

# Cleanup old temporary directories (older than 24 hours)
cleaned_count = sfm.cleanup_temp_directories(max_age_hours=24)
print(f"Cleaned up {cleaned_count} old temp directories")
```

#### 6. Disk Usage Monitoring

```python
# Get disk usage statistics
usage = sfm.get_disk_usage()
print(f"Total: {usage['total'] / 1024 / 1024:.2f} MB")
print(f"Sessions: {usage['sessions'] / 1024 / 1024:.2f} MB")
print(f"Golden Samples: {usage['golden_samples'] / 1024 / 1024:.2f} MB")
print(f"Temp: {usage['temp'] / 1024 / 1024:.2f} MB")
```

## Integration with Existing Client

### Before (Hardcoded Paths)

```python
# OLD CODE - scattered throughout client_app_simple.py
session_dir = f"/mnt/visual-aoi-shared/sessions/{self.session_id}"
output_dir = os.path.join(session_dir, "output")
roi_image_path = os.path.join(output_dir, roi_result['roi_image_file'])
```

### After (Using SharedFolderManager)

```python
# NEW CODE - centralized and maintainable
from client.shared_folder_manager import SharedFolderManager

class VisualAOIClient:
    def __init__(self):
        # Initialize shared folder manager
        self.shared_folder = SharedFolderManager()
        
    def display_roi_image(self, roi_result):
        # Clean API for accessing ROI images
        roi_image_path = self.shared_folder.get_roi_image_path(
            self.session_id, 
            roi_result['roi_image_file']
        )
        
        if roi_image_path:
            roi_img = Image.open(roi_image_path)
            # Display image...
```

## Benefits

### 1. **Centralized Path Management**
- All paths defined in one place
- Easy to update if directory structure changes
- No hardcoded paths scattered throughout code

### 2. **Robust Error Handling**
- Comprehensive error checking
- Detailed logging
- Graceful fallbacks

### 3. **Type Safety**
- Uses `pathlib.Path` for type-safe path operations
- Type hints for all methods
- Better IDE support and autocomplete

### 4. **Maintainability**
- Single source of truth for shared folder operations
- Easy to add new features
- Simplified testing

### 5. **Performance**
- Efficient file operations
- Batch operations support
- Lazy loading of images

## Usage Examples

### Example 1: Complete Inspection Workflow

```python
from client.shared_folder_manager import SharedFolderManager
import cv2

# Initialize
sfm = SharedFolderManager()
session_id = "session_20251003_103000"

# 1. Create session directories
input_dir, output_dir = sfm.create_session_directories(session_id)

# 2. Capture and save images
for focus, exposure in [(325, 1500), (350, 2000)]:
    image = capture_image(focus, exposure)
    _, encoded = cv2.imencode('.jpg', image)
    
    sfm.save_captured_image(
        session_id=session_id,
        image_data=encoded.tobytes(),
        filename=f"capture_F{focus}_E{exposure}.jpg",
        metadata={'focus': focus, 'exposure': exposure}
    )

# 3. Wait for server processing...
# (Server reads from input/, processes, writes to output/)

# 4. Read results
results = sfm.read_results_json(session_id)

# 5. Display ROI images
for roi_result in results['roi_results']:
    roi_image_path = sfm.get_roi_image_path(
        session_id, 
        roi_result['roi_image_file']
    )
    if roi_image_path:
        img = cv2.imread(str(roi_image_path))
        cv2.imshow(f"ROI {roi_result['roi_id']}", img)

# 6. Cleanup (keep output for history)
sfm.cleanup_session(session_id, keep_output=True)
```

### Example 2: Golden Sample Browser

```python
def browse_golden_samples(product_name: str):
    """Browse all golden samples for a product."""
    sfm = SharedFolderManager()
    
    # Get all golden samples
    samples = sfm.list_golden_samples(product_name)
    
    print(f"Golden samples for {product_name}:")
    for sample in samples:
        print(f"  - {sample}")
    
    # Get samples by ROI
    roi_groups = {}
    for sample in samples:
        # Extract ROI ID from filename (e.g., "roi_3_sample_1.jpg")
        if sample.startswith("roi_"):
            roi_id = int(sample.split('_')[1])
            if roi_id not in roi_groups:
                roi_groups[roi_id] = []
            roi_groups[roi_id].append(sample)
    
    print("\nGrouped by ROI:")
    for roi_id, roi_samples in sorted(roi_groups.items()):
        print(f"  ROI {roi_id}: {len(roi_samples)} samples")
```

### Example 3: Session History Viewer

```python
def view_session_history():
    """View all past inspection sessions."""
    sfm = SharedFolderManager()
    sessions_path = sfm.sessions_path
    
    if not sessions_path.exists():
        print("No sessions found")
        return
    
    print("Inspection Sessions:")
    print("-" * 60)
    
    for session_dir in sorted(sessions_path.iterdir()):
        if session_dir.is_dir():
            session_id = session_dir.name
            
            # Get session info
            input_images = sfm.list_session_images(session_id, "input")
            output_images = sfm.list_session_images(session_id, "output")
            results = sfm.read_results_json(session_id)
            
            print(f"\nSession: {session_id}")
            print(f"  Input images:  {len(input_images)}")
            print(f"  Output images: {len(output_images)}")
            
            if results:
                overall = results['overall_result']
                print(f"  Result: {'PASS' if overall['passed'] else 'FAIL'} "
                      f"({overall['passed_rois']}/{overall['total_rois']})")
```

## Error Handling

The `SharedFolderManager` provides comprehensive error handling:

```python
try:
    sfm = SharedFolderManager()
    
    # Check accessibility
    if not sfm.check_server_connection():
        print("ERROR: Shared folder not accessible")
        print("Possible causes:")
        print("  - Server not running")
        print("  - Network connection issues")
        print("  - Permission problems")
        sys.exit(1)
    
    # Safe operations with error handling
    roi_image_path = sfm.get_roi_image_path(session_id, filename)
    if roi_image_path:
        # File exists
        pass
    else:
        # File not found - handle gracefully
        logger.warning(f"ROI image not found: {filename}")
        # Show placeholder or default image
        
except OSError as e:
    logger.error(f"File system error: {e}")
    # Handle filesystem errors
    
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    # Handle other errors
```

## Configuration

The shared folder base path can be configured:

```python
# Default path
sfm = SharedFolderManager()  # Uses /mnt/visual-aoi-shared

# Custom path
sfm = SharedFolderManager(base_path="/custom/path/to/shared")

# From environment variable
import os
base_path = os.getenv('AOI_SHARED_PATH', '/mnt/visual-aoi-shared')
sfm = SharedFolderManager(base_path=base_path)

# From config file
import json
with open('config/client_settings.json') as f:
    config = json.load(f)
sfm = SharedFolderManager(base_path=config['shared_folder_path'])
```

## Testing

### Unit Tests

```python
import unittest
from client.shared_folder_manager import SharedFolderManager
from pathlib import Path
import tempfile
import shutil

class TestSharedFolderManager(unittest.TestCase):
    def setUp(self):
        # Create temporary test directory
        self.test_dir = tempfile.mkdtemp()
        self.sfm = SharedFolderManager(base_path=self.test_dir)
    
    def tearDown(self):
        # Cleanup
        shutil.rmtree(self.test_dir)
    
    def test_create_session_directories(self):
        session_id = "test_session_001"
        input_dir, output_dir = self.sfm.create_session_directories(session_id)
        
        self.assertTrue(input_dir.exists())
        self.assertTrue(output_dir.exists())
        self.assertEqual(input_dir.name, "input")
        self.assertEqual(output_dir.name, "output")
    
    def test_save_and_read_image(self):
        session_id = "test_session_002"
        self.sfm.create_session_directories(session_id)
        
        # Save test image
        test_data = b"fake_image_data"
        image_path = self.sfm.save_captured_image(
            session_id, test_data, "test.jpg"
        )
        
        self.assertTrue(image_path.exists())
        
        # Read back
        with open(image_path, 'rb') as f:
            read_data = f.read()
        
        self.assertEqual(test_data, read_data)
```

## Performance Considerations

### 1. Image Size Optimization
- Compress images before saving
- Use appropriate JPEG quality settings
- Consider image resolution needs

### 2. Caching
- Cache frequently accessed paths
- Use `pathlib.Path` caching

### 3. Batch Operations
- Use `list_session_images()` for batch operations
- Minimize individual file access calls

### 4. Cleanup Strategy
- Regular cleanup of old sessions
- Automatic temp file cleanup
- Configurable retention policies

## Security

### File Access Permissions
```python
# Ensure proper permissions
if not os.access(str(sfm.base_path), os.R_OK | os.W_OK):
    raise PermissionError("Insufficient permissions for shared folder")
```

### Path Traversal Prevention
```python
# SharedFolderManager prevents path traversal
# All paths are resolved relative to base_path
# No user-supplied paths can escape the shared folder
```

## Migration Guide

To migrate existing code to use `SharedFolderManager`:

### Step 1: Import the manager
```python
from client.shared_folder_manager import SharedFolderManager
```

### Step 2: Initialize in `__init__`
```python
class VisualAOIClient:
    def __init__(self):
        self.shared_folder = SharedFolderManager()
```

### Step 3: Replace hardcoded paths
```python
# Before:
session_dir = f"/mnt/visual-aoi-shared/sessions/{self.session_id}"
output_dir = os.path.join(session_dir, "output")

# After:
output_dir = self.shared_folder.get_session_output_directory(self.session_id)
```

### Step 4: Use path methods
```python
# Before:
roi_image_path = os.path.join(output_dir, roi_result['roi_image_file'])
if os.path.exists(roi_image_path):
    roi_img = Image.open(roi_image_path)

# After:
roi_image_path = self.shared_folder.get_roi_image_path(
    self.session_id, roi_result['roi_image_file']
)
if roi_image_path:
    roi_img = Image.open(roi_image_path)
```

## Future Enhancements

### 1. Remote Shared Folders
- Support for SMB/CIFS network shares
- NFS mount support
- Cloud storage integration (S3, Azure Blob)

### 2. Advanced Caching
- In-memory image cache
- LRU cache for frequently accessed images
- Cache invalidation strategies

### 3. Compression
- Automatic image compression
- Archive old sessions to ZIP
- Incremental backups

### 4. Monitoring
- Real-time disk usage monitoring
- File access statistics
- Performance metrics

## Troubleshooting

### Issue: Shared folder not accessible
**Symptoms:** `check_server_connection()` returns `False`

**Solutions:**
1. Check if server is running
2. Verify network connectivity
3. Check folder permissions
4. Ensure path exists

### Issue: Image files not found
**Symptoms:** `get_roi_image_path()` returns `None`

**Solutions:**
1. Verify session ID is correct
2. Check if server processing completed
3. Verify filename spelling
4. Check output directory exists

### Issue: Disk space full
**Symptoms:** `OSError` when saving images

**Solutions:**
1. Run `cleanup_temp_directories()`
2. Run `cleanup_session()` on old sessions
3. Check disk usage with `get_disk_usage()`
4. Implement retention policy

## References

- Client Application: `client/client_app_simple.py`
- Shared Folder Manager: `client/shared_folder_manager.py`
- Server API Documentation: http://10.100.27.156:5000/apidocs/
- ROI Schema: http://10.100.27.156:5000/api/schema/roi
- Result Schema: http://10.100.27.156:5000/api/schema/result

## Change Log

| Date | Version | Changes |
|------|---------|---------|
| 2025-10-03 | 1.0 | Initial implementation with full feature set |

---

**Status:** ✅ IMPLEMENTED  
**Next Steps:** 
1. Integrate into `client_app_simple.py`
2. Add unit tests
3. Add configuration file support
4. Implement remote storage options
