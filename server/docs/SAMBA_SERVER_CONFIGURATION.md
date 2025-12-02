# Samba/CIFS Server Configuration - Visual AOI Server

**Date**: October 13, 2025  
**Server**: 10.100.27.156 (FVN-ML-001)  
**Status**: ✅ **ALREADY CONFIGURED AND OPERATIONAL**

---

## 🎯 Overview

The Visual AOI Server is using **Samba/CIFS** (not NFS) to share folders with Windows and Linux clients over the network. Samba has been running since October 3, 2025, with active client connections.

---

## ✅ Current Configuration

### Samba Service Status

```bash
● smbd.service - Samba SMB Daemon
   Active: active (running) since Fri 2025-10-03 20:19:11 +07
   Status: "smbd: ready to serve connections..."
```

**Running for**: 1 week 2 days  
**Auto-start**: Enabled on boot ✅

---

## 📂 Active Samba Shares

### 1. **visual-aoi-shared** (Primary Share)

**Path**: `/home/jason_nguyen/visual-aoi-server/shared`  
**Network Path**: `\\10.100.27.156\visual-aoi-shared`  
**Purpose**: Session data, inspection results, ROI images

**Contents**:

- `sessions/{uuid}/input/` - Input images from clients
- `sessions/{uuid}/output/` - Processed ROI images
- `golden/` - Symlink to `../config/products`

**Configuration**:

```ini
[visual-aoi-shared]
    comment = Visual AOI Shared Storage
    path = /home/jason_nguyen/visual-aoi-server/shared
    browseable = yes
    writable = yes
    guest ok = no
    valid users = jason_nguyen
    create mask = 0755
    directory mask = 0755
    force user = jason_nguyen
    force group = jason_nguyen
```

### 2. **visual-aoi-server** (Full Server Share)

**Path**: `/home/jason_nguyen/visual-aoi-server`  
**Network Path**: `\\10.100.27.156\visual-aoi-server`  
**Purpose**: Full server access (config, code, documentation)

**Contents**:

- `shared/` - Same as visual-aoi-shared
- `config/products/` - Golden samples and ROI configurations
- `server/` - API server code
- `src/` - Source code modules
- `docs/` - Documentation

**Configuration**:

```ini
[visual-aoi-server]
    comment = Visual AOI Client Sourcer
    path = /home/jason_nguyen/visual-aoi-server
    browseable = yes
    writable = yes
    guest ok = no
    valid users = jason_nguyen
    create mask = 0755
    directory mask = 0755
    force user = jason_nguyen
    force group = jason_nguyen
```

### 3. **visual-aoi-client** (Client Application Share)

**Path**: `/home/jason_nguyen/visual-aoi-client`  
**Network Path**: `\\10.100.27.156\visual-aoi-client`  
**Purpose**: Client application code and resources

---

## 👥 Active Client Connections

### Currently Connected Clients

| Client IP | Share | Connected Since | Status |
|-----------|-------|----------------|--------|
| 10.100.27.82 | visual-aoi-shared | Oct 13, 10:04 AM | ✅ Active |
| 10.100.27.82 | visual-aoi-server | Oct 10, 10:51 AM | ✅ Active |
| 10.100.27.82 | visual-aoi-client | Oct 10, 10:52 AM | ✅ Active |
| 10.100.27.112 | visual-aoi-shared | Oct 13, 11:02 AM | ✅ Active |
| 10.100.27.156 | visual-aoi-shared | Oct 3, 8:19 PM | ✅ Active (localhost) |

**Total Active Connections**: 3 unique clients

---

## 🔐 Authentication

**User**: `jason_nguyen`  
**Authentication**: Password-based (Samba user database)  
**Guest Access**: Disabled (more secure)

### Samba User Management

```bash
# List Samba users
sudo pdbedit -L

# Add new Samba user
sudo smbpasswd -a username

# Change Samba password
sudo smbpasswd username

# Delete Samba user
sudo smbpasswd -x username
```

---

## 💻 Client Setup Instructions

### Windows Clients

#### Option 1: Map Network Drive (GUI)

1. Open **File Explorer**
2. Right-click **This PC** → **Map network drive**
3. Choose drive letter (e.g., Z:)
4. Folder: `\\10.100.27.156\visual-aoi-shared`
5. Check **"Connect using different credentials"**
6. Enter:
   - Username: `jason_nguyen`
   - Password: [Samba password]
7. Check **"Reconnect at sign-in"**
8. Click **Finish**

#### Option 2: Command Line

```cmd
REM Map visual-aoi-shared to Z: drive
net use Z: \\10.100.27.156\visual-aoi-shared /user:jason_nguyen /persistent:yes

REM Map visual-aoi-server to Y: drive
net use Y: \\10.100.27.156\visual-aoi-server /user:jason_nguyen /persistent:yes

REM View mapped drives
net use
```

#### Option 3: Direct UNC Path

Simply use in code or File Explorer:

```
\\10.100.27.156\visual-aoi-shared\sessions\uuid\output\roi_3.jpg
```

---

### Linux Clients

#### Install CIFS Utilities

```bash
sudo apt-get update
sudo apt-get install cifs-utils
```

#### Mount Samba Share

**Option A: Manual Mount**

```bash
# Create mount point
sudo mkdir -p /mnt/visual-aoi-shared

# Mount share
sudo mount -t cifs //10.100.27.156/visual-aoi-shared /mnt/visual-aoi-shared \
  -o username=jason_nguyen,password=YOUR_PASSWORD,uid=$(id -u),gid=$(id -g)

# Verify
df -h | grep visual-aoi
```

**Option B: Auto-mount with Credentials File**

1. Create credentials file:

```bash
sudo nano /etc/samba-credentials
```

2. Add credentials:

```
username=jason_nguyen
password=YOUR_PASSWORD
```

3. Secure the file:

```bash
sudo chmod 600 /etc/samba-credentials
```

4. Add to `/etc/fstab`:

```
//10.100.27.156/visual-aoi-shared /mnt/visual-aoi-shared cifs credentials=/etc/samba-credentials,uid=1000,gid=1000,_netdev 0 0
```

5. Mount:

```bash
sudo mount -a
```

---

## 🔧 API Integration (Path Format)

### Current API Behavior

The Visual AOI API returns file paths that work with Samba mounts:

**Example Response**:

```json
{
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "roi_results": [
    {
      "roi_idx": 3,
      "roi_image_path": "/mnt/visual-aoi-shared/sessions/123e4567.../output/roi_3.jpg",
      "golden_image_path": "/mnt/visual-aoi-shared/golden/20003548/golden_rois/roi_3/best_golden.jpg"
    }
  ]
}
```

### Windows Client Path Conversion

**Linux path from API**: `/mnt/visual-aoi-shared/sessions/uuid/output/roi_3.jpg`

**Convert to Windows**:

- If mounted as Z: drive: `Z:\sessions\uuid\output\roi_3.jpg`
- Or UNC path: `\\10.100.27.156\visual-aoi-shared\sessions\uuid\output\roi_3.jpg`

**Python Example (Windows)**:

```python
import os

# API returns Linux path
linux_path = result['roi_image_path']

# Convert to Windows
if linux_path.startswith('/mnt/visual-aoi-shared'):
    # Option 1: Mapped drive
    windows_path = linux_path.replace('/mnt/visual-aoi-shared', 'Z:').replace('/', '\\')
    
    # Option 2: UNC path
    unc_path = linux_path.replace('/mnt/visual-aoi-shared', '\\\\10.100.27.156\\visual-aoi-shared').replace('/', '\\')

# Use the path
from PIL import Image
img = Image.open(windows_path)
```

---

## 🛠️ Server Management

### Check Samba Status

```bash
# Service status
sudo systemctl status smbd

# Active connections
sudo smbstatus

# Connected users
sudo smbstatus --brief

# Shared resources
sudo smbstatus --shares

# View configuration
testparm -s
```

### Restart Samba

```bash
# Restart service
sudo systemctl restart smbd

# Reload configuration (no downtime)
sudo smbcontrol all reload-config
```

### View Logs

```bash
# Real-time logs
sudo tail -f /var/log/samba/log.smbd

# Check for errors
sudo journalctl -u smbd -f

# View client-specific logs
sudo tail -f /var/log/samba/log.10.100.27.82
```

### Modify Configuration

```bash
# Edit configuration
sudo nano /etc/samba/smb.conf

# Test configuration
testparm

# Apply changes
sudo systemctl restart smbd
```

---

## 🔍 Troubleshooting

### Problem: Cannot Connect from Windows

**Symptoms**: "Network path not found" or "Access denied"

**Solutions**:

1. **Check connectivity**:

```cmd
ping 10.100.27.156
```

2. **Test SMB port**:

```cmd
telnet 10.100.27.156 445
```

3. **Try direct UNC path**:

```cmd
\\10.100.27.156\visual-aoi-shared
```

4. **Clear credentials cache**:

```cmd
net use * /delete
control userpasswords2
```

5. **Check Windows SMB version**:

```cmd
REM Enable SMBv2/v3
sc.exe config lanmanworkstation depend= bowser/mrxsmb10/mrxsmb20/nsi
sc.exe config mrxsmb20 start= auto
```

---

### Problem: Cannot Mount on Linux

**Symptoms**: `mount error(13): Permission denied`

**Solutions**:

1. **Install CIFS utilities**:

```bash
sudo apt-get install cifs-utils
```

2. **Check credentials**:

```bash
# Test with verbose output
sudo mount -t cifs //10.100.27.156/visual-aoi-shared /mnt/test \
  -o username=jason_nguyen,password=PASS,vers=3.0 -v
```

3. **Check SMB version**:

```bash
# Try different SMB versions
sudo mount -t cifs //10.100.27.156/visual-aoi-shared /mnt/test \
  -o username=jason_nguyen,password=PASS,vers=2.1
```

---

### Problem: Permission Denied Writing Files

**Solutions**:

1. **Check mount options** (Linux):

```bash
# Mount with proper uid/gid
sudo mount -t cifs //10.100.27.156/visual-aoi-shared /mnt/test \
  -o username=jason_nguyen,password=PASS,uid=$(id -u),gid=$(id -g)
```

2. **Check Samba user** (Server):

```bash
# Verify user exists
sudo pdbedit -L | grep jason_nguyen

# Reset password if needed
sudo smbpasswd jason_nguyen
```

3. **Check directory permissions** (Server):

```bash
ls -la /home/jason_nguyen/visual-aoi-server/shared
sudo chown -R jason_nguyen:jason_nguyen /home/jason_nguyen/visual-aoi-server/shared
sudo chmod -R 755 /home/jason_nguyen/visual-aoi-server/shared
```

---

### Problem: Slow Performance

**Solutions**:

1. **Check network**:

```bash
# Test bandwidth
iperf3 -s  # On server
iperf3 -c 10.100.27.156  # On client
```

2. **Optimize Samba** (add to `/etc/samba/smb.conf` under `[global]`):

```ini
# Performance tuning
socket options = TCP_NODELAY IPTOS_LOWDELAY SO_RCVBUF=131072 SO_SNDBUF=131072
read raw = yes
write raw = yes
min receivefile size = 16384
use sendfile = yes
aio read size = 16384
aio write size = 16384
```

3. **Restart Samba**:

```bash
sudo systemctl restart smbd
```

---

## 🔐 Security Considerations

### Current Security Setup

✅ **Authentication Required**: No guest access  
✅ **User-based Access**: Only `jason_nguyen` can access  
✅ **Local Network Only**: Not exposed to internet  
⚠️ **No Encryption**: SMB traffic not encrypted (acceptable for trusted network)

### Security Recommendations

1. **Use SMB3 with Encryption** (add to `/etc/samba/smb.conf`):

```ini
[global]
   server min protocol = SMB3
   server smb encrypt = required
```

2. **Restrict to Specific IPs**:

```ini
[visual-aoi-shared]
   hosts allow = 10.100.27.0/24
   hosts deny = 0.0.0.0/0
```

3. **Enable Audit Logging**:

```ini
[global]
   log level = 2
   max log size = 1000
```

4. **Regular Password Changes**:

```bash
# Change Samba password
sudo smbpasswd jason_nguyen
```

---

## 📊 Performance vs NFS

### Samba/CIFS Advantages

✅ **Windows Native**: Works seamlessly with Windows clients  
✅ **Authentication**: Built-in user authentication  
✅ **File Locking**: Better file locking for concurrent access  
✅ **Browseable**: Can browse shares in Network Neighborhood  
✅ **Already Running**: No additional setup needed  

### Samba/CIFS Disadvantages

⚠️ **Slightly Slower**: ~10-15% slower than NFS for large file transfers  
⚠️ **More Overhead**: SMB protocol has more overhead than NFS  
⚠️ **Memory Usage**: Uses more memory (1.5GB currently)  

### When to Use Samba vs NFS

| Use Case | Recommended |
|----------|-------------|
| Windows clients | ✅ Samba (CIFS) |
| Linux-only clients | NFS |
| Mixed Windows/Linux | ✅ Samba (works for both) |
| Authentication needed | ✅ Samba |
| Maximum performance | NFS |
| Current setup | ✅ Samba (already configured) |

**Recommendation**: Keep using Samba - it's already working well with your mixed environment!

---

## 📝 Configuration Files

### Main Config: `/etc/samba/smb.conf`

```ini
[global]
   workgroup = WORKGROUP
   server string = %h server (Samba, Ubuntu)
   # ... other global settings ...

[visual-aoi-shared]
    comment = Visual AOI Shared Storage
    path = /home/jason_nguyen/visual-aoi-server/shared
    browseable = yes
    writable = yes
    guest ok = no
    valid users = jason_nguyen
    create mask = 0755
    directory mask = 0755
    force user = jason_nguyen
    force group = jason_nguyen

[visual-aoi-server]
    comment = Visual AOI Client Sourcer
    path = /home/jason_nguyen/visual-aoi-server
    browseable = yes
    writable = yes
    guest ok = no
    valid users = jason_nguyen
    create mask = 0755
    directory mask = 0755
    force user = jason_nguyen
    force group = jason_nguyen

[visual-aoi-client]
    comment = Visual AOI Client Sourcer
    path = /home/jason_nguyen/visual-aoi-client
    browseable = yes
    writable = yes
    guest ok = no
    valid users = jason_nguyen
    create mask = 0755
    directory mask = 0755
    force user = jason_nguyen
    force group = jason_nguyen
```

---

## 🎓 Common Commands Reference

### Server Commands

```bash
# Status and monitoring
sudo systemctl status smbd                    # Service status
sudo smbstatus                                # All connections
sudo smbstatus --shares                       # Shared resources
sudo smbstatus --brief                        # Brief connection list

# Configuration
sudo nano /etc/samba/smb.conf                 # Edit config
testparm                                      # Test config
testparm -s                                   # Show active config

# Service management
sudo systemctl restart smbd                   # Restart
sudo systemctl reload smbd                    # Reload config
sudo smbcontrol all reload-config             # Reload without restart

# User management
sudo pdbedit -L                               # List users
sudo smbpasswd -a username                    # Add user
sudo smbpasswd username                       # Change password
sudo smbpasswd -x username                    # Delete user

# Logs
sudo tail -f /var/log/samba/log.smbd         # Server logs
sudo journalctl -u smbd -f                    # System logs
```

### Client Commands (Windows)

```cmd
REM Map drive
net use Z: \\10.100.27.156\visual-aoi-shared /user:jason_nguyen

REM List mapped drives
net use

REM Disconnect drive
net use Z: /delete

REM Clear all connections
net use * /delete

REM View shared resources
net view \\10.100.27.156
```

### Client Commands (Linux)

```bash
# Mount
sudo mount -t cifs //10.100.27.156/visual-aoi-shared /mnt/share \
  -o username=jason_nguyen,password=PASS

# Unmount
sudo umount /mnt/share

# List available shares
smbclient -L //10.100.27.156 -U jason_nguyen

# Check mount
df -h | grep cifs
mount | grep cifs
```

---

## ✅ Summary

**Status**: ✅ **Samba/CIFS Server OPERATIONAL**

- **Service**: Running for 1 week 2 days
- **Active Shares**: 3 shares configured
- **Connected Clients**: 3 active clients (10.100.27.82, 10.100.27.112, 10.100.27.156)
- **Authentication**: Password-based, user `jason_nguyen`
- **Auto-start**: Enabled on boot
- **Performance**: Good (1.5GB memory usage)

**Network Paths**:

- `\\10.100.27.156\visual-aoi-shared` - Primary share for inspection data
- `\\10.100.27.156\visual-aoi-server` - Full server access
- `\\10.100.27.156\visual-aoi-client` - Client application code

**Next Steps**: None needed - system is working perfectly! Continue using Samba for file sharing.

---

**Documentation Date**: October 13, 2025  
**Server**: 10.100.27.156 (FVN-ML-001)  
**Protocol**: Samba/CIFS (SMB)  
**Status**: Production Ready ✅
