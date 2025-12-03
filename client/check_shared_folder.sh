#!/bin/bash
# Quick diagnostic script to check shared folder status

echo "=================================="
echo "Shared Folder Diagnostic Tool"
echo "=================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if mount point exists
echo "1. Checking mount point..."
if [ -d "/mnt/visual-aoi-shared" ]; then
    echo -e "${GREEN}✓${NC} Mount point exists: /mnt/visual-aoi-shared"
else
    echo -e "${RED}✗${NC} Mount point does not exist!"
    exit 1
fi

# Check if it's mounted
echo ""
echo "2. Checking if folder is mounted..."
if mountpoint -q /mnt/visual-aoi-shared; then
    echo -e "${GREEN}✓${NC} Folder is mounted via NFS"
    
    # Show mount details
    echo ""
    echo "Mount details:"
    mount | grep visual-aoi-shared
    
    echo ""
    df -h /mnt/visual-aoi-shared
else
    echo -e "${YELLOW}⚠${NC} Folder is NOT mounted (using local directory)"
    echo "  This means client and server do NOT share the same folder!"
    echo ""
    echo "To fix this, run: ./mount_shared_folder.sh"
fi

# Check permissions
echo ""
echo "3. Checking permissions..."
ls -ld /mnt/visual-aoi-shared
OWNER=$(stat -c '%U' /mnt/visual-aoi-shared 2>/dev/null)
echo "  Owner: $OWNER"

# Test write access
echo ""
echo "4. Testing write access..."
TEST_FILE="/mnt/visual-aoi-shared/.test_write_$$"
if touch "$TEST_FILE" 2>/dev/null; then
    rm "$TEST_FILE"
    echo -e "${GREEN}✓${NC} Write access OK"
else
    echo -e "${RED}✗${NC} No write access!"
fi

# Check sessions directory
echo ""
echo "5. Checking sessions directory..."
if [ -d "/mnt/visual-aoi-shared/sessions" ]; then
    echo -e "${GREEN}✓${NC} Sessions directory exists"
    
    # Count session folders
    SESSION_COUNT=$(find /mnt/visual-aoi-shared/sessions -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l)
    echo "  Active sessions: $SESSION_COUNT"
    
    if [ $SESSION_COUNT -gt 0 ]; then
        echo ""
        echo "  Recent sessions:"
        ls -lt /mnt/visual-aoi-shared/sessions/ | head -5
    fi
else
    echo -e "${YELLOW}⚠${NC} Sessions directory does not exist"
    echo "  Creating it..."
    mkdir -p /mnt/visual-aoi-shared/sessions
fi

# Check if NFS client is installed
echo ""
echo "6. Checking NFS client installation..."
if dpkg -l | grep -q nfs-common; then
    echo -e "${GREEN}✓${NC} NFS client (nfs-common) is installed"
else
    echo -e "${YELLOW}⚠${NC} NFS client (nfs-common) is NOT installed"
    echo "  To install: sudo apt-get install -y nfs-common"
fi

# Network connectivity to server
echo ""
echo "7. Checking server connectivity..."
SERVER_IP="10.100.27.156"
if ping -c 1 -W 2 $SERVER_IP >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Server $SERVER_IP is reachable"
    
    # Check if NFS port is open
    if command -v nc >/dev/null 2>&1; then
        if nc -z -w 2 $SERVER_IP 2049 2>/dev/null; then
            echo -e "${GREEN}✓${NC} NFS port 2049 is open on server"
        else
            echo -e "${YELLOW}⚠${NC} NFS port 2049 is NOT accessible"
            echo "  Server may not have NFS server running"
        fi
    fi
else
    echo -e "${RED}✗${NC} Server $SERVER_IP is NOT reachable"
fi

# Check /etc/fstab for auto-mount
echo ""
echo "8. Checking auto-mount configuration..."
if grep -q "visual-aoi-shared" /etc/fstab 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Auto-mount configured in /etc/fstab"
    grep "visual-aoi-shared" /etc/fstab
else
    echo -e "${YELLOW}⚠${NC} Not configured for auto-mount on boot"
    echo "  Mount will be lost after reboot"
fi

# Final summary
echo ""
echo "=================================="
echo "Summary"
echo "=================================="

if mountpoint -q /mnt/visual-aoi-shared; then
    echo -e "${GREEN}✓ SHARED FOLDER IS PROPERLY MOUNTED${NC}"
    echo "  Client and server should share the same files"
else
    echo -e "${RED}✗ SHARED FOLDER IS NOT MOUNTED${NC}"
    echo ""
    echo "Action required:"
    echo "  1. Configure NFS server on 10.100.27.156 (see SHARED_FOLDER_SETUP.md)"
    echo "  2. Run: ./mount_shared_folder.sh"
fi

echo ""
