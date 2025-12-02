#!/bin/bash
# Mount shared folder from server via NFS
# This script mounts /mnt/visual-aoi-shared from the server

SERVER_IP="10.100.27.156"
MOUNT_POINT="/mnt/visual-aoi-shared"
SERVER_PATH="/mnt/visual-aoi-shared"

echo "Setting up NFS mount from server $SERVER_IP..."

# Install NFS client if not present
if ! dpkg -l | grep -q nfs-common; then
    echo "Installing NFS client..."
    sudo apt-get update
    sudo apt-get install -y nfs-common
fi

# Create mount point
sudo mkdir -p "$MOUNT_POINT"

# Unmount if already mounted
if mountpoint -q "$MOUNT_POINT"; then
    echo "Unmounting existing mount..."
    sudo umount "$MOUNT_POINT"
fi

# Remove any files in local directory (backup first if needed)
if [ "$(ls -A $MOUNT_POINT 2>/dev/null)" ]; then
    echo "⚠️  Warning: Local directory not empty. Moving to backup..."
    sudo mv "$MOUNT_POINT" "${MOUNT_POINT}.backup.$(date +%Y%m%d_%H%M%S)"
    sudo mkdir -p "$MOUNT_POINT"
fi

# Mount the NFS share
echo "Mounting NFS share..."
sudo mount -t nfs -o vers=4,rw,sync "$SERVER_IP:$SERVER_PATH" "$MOUNT_POINT"

# Check if mount succeeded
if mountpoint -q "$MOUNT_POINT"; then
    echo "✅ Successfully mounted $SERVER_IP:$SERVER_PATH to $MOUNT_POINT"
    
    # Add to /etc/fstab for automatic mounting on boot
    if ! grep -q "$SERVER_IP:$SERVER_PATH" /etc/fstab; then
        echo "Adding to /etc/fstab for automatic mounting on boot..."
        echo "$SERVER_IP:$SERVER_PATH $MOUNT_POINT nfs vers=4,rw,sync,_netdev 0 0" | sudo tee -a /etc/fstab
        echo "✅ Added to /etc/fstab"
    fi
    
    # Show mount info
    echo ""
    echo "Mount details:"
    df -h "$MOUNT_POINT"
    echo ""
    ls -la "$MOUNT_POINT"
else
    echo "❌ Failed to mount NFS share"
    echo "Please check:"
    echo "  1. Server $SERVER_IP is running NFS server"
    echo "  2. Server has exported $SERVER_PATH"
    echo "  3. Server firewall allows NFS (port 2049)"
    exit 1
fi
