#!/bin/bash
# Visual AOI Server Killer Script
# Kills all running Visual AOI Server processes

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}╔════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║   Visual AOI Server - Kill Processes      ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════╝${NC}"
echo ""

# Function to kill processes by pattern
kill_process() {
    local pattern=$1
    local description=$2
    
    pids=$(pgrep -f "$pattern" 2>/dev/null || true)
    
    if [ -z "$pids" ]; then
        echo -e "${YELLOW}ℹ  No running $description found${NC}"
        return 0
    fi
    
    echo -e "${CYAN}→ Found $description: PIDs $pids${NC}"
    
    # Try graceful shutdown first (SIGTERM)
    kill $pids 2>/dev/null || true
    sleep 2
    
    # Check if still running
    still_running=$(pgrep -f "$pattern" 2>/dev/null || true)
    
    if [ -n "$still_running" ]; then
        echo -e "${YELLOW}⚠  Processes still running, sending SIGKILL...${NC}"
        kill -9 $still_running 2>/dev/null || true
        sleep 1
    fi
    
    # Final check
    final_check=$(pgrep -f "$pattern" 2>/dev/null || true)
    
    if [ -z "$final_check" ]; then
        echo -e "${GREEN}✓ Successfully killed $description${NC}"
        return 0
    else
        echo -e "${RED}✗ Failed to kill $description (PIDs: $final_check)${NC}"
        return 1
    fi
}

# Kill server application (Flask app running on port 5000)
echo -e "${CYAN}[1/2] Stopping Visual AOI Server Flask app...${NC}"
kill_process "server/simple_api_server.py" "Server Flask application"
echo ""

# Kill any stuck Python processes on port 5000
echo -e "${CYAN}[2/2] Checking for processes using port 5000...${NC}"
port_pids=$(lsof -ti:5000 2>/dev/null || true)
if [ -n "$port_pids" ]; then
    echo -e "${CYAN}→ Found processes on port 5000: PIDs $port_pids${NC}"
    kill -9 $port_pids 2>/dev/null || true
    sleep 1
    echo -e "${GREEN}✓ Freed port 5000${NC}"
else
    echo -e "${GREEN}✓ Port 5000 is free${NC}"
fi
echo ""

echo -e "${GREEN}═══════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Visual AOI Server shutdown complete${NC}"
echo -e "${GREEN}═══════════════════════════════════════════${NC}"
