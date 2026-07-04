#!/bin/bash
# Double-click me in Finder: starts the local proxy and opens the monitor page.
cd "$(dirname "$0")"
echo "Starting Fusion Job Monitor... (close this window or press Ctrl+C to stop)"
python3 cors-proxy.py
