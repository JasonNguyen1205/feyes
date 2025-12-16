#!/bin/bash
# Dynamic shared folder mount script
# Mounts /mnt/visual-aoi-shared from the server the client is connected to
#
# Usage:
#   ./mount_shared_folder_dynamic.sh <server_ip>
#   OR
#   ./mount_shared_folder_dynamic.sh (will prompt for IP)

set -e

MOUNT_POINT="/mnt/visual-aoi-shared"
SHARE_NAME="visual-aoi-shared"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse arguments
SERVER_IP="$1"

# If no IP provided, prompt user
if [ -z "$SERVER_IP" ]; then
    echo -e "${YELLOW}Enter the server IP address (e.g., 10.100.27.32):${NC}"
    read -r SERVER_IP
fi

# Validate IP format
if ! [[ $SERVER_IP =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo -e "${RED}❌ Invalid IP address format: $SERVER_IP${NC}"
    exit 1
fi

echo -e "${GREEN}Setting up CIFS mount from server $SERVER_IP...${NC}"

# Install CIFS utilities if not present
if ! dpkg -l | grep -q cifs-utils; then
    echo "Installing CIFS utilities..."
    sudo apt-get update
    sudo apt-get install -y cifs-utils
fi

# Create mount point
sudo mkdir -p "$MOUNT_POINT"

# Unmount if already mounted
if mountpoint -q "$MOUNT_POINT"; then
    echo -e "${YELLOW}Unmounting existing mount...${NC}"
    sudo umount "$MOUNT_POINT" || {
        echo -e "${RED}Failed to unmount. Trying force unmount...${NC}"
        sudo umount -f "$MOUNT_POINT" || sudo umount -l "$MOUNT_POINT"
    }
fi

# Prompt for credentials
echo -e "${YELLOW}Enter server username (default: jason_nguyen):${NC}"
read -r USERNAME
USERNAME=${USERNAME:-jason_nguyen}

echo -e "${YELLOW}Enter server password:${NC}"
read -rs PASSWORD
PASSWORD=${PASSWORD:-1}

# Mount the CIFS share
echo -e "${GREEN}Mounting CIFS share...${NC}"
sudo mount -t cifs "//$SERVER_IP/$SHARE_NAME" "$MOUNT_POINT" \
    -o "username=$USERNAME,password=$PASSWORD,uid=$(id -u),gid=$(id -g),file_mode=0755,dir_mode=0755,vers=3.0,_netdev"

# Check if mount succeeded
if mountpoint -q "$MOUNT_POINT"; then
    echo -e "${GREEN}✅ Successfully mounted //$SERVER_IP/$SHARE_NAME to $MOUNT_POINT${NC}"
    
    # Update /etc/fstab entry
    FSTAB_LINE="//$SERVER_IP/$SHARE_NAME $MOUNT_POINT cifs username=$USERNAME,password=$PASSWORD,uid=$(id -u),gid=$(id -g),file_mode=0755,dir_mode=0755,vers=3.0,_netdev 0 0"
    
    # Remove old fstab entries for visual-aoi-shared
    if grep -q "visual-aoi-shared" /etc/fstab; then
        echo -e "${YELLOW}Removing old fstab entry...${NC}"
        sudo sed -i '/visual-aoi-shared/d' /etc/fstab
    fi
    
    # Add new fstab entry
    echo -e "${GREEN}Adding to /etc/fstab for automatic mounting on boot...${NC}"
    echo "$FSTAB_LINE" | sudo tee -a /etc/fstab > /dev/null
    echo -e "${GREEN}✅ Added to /etc/fstab${NC}"
    
    # Show mount info
    echo ""
    echo -e "${GREEN}Mount details:${NC}"
    df -h "$MOUNT_POINT"
    echo ""
    echo -e "${GREEN}Contents:${NC}"
    ls -la "$MOUNT_POINT" 2>/dev/null || echo "(empty or permissions issue)"
else
    echo -e "${RED}❌ Failed to mount CIFS share${NC}"
    echo "Please check:"
    echo "  1. Server $SERVER_IP is reachable (ping $SERVER_IP)"
    echo "  2. Server has Samba configured with share name '$SHARE_NAME'"
    echo "  3. Server firewall allows SMB (port 445)"
    echo "  4. Credentials are correct"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ Shared folder setup complete!${NC}"
echo -e "${GREEN}Client can now save/read files via $MOUNT_POINT${NC}"
echo -e "${GREEN}Server will access files at /home/jason_nguyen/visual-aoi-server/shared/${NC}"
