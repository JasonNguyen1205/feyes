# NFS Server Setup for Visual AOI Server

**Date**: October 13, 2025  
**Server**: 10.100.27.156 (FVN-ML-001)  
**Status**: ✅ **CONFIGURED AND ACTIVE**

---

## 📋 Overview

The Visual AOI Server at 10.100.27.156 is now configured as an NFS server to share inspection data and golden samples with client machines over the network.

---

## 🗂️ Shared Directories

### 1. **Session Data** (Inspection Results & Images)

**Server Path**: `/home/jason_nguyen/visual-aoi-server/shared`  
**Network Export**: `10.100.27.156:/home/jason_nguyen/visual-aoi-server/shared`  
**Client Mount Point**: `/mnt/visual-aoi-shared`

**Contents**:

- `sessions/{uuid}/input/` - Input images from clients
- `sessions/{uuid}/output/` - Processed ROI images and results
- `golden/` - Symlink to `../config/products`

### 2. **Golden Samples** (Reference Images)

**Server Path**: `/home/jason_nguyen/visual-aoi-server/config/products`  
**Network Export**: `10.100.27.156:/home/jason_nguyen/visual-aoi-server/config/products`  
**Client Mount Point**: `/mnt/visual-aoi-shared/golden`

**Contents**:

- `{product_name}/rois_config_{product_name}.json` - Product configurations
- `{product_name}/golden_rois/roi_{idx}/` - Golden sample images

---

## ⚙️ NFS Server Configuration

### Configuration File: `/etc/exports`

```bash
# Visual AOI Server - Shared directory for client access
/home/jason_nguyen/visual-aoi-server/shared 10.100.27.0/24(rw,sync,no_subtree_check,no_root_squash)
/home/jason_nguyen/visual-aoi-server/config/products 10.100.27.0/24(rw,sync,no_subtree_check,no_root_squash)
```

### Export Options Explained

| Option | Description |
|--------|-------------|
| `10.100.27.0/24` | Allow access from entire 10.100.27.x subnet |
| `rw` | Read-write access |
| `sync` | Write changes to disk before responding (safer) |
| `no_subtree_check` | Disable subtree checking (better performance) |
| `no_root_squash` | Allow root on client to have root access (needed for file operations) |

---

## 🚀 Server Setup Commands

### Installation (Already Done)

```bash
# NFS server is already installed
sudo apt-get update
sudo apt-get install nfs-kernel-server nfs-common
```

### Configuration Applied

```bash
# 1. Backup original configuration
sudo cp /etc/exports /etc/exports.backup.$(date +%Y%m%d_%H%M%S)

# 2. Add exports to /etc/exports
echo '# Visual AOI Server - Shared directory for client access
/home/jason_nguyen/visual-aoi-server/shared 10.100.27.0/24(rw,sync,no_subtree_check,no_root_squash)
/home/jason_nguyen/visual-aoi-server/config/products 10.100.27.0/24(rw,sync,no_subtree_check,no_root_squash)' | sudo tee -a /etc/exports

# 3. Apply exports
sudo exportfs -ra

# 4. Restart NFS server
sudo systemctl restart nfs-kernel-server

# 5. Enable on boot
sudo systemctl enable nfs-kernel-server
```

### Verification

```bash
# Check exports are active
sudo exportfs -v

# Check NFS server status
sudo systemctl status nfs-kernel-server

# Check NFS ports
sudo rpcinfo -p | grep nfs
```

**Expected Output**:

```
/home/jason_nguyen/visual-aoi-server/shared
        10.100.27.0/24(sync,wdelay,hide,no_subtree_check,sec=sys,rw,secure,no_root_squash,no_all_squash)
/home/jason_nguyen/visual-aoi-server/config/products
        10.100.27.0/24(sync,wdelay,hide,no_subtree_check,sec=sys,rw,secure,no_root_squash,no_all_squash)
```

---

## 💻 Client Setup Instructions

### For Ubuntu/Linux Clients

#### 1. Install NFS Client

```bash
sudo apt-get update
sudo apt-get install nfs-common
```

#### 2. Create Mount Point

```bash
sudo mkdir -p /mnt/visual-aoi-shared
sudo mkdir -p /mnt/visual-aoi-shared/golden
```

#### 3. Mount NFS Shares

**Option A: Manual Mount (for testing)**

```bash
# Mount shared directory
sudo mount -t nfs 10.100.27.156:/home/jason_nguyen/visual-aoi-server/shared /mnt/visual-aoi-shared

# Mount golden samples
sudo mount -t nfs 10.100.27.156:/home/jason_nguyen/visual-aoi-server/config/products /mnt/visual-aoi-shared/golden
```

**Option B: Automatic Mount on Boot (recommended)**

Edit `/etc/fstab`:

```bash
sudo nano /etc/fstab
```

Add these lines:

```
# Visual AOI Server NFS Shares
10.100.27.156:/home/jason_nguyen/visual-aoi-server/shared /mnt/visual-aoi-shared nfs defaults,_netdev 0 0
10.100.27.156:/home/jason_nguyen/visual-aoi-server/config/products /mnt/visual-aoi-shared/golden nfs defaults,_netdev 0 0
```

Mount all:

```bash
sudo mount -a
```

#### 4. Verify Mount

```bash
# Check mounts
df -h | grep visual-aoi

# List shared files
ls -la /mnt/visual-aoi-shared/
ls -la /mnt/visual-aoi-shared/golden/

# Test write access
touch /mnt/visual-aoi-shared/test_file.txt
rm /mnt/visual-aoi-shared/test_file.txt
```

**Expected Output**:

```
10.100.27.156:/home/jason_nguyen/visual-aoi-server/shared         100G   50G   50G  50% /mnt/visual-aoi-shared
10.100.27.156:/home/jason_nguyen/visual-aoi-server/config/products 100G   50G   50G  50% /mnt/visual-aoi-shared/golden
```

---

## 🔧 Client Application Integration

### Python Example

```python
import os

# Server paths (on client machine after NFS mount)
SHARED_BASE = "/mnt/visual-aoi-shared"
SESSIONS_PATH = os.path.join(SHARED_BASE, "sessions")
GOLDEN_PATH = os.path.join(SHARED_BASE, "golden")

# Access session output
session_id = "123e4567-e89b-12d3-a456-426614174000"
output_path = os.path.join(SESSIONS_PATH, session_id, "output")

# List ROI images
if os.path.exists(output_path):
    roi_images = [f for f in os.listdir(output_path) if f.endswith('.jpg')]
    print(f"Found {len(roi_images)} ROI images")

# Access golden sample
product_name = "20003548"
roi_idx = 3
golden_image = os.path.join(GOLDEN_PATH, product_name, "golden_rois", 
                            f"roi_{roi_idx}", "best_golden.jpg")

if os.path.exists(golden_image):
    print(f"Golden sample found: {golden_image}")
```

### API Usage (No Changes Needed)

The API already returns file paths with the client mount prefix:

```json
{
  "roi_results": [
    {
      "roi_image_path": "/mnt/visual-aoi-shared/sessions/123e4567.../output/roi_3.jpg",
      "golden_image_path": "/mnt/visual-aoi-shared/golden/20003548/golden_rois/roi_3/best_golden.jpg"
    }
  ]
}
```

Clients can directly access these paths after mounting NFS shares.

---

## 🛡️ Security Considerations

### Current Configuration

- ✅ **Subnet Restriction**: Only 10.100.27.0/24 can access (local network)
- ✅ **No Root Squash**: Allows proper file operations
- ⚠️ **No Authentication**: NFS v3 has no user authentication (rely on network security)
- ✅ **Firewall**: Currently disabled (UFW inactive) - appropriate for trusted network

### Recommended Security Measures

1. **Network Isolation**: Keep 10.100.27.x network isolated from internet
2. **VPN Access**: Use VPN for remote access instead of exposing NFS
3. **Firewall Rules** (if needed):

```bash
# Allow NFS only from specific subnet
sudo ufw allow from 10.100.27.0/24 to any port 2049 proto tcp
sudo ufw allow from 10.100.27.0/24 to any port 111 proto tcp
sudo ufw enable
```

4. **Read-Only Access** (optional for golden samples):

```bash
# In /etc/exports, change to 'ro' for read-only:
/home/jason_nguyen/visual-aoi-server/config/products 10.100.27.0/24(ro,sync,no_subtree_check)
```

---

## 🔍 Troubleshooting

### Problem: Cannot Mount on Client

**Symptoms**: `mount.nfs: Connection refused`

**Solutions**:

```bash
# On server - check NFS is running
sudo systemctl status nfs-kernel-server

# On server - verify exports
sudo exportfs -v

# On client - check connectivity
ping 10.100.27.156
telnet 10.100.27.156 2049

# On client - check NFS client is installed
dpkg -l | grep nfs-common
```

### Problem: Permission Denied

**Symptoms**: Can mount but cannot write files

**Solutions**:

```bash
# On server - check directory permissions
ls -la /home/jason_nguyen/visual-aoi-server/shared

# Make directory writable
sudo chmod 755 /home/jason_nguyen/visual-aoi-server/shared

# Verify no_root_squash is set
sudo exportfs -v | grep no_root_squash
```

### Problem: Stale File Handle

**Symptoms**: `Stale NFS file handle` error

**Solutions**:

```bash
# On client - unmount and remount
sudo umount -f /mnt/visual-aoi-shared
sudo mount -t nfs 10.100.27.156:/home/jason_nguyen/visual-aoi-server/shared /mnt/visual-aoi-shared

# On server - re-export
sudo exportfs -ra
```

### Problem: Slow Performance

**Solutions**:

```bash
# On client - mount with performance options
sudo mount -t nfs -o rsize=8192,wsize=8192,timeo=14,intr \
  10.100.27.156:/home/jason_nguyen/visual-aoi-server/shared /mnt/visual-aoi-shared

# Or in /etc/fstab:
10.100.27.156:/home/jason_nguyen/visual-aoi-server/shared /mnt/visual-aoi-shared nfs rsize=8192,wsize=8192,timeo=14,intr,_netdev 0 0
```

---

## 📊 Monitoring & Maintenance

### Check Active Connections

```bash
# On server - show active NFS connections
sudo nfsstat -c

# Show what's exported
showmount -e localhost

# Show what clients are connected
showmount -a
```

### Monitor NFS Performance

```bash
# Real-time NFS statistics
nfsstat -s

# Monitor NFS I/O
iostat -x 2
```

### Logs

```bash
# System logs
sudo journalctl -u nfs-kernel-server -f

# Check for errors
sudo tail -f /var/log/syslog | grep nfs
```

---

## 🔄 Common Maintenance Tasks

### Restart NFS Server

```bash
sudo systemctl restart nfs-kernel-server
```

### Reload Exports (without restart)

```bash
sudo exportfs -ra
```

### Add New Export

```bash
# Edit /etc/exports
sudo nano /etc/exports

# Apply changes
sudo exportfs -ra
```

### Remove Export

```bash
# Edit /etc/exports and remove the line
sudo nano /etc/exports

# Unexport specific directory
sudo exportfs -u 10.100.27.0/24:/home/jason_nguyen/visual-aoi-server/shared

# Or reload all
sudo exportfs -ra
```

---

## 📈 Performance Optimization

### Server-Side Tuning

```bash
# Increase number of NFS server threads (default 8)
sudo nano /etc/default/nfs-kernel-server

# Add or modify:
RPCNFSDCOUNT=16
```

### Client-Side Mount Options

```bash
# High performance mount options
mount -t nfs -o rsize=131072,wsize=131072,hard,timeo=600,retrans=2,_netdev \
  10.100.27.156:/home/jason_nguyen/visual-aoi-server/shared /mnt/visual-aoi-shared
```

**Mount Options Explained**:

- `rsize=131072` - Read buffer size (128KB)
- `wsize=131072` - Write buffer size (128KB)
- `hard` - Keep trying if server unavailable
- `timeo=600` - Timeout 60 seconds
- `retrans=2` - Retry 2 times
- `_netdev` - Wait for network before mounting

---

## ✅ Setup Verification Checklist

Server Setup:

- [x] NFS server installed
- [x] `/etc/exports` configured
- [x] Exports applied (`exportfs -ra`)
- [x] NFS server running
- [x] NFS server enabled on boot
- [x] Firewall configured (or disabled for trusted network)

Client Setup:

- [ ] NFS client installed
- [ ] Mount points created
- [ ] Manual mount tested
- [ ] `/etc/fstab` configured for auto-mount
- [ ] Write access verified
- [ ] Application tested with NFS paths

---

## 🎯 Summary

✅ **NFS Server Status**: Active and running  
✅ **Shared Directories**: 2 exports configured  
✅ **Network Access**: 10.100.27.0/24 subnet  
✅ **Permissions**: Read-write with no_root_squash  
✅ **Auto-start**: Enabled on boot  

**Server**: 10.100.27.156  
**Exports**:

- `/home/jason_nguyen/visual-aoi-server/shared` → Client: `/mnt/visual-aoi-shared`
- `/home/jason_nguyen/visual-aoi-server/config/products` → Client: `/mnt/visual-aoi-shared/golden`

**Next Step**: Configure client machines to mount these NFS shares.

---

## 📚 References

- NFS Documentation: <https://linux.die.net/man/5/exports>
- Ubuntu NFS Guide: <https://ubuntu.com/server/docs/service-nfs>
- Performance Tuning: <https://nfs.sourceforge.net/nfs-howto/ar01s05.html>

---

**Author**: GitHub Copilot  
**Date**: October 13, 2025  
**Version**: 1.0  
**Status**: Production Ready
