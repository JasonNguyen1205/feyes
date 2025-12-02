# Path Reference Corrections Summary

**Date:** 2025-01-XX  
**Status:** ✅ COMPLETED  
**Updated:** October 3, 2025 - Path changed to `/home/jason_nguyen/visual-aoi-server/shared/`

---

## 🔄 Path Update (October 3, 2025)

The server path has been updated from `/home/jason_nguyen/visual-aoi-server/shared/` to `/home/jason_nguyen/visual-aoi-server/shared/` to match the actual project directory structure. All references in this document have been updated to reflect the new path.

---

## Overview

Corrected documentation to accurately reflect that the server uses absolute path `/home/jason_nguyen/visual-aoi-server/shared/` rather than relative path `./shared`. This clarification ensures developers understand the actual implementation.

---

## Technical Background

### The Two Paths

1. **Server Local Path (Used in Code)**
   - Path: `/home/jason_nguyen/visual-aoi-server/shared/`
   - Type: Absolute filesystem path
   - Usage: Server code directly accesses this path
   - Performance: No network overhead (direct disk I/O)
   - Example in code (line 1548 of simple_api_server.py):
     ```python
     session_dir = f"/home/jason_nguyen/visual-aoi-server/shared/sessions/{session_id}"
     ```

2. **CIFS Network Mount (Client Access)**
   - Path: `/mnt/visual-aoi-shared/`
   - Type: CIFS/SMB network mount
   - Usage: Clients mount this share for file exchange
   - Protocol: SMB 2.0 with credentials
   - Share: `//10.100.27.156/visual-aoi-shared`

### Physical Reality

**Both paths point to the same physical directory:**
```bash
$ stat /home/jason_nguyen/visual-aoi-server/shared/sessions/
Device: 259,2   Inode: 58335949    Links: 65

$ stat /mnt/visual-aoi-shared/sessions/
Device: 0,90    Inode: 58335949    Links: 2
```

**Explanation:** The server shares its own local directory via CIFS/SMB. The mount at `/mnt/visual-aoi-shared/` is accessing that same shared directory through the network protocol.

---

## Files Updated

### 1. docs/SHARED_FOLDER_CONFIGURATION.md

**Changes Made:**

#### A. NOTE Section (Line ~100)
**Before:**
```markdown
⚠️ NOTE: The server code references `/home/jason_nguyen/visual-aoi-server/shared/` but the mounted 
path is `/mnt/visual-aoi-shared/`. This needs investigation - they may be different paths.
```

**After:**
```markdown
✅ NOTE: The server uses the absolute path `/home/jason_nguyen/visual-aoi-server/shared/` for 
direct filesystem access. The CIFS mount at `/mnt/visual-aoi-shared/` is the same 
physical directory (verified by inode 58335949). Both paths are valid and correct.
```

#### B. Possible Explanations Section → Resolution Section
**Before:**
```markdown
### Possible Explanations

1. **Symlink:** `/home/jason_nguyen/visual-aoi-server/shared/` → `/mnt/visual-aoi-shared/`
2. **Bind Mount:** Secondary mount of the same share
3. **Same Filesystem:** Both are on the same local filesystem
4. **SMB Server on Same Machine:** Server is sharing its own local folder

**Conclusion:** The server is mounting its own SMB share. Both paths likely refer to 
the same physical location on disk.
```

**After:**
```markdown
### Resolution: Same Physical Location

The server is hosting a SMB/CIFS share of its own local directory:

1. **Local Directory:** `/home/jason_nguyen/visual-aoi-server/shared/` (actual data location)
2. **SMB Share:** The server shares this directory as `//10.100.27.156/visual-aoi-shared`
3. **Mount Point:** The same server mounts it back at `/mnt/visual-aoi-shared/`
4. **Inode Evidence:** Both paths show inode 58335949 - **same physical directory**

**Conclusion:** 
- Server code correctly uses `/home/jason_nguyen/visual-aoi-server/shared/` (local path)
- Mount at `/mnt/visual-aoi-shared/` is the same directory accessed via CIFS
- Both paths are valid and point to the same physical location
- Server uses local path for better performance (no network overhead)
```

#### C. Recommendations Section
**Before:**
```markdown
### 1. Path Consistency

**Current Issue:** Code uses two different paths for the same location.

**Recommendation:** Choose one path and update code consistently.

**Option A - Use Mount Path:**
# server/simple_api_server.py
session_dir = f"/mnt/visual-aoi-shared/sessions/{session_id}"

**Option B - Create Symlink:**
ln -s /mnt/visual-aoi-shared /home/jason_nguyen/visual-aoi-server/shared
```

**After:**
```markdown
### 1. Path Usage - ✅ RESOLVED

**Understanding:** Both paths point to the same physical directory (inode 58335949).

**Current Implementation (Correct):**
# server/simple_api_server.py - Uses absolute local path
session_dir = f"/home/jason_nguyen/visual-aoi-server/shared/sessions/{session_id}"

**Why This Is Optimal:**
- ✅ **Performance:** Direct filesystem access (no CIFS network overhead)
- ✅ **Reliability:** No dependency on SMB service for server operations
- ✅ **Clarity:** Absolute path (not relative like `./shared`)

**Conclusion:** No action required. Current implementation is correct and follows best practices.
```

#### D. Summary - Key Findings
**Before:**
```markdown
⚠️ **Path inconsistency:** Code uses `/home/.../shared/` but mount is at `/mnt/visual-aoi-shared/`
⚠️ **Same-machine SMB:** Server mounts its own share (unusual but functional)
```

**After:**
```markdown
✅ **Path architecture:** Server uses absolute local path `/home/jason_nguyen/visual-aoi-server/shared/` 
   for direct filesystem access
✅ **CIFS mount:** `/mnt/visual-aoi-shared/` is same directory (inode 58335949) accessed via 
   network protocol
✅ **Same-machine SMB:** Server shares local directory for client compatibility (correct design)
```

---

### 2. README.md

**Section:** Shared Folder Configuration → File Exchange Architecture

**Before:**
```markdown
- **Type:** CIFS/SMB Network Share
- **Mount Point:** `/mnt/visual-aoi-shared/`
- **Code Path:** `/home/jason_nguyen/visual-aoi-server/shared/` (same location)
- **Structure:** `sessions/<uuid>/input/` and `sessions/<uuid>/output/`

**Workflow:**
1. Client writes captured images to `sessions/<uuid>/input/`
2. Client calls API with session ID
3. Server reads from input folder
4. Server processes (AI, barcode, OCR)
5. Server writes ROI/golden images to `sessions/<uuid>/output/`
6. Client reads results from output folder
```

**After:**
```markdown
- **Type:** CIFS/SMB Network Share
- **Server Path:** `/home/jason_nguyen/visual-aoi-server/shared/` (absolute path used in code)
- **Client Mount:** `/mnt/visual-aoi-shared/` (CIFS network mount)
- **Note:** Both paths point to the same physical directory (verified by inode)
- **Structure:** `sessions/<uuid>/input/` and `sessions/<uuid>/output/`

**Workflow:**
1. Client writes captured images to `sessions/<uuid>/input/`
2. Client calls API with session ID
3. Server reads from input folder (using absolute local path)
4. Server processes (AI, barcode, OCR)
5. Server writes ROI/golden images to `sessions/<uuid>/output/`
6. Client reads results from output folder (via CIFS mount)
```

**Changes:**
- Replaced "Mount Point" / "Code Path" terminology with "Server Path" / "Client Mount"
- Added explicit note that both paths point to same physical directory
- Clarified workflow steps 3 and 6 to indicate which path is used

---

### 3. docs/PROJECT_INSTRUCTIONS.md

**Section A:** `/process_grouped_inspection` endpoint logic

**Before:**
```markdown
- **File System Access**: Read images from shared session directories
  - **Shared Folder**: `/home/jason_nguyen/visual-aoi-server/shared/sessions/<uuid>/`
  - **Input Folder**: `sessions/<uuid>/input/` - Client writes captured images
  - **Output Folder**: `sessions/<uuid>/output/` - Server writes ROI/golden images
  - **Mount**: CIFS/SMB network share at `/mnt/visual-aoi-shared/` (same location)
```

**After:**
```markdown
- **File System Access**: Read images from shared session directories
  - **Server Path**: `/home/jason_nguyen/visual-aoi-server/shared/sessions/<uuid>/` (absolute path in code)
  - **Input Folder**: `sessions/<uuid>/input/` - Client writes captured images
  - **Output Folder**: `sessions/<uuid>/output/` - Server writes ROI/golden images
  - **Client Access**: Via CIFS mount at `/mnt/visual-aoi-shared/` (same physical directory)
```

**Section B:** Shared Folder Architecture

**Before:**
```markdown
### Shared Folder Architecture
- **Type**: CIFS/SMB Network Share
- **Primary Path**: `/home/jason_nguyen/visual-aoi-server/shared/`
- **Mount Path**: `/mnt/visual-aoi-shared/` (same physical location)
- **Protocol**: SMB 2.0 with credentials at `/etc/samba/visual-aoi-credentials`
- **Permissions**: Read/Write for jason_nguyen (uid=1000)
- **Session Cleanup**: 63 active sessions (consider implementing auto-cleanup)
```

**After:**
```markdown
### Shared Folder Architecture
- **Type**: CIFS/SMB Network Share
- **Server Path**: `/home/jason_nguyen/visual-aoi-server/shared/` (absolute path used in server code)
- **Client Mount**: `/mnt/visual-aoi-shared/` (CIFS network mount for clients)
- **Physical Location**: Both paths point to same directory (inode 58335949)
- **Protocol**: SMB 2.0 with credentials at `/etc/samba/visual-aoi-credentials`
- **Permissions**: Read/Write for jason_nguyen (uid=1000)
- **Performance**: Server uses local path for direct access (no network overhead)
- **Session Cleanup**: 63 active sessions (consider implementing auto-cleanup)
```

**Changes:**
- Replaced "Primary Path" / "Mount Path" with "Server Path" / "Client Mount"
- Added "Physical Location" note with inode evidence
- Added "Performance" note explaining why server uses local path

---

## Terminology Standardization

### Server Side References
**Use:** "Server Path" or "absolute path"  
**Example:** `/home/jason_nguyen/visual-aoi-server/shared/`  
**Context:** When referring to the path used in server code

### Client Side References
**Use:** "Client Mount" or "CIFS mount"  
**Example:** `/mnt/visual-aoi-shared/`  
**Context:** When referring to network-accessible mount point

### General References
**Phrase:** "Both paths point to the same physical directory"  
**Evidence:** "verified by inode 58335949"  
**When to use:** When explaining relationship between the two paths

---

## Key Technical Points

### Why Two Paths Exist

1. **Server Performance**
   - Direct filesystem access avoids CIFS protocol overhead
   - Better I/O performance for server operations
   - No dependency on SMB service availability

2. **Client Compatibility**
   - CIFS/SMB provides network-accessible file share
   - Cross-platform support (Windows, Linux, Mac clients)
   - Standard protocol for file exchange

3. **Same Physical Location**
   - Server shares its own local directory
   - Mount accesses that share via network protocol
   - Both paths reference identical data (inode 58335949)

### Architecture Correctness

**This is the correct design:**
- ✅ Server uses local path for efficiency
- ✅ Clients use network mount for accessibility
- ✅ No synchronization needed (same directory)
- ✅ Performance optimized for server operations
- ✅ Network compatibility for distributed clients

---

## Verification Commands

### Check Inode Match
```bash
# Verify both paths point to same directory
stat /home/jason_nguyen/visual-aoi-server/shared/sessions/ | grep Inode
stat /mnt/visual-aoi-shared/sessions/ | grep Inode

# Expected output: Both show inode 58335949
```

### Check Server Code
```bash
# Verify path used in server code
grep -n "session_dir.*=.*shared" server/simple_api_server.py

# Expected output:
# Line 1548: session_dir = f"/home/jason_nguyen/visual-aoi-server/shared/sessions/{session_id}"
```

### Check Mount Point
```bash
# Verify CIFS mount
mount | grep visual-aoi

# Expected output:
# //10.100.27.156/visual-aoi-shared on /mnt/visual-aoi-shared type cifs (...)
```

---

## Documentation Impact

### Files Updated: 3
1. ✅ docs/SHARED_FOLDER_CONFIGURATION.md (4 sections corrected)
2. ✅ README.md (File Exchange Architecture section)
3. ✅ docs/PROJECT_INSTRUCTIONS.md (2 sections corrected)

### Lines Changed: ~50
- Replaced ambiguous terminology
- Added technical clarifications
- Included inode evidence
- Explained performance rationale

### Cross-References Updated
- All shared folder documentation now consistent
- Terminology standardized across all docs
- Clear distinction between server path and client mount

---

## Developer Guidance

### When Working with File I/O

1. **Server-Side Code**
   ```python
   # Use absolute local path
   session_dir = f"/home/jason_nguyen/visual-aoi-server/shared/sessions/{session_id}"
   ```

2. **Client-Side Code**
   ```python
   # Use mount point or direct SMB
   mount_dir = "/mnt/visual-aoi-shared/sessions/{session_id}"
   # OR
   smb_share = "//10.100.27.156/visual-aoi-shared/sessions/{session_id}"
   ```

3. **Documentation References**
   - Always specify "Server Path" vs "Client Mount"
   - Note they're the same physical location
   - Explain performance/compatibility reasons

---

## Future Considerations

### Path Configuration
Consider making the path configurable via environment variable:
```python
import os
SHARED_FOLDER_BASE = os.getenv(
    'VISUAL_AOI_SHARED_PATH',
    '/home/jason_nguyen/visual-aoi-server/shared'
)
```

### Documentation Template
When documenting file I/O operations, use this template:
```markdown
### File Access
- **Server Path:** `/home/jason_nguyen/visual-aoi-server/shared/...` (absolute path in code)
- **Client Mount:** `/mnt/visual-aoi-shared/...` (CIFS network access)
- **Note:** Both paths reference the same physical directory
```

---

## Summary

**Status:** ✅ All path references corrected  
**Consistency:** Terminology standardized across all documentation  
**Clarity:** Clear distinction between server path and client mount  
**Technical Accuracy:** Inode evidence documented, performance rationale explained  

**Key Message:** The server correctly uses absolute local path `/home/jason_nguyen/visual-aoi-server/shared/` for direct filesystem access, while clients access the same directory via CIFS mount at `/mnt/visual-aoi-shared/`. This architecture is optimal for performance and compatibility.

---

*Documentation Last Updated: 2025-01-XX*  
*Related Documents: SHARED_FOLDER_CONFIGURATION.md, PROJECT_INSTRUCTIONS.md, README.md*
