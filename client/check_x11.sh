#!/bin/bash
# X11 Forwarding Diagnostic Tool

echo "=== X11 Forwarding Diagnostics ==="
echo ""

# Check SSH mode
if [ -n "$SSH_CLIENT" ] || [ -n "$SSH_TTY" ]; then
    echo "✓ SSH connection detected"
    echo "  From: $(echo $SSH_CLIENT | awk '{print $1":"$2}')"
    echo "  To: $(echo $SSH_CLIENT | awk '{print $3":"$4}')"
else
    echo "○ Local connection (not SSH)"
fi
echo ""

# Check DISPLAY
echo "Current DISPLAY: ${DISPLAY:-not set}"
echo ""

# Check X11 forwarding ports
echo "X11 Forwarding Ports:"
PORTS=$(netstat -an 2>/dev/null | grep '127.0.0.1:60[0-9][0-9]' | grep LISTEN)
if [ -n "$PORTS" ]; then
    echo "$PORTS" | while read line; do
        PORT=$(echo $line | awk '{print $4}' | cut -d':' -f2)
        DISP=$((PORT - 6000))
        STATUS="  "
        if [ "$DISPLAY" = "localhost:${DISP}.0" ]; then
            STATUS="→ "
        fi
        echo "${STATUS}Port $PORT = DISPLAY localhost:${DISP}.0"
    done
else
    echo "  ✗ No X11 forwarding ports found"
fi
echo ""

# Check X11 auth
echo "X11 Authentication:"
if xauth list 2>/dev/null | grep -q .; then
    echo "  ✓ X11 auth cookies exist:"
    xauth list | while read line; do
        echo "    $line"
    done
else
    echo "  ✗ No X11 auth cookies"
fi
echo ""

# Test X11 connection
echo "X11 Connection Test:"
if [ -n "$DISPLAY" ]; then
    if xdpyinfo &>/dev/null 2>&1; then
        echo "  ✓ Successfully connected to $DISPLAY"
        echo "  Screen: $(xdpyinfo | grep dimensions | awk '{print $2}')"
    else
        echo "  ✗ Cannot connect to $DISPLAY"
        echo ""
        echo "Suggested fixes:"
        echo "  1. Check if XQuartz is running (macOS)"
        echo "  2. Try: export DISPLAY=localhost:10.0"
        echo "  3. Reconnect SSH with: ssh -X -Y user@host"
    fi
else
    echo "  ✗ DISPLAY not set"
fi
echo ""

# Recommendations
echo "=== Recommendations ==="
AUTO_PORT=$(netstat -an 2>/dev/null | grep '127.0.0.1:60[0-9][0-9]' | grep LISTEN | head -1 | awk '{print $4}' | cut -d':' -f2)
if [ -n "$AUTO_PORT" ]; then
    AUTO_DISP=$((AUTO_PORT - 6000))
    if [ "$DISPLAY" != "localhost:${AUTO_DISP}.0" ]; then
        echo "Run this command:"
        echo "  export DISPLAY=localhost:${AUTO_DISP}.0"
        echo ""
    fi
fi

if [ -z "$DISPLAY" ] || ! xdpyinfo &>/dev/null 2>&1; then
    echo "For macOS SSH users:"
    echo "  1. brew install --cask xquartz"
    echo "  2. open -a XQuartz"
    echo "  3. Reconnect VS Code Remote-SSH"
fi