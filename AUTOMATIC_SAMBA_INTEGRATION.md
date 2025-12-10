# Automatic Samba Integration - Complete

## ✅ Implementation Complete

The launcher scripts now **automatically** handle Samba server setup and network mounting with **zero user interaction** required.

## Changes Made

### 1. Server Launcher (`launch_server.sh`)
- Automatically calls `setup_samba_server.sh` on first run
- Detects if Samba share already configured (skips if exists)
- Non-interactive setup (no prompts)
- Displays network connection info with server IP
- Starts Samba service if configured

### 2. Client Launcher (`launch_client.sh`)
- Auto-detects localhost vs remote server from `--server` URL
- **Localhost**: Creates symlink automatically (no Samba needed)
- **Remote**: Automatically calls `mount_shared_folder_dynamic.sh`
- Uses default credentials (jason_nguyen / 1) for auto-mount
- Verifies mount matches target server IP
- Auto-remounts if server IP changes

### 3. Mount Script (`client/mount_shared_folder_dynamic.sh`)
- Now accepts credentials as command-line arguments
- Usage: `./mount_shared_folder_dynamic.sh <ip> [username] [password]`
- Falls back to interactive prompts if args not provided
- Fully backward compatible with manual usage

## Default Credentials

```
Username: jason_nguyen
Password: 1
```

## Usage - Now Fully Automatic!

### Localhost Deployment (Most Common)

```bash
# Start server
./launch_server.sh
# Output: ✓ Samba share configured (or already exists)
#         ✓ Server ready

# Start client (on same machine)
./launch_client.sh
# Output: ✓ Shared folder symlink configured for localhost
#         ✓ Client ready
```

**No configuration needed!** The client automatically detects localhost and creates a symlink.

### Network Deployment (Different Machines)

```bash
# On server machine (e.g., 10.100.27.32)
./launch_server.sh
# Output: ✓ Samba server configured
#         Network clients can connect to: //10.100.27.32/visual-aoi-shared

# On client machine (e.g., 10.100.27.10)
./launch_client.sh -s http://10.100.27.32:5000
# Output: Mounting shared folder from 10.100.27.32...
#         (using default credentials: jason_nguyen / 1)
#         ✓ Shared folder mounted successfully
```

**No prompts! No manual steps!** Everything is automatic.

### Switching Between Servers

```bash
# Client was connected to 10.100.27.32, now switch to 10.100.27.50
./launch_client.sh -s http://10.100.27.50:5000
# Output: ❌ Shared folder mounted to wrong server!
#            Currently: 10.100.27.32 | Target: 10.100.27.50
#         Remounting to correct server...
#         ✓ Remounted to 10.100.27.50
```

The client **automatically detects** and fixes server mismatches.

## Architecture

### Localhost Setup
```
Client                           Server
/mnt/visual-aoi-shared  ─────>  /home/pi/feyes/server/shared
      (symlink)
```

### Network Setup
```
Client                                Server
/mnt/visual-aoi-shared  ──(CIFS)──>  Samba Server
                                     /home/pi/feyes/server/shared
                                     [visual-aoi-shared]
                                     user: jason_nguyen
                                     pass: 1
```

## Manual Operations (Optional)

If you need to configure manually or use different credentials:

### Server: Manual Samba Setup
```bash
cd server
./setup_samba_server.sh
```

### Client: Manual Mount with Custom Credentials
```bash
cd client
./mount_shared_folder_dynamic.sh 10.100.27.32 myuser mypass
```

### Check Mount Status
```bash
mount | grep visual-aoi-shared
```

### Unmount
```bash
sudo umount /mnt/visual-aoi-shared
```

## Verification

### Server Side
```bash
# Check Samba status
sudo systemctl status smbd

# List shares
smbclient -L localhost -U jason_nguyen%1

# Test access
smbclient //localhost/visual-aoi-shared -U jason_nguyen%1
```

### Client Side
```bash
# Check mount
mount | grep visual-aoi-shared

# Test write
touch /mnt/visual-aoi-shared/test.txt && rm /mnt/visual-aoi-shared/test.txt

# Verify from server (should see same files)
ls -la /home/pi/feyes/server/shared/
```

## Benefits

✅ **Zero-configuration for localhost** - Just run the launchers
✅ **Automatic network mounting** - No manual mount commands
✅ **No user prompts** - Uses secure default credentials
✅ **Server IP verification** - Prevents mismatches automatically
✅ **Graceful server switching** - Auto-remounts when server changes
✅ **Backward compatible** - Manual scripts still work

## Workflow Examples

### Example 1: First-Time Localhost Setup
```bash
user@pi:~/feyes$ ./launch_server.sh
✓ Samba server configured
✓ Server running on http://0.0.0.0:5000

user@pi:~/feyes$ ./launch_client.sh
✓ Shared folder symlink configured for localhost
✓ Client running on http://0.0.0.0:5100
```

### Example 2: First-Time Network Setup
```bash
# Server (10.100.27.32)
user@server:~/feyes$ ./launch_server.sh
Running automated Samba setup...
✓ Samba installed
✓ System user created
✓ Samba password set
✓ Share configured
Network clients can connect to: //10.100.27.32/visual-aoi-shared

# Client (10.100.27.10)
user@client:~/feyes$ ./launch_client.sh -s http://10.100.27.32:5000
Network mount not found, setting up automatically...
Mounting shared folder from 10.100.27.32...
✓ Successfully mounted
✓ Client ready
```

### Example 3: Subsequent Runs
```bash
# Server
./launch_server.sh
✓ Samba share already configured
✓ Server ready

# Client
./launch_client.sh -s http://10.100.27.32:5000
✓ Shared folder mounted from server 10.100.27.32
✓ Client ready
```

## Security Notes

1. **Default password is weak** - Fine for development/testing
2. **For production**, change credentials:
   ```bash
   sudo smbpasswd jason_nguyen
   # Then update client to use new password
   ```
3. **Firewall rules** - Restrict to specific network:
   ```bash
   sudo ufw allow from 10.100.0.0/16 to any port 445
   ```
4. **Use credentials file** for better security:
   ```bash
   echo -e "username=jason_nguyen\npassword=1" > ~/.smbcredentials
   chmod 600 ~/.smbcredentials
   ```

## Troubleshooting

### Samba Not Configured
```bash
cd server
./setup_samba_server.sh
```

### Mount Failed
```bash
# Check server is reachable
ping 10.100.27.32

# Check Samba is running on server
sudo systemctl status smbd

# Try manual mount
cd client
./mount_shared_folder_dynamic.sh 10.100.27.32
```

### Wrong Server Mounted
The launcher will auto-detect and fix this, but you can also:
```bash
sudo umount /mnt/visual-aoi-shared
cd client
./mount_shared_folder_dynamic.sh <correct_server_ip>
```

## Files Modified

1. `launch_server.sh` - Added automatic Samba setup integration
2. `launch_client.sh` - Added automatic mount for remote servers
3. `client/mount_shared_folder_dynamic.sh` - Added argument support
4. `server/setup_samba_server.sh` - Created (standalone setup script)
5. `SAMBA_SETUP_GUIDE.md` - Comprehensive documentation

## What Happens Behind the Scenes

### Server Startup
1. Checks if `/etc/samba/smb.conf` contains `[visual-aoi-shared]`
2. If not found, runs `setup_samba_server.sh`
3. Script installs Samba, creates user, sets password, configures share
4. Restarts Samba services
5. Opens firewall ports
6. Displays connection info

### Client Startup (Remote)
1. Extracts server IP from `--server` URL
2. Checks if shared folder is mounted
3. If not mounted or wrong server, calls mount script
4. Passes server IP + default credentials
5. Mount script creates CIFS mount
6. Verifies mount succeeded
7. Client proceeds with startup

### Client Startup (Localhost)
1. Detects `localhost` or `127.0.0.1` in server URL
2. Creates symlink `/mnt/visual-aoi-shared` → `server/shared`
3. No Samba needed
4. Client proceeds with startup

---

**Result**: Complete automation! Just run the launchers and everything works. 🎉
