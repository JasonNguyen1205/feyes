#!/bin/bash
# Test Visual AOI launchers for Linux
# Validates that all launcher scripts exist and have correct syntax.

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "\n${GREEN}========================================"
echo "Visual AOI Launcher Validation"
echo "========================================${NC}\n"

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ERRORS=0
WARNINGS=0

# Test files to check
declare -a REQUIRED_FILES=(
    "launch_all.sh:Bash Launcher"
    "launch_server.sh:Bash Launcher"
    "launch_client.sh:Bash Launcher"
    "start.sh:Bash Launcher"
    "LAUNCHER_README.md:Documentation"
    "QUICK_REFERENCE.md:Documentation"
    "LAUNCHER_SETUP_SUMMARY.md:Documentation"
    "LAUNCHER_GUIDE.md:Documentation"
)

# Check file existence
echo -e "${YELLOW}Checking file existence...${NC}"
for file_info in "${REQUIRED_FILES[@]}"; do
    IFS=':' read -r file type <<< "$file_info"
    FILE_PATH="$SCRIPT_DIR/$file"
    if [ -f "$FILE_PATH" ]; then
        SIZE=$(stat -f%z "$FILE_PATH" 2>/dev/null || stat -c%s "$FILE_PATH" 2>/dev/null || echo "unknown")
        echo -e "  ${GREEN}✓${NC} $file ($SIZE bytes) - $type"
    else
        echo -e "  ${RED}✗${NC} $file - MISSING!"
        ((ERRORS++))
    fi
done

# Test Bash syntax
echo -e "\n${YELLOW}Checking Bash script syntax...${NC}"
for file_info in "${REQUIRED_FILES[@]}"; do
    IFS=':' read -r file type <<< "$file_info"
    if [[ "$file" == *.sh ]]; then
        SCRIPT_PATH="$SCRIPT_DIR/$file"
        if [ -f "$SCRIPT_PATH" ]; then
            if bash -n "$SCRIPT_PATH" 2>/dev/null; then
                echo -e "  ${GREEN}✓${NC} $file - Syntax OK"
            else
                echo -e "  ${RED}✗${NC} $file - Syntax Error"
                ((ERRORS++))
            fi
        fi
    fi
done

# Check Python availability
echo -e "\n${YELLOW}Checking Python installation...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1)
    echo -e "  ${GREEN}✓${NC} Python found: $PYTHON_VERSION"
else
    echo -e "  ${YELLOW}⚠${NC} Python3 not found - Launchers require Python 3.8+"
    ((WARNINGS++))
fi

# Check directories
echo -e "\n${YELLOW}Checking project structure...${NC}"
declare -a REQUIRED_DIRS=("server" "client" "server/server" "client/src")
for dir in "${REQUIRED_DIRS[@]}"; do
    DIR_PATH="$SCRIPT_DIR/$dir"
    if [ -d "$DIR_PATH" ]; then
        echo -e "  ${GREEN}✓${NC} $dir/ exists"
    else
        echo -e "  ${YELLOW}⚠${NC} $dir/ not found"
        ((WARNINGS++))
    fi
done

# Check entry points
echo -e "\n${YELLOW}Checking application entry points...${NC}"
declare -a ENTRY_POINTS=("server/server/simple_api_server.py" "client/app.py")
for entry in "${ENTRY_POINTS[@]}"; do
    ENTRY_PATH="$SCRIPT_DIR/$entry"
    if [ -f "$ENTRY_PATH" ]; then
        echo -e "  ${GREEN}✓${NC} $entry exists"
    else
        echo -e "  ${RED}✗${NC} $entry - MISSING!"
        ((ERRORS++))
    fi
done

# Check requirements files
echo -e "\n${YELLOW}Checking requirements files...${NC}"
declare -a REQ_FILES=("server/requirements.txt" "client/requirements.txt")
for req in "${REQ_FILES[@]}"; do
    REQ_PATH="$SCRIPT_DIR/$req"
    if [ -f "$REQ_PATH" ]; then
        LINE_COUNT=$(wc -l < "$REQ_PATH")
        echo -e "  ${GREEN}✓${NC} $req ($LINE_COUNT lines)"
    else
        echo -e "  ${YELLOW}⚠${NC} $req not found"
        ((WARNINGS++))
    fi
done

# Check script permissions
echo -e "\n${YELLOW}Checking script permissions...${NC}"
for file_info in "${REQUIRED_FILES[@]}"; do
    IFS=':' read -r file type <<< "$file_info"
    if [[ "$file" == *.sh ]]; then
        SCRIPT_PATH="$SCRIPT_DIR/$file"
        if [ -f "$SCRIPT_PATH" ]; then
            if [ -x "$SCRIPT_PATH" ]; then
                echo -e "  ${GREEN}✓${NC} $file - Executable"
            else
                echo -e "  ${YELLOW}⚠${NC} $file - Not executable (will be made executable on first run)"
                ((WARNINGS++))
            fi
        fi
    fi
done

# Check terminal emulators (for parallel mode)
echo -e "\n${YELLOW}Checking terminal emulators...${NC}"
FOUND_TERMINAL=false
for term in gnome-terminal xterm konsole xfce4-terminal; do
    if command -v $term &> /dev/null; then
        echo -e "  ${GREEN}✓${NC} $term available"
        FOUND_TERMINAL=true
    fi
done
if [ "$FOUND_TERMINAL" = false ]; then
    echo -e "  ${YELLOW}⚠${NC} No terminal emulator found - Parallel mode will fallback to sequential"
    ((WARNINGS++))
fi

# Summary
echo -e "\n${GREEN}========================================"
echo "Validation Summary"
echo "========================================${NC}"

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo -e "\n${CYAN}Launchers are ready to use!${NC}"
    echo -e "${CYAN}  Quick start: ./start.sh${NC}"
    echo -e "${CYAN}  Advanced:    ./launch_all.sh --debug${NC}"
    echo -e "${CYAN}  Help:        ./launch_all.sh --help${NC}"
    exit 0
else
    if [ $ERRORS -gt 0 ]; then
        echo -e "${RED}✗ $ERRORS error(s) found${NC}"
    fi
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}⚠ $WARNINGS warning(s) found${NC}"
    fi
    
    if [ $ERRORS -gt 0 ]; then
        echo -e "\n${RED}Please fix errors before using launchers.${NC}"
        exit 1
    else
        echo -e "\n${YELLOW}Warnings can be ignored, but may affect functionality.${NC}"
        exit 0
    fi
fi
