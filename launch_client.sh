#!/bin/bash
# Visual AOI Client Launcher for Linux
# Starts the Visual AOI Client Flask web application.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default values
PORT=5100
HOST="0.0.0.0"
SERVER_URL="http://localhost:5000"
DEBUG=false
NO_VENV=false
CHECK_CAMERA=false

# Parse command line arguments
show_help() {
    cat << EOF
Visual AOI Client Launcher

Usage: $0 [OPTIONS]

Options:
    -p, --port PORT         Port to run client on (default: 5100)
    -h, --host HOST         Host to bind to (default: 0.0.0.0)
    -s, --server URL        Server API URL (default: http://localhost:5000)
    -d, --debug             Enable debug mode
    -n, --no-venv          Skip virtual environment creation/activation
    -c, --check-camera     Check TIS camera availability before starting
    --help                  Show this help message

Examples:
    $0                      # Start with defaults
    $0 -p 5101 -d          # Custom port with debug
    $0 -s http://192.168.1.100:5000  # Connect to remote server
    $0 --check-camera      # Check camera before starting
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
        -s|--server)
            SERVER_URL="$2"
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
        -c|--check-camera)
            CHECK_CAMERA=true
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
echo "Visual AOI Client Launcher"
echo "========================================"
echo -e "${NC}"

# Navigate to script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CLIENT_DIR="$SCRIPT_DIR/client"

if [ ! -d "$CLIENT_DIR" ]; then
    echo -e "${RED}Error: Client directory not found at $CLIENT_DIR${NC}"
    exit 1
fi

cd "$CLIENT_DIR"
echo -e "${YELLOW}Working directory: $CLIENT_DIR${NC}"

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python3 not found. Please install Python 3.8 or higher.${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1)
echo -e "${CYAN}Python version: $PYTHON_VERSION${NC}"

# Check if port is in use
echo -e "${YELLOW}Checking port $PORT availability...${NC}"
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}Warning: Port $PORT is in use. Attempting to free it...${NC}"
    PIDS=$(lsof -Pi :$PORT -sTCP:LISTEN -t)
    for PID in $PIDS; do
        echo -e "${YELLOW}Stopping process $PID on port $PORT${NC}"
        kill -9 $PID 2>/dev/null || true
    done
    sleep 1
    
    # Verify port is free
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${RED}Error: Could not free port $PORT${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Port $PORT is now free${NC}"
else
    echo -e "${GREEN}✓ Port $PORT is available${NC}"
fi

# Virtual environment management
if [ "$NO_VENV" = false ]; then
    VENV_PATH="$CLIENT_DIR/.venv"
    
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
    REQUIREMENTS_FILE="$CLIENT_DIR/requirements.txt"
    if [ -f "$REQUIREMENTS_FILE" ]; then
        echo -e "${YELLOW}Checking dependencies...${NC}"
        echo -e "${YELLOW}Installing dependencies from requirements.txt...${NC}"
        python3 -m pip install --quiet --upgrade pip
        python3 -m pip install --quiet -r requirements.txt
        echo -e "${GREEN}✓ Dependencies installed${NC}"
    fi
fi

# Check server connectivity
echo -e "${YELLOW}Checking server connectivity at $SERVER_URL...${NC}"
if curl -s --connect-timeout 5 "$SERVER_URL/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Server is reachable${NC}"
else
    echo -e "${YELLOW}Warning: Server not reachable at $SERVER_URL${NC}"
    echo -e "${YELLOW}Make sure to start the server first using ./launch_server.sh${NC}"
fi

# Check TIS camera (if requested)
if [ "$CHECK_CAMERA" = true ]; then
    echo -e "${YELLOW}Checking TIS camera availability...${NC}"
    CAMERA_CHECK=$(python3 -c "try:
    import TIS
    print('available')
except:
    print('not_available')" 2>&1)
    if [[ "$CAMERA_CHECK" == *"available"* ]]; then
        echo -e "${GREEN}✓ TIS camera library available${NC}"
    else
        echo -e "${YELLOW}Warning: TIS camera library not available${NC}"
        echo -e "${YELLOW}Camera features will be disabled${NC}"
    fi
fi

# Check for shared folder mount
SHARED_FOLDER="/mnt/visual-aoi-shared"
if [ -d "$SHARED_FOLDER" ]; then
    echo -e "${GREEN}✓ Shared folder available at $SHARED_FOLDER${NC}"
else
    echo -e "${YELLOW}Warning: Shared folder not found at $SHARED_FOLDER${NC}"
    echo -e "${YELLOW}Image transfer may use Base64 encoding (slower)${NC}"
    echo -e "${YELLOW}Run ./setup_shared_folder.sh to configure CIFS mount${NC}"
fi

# Check client script exists
CLIENT_SCRIPT="$CLIENT_DIR/app.py"
if [ ! -f "$CLIENT_SCRIPT" ]; then
    echo -e "${RED}Error: Client script not found at $CLIENT_SCRIPT${NC}"
    exit 1
fi

echo -e "${GREEN}"
echo "========================================"
echo "Starting Visual AOI Client..."
echo "========================================"
echo -e "${CYAN}Client URL: http://${HOST}:${PORT}${NC}"
echo -e "${CYAN}Server URL: $SERVER_URL${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Set environment variables
export SERVER_URL="$SERVER_URL"
export FLASK_APP="app.py"
if [ "$DEBUG" = true ]; then
    export FLASK_DEBUG=1
fi

# Start client
trap 'echo -e "\n${YELLOW}Shutting down...${NC}"; exit 0' INT TERM
python3 "$CLIENT_SCRIPT"
