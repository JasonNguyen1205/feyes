#!/bin/bash
# Script to update server at 10.100.27.75

SERVER_IP="10.100.27.75"
SERVER_USER="jason_nguyen"
SERVER_PATH="/home/jason_nguyen/feyes"

echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║           Updating Server at $SERVER_IP                          ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""

echo "Connecting to server..."
ssh ${SERVER_USER}@${SERVER_IP} << 'ENDSSH'
cd /home/jason_nguyen/feyes

echo "1. Pulling latest code..."
git pull origin main

echo ""
echo "2. Stopping old server..."
pkill -f simple_api_server

echo ""
echo "3. Starting updated server..."
nohup ./launch_server.sh > /tmp/server.log 2>&1 &

sleep 2
echo ""
echo "4. Checking server status..."
if pgrep -f simple_api_server > /dev/null; then
    echo "✅ Server started successfully!"
    echo ""
    echo "Server logs: tail -f /tmp/server.log"
else
    echo "❌ Server failed to start. Check logs: cat /tmp/server.log"
fi
ENDSSH

echo ""
echo "Done! Server at $SERVER_IP updated."
