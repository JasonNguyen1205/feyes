# Visual AOI Web Client - Getting Started

**Version:** 2.0.0  
**Date:** October 3, 2025  
**Application:** Web-based Visual AOI Client

---

## Overview

The Visual AOI Web Client is a modern web-based interface for the Visual AOI inspection system. It provides a professional, user-friendly interface accessible through any web browser.

---

## Quick Start

### **Option 1: Using Startup Script (Recommended)**

```bash
# Navigate to project directory
cd /home/jason_nguyen/visual-aoi-client

# Run the startup script
./start_web_client.sh
```

The script will:
- ✅ Check and free port 5100 if needed
- ✅ Verify Python dependencies
- ✅ Start the Flask web server
- ✅ Display the access URL

### **Option 2: Direct Python Command**

```bash
# Navigate to project directory
cd /home/jason_nguyen/visual-aoi-client

# Start the application
python3 app.py
```

---

## Accessing the Client

Once started, the web client is accessible at:

- **Local:** http://localhost:5100
- **Network:** http://127.0.0.1:5100
- **LAN:** http://<your-ip>:5100

**Open in your browser:**
```bash
# Automatically open in browser (Linux)
xdg-open http://localhost:5100

# Or manually navigate to:
http://localhost:5100
```

---

## Application Structure

```
app.py                          # Main Flask application (Web Server)
├── Routes (API Endpoints)
│   ├── /                      # Main UI (renders professional_index.html)
│   ├── /api/health            # Health check
│   ├── /api/server/connect    # Connect to AOI server
│   ├── /api/session           # Session management
│   ├── /api/cameras           # Camera management
│   ├── /api/inspect           # Run inspection
│   └── ... (more endpoints)
│
templates/
└── professional_index.html    # Modern web UI
    
static/
├── professional.css           # Styling
└── placeholder.png            # Assets

client/
├── client_app.py             # Desktop client (legacy)
└── client_app_simple.py      # Simplified desktop client

start_web_client.sh           # Startup script
start_client.sh               # Desktop client startup
```

---

## Architecture

### **Web-Based Client (app.py)**

```
┌─────────────────────────────────────────────────────────────┐
│                      Web Browser                             │
│  http://localhost:5100/                                      │
│                                                              │
│  • Modern UI with professional design                        │
│  • Real-time camera feed                                     │
│  • Inspection controls                                       │
│  • Result visualization                                      │
└──────────────────────┬───────────────────────────────────────┘
                       │ HTTP/REST API
                       ↓
┌─────────────────────────────────────────────────────────────┐
│              Flask Web Server (app.py)                       │
│              Running on port 5100                            │
│                                                              │
│  • API endpoints for inspection workflow                     │
│  • Camera integration (TIS cameras)                          │
│  • Session management                                        │
│  • Real-time image streaming                                │
└──────────────────────┬───────────────────────────────────────┘
                       │ HTTP/REST API
                       ↓
┌─────────────────────────────────────────────────────────────┐
│            AOI Server (Processing Backend)                   │
│            http://10.100.27.156:5000                        │
│                                                              │
│  • AI-based inspection processing                            │
│  • ROI configuration management                              │
│  • Product configuration                                     │
│  • Golden sample management                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Features

### ✅ **Web-Based Interface**
- Modern, professional UI design
- Accessible from any device on the network
- No installation required for users
- Responsive design

### ✅ **Camera Integration**
- TIS industrial camera support
- Live camera preview
- Automatic camera detection
- Multi-camera support

### ✅ **Inspection Workflow**
- Product selection
- Session management
- Multi-device support
- Device barcode management
- Grouped ROI capture (optimized)
- Real-time result display

### ✅ **API-Driven**
- RESTful API endpoints
- JSON-based communication
- Easy integration with other systems
- Comprehensive error handling

---

## Configuration

### **Server URL**

The default server URL is configured in `app.py`:

```python
server_url: str = "http://10.100.27.156:5000"
```

**To change:**
1. Edit `app.py`
2. Update the `server_url` in the `AOIState` class
3. Restart the application

**Or connect via UI:**
- Open the web interface
- Use the "Connect to Server" dialog
- Enter the server URL

---

### **Port Configuration**

The default port is **5100**. To change:

```python
# In app.py, at the bottom:
if __name__ == "__main__":
    app.run(debug=True, threaded=True, port=5100)  # Change port here
```

---

## Troubleshooting

### **Issue: Port Already in Use**

**Error:**
```
Address already in use
Port 5100 is in use by another program.
```

**Solution 1: Use startup script (automatically handles this)**
```bash
./start_web_client.sh
```

**Solution 2: Manual fix**
```bash
# Find process using port 5100
lsof -i :5100

# Kill the process
kill -9 <PID>

# Start the app
python3 app.py
```

---

### **Issue: Cannot Connect to Server**

**Error in UI:**
```
Failed to connect to server
```

**Solutions:**
1. **Check server is running**
   ```bash
   curl http://10.100.27.156:5000/api/health
   ```

2. **Check network connectivity**
   ```bash
   ping 10.100.27.156
   ```

3. **Verify server URL in app.py**
   ```python
   server_url: str = "http://10.100.27.156:5000"  # Check this
   ```

---

### **Issue: Camera Not Detected**

**Error in UI:**
```
No cameras detected
```

**Solutions:**
1. **Check camera connection**
   ```bash
   lsusb | grep "Imaging"
   ```

2. **Verify camera permissions**
   ```bash
   sudo usermod -a -G video $USER
   # Logout and login again
   ```

3. **Check TIS camera drivers**
   ```bash
   python3 -c "import TIS; print('TIS module OK')"
   ```

---

### **Issue: Dependencies Missing**

**Error:**
```
ModuleNotFoundError: No module named 'flask'
```

**Solution:**
```bash
# Install dependencies
cd /home/jason_nguyen/visual-aoi-client
pip install -r requirements.txt
```

---

## API Endpoints Reference

### **Health Check**
```http
GET /api/health
```
Returns application and server health status.

### **Server Connection**
```http
POST /api/server/connect
Content-Type: application/json

{
  "server_url": "http://10.100.27.156:5000"
}
```

### **List Cameras**
```http
GET /api/cameras
```

### **Initialize Camera**
```http
POST /api/camera/initialize
Content-Type: application/json

{
  "serial": "30320436"
}
```

### **Create Session**
```http
POST /api/session
Content-Type: application/json

{
  "product": "20003548"
}
```

### **Run Inspection**
```http
POST /api/inspect
Content-Type: application/json

{
  "product": "20003548",
  "device_barcodes": [
    {"device_id": 1, "barcode": "ABC123"}
  ]
}
```

**Full API documentation:** See code comments in `app.py`

---

## Development

### **Debug Mode**

The app runs in debug mode by default:
```python
app.run(debug=True, threaded=True, port=5100)
```

**Debug features:**
- Auto-reload on code changes
- Detailed error pages
- Debug PIN for interactive debugging

**Production deployment:**
```python
# Disable debug mode for production
app.run(debug=False, threaded=True, port=5100, host='0.0.0.0')
```

---

### **Logging**

The app uses Python's logging module:

```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

**Log output:**
- INFO: Normal operations
- WARNING: Non-fatal issues
- ERROR: Fatal errors
- DEBUG: Detailed debugging (when enabled)

---

## Client Application Comparison

| Feature | Web Client (app.py) | Desktop Client (client_app.py) |
|---------|-------------------|-------------------------------|
| **Interface** | Web browser | Tkinter GUI |
| **Access** | Any device on network | Local machine only |
| **Installation** | Server only | Full installation required |
| **Updates** | Server-side only | Client-side updates needed |
| **Performance** | Network dependent | Direct hardware access |
| **Use Case** | Remote access, multiple users | Local operation, production floor |

**Recommendation:**
- **Use Web Client for:** Remote access, demonstrations, multi-user scenarios
- **Use Desktop Client for:** Production floor, direct camera control, offline operation

---

## Production Deployment

### **Using Gunicorn (Recommended)**

```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5100 app:app

# With logging
gunicorn -w 4 -b 0.0.0.0:5100 --access-logfile - --error-logfile - app:app
```

### **Using systemd (Auto-start on boot)**

Create `/etc/systemd/system/visual-aoi-web.service`:

```ini
[Unit]
Description=Visual AOI Web Client
After=network.target

[Service]
Type=simple
User=jason_nguyen
WorkingDirectory=/home/jason_nguyen/visual-aoi-client
ExecStart=/usr/bin/python3 /home/jason_nguyen/visual-aoi-client/app.py
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable visual-aoi-web
sudo systemctl start visual-aoi-web
sudo systemctl status visual-aoi-web
```

---

## Performance Optimization

### **Threading**

The app uses threading for concurrent requests:
```python
app.run(debug=True, threaded=True, port=5100)
```

### **Image Compression**

Images are JPEG encoded with 95% quality:
```python
cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 95])
```

### **Caching**

ROI groups and products are cached in memory:
```python
state.roi_groups_cache = {}
state.products_cache = []
```

---

## Security Considerations

⚠️ **Important for production:**

1. **Authentication:** Add user authentication
2. **HTTPS:** Use SSL/TLS certificates
3. **CORS:** Configure allowed origins
4. **Input Validation:** Validate all user inputs
5. **API Rate Limiting:** Prevent abuse

---

## Support

### **Log Files**
- Application logs: Console output
- Server logs: Check AOI server

### **Common Commands**
```bash
# Check if running
lsof -i :5100

# View logs
tail -f /var/log/visual-aoi-web.log  # If using systemd

# Restart service
sudo systemctl restart visual-aoi-web  # If using systemd
```

### **Getting Help**
1. Check logs for error messages
2. Verify server connectivity
3. Check camera connections
4. Review API endpoint responses

---

## Summary

✅ **Web client starts with:** `python3 app.py` or `./start_web_client.sh`  
✅ **Access at:** http://localhost:5100  
✅ **Default server:** http://10.100.27.156:5000  
✅ **Desktop client:** `python3 client/client_app.py` or `./start_client.sh`

---

**Documentation Complete:** October 3, 2025  
**Status:** ✅ PRODUCTION READY
