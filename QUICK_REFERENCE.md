# Visual AOI System - Quick Reference

## 🚀 Launch Commands

### Windows

#### Simplest Way (Double-click or Command)

```cmd
start.bat          → Launches EVERYTHING (server + client)
server.bat         → Launches SERVER only
client.bat         → Launches CLIENT only
```

#### PowerShell (More Control)

```powershell
.\launch_all.ps1           → Full system (separate windows)
.\launch_all.ps1 -Debug    → Full system with debug mode
.\launch_server.ps1        → Server only
.\launch_client.ps1        → Client only
```

### Linux

#### Simplest Way

```bash
./start.sh                 → Launches EVERYTHING (server + client)
```

#### Bash (More Control)

```bash
./launch_all.sh            → Full system (separate terminals)
./launch_all.sh --debug    → Full system with debug mode
./launch_server.sh         → Server only
./launch_client.sh         → Client only
```

## 🌐 Default URLs

| Component | URL | Description |
|-----------|-----|-------------|
| **Client UI** | <http://localhost:5100> | Main web interface |
| **Server API** | <http://localhost:5000> | REST API endpoint |
| **Swagger UI** | <http://localhost:5000/apidocs/> | API documentation |
| **Health Check** | <http://localhost:5000/health> | Server status |

## 📁 Project Layout

```text
w:\
├── launch_all.ps1      ← Launch everything
├── launch_server.ps1   ← Launch server
├── launch_client.ps1   ← Launch client
├── start.bat           ← Simple launcher (all)
├── server.bat          ← Simple launcher (server)
├── client.bat          ← Simple launcher (client)
├── client/
│   ├── app.py          ← Client Flask app (entry point)
│   ├── src/
│   │   ├── camera.py   ← TIS camera control
│   │   └── ui.py       ← UI theme system
│   ├── templates/
│   │   └── professional_index.html  ← Main UI
│   └── config/
│       └── products/   ← Product ROI configs
└── server/
    ├── server/
    │   └── simple_api_server.py  ← Server Flask app (entry point)
    ├── src/
    │   ├── inspection.py         ← Core inspection logic
    │   ├── roi.py                ← ROI processing
    │   ├── ai_pytorch.py         ← PyTorch AI
    │   ├── barcode.py            ← Barcode reading
    │   └── ocr.py                ← OCR processing
    └── config/
        └── products/   ← Product ROI configs
```

## 🔄 Typical Workflow

### 1. Development
```powershell
# Start with debug mode for auto-reload
.\launch_all.ps1 -Debug

# Open in browser
# - Client: http://localhost:5100
# - Server Swagger: http://localhost:5000/apidocs/

# Make code changes → Flask auto-reloads

# Stop: Ctrl+C in each window
```

### 2. Testing
```powershell
# Server tests
cd server
pytest tests/ -m "unit"           # Unit tests
pytest tests/ -m "not slow"       # Skip slow tests
pytest tests/ --cov=src           # With coverage

# Client tests
cd client
pytest tests/ -m "not camera"     # Skip hardware tests
```

### 3. Inspection Session
```text
POST /api/session/create
  → Returns session_id

GET /api/session/{id}/status
  → Check session state

POST /api/session/{id}/inspect
  → Process image with ROIs
  → Returns device-grouped results

POST /api/session/{id}/close
  → Cleanup session
```

## 🎯 Common Tasks

### Connect Client to Remote Server
```powershell
.\launch_client.ps1 -ServerUrl http://192.168.1.100:5000
```

### Use Custom Ports
```powershell
.\launch_all.ps1 -ServerPort 5001 -ClientPort 5101
```

### Run Without Virtual Environment
```powershell
.\launch_server.ps1 -NoVenv
.\launch_client.ps1 -NoVenv
```

### Check Camera Availability
```powershell
.\launch_client.ps1 -CheckCamera
```

### Force Fresh Dependencies
```powershell
# Remove old virtual environments
Remove-Item -Recurse -Force server\.venv, client\.venv

# Reinstall everything
.\launch_all.ps1
```

## 🔧 Troubleshooting

### Port Already in Use
Launchers automatically free ports, but if issues persist:
```powershell
Get-NetTCPConnection -LocalPort 5000
Stop-Process -Id <PID> -Force
```

### Server Not Responding
```powershell
# Check health endpoint
Invoke-WebRequest http://localhost:5000/health

# Or in browser
# http://localhost:5000/health
```

### GPU Not Detected
```powershell
# Check CUDA
nvidia-smi

# Verify PyTorch GPU (in server venv)
cd server
.\.venv\Scripts\Activate.ps1
python -c "import torch; print(torch.cuda.is_available())"
```

### Camera Issues
```powershell
# Check TIS library
python -c "import TIS; print('Camera library available')"
```

### Import Errors
```powershell
# Reinstall dependencies
cd server  # or client
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 📊 ROI Structure (v3.2)

ROIs are 12-field tuples stored as JSON objects:

```json
{
  "idx": 1,
  "type": 2,
  "coords": [100, 100, 200, 200],
  "focus": 305,
  "exposure": 1200,
  "ai_threshold": 0.93,
  "feature_method": "mobilenet",
  "rotation": 0,
  "device_location": 1,
  "expected_text": "",
  "is_device_barcode": false,
  "color_config": {}
}
```

**ROI Types:**
- `1` = Barcode
- `2` = Compare (AI similarity)
- `3` = OCR (text recognition)
- `4` = Color detection

## 🎨 Key Conventions

### Camera Integration (Client Only)
```python
import TIS
camera.Set_Image_Format(TIS.SinkFormats.BGRA)  # ALWAYS use BGRA
```

### Field Naming
- Use `exposure` (NOT `exposure_time`)
- Use `coords` for [x1, y1, x2, y2]

### ROI Normalization
```python
from src.roi import normalize_roi
roi = normalize_roi(roi_data)  # Handles legacy formats
```

### File Paths
```python
# Client sends: /mnt/visual-aoi-shared/...
# Server uses: /home/.../visual-aoi-server/shared/...
# API auto-converts
```

## 📚 Documentation

| File | Purpose |
|------|---------|
| `LAUNCHER_README.md` | Complete launcher documentation |
| `.github/copilot-instructions.md` | AI agent guide |
| `server/docs/PROJECT_INSTRUCTIONS.md` | Core application logic |
| `server/docs/ROI_DEFINITION_SPECIFICATION.md` | ROI structure spec (v3.2) |
| `server/docs/INSPECTION_RESULT_SPECIFICATION.md` | Result structure (v2.0) |
| `client/docs/` | 150+ implementation docs |

## 🔐 Environment Variables

Automatically set by launchers:
- `CUDA_FORCE_PTX_JIT=1` - Enable RTX GPU support
- `SERVER_URL` - Client's server URL
- `FLASK_DEBUG=1` - When using `-Debug`

## ⚡ Performance Tips

1. **GPU**: Server auto-enables CUDA if available (RTX 5080)
2. **Parallel ROI Processing**: 2-10x speedup (ThreadPoolExecutor)
3. **File-based Exchange**: 195x faster than Base64 (via shared folder)
4. **Virtual Env**: Isolates dependencies, prevents conflicts

## 🏗️ Architecture

```text
┌────────────────────────────────────────────────────┐
│              launch_all.ps1                        │
│        (Orchestrates system startup)               │
└───────────┬──────────────────┬─────────────────────┘
            │                  │
    ┌───────▼────────┐  ┌─────▼──────────┐
    │     SERVER     │  │     CLIENT     │
    │   Port 5000    │  │   Port 5100    │
    │                │  │                │
    │ • REST API     │  │ • Web UI       │
    │ • PyTorch AI   │  │ • TIS Camera   │
    │ • EasyOCR      │  │ • Image Capture│
    │ • Barcode      │  │ • Results View │
    │ • Session Mgmt │  │                │
    └────────┬───────┘  └────────┬───────┘
             │                   │
             └─────────┬─────────┘
                       │
            ┌──────────▼──────────┐
            │   Shared Folder     │
            │   (File Exchange)   │
            │                     │
            │ • Input images      │
            │ • Output images     │
            │ • Golden samples    │
            └─────────────────────┘
```

## 🎓 Learning Path

1. **Start with basics**: `.\start.bat`
2. **Explore UI**: <http://localhost:5100>
3. **Try Swagger**: <http://localhost:5000/apidocs/>
4. **Read specs**: `server/docs/PROJECT_INSTRUCTIONS.md`
5. **Test changes**: `pytest tests/`
6. **Review patterns**: `.github/copilot-instructions.md`

## 🆘 Quick Help

```powershell
# Get launcher help
Get-Help .\launch_all.ps1 -Full
Get-Help .\launch_server.ps1 -Full
Get-Help .\launch_client.ps1 -Full

# View launcher parameters
.\launch_all.ps1 -?
```

---

**Pro Tip**: Use `.\launch_all.ps1 -Debug` during development for auto-reload! 🔄
