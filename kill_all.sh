#!/bin/bash
# Visual AOI System - Kill All Processes
# Stops both client and server applications

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}╔════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║   Visual AOI System - Kill All Processes  ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════╝${NC}"
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Kill server first
if [ -f "$SCRIPT_DIR/kill_server.sh" ]; then
    echo -e "${CYAN}═══════════════════════════════════════════${NC}"
    echo -e "${CYAN}  Stopping Server...${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════${NC}"
    bash "$SCRIPT_DIR/kill_server.sh"
    echo ""
else
    echo -e "${YELLOW}⚠  kill_server.sh not found, skipping server shutdown${NC}"
    echo ""
fi

# Kill client
if [ -f "$SCRIPT_DIR/kill_client.sh" ]; then
    echo -e "${CYAN}═══════════════════════════════════════════${NC}"
    echo -e "${CYAN}  Stopping Client...${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════${NC}"
    bash "$SCRIPT_DIR/kill_client.sh"
    echo ""
else
    echo -e "${YELLOW}⚠  kill_client.sh not found, skipping client shutdown${NC}"
    echo ""
fi

echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   All Visual AOI processes stopped         ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
