#!/bin/bash
# Mount shared folder from server via Samba/CIFS
# Server: 10.100.27.156
# Share: \\10.100.27.156\visual-aoi-shared

SERVER_IP="10.100.27.156"
SHARE_NAME="visual-aoi-shared"
MOUNT_POINT="/mnt/visual-aoi-shared"
USERNAME="jason_nguyen"
PASSWORD="1"

echo "╔════════════════════════════════════════════════════╗"
echo "║     Mounting Samba Share from Server               ║"
echo "╚════════════════════════════════════════════════════╝"
echo ""
echo "Server: //$SERVER_IP/$SHARE_NAME"
echo "Mount point: $MOUNT_POINT"
echo "User: $USERNAME"
echo ""

# Check if CIFS utilities are installed
if ! command -v mount.cifs &> /dev/null; then
    echo "❌ CIFS utilities not installed"
    echo "Installing cifs-utils..."
    sudo apt-get update && sudo apt-get install -y cifs-utils
fi

# Create mount point if it doesn't exist
if [ ! -d "$MOUNT_POINT" ]; then
    echo "Creating mount point..."
    sudo mkdir -p "$MOUNT_POINT"
fi

# Unmount if already mounted
if mountpoint -q "$MOUNT_POINT"; then
    echo "⚠️  Already mounted. Unmounting first..."
    sudo umount "$MOUNT_POINT"
    sleep 1
fi

# Backup local files if directory is not empty
if [ "$(ls -A $MOUNT_POINT 2>/dev/null)" ]; then
    echo "⚠️  Local directory not empty. Creating backup..."
    BACKUP_DIR="${MOUNT_POINT}.backup.$(date +%Y%m%d_%H%M%S)"
    sudo mv "$MOUNT_POINT" "$BACKUP_DIR"
    sudo mkdir -p "$MOUNT_POINT"
    echo "✓ Backed up to: $BACKUP_DIR"
fi

# Mount the Samba share
echo ""
echo "Mounting Samba share..."
sudo mount -t cifs \
    "//$SERVER_IP/$SHARE_NAME" \
    "$MOUNT_POINT" \
    -o username="$USERNAME",password="$PASSWORD",uid=$(id -u),gid=$(id -g),file_mode=0755,dir_mode=0755,vers=3.0

# Check if mount succeeded
if mountpoint -q "$MOUNT_POINT"; then
    echo ""
    echo "✅ SUCCESS! Mounted //$SERVER_IP/$SHARE_NAME to $MOUNT_POINT"
    echo ""
    
    # Show mount details
    echo "Mount details:"
    df -h "$MOUNT_POINT"
    echo ""
    
    # Show contents
    echo "Directory contents:"
    ls -la "$MOUNT_POINT"
    echo ""
    
    # Test write access
    TEST_FILE="$MOUNT_POINT/.test_write_$$"
    if touch "$TEST_FILE" 2>/dev/null; then
        rm "$TEST_FILE"
        echo "✓ Write access confirmed"
    else
        echo "⚠️  Warning: No write access"
    fi
    
    # Add to /etc/fstab for automatic mounting on boot
    FSTAB_ENTRY="//$SERVER_IP/$SHARE_NAME $MOUNT_POINT cifs username=$USERNAME,password=$PASSWORD,uid=$(id -u),gid=$(id -g),file_mode=0755,dir_mode=0755,vers=3.0,_netdev 0 0"
    
    if ! grep -q "$SERVER_IP/$SHARE_NAME" /etc/fstab 2>/dev/null; then
        echo ""
        echo "Adding to /etc/fstab for automatic mounting on boot..."
        echo "$FSTAB_ENTRY" | sudo tee -a /etc/fstab > /dev/null
        echo "✓ Added to /etc/fstab"
    else
        echo ""
        echo "✓ Already configured in /etc/fstab"
    fi
    
    echo ""
    echo "╔════════════════════════════════════════════════════╗"
    echo "║              MOUNT SUCCESSFUL!                     ║"
    echo "╚════════════════════════════════════════════════════╝"
    echo ""
    echo "Next steps:"
    echo "  1. Run: ./check_shared_folder.sh (to verify)"
    echo "  2. Start client: python3 ./app.py"
    echo "  3. Test inspection workflow"
    echo ""
    
else
    echo ""
    echo "❌ FAILED to mount Samba share"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Verify server is reachable: ping $SERVER_IP"
    echo "  2. Check if share exists: smbclient -L //$SERVER_IP -U $USERNAME"
    echo "  3. Test credentials: smbclient //$SERVER_IP/$SHARE_NAME -U $USERNAME"
    echo "  4. Check firewall: Server must allow SMB (ports 139, 445)"
    echo ""
    echo "Manual mount command:"
    echo "sudo mount -t cifs //$SERVER_IP/$SHARE_NAME $MOUNT_POINT -o username=$USERNAME,password=$PASSWORD,uid=\$(id -u),gid=\$(id -g)"
    echo ""
    exit 1
fi
