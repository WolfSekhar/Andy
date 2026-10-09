# Andy - GTK4 scrcpy Wrapper

## Project Overview
Andy is a modular Python and GTK4 (Libadwaita) application designed as a modern, Wayland-native GUI wrapper for `scrcpy`. It allows users to manage connected Android devices via ADB, view device details, and launch customized `scrcpy` sessions.

## Key Features
- **Dynamic Resolution**: Automatically calculates 5 proportional quality levels based on the device's native resolution.
- **Orientation Awareness**: Background monitoring of device rotation to keep resolution presets accurate in real-time.
- **Camera Streaming**: Support for all on-device cameras with automatic resolution detection.
- **Connect M/K**: Dedicated mode to send Mouse and Keyboard input without high-resource video streaming (uses a low-res fullscreen bridge).
- **Custom Parameters**: Editable fields for Max FPS and Max Size alongside presets.
- **Profile Management**: Save and manage custom parameter profiles.
- **Robust Error Handling**: Real-time capture of `scrcpy` logs and detailed error dialogs for troubleshooting.

## Building and Running
*   **Build the environment:** Run `./build.sh` to create a Python virtual environment and install dependencies.
*   **Run the application:** Execute `./run.sh`. This script enforces Wayland (`GDK_BACKEND=wayland`) and starts the app.
*   **Desktop Shortcut:** Run `./desktop.sh` to install a desktop entry and icon into your application menu.

## Project Structure
*   `src/main.py`: Application entry point.
*   `src/ui/window.py`: Main window orchestrator.
*   `src/ui/header_bar.py`: Custom header bar (composition-based).
*   `src/ui/settings_dialog.py`: Profile management and settings.
*   `src/ui/stream_card.py` / `advanced_card.py` / `details_card.py`: Modular UI sections.
*   `src/scrcpy_manager.py`: ADB and scrcpy CLI interface logic.

## Development Conventions
*   **Wayland Exclusive**: Strict enforcement of Wayland backends.
*   **Composition Over Inheritance**: Prefer wrapping `Adw` widgets (like `Adw.HeaderBar`) rather than subclassing to avoid issues with final types in Libadwaita.
*   **Async Operations**: All blocking CLI calls (ADB/scrcpy) must run in background threads and update the UI via `GLib.idle_add`.
*   **Process Lifecycle**: Subprocesses are tracked locally and monitored via `GLib.child_watch_add` for automatic UI state resets on exit.
