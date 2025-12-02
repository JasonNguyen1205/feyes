# ROI Configuration Editor - User Guide

**Date:** October 4, 2025  
**Version:** 1.0  
**Status:** ✅ Complete

## Overview

The ROI Configuration Editor is a comprehensive visual tool for defining and managing Region of Interest (ROI) configurations for different products in the Visual AOI system. It provides an intuitive canvas-based interface for drawing ROI rectangles, setting properties, and synchronizing with the server.

## Features

### 🎨 Canvas-Based Drawing
- **Interactive Canvas:** Draw ROI rectangles directly on reference images
- **Visual Feedback:** Real-time preview of ROI boundaries with color-coded types
- **Zoom & Pan:** Navigate large images with smooth zoom controls
- **Multiple Tools:** Select, draw, pan, and zoom tools

### 🔧 ROI Configuration
- **ROI Types:** Support for barcode, OCR, compare, and text match ROIs
- **Device Assignment:** Assign ROIs to devices 1-4
- **Coordinates:** Precise coordinate editing (X1, Y1, X2, Y2)
- **Thresholds:** AI similarity threshold configuration (0.0 - 1.0)
- **Type-Specific Settings:** Custom settings for each ROI type

### 🌐 Server Integration
- **Product Management:** Load and save configurations per product
- **Auto-Sync:** Proxy API calls through client to avoid CORS
- **Validation:** Configuration validation before saving
- **Export:** Export configurations as JSON files

### 📷 Image Handling
- **Camera Capture:** Capture reference images directly from TIS camera
- **File Upload:** Upload existing images for ROI definition
- **Image Info:** Display image dimensions and properties

## Getting Started

### 1. Access the Editor

Navigate to the ROI editor from the main interface:
- Click the **"🎯 ROI Configuration Editor"** button in the header
- Or visit: `http://127.0.0.1:5100/roi-editor`

### 2. Connect to Server

1. Enter server URL (default: `http://10.100.27.156:5000`)
2. Click **Connect**
3. Wait for "✓ Connected" status

### 3. Select Product

1. Choose product from dropdown (populated from server)
2. Click **Load Configuration** to load existing ROIs
3. Or click **New Configuration** to start fresh

### 4. Load Reference Image

**Option A: Capture from Camera**
- Ensure camera is initialized in main interface
- Click **📷 Capture from Camera**
- Image will be captured and loaded automatically

**Option B: Upload Image**
- Click **📁 Upload Image**
- Select image file from your computer
- Image will be loaded onto canvas

### 5. Define ROIs

#### Drawing a New ROI

1. Select **✏️ Draw** tool from toolbar
2. Click and drag on the canvas to draw rectangle
3. Release mouse to create ROI
4. ROI appears in the list with auto-generated ID

#### Editing ROI Properties

1. Click on an ROI in the list or canvas (with Select tool)
2. Properties panel populates on the right
3. Edit properties:
   - **ROI ID:** Unique identifier (numeric)
   - **ROI Type:** barcode, ocr, compare, text
   - **Device ID:** 1, 2, 3, or 4
   - **Coordinates:** [X1, Y1, X2, Y2]
   - **AI Threshold:** 0.0 to 1.0 (default 0.8)
   - **Enabled:** Toggle ROI active/inactive
   - **Notes:** Optional description

#### Type-Specific Settings

**Barcode ROI:**
- Expected Pattern: Regex pattern for validation (optional)

**OCR ROI:**
- Expected Text: Text to expect
- Case Sensitive: Enable/disable case sensitivity

**Compare ROI:**
- Comparison Mode: Structural, Histogram, or Pixel-by-Pixel
- Golden Sample: Capture reference image

**Text Match ROI:**
- Expected Text: Exact text to match
- Match Mode: Exact, Contains, or Regex

### 6. Manage ROIs

#### Select ROI
- Click **☝️ Select** tool
- Click on ROI in canvas or list
- Selected ROI highlights in orange

#### Delete ROI
- Select the ROI to delete
- Click **🗑️ Delete Selected**
- Confirm deletion

#### Navigate Canvas
- **Pan:** Select ✋ Pan tool, click and drag
- **Zoom:** Use 🔍 Zoom tool, mouse wheel, or +/- buttons
- **Fit:** Click **Fit** to auto-fit image to screen

### 7. Save Configuration

1. Click **✅ Validate** to check configuration
2. Fix any validation errors
3. Click **💾 Save to Server**
4. Wait for "✓ Configuration saved" message

### 8. Export Configuration

- Click **📥 Export JSON** to download configuration file
- File includes all ROI definitions and metadata
- Can be used for backup or migration

## UI Layout

```
┌─────────────────────────────────────────────────────────┐
│                        HEADER                           │
│    🎯 ROI Configuration Editor    ← Back | 🌓 Theme   │
├──────────┬──────────────────────────────┬──────────────┤
│   LEFT   │         CENTER CANVAS        │    RIGHT     │
│  PANEL   │                              │   PANEL      │
│          │                              │              │
│ • Server │      [Image with ROIs]       │ • Properties │
│ • Product│                              │ • Summary    │
│ • Image  │      🖱️ Drawing Area         │ • Actions    │
│ • Tools  │                              │              │
│ • ROI    │    X: 0, Y: 0 | 1920x1080   │              │
│   List   │                              │              │
└──────────┴──────────────────────────────┴──────────────┘
```

## ROI Color Coding

- **Barcode:** 🟢 Green (#4CAF50)
- **OCR:** 🔵 Blue (#2196F3)
- **Compare:** 🟣 Purple (#9C27B0)
- **Text:** 🔴 Red (#FF5722)
- **Selected:** 🟠 Orange (#FF9800)

## Keyboard Shortcuts

- **Delete:** Delete selected ROI (future)
- **Ctrl + Z:** Undo last action (future)
- **Ctrl + S:** Save configuration (future)
- **Escape:** Deselect ROI (future)

## Server API Integration

The ROI editor integrates with the following server endpoints:

### GET /api/products
**Purpose:** List all available products  
**Response:**
```json
{
  "products": ["20003548", "20001234", ...]
}
```

### GET /api/products/{product_name}/config
**Purpose:** Load ROI configuration for a product  
**Response:**
```json
{
  "product_name": "20003548",
  "rois": [
    {
      "roi_id": 1,
      "roi_type_name": "barcode",
      "device_id": 1,
      "coordinates": [100, 200, 300, 400],
      "ai_threshold": 0.8,
      "enabled": true
    }
  ]
}
```

### POST /api/products/{product_name}/config
**Purpose:** Save ROI configuration  
**Request Body:**
```json
{
  "product_name": "20003548",
  "rois": [...]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Configuration saved successfully"
}
```

### GET /api/camera/capture
**Purpose:** Capture image from camera  
**Response:**
```json
{
  "success": true,
  "image_path": "roi_editor/20251004_123456.jpg",
  "width": 7716,
  "height": 5360
}
```

## Client Proxy Routes

All server API calls are proxied through the client to avoid CORS issues:

**Client Route → Server Route**
- `GET /api/products/{name}/config` → `GET http://server/api/products/{name}/config`
- `POST /api/products/{name}/config` → `POST http://server/api/products/{name}/config`
- `GET /api/camera/capture` → Captures from local TIS camera

## Configuration Format

### ROI Object Schema

```json
{
  "roi_id": 1,                    // Unique identifier (int)
  "roi_type_name": "compare",     // Type: barcode, ocr, compare, text
  "device_id": 1,                 // Device assignment: 1-4
  "coordinates": [100, 200, 300, 400],  // [x1, y1, x2, y2]
  "ai_threshold": 0.8,            // Similarity threshold (0.0-1.0)
  "enabled": true,                // Active/inactive
  "notes": "Description",         // Optional notes
  
  // Type-specific fields
  "expected_pattern": "^\\d{12}$",  // Barcode regex
  "expected_text": "PASS",        // OCR/Text expected value
  "case_sensitive": false,        // OCR case sensitivity
  "comparison_mode": "structural", // Compare mode
  "match_mode": "exact"           // Text match mode
}
```

### Full Configuration Example

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
      "expected_pattern": "^\\d{7}-\\d{7}-\\d{7}-\\d{3}$",
      "notes": "Device 1 barcode"
    },
    {
      "roi_id": 5,
      "roi_type_name": "compare",
      "device_id": 1,
      "coordinates": [3619, 3369, 3843, 3644],
      "ai_threshold": 0.85,
      "enabled": true,
      "comparison_mode": "structural",
      "notes": "PCB component check"
    },
    {
      "roi_id": 6,
      "roi_type_name": "ocr",
      "device_id": 1,
      "coordinates": [3727, 4294, 3953, 4485],
      "ai_threshold": 0.8,
      "enabled": true,
      "expected_text": "PCB",
      "case_sensitive": false,
      "notes": "PCB text verification"
    }
  ]
}
```

## Validation Rules

The editor validates configurations before saving:

1. **Product Required:** Must select a product
2. **ROI Count:** At least one ROI must be defined
3. **Unique IDs:** No duplicate ROI IDs
4. **Valid Coordinates:** X2 > X1 and Y2 > Y1
5. **Threshold Range:** AI threshold between 0.0 and 1.0
6. **Device Range:** Device ID between 1 and 4

## Troubleshooting

### Connection Failed
**Problem:** Cannot connect to server  
**Solution:**
- Verify server is running
- Check server URL is correct
- Ensure network connectivity
- Check firewall settings

### Camera Capture Failed
**Problem:** Cannot capture from camera  
**Solution:**
- Initialize camera in main interface first
- Check camera connection
- Ensure camera is not in use by another process

### ROI Not Saving
**Problem:** Save operation fails  
**Solution:**
- Run validation first
- Check server logs for errors
- Verify product exists on server
- Ensure proper permissions

### Canvas Not Updating
**Problem:** Changes don't reflect on canvas  
**Solution:**
- Refresh page (F5)
- Clear browser cache (Ctrl+F5)
- Check console for JavaScript errors

### Image Too Large
**Problem:** Canvas performance issues with large images  
**Solution:**
- Use zoom and pan tools
- Consider resizing image before upload
- Close other browser tabs

## Best Practices

### ROI Definition
1. **Use High-Quality Images:** Capture clear, well-lit reference images
2. **Consistent Lighting:** Ensure lighting matches production conditions
3. **Tight Bounds:** Draw ROIs as tightly as possible around features
4. **Avoid Overlap:** Minimize ROI overlap unless necessary
5. **Logical Grouping:** Group related ROIs by device

### Threshold Settings
- **Start High:** Begin with 0.8 threshold, adjust down if too strict
- **Test Thoroughly:** Test with multiple sample images
- **Document Changes:** Use notes field to explain threshold choices

### Configuration Management
1. **Regular Backups:** Export configurations regularly
2. **Version Control:** Keep track of configuration changes
3. **Test Before Production:** Validate in test environment first
4. **Document Differences:** Note changes between product variants

## Future Enhancements

Planned features for future releases:

- [ ] Copy/paste ROIs between products
- [ ] Undo/redo functionality
- [ ] Keyboard shortcuts
- [ ] Batch ROI creation
- [ ] ROI templates library
- [ ] Golden sample management integration
- [ ] Multi-select and bulk edit
- [ ] ROI grouping and layers
- [ ] Configuration diff/compare tool
- [ ] Auto-suggest ROI placement (AI)

## Technical Details

### Files Created

```
templates/roi_editor.html    # Main HTML interface
static/roi_editor.css        # Styling and layout
static/roi_editor.js         # Canvas interaction and logic
app.py                       # Flask routes (updated)
docs/ROI_EDITOR.md          # This documentation
```

### Dependencies

- **Flask:** Web server framework
- **HTML5 Canvas:** Drawing and image display
- **JavaScript ES6:** Client-side logic
- **CSS3:** Modern styling with glass effects
- **TIS Camera:** Image capture integration

### Browser Compatibility

- ✅ Chrome/Edge (Recommended)
- ✅ Firefox
- ✅ Safari
- ⚠️ IE11 (Not supported)

### Performance

- **Recommended Resolution:** 1920x1080 or higher
- **Max Image Size:** 7716x5360 (TIS camera native)
- **ROI Limit:** 100+ ROIs per configuration
- **Zoom Range:** 10% to 500%

## Support

For issues or questions:
1. Check this documentation
2. Review console logs (F12)
3. Check server API documentation
4. Refer to main application docs

---

**Created:** October 4, 2025  
**Author:** Visual AOI Development Team  
**Version:** 1.0  
**Status:** Production Ready ✅
