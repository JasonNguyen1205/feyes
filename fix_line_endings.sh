#!/bin/bash
# Fix Windows CRLF line endings to Unix LF
# Run this if you get "cannot execute: required file not found" errors

echo "Converting all shell scripts to Unix line endings..."

# Find and fix all .sh files
find . -name "*.sh" -type f -exec sed -i 's/\r$//' {} +

echo "✓ Done! All .sh files now have Unix (LF) line endings"
echo ""
echo "If you cloned from Windows or edited files on Windows,"
echo "run this script whenever you get execution errors."
