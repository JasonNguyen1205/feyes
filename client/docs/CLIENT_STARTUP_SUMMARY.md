# Client Startup Guide - Summary

**Date:** October 3, 2025  
**Status:** ✅ RESOLVED  
**Issue:** "the client should start with app.py"

---

## Problem

User tried to run `python3 ./app.py` but got error:
```
Address already in use
Port 5100 is in use by another program.
```

---

## Solution

✅ **Killed existing processes on port 5100**  
✅ **Started the web client successfully**  
✅ **Created startup script for easy launching**  
✅ **Updated documentation**

---

## How to Start the Client

### **Method 1: Using Startup Script** ⭐ Recommended

```bash
./start_web_client.sh
```

**Benefits:**
- Automatically checks and frees port 5100
- Verifies dependencies
- Shows clear status messages
- Handles errors gracefully

### **Method 2: Direct Python Command**

```bash
python3 app.py
```

**If port is in use:**
```bash
# Kill processes on port 5100
lsof -i :5100 | grep python | awk '{print $2}' | xargs kill -9

# Then start
python3 app.py
```

---

## Application Status

✅ **Web client is running at:** http://localhost:5100

**Current output:**
```
GStreamer initialized successfully
TIS module imported successfully
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5100
 * Debugger is active!
```

---

## Two Client Options

### **1. Web Client (app.py)** - Port 5100

**Start:**
```bash
python3 app.py
# or
./start_web_client.sh
```

**Access:**
- http://localhost:5100
- http://127.0.0.1:5100

**Features:**
- Modern web interface
- Browser-based access
- Remote access capable
- Professional UI design

---

### **2. Desktop Client (client_app.py)** - Tkinter GUI

**Start:**
```bash
python3 client/client_app.py
# or
./start_client.sh
```

**Features:**
- Traditional desktop GUI
- Direct hardware control
- Offline operation
- Production floor ready

---

## Files Created

### **1. start_web_client.sh**
- Startup script for web client
- Auto-checks port availability
- Verifies dependencies
- Shows status messages

### **2. docs/WEB_CLIENT_GETTING_STARTED.md**
- Complete getting started guide
- Architecture overview
- API endpoint reference
- Troubleshooting guide
- Production deployment instructions

### **3. Updated README.md**
- Clarified two client options
- Quick start for both clients
- Architecture diagrams
- Installation instructions

---

## Key Differences

| Feature | Web Client (app.py) | Desktop Client (client_app.py) |
|---------|-------------------|-------------------------------|
| **Interface** | Browser-based | Tkinter GUI |
| **Port** | 5100 | N/A |
| **Access** | Any device | Local only |
| **Startup** | `python3 app.py` | `python3 client/client_app.py` |
| **Use Case** | Remote, demos, multi-user | Production floor, local |

---

## Troubleshooting

### Port 5100 Already in Use

**Check:**
```bash
lsof -i :5100
```

**Fix:**
```bash
# Use startup script (auto-fixes)
./start_web_client.sh

# Or manually kill
kill -9 $(lsof -t -i:5100)
python3 app.py
```

---

### Cannot Connect to Server

**Check server:**
```bash
curl http://10.100.27.156:5000/api/health
```

**Update server URL in UI or app.py:**
```python
server_url: str = "http://10.100.27.156:5000"
```

---

### Camera Not Detected

**Check camera:**
```bash
lsusb | grep "Imaging"
```

**Check permissions:**
```bash
sudo usermod -a -G video $USER
# Logout and login
```

---

## Verification

✅ **Web client started successfully**  
✅ **Accessible at http://localhost:5100**  
✅ **Connected to server: http://10.100.27.156:5000**  
✅ **Cameras detected:**
- NTx-Mini PT01-PBXMX1-32XG25 (00:11:1c:03:e4:8d)
- DFK AFU420-L62 (30320436)

✅ **Session created:** a2fc8911-a88d-4d4b-9742-9df9cffdc809  
✅ **Product:** 20003548  
✅ **Inspection completed successfully**

---

## Next Steps

1. ✅ Web client is running
2. ✅ Documentation complete
3. ✅ Startup script created
4. 📋 Use the client for inspections
5. 📋 Deploy to production (see WEB_CLIENT_GETTING_STARTED.md)

---

## Quick Reference

```bash
# Web Client
python3 app.py                        # Start web server
./start_web_client.sh                 # Start with script
http://localhost:5100                 # Access URL

# Desktop Client
python3 client/client_app.py          # Start desktop GUI
./start_client.sh                     # Start with script

# Troubleshooting
lsof -i :5100                         # Check port
kill -9 $(lsof -t -i:5100)           # Free port
```

---

## Documentation

- **Web Client Guide:** `docs/WEB_CLIENT_GETTING_STARTED.md`
- **Main README:** `README.md`
- **API Reference:** See code comments in `app.py`
- **Troubleshooting:** See getting started guide

---

**Issue Resolved:** October 3, 2025  
**Status:** ✅ CLIENT RUNNING SUCCESSFULLY  
**Access:** http://localhost:5100
