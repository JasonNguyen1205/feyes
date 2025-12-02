# Visual AOI Client 🔍

**Professional Web-Based Visual Inspection Client for Raspberry Pi**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Modern web client for Visual AOI (Automated Optical Inspection) system. Captures high-resolution images from TIS industrial cameras and communicates with a separate server for AI-powered inspection.

---

## 🌟 Key Features

### Performance Optimized for Raspberry Pi
- ✅ **80% faster page load** - Modal-based lazy image loading
- ✅ **99% bandwidth reduction** - Images load on-demand only
- ✅ **Zero animations** - Stable UI on weak devices
- ✅ **Chromium optimized** - 16 categories of browser optimizations

### Modern Professional UI
- 🎨 **iOS-inspired theme** - Light/Dark mode with "Liquid Glass" effects
- 📱 **Responsive design** - Works on desktop, tablet, and mobile
- 🖼️ **Modal detail view** - Clean, focused interface
- ⚡ **Instant interactions** - No lag or jank on Raspberry Pi

### Multi-Device Inspection
- 📊 **Device grouping** - Results organized by device (1-4)
- 🏷️ **Barcode tracking** - Per-device barcode identification
- 🔍 **ROI filtering** - Show only failed ROIs with one click
- ✓ **Pass/Fail indicators** - Clear visual feedback

### Camera Integration
- 📷 **TIS Camera support** - Industrial-grade image capture (7716x5360)
- 🎯 **Manual mode** - All auto modes disabled for stability
- ⚡ **Fast capture** - Optimized for 1.6s capture time
- 🔄 **Multi-group capture** - Support for focus/exposure groups

---

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [System Requirements](#-system-requirements)
- [Installation](#-installation)
- [Usage](#-usage)
- [Performance](#-performance)
- [Architecture](#-architecture)
- [Configuration](#-configuration)
- [Documentation](#-documentation)
- [Troubleshooting](#-troubleshooting)

---

## 🚀 Quick Start

### Start the Web Server

```bash
# Method 1: Direct Python
python3 app.py

# Method 2: Startup script
./start_web_client.sh

# Access in browser
http://127.0.0.1:5100
```

### Basic Workflow

1. **Connect to Server** → Enter server URL (default: `http://10.100.27.156:5000`)
2. **Initialize Camera** → Select camera and product
3. **Create Session** → Start inspection session
4. **Run Inspection** → Capture and analyze images
5. **View Results** → Click "View Detailed Results" for each device

---

## 💻 System Requirements

### Hardware
- **Raspberry Pi 4** (2GB+ RAM) or better
- **TIS Camera** (The Imaging Source)
  - Supported: DFK AFU420-L62, NTx-Mini PT01-PBXMX1-32XG25
- **Network connection** to Visual AOI Server

### Software
- **OS**: Raspberry Pi OS (Debian 12 Bookworm) or Ubuntu 20.04+
- **Python**: 3.8 or higher
- **Browser**: Chromium (recommended), Chrome, Firefox, Safari

---

## 📦 Installation

### 1. System Dependencies

```bash
# Install GTK and GStreamer (required for TIS cameras)
sudo apt-get update
sudo apt-get install -y \
    python3-gi \
    python3-gi-cairo \
    gir1.2-gtk-3.0 \
    gir1.2-gstreamer-1.0 \
    gstreamer1.0-tools \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-libav
```

### 2. Python Dependencies

```bash
# Create virtual environment (optional but recommended)
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS

# Install Python packages
pip install -r requirements.txt
```

### 3. Shared Folder Setup

```bash
# Mount shared folder for image storage
./setup_shared_folder.sh

# Verify mount
ls -la /mnt/visual-aoi-shared/
```

---

## 🎯 Usage

### 1. Server Connection

**Connect to Visual AOI Server:**
- Enter server URL in the interface
- Click "🔗 Connect to Server"
- Wait for green "✓ Connected" status

**Default Server**: `http://10.100.27.156:5000`

### 2. Camera Initialization

**Steps:**
1. Click "🔄 Refresh Cameras" to detect available cameras
2. Select camera from dropdown (serial number shown)
3. Select product from dropdown
4. Click "📷 Initialize Camera"
5. Wait for initialization (takes ~3-5 seconds)

**Camera Settings:**
- **Focus**: Manual mode (product-specific)
- **Exposure**: Manual mode (product-specific)
- **Format**: BGRA (required for TIS cameras)
- **Resolution**: 7716x5360 (full sensor)

### 3. Session Management

**Create Session:**
1. Camera must be initialized first
2. Product is auto-selected from camera init
3. Click "🆕 Create Session"
4. Session ID displayed (e.g., `d53fae17-...`)

**Session Data:**
- Stored in `/mnt/visual-aoi-shared/sessions/{session_id}/`
- Captures: `captures/` folder
- Output images: `output/` folder

### 4. Running Inspection

**Auto-Capture Mode:**
- Enter barcodes for each device
- System auto-captures and inspects when all barcodes entered

**Manual Mode:**
- Click "🔍 Inspect" button
- Image captured and sent to server
- Results displayed in ~5-7 seconds

**Barcode Input:**
- One barcode per device (up to 4 devices)
- Auto-populated for barcode-type ROIs
- Manual input for devices without barcode ROIs

### 5. Viewing Results

**Device Summary Cards:**
```
Device 1: ✓ PASS
  Barcode: ['20004960-0000978-1020822-101']
  ROIs: 23/23 passed
  Success Rate: 100.0%
  [🔍 View Detailed Results]
```

**Click "View Detailed Results"** to open modal with:
- All ROI inspection details
- Golden sample vs. captured images (lazy loaded)
- AI similarity scores
- Pass/fail status for each ROI
- Filter button to show only failures

**Result Details:**
- ✓ **PASS** - Green indicator, ROI matches criteria
- ✗ **FAIL** - Red indicator, ROI failed inspection
- **AI Similarity** - Percentage match (0-100%)
- **Barcode/OCR Text** - Extracted text values
- **Position** - ROI coordinates [x1, y1, x2, y2]

### 6. Image Viewing

**Modal Image View:**
- Click any ROI image thumbnail
- Opens full-screen modal
- High-resolution zoom
- Click outside or press ESC to close

**Image Types:**
- 🌟 **Golden Sample** - Reference image from server
- 📸 **Captured Image** - Current inspection image
- Both displayed side-by-side for comparison

---

## ⚡ Performance

### Optimization Summary

| Feature | Before | After | Improvement |
|---------|--------|-------|-------------|
| **Initial Page Load** | 5-10s | 1-2s | 80% faster |
| **Initial Bandwidth** | 5-20 MB | 50 KB | 99% reduction |
| **Images on Load** | 30+ | 0 | 100% deferred |
| **Hover Animations** | 21 | 0 | All removed |
| **Scroll Animations** | Yes | No | Instant scroll |
| **Lazy Loading** | IntersectionObserver | Modal-based | On-demand only |

### Performance Features

1. **Modal-Based Lazy Loading**
   - Images load only when modal opens
   - 100ms delay for smooth rendering
   - Placeholder: "⏳ Loading image..."

2. **No Animations**
   - All hover effects removed
   - No scroll animations
   - No CSS transitions
   - Stable UI on weak devices

3. **Chromium Optimizations**
   - Hardware acceleration
   - GPU compositing
   - Efficient paint operations
   - Optimized scrollbar rendering

4. **Compact UI**
   - 2x2 grid layout
   - Collapsible settings panel
   - Auto-collapsed sections
   - Focus on inspection workflow

---

## 🏗️ Architecture

### Client-Server Design

```
┌─────────────────────────────────────────────────────────┐
│                    Browser (Chromium)                    │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │        Web UI (professional_index.html)        │    │
│  │  - Device cards with modal detail view         │    │
│  │  - Lazy image loading (on-demand)              │    │
│  │  - Filter failures button                      │    │
│  └────────────────────────────────────────────────┘    │
│                        ▲                                 │
│                        │ HTTP/REST                       │
│                        ▼                                 │
│  ┌────────────────────────────────────────────────┐    │
│  │          Flask Server (app.py:5100)            │    │
│  │  - Serves static files and templates           │    │
│  │  - Proxies camera and server requests          │    │
│  │  - Serves shared folder images (/shared/)      │    │
│  └────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
                           ▲
                           │ REST API
                           ▼
         ┌─────────────────────────────────────┐
         │  Visual AOI Server (port 5000)      │
         │  - AI inspection logic              │
         │  - ROI processing                   │
         │  - Golden sample management         │
         │  - Result generation                │
         └─────────────────────────────────────┘
                           ▲
                           │
                           ▼
         ┌─────────────────────────────────────┐
         │  Shared Folder (/mnt/visual-aoi/)   │
         │  - Session data                     │
         │  - Captured images                  │
         │  - Output images (golden + ROI)     │
         └─────────────────────────────────────┘
                           ▲
                           │ Camera API
                           ▼
         ┌─────────────────────────────────────┐
         │    TIS Camera (Hardware)            │
         │  - 7716x5360 resolution             │
         │  - Manual focus/exposure            │
         │  - BGRA format                      │
         └─────────────────────────────────────┘
```

### Key Design Principles

1. **Client handles camera** - Server never accesses camera (avoids EBUSY)
2. **Server handles AI** - All inspection logic on server
3. **Shared folder** - Common storage for images
4. **REST API** - Clean separation of concerns
5. **Base64 encoding** - Images sent in JSON payloads

### File Structure

```
visual-aoi-client/
├── app.py                          # Flask web server (main entry)
├── start_web_client.sh             # Startup script
├── requirements.txt                # Python dependencies
│
├── src/                            # Core modules
│   ├── camera.py                   # TIS camera integration
│   ├── config.py                   # Configuration management
│   ├── roi.py                      # ROI handling
│   └── ui.py                       # Theme system
│
├── templates/                      # HTML templates
│   └── professional_index.html     # Main UI (3486 lines)
│
├── static/                         # Static assets
│   ├── professional.css            # Base styles (1547 lines)
│   ├── chromium-optimizations.css  # Browser optimizations (502 lines)
│   ├── compact-ui.css              # Compact layout styles
│   └── favicon.svg                 # App icon
│
├── config/                         # Configuration files
│   ├── theme_settings.json         # UI theme settings
│   └── system/
│       └── camera.json             # Camera hardware config
│
├── docs/                           # Documentation
│   ├── MODAL_DETAIL_VIEW_WITH_LAZY_LOADING.md
│   ├── HOVER_ANIMATIONS_REMOVAL.md
│   ├── MODAL_CENTERING_FIX.md
│   └── ... (50+ documentation files)
│
└── tests/                          # Test suite
    ├── test_camera.py
    ├── test_config.py
    └── ...
```

---

## ⚙️ Configuration

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

**Camera Settings:**
- **Serial**: Camera serial number (auto-detected)
- **Resolution**: Full sensor resolution (don't change)
- **FPS**: Frame rate (7/1 = 7fps)
- **Format**: Must be BGRA for TIS cameras
- **Focus**: Default focus value (manual mode)
- **Exposure**: Default exposure in microseconds

### Theme Configuration

Edit `config/theme_settings.json`:

```json
{
  "theme": "light",
  "font_family": "Titillium Web, -apple-system, sans-serif",
  "glass_effects": true,
  "compact_mode": true
}
```

**Theme Options:**
- **theme**: "light" or "dark"
- **font_family**: Main UI font
- **glass_effects**: Enable glass morphism
- **compact_mode**: Compact layout with settings panel

### Server Configuration

Configure in web UI or environment variable:

```bash
export AOI_SERVER_URL=http://10.100.27.156:5000
```

**Server API Endpoints:**
- `/api/health` - Server status check
- `/api/products` - List available products
- `/api/session` - Session management
- `/api/inspect` - Run inspection
- `/api/roi/groups/{product_id}` - Get ROI groups

---

## 📚 Documentation

### Main Documentation Files

- **[MODAL_DETAIL_VIEW_WITH_LAZY_LOADING.md](docs/MODAL_DETAIL_VIEW_WITH_LAZY_LOADING.md)** - Modal lazy loading implementation
- **[HOVER_ANIMATIONS_REMOVAL.md](docs/HOVER_ANIMATIONS_REMOVAL.md)** - Performance optimization details
- **[MODAL_CENTERING_FIX.md](docs/MODAL_CENTERING_FIX.md)** - Modal centering solution
- **[CLIENT_SERVER_ARCHITECTURE.md](docs/CLIENT_SERVER_ARCHITECTURE.md)** - Architecture overview
- **[CAMERA_INITIALIZATION_PROFESSIONAL.md](docs/CAMERA_INITIALIZATION_PROFESSIONAL.md)** - Camera setup guide
- **[IMAGE_FRESHNESS_COMPLETE.md](docs/IMAGE_FRESHNESS_COMPLETE.md)** - Image caching strategy

### Quick References

- **[SCHEMA_V2_QUICK_REFERENCE.md](docs/SCHEMA_V2_QUICK_REFERENCE.md)** - API schema documentation
- **[IMAGE_SAVE_QUICK_REFERENCE.md](docs/IMAGE_SAVE_QUICK_REFERENCE.md)** - Image path conventions
- **[CHROMIUM_QUICK_REFERENCE.txt](CHROMIUM_QUICK_REFERENCE.txt)** - Browser optimization checklist

### All Documentation

See `docs/` folder for 50+ detailed documentation files covering:
- Camera operations and troubleshooting
- UI patterns and theming
- Server integration
- Performance optimizations
- Multi-device handling
- ROI management
- Barcode tracking
- Testing procedures

---

## 🔧 Troubleshooting

### Camera Issues

**Camera Not Detected**
```bash
# Check USB connection
ls /dev/video*

# Check TIS camera detection
v4l2-ctl --list-devices

# Restart camera
sudo systemctl restart v4l2

# Check permissions
sudo chmod 666 /dev/video*
```

**EBUSY Error**
```
Problem: Camera in use by another process
Solution: Ensure server doesn't access camera
Action: Restart camera hardware
```

**Pipeline Error**
```
Problem: GStreamer pipeline failed
Solution: Check GStreamer installation
Action: Reinstall gstreamer1.0-* packages
```

### Server Connection Issues

**Connection Refused**
```bash
# Check server status
curl http://10.100.27.156:5000/api/health

# Check firewall
sudo ufw status
sudo ufw allow 5000/tcp

# Check server logs
# (on server machine)
```

**Timeout Errors**
```
Problem: Inspection taking too long
Solution: Check server performance
Action: Verify AI models loaded
```

### Image Issues

**Images Not Loading**
```bash
# Check shared folder mount
df -h | grep visual-aoi-shared

# Verify permissions
ls -la /mnt/visual-aoi-shared/sessions/

# Check Flask route
curl http://127.0.0.1:5100/shared/test.jpg
```

**Stale Images**
```
Problem: Old images showing after new inspection
Solution: Cache busting implemented with ?t=timestamp
Action: Hard refresh browser (Ctrl+Shift+R)
```

### UI Issues

**Modal Not Centered**
```
Problem: Modal appears at top of page
Solution: Already fixed with transform centering
Action: Clear browser cache and reload
```

**Slow Performance**
```
Problem: UI lagging on Raspberry Pi
Solution: All animations removed
Action: Use Chromium browser (not Firefox)
Check: Ensure no other heavy processes running
```

**Images Not Lazy Loading**
```
Problem: All images load at once
Solution: Check modal implementation
Action: Images should load only when modal opens
Verify: Network tab shows no image requests until button click
```

### Development Issues

**Import Errors**
```bash
# TIS module not found
export PYTHONPATH=$PYTHONPATH:/path/to/python-common

# GTK warnings
sudo apt-get install python3-gi

# Flask not found
pip install -r requirements.txt
```

---

## 🧪 Testing

### Run Tests

```bash
# All tests
pytest tests/

# Specific test file
pytest tests/test_camera.py -v

# With coverage
pytest tests/ --cov=src --cov-report=html

# Only unit tests
pytest tests/ -m "unit"
```

### Manual Testing

```bash
# Test camera detection
python3 -c "import TIS; print(TIS.get_devices())"

# Test server connection
curl http://10.100.27.156:5000/api/health

# Test shared folder
ls -la /mnt/visual-aoi-shared/sessions/
```

---

## 📝 Development

### Adding Features

1. **UI Components** - Edit `templates/professional_index.html`
2. **Styles** - Edit `static/professional.css`
3. **Camera Logic** - Edit `src/camera.py`
4. **Server API** - Edit `app.py` routes
5. **Configuration** - Edit `config/` files

### Code Style

- **Python**: PEP 8 compliant
- **JavaScript**: ES6+ with clear comments
- **CSS**: BEM-like naming, organized by section
- **HTML**: Semantic markup, accessibility considered

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/new-feature

# Commit changes
git add .
git commit -m "feat: add new feature"

# Push to remote
git push origin feature/new-feature

# Create pull request
```

---

## 🚢 Deployment

### Production Deployment

```bash
# On Raspberry Pi
cd /opt/visual-aoi-client

# Update code
git pull origin master

# Restart service
sudo systemctl restart visual-aoi-client

# Check logs
sudo journalctl -u visual-aoi-client -f
```

### Systemd Service

Create `/etc/systemd/system/visual-aoi-client.service`:

```ini
[Unit]
Description=Visual AOI Client Web Server
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/opt/visual-aoi-client
Environment="PATH=/opt/visual-aoi-client/.venv/bin"
ExecStart=/opt/visual-aoi-client/.venv/bin/python3 app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable visual-aoi-client
sudo systemctl start visual-aoi-client
```

---

## 📊 Performance Metrics

### Page Load Performance

| Metric | Value |
|--------|-------|
| Initial Load Time | 1-2 seconds |
| Time to Interactive | 2 seconds |
| Initial Bandwidth | 50 KB |
| JavaScript Bundle | 150 KB |
| CSS Bundle | 180 KB |
| First Contentful Paint | 0.8s |

### Inspection Performance

| Operation | Time |
|-----------|------|
| Camera Capture | 1.6s |
| Image Encoding | 0.5s |
| Server Processing | 3-5s |
| Result Display | 0.2s |
| **Total** | **5-7s** |

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details

---

## 👥 Authors

- **Visual AOI Team** - Industrial inspection system development

---

## 🙏 Acknowledgments

- **The Imaging Source** - TIS Camera SDK
- **Flask Community** - Web framework
- **Chromium Team** - Browser optimizations
- **Raspberry Pi Foundation** - Hardware platform

---

## 📞 Support

For issues and questions:
- **Documentation**: See `docs/` folder
- **Issues**: GitHub issue tracker
- **Email**: Support contact

---

**Version**: 2.0.0 (October 2025)  
**Python**: 3.8+  
**Platform**: Raspberry Pi 4 / Linux  
**Browser**: Chromium (optimized)

---

⭐ **Star this repository if you find it helpful!**
