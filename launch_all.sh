#!/bin/bash
# Visual AOI System Launcher for Linux
# Starts both the Visual AOI Server and Client applications.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default values
SERVER_PORT=5000
CLIENT_PORT=5100
DEBUG=false
SEQUENTIAL=false

# Parse command line arguments
show_help() {
    cat << EOF
Visual AOI System Launcher

Usage: $0 [OPTIONS]

Options:
    --server-port PORT      Port for server (default: 5000)
    --client-port PORT      Port for client (default: 5100)
    -d, --debug             Enable debug mode for both applications
    -s, --sequential        Run sequentially in same terminal (default: open separate terminals)
    --help                  Show this help message

Examples:
    $0                      # Start with defaults (separate terminals)
    $0 --debug             # Start with debug mode
    $0 --server-port 5001 --client-port 5101  # Custom ports
    $0 --sequential        # Run in same terminal (foreground)

Note:
    - Separate terminal mode uses gnome-terminal, xterm, or konsole
    - Sequential mode runs server in foreground (Ctrl+C stops both)
EOF
    exit 0
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --server-port)
            SERVER_PORT="$2"
            shift 2
            ;;
        --client-port)
            CLIENT_PORT="$2"
            shift 2
            ;;
        -d|--debug)
            DEBUG=true
            shift
            ;;
        -s|--sequential)
            SEQUENTIAL=true
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
echo "Visual AOI System Launcher"
echo "========================================"
echo -e "${NC}"

# Navigate to script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if launcher scripts exist
SERVER_LAUNCHER="$SCRIPT_DIR/launch_server.sh"
CLIENT_LAUNCHER="$SCRIPT_DIR/launch_client.sh"

if [ ! -f "$SERVER_LAUNCHER" ]; then
    echo -e "${RED}Error: Server launcher not found at $SERVER_LAUNCHER${NC}"
    exit 1
fi

if [ ! -f "$CLIENT_LAUNCHER" ]; then
    echo -e "${RED}Error: Client launcher not found at $CLIENT_LAUNCHER${NC}"
    exit 1
fi

# Make scripts executable
chmod +x "$SERVER_LAUNCHER" "$CLIENT_LAUNCHER"

# Function to check if server is ready
wait_server_ready() {
    local URL=$1
    local MAX_ATTEMPTS=30
    
    echo -e "${YELLOW}Waiting for server to be ready at $URL...${NC}"
    
    for i in $(seq 1 $MAX_ATTEMPTS); do
        if curl -s --connect-timeout 2 "$URL/health" > /dev/null 2>&1; then
            echo -e "\n${GREEN}✓ Server is ready!${NC}"
            return 0
        fi
        echo -n "."
        sleep 1
    done
    
    echo ""
    echo -e "${YELLOW}Warning: Server did not respond within timeout${NC}"
    return 1
}

# Function to find available terminal emulator
find_terminal() {
    if command -v gnome-terminal &> /dev/null; then
        echo "gnome-terminal"
    elif command -v xterm &> /dev/null; then
        echo "xterm"
    elif command -v konsole &> /dev/null; then
        echo "konsole"
    elif command -v xfce4-terminal &> /dev/null; then
        echo "xfce4-terminal"
    else
        echo ""
    fi
}

if [ "$SEQUENTIAL" = true ]; then
    # Run in same terminal (sequential mode)
    echo -e "${CYAN}Starting in Sequential mode...${NC}"
    echo -e "${YELLOW}Note: Server will run in foreground. Press Ctrl+C to stop both.${NC}"
    echo -e "\n${GREEN}Starting Server...${NC}"
    
    # Build server arguments
    SERVER_ARGS="-p $SERVER_PORT"
    if [ "$DEBUG" = true ]; then
        SERVER_ARGS="$SERVER_ARGS -d"
    fi
    
    "$SERVER_LAUNCHER" $SERVER_ARGS
    
else
    # Run in separate terminals (parallel mode)
    echo -e "${CYAN}Starting in Parallel mode (separate terminals)...${NC}"
    
    # Find terminal emulator
    TERMINAL=$(find_terminal)
    if [ -z "$TERMINAL" ]; then
        echo -e "${RED}Error: No terminal emulator found (tried: gnome-terminal, xterm, konsole, xfce4-terminal)${NC}"
        echo -e "${YELLOW}Falling back to sequential mode...${NC}"
        SEQUENTIAL=true
        exec "$0" --sequential --server-port "$SERVER_PORT" --client-port "$CLIENT_PORT" $([ "$DEBUG" = true ] && echo "--debug")
    fi
    
    # Build server arguments
    SERVER_ARGS="-p $SERVER_PORT"
    if [ "$DEBUG" = true ]; then
        SERVER_ARGS="$SERVER_ARGS -d"
    fi
    
    # Start server in new terminal
    echo -e "${GREEN}Launching Server in new terminal...${NC}"
    case "$TERMINAL" in
        gnome-terminal)
            gnome-terminal -- bash -c "cd '$SCRIPT_DIR' && '$SERVER_LAUNCHER' $SERVER_ARGS; exec bash" &
            ;;
        xterm)
            xterm -hold -e "cd '$SCRIPT_DIR' && '$SERVER_LAUNCHER' $SERVER_ARGS" &
            ;;
        konsole)
            konsole --hold -e bash -c "cd '$SCRIPT_DIR' && '$SERVER_LAUNCHER' $SERVER_ARGS" &
            ;;
        xfce4-terminal)
            xfce4-terminal --hold -e "bash -c \"cd '$SCRIPT_DIR' && '$SERVER_LAUNCHER' $SERVER_ARGS\"" &
            ;;
    esac
    SERVER_PID=$!
    echo -e "${GREEN}✓ Server terminal opened (PID: $SERVER_PID)${NC}"
    
    # Wait for server to be ready
    SERVER_URL="http://localhost:$SERVER_PORT"
    wait_server_ready "$SERVER_URL"
    
    # Give server a moment to stabilize
    sleep 2
    
    # Build client arguments
    CLIENT_ARGS="-p $CLIENT_PORT -s $SERVER_URL"
    if [ "$DEBUG" = true ]; then
        CLIENT_ARGS="$CLIENT_ARGS -d"
    fi
    
    # Start client in new terminal
    echo -e "${GREEN}Launching Client in new terminal...${NC}"
    case "$TERMINAL" in
        gnome-terminal)
            gnome-terminal -- bash -c "cd '$SCRIPT_DIR' && '$CLIENT_LAUNCHER' $CLIENT_ARGS; exec bash" &
            ;;
        xterm)
            xterm -hold -e "cd '$SCRIPT_DIR' && '$CLIENT_LAUNCHER' $CLIENT_ARGS" &
            ;;
        konsole)
            konsole --hold -e bash -c "cd '$SCRIPT_DIR' && '$CLIENT_LAUNCHER' $CLIENT_ARGS" &
            ;;
        xfce4-terminal)
            xfce4-terminal --hold -e "bash -c \"cd '$SCRIPT_DIR' && '$CLIENT_LAUNCHER' $CLIENT_ARGS\"" &
            ;;
    esac
    CLIENT_PID=$!
    echo -e "${GREEN}✓ Client terminal opened (PID: $CLIENT_PID)${NC}"
    
    echo -e "\n${GREEN}"
    echo "========================================"
    echo "System Started Successfully!"
    echo "========================================"
    echo -e "${CYAN}Server URL: http://localhost:$SERVER_PORT${NC}"
    echo -e "${CYAN}Server Swagger: http://localhost:$SERVER_PORT/apidocs/${NC}"
    echo -e "${CYAN}Client URL: http://localhost:$CLIENT_PORT${NC}"
    echo -e "\n${YELLOW}Server PID: $SERVER_PID${NC}"
    echo -e "${YELLOW}Client PID: $CLIENT_PID${NC}"
    echo -e "\n${YELLOW}To stop: Close the terminal windows or use 'kill $SERVER_PID $CLIENT_PID'${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    
    echo -e "${CYAN}Terminals are running in background. This script will exit now.${NC}"
fi
