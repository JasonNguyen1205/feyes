#!/bin/bash
# Visual AOI Server Launcher for Linux
# Starts the Visual AOI Server Flask application with GPU support.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default values
PORT=5000
HOST="0.0.0.0"
DEBUG=false
NO_VENV=false

# Parse command line arguments
show_help() {
    cat << EOF
Visual AOI Server Launcher

Usage: $0 [OPTIONS]

Options:
    -p, --port PORT         Port to run server on (default: 5000)
    -h, --host HOST         Host to bind to (default: 0.0.0.0)
    -d, --debug             Enable debug mode
    -n, --no-venv          Skip virtual environment creation/activation
    --help                  Show this help message

Examples:
    $0                      # Start with defaults
    $0 -p 5001 -d          # Custom port with debug
    $0 --no-venv           # Skip virtual environment
EOF
    exit 0
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        -h|--host)
            HOST="$2"
            shift 2
            ;;
        -d|--debug)
            DEBUG=true
            shift
            ;;
        -n|--no-venv)
            NO_VENV=true
            shift
            ;;
        --help)
            show_help
            ;;
        *)
            echo -e "${RED}Error: Unknown option $1${NC}"
            show_help
            ;;
    esac
done

echo -e "${GREEN}"
echo "========================================"
echo "Visual AOI Server Launcher"
echo "========================================"
echo -e "${NC}"

# Navigate to script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SERVER_DIR="$SCRIPT_DIR/server"

if [ ! -d "$SERVER_DIR" ]; then
    echo -e "${RED}Error: Server directory not found at $SERVER_DIR${NC}"
    exit 1
fi

cd "$SERVER_DIR"
echo -e "${YELLOW}Working directory: $SERVER_DIR${NC}"

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python3 not found. Please install Python 3.8 or higher.${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1)
echo -e "${CYAN}Python version: $PYTHON_VERSION${NC}"

# Virtual environment management
if [ "$NO_VENV" = false ]; then
    VENV_PATH="$SERVER_DIR/.venv"
    
    if [ ! -d "$VENV_PATH" ]; then
        echo -e "${YELLOW}Creating virtual environment...${NC}"
        python3 -m venv .venv
        if [ $? -ne 0 ]; then
            echo -e "${RED}Error: Failed to create virtual environment${NC}"
            exit 1
        fi
        echo -e "${GREEN}✓ Virtual environment created${NC}"
    fi
    
    # Activate virtual environment
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source "$VENV_PATH/bin/activate"
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Virtual environment activated${NC}"
    else
        echo -e "${YELLOW}Warning: Could not activate virtual environment${NC}"
    fi
    
    # Install/Update dependencies
    REQUIREMENTS_FILE="$SERVER_DIR/requirements.txt"
    if [ -f "$REQUIREMENTS_FILE" ]; then
        echo -e "${YELLOW}Checking dependencies...${NC}"
        echo -e "${YELLOW}Installing dependencies from requirements.txt...${NC}"
        python3 -m pip install --quiet --upgrade pip
        python3 -m pip install --quiet -r requirements.txt
        echo -e "${GREEN}✓ Dependencies installed${NC}"
    fi
fi

# Enable PTX JIT compilation for RTX 5080 GPU support
echo -e "${YELLOW}Enabling PTX JIT for RTX GPU support...${NC}"
export CUDA_FORCE_PTX_JIT=1
echo -e "${GREEN}✓ GPU settings configured${NC}"

# Configure firewall to allow port
echo -e "${YELLOW}Configuring firewall to allow port $PORT...${NC}"
if command -v ufw &> /dev/null; then
    # Ubuntu/Debian UFW
    sudo ufw allow $PORT/tcp 2>/dev/null && echo -e "${GREEN}✓ UFW: Port $PORT allowed${NC}" || echo -e "${YELLOW}⚠ Could not configure UFW (may need sudo)${NC}"
elif command -v firewall-cmd &> /dev/null; then
    # RedHat/CentOS firewalld
    sudo firewall-cmd --permanent --add-port=$PORT/tcp 2>/dev/null && sudo firewall-cmd --reload 2>/dev/null && echo -e "${GREEN}✓ firewalld: Port $PORT allowed${NC}" || echo -e "${YELLOW}⚠ Could not configure firewalld (may need sudo)${NC}"
elif command -v iptables &> /dev/null; then
    # Generic iptables
    sudo iptables -I INPUT -p tcp --dport $PORT -j ACCEPT 2>/dev/null && echo -e "${GREEN}✓ iptables: Port $PORT allowed${NC}" || echo -e "${YELLOW}⚠ Could not configure iptables (may need sudo)${NC}"
else
    echo -e "${YELLOW}⚠ No supported firewall found (ufw/firewalld/iptables)${NC}"
fi

# Setup shared folder - map /mnt/visual-aoi-shared to server's shared directory
echo -e "${YELLOW}Setting up shared folder mapping...${NC}"
SHARED_FOLDER="$SERVER_DIR/shared"
MOUNT_POINT="/mnt/visual-aoi-shared"

# Ensure server's shared folder exists
if [ ! -d "$SHARED_FOLDER" ]; then
    mkdir -p "$SHARED_FOLDER/sessions"
    echo -e "${GREEN}✓ Created server shared folder at $SHARED_FOLDER${NC}"
fi

# Map /mnt/visual-aoi-shared to server's shared folder
if [ -L "$MOUNT_POINT" ]; then
    # Symlink exists - verify it points to correct location
    CURRENT_TARGET=$(readlink "$MOUNT_POINT")
    if [ "$CURRENT_TARGET" != "$SHARED_FOLDER" ]; then
        echo -e "${YELLOW}Updating symlink to point to $SHARED_FOLDER${NC}"
        echo "1" | sudo -S rm "$MOUNT_POINT"
        echo "1" | sudo -S ln -s "$SHARED_FOLDER" "$MOUNT_POINT"
        echo -e "${GREEN}✓ Symlink updated${NC}"
    else
        echo -e "${GREEN}✓ Shared folder symlink already configured${NC}"
    fi
elif [ -d "$MOUNT_POINT" ]; then
    # Directory exists - check if it's empty and safe to replace
    if [ -z "$(ls -A $MOUNT_POINT)" ]; then
        echo -e "${YELLOW}Replacing empty directory with symlink${NC}"
        echo "1" | sudo -S rmdir "$MOUNT_POINT"
        echo "1" | sudo -S ln -s "$SHARED_FOLDER" "$MOUNT_POINT"
        echo -e "${GREEN}✓ Created symlink: $MOUNT_POINT → $SHARED_FOLDER${NC}"
    else
        echo -e "${YELLOW}⚠ $MOUNT_POINT is not empty, keeping as-is${NC}"
        echo -e "${YELLOW}  Manual action: sudo rm -rf $MOUNT_POINT && sudo ln -s $SHARED_FOLDER $MOUNT_POINT${NC}"
    fi
else
    # Doesn't exist - create symlink
    echo -e "${YELLOW}Creating shared folder symlink...${NC}"
    echo "1" | sudo -S ln -s "$SHARED_FOLDER" "$MOUNT_POINT"
    echo -e "${GREEN}✓ Created symlink: $MOUNT_POINT → $SHARED_FOLDER${NC}"
fi

# Ensure proper permissions
echo "1" | sudo -S chown -R $(whoami):$(whoami) "$SHARED_FOLDER" 2>/dev/null
echo "1" | sudo -S chmod -R 775 "$SHARED_FOLDER" 2>/dev/null
echo -e "${GREEN}✓ Shared folder permissions configured${NC}"

# Ensure shared folder has proper permissions for client access
if [ -d "$SHARED_FOLDER" ]; then
    chmod 755 "$SHARED_FOLDER"
    echo -e "${GREEN}✓ Shared folder permissions configured${NC}"
fi

# Check server script exists
SERVER_SCRIPT="$SERVER_DIR/server/simple_api_server.py"
if [ ! -f "$SERVER_SCRIPT" ]; then
    echo -e "${RED}Error: Server script not found at $SERVER_SCRIPT${NC}"
    exit 1
fi

echo -e "${GREEN}"
echo "========================================"
echo "Starting Visual AOI Server..."
echo "========================================"
echo -e "${CYAN}Server URL: http://${HOST}:${PORT}${NC}"
echo -e "${CYAN}Swagger UI: http://${HOST}:${PORT}/apidocs/${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Build arguments
ARGS="--host $HOST --port $PORT"
if [ "$DEBUG" = true ]; then
    ARGS="$ARGS --debug"
fi

# Start server
trap 'echo -e "\n${YELLOW}Shutting down...${NC}"; exit 0' INT TERM
python3 "$SERVER_SCRIPT" $ARGS
