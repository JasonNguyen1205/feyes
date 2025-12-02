# Today's Troubleshooting Summary

**Date:** October 13, 2025  
**System:** Visual AOI Client (Raspberry Pi)

---

## Issues Fixed Today

### ✅ Issue 1: Server Connection Failed (403 Forbidden)

**Symptom:**
```
ERROR: Failed to connect to server: 403 Client Error: Forbidden
```

**Root Cause:**  
Corporate proxy at `10.100.10.1:8080` was blocking non-standard destination port (5000).

**Solution:**
```bash
# Set no_proxy to bypass proxy for local network
export no_proxy="localhost,127.0.0.1,10.100.27.156"
export NO_PROXY="localhost,127.0.0.1,10.100.27.156"

# Made permanent in ~/.bashrc
echo 'export no_proxy="localhost,127.0.0.1,10.100.27.156"' >> ~/.bashrc
echo 'export NO_PROXY="localhost,127.0.0.1,10.100.27.156"' >> ~/.bashrc
```

**Status:** ✅ RESOLVED

---

### ✅ Issue 2: Permission Denied on Shared Folder

**Symptom:**
```
PermissionError: [Errno 13] Permission denied: '/mnt/visual-aoi-shared/sessions'
```

**Root Cause:**  
The `/mnt/visual-aoi-shared` directory was owned by `root:root` with read-only permissions for user `pi`.

**Solution:**
```bash
# Create sessions directory and fix ownership
sudo mkdir -p /mnt/visual-aoi-shared/sessions
sudo chown -R pi:pi /mnt/visual-aoi-shared

# Verify write access
touch /mnt/visual-aoi-shared/sessions/test_write.txt && rm /mnt/visual-aoi-shared/sessions/test_write.txt
```

**Created Script:**  
`setup_shared_folder.sh` - Automatically sets up permissions on boot

**Status:** ✅ RESOLVED

---

### ⚠️ Issue 3: Shared Folder Not Actually Shared

**Symptom:**
- Client saves images to `/mnt/visual-aoi-shared/sessions/.../captures/group_310_800.jpg`
- Server cannot see these images
- Client and server have separate local directories with same path

**Root Cause:**  
`/mnt/visual-aoi-shared` is a **local directory** on both machines, NOT a network-shared folder. They are completely separate folders that happen to have the same path.

**Current Status:**
```
Client (Pi): /mnt/visual-aoi-shared/  [Local, NOT shared]
Server:      /mnt/visual-aoi-shared/  [Local, NOT shared]
             ↑ These are TWO DIFFERENT folders!
```

**Solution Required:**  
Set up NFS (Network File System) to actually share the folder over the network.

**Status:** ⚠️ **PENDING - Requires server configuration**

---

## Tools Created

### 1. Diagnostic Scripts
- **`check_shared_folder.sh`** - Check mount status and diagnose issues
- **`mount_shared_folder.sh`** - Automated NFS mount script
- **`setup_shared_folder.sh`** - Set local folder permissions

### 2. Documentation
- **`SHARED_FOLDER_SETUP.md`** - Complete NFS setup guide (15+ sections)
- **`SHARED_FOLDER_ISSUE.md`** - Problem summary and solution
- **`QUICK_FIX.txt`** - Copy-paste commands for quick fix

### 3. Configuration
- **`~/.bashrc`** - Updated with no_proxy settings (permanent)

---

## How to Complete the Fix

### Quick Steps:

1. **On Server (10.100.27.156)**  
   SSH and run these commands:
   ```bash
   sudo apt-get update && sudo apt-get install -y nfs-kernel-server
   sudo mkdir -p /mnt/visual-aoi-shared/sessions
   sudo chown -R jason_nguyen:jason_nguyen /mnt/visual-aoi-shared
   echo "/mnt/visual-aoi-shared 10.100.27.0/24(rw,sync,no_subtree_check,no_root_squash)" | sudo tee -a /etc/exports
   sudo exportfs -ra
   sudo systemctl restart nfs-kernel-server
   ```

2. **On Client (Raspberry Pi)**  
   ```bash
   cd /home/pi/visual-aoi-client
   ./mount_shared_folder.sh
   ```

3. **Verify**  
   ```bash
   ./check_shared_folder.sh
   ```

### Expected Result:
```
✓ SHARED FOLDER IS PROPERLY MOUNTED
```

---

## Current System Status

### Working ✅
- [x] Camera initialization and capture
- [x] Session creation
- [x] Image capture to shared folder (local)
- [x] Inspection API requests to server
- [x] Server connectivity (proxy bypassed)
- [x] File write permissions
- [x] NFS client tools installed

### Needs Configuration ⚠️
- [ ] **NFS server setup on 10.100.27.156** ← **REQUIRED**
- [ ] **Client mount to server** ← **After server setup**

### Will Work After NFS Setup ✅
- [ ] Server can see client's captured images
- [ ] Client can display server's golden images
- [ ] Full bidirectional file sharing
- [ ] Image display in inspection results
- [ ] Complete inspection workflow

---

## Testing Checklist

After NFS setup is complete:

### Basic Tests
- [ ] `./check_shared_folder.sh` shows "mounted via NFS"
- [ ] Create file on client, verify visible on server
- [ ] Create file on server, verify visible on client
- [ ] Check `df -h /mnt/visual-aoi-shared` shows network mount

### Application Tests
- [ ] Start client: `python3 ./app.py`
- [ ] Connect to server (no proxy error)
- [ ] Initialize camera
- [ ] Create session
- [ ] Run inspection
- [ ] Check captured images exist on server
- [ ] Verify golden images display in browser

---

## Files Modified/Created Today

### Configuration Files
- `~/.bashrc` - Added no_proxy settings

### Scripts (Executable)
- `check_shared_folder.sh` - Diagnostic tool
- `mount_shared_folder.sh` - Auto-mount script
- `setup_shared_folder.sh` - Permission setup

### Documentation
- `SHARED_FOLDER_SETUP.md` - Complete setup guide
- `SHARED_FOLDER_ISSUE.md` - Issue summary
- `QUICK_FIX.txt` - Quick reference
- `TODAYS_FIXES.md` - This file

### Permissions Fixed
- `/mnt/visual-aoi-shared/` - Now owned by `pi:pi`
- `/mnt/visual-aoi-shared/sessions/` - Created with write access

---

## Network Configuration

### Proxy Settings (Permanent)
```bash
export no_proxy="localhost,127.0.0.1,10.100.27.156"
export NO_PROXY="localhost,127.0.0.1,10.100.27.156"
```

### Server Details
- **IP:** 10.100.27.156
- **Port:** 5000 (API)
- **Port:** 2049 (NFS - needs to be configured)
- **User:** jason_nguyen
- **Password:** jason_nguyen

### Client Details
- **IP:** 10.100.27.XXX (in 10.100.27.0/24 subnet)
- **User:** pi
- **Home:** /home/pi/visual-aoi-client

---

## Troubleshooting Quick Reference

### If server connection fails (403):
```bash
# Check proxy settings
env | grep -i proxy
# Should show no_proxy includes 10.100.27.156
```

### If permission denied:
```bash
# Check ownership
ls -ld /mnt/visual-aoi-shared
# Should show: pi pi (not root root)

# Fix if needed
sudo chown -R pi:pi /mnt/visual-aoi-shared
```

### If folder not shared:
```bash
# Check mount status
./check_shared_folder.sh

# If not mounted, configure server NFS first, then:
./mount_shared_folder.sh
```

---

## Next Steps

**Priority 1 (CRITICAL):**  
Configure NFS server on 10.100.27.156 to enable shared folder functionality

**Priority 2:**  
Test full inspection workflow after NFS is working

**Priority 3:**  
Set up monitoring/logging for shared folder access

---

## Support Resources

- **Full Setup Guide:** `SHARED_FOLDER_SETUP.md`
- **Quick Commands:** `QUICK_FIX.txt`
- **Diagnostics:** `./check_shared_folder.sh`
- **Architecture Docs:** `.github/copilot-instructions.md`
- **Server API Docs:** http://10.100.27.156:5000/apidocs/

---

**Last Updated:** October 13, 2025, 10:05 AM  
**Technician:** AI Assistant  
**Status:** Partial fix complete, awaiting server NFS configuration
