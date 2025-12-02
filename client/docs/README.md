# Visual AOI Client

Client application for Visual AOI (Automated Optical Inspection) system. Captures images from TIS industrial cameras and sends them to the Visual AOI Server for processing.

## Overview

The Visual AOI Client provides two interfaces:

### **Web Client (Recommended)** - `app.py`
- **Modern web-based interface** accessible from any browser
- **No installation required** for users
- **Remote access** from any device on network
- **Professional UI** with real-time updates
- **Multi-user support** (future enhancement)

### **Desktop Client** - `client/client_app.py`
- **Tkinter-based GUI** application
- **Direct hardware access** for production environments
- **Offline operation** capability
- **Traditional desktop application** experience

---

## Quick Start

### **Option 1: Web Client (app.py)** ⭐ Recommended

```bash
# Start the web server
python3 app.py

# Or use the startup script
./start_web_client.sh

# Access in browser
http://localhost:5100
```

**Features:**
- ✅ Modern professional UI
- ✅ Works on any device with browser
- ✅ No client installation needed
- ✅ Real-time camera feed
- ✅ API-driven architecture

### **Option 2: Desktop Client**

```bash
# Run desktop client
python3 client/client_app.py

# Or use the startup script
./start_client.sh
```

**Features:**
- ✅ Traditional desktop GUI
- ✅ Direct camera control
- ✅ Offline operation
- ✅ Production floor ready

---

## System Requirements

- **Linux** (primary) or Windows (secondary)
- **Python 3.8+**
- **TIS Camera** (The Imaging Source)
- **System packages**: `python3-gi` (GTK support for desktop client)

---

## Installation

```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt-get install python3-gi python3-gi-cairo gir1.2-gtk-3.0

# Create virtual environment (optional)
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS

# Install Python dependencies
pip install -r requirements.txt
```

---

## Architecture

### **Web Client Architecture**
```
Browser → Flask (app.py:5100) → AOI Server (port 5000) → Camera Hardware
```

### **Desktop Client Architecture**
```
Tkinter GUI (client_app.py) → AOI Server (port 5000) → Camera Hardware
```

**Common Features:**
- **TIS Camera SDK integration** for hardware control
- **REST API communication** with server
- **Real-time result visualization** with device grouping
- **Export functionality** for quality records
- **Multi-device support** with barcode management

## Configuration

### Server Connection

Configure server URL in the GUI or via environment:
```bash
export AOI_SERVER_URL=http://localhost:5000
```

### Camera Configuration

Edit `config/system/camera.json`:
```json
{
  "camera_hardware": {
    "serial": "30320436",
    "width": 7716,
    "height": 5360,
    "fps": "7/1",
    "format": "BGRA"
  },
  "camera_defaults": {
    "focus": 305,
    "exposure": 3000
  }
}
```

### Theme Settings

Edit `config/theme_settings.json` for UI appearance.

## Using the Client

### 1. Connect to Server
- Enter server URL (default: `http://localhost:5000`)
- Click "Connect" to establish connection
- Status indicator shows connection state

### 2. Initialize Camera
- Select camera from dropdown (auto-detected)
- Set default focus and exposure values
- Click "Initialize Camera"

### 3. Capture and Inspect
- Click "Capture Image" to take snapshot
- Image is automatically sent to server
- Results display in device-grouped format

### 4. View Results
- **Device summaries**: Per-device pass/fail status
- **ROI details**: Individual ROI inspection results
- **Barcode tracking**: Each device shows associated barcode
- **Visual feedback**: Green (pass) / Red (fail) indicators

### 5. Export Results
- Click "Export Results" to save as JSON
- Includes all ROI details and device summaries
- Timestamp and metadata included

## Camera Operations

### TIS Camera Integration

The client uses The Imaging Source SDK:
```python
sys.path.append('/path/to/visual-aoi/python/python-common')
import TIS
```

**Important**: Always use `TIS.SinkFormats.BGRA` format.

### Camera Troubleshooting

**Camera Not Found**
```bash
# Check camera connection
ls /dev/video*

# Test with TIS software
# Verify camera serial number matches config
```

**EBUSY Errors**
- Only client should access camera (never server)
- Ensure no other processes using camera
- Restart camera hardware if needed

**Image Quality Issues**
- Adjust focus and exposure in camera config
- Use preview mode to fine-tune settings
- Check lighting conditions

## Theme System

The client supports customizable themes:

```python
from src.ui import get_current_theme, apply_theme, set_theme

# Switch theme
set_theme('dark')  # or 'light'

# Apply to new widgets
widget = tk.Frame(parent)
apply_theme(widget)
```

## Development

### Testing

```bash
# Run client tests
pytest tests/

# Test client standalone
python test_client_standalone.py

# Test camera integration
python test_client_camera.py
```

### Adding New Features

1. **UI components**: Edit `src/ui.py` or `client/client_app.py`
2. **Camera control**: Edit `src/camera.py`
3. **API communication**: Edit client API methods in `client/client_app.py`
4. **Theme updates**: Edit `config/theme_settings.json`

## Multi-Device Display

The client displays results grouped by device (1-4):

```
Device 1: PASS (Barcode: ABC123)
  ✓ ROI 1: Compare - PASS (98.5% match)
  ✓ ROI 2: Barcode - PASS (ABC123)
  
Device 2: FAIL (Barcode: XYZ789)
  ✓ ROI 3: Compare - PASS (95.2% match)
  ✗ ROI 4: OCR - FAIL (Text mismatch)
```

## Server Integration

This client works with the Visual AOI Server:
- Repository: `visual-aoi-server`
- Server URL: Configure in client settings
- Supports multiple concurrent clients

## Deployment

### Standalone Installation

```bash
# Copy to target machine
scp -r visual-aoi-client/ user@target:/opt/

# Install on target
cd /opt/visual-aoi-client
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Desktop Integration (Linux)

Create `.desktop` file:
```ini
[Desktop Entry]
Name=Visual AOI Client
Exec=/opt/visual-aoi-client/.venv/bin/python /opt/visual-aoi-client/client/client_app.py
Icon=/opt/visual-aoi-client/icon.png
Type=Application
Categories=Development;
```

## Troubleshooting

### Common Issues

**TIS Library Not Found**
```bash
# Add to Python path
export PYTHONPATH=$PYTHONPATH:/path/to/python/python-common
```

**GTK Warnings**
- Install `python3-gi` via system package manager
- Do not install via pip

**Connection Refused**
- Verify server is running
- Check firewall settings
- Confirm server URL and port

**Image Transmission Errors**
- Check network bandwidth
- Reduce image resolution if needed
- Verify base64 encoding works

## License

MIT License - See LICENSE file for details

---
**Version**: 1.0 (October 2025) | **Python**: 3.8+
