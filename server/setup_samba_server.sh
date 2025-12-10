#!/bin/bash
# Setup Samba server for Visual AOI shared folder
# This script configures Samba to share the server/shared directory
# with username: jason_nguyen, password: 1

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${GREEN}"
echo "========================================"
echo "Visual AOI - Samba Server Setup"
echo "========================================"
echo -e "${NC}"

# Get script directory and shared folder path
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SHARED_FOLDER="$SCRIPT_DIR/shared"

# Resolve absolute path (handles symlinks)
SHARED_FOLDER_ABS="$(cd "$SCRIPT_DIR" && pwd)/shared"

echo -e "${CYAN}Detected paths:${NC}"
echo -e "  Script directory: $SCRIPT_DIR"
echo -e "  Shared folder: $SHARED_FOLDER_ABS"

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    echo -e "${YELLOW}Warning: Running as root. This is not recommended.${NC}"
fi

# Install Samba if not present
if ! command -v smbd &> /dev/null; then
    echo -e "${YELLOW}Samba not found. Installing...${NC}"
    sudo apt-get update
    sudo apt-get install -y samba samba-common-bin
    echo -e "${GREEN}✓ Samba installed${NC}"
else
    echo -e "${GREEN}✓ Samba already installed${NC}"
fi

# Ensure shared folder exists with proper permissions
if [ ! -d "$SHARED_FOLDER" ]; then
    echo -e "${YELLOW}Creating shared folder...${NC}"
    mkdir -p "$SHARED_FOLDER"
fi
chmod 755 "$SHARED_FOLDER"
echo -e "${GREEN}✓ Shared folder ready: $SHARED_FOLDER${NC}"

# Backup original smb.conf if not already backed up
if [ ! -f /etc/samba/smb.conf.backup ]; then
    echo -e "${YELLOW}Backing up original Samba configuration...${NC}"
    sudo cp /etc/samba/smb.conf /etc/samba/smb.conf.backup
    echo -e "${GREEN}✓ Backup created: /etc/samba/smb.conf.backup${NC}"
fi

# Check if share already exists and verify path
if grep -q "\[visual-aoi-shared\]" /etc/samba/smb.conf; then
    echo -e "${YELLOW}visual-aoi-shared share already exists in configuration${NC}"
    
    # Extract current path from smb.conf
    CURRENT_PATH=$(grep -A 10 '\[visual-aoi-shared\]' /etc/samba/smb.conf | grep 'path =' | head -1 | sed 's/.*path = //' | xargs)
    
    if [ "$CURRENT_PATH" != "$SHARED_FOLDER_ABS" ]; then
        echo -e "${RED}⚠ Path mismatch detected!${NC}"
        echo -e "  Current: $CURRENT_PATH"
        echo -e "  Should be: $SHARED_FOLDER_ABS"
        echo -e "${YELLOW}Updating Samba configuration path...${NC}"
        
        # Escape paths for sed
        ESCAPED_OLD=$(echo "$CURRENT_PATH" | sed 's/[]\\/\$*.^[]/\\&/g')
        ESCAPED_NEW=$(echo "$SHARED_FOLDER_ABS" | sed 's/[]\\/\$*.^[]/\\&/g')
        
        # Update the path
        sudo sed -i "s|path = $ESCAPED_OLD|path = $ESCAPED_NEW|" /etc/samba/smb.conf
        echo -e "${GREEN}✓ Path updated successfully${NC}"
        
        # Restart Samba
        echo -e "${YELLOW}Restarting Samba service...${NC}"
        sudo systemctl restart smbd
        echo -e "${GREEN}✓ Samba restarted${NC}"
    else
        echo -e "${GREEN}✓ Path is correct: $CURRENT_PATH${NC}"
    fi
else
    echo -e "${YELLOW}Adding visual-aoi-shared share to Samba configuration...${NC}"
    sudo tee -a /etc/samba/smb.conf > /dev/null << EOF

[visual-aoi-shared]
   comment = Visual AOI Shared Folder
   path = $SHARED_FOLDER_ABS
   browseable = yes
   read only = no
   guest ok = no
   valid users = jason_nguyen
   create mask = 0755
   directory mask = 0755
   force user = $(whoami)
   force group = $(id -gn)
EOF
    echo -e "${GREEN}✓ Share configuration added${NC}"
fi

# Create jason_nguyen system user if doesn't exist
if ! id "jason_nguyen" &>/dev/null; then
    echo -e "${YELLOW}Creating system user jason_nguyen...${NC}"
    sudo useradd -M -s /usr/sbin/nologin jason_nguyen
    echo -e "${GREEN}✓ System user created${NC}"
else
    echo -e "${GREEN}✓ System user jason_nguyen already exists${NC}"
fi

# Set Samba password for jason_nguyen (password: 1)
echo -e "${YELLOW}Setting Samba password for jason_nguyen (password: 1)...${NC}"
(echo "1"; echo "1") | sudo smbpasswd -a jason_nguyen
if [ $? -eq 0 ]; then
    sudo smbpasswd -e jason_nguyen
    echo -e "${GREEN}✓ Samba password set successfully${NC}"
else
    echo -e "${RED}❌ Failed to set Samba password${NC}"
    exit 1
fi

# Test Samba configuration
echo -e "${YELLOW}Testing Samba configuration...${NC}"
if sudo testparm -s &>/dev/null; then
    echo -e "${GREEN}✓ Samba configuration is valid${NC}"
else
    echo -e "${RED}❌ Samba configuration has errors${NC}"
    sudo testparm -s
    exit 1
fi

# Configure firewall to allow Samba (ports 139, 445)
echo -e "${YELLOW}Configuring firewall for Samba...${NC}"
if command -v ufw &> /dev/null; then
    sudo ufw allow 139/tcp 2>/dev/null
    sudo ufw allow 445/tcp 2>/dev/null
    echo -e "${GREEN}✓ UFW: Samba ports allowed${NC}"
elif command -v firewall-cmd &> /dev/null; then
    sudo firewall-cmd --permanent --add-service=samba 2>/dev/null
    sudo firewall-cmd --reload 2>/dev/null
    echo -e "${GREEN}✓ firewalld: Samba service allowed${NC}"
elif command -v iptables &> /dev/null; then
    sudo iptables -I INPUT -p tcp --dport 139 -j ACCEPT 2>/dev/null
    sudo iptables -I INPUT -p tcp --dport 445 -j ACCEPT 2>/dev/null
    echo -e "${GREEN}✓ iptables: Samba ports allowed${NC}"
else
    echo -e "${YELLOW}⚠ No firewall detected${NC}"
fi

# Restart Samba services
echo -e "${YELLOW}Restarting Samba services...${NC}"
if sudo systemctl restart smbd nmbd 2>/dev/null; then
    echo -e "${GREEN}✓ Samba services restarted (systemd)${NC}"
elif sudo service smbd restart && sudo service nmbd restart 2>/dev/null; then
    echo -e "${GREEN}✓ Samba services restarted (sysvinit)${NC}"
else
    echo -e "${RED}❌ Failed to restart Samba services${NC}"
    exit 1
fi

# Enable Samba to start on boot
sudo systemctl enable smbd nmbd 2>/dev/null || sudo update-rc.d smbd enable 2>/dev/null || true

echo ""
echo -e "${GREEN}========================================"
echo "✅ Samba Server Setup Complete!"
echo "========================================${NC}"
echo ""
echo -e "${CYAN}Share Information:${NC}"
echo -e "  Share Name: ${YELLOW}visual-aoi-shared${NC}"
echo -e "  Path: ${YELLOW}$SHARED_FOLDER${NC}"
echo -e "  Username: ${YELLOW}jason_nguyen${NC}"
echo -e "  Password: ${YELLOW}1${NC}"
echo ""
echo -e "${CYAN}Client Connection:${NC}"
SERVER_IP=$(hostname -I | awk '{print $1}')
echo -e "  From client: ${YELLOW}cd client && ./mount_shared_folder_dynamic.sh $SERVER_IP${NC}"
echo ""
echo -e "${CYAN}Test Connection:${NC}"
echo -e "  ${YELLOW}smbclient //$SERVER_IP/visual-aoi-shared -U jason_nguyen%1${NC}"
echo ""
