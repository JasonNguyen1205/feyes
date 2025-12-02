# NFS Setup - Quick Reference Card

**Server**: 10.100.27.156 (FVN-ML-001)  
**Date**: October 13, 2025

---

## 🖥️ SERVER (10.100.27.156)

### Status Check

```bash
sudo systemctl status nfs-kernel-server
sudo exportfs -v
showmount -e localhost
```

### Restart NFS

```bash
sudo systemctl restart nfs-kernel-server
```

### Reload Exports (no restart)

```bash
sudo exportfs -ra
```

### View Active Connections

```bash
showmount -a
```

---

## 💻 CLIENT Setup (One-time)

### Quick Setup (Automated)

```bash
# Copy script from server
scp jason_nguyen@10.100.27.156:/home/jason_nguyen/visual-aoi-server/scripts/setup_nfs_client.sh .

# Run setup script
sudo bash setup_nfs_client.sh
```

### Manual Setup

```bash
# 1. Install NFS client
sudo apt-get update
sudo apt-get install nfs-common

# 2. Create mount points
sudo mkdir -p /mnt/visual-aoi-shared
sudo mkdir -p /mnt/visual-aoi-shared/golden

# 3. Mount shares
sudo mount -t nfs 10.100.27.156:/home/jason_nguyen/visual-aoi-server/shared /mnt/visual-aoi-shared
sudo mount -t nfs 10.100.27.156:/home/jason_nguyen/visual-aoi-server/config/products /mnt/visual-aoi-shared/golden

# 4. Verify
df -h | grep visual-aoi
```

### Auto-mount on Boot

Add to `/etc/fstab`:

```
10.100.27.156:/home/jason_nguyen/visual-aoi-server/shared /mnt/visual-aoi-shared nfs defaults,_netdev 0 0
10.100.27.156:/home/jason_nguyen/visual-aoi-server/config/products /mnt/visual-aoi-shared/golden nfs defaults,_netdev 0 0
```

Then: `sudo mount -a`

---

## 📂 Shared Paths

| Server Path | Client Mount | Contents |
|------------|--------------|----------|
| `/home/jason_nguyen/visual-aoi-server/shared` | `/mnt/visual-aoi-shared` | Session data, ROI images |
| `/home/jason_nguyen/visual-aoi-server/config/products` | `/mnt/visual-aoi-shared/golden` | Golden samples, configs |

---

## 🔧 Common Commands

### Check Mounts

```bash
df -h | grep visual-aoi
mount | grep visual-aoi
```

### Unmount

```bash
sudo umount /mnt/visual-aoi-shared/golden
sudo umount /mnt/visual-aoi-shared
```

### Remount

```bash
sudo mount -a
```

### Force Unmount (if stuck)

```bash
sudo umount -f /mnt/visual-aoi-shared
```

---

## 🐛 Troubleshooting

### Problem: Cannot Mount

```bash
# Check server is reachable
ping 10.100.27.156

# Check NFS port
telnet 10.100.27.156 2049

# Check exports available
showmount -e 10.100.27.156
```

### Problem: Permission Denied

```bash
# On server - check exports
sudo exportfs -v | grep no_root_squash

# On client - check you're using sudo
sudo ls /mnt/visual-aoi-shared
```

### Problem: Stale File Handle

```bash
# Unmount and remount
sudo umount -f /mnt/visual-aoi-shared
sudo mount -t nfs 10.100.27.156:/home/jason_nguyen/visual-aoi-server/shared /mnt/visual-aoi-shared
```

---

## 📝 API Integration

No code changes needed! API already returns paths like:

```json
{
  "roi_image_path": "/mnt/visual-aoi-shared/sessions/uuid/output/roi_3.jpg",
  "golden_image_path": "/mnt/visual-aoi-shared/golden/20003548/golden_rois/roi_3/best_golden.jpg"
}
```

Client applications can access these paths directly after mounting NFS.

---

## ✅ Verification Checklist

**Server (10.100.27.156)**:

- [x] NFS server running
- [x] Exports configured
- [x] Auto-start enabled

**Client**:

- [ ] NFS client installed
- [ ] Shares mounted
- [ ] Write access verified
- [ ] Auto-mount configured

---

## 📞 Support

**Full Documentation**: `/home/jason_nguyen/visual-aoi-server/docs/NFS_SERVER_SETUP.md`

**Quick Test**:

```bash
# On client - test access
ls /mnt/visual-aoi-shared/sessions
touch /mnt/visual-aoi-shared/test.txt && rm /mnt/visual-aoi-shared/test.txt
```
