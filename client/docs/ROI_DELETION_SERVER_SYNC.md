# ROI Deletion Server Synchronization

**Date:** October 9, 2025  
**Feature:** Automatic server sync when deleting ROIs from ROI Editor  
**Status:** ✅ Implemented

---

## Overview

When a user deletes an ROI from the ROI list in the ROI Editor, the deletion is now automatically synchronized with the server. This ensures the server's ROI configuration stays in sync with the client's state without requiring a manual "Save Configuration" action.

---

## Implementation Details

### Modified Function: `deleteSelectedROI()`

**File:** `static/roi_editor.js`  
**Lines:** 808-870 (approximately)

**Key Changes:**

1. **Changed to async function** - Enables await for fetch API call
2. **Added server sync logic** - Automatically saves configuration after deletion
3. **Enhanced user feedback** - Shows sync status and handles errors gracefully
4. **Updated confirmation message** - Informs user about server update

---

## Behavior Flow

### Step 1: User Initiates Deletion

```javascript
// User clicks delete button or presses Delete key
deleteSelectedROI()
```

### Step 2: Confirmation Dialog

```
┌────────────────────────────────────────────────────┐
│  Delete ROI 5?                                     │
│                                                     │
│  This will also update the server configuration.   │
│                                                     │
│           [Cancel]  [OK]                           │
└────────────────────────────────────────────────────┘
```

### Step 3: Local Deletion

```javascript
// Remove from local ROI array
editorState.rois.splice(index, 1);
editorState.selectedROI = null;

// Update UI
updateROIList();
updatePropertiesPanel();
updateSummary();
redrawCanvas();
```

### Step 4: Server Synchronization

```javascript
// POST updated configuration to server
POST /api/products/{product_name}/config
Body: {
    "product_name": "20003548",
    "rois": [...remaining ROIs...]
}
```

### Step 5: User Feedback

- **Success:** `✓ ROI 5 deleted and synced to server`
- **Failure:** `⚠️ ROI deleted locally but server sync failed: {error}`
- **Not connected:** `⚠️ ROI deleted locally only (not connected to server)`

---

## Code Implementation

### Before (Old)

```javascript
function deleteSelectedROI() {
    if (!editorState.selectedROI) {
        showNotification('No ROI selected', 'error');
        return;
    }

    if (confirm(`Delete ROI ${editorState.selectedROI.roi_id}?`)) {
        const index = editorState.rois.indexOf(editorState.selectedROI);
        editorState.rois.splice(index, 1);
        editorState.selectedROI = null;

        updateROIList();
        updatePropertiesPanel();
        updateSummary();
        redrawCanvas();

        showNotification('ROI deleted', 'success');
    }
}
```

**Issues:**

- ❌ Deletion only local, not synced to server
- ❌ User must manually click "Save Configuration"
- ❌ Risk of forgetting to save (data loss)
- ❌ No indication of server state

### After (New)

```javascript
async function deleteSelectedROI() {
    if (!editorState.selectedROI) {
        showNotification('No ROI selected', 'error');
        return;
    }

    const roiId = editorState.selectedROI.roi_id;
    
    if (confirm(`Delete ROI ${roiId}?\n\nThis will also update the server configuration.`)) {
        // 1. Delete locally
        const index = editorState.rois.indexOf(editorState.selectedROI);
        editorState.rois.splice(index, 1);
        editorState.selectedROI = null;

        updateROIList();
        updatePropertiesPanel();
        updateSummary();
        redrawCanvas();

        showNotification(`ROI ${roiId} deleted`, 'success');

        // 2. Sync with server (NEW)
        if (editorState.connected && editorState.currentProduct) {
            try {
                showNotification('Syncing with server...', 'info');

                const config = {
                    product_name: editorState.currentProduct,
                    rois: editorState.rois
                };

                const response = await fetch(
                    `/api/products/${editorState.currentProduct}/config`,
                    {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(config)
                    }
                );

                if (!response.ok) {
                    throw new Error(`Server returned ${response.status}`);
                }

                const result = await response.json();
                showNotification(`✓ ROI ${roiId} deleted and synced to server`, 'success');
                console.log('✅ Server sync successful:', result);
            } catch (error) {
                console.error('❌ Failed to sync deletion to server:', error);
                showNotification(
                    `⚠️ ROI deleted locally but server sync failed: ${error.message}`, 
                    'warning'
                );
            }
        } else {
            // 3. Handle disconnected state
            if (!editorState.connected) {
                showNotification('⚠️ ROI deleted locally only (not connected to server)', 'warning');
            }
            if (!editorState.currentProduct) {
                showNotification('⚠️ ROI deleted locally only (no product selected)', 'warning');
            }
        }
    }
}
```

**Benefits:**

- ✅ Automatic server sync after deletion
- ✅ Clear user feedback on sync status
- ✅ Handles errors gracefully with warnings
- ✅ Works offline (local deletion still possible)
- ✅ Prevents data loss from forgotten saves

---

## API Endpoint

**Endpoint:** `POST /api/products/{product_name}/config`

**Request Body:**

```json
{
    "product_name": "20003548",
    "rois": [
        {
            "roi_id": 1,
            "roi_type_name": "compare",
            "device_id": 1,
            "coordinates": [100, 200, 300, 400],
            "detection_method": "mobilenet",
            "ai_threshold": 0.8,
            "focus": 305,
            "exposure": 1200,
            "enabled": true,
            "notes": ""
        },
        // ... remaining ROIs after deletion
    ]
}
```

**Success Response (200):**

```json
{
    "message": "Configuration saved successfully",
    "roi_count": 9,
    "product_name": "20003548"
}
```

**Error Response (400/500):**

```json
{
    "error": "Validation failed",
    "details": ["ROI 1: coordinates must be array of 4 numbers"]
}
```

---

## User Experience

### Success Scenario

1. **User Action:** Clicks delete button on ROI 5
2. **Confirmation:** Dialog appears with warning about server update
3. **User Confirms:** Clicks OK
4. **Immediate Feedback:** "ROI 5 deleted" notification (green)
5. **Syncing:** "Syncing with server..." notification (blue)
6. **Success:** "✓ ROI 5 deleted and synced to server" (green)
7. **Result:** ROI removed from list, server updated, UI refreshed

**Total Time:** ~500-1000ms (including network request)

### Failure Scenario

1. **User Action:** Deletes ROI 5
2. **Local Success:** ROI removed from UI
3. **Server Error:** Network timeout or server unavailable
4. **Warning:** "⚠️ ROI deleted locally but server sync failed: Network error"
5. **User Action:** Can manually click "Save Configuration" to retry

**Fallback:** Local deletion persists, user can retry sync later

### Offline Scenario

1. **User Action:** Deletes ROI 5 (not connected to server)
2. **Local Success:** ROI removed from UI
3. **Warning:** "⚠️ ROI deleted locally only (not connected to server)"
4. **Result:** Changes stay in browser until server connection restored

---

## Error Handling

### Connection Errors

```javascript
catch (error) {
    // Network timeout, DNS failure, etc.
    showNotification(`⚠️ ROI deleted locally but server sync failed: ${error.message}`, 'warning');
}
```

### Server Errors (4xx/5xx)

```javascript
if (!response.ok) {
    throw new Error(`Server returned ${response.status}`);
}
// Shows: "⚠️ ROI deleted locally but server sync failed: Server returned 500"
```

### Validation Errors

```json
{
    "error": "ROI validation failed",
    "details": ["ROI coordinates required"]
}
```

---

## State Management

### editorState Object

```javascript
{
    connected: true,              // Server connection status
    currentProduct: "20003548",   // Active product
    rois: [...],                  // Array of ROI objects
    selectedROI: null             // Currently selected ROI (null after delete)
}
```

### State Changes During Deletion

**Before:**

```javascript
editorState.rois = [ROI1, ROI2, ROI3, ROI4, ROI5]
editorState.selectedROI = ROI5
```

**After Local Deletion:**

```javascript
editorState.rois = [ROI1, ROI2, ROI3, ROI4]
editorState.selectedROI = null
```

**After Server Sync:**

```javascript
// Server ROI configuration updated to match client
// No state change needed on client side
```

---

## Testing

### Test Case 1: Successful Deletion and Sync

**Steps:**

1. Connect to server
2. Load product "20003548"
3. Select ROI 5
4. Click "Delete" or press Delete key
5. Confirm deletion in dialog

**Expected:**

- ✅ ROI removed from list
- ✅ UI updates immediately
- ✅ "Syncing with server..." appears
- ✅ "✓ ROI 5 deleted and synced to server" appears
- ✅ Console shows: `✅ Server sync successful: {...}`
- ✅ Server ROI count decreases by 1

### Test Case 2: Deletion with Server Error

**Steps:**

1. Connect to server
2. Stop server (simulate network error)
3. Select and delete ROI 5
4. Confirm deletion

**Expected:**

- ✅ ROI removed from UI
- ✅ Warning: "⚠️ ROI deleted locally but server sync failed: ..."
- ✅ Console shows: `❌ Failed to sync deletion to server: ...`
- ✅ User can manually retry with "Save Configuration"

### Test Case 3: Offline Deletion

**Steps:**

1. Disconnect from server
2. Select and delete ROI 5
3. Confirm deletion

**Expected:**

- ✅ ROI removed from UI
- ✅ Warning: "⚠️ ROI deleted locally only (not connected to server)"
- ✅ Changes persist in browser session
- ✅ No network request attempted

### Test Case 4: Cancel Deletion

**Steps:**

1. Select ROI 5
2. Click "Delete"
3. Click "Cancel" in confirmation dialog

**Expected:**

- ✅ No changes to ROI list
- ✅ ROI 5 still selected
- ✅ No server request sent
- ✅ No notifications shown

---

## Console Logging

### Success Logs

```javascript
console.log('✅ Server sync successful:', result);
// Output: ✅ Server sync successful: {message: "Configuration saved successfully", roi_count: 9}
```

### Error Logs

```javascript
console.error('❌ Failed to sync deletion to server:', error);
// Output: ❌ Failed to sync deletion to server: TypeError: Failed to fetch
```

---

## Browser Compatibility

**Async/Await Support:**

- ✅ Chrome 55+
- ✅ Firefox 52+
- ✅ Safari 10.1+
- ✅ Edge 15+

**Fetch API Support:**

- ✅ Chrome 42+
- ✅ Firefox 39+
- ✅ Safari 10.1+
- ✅ Edge 14+

**All modern browsers supported** ✅

---

## Related Features

### Manual Save Configuration

- Still available via "Save Configuration" button
- Useful for bulk changes or retry after sync failure
- Function: `async function saveConfiguration()`

### Server Connection Management

- Managed by `editorState.connected` flag
- Set during server connection establishment
- Checked before attempting sync

### ROI Validation

- Performed on server side before saving
- Client validation can be added in future
- Server returns detailed error messages

---

## Future Enhancements

### Possible Improvements

1. **Undo/Redo Support**
   - Allow reverting accidental deletions
   - Store deletion history in memory
   - "Undo Delete" button with 5-second window

2. **Batch Deletion**
   - Select multiple ROIs and delete at once
   - Single server sync for all deletions
   - Improves efficiency for bulk operations

3. **Optimistic Updates**
   - Show success immediately
   - Sync in background
   - Revert on failure with notification

4. **Offline Queue**
   - Queue deletions when offline
   - Auto-sync when connection restored
   - Show pending changes indicator

5. **Confirmation Preferences**
   - "Don't ask again" checkbox
   - Save preference to localStorage
   - Hold Shift key to skip confirmation

---

## Troubleshooting

### Issue: Deletion succeeds but sync fails

**Symptom:** ROI removed from UI, warning notification appears

**Possible Causes:**

- Network connection lost
- Server temporarily unavailable
- Invalid ROI configuration
- Authentication token expired

**Solution:**

1. Check server is running
2. Verify network connection
3. Click "Save Configuration" to retry
4. Check browser console for detailed error

### Issue: Confirmation dialog doesn't show server warning

**Symptom:** Old confirmation message without sync warning

**Cause:** Browser cache serving old JavaScript

**Solution:**

1. Hard refresh: `Ctrl + Shift + R`
2. Clear browser cache
3. Restart browser

### Issue: Server returns 400 validation error

**Symptom:** Warning about ROI validation failed

**Cause:** Remaining ROIs have invalid configuration

**Solution:**

1. Check console for validation details
2. Fix invalid ROI properties
3. Click "Save Configuration" after fixing

---

## Summary

The ROI deletion feature now automatically synchronizes with the server, providing:

✅ **Immediate sync** - No manual save needed  
✅ **Clear feedback** - User knows sync status  
✅ **Error resilience** - Graceful failure handling  
✅ **Offline support** - Works without server  
✅ **Undo protection** - Confirmation dialog prevents accidents  

**Status:** ✅ Ready for use  
**Testing:** Recommended before production deployment
