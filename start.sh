#!/bin/bash
# Quick launcher for Visual AOI System (Linux)
# Simple wrapper around launch_all.sh

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
exec "$SCRIPT_DIR/launch_all.sh" "$@"
