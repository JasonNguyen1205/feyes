#!/bin/bash
# Setup script for visual-aoi-shared folder permissions
# This ensures the pi user can write to the shared folder

SHARED_DIR="/mnt/visual-aoi-shared"

# Create directory if it doesn't exist
sudo mkdir -p "$SHARED_DIR/sessions"

# Set ownership to pi user
sudo chown -R pi:pi "$SHARED_DIR"

# Set permissions
sudo chmod -R 755 "$SHARED_DIR"

echo "✓ Shared folder permissions configured"
