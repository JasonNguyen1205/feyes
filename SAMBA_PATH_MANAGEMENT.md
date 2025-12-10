# Samba Share Path Management

## Overview

The Visual AOI system uses Samba (CIFS/SMB) to share files between the server and client machines. The **share path must match the server's actual repository location** for the system to work correctly.

## The Problem

When the repository location changes (e.g., from `/home/jason_nguyen/visual-aoi-server` to `/home/jason_nguyen/feyes`), the Samba configuration may still point to the old path, causing a mismatch:

```
❌ PROBLEM:
- Client saves image → //server/visual-aoi-shared/sessions/.../captures/image.jpg
- Samba writes to    → /home/jason_nguyen/visual-aoi-server/shared/...  (OLD PATH)
- Server looks in    → /home/jason_nguyen/feyes/server/shared/...        (NEW PATH)
- Result: "Input image not found" error
```

## Automatic Fix (Recommended)

The launcher scripts now **automatically detect and fix** Samba path mismatches:

### On Server Startup

When you run `./launch_server.sh`, it will:

1. ✅ Detect the current repository location
2. ✅ Check Samba configuration path
3. ✅ **Automatically update** if mismatch is found
4. ✅ Restart Samba service
5. ✅ Verify the fix

**Example output:**
```bash
⚠ Samba path mismatch detected!
  Current: /home/jason_nguyen/visual-aoi-server/shared
  Should be: /home/jason_nguyen/feyes/server/shared
Running automatic fix...
✓ Path updated successfully
✓ Samba restarted
```

### Manual Fix (If Needed)

If automatic fix fails, run the setup script directly:

```bash
cd /home/jason_nguyen/feyes/server
sudo ./setup_samba_server.sh
```

The script will:
- Detect the current repository path
- Update `/etc/samba/smb.conf` if needed
- Restart the Samba service

## Verification

### Check Current Samba Configuration

```bash
# View the share configuration
grep -A 10 '[visual-aoi-shared]' /etc/samba/smb.conf

# Expected output:
[visual-aoi-shared]
   comment = Visual AOI Shared Folder
   path = /home/jason_nguyen/feyes/server/shared  # ✓ Should match current repo
   browseable = yes
   read only = no
   ...
```

### Check What Path is Actually Shared

```bash
# On server
smbclient -L localhost -U jason_nguyen%1

# On client  
mount | grep visual-aoi-shared
```

### Verify Files Are in Correct Location

```bash
# On server - check where files are actually written
ls -la /home/jason_nguyen/feyes/server/shared/sessions/*/captures/

# On client - check mount point
ls -la /mnt/visual-aoi-shared/sessions/*/captures/
```

## After Changing Repository Location

Whenever you move or rename the repository:

1. **Server side:**
   ```bash
   cd /path/to/new/location/feyes
   ./launch_server.sh  # Auto-detects and fixes path
   ```

2. **Client side:**
   ```bash
   # Remount to ensure sync
   sudo umount /mnt/visual-aoi-shared
   ./client/mount_shared_folder_dynamic.sh <server_ip>
   ```

## Technical Details

### Path Resolution

The setup script uses absolute path resolution:
```bash
SHARED_FOLDER_ABS="$(cd "$SCRIPT_DIR" && pwd)/shared"
```

This ensures:
- ✅ Symlinks are resolved to actual paths
- ✅ Relative paths are converted to absolute
- ✅ Path is consistent across reboots

### Automatic Detection

The launcher checks on every startup:
```bash
CURRENT_PATH=$(grep -A 10 '\[visual-aoi-shared\]' /etc/samba/smb.conf | \
               grep 'path =' | head -1 | sed 's/.*path = //' | xargs)

if [ "$CURRENT_PATH" != "$SHARED_FOLDER_ABS" ]; then
    # Automatic fix triggered
fi
```

### Path Update Process

1. Extract current path from `/etc/samba/smb.conf`
2. Compare with detected repository path
3. If mismatch: use `sed` to update path in-place
4. Restart Samba: `systemctl restart smbd`

## Troubleshooting

### "Input image not found" Error

**Symptom:** Server logs show:
```
ERROR - Input image not found at absolute path: /home/jason_nguyen/feyes/server/shared/sessions/.../image.jpg
```

**Cause:** Samba path mismatch - files written to old location, server reads from new location

**Fix:**
```bash
# On server
cd /home/jason_nguyen/feyes
./launch_server.sh  # Auto-fixes path

# OR manually
cd /home/jason_nguyen/feyes/server
sudo ./setup_samba_server.sh
```

### Files Appear in Wrong Location

**Symptom:** Files saved by client don't appear in the server's repository

**Check:**
```bash
# On server - where is Samba writing?
grep 'path =' /etc/samba/smb.conf

# Where does server code look?
grep 'SHARED_FOLDER_PATH' /home/jason_nguyen/feyes/server/server/simple_api_server.py
```

Both should show the same base path.

### Cannot Update Samba Configuration

**Symptom:** `sudo` asks for password when auto-fixing

**Cause:** User doesn't have passwordless sudo for Samba commands

**Options:**

1. **Run launcher interactively** (enter password when prompted)
2. **Add passwordless sudo** (advanced):
   ```bash
   sudo visudo
   # Add: jason_nguyen ALL=(ALL) NOPASSWD: /bin/systemctl restart smbd, /usr/bin/tee -a /etc/samba/smb.conf
   ```
3. **Manual fix** (see Manual Fix section above)

## Prevention

To avoid path mismatches in the future:

1. ✅ **Always use launchers** (`./launch_server.sh`, `./launch_client.sh`)
2. ✅ **Don't manually edit** `/etc/samba/smb.conf` paths
3. ✅ **Use dynamic mounting** (`mount_shared_folder_dynamic.sh`)
4. ✅ **Verify after moves**: Run launchers after changing repo location

## Related Documentation

- **SAMBA_SETUP_GUIDE.md** - Initial Samba setup
- **SHARED_FOLDER_VERIFICATION.md** - Testing and verification
- **AUTOMATIC_SAMBA_INTEGRATION.md** - Launcher integration details
- **.github/copilot-instructions.md** - Architecture notes (line 65-68)

## Summary

| Scenario | Action | Auto-Fixed? |
|----------|--------|-------------|
| First-time setup | Run `./launch_server.sh` | ✅ Yes |
| Repository moved | Run `./launch_server.sh` | ✅ Yes |
| Path mismatch detected | Run `./launch_server.sh` | ✅ Yes |
| Manual verification needed | Run `setup_samba_server.sh` | ✅ Yes |
| Passwordless sudo not available | Manual edit `/etc/samba/smb.conf` | ❌ No |

**The system is self-healing** - just run the launchers and they'll detect and fix path issues automatically! 🎉
