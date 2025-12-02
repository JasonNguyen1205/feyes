# ROI Editor - Quick Reference

## Access
**URL:** `http://127.0.0.1:5100/roi-editor`  
**From Main:** Click "🎯 ROI Configuration Editor" button

## Quick Start (5 Steps)

1. **Connect** → Enter server URL → Click "Connect"
2. **Select** → Choose product from dropdown
3. **Load** → Load existing config or create new
4. **Draw** → Capture/upload image → Draw ROIs on canvas
5. **Save** → Validate → Save to server

## Tools

| Tool | Icon | Shortcut | Description |
|------|------|----------|-------------|
| Select | ☝️ | - | Select and edit ROI |
| Draw | ✏️ | - | Draw new ROI rectangle |
| Pan | ✋ | - | Pan around image |
| Zoom | 🔍 | Wheel | Zoom in/out |

## ROI Types

| Type | Color | Use Case |
|------|-------|----------|
| Barcode | 🟢 Green | QR codes, barcodes |
| OCR | 🔵 Blue | Text recognition |
| Compare | 🟣 Purple | Visual matching |
| Text | 🔴 Red | Exact text match |

## Key Properties

- **ROI ID:** Unique number (1, 2, 3...)
- **Device ID:** 1-4 (device assignment)
- **Coordinates:** [X1, Y1, X2, Y2]
- **Threshold:** 0.0-1.0 (default 0.8)
- **Enabled:** On/Off toggle

## Canvas Controls

- **Zoom In:** + button or scroll up
- **Zoom Out:** - button or scroll down
- **Fit Screen:** Fit button
- **Pan:** Pan tool + drag

## Workflow

```
Connect → Select Product → Load Image → Draw ROIs → Set Properties → Validate → Save
```

## Common Tasks

### Create New ROI
1. Click Draw tool (✏️)
2. Click and drag on image
3. Edit properties in right panel
4. Adjust coordinates if needed

### Edit Existing ROI
1. Click Select tool (☝️)
2. Click ROI in list or canvas
3. Modify properties in right panel
4. Changes apply immediately

### Delete ROI
1. Select ROI
2. Click "🗑️ Delete Selected"
3. Confirm deletion

### Save Configuration
1. Click "✅ Validate"
2. Fix any errors
3. Click "💾 Save to Server"
4. Wait for confirmation

## Server Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/products` | GET | List products |
| `/api/products/{name}/config` | GET | Load config |
| `/api/products/{name}/config` | POST | Save config |
| `/api/camera/capture` | GET | Capture image |

## Validation Rules

✅ **Must Have:**
- Product selected
- At least 1 ROI
- Unique ROI IDs
- Valid coordinates (X2>X1, Y2>Y1)
- Threshold 0.0-1.0
- Device ID 1-4

## Tips

💡 **Best Practices:**
- Use high-quality reference images
- Draw tight ROI boundaries
- Start with threshold 0.8
- Test with multiple samples
- Export backups regularly

⚠️ **Common Mistakes:**
- Overlapping ROIs
- Too loose boundaries
- Wrong device assignment
- Threshold too strict/loose

## Keyboard Shortcuts (Planned)

- `Delete` - Delete selected ROI
- `Ctrl+Z` - Undo
- `Ctrl+S` - Save
- `Esc` - Deselect

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Can't connect | Check server URL and network |
| Camera fails | Initialize camera in main UI first |
| Can't save | Run validation, check server logs |
| Canvas slow | Zoom in, reduce image size |

## Files & Routes

**Pages:**
- Main: `http://127.0.0.1:5100/`
- Editor: `http://127.0.0.1:5100/roi-editor`

**Files:**
- `templates/roi_editor.html`
- `static/roi_editor.css`
- `static/roi_editor.js`

## Support

📚 Full Documentation: `docs/ROI_EDITOR.md`  
🔧 Server API: `http://10.100.27.156:5000/apidocs/`  
💬 Check console logs (F12) for errors

---

**Quick Help:** Press F12 → Console for detailed logs
