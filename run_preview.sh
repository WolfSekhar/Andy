#!/usr/bin/env bash
# run_preview.sh - Launch Andy UI Overhaul Layout Previews
set -e
cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Running ./build.sh..."
    ./build.sh
fi

export GDK_BACKEND="wayland,x11"

case "$1" in
    1)
        echo "Launching Option 1: The Modern Workstation (NavigationSplitView)..."
        ./venv/bin/python3 previews/preview_1_modern_workstation.py
        ;;
    2)
        echo "Launching Option 2: The Studio Command Deck (ViewSwitcher + Hero Card)..."
        ./venv/bin/python3 previews/preview_2_studio_command_deck.py
        ;;
    3)
        echo "Launching Option 3: The Compact Floating Inspector (OverlaySplitView + OSD)..."
        ./venv/bin/python3 previews/preview_3_compact_inspector.py
        ;;
    4)
        echo "Launching Option 4: The Modular Card Hub (3-Pod Grid + Profile Chips)..."
        ./venv/bin/python3 previews/preview_4_modular_card_hub.py
        ;;
    5)
        echo "Launching Option 5: The Action-Driven Assistant (5 Goal Workflow Cards)..."
        ./venv/bin/python3 previews/preview_5_action_assistant.py
        ;;
    *)
        echo "Launching Andy UI Overhaul Preview Hub..."
        ./venv/bin/python3 previews/launcher.py
        ;;
esac
