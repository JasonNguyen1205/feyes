#!/bin/bash
# Visual AOI Client Selector
# Helper script to choose between web and desktop clients

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

clear
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           Visual AOI Client Selector                      ║${NC}"
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo ""
echo -e "${BLUE}Please choose which client to start:${NC}"
echo ""
echo -e "  ${YELLOW}1)${NC} Web Client (Recommended)"
echo -e "     • Modern browser-based interface"
echo -e "     • Access: http://localhost:5100"
echo -e "     • Remote access capable"
echo -e "     • Professional UI"
echo ""
echo -e "  ${YELLOW}2)${NC} Desktop Client (Traditional)"
echo -e "     • Tkinter GUI application"
echo -e "     • Direct hardware access"
echo -e "     • Offline operation"
echo -e "     • Production floor ready"
echo ""
echo -e "  ${YELLOW}3)${NC} Exit"
echo ""
echo -n "Enter your choice [1-3]: "
read choice

case $choice in
    1)
        echo ""
        echo -e "${GREEN}Starting Web Client...${NC}"
        echo ""
        ./start_web_client.sh
        ;;
    2)
        echo ""
        echo -e "${GREEN}Starting Desktop Client...${NC}"
        echo ""
        ./start_client.sh
        ;;
    3)
        echo ""
        echo -e "${GREEN}Exiting...${NC}"
        exit 0
        ;;
    *)
        echo ""
        echo -e "${YELLOW}Invalid choice. Please run again.${NC}"
        exit 1
        ;;
esac
