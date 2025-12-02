# ROI Deletion Server Sync - Quick Reference

## Feature

When deleting an ROI from the ROI Editor, it automatically syncs to the server.

## What Changed

- `deleteSelectedROI()` is now an **async function**
- Automatic `POST /api/products/{product}/config` after deletion
- Enhanced user feedback with sync status notifications

## User Experience

### Success Flow

1. User deletes ROI 5
2. Notification: "ROI 5 deleted" ✓
3. Notification: "Syncing with server..." ⏳
4. Notification: "✓ ROI 5 deleted and synced to server" ✓

### Failure Flow

1. User deletes ROI 5
2. Notification: "ROI 5 deleted" ✓
3. Notification: "⚠️ ROI deleted locally but server sync failed: {error}"
4. User can manually click "Save Configuration" to retry

### Offline Flow

1. User deletes ROI 5 (not connected)
2. Notification: "ROI 5 deleted" ✓
3. Notification: "⚠️ ROI deleted locally only (not connected to server)"

## API Endpoint

```
POST /api/products/{product_name}/config
Body: { "product_name": "20003548", "rois": [...] }
```

## Files Modified

- `static/roi_editor.js` - Function `deleteSelectedROI()`

## Benefits

✅ Automatic server sync (no manual save needed)  
✅ Data integrity (server always in sync)  
✅ Clear user feedback  
✅ Graceful error handling  
✅ Works offline  

## Testing

1. Delete ROI with server running → Should show success
2. Delete ROI with server offline → Should show warning
3. Delete ROI when disconnected → Should show local-only message

## Documentation

- Full docs: `docs/ROI_DELETION_SERVER_SYNC.md`
- Summary: `/tmp/roi_deletion_sync_summary.txt`
