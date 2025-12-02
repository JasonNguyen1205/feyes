# Golden Sample Management Feature

## Overview

The Visual AOI system now includes **Enhanced Golden Sample Management** that allows users to easily capture, manage, and promote golden samples directly from the inspection results interface.

## Features

### 🎯 **Take Golden Sample**
- **One-Click Capture**: Take the current ROI image as a golden sample directly from the inspection results
- **Smart Backup**: Automatically renames existing golden samples when a new one is captured
- **Compare ROIs Only**: Feature is only available for Compare-type ROIs (Type 2)

### 📁 **Manage Golden Samples**
- **View All Samples**: See all golden samples for a specific ROI in a dedicated management window
- **Visual Display**: Thumbnail view of each golden sample with metadata
- **Sample Information**: Shows creation time, file size, and sample type
- **Status Indication**: Clear indication of which sample is currently the "best golden"

### 🔄 **Promote Samples**
- **Make Best Golden**: Promote any alternative golden sample to become the primary reference
- **Automatic Backup**: Previous best golden is automatically backed up with timestamp
- **Smart Management**: Follows the enhanced golden matching file structure

### 🗑️ **Delete Samples**
- **Safe Deletion**: Delete alternative golden samples while protecting the primary reference
- **Prevention Logic**: Cannot delete the only remaining golden sample
- **Confirmation Required**: All deletions require user confirmation

## File Structure

The enhanced golden sample management follows the structured approach:

```
config/
└── products/
    └── {product_name}/
        └── golden_rois/
            └── roi_{roi_id}/
                ├── best_golden.jpg           # Current best reference (always tried first)
                ├── original_1647123456.jpg   # Alternative samples with timestamp
                └── original_1647123789_old_best.jpg  # Backed up previous best
```

### File Naming Convention

- **`best_golden.jpg`**: The current best reference image (always tried first in comparisons)
- **`original_{timestamp}.jpg`**: Alternative golden images that can be promoted
- **`original_{timestamp}_old_best.jpg`**: Backed up previous best golden when promoting

## User Interface

### In Inspection Results Detail View

Each Compare ROI now shows two new buttons:

1. **"Take Golden Sample"** (Green button)
   - Saves the current ROI image as the new best golden sample
   - Backs up any existing best golden sample
   - Shows confirmation dialog with details about what will happen

2. **"Manage Golden Samples"** (Blue button)
   - Opens dedicated golden sample management window
   - Shows all golden samples for this ROI
   - Provides promote and delete functionality

### Golden Sample Management Window

- **Thumbnail View**: Visual display of each golden sample
- **Sample Information**: 
  - Sample name and type
  - Creation timestamp
  - File size
  - Current status (Best Golden vs Alternative)
- **Action Buttons**:
  - **"Make Best Golden"**: Promote alternative to best (only shown for alternatives)
  - **"Delete"**: Remove sample (with safety checks)

## API Endpoints

### Save Golden Sample
```
POST /api/golden-sample/save
Content-Type: multipart/form-data

Form Data:
- product_name: string
- roi_id: string
- golden_image: file
```

### Get Golden Samples
```
GET /api/golden-sample/{product_name}/{roi_id}

Response:
{
  "golden_samples": [
    {
      "name": "best_golden.jpg",
      "type": "best_golden",
      "is_best": true,
      "created_time": "2023-12-09 14:30:15",
      "file_size": 45123,
      "image_data": "data:image/jpeg;base64,..."
    }
  ]
}
```

### Promote Golden Sample
```
POST /api/golden-sample/promote
Content-Type: application/json

{
  "product_name": "string",
  "roi_id": "string", 
  "sample_name": "string"
}
```

### Delete Golden Sample
```
DELETE /api/golden-sample/delete
Content-Type: application/json

{
  "product_name": "string",
  "roi_id": "string",
  "sample_name": "string"
}
```

## Usage Workflow

### 1. Taking a New Golden Sample

1. Run inspection to capture ROI images
2. Open the "View Details" window to see inspection results
3. Find the Compare ROI you want to use as golden sample
4. Click **"Take Golden Sample"** button
5. Confirm the action in the dialog
6. The ROI image is saved as `best_golden.jpg`
7. Any existing best golden is backed up automatically

### 2. Managing Existing Golden Samples

1. From the inspection results detail view, click **"Manage Golden Samples"**
2. The management window shows all golden samples for this ROI
3. **To promote an alternative**: Click "Make Best Golden" on any alternative sample
4. **To delete a sample**: Click "Delete" button (with confirmation)
5. **View sample details**: See creation time, file size, and current status

### 3. Integration with Inspection

The golden sample management integrates seamlessly with the existing inspection process:

- **Enhanced Golden Matching**: Uses the same file structure as the automatic golden promotion
- **AI Processing**: Compare ROIs automatically use `best_golden.jpg` as primary reference
- **Fallback Options**: Alternative samples are available for automatic promotion during inspection
- **Performance**: Best golden is always tried first for optimal speed

## Benefits

### For Operators
- **Easy Capture**: One-click golden sample creation from inspection results
- **Visual Management**: See all golden samples at a glance
- **Safe Operations**: Automatic backups prevent data loss
- **Clear Status**: Always know which sample is currently active

### For Quality Control
- **Multiple References**: Maintain multiple golden samples for different conditions
- **Historical Tracking**: Timestamped backups maintain history
- **Flexible Management**: Easy to change reference samples as needed
- **Audit Trail**: Clear naming convention shows sample evolution

### For System Performance
- **Optimized Matching**: Best golden is always tried first
- **Smart Promotion**: System can automatically promote better matches
- **Reduced Setup Time**: Quick golden sample updates without manual file management
- **Consistent Structure**: Standardized file organization across all products

## Technical Implementation

### Client Side
- Enhanced ROI detail frame with golden sample buttons
- Dedicated golden sample management window
- Image display with thumbnails and metadata
- Confirmation dialogs for all operations

### Server Side
- RESTful API endpoints for golden sample operations
- Enhanced golden matching file structure support
- Automatic backup and timestamp management
- Safety checks and validation

### File Operations
- Atomic file operations for data integrity
- Timestamp-based naming for uniqueness
- Automatic directory creation
- Safe backup procedures

The golden sample management feature provides a comprehensive, user-friendly interface for managing reference images while maintaining compatibility with the existing enhanced golden matching system.
