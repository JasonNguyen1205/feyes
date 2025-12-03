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

# Check for shared folder
SHARED_FOLDER="$SERVER_DIR/shared"
if [ ! -d "$SHARED_FOLDER" ]; then
    echo -e "${YELLOW}Creating shared folder...${NC}"
    mkdir -p "$SHARED_FOLDER"
    echo -e "${GREEN}✓ Shared folder created at $SHARED_FOLDER${NC}"
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
