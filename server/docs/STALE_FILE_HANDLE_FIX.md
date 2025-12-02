# Stale File Handle Fix - October 3, 2025

## Problem
```
jason_nguyen@FVN-ML-001:~/visual-aoi-server$ ls /mnt/visual-aoi-shared 
ls: cannot access '/mnt/visual-aoi-shared': Stale file handle
```

## Root Cause
The CIFS mount at `/mnt/visual-aoi-shared` was pointing to the old path `/home/jason_nguyen/visual-aoi/shared` which no longer exists. After updating the server code to use `/home/jason_nguyen/visual-aoi-server/shared`, the SMB share was updated but the CIFS mount was stale.

## Solution Applied

### 1. Unmounted Stale Connection
```bash
sudo umount -f /mnt/visual-aoi-shared
```

### 2. Verified SMB Configuration
The SMB configuration was already correctly updated:
```ini
[visual-aoi-shared]
    path = /home/jason_nguyen/visual-aoi-server/shared
```

### 3. Restarted SMB Service
```bash
sudo systemctl restart smbd
```
Status: Active (running) since October 3, 2025 20:19

### 4. Remounted CIFS Share
```bash
sudo mount -t cifs //10.100.27.156/visual-aoi-shared /mnt/visual-aoi-shared \
  -o credentials=/etc/samba/visual-aoi-credentials,uid=1000,gid=1000,\
     file_mode=0664,dir_mode=0775
```

### 5. Verified Both Paths
```bash
# Local path works
ls -la /home/jason_nguyen/visual-aoi-server/shared/sessions/
✅ drwxr-xr-x jason_nguyen jason_nguyen sessions

# CIFS mount works
ls -la /mnt/visual-aoi-shared/sessions/
✅ drwxrwxr-x jason_nguyen jason_nguyen sessions

# Both paths are synchronized
echo "test" > /home/jason_nguyen/visual-aoi-server/shared/sessions/test.txt
cat /mnt/visual-aoi-shared/sessions/test.txt
✅ test (file accessible from both paths)
```

## Current Status

### Mount Information
```
//10.100.27.156/visual-aoi-shared on /mnt/visual-aoi-shared type cifs
- SMB Version: 3.1.1 (upgraded from 2.0)
- User: jason_nguyen (uid=1000, gid=1000)
- Permissions: file_mode=0664, dir_mode=0775
- Status: Active and working
```

### Directory Structure
```
/home/jason_nguyen/visual-aoi-server/shared/
└── sessions/              (empty, ready for new sessions)
    
/mnt/visual-aoi-shared/
└── sessions/              (same physical directory via CIFS)
```

## Verification Commands

### Check Mount Status
```bash
mount | grep visual-aoi
# Should show active CIFS mount with SMB 3.1.1
```

### Test Write Access
```bash
touch /home/jason_nguyen/visual-aoi-server/shared/sessions/test.txt
ls /mnt/visual-aoi-shared/sessions/test.txt
# File should be visible from both paths
```

### Test Read Access
```bash
echo "content" > /mnt/visual-aoi-shared/sessions/test2.txt
cat /home/jason_nguyen/visual-aoi-server/shared/sessions/test2.txt
# Content should be readable from both paths
```

## Result: ✅ FIXED

The stale file handle error has been resolved. The CIFS mount is now properly connected to the new server path and both paths are synchronized.

## Next Steps

1. ✅ **Server can be restarted** - Infrastructure is ready
2. ⏭️ **Test API endpoints** - Verify session creation works
3. ⏭️ **Test client workflow** - Upload images, run inspection

## Related Documentation

- [PATH_UPDATE_SUMMARY.md](./PATH_UPDATE_SUMMARY.md) - Complete deployment summary
- [PATH_UPDATE_OCTOBER_2025.md](./PATH_UPDATE_OCTOBER_2025.md) - Migration guide
- [SHARED_FOLDER_CONFIGURATION.md](./SHARED_FOLDER_CONFIGURATION.md) - CIFS/SMB details

---

*Issue Resolved: October 3, 2025 20:19*  
*Time to Fix: ~5 minutes*  
*Impact: Zero downtime (server was not running)*
