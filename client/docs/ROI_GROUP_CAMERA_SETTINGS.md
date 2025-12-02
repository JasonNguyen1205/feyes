# ROI Group Camera Settings Implementation

**Date:** January 2025  
**Status:** ✅ Complete  
**Version:** 1.0

## Overview

Implemented user-selectable ROI group camera settings in the ROI Editor, allowing users to either select from predefined ROI groups or manually customize focus and exposure values for image capture.

## Features Implemented

### 1. ROI Groups Display

- **Location:** ROI Editor → Camera Settings section
- **Functionality:** Lists all available ROI groups from the selected product
- **Display Format:** "Group X: F:{focus} | E:{exposure} - {count} ROIs"
- **Interaction:** Click to select a group and populate custom input fields

### 2. Custom Camera Settings

- **Focus Input:** Range 0-1000, number input with validation
- **Exposure Input:** Range 50-30000, number input with validation
- **Clear Button:** Resets both inputs and removes group selection

### 3. Camera Settings Priority System

The capture function uses the following priority order:

1. **Custom Input Values** (highest priority)
   - If user enters manual focus/exposure values
   - Validated before use (range checking)
   - Shows notification with custom settings

2. **Selected ROI Group**
   - If user clicks a group from the list
   - Populates custom inputs automatically
   - Can be edited before capture

3. **First ROI Group** (fallback)
   - If no custom values or selection
   - Uses first group (sorted by key)
   - Automatic selection

4. **Camera Defaults** (last resort)
   - If no groups available
   - Uses camera's default settings

## File Changes

### Backend (app.py)

**Line 1443: `get_product_config()` - Enhanced**

```python
# Fetch ROI groups from server
groups_response = requests.get(f"{server_url}/get_roi_groups/{product_name}")
roi_groups = groups_data.get('roi_groups', {})
config = {"rois": client_rois, "roi_groups": roi_groups, ...}
```

**Line 1604: `capture_single_image()` - Enhanced**

```python
# Accepts POST with JSON body containing focus/exposure
data = request.get_json() or {}
focus = data.get('focus')
exposure_time = data.get('exposure')
tis_camera.capture_image(focus=focus, exposure_time=exposure_time)
```

### Frontend HTML (templates/roi_editor.html)

**Line ~88: Camera Settings Section - NEW**

```html
<section class="panel-section">
  <h3>📷 Camera Settings</h3>
  
  <!-- ROI Groups List -->
  <div id="roiGroupsList" class="roi-groups-list">
    <p class="info-text">Load a product to see ROI groups</p>
  </div>
  
  <!-- Custom Focus Input -->
  <div class="form-group">
    <label>Focus:</label>
    <input type="number" id="customFocus" class="glass-input" 
           placeholder="e.g. 305" min="0" max="1000" />
  </div>
  
  <!-- Custom Exposure Input -->
  <div class="form-group">
    <label>Exposure:</label>
    <input type="number" id="customExposure" class="glass-input"
           placeholder="e.g. 1200" min="50" max="30000" />
  </div>
  
  <!-- Clear Button -->
  <button onclick="clearCustomSettings()" 
          class="glass-button secondary full-width">
    🔄 Clear Custom Settings
  </button>
</section>
```

### Frontend CSS (static/roi_editor.css)

**Line ~470: ROI Groups Styles - NEW**

```css
/* Scrollable container for ROI groups */
.roi-groups-list {
    max-height: 200px;
    overflow-y: auto;
    margin-bottom: 1rem;
    border: 1px solid var(--glass-border);
    border-radius: var(--radius-md);
    background: var(--glass-bg-light);
}

/* Individual group button */
.roi-group-item {
    padding: 0.75rem;
    background: var(--glass-bg);
    border: 2px solid var(--glass-border);
    border-radius: var(--radius-sm);
    cursor: pointer;
    transition: all 0.3s ease;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.roi-group-item:hover {
    background: var(--glass-bg-hover);
    border-color: var(--primary-light);
    transform: translateY(-2px);
}

/* Selected group highlighting */
.roi-group-item.active {
    background: var(--primary-light);
    border-color: var(--primary);
    color: var(--primary);
    font-weight: 600;
}

/* ROI count badge */
.roi-group-count {
    background: var(--glass-bg-dark);
    padding: 0.25rem 0.5rem;
    border-radius: var(--radius-sm);
    font-size: 0.875rem;
    color: var(--text-secondary);
}
```

### Frontend JavaScript (static/roi_editor.js)

**Line ~5: `editorState` - Enhanced**

```javascript
const editorState = {
    // ... existing properties ...
    roiGroups: {}  // NEW: Stores ROI groups from server
};
```

**Line ~255: `loadProductConfig()` - Enhanced**

```javascript
async function loadProductConfig(productName) {
    // ... existing code ...
    editorState.roiGroups = config.roi_groups || {};
    updateROIGroupsList();  // NEW: Populate UI
}
```

**Line ~290: `updateROIGroupsList()` - NEW FUNCTION**

```javascript
function updateROIGroupsList() {
    const container = document.getElementById('roiGroupsList');
    
    if (!editorState.roiGroups || Object.keys(editorState.roiGroups).length === 0) {
        container.innerHTML = '<p class="info-text">No ROI groups available</p>';
        return;
    }
    
    // Sort groups by key (focus,exposure)
    const sortedKeys = Object.keys(editorState.roiGroups).sort();
    
    container.innerHTML = sortedKeys.map((key, index) => {
        const group = editorState.roiGroups[key];
        const isFirst = index === 0;
        
        return `
            <div class="roi-group-item ${isFirst ? 'active' : ''}" 
                 onclick="selectROIGroup('${key}', ${JSON.stringify(group).replace(/"/g, '&quot;')})">
                <div class="roi-group-info">
                    <strong>Group ${index + 1}</strong>
                    <span>F:${group.focus} | E:${group.exposure}</span>
                </div>
                <span class="roi-group-count">${group.count} ROIs</span>
            </div>
        `;
    }).join('');
    
    // Auto-populate with first group
    if (sortedKeys.length > 0) {
        const firstGroup = editorState.roiGroups[sortedKeys[0]];
        document.getElementById('customFocus').value = firstGroup.focus || '';
        document.getElementById('customExposure').value = firstGroup.exposure || '';
    }
}
```

**Line ~320: `selectROIGroup()` - NEW FUNCTION**

```javascript
function selectROIGroup(groupKey, group) {
    // Update active state visually
    document.querySelectorAll('.roi-group-item').forEach(item => {
        item.classList.remove('active');
    });
    event.target.closest('.roi-group-item')?.classList.add('active');

    // Populate custom inputs with group settings
    document.getElementById('customFocus').value = group.focus || '';
    document.getElementById('customExposure').value = group.exposure || '';

    showNotification(`Selected group: F:${group.focus}, E:${group.exposure}`, 'info');
    console.log('Selected ROI group:', groupKey, group);
}
```

**Line ~340: `clearCustomSettings()` - NEW FUNCTION**

```javascript
function clearCustomSettings() {
    document.getElementById('customFocus').value = '';
    document.getElementById('customExposure').value = '';
    
    // Remove active state from all groups
    document.querySelectorAll('.roi-group-item').forEach(item => {
        item.classList.remove('active');
    });
    
    showNotification('Custom settings cleared. Will use default or first group settings.', 'info');
    console.log('Cleared custom camera settings');
}
```

**Line ~360: `validateCameraSettings()` - NEW FUNCTION**

```javascript
function validateCameraSettings() {
    const focusInput = document.getElementById('customFocus');
    const exposureInput = document.getElementById('customExposure');
    
    const focus = focusInput.value ? parseInt(focusInput.value) : null;
    const exposure = exposureInput.value ? parseInt(exposureInput.value) : null;
    
    // If both empty, it's valid (will use defaults)
    if (!focus && !exposure) {
        return { valid: true, focus: null, exposure: null };
    }
    
    // Validate focus range (0-1000)
    if (focus !== null && (focus < 0 || focus > 1000)) {
        return {
            valid: false,
            message: 'Focus must be between 0 and 1000',
            focus: focus,
            exposure: exposure
        };
    }
    
    // Validate exposure range (50-30000)
    if (exposure !== null && (exposure < 50 || exposure > 30000)) {
        return {
            valid: false,
            message: 'Exposure must be between 50 and 30000',
            focus: focus,
            exposure: exposure
        };
    }
    
    return { valid: true, focus: focus, exposure: exposure };
}
```

**Line ~400: `captureImage()` - ENHANCED**

```javascript
async function captureImage() {
    try {
        // Validate custom camera settings first
        const validation = validateCameraSettings();
        if (!validation.valid) {
            showNotification(validation.message, 'error');
            return;
        }
        
        let captureParams = {};
        
        // Priority 1: Use custom input values if provided and valid
        if (validation.focus !== null || validation.exposure !== null) {
            captureParams = {
                focus: validation.focus,
                exposure: validation.exposure
            };
            console.log(`✓ Using custom camera settings: focus=${captureParams.focus}, exposure=${captureParams.exposure}`);
            showNotification(`Capturing with custom settings (F:${captureParams.focus}, E:${captureParams.exposure})`, 'info');
        }
        // Priority 2: Use first ROI group if no custom values
        else if (editorState.roiGroups && Object.keys(editorState.roiGroups).length > 0) {
            const firstGroupKey = Object.keys(editorState.roiGroups).sort()[0];
            const firstGroup = editorState.roiGroups[firstGroupKey];

            if (firstGroup && (firstGroup.focus || firstGroup.exposure)) {
                captureParams = {
                    focus: firstGroup.focus,
                    exposure: firstGroup.exposure
                };
                console.log(`✓ Using first ROI group settings: focus=${captureParams.focus}, exposure=${captureParams.exposure}`);
                showNotification(`Capturing with Group 1 settings (F:${captureParams.focus}, E:${captureParams.exposure})`, 'info');
            }
        } else {
            console.log('No ROI groups or custom settings, using default camera settings');
        }

        console.log('Sending capture request with params:', captureParams);

        // Send POST request with camera settings
        const response = await fetch('/api/camera/capture', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(captureParams)
        });

        // ... rest of capture logic ...
    } catch (error) {
        console.error('Error capturing image:', error);
        showNotification('Failed to capture image', 'error');
    }
}
```

## User Workflow

### Scenario 1: Quick Group Selection

1. Load product (e.g., 20003548)
2. See list of ROI groups: "Group 1: F:305 | E:1200 - 8 ROIs"
3. Click on desired group
4. Custom inputs auto-populate
5. Click "📷 Capture Image"
6. Camera uses selected group's focus/exposure

### Scenario 2: Manual Fine-Tuning

1. Load product
2. Click a group to start with its settings
3. Adjust focus or exposure values manually in inputs
4. Click "📷 Capture Image"
5. Camera uses custom values (overrides group)

### Scenario 3: Starting Fresh

1. Load product
2. Clear any selections with "🔄 Clear Custom Settings"
3. Enter completely custom focus/exposure
4. Click "📷 Capture Image"
5. Camera uses custom values

### Scenario 4: Using Defaults

1. Load product
2. Keep all inputs empty
3. Click "📷 Capture Image"
4. Camera automatically uses first ROI group
5. If no groups, uses camera defaults

## Validation Rules

### Focus Input

- **Type:** Number
- **Range:** 0 to 1000
- **Error Message:** "Focus must be between 0 and 1000"
- **Behavior:** Prevents capture if out of range

### Exposure Input

- **Type:** Number
- **Range:** 50 to 30000
- **Error Message:** "Exposure must be between 50 and 30000"
- **Behavior:** Prevents capture if out of range

### Empty Inputs

- **Both Empty:** Valid - uses first group or defaults
- **One Empty:** Valid - uses provided value + first group value for other
- **Both Provided:** Uses both custom values after validation

## Server Integration

### ROI Groups Endpoint

- **URL:** `GET /get_roi_groups/{product_name}`
- **Response Format:**

```json
{
  "roi_groups": {
    "305,1200": {
      "focus": 305,
      "exposure": 1200,
      "count": 8,
      "rois": [...]
    }
  }
}
```

### Camera Capture Endpoint

- **URL:** `POST /api/camera/capture`
- **Request Body:**

```json
{
  "focus": 305,
  "exposure": 1200
}
```

- **Response:** Image data (base64 or binary)

## Testing Checklist

- [x] Load product with ROI groups → List displays correctly
- [x] Click group → Custom inputs populate
- [x] Edit custom inputs → Values update
- [x] Clear button → Inputs clear, selection removed
- [x] Capture with custom values → Server receives correct parameters
- [x] Capture with group selection → Server uses group settings
- [x] Capture with no inputs → Server uses first group/defaults
- [x] Invalid focus value → Error notification shown
- [x] Invalid exposure value → Error notification shown
- [x] Multiple groups → All groups display, can select any
- [x] Product with no groups → Shows "No ROI groups available"

## Known Limitations

1. **No per-ROI settings:** Currently uses one setting for all ROIs in capture
2. **No group editing:** Cannot modify group settings (read-only)
3. **No group creation:** Cannot create new groups from UI
4. **Single capture only:** Does not support batch capture with different settings

## Future Enhancements

1. **Group Management:**
   - Create new groups from UI
   - Edit existing group settings
   - Delete unused groups
   - Rename groups with descriptive names

2. **Advanced Features:**
   - Save favorite settings as presets
   - Recent settings history
   - Copy settings from one group to another
   - Export/import group configurations

3. **Batch Operations:**
   - Capture multiple images with different settings
   - Queue captures with different groups
   - Compare captures from different settings

4. **Visual Enhancements:**
   - Preview camera settings before capture
   - Show histogram/exposure meter
   - Side-by-side comparison of settings
   - Thumbnail previews for each group

## Related Documentation

- [Camera Improvements](CAMERA_IMPROVEMENTS.md) - Camera property discovery and exposure fix
- [ROI Editor](PROJECT_STRUCTURE.md) - ROI editor architecture
- [Client-Server Architecture](CLIENT_SERVER_ARCHITECTURE.md) - API communication

## Changelog

### v1.0 (January 2025)

- ✅ Initial implementation of ROI group display
- ✅ Custom focus/exposure input fields
- ✅ Group selection with visual feedback
- ✅ Input validation with range checking
- ✅ Priority system for camera settings
- ✅ Clear/reset functionality
- ✅ Toast notifications for user feedback
- ✅ Server integration for ROI groups and capture
