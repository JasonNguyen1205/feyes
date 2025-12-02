#!/bin/bash
# Start Visual AOI Server

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}Visual AOI Server Startup${NC}"
echo "==============================="

# Check virtual environment
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv .venv
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source .venv/bin/activate

# Install/Update dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

# Enable PTX JIT compilation for RTX 5080 GPU support
echo -e "${YELLOW}Enabling PTX JIT for RTX 5080 GPU...${NC}"
export CUDA_FORCE_PTX_JIT=1

# Start server
echo -e "${GREEN}Starting server...${NC}"
echo -e "${YELLOW}Server will run on http://0.0.0.0:5000${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
echo "==============================="

python server/simple_api_server.py --host 0.0.0.0 --port 5000 "$@" --debug
