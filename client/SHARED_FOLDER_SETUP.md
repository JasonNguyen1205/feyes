# Shared Folder Setup Guide

**Issue:** Client can save images to `/mnt/visual-aoi-shared/sessions/...` but the server cannot see them because the folder is not shared over the network.

**Solution:** Set up NFS (Network File System) to share the folder between client and server.

## Architecture

```
┌─────────────────────────────────┐
│  Server (10.100.27.156)         │
│  - Hosts /mnt/visual-aoi-shared │
│  - NFS Server (exports folder)  │
│  - Processes inspection requests│
│  - Saves golden images          │
└────────────┬────────────────────┘
             │ NFS (Port 2049)
             │
┌────────────┴────────────────────┐
│  Client (Raspberry Pi)          │
│  - Mounts /mnt/visual-aoi-shared│
│  - NFS Client                   │
│  - Captures camera images       │
│  - Saves to shared folder       │
└─────────────────────────────────┘
```

## Step 1: Configure Server (10.100.27.156)

SSH to the server and run:

```bash
# SSH to server
ssh jason_nguyen@10.100.27.156

# Install NFS server
sudo apt-get update
sudo apt-get install -y nfs-kernel-server

# Create shared folder (if it doesn't exist)
sudo mkdir -p /mnt/visual-aoi-shared/sessions

# Set ownership (change 'jason_nguyen' to the actual user running the server)
sudo chown -R jason_nguyen:jason_nguyen /mnt/visual-aoi-shared

# Set permissions
sudo chmod -R 755 /mnt/visual-aoi-shared

# Configure NFS export
# This allows the client subnet (10.100.27.0/24) to mount the folder
echo "/mnt/visual-aoi-shared 10.100.27.0/24(rw,sync,no_subtree_check,no_root_squash)" | sudo tee -a /etc/exports

# If you want to restrict to only the client IP:
# echo "/mnt/visual-aoi-shared 10.100.27.XXX(rw,sync,no_subtree_check,no_root_squash)" | sudo tee -a /etc/exports
# (Replace XXX with client's last IP octet)

# Apply NFS export changes
sudo exportfs -ra

# Restart NFS server
sudo systemctl restart nfs-kernel-server

# Enable NFS server on boot
sudo systemctl enable nfs-kernel-server

# Verify export
sudo exportfs -v

# Check NFS server status
sudo systemctl status nfs-kernel-server

# Allow NFS through firewall (if firewall is enabled)
sudo ufw allow from 10.100.27.0/24 to any port nfs
```

**Expected output from `sudo exportfs -v`:**
```
/mnt/visual-aoi-shared
        10.100.27.0/24(rw,wdelay,no_root_squash,no_subtree_check,sec=sys,rw,secure,no_root_squash,no_all_squash)
```

## Step 2: Configure Client (Raspberry Pi)

**IMPORTANT:** Before mounting, backup local files if needed:

```bash
# Check what's currently in the local folder
ls -lR /mnt/visual-aoi-shared/

# If there are important files, backup first:
sudo mv /mnt/visual-aoi-shared /mnt/visual-aoi-shared.backup.$(date +%Y%m%d_%H%M%S)
```

**Run the automated mount script:**

```bash
cd /home/pi/visual-aoi-client
./mount_shared_folder.sh
```

**OR manually mount:**

```bash
# Install NFS client
sudo apt-get update
sudo apt-get install -y nfs-common

# Create mount point
sudo mkdir -p /mnt/visual-aoi-shared

# Test mount
sudo mount -t nfs -o vers=4,rw,sync 10.100.27.156:/mnt/visual-aoi-shared /mnt/visual-aoi-shared

# Verify mount
df -h /mnt/visual-aoi-shared
ls -la /mnt/visual-aoi-shared

# If successful, add to /etc/fstab for automatic mounting on boot
echo "10.100.27.156:/mnt/visual-aoi-shared /mnt/visual-aoi-shared nfs vers=4,rw,sync,_netdev 0 0" | sudo tee -a /etc/fstab
```

## Step 3: Test the Setup

### On Client (Raspberry Pi):

```bash
# Create test file
echo "Test from client" | sudo tee /mnt/visual-aoi-shared/test_client.txt

# Check if file exists
ls -la /mnt/visual-aoi-shared/test_client.txt
```

### On Server (10.100.27.156):

```bash
# SSH to server
ssh jason_nguyen@10.100.27.156

# Check if file is visible
cat /mnt/visual-aoi-shared/test_client.txt

# Should show: "Test from client"
```

### Test bidirectional access:

**On Server:**
```bash
echo "Test from server" | sudo tee /mnt/visual-aoi-shared/test_server.txt
```

**On Client:**
```bash
cat /mnt/visual-aoi-shared/test_server.txt
# Should show: "Test from server"
```

### Clean up test files:
```bash
sudo rm /mnt/visual-aoi-shared/test_*.txt
```

## Step 4: Restart Services and Test Full Flow

### On Client:

```bash
cd /home/pi/visual-aoi-client

# Make sure no_proxy is set
export no_proxy="localhost,127.0.0.1,10.100.27.156"
export NO_PROXY="localhost,127.0.0.1,10.100.27.156"

# Start the client
python3 ./app.py
```

### Test Inspection:

1. Open browser: `http://localhost:5100`
2. Connect to server
3. Select product
4. Initialize camera
5. Create session
6. Run inspection

### Verify Files on Server:

```bash
# SSH to server
ssh jason_nguyen@10.100.27.156

# Check session folders
ls -lR /mnt/visual-aoi-shared/sessions/

# You should see:
# - Captured images from client camera
# - Golden images saved by server
# - ROI crop images saved by server
```

## Troubleshooting

### Problem 1: "mount.nfs: Connection refused"

**Cause:** NFS server not running on server

**Solution:**
```bash
# On server
sudo systemctl start nfs-kernel-server
sudo systemctl status nfs-kernel-server
```

### Problem 2: "mount.nfs: access denied"

**Cause:** Export not configured or firewall blocking

**Solution:**
```bash
# On server, check exports
sudo exportfs -v

# If empty, add export again
echo "/mnt/visual-aoi-shared 10.100.27.0/24(rw,sync,no_subtree_check,no_root_squash)" | sudo tee -a /etc/exports
sudo exportfs -ra

# Check firewall
sudo ufw status
sudo ufw allow from 10.100.27.0/24 to any port nfs
```

### Problem 3: "Permission denied" when writing files

**Cause:** Wrong ownership or permissions

**Solution:**
```bash
# On server
sudo chown -R jason_nguyen:jason_nguyen /mnt/visual-aoi-shared
sudo chmod -R 755 /mnt/visual-aoi-shared

# In NFS export, make sure you have 'no_root_squash'
# Edit /etc/exports if needed:
sudo nano /etc/exports

# Then:
sudo exportfs -ra
sudo systemctl restart nfs-kernel-server
```

### Problem 4: Mount works but files not syncing

**Cause:** NFS cache or network delay

**Solution:**
```bash
# On client, remount with sync option
sudo umount /mnt/visual-aoi-shared
sudo mount -t nfs -o vers=4,rw,sync 10.100.27.156:/mnt/visual-aoi-shared /mnt/visual-aoi-shared

# Force sync after writing
sync
```

### Problem 5: Mount not persisting after reboot

**Cause:** Not added to /etc/fstab or wrong _netdev option

**Solution:**
```bash
# On client, check /etc/fstab
cat /etc/fstab | grep visual-aoi-shared

# Should show:
# 10.100.27.156:/mnt/visual-aoi-shared /mnt/visual-aoi-shared nfs vers=4,rw,sync,_netdev 0 0

# The _netdev option ensures mount waits for network
```

## Verification Checklist

- [ ] Server: NFS server installed and running
- [ ] Server: `/mnt/visual-aoi-shared` exists with correct permissions
- [ ] Server: Folder exported in `/etc/exports`
- [ ] Server: `exportfs -v` shows the export
- [ ] Server: Firewall allows NFS (port 2049)
- [ ] Client: NFS client installed (`nfs-common`)
- [ ] Client: `/mnt/visual-aoi-shared` mounted (check with `df -h`)
- [ ] Client: Can create files in shared folder
- [ ] Server: Can see files created by client
- [ ] Client: Can see files created by server
- [ ] Client: Mount added to `/etc/fstab` for persistence
- [ ] Full test: Run inspection and verify images visible on both sides

## Alternative: Manual File Copy (NOT RECOMMENDED)

If NFS setup is not possible, you could modify the client to send images via HTTP API, but this is **not recommended** because:

- Slower (network overhead for large 7716x5360 images)
- More complex (requires API changes on both sides)
- Defeats the purpose of the shared folder architecture
- Would require significant code changes

## Current Status

**Before NFS setup:**
- ❌ Client saves to local `/mnt/visual-aoi-shared/` (only visible on client)
- ❌ Server cannot see client's captured images
- ❌ Server saves golden images to its own local `/mnt/visual-aoi-shared/` (only visible on server)
- ❌ Client cannot display golden images from server

**After NFS setup:**
- ✅ Client and server share the same `/mnt/visual-aoi-shared/` folder
- ✅ Server can see client's captured images immediately
- ✅ Client can display golden images saved by server
- ✅ All inspection workflow works as designed

## Security Notes

### Current NFS Export Options

```
no_root_squash  - Allows root on client to write as root on server
                  Required for client to save images

rw              - Read-write access
sync            - Writes are committed to disk before responding
no_subtree_check - Improves reliability
```

### Production Security Improvements

For production, consider:

1. **Restrict to specific client IP:**
   ```
   /mnt/visual-aoi-shared 10.100.27.XXX(rw,sync,no_subtree_check,no_root_squash)
   ```

2. **Use Kerberos authentication:**
   ```
   /mnt/visual-aoi-shared 10.100.27.0/24(rw,sync,no_subtree_check,sec=krb5)
   ```

3. **Firewall rules:**
   ```bash
   # Allow only from client IP
   sudo ufw allow from 10.100.27.XXX to any port nfs
   ```

4. **Read-only for most access:**
   If only server needs write access, make it read-only for client:
   ```
   /mnt/visual-aoi-shared 10.100.27.XXX(ro,sync,no_subtree_check)
   ```

## Next Steps

1. **Configure server NFS export** (see Step 1)
2. **Run mount script on client:** `./mount_shared_folder.sh`
3. **Test with inspection workflow**
4. **Verify images are visible on both sides**

---

**Date:** October 13, 2025  
**Status:** Setup guide ready, awaiting server configuration  
**Script:** `mount_shared_folder.sh` ready to use
