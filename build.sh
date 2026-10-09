#!/bin/bash

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install PyGObject and other dependencies
# Note: On some systems, you might need to install system packages first (like libgtk-4-dev)
# But here we assume the environment has the necessary headers.
pip install --upgrade pip
pip install PyGObject

echo "Build complete. Virtual environment ready."
