# Shared Folder Server Matching - Critical Configuration

## Problem Statement

The Visual AOI system uses a CIFS/SMB shared folder for high-performance image exchange between client and server. **The shared folder mount MUST point to the same server that the application connects to**, otherwise inspection will fail.

## Why This Matters

### The Image Flow
1. **Client captures image** from TIS camera
2. **Client saves image** to `/mnt/visual-aoi-shared/sessions/{uuid}/input/image.jpg`
3. **Client sends request** to server with file path
4. **Server reads image** from `/home/jason_nguyen/visual-aoi-server/shared/sessions/{uuid}/input/image.jpg`
5. **Server processes** and saves results to `/home/jason_nguyen/visual-aoi-server/shared/sessions/{uuid}/output/`
6. **Client reads results** from `/mnt/visual-aoi-shared/sessions/{uuid}/output/`

### The Problem
If the client is connected to `10.100.27.32:5000` but the shared folder is mounted from `10.100.27.156`, then:
- Client saves images to Server B (`10.100.27.156`)
- Server A (`10.100.27.32`) cannot find the images
- Inspection fails with "file not found" errors

## Detection

### Automated Detection (Launcher)
The `launch_client.sh` script now **automatically detects** mismatches:
```bash
./launch_client.sh
```

Output example:
```
❌ Shared folder mounted to wrong server!
   Currently mounted: 10.100.27.156
   Should be mounted: 10.100.27.32
   Run: cd client && ./mount_shared_folder_dynamic.sh 10.100.27.32
```

### Manual Detection
```bash
# Check where shared folder is mounted
mount | grep visual-aoi-shared

# Example output:
//10.100.27.156/visual-aoi-shared on /mnt/visual-aoi-shared type cifs (...)
```

Extract the server IP (`10.100.27.156` in this case) and compare with your application's server URL.

## Solution

### Method 1: Dynamic Mount Script (Recommended)
Use the new dynamic mount script that accepts any server IP:

```bash
cd /home/pi/feyes/client
./mount_shared_folder_dynamic.sh 10.100.27.32
```

This will:
1. Unmount the old shared folder (if any)
2. Mount the shared folder from the specified server
3. Update `/etc/fstab` for automatic mounting on boot
4. Verify the mount succeeded

### Method 2: Manual Remount
```bash
# Unmount current mount
sudo umount /mnt/visual-aoi-shared

# Mount from correct server
sudo mount -t cifs //10.100.27.32/visual-aoi-shared /mnt/visual-aoi-shared \
    -o "username=jason_nguyen,password=YOUR_PASSWORD,uid=$(id -u),gid=$(id -g),file_mode=0755,dir_mode=0755,vers=3.0,_netdev"

# Update /etc/fstab
sudo nano /etc/fstab
# Change the IP in the visual-aoi-shared line to match your server
```

## Verification

After remounting, verify the configuration:

```bash
# Check mount status
mount | grep visual-aoi-shared

# Should show the correct server IP
//10.100.27.32/visual-aoi-shared on /mnt/visual-aoi-shared type cifs (...)

# Test file access
ls -la /mnt/visual-aoi-shared/
df -h /mnt/visual-aoi-shared/
```

## Best Practices

### 1. Always Use Dynamic Mount Script
The old `mount_shared_folder.sh` has a **hardcoded IP** (`10.100.27.156`) and is now deprecated. Always use:
```bash
./mount_shared_folder_dynamic.sh <server_ip>
```

### 2. Check Before Running Application
Before starting the client application:
```bash
# 1. Determine your target server IP
# 2. Check current mount
mount | grep visual-aoi-shared
# 3. If mismatch, remount
./client/mount_shared_folder_dynamic.sh <correct_server_ip>
# 4. Launch application
./launch_client.sh
```

### 3. One Server at a Time
The system can only work with **one server at a time**. If you need to switch servers:
1. Close the client application
2. Remount the shared folder to the new server
3. Restart the client application with the new server URL

### 4. Document Your Server IP
Keep track of which server you're using:
- Development server: `10.100.27.156`
- Production server: `10.100.27.32`
- Local testing: `localhost` (no shared folder needed)

## Troubleshooting

### Issue: "File not found" during inspection
**Cause**: Shared folder points to wrong server
**Solution**: Remount to correct server using `mount_shared_folder_dynamic.sh`

### Issue: Images not appearing in results
**Cause**: Server saved images to its local folder, but client mount points elsewhere
**Solution**: Remount to correct server

### Issue: Permission denied on shared folder
**Cause**: Wrong credentials or server not configured
**Solution**: 
1. Check server has Samba configured
2. Verify username/password
3. Check server firewall allows SMB (port 445)

### Issue: Mount fails
**Cause**: Server unreachable or not running Samba
**Solution**:
1. Ping the server: `ping 10.100.27.32`
2. Check Samba is running on server: `systemctl status smbd`
3. Verify firewall on server allows SMB

## Architecture Summary

```
┌─────────────────────────────────────────────────────┐
│  Client (Raspberry Pi)                              │
│  - Connects to: http://10.100.27.32:5000           │
│  - Mounts from: //10.100.27.32/visual-aoi-shared   │
│  - Local path: /mnt/visual-aoi-shared/             │
│                                                     │
│  ✓ MATCH: Same server IP for both!                 │
└───────────────────────┬─────────────────────────────┘
                        │
                        │ Network
                        │
┌───────────────────────┴─────────────────────────────┐
│  Server (10.100.27.32)                              │
│  - API: http://10.100.27.32:5000                    │
│  - Share: //10.100.27.32/visual-aoi-shared         │
│  - Local path: /home/jason_nguyen/visual-aoi-       │
│                server/shared/                       │
└─────────────────────────────────────────────────────┘
```

**Key Point**: The application server IP and the shared folder server IP **must be identical**.

## Files Modified (Nov 2025)

1. **`client/mount_shared_folder_dynamic.sh`** - New dynamic mount script
2. **`launch_client.sh`** - Auto-detection of mount mismatches
3. **`.github/copilot-instructions.md`** - Documentation of this requirement
4. **`client/SHARED_FOLDER_SERVER_MATCHING.md`** - This comprehensive guide

## References

- See `.github/copilot-instructions.md` - "File Exchange Architecture" section
- See `client/SHARED_FOLDER_SETUP.md` - Original setup instructions (uses old hardcoded IP)
- See `launch_client.sh` lines 191-215 - Mismatch detection code
