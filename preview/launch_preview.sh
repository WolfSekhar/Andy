#!/bin/bash
# Launcher for Andy UX Design Concepts Showcase

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$APP_DIR"

export GDK_BACKEND=wayland
source venv/bin/activate
python3 preview/preview_runner.py "$@"
