# Server Path Update - October 2025

**Date:** October 3, 2025  
**Status:** ✅ COMPLETED  
**Type:** Path Configuration Update

---

## Summary

Updated the server's shared folder path from `/home/jason_nguyen/visual-aoi-server/shared/` to `/home/jason_nguyen/visual-aoi-server/shared/` to align with the actual project directory structure.

---

## Changes Made

### 1. Server Code
**File:** `server/simple_api_server.py` (Line 1548)

**Before:**
```python
session_dir = f"/home/jason_nguyen/visual-aoi-server/shared/sessions/{session_id}"
```

**After:**
```python
session_dir = f"/home/jason_nguyen/visual-aoi-server/shared/sessions/{session_id}"
```

### 2. Documentation Files Updated

#### README.md
- Updated File Exchange Architecture section
- Changed server path reference

#### docs/PROJECT_INSTRUCTIONS.md
- Updated `/process_grouped_inspection` endpoint documentation
- Updated Shared Folder Architecture section

#### docs/SHARED_FOLDER_CONFIGURATION.md
- Updated all code examples
- Updated path references throughout
- Updated verification commands

#### docs/PATH_REFERENCE_CORRECTIONS.md
- Added update notice at the top
- Updated all historical path references

---

## Technical Details

### Old Configuration
```
Server Path: /home/jason_nguyen/visual-aoi-server/shared/
Client Mount: /mnt/visual-aoi-shared/
```

### New Configuration
```
Server Path: /home/jason_nguyen/visual-aoi-server/shared/
Client Mount: /mnt/visual-aoi-shared/
```

### Important Notes

1. **Directory Structure**: The new path matches the actual project directory (`visual-aoi-server`)
2. **Client Mount**: The CIFS mount point `/mnt/visual-aoi-shared/` remains unchanged
3. **Physical Location**: Both paths still point to the same physical directory
4. **Session Structure**: Still uses `sessions/<uuid>/input/` and `sessions/<uuid>/output/`

---

## Action Items

### Required Actions

- [ ] **Create the new directory structure** (if it doesn't exist):
  ```bash
  sudo mkdir -p /home/jason_nguyen/visual-aoi-server/shared/sessions
  sudo chown jason_nguyen:jason_nguyen /home/jason_nguyen/visual-aoi-server/shared
  ```

- [ ] **Update SMB share configuration** to share the new path:
  ```bash
  # Edit /etc/samba/smb.conf
  [visual-aoi-shared]
  path = /home/jason_nguyen/visual-aoi-server/shared
  ```

- [ ] **Restart SMB service**:
  ```bash
  sudo systemctl restart smbd
  ```

- [ ] **Remount the CIFS share** (if needed):
  ```bash
  sudo umount /mnt/visual-aoi-shared
  sudo mount -t cifs //10.100.27.156/visual-aoi-shared /mnt/visual-aoi-shared \
    -o credentials=/etc/samba/visual-aoi-credentials,uid=1000,gid=1000
  ```

- [ ] **Migrate existing sessions** (if any):
  ```bash
  # Copy existing sessions to new location
  cp -r /home/jason_nguyen/visual-aoi-server/shared/sessions/* \
        /home/jason_nguyen/visual-aoi-server/shared/sessions/
  ```

- [ ] **Verify the setup**:
  ```bash
  # Test write to new location
  touch /home/jason_nguyen/visual-aoi-server/shared/sessions/test.txt
  
  # Verify accessible via mount
  ls -la /mnt/visual-aoi-shared/sessions/test.txt
  
  # Clean up test file
  rm /home/jason_nguyen/visual-aoi-server/shared/sessions/test.txt
  ```

### Optional Actions

- [ ] **Update environment variables** (if any are set)
- [ ] **Update deployment scripts** (if they reference the old path)
- [ ] **Update backup scripts** (if they reference the old path)
- [ ] **Clean up old directory** (after confirming everything works):
  ```bash
  # Only do this after verifying the new path works!
  # rm -rf /home/jason_nguyen/visual-aoi/shared
  ```

---

## Verification Commands

### Check Directory Exists
```bash
ls -la /home/jason_nguyen/visual-aoi-server/shared/sessions/
```

### Check Permissions
```bash
stat /home/jason_nguyen/visual-aoi-server/shared/
```

### Check Server Code
```bash
grep -n "session_dir.*=" server/simple_api_server.py | grep shared
```

### Check CIFS Mount
```bash
mount | grep visual-aoi
```

### Test Session Creation
```bash
# Create a test session directory
mkdir -p /home/jason_nguyen/visual-aoi-server/shared/sessions/test-session/input
mkdir -p /home/jason_nguyen/visual-aoi-server/shared/sessions/test-session/output

# Verify accessible via both paths
ls /home/jason_nguyen/visual-aoi-server/shared/sessions/test-session/
ls /mnt/visual-aoi-shared/sessions/test-session/

# Clean up
rm -rf /home/jason_nguyen/visual-aoi-server/shared/sessions/test-session/
```

---

## Rollback Plan

If issues arise, you can revert the changes:

### 1. Revert Server Code
```bash
cd /home/jason_nguyen/visual-aoi-server
git checkout server/simple_api_server.py
```

### 2. Revert Documentation
```bash
git checkout README.md
git checkout docs/PROJECT_INSTRUCTIONS.md
git checkout docs/SHARED_FOLDER_CONFIGURATION.md
git checkout docs/PATH_REFERENCE_CORRECTIONS.md
```

### 3. Revert SMB Configuration
```bash
sudo nano /etc/samba/smb.conf
# Change path back to: /home/jason_nguyen/visual-aoi/shared
sudo systemctl restart smbd
```

---

## Impact Assessment

### Low Risk Areas ✅
- Server code has single point of path configuration
- Documentation updates are non-functional
- CIFS mount path unchanged for clients

### Medium Risk Areas ⚠️
- SMB share configuration needs update
- Existing sessions may need migration
- Service restart required

### Testing Required 🧪
- [ ] Test session creation via API
- [ ] Test file upload via client
- [ ] Test file download via client
- [ ] Test AI processing with new paths
- [ ] Test barcode detection with new paths
- [ ] Test OCR processing with new paths

---

## Related Documentation

- [SHARED_FOLDER_CONFIGURATION.md](./SHARED_FOLDER_CONFIGURATION.md) - Complete CIFS/SMB setup
- [PROJECT_INSTRUCTIONS.md](./PROJECT_INSTRUCTIONS.md) - File I/O endpoints
- [PATH_REFERENCE_CORRECTIONS.md](./PATH_REFERENCE_CORRECTIONS.md) - Historical path corrections
- [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md) - Overall project organization

---

## Success Criteria

✅ **Complete when:**
1. Server starts without errors
2. Session directories can be created
3. Files can be written to input folder
4. Files can be read from input folder
5. Files can be written to output folder
6. Files can be read from output folder via CIFS
7. All tests pass
8. Client can access files via CIFS mount

---

## Notes

- This change improves consistency with the project directory name (`visual-aoi-server`)
- The old path `/home/jason_nguyen/visual-aoi/` may still exist on the system
- Both paths could coexist during a migration period if needed
- Consider setting up a symlink as a temporary compatibility measure:
  ```bash
  ln -s /home/jason_nguyen/visual-aoi-server/shared /home/jason_nguyen/visual-aoi/shared
  ```

---

*Last Updated: October 3, 2025*  
*Author: System Update*
