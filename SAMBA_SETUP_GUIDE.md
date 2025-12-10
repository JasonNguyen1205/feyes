# Samba Shared Folder Setup Guide

## Overview

The Visual AOI system uses **different shared folder strategies** depending on deployment:

- **Localhost (same machine)**: Symlink `/mnt/visual-aoi-shared` → `server/shared`
- **Network (different machines)**: CIFS/SMB mount with Samba server

## Credentials

- **Username**: `jason_nguyen`
- **Password**: `1`

## Server Setup (One-time)

### Automatic Setup

Run the automated setup script on the **server machine**:

```bash
cd server/
./setup_samba_server.sh
```

This will:
1. Install Samba if not present
2. Create system user `jason_nguyen`
3. Configure Samba share `visual-aoi-shared`
4. Set password to `1`
5. Configure firewall (ports 139, 445)
6. Start Samba services

### Manual Setup

If you prefer manual configuration:

```bash
# 1. Install Samba
sudo apt-get update
sudo apt-get install -y samba samba-common-bin

# 2. Create system user
sudo useradd -M -s /usr/sbin/nologin jason_nguyen

# 3. Add to Samba configuration
sudo nano /etc/samba/smb.conf
```

Add this at the end:

```ini
[visual-aoi-shared]
   comment = Visual AOI Shared Folder
   path = /home/pi/feyes/server/shared
   browseable = yes
   read only = no
   guest ok = no
   valid users = jason_nguyen
   create mask = 0755
   directory mask = 0755
   force user = pi
   force group = pi
```

```bash
# 4. Set Samba password
sudo smbpasswd -a jason_nguyen
# Enter password: 1
# Retype password: 1

# 5. Enable user
sudo smbpasswd -e jason_nguyen

# 6. Restart Samba
sudo systemctl restart smbd nmbd

# 7. Enable on boot
sudo systemctl enable smbd nmbd
```

## Client Setup

### Localhost Setup (Same Machine)

When client and server run on the **same machine**, use symlink (automatic):

```bash
./launch_client.sh
```

The launcher will automatically detect localhost and create:
```
/mnt/visual-aoi-shared → /home/pi/feyes/server/shared
```

### Network Setup (Different Machines)

When client and server run on **different machines**:

#### Option 1: Automatic Mount (via launcher)

The client launcher will detect remote server and prompt:

```bash
./launch_client.sh -s http://10.100.27.32:5000
```

Follow the prompts to mount the shared folder.

#### Option 2: Manual Mount

```bash
cd client/
./mount_shared_folder_dynamic.sh 10.100.27.32
```

When prompted:
- Username: `jason_nguyen` (or press Enter for default)
- Password: `1` (or press Enter for default)

#### Option 3: Credentials File (Secure)

Create `/home/pi/.smbcredentials`:

```ini
username=jason_nguyen
password=1
```

Secure the file:
```bash
chmod 600 /home/pi/.smbcredentials
```

Mount with credentials file:
```bash
sudo mount -t cifs //10.100.27.32/visual-aoi-shared /mnt/visual-aoi-shared \
    -o "credentials=/home/pi/.smbcredentials,uid=$(id -u),gid=$(id -g),file_mode=0755,dir_mode=0755,vers=3.0"
```

## Verification

### Server Side

```bash
# Check Samba status
sudo systemctl status smbd

# List shares
smbclient -L localhost -U jason_nguyen%1

# Test share access
smbclient //localhost/visual-aoi-shared -U jason_nguyen%1

# Check listening ports
sudo netstat -tulpn | grep smbd
```

### Client Side

```bash
# Check mount status
mount | grep visual-aoi-shared

# Test write access
touch /mnt/visual-aoi-shared/test.txt && rm /mnt/visual-aoi-shared/test.txt

# Check from server side (should see same files)
ls -la /home/pi/feyes/server/shared/
```

## Troubleshooting

### Connection Refused

```bash
# Check firewall on server
sudo ufw status
sudo ufw allow 139/tcp
sudo ufw allow 445/tcp

# Check Samba is running
sudo systemctl status smbd nmbd

# Check network connectivity
ping 10.100.27.32
```

### Permission Denied

```bash
# Verify Samba user
sudo pdbedit -L -v jason_nguyen

# Reset password
sudo smbpasswd -a jason_nguyen

# Check share permissions
ls -la /home/pi/feyes/server/shared/
chmod 755 /home/pi/feyes/server/shared/
```

### Mount Fails with "Invalid Argument"

Try different SMB versions:

```bash
# Try SMB 3.0 (default)
sudo mount -t cifs //server/visual-aoi-shared /mnt/visual-aoi-shared -o vers=3.0,...

# Try SMB 2.1
sudo mount -t cifs //server/visual-aoi-shared /mnt/visual-aoi-shared -o vers=2.1,...

# Try SMB 1.0 (not recommended)
sudo mount -t cifs //server/visual-aoi-shared /mnt/visual-aoi-shared -o vers=1.0,...
```

### Check Samba Logs

```bash
# View Samba logs
sudo tail -f /var/log/samba/log.smbd

# View detailed logs
sudo journalctl -u smbd -f
```

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────┐
│                      LOCALHOST SETUP                         │
├─────────────────────────────────────────────────────────────┤
│  Client                          Server                      │
│  /mnt/visual-aoi-shared  ──────> /home/pi/feyes/server/shared
│       (symlink)                                              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                      NETWORK SETUP                           │
├─────────────────────────────────────────────────────────────┤
│  Client (10.100.27.10)           Server (10.100.27.32)      │
│  /mnt/visual-aoi-shared  ──────> Samba Server               │
│       (CIFS mount)               /home/pi/feyes/server/shared
│                                  [visual-aoi-shared]         │
│                                  user: jason_nguyen          │
│                                  pass: 1                     │
└─────────────────────────────────────────────────────────────┘
```

## Security Notes

1. **Default password is weak** - Change for production:
   ```bash
   sudo smbpasswd jason_nguyen
   ```

2. **Firewall rules** - Restrict to specific network:
   ```bash
   sudo ufw allow from 10.100.0.0/16 to any port 445
   ```

3. **Use credentials file** instead of command-line passwords

4. **Disable SMB1** if not needed (already done by using `vers=3.0`)

## Quick Reference

| Scenario | Command |
|----------|---------|
| **Server Setup** | `cd server && ./setup_samba_server.sh` |
| **Client Mount (auto)** | `cd client && ./mount_shared_folder_dynamic.sh <server_ip>` |
| **Test Connection** | `smbclient //<server_ip>/visual-aoi-shared -U jason_nguyen%1` |
| **Unmount** | `sudo umount /mnt/visual-aoi-shared` |
| **Check Status** | `mount \| grep visual-aoi-shared` |
| **Restart Samba** | `sudo systemctl restart smbd nmbd` |

## Integration with Launchers

The launcher scripts (`launch_server.sh` and `launch_client.sh`) now automatically:

1. **Server**: Configure Samba share on first run
2. **Client**: Detect localhost vs remote and setup appropriate mount
3. **Client**: Verify mount matches connected server IP

No manual intervention needed in most cases!
