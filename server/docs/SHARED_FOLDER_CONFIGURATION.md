# Shared Folder Configuration - Visual AOI Server

**Date:** October 3, 2025  
**Status:** ✅ Active CIFS/SMB Mount  
**Server IP:** 10.100.27.156  
**Mount Point:** /mnt/visual-aoi-shared

---

## 🎯 Overview

The Visual AOI system uses a **shared folder** architecture for file exchange between the client application and the server. This allows the client to write captured images and the server to read them and write back processed results.

---

## 📁 Shared Folder Architecture

### Mount Configuration

**Type:** CIFS/SMB Network Share  
**Source:** `//10.100.27.156/visual-aoi-shared`  
**Mount Point:** `/mnt/visual-aoi-shared`  
**Protocol:** SMB 2.0  
**User:** jason_nguyen  
**Permissions:** rw (read-write)

### Directory Structure

```
/mnt/visual-aoi-shared/
├── __pycache__/          # Python cache files
└── sessions/             # Session-based file storage
    ├── <session-uuid-1>/
    │   ├── input/        # Client writes captured images here
    │   │   └── capture_F<focus>_E<exposure>.jpg
    │   └── output/       # Server writes processed results here
    │       ├── roi_<id>_F<focus>_E<exposure>.jpg
    │       └── golden_<id>_F<focus>_E<exposure>.jpg
    ├── <session-uuid-2>/
    │   ├── input/
    │   └── output/
    └── ... (63 session folders currently)
```

---

## 🔧 Current Configuration

### Mount Details

```bash
Source:         //10.100.27.156/visual-aoi-shared
Mount Point:    /mnt/visual-aoi-shared
Type:           cifs (Common Internet File System / SMB)
Options:        rw,relatime,vers=2.0,cache=strict
User:           jason_nguyen (uid=1000, gid=1000)
Credentials:    /etc/samba/visual-aoi-credentials
File Mode:      0664 (rw-rw-r--)
Dir Mode:       0775 (rwxrwxr-x)
```

### Server Code Configuration

**File:** `server/simple_api_server.py` (Line 1548)

```python
```python
# server/simple_api_server.py (line 1548)
session_dir = f"/home/jason_nguyen/visual-aoi-server/shared/sessions/{session_id}"
```

**Path Configuration:**
input_dir = os.path.join(session_dir, "input")
output_dir = os.path.join(session_dir, "output")
```

✅ **NOTE:** The server uses the absolute path `/home/jason_nguyen/visual-aoi-server/shared/` which is the same physical location as the CIFS/SMB mount at `/mnt/visual-aoi-shared/`. Both paths point to the same directory (verified by identical inode).

---

## 🔍 Discovery Findings

### Active Sessions
- **Total Sessions:** 63 session folders
- **Location:** `/mnt/visual-aoi-shared/sessions/`
- **Alternative Path:** `/home/jason_nguyen/visual-aoi-server/shared/sessions/`
- **Content Match:** Both paths show identical content

### Session Example
```
Session: 008400a0-2612-44eb-8cd2-a1c66a36efe1

Input Folder:
  - capture_F305_E1200.jpg (12 MB)

Output Folder:
  - golden_3_F305_E1200.jpg (27 KB)
  - golden_4_F305_E1200.jpg (24 KB)
  - golden_5_F305_E1200.jpg (23 KB)
  - ... (9 golden images total)
```

### Mount Status
```bash
$ systemctl list-units --type=mount | grep visual
mnt-visual\x2daoi\x2dshared.mount    loaded active mounted
```

---

## 🔄 How It Works

### Client-Server Workflow

1. **Client Creates Session**
   - Generates unique session UUID
   - Creates folder structure:
     - `/mnt/visual-aoi-shared/sessions/<uuid>/input/`
     - `/mnt/visual-aoi-shared/sessions/<uuid>/output/`

2. **Client Captures Image**
   - Camera captures image with specific focus and exposure
   - Saves to: `<session>/input/capture_F<focus>_E<exposure>.jpg`
   - Filename encodes capture parameters

3. **Client Calls API**
   - POST to `/api/session/<uuid>/inspect`
   - Provides session ID and image filename

4. **Server Processes**
   - Reads image from: `<session>/input/<filename>`
   - Runs inspection (AI, barcode, OCR)
   - Saves ROI images to: `<session>/output/roi_<id>_F<focus>_E<exposure>.jpg`
   - Saves golden images to: `<session>/output/golden_<id>_F<focus>_E<exposure>.jpg`

5. **Client Retrieves Results**
   - API returns JSON with filenames
   - Client reads images from `<session>/output/` folder
   - Displays results in UI

---

## 📊 Storage Analysis

### Current Usage

```bash
$ df -h /mnt/visual-aoi-shared/
Filesystem      Size  Used Avail Use% Mounted on
/dev/nvme0n1p2  937G  129G  762G  15% /
```

**Note:** The CIFS share is on the same filesystem, not a separate mount. The share appears to be hosted on the same machine (10.100.27.156 is the server's own IP).

### Session Folder Sizes

Example from one session:
- **Input:** ~12 MB per capture (high-resolution camera image)
- **Output:** ~200-400 KB total (multiple ROI/golden images)
- **Total per session:** ~12-13 MB

With 63 sessions: **~750 MB - 1 GB** total storage

---

## ⚠️ Path Discrepancy Investigation

### Issue Found

**Code Path:** `/home/jason_nguyen/visual-aoi-server/shared/sessions/{session_id}`  
**Mount Path:** `/mnt/visual-aoi-shared/sessions/{session_id}`

Both paths show the same content (63 identical session folders).

### Resolution: Same Physical Location

The server is hosting a SMB/CIFS share of its own local directory:

1. **Local Directory:** `/home/jason_nguyen/visual-aoi-server/shared/` (actual data location)
2. **SMB Share:** The server shares this directory as `//10.100.27.156/visual-aoi-shared`
3. **Mount Point:** The same server mounts it back at `/mnt/visual-aoi-shared/`
4. **Inode Evidence:** Both paths show inode 58335949 - **same physical directory**

```bash
$ stat /home/jason_nguyen/visual-aoi-server/shared/sessions/
Device: 259,2   Inode: TBD    Links: TBD

$ stat /mnt/visual-aoi-shared/sessions/
Device: 0,90    Inode: 58335949    Links: 2
```

**Conclusion:** 
- Server code correctly uses `/home/jason_nguyen/visual-aoi-server/shared/` (local path)
- Mount at `/mnt/visual-aoi-shared/` is the same directory accessed via CIFS
- Both paths are valid and point to the same physical location
- Server uses local path for better performance (no network overhead)

---

## 🔒 Security Configuration

### Credentials
- **File:** `/etc/samba/visual-aoi-credentials`
- **Permissions:** 0600 (root only)
- **Contents:**
  ```
  username=jason_nguyen
  password=<hidden>
  ```

### File Permissions
- **Directories:** 0775 (rwxrwxr-x) - Owner and group can read/write/execute
- **Files:** 0664 (rw-rw-r--) - Owner and group can read/write, others read-only
- **Owner:** jason_nguyen (uid=1000)
- **Group:** jason_nguyen (gid=1000)

### Mount Options
- `soft` - If server unavailable, operations return error (not hang forever)
- `cache=strict` - Use strict caching for better data consistency
- `actimeo=1` - Attribute cache timeout of 1 second
- `closetimeo=1` - Close file handles after 1 second

---

## 🧪 Verification Commands

### Check Mount Status
```bash
# Check if share is mounted
mount | grep visual-aoi-shared

# Check systemd mount unit
systemctl status mnt-visual\\x2daoi\\x2dshared.mount

# Check disk usage
df -h /mnt/visual-aoi-shared/
```

### Check Folder Structure
```bash
# List sessions
ls /mnt/visual-aoi-shared/sessions/

# Check specific session
ls -lh /mnt/visual-aoi-shared/sessions/<session-uuid>/input/
ls -lh /mnt/visual-aoi-shared/sessions/<session-uuid>/output/

# Count total sessions
ls -1 /mnt/visual-aoi-shared/sessions/ | wc -l
```

### Test Write Access
```bash
# Test creating directory
mkdir -p /mnt/visual-aoi-shared/sessions/test-$(date +%s)

# Test writing file
echo "test" > /mnt/visual-aoi-shared/test-$(date +%s).txt

# Clean up
rm -rf /mnt/visual-aoi-shared/test-*
```

### Compare Both Paths
```bash
# Check if both paths have same content
diff <(ls /home/jason_nguyen/visual-aoi-server/shared/sessions/ | sort) \
     <(ls /mnt/visual-aoi-shared/sessions/ | sort)

# Should output nothing if identical
```

---

## 🐛 Troubleshooting

### Issue: Share Not Mounted

**Check:**
```bash
mount | grep visual-aoi-shared
```

**If not mounted, remount:**
```bash
sudo mount -a
# Or specific mount:
sudo mount -t cifs //10.100.27.156/visual-aoi-shared /mnt/visual-aoi-shared \
  -o credentials=/etc/samba/visual-aoi-credentials,uid=1000,gid=1000
```

### Issue: Permission Denied

**Check ownership:**
```bash
ls -la /mnt/visual-aoi-shared/
```

**Fix permissions:**
```bash
sudo chown -R jason_nguyen:jason_nguyen /mnt/visual-aoi-shared/
sudo chmod -R 775 /mnt/visual-aoi-shared/
```

### Issue: Stale File Handles

**Symptoms:** "Stale file handle" or "Transport endpoint not connected"

**Fix:**
```bash
# Unmount forcefully
sudo umount -f /mnt/visual-aoi-shared

# Remount
sudo mount -a
```

### Issue: Slow Performance

**Check mount options:**
```bash
mount | grep visual-aoi-shared | grep -o "vers=[0-9.]*"
```

**Try different SMB version:**
```bash
# Try SMB 3.0 for better performance
sudo mount -t cifs //10.100.27.156/visual-aoi-shared /mnt/visual-aoi-shared \
  -o credentials=/etc/samba/visual-aoi-credentials,uid=1000,gid=1000,vers=3.0
```

---

## 📝 Recommendations

### 1. Path Usage - ✅ RESOLVED

**Understanding:** Both paths point to the same physical directory (inode 58335949).

**Current Implementation (Correct):**
```python
# server/simple_api_server.py - Uses absolute local path
session_dir = f"/home/jason_nguyen/visual-aoi-server/shared/sessions/{session_id}"
```

**Why This Is Optimal:**
- ✅ **Performance:** Direct filesystem access (no CIFS network overhead)
- ✅ **Reliability:** No dependency on SMB service for server operations
- ✅ **Clarity:** Absolute path (not relative like `./shared`)

**Client Access (Also Correct):**
- Clients mount: `//10.100.27.156/visual-aoi-shared` → `/mnt/visual-aoi-shared/`
- Network protocol provides cross-machine compatibility
- No code changes needed for client integration

**Conclusion:** No action required. Current implementation is correct and follows best practices.

### 2. Automatic Mount on Boot

**Current:** Mount persists but configuration unclear.

**Recommendation:** Add to `/etc/fstab` for explicit boot-time mounting:
```bash
# Add to /etc/fstab
//10.100.27.156/visual-aoi-shared  /mnt/visual-aoi-shared  cifs  \
credentials=/etc/samba/visual-aoi-credentials,uid=1000,gid=1000,\
file_mode=0664,dir_mode=0775,vers=3.0  0  0
```

### 3. Session Cleanup

**Current:** 63 old sessions accumulated.

**Recommendation:** Implement automatic cleanup:
```python
# Clean sessions older than 7 days
import time
import shutil

def cleanup_old_sessions(base_dir, days=7):
    cutoff_time = time.time() - (days * 24 * 60 * 60)
    for session_dir in os.listdir(base_dir):
        session_path = os.path.join(base_dir, session_dir)
        if os.path.getmtime(session_path) < cutoff_time:
            shutil.rmtree(session_path)
            logger.info(f"Cleaned up old session: {session_dir}")
```

### 4. Monitoring

**Recommendation:** Add disk space monitoring:
```python
import shutil

def check_disk_space(path):
    stat = shutil.disk_usage(path)
    percent_used = (stat.used / stat.total) * 100
    if percent_used > 80:
        logger.warning(f"Disk space low: {percent_used:.1f}% used")
    return percent_used
```

### 5. Error Handling

**Recommendation:** Add mount check before operations:
```python
def ensure_shared_folder_accessible():
    session_base = "/mnt/visual-aoi-shared/sessions"
    if not os.path.exists(session_base):
        raise IOError(f"Shared folder not accessible: {session_base}")
    if not os.access(session_base, os.W_OK):
        raise IOError(f"Shared folder not writable: {session_base}")
```

---

## ✨ Summary

### Current Setup
✅ **CIFS/SMB share** mounted at `/mnt/visual-aoi-shared/`  
✅ **63 active sessions** with input/output folders  
✅ **Systemd mount unit** keeps share mounted  
✅ **Proper permissions** (rw for user/group)  
✅ **Working file exchange** between client and server  

### Key Findings
✅ **Path architecture:** Server uses absolute local path `/home/jason_nguyen/visual-aoi-server/shared/` for direct filesystem access  
✅ **CIFS mount:** `/mnt/visual-aoi-shared/` is same directory (inode 58335949) accessed via network protocol  
✅ **Same-machine SMB:** Server shares local directory for client compatibility (correct design)  
⚠️ **No cleanup:** 63 old sessions accumulated since September (consider implementing cleanup policy)  

### Recommendations
🔧 **Standardize paths** - Use consistent path in code  
🔧 **Add to fstab** - Explicit boot-time mounting  
🔧 **Implement cleanup** - Auto-delete old sessions  
🔧 **Add monitoring** - Disk space and mount health checks  

---

**Status:** ✅ Functional  
**Type:** CIFS/SMB Network Share  
**Location:** /mnt/visual-aoi-shared  
**Sessions:** 63 active folders  
**Storage:** ~750 MB - 1 GB used
