#!/bin/bash
# Visual AOI Client - NFS Mount Setup Script
# This script configures a client machine to mount the Visual AOI Server NFS shares

set -e

# Configuration
NFS_SERVER="10.100.27.156"
SHARED_EXPORT="/home/jason_nguyen/visual-aoi-server/shared"
GOLDEN_EXPORT="/home/jason_nguyen/visual-aoi-server/config/products"
MOUNT_BASE="/mnt/visual-aoi-shared"
MOUNT_GOLDEN="${MOUNT_BASE}/golden"

echo "========================================"
echo "Visual AOI Client NFS Setup"
echo "========================================"
echo "Server: ${NFS_SERVER}"
echo "Mount Point: ${MOUNT_BASE}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ This script must be run as root (use sudo)"
    exit 1
fi

# Step 1: Check connectivity
echo "1. Checking connectivity to NFS server..."
if ping -c 1 -W 2 ${NFS_SERVER} > /dev/null 2>&1; then
    echo "   ✓ Server ${NFS_SERVER} is reachable"
else
    echo "   ❌ Cannot reach server ${NFS_SERVER}"
    echo "   Please check network connectivity"
    exit 1
fi

# Step 2: Install NFS client
echo ""
echo "2. Installing NFS client packages..."
if dpkg -l | grep -q nfs-common; then
    echo "   ✓ nfs-common already installed"
else
    echo "   Installing nfs-common..."
    apt-get update > /dev/null 2>&1
    apt-get install -y nfs-common
    echo "   ✓ nfs-common installed"
fi

# Step 3: Check available exports
echo ""
echo "3. Checking available NFS exports..."
if showmount -e ${NFS_SERVER} > /dev/null 2>&1; then
    showmount -e ${NFS_SERVER}
    echo "   ✓ NFS exports available"
else
    echo "   ❌ Cannot access NFS exports on ${NFS_SERVER}"
    echo "   Please verify NFS server is running"
    exit 1
fi

# Step 4: Create mount points
echo ""
echo "4. Creating mount points..."
mkdir -p ${MOUNT_BASE}
mkdir -p ${MOUNT_GOLDEN}
echo "   ✓ Created ${MOUNT_BASE}"
echo "   ✓ Created ${MOUNT_GOLDEN}"

# Step 5: Unmount if already mounted (cleanup)
echo ""
echo "5. Checking existing mounts..."
if mount | grep -q "${MOUNT_BASE}"; then
    echo "   Unmounting existing mount at ${MOUNT_BASE}..."
    umount -f ${MOUNT_BASE} 2>/dev/null || true
fi
if mount | grep -q "${MOUNT_GOLDEN}"; then
    echo "   Unmounting existing mount at ${MOUNT_GOLDEN}..."
    umount -f ${MOUNT_GOLDEN} 2>/dev/null || true
fi

# Step 6: Mount NFS shares
echo ""
echo "6. Mounting NFS shares..."
if mount -t nfs ${NFS_SERVER}:${SHARED_EXPORT} ${MOUNT_BASE}; then
    echo "   ✓ Mounted ${SHARED_EXPORT} to ${MOUNT_BASE}"
else
    echo "   ❌ Failed to mount shared directory"
    exit 1
fi

if mount -t nfs ${NFS_SERVER}:${GOLDEN_EXPORT} ${MOUNT_GOLDEN}; then
    echo "   ✓ Mounted ${GOLDEN_EXPORT} to ${MOUNT_GOLDEN}"
else
    echo "   ❌ Failed to mount golden directory"
    exit 1
fi

# Step 7: Verify mounts
echo ""
echo "7. Verifying mounts..."
df -h | grep visual-aoi
echo ""

# Step 8: Test write access
echo "8. Testing write access..."
TEST_FILE="${MOUNT_BASE}/test_write_$(date +%s).txt"
if echo "Test write access" > ${TEST_FILE} 2>/dev/null; then
    rm ${TEST_FILE}
    echo "   ✓ Write access confirmed"
else
    echo "   ⚠ Write access failed (may be read-only)"
fi

# Step 9: Configure auto-mount on boot
echo ""
echo "9. Configuring auto-mount on boot..."

# Backup fstab
cp /etc/fstab /etc/fstab.backup.$(date +%Y%m%d_%H%M%S)
echo "   ✓ Backed up /etc/fstab"

# Check if entries already exist
if grep -q "visual-aoi" /etc/fstab; then
    echo "   ⚠ Visual AOI entries already exist in /etc/fstab"
    echo "   Skipping fstab modification (manual edit required if changes needed)"
else
    # Add entries to fstab
    cat >> /etc/fstab << EOF

# Visual AOI Server NFS Shares (added by setup script on $(date))
${NFS_SERVER}:${SHARED_EXPORT} ${MOUNT_BASE} nfs defaults,_netdev 0 0
${NFS_SERVER}:${GOLDEN_EXPORT} ${MOUNT_GOLDEN} nfs defaults,_netdev 0 0
EOF
    echo "   ✓ Added auto-mount entries to /etc/fstab"
fi

# Step 10: List mounted contents
echo ""
echo "10. Listing shared contents..."
echo ""
echo "Sessions directory:"
ls -la ${MOUNT_BASE}/sessions 2>/dev/null | head -5 || echo "   (empty or not accessible)"
echo ""
echo "Golden samples directory:"
ls -la ${MOUNT_GOLDEN} 2>/dev/null | head -5 || echo "   (empty or not accessible)"

# Summary
echo ""
echo "========================================"
echo "✅ Setup Complete!"
echo "========================================"
echo ""
echo "NFS Shares Mounted:"
echo "  • ${MOUNT_BASE} → ${NFS_SERVER}:${SHARED_EXPORT}"
echo "  • ${MOUNT_GOLDEN} → ${NFS_SERVER}:${GOLDEN_EXPORT}"
echo ""
echo "Auto-mount configured: Yes (will mount on boot)"
echo ""
echo "Next Steps:"
echo "  1. Test accessing files in ${MOUNT_BASE}"
echo "  2. Update your application to use these paths"
echo "  3. Reboot to verify auto-mount works"
echo ""
echo "To manually unmount:"
echo "  sudo umount ${MOUNT_BASE}"
echo "  sudo umount ${MOUNT_GOLDEN}"
echo ""
echo "To manually mount (after reboot):"
echo "  sudo mount -a"
echo ""
