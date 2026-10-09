#!/bin/bash

# Get the directory of the script
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$APP_DIR"

# Enforce Wayland
export GDK_BACKEND=wayland
export SDL_VIDEODRIVER=wayland

# Activate virtual environment
source venv/bin/activate

# Run the application with any provided CLI arguments
python3 src/main.py "$@"
