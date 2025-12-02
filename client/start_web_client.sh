#!/bin/bash
# Visual AOI Web Client Startup Script
# This script starts the web-based client application

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Visual AOI Web Client Startup${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Navigate to project directory
cd "$(dirname "$0")"
PROJECT_DIR=$(pwd)

echo -e "${YELLOW}Project directory:${NC} $PROJECT_DIR"

# Check if port 5100 is in use
PORT=5100
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}Port $PORT is already in use. Attempting to free it...${NC}"
    PIDS=$(lsof -Pi :$PORT -sTCP:LISTEN -t)
    for PID in $PIDS; do
        echo -e "${YELLOW}Killing process $PID on port $PORT${NC}"
        kill -9 $PID 2>/dev/null || true
    done
    sleep 1
    
    # Verify port is free
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${RED}Error: Could not free port $PORT${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Port $PORT is now free${NC}"
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${YELLOW}Python version:${NC} $PYTHON_VERSION"

# Check if virtual environment should be used
if [ -d "venv" ]; then
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source venv/bin/activate
    echo -e "${GREEN}✓ Virtual environment activated${NC}"
fi

# Check if required packages are installed
echo ""
echo -e "${YELLOW}Checking dependencies...${NC}"
python3 -c "import flask" 2>/dev/null || {
    echo -e "${RED}Error: Flask is not installed${NC}"
    echo -e "${YELLOW}Install dependencies with: pip install -r requirements.txt${NC}"
    exit 1
}
echo -e "${GREEN}✓ Flask is installed${NC}"

python3 -c "import cv2" 2>/dev/null || {
    echo -e "${RED}Error: OpenCV is not installed${NC}"
    echo -e "${YELLOW}Install dependencies with: pip install -r requirements.txt${NC}"
    exit 1
}
echo -e "${GREEN}✓ OpenCV is installed${NC}"

# Start the application
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Starting Visual AOI Web Client...${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${GREEN}Server will be available at:${NC}"
echo -e "  ${YELLOW}http://localhost:5100${NC}"
echo -e "  ${YELLOW}http://127.0.0.1:5100${NC}"
echo ""
echo -e "${YELLOW}Press CTRL+C to stop the server${NC}"
echo ""

# Start the Flask app
python3 app.py
