# Shared Folder Issue - Summary

## Problem

✗ **Client and server cannot see each other's files**

- Client saves images to **local** `/mnt/visual-aoi-shared/sessions/.../captures/`
- Server cannot see these images because it's looking in its **own local** `/mnt/visual-aoi-shared/`
- They are two separate directories on two different machines

## Root Cause

The `/mnt/visual-aoi-shared` folder is **NOT shared via network (NFS)**. Both machines have their own local directories with the same path, but they are completely separate.

```
Current (BROKEN):
┌─────────────────────┐     ┌─────────────────────┐
│ Server              │     │ Client (Pi)         │
│ 10.100.27.156       │     │ 10.100.27.XXX       │
│                     │     │                     │
│ /mnt/visual-aoi-    │ ✗   │ /mnt/visual-aoi-    │
│     shared/         │     │     shared/         │
│   (separate local)  │     │   (separate local)  │
└─────────────────────┘     └─────────────────────┘
```

## Solution

Set up **NFS (Network File System)** so both machines access the same folder:

```
Fixed (with NFS):
┌─────────────────────┐     ┌─────────────────────┐
│ Server              │     │ Client (Pi)         │
│ 10.100.27.156       │────▶│ 10.100.27.XXX       │
│                     │ NFS │                     │
│ /mnt/visual-aoi-    │◀────│ /mnt/visual-aoi-    │
│     shared/         │     │     shared/ (mount) │
│   (NFS Server)      │     │   (NFS Client)      │
└─────────────────────┘     └─────────────────────┘
     Same folder accessed by both machines!
```

## Quick Start

### On Server (10.100.27.156)

Login credentials: `jason_nguyen` / `jason_nguyen`

```bash
# 1. Install NFS server
sudo apt-get update && sudo apt-get install -y nfs-kernel-server

# 2. Create and configure shared folder
sudo mkdir -p /mnt/visual-aoi-shared/sessions
sudo chown -R jason_nguyen:jason_nguyen /mnt/visual-aoi-shared

# 3. Export the folder (allow client subnet to access)
echo "/mnt/visual-aoi-shared 10.100.27.0/24(rw,sync,no_subtree_check,no_root_squash)" | sudo tee -a /etc/exports

# 4. Apply and restart NFS
sudo exportfs -ra
sudo systemctl restart nfs-kernel-server

# 5. Verify
sudo exportfs -v
# Should show: /mnt/visual-aoi-shared ... 10.100.27.0/24(...)
```

### On Client (Raspberry Pi)

```bash
cd /home/pi/visual-aoi-client

# Run automated mount script
./mount_shared_folder.sh

# Or check current status first
./check_shared_folder.sh
```

## Verification Steps

### 1. Test from Client → Server

On **Client**:
```bash
echo "Hello from client" > /mnt/visual-aoi-shared/test.txt
```

On **Server**:
```bash
cat /mnt/visual-aoi-shared/test.txt
# Should show: "Hello from client"
```

### 2. Test from Server → Client

On **Server**:
```bash
echo "Hello from server" > /mnt/visual-aoi-shared/test2.txt
```

On **Client**:
```bash
cat /mnt/visual-aoi-shared/test2.txt
# Should show: "Hello from server"
```

### 3. Test Full Inspection Flow

1. Start client application: `python3 ./app.py`
2. Open browser: `http://localhost:5100`
3. Connect to server
4. Run inspection
5. Check on **server** that captured images are visible:
   ```bash
   ls -lR /mnt/visual-aoi-shared/sessions/
   ```

## Diagnostic Tools

### Check Status
```bash
./check_shared_folder.sh
```

### Expected Output When Working:
```
✓ Folder is mounted via NFS
✓ Write access OK
✓ Server 10.100.27.156 is reachable
✓ NFS port 2049 is open on server
✓ SHARED FOLDER IS PROPERLY MOUNTED
```

### Expected Output When Broken:
```
⚠ Folder is NOT mounted (using local directory)
✗ SHARED FOLDER IS NOT MOUNTED
```

## Files Created

1. **`SHARED_FOLDER_SETUP.md`** - Complete setup guide with troubleshooting
2. **`mount_shared_folder.sh`** - Automated mount script for client
3. **`check_shared_folder.sh`** - Diagnostic tool
4. **`setup_shared_folder.sh`** - Local folder permission setup (already done)

## Current Status

- ✅ Client-side folder created with correct permissions
- ✅ NFS client tools installed
- ✅ Server is reachable
- ✅ Mount scripts ready
- ❌ **Server NFS not configured yet** ← **ACTION REQUIRED**
- ❌ **Client not mounted to server** ← **Will work after server setup**

## Next Steps

1. **SSH to server** and configure NFS (see commands above)
2. **Run mount script** on client: `./mount_shared_folder.sh`
3. **Test** bidirectional file access
4. **Run inspection** and verify images are visible on both sides

## Support

- Full documentation: `SHARED_FOLDER_SETUP.md`
- Run diagnostics: `./check_shared_folder.sh`
- Auto-mount: `./mount_shared_folder.sh`

---

**Date:** October 13, 2025  
**Issue:** Shared folder not shared over network  
**Status:** Awaiting server NFS configuration  
**Priority:** HIGH (blocks inspection image display)
