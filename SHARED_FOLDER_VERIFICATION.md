# Shared Folder Verification Guide

## Quick Status Check

```bash
# 1. Verify symlink exists and points correctly
ls -la /mnt/visual-aoi-shared
# Should show: lrwxrwxrwx ... visual-aoi-shared -> /home/jason_nguyen/visual-aoi-server/shared

# 2. Test write permissions
touch /mnt/visual-aoi-shared/test_write.txt && rm /mnt/visual-aoi-shared/test_write.txt
# Should succeed without errors

# 3. Check shared folder permissions
stat -c "%a %U:%G %n" /home/jason_nguyen/visual-aoi-server/shared
# Should show: 755 jason_nguyen:jason_nguyen

# 4. Verify both paths point to same location
readlink -f /mnt/visual-aoi-shared
# Should output: /home/jason_nguyen/visual-aoi-server/shared
```

## Setup (Localhost - Client & Server on Same Machine)

The system uses a **symlink** (not CIFS/SMB mount) for localhost deployments:

```bash
# Remove old directory if exists
sudo rmdir /mnt/visual-aoi-shared 2>/dev/null

# Create symlink
sudo ln -s /home/jason_nguyen/visual-aoi-server/shared /mnt/visual-aoi-shared

# Verify
ls -la /mnt/visual-aoi-shared
```

## Path Mapping

| Component | Path Used | Actual Location |
|-----------|-----------|-----------------|
| **Client saves to** | `/mnt/visual-aoi-shared/sessions/{uuid}/captures/` | ↓ |
| **Symlink** | `/mnt/visual-aoi-shared` → `/home/jason_nguyen/visual-aoi-server/shared` | ↓ |
| **Server reads from** | `/home/jason_nguyen/visual-aoi-server/shared/sessions/{uuid}/captures/` | ✓ Same location |

## Troubleshooting

### Images not found during inspection

**Symptoms:**
```
ERROR - Input image not found at absolute path: /home/jason_nguyen/visual-aoi-server/shared/sessions/{uuid}/captures/group_230_400.jpg
```

**Checks:**
1. Verify symlink exists: `ls -la /mnt/visual-aoi-shared`
2. Check if captures folder is created: `ls /mnt/visual-aoi-shared/sessions/{uuid}/`
3. Verify client can write: `touch /mnt/visual-aoi-shared/test.txt && rm /mnt/visual-aoi-shared/test.txt`
4. Check permissions: `stat -c "%a" /home/jason_nguyen/visual-aoi-server/shared` (should be 755)

**Fix:**
```bash
# Recreate symlink
sudo rm /mnt/visual-aoi-shared 2>/dev/null
sudo ln -s /home/jason_nguyen/visual-aoi-server/shared /mnt/visual-aoi-shared

# Fix permissions
chmod 755 /home/jason_nguyen/visual-aoi-server/shared
chmod 755 /home/jason_nguyen/visual-aoi-server/shared/sessions
```

### Client doesn't save images

**Check client logs for:**
- `RuntimeError: Failed to save image to ...` - Permission issue
- No log about saving - Capture function not called
- `OSError: [Errno 30] Read-only file system` - Symlink broken

**Debug capture flow:**
```python
# Add to client/app.py in save_captured_image()
logger.info(f"[DEBUG] Attempting to save to: {filepath}")
logger.info(f"[DEBUG] Directory exists: {os.path.exists(captures_dir)}")
logger.info(f"[DEBUG] Can write: {os.access(captures_dir, os.W_OK)}")
```

## Remote Server Setup (Different Machines)

If client and server are on **different machines**, use CIFS/SMB mount instead:

```bash
# On server machine - share the folder via Samba
# On client machine - mount the share
sudo mount -t cifs //server_ip/visual-aoi-shared /mnt/visual-aoi-shared -o user=jason_nguyen,uid=$(id -u),gid=$(id -g)
```

See [SHARED_FOLDER_SETUP.md](client/SHARED_FOLDER_SETUP.md) for detailed remote setup.

## Launcher Script Updates

Both `launch_client.sh` and `launch_server.sh` now automatically:
- ✓ Check for symlink/mount existence
- ✓ Create symlink if localhost setup detected
- ✓ Set proper permissions (755)
- ✓ Verify write access

## Verification After Launch

After starting client and server, verify:

```bash
# 1. Create test session
curl -X POST http://localhost:5000/api/session/create -H "Content-Type: application/json" -d '{"product_id": "20003548"}'
# Note the session_id from response

# 2. Check session folders created
ls -la /home/jason_nguyen/visual-aoi-server/shared/sessions/{session_id}/

# 3. Client should be able to create captures/
mkdir -p /mnt/visual-aoi-shared/sessions/{session_id}/captures
ls -la /mnt/visual-aoi-shared/sessions/{session_id}/captures/

# 4. Both paths should show the same directory
ls -la /home/jason_nguyen/visual-aoi-server/shared/sessions/{session_id}/captures/
```

## Performance Notes

**Symlink (localhost):**
- ✅ Zero overhead - direct filesystem access
- ✅ No network latency
- ✅ No encoding/decoding (Base64 avoided)
- ✅ 195x faster than Base64 transmission

**CIFS mount (remote):**
- ⚠️ Network latency
- ✅ Still faster than Base64
- ⚠️ Requires Samba configuration
- ⚠️ May require credentials management

## Last Updated

2025-12-16 - Verified symlink setup for RTX 5080 deployment
