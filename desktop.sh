#!/bin/bash

# Get absolute path of the current directory
APP_DIR=$(cd "$(dirname "$0")" && pwd)
ICON_PATH="$APP_DIR/assets/icon.svg"
EXEC_PATH="$APP_DIR/run.sh"
APP_ID="com.wolfsekhar.Andy"

# Define destination paths
APPLICATIONS_DIR="$HOME/.local/share/applications"
DESKTOP_FILE_PATH="$APPLICATIONS_DIR/$APP_ID.desktop"
LEGACY_DESKTOP_PATH="$APPLICATIONS_DIR/Andy.desktop"

HICOLOR_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"
LEGACY_ICON_DIR="$HOME/.local/share/icons"

USER_ICON_PATH="$HICOLOR_DIR/$APP_ID.svg"
LEGACY_HICOLOR_ICON_PATH="$HICOLOR_DIR/Andy.svg"
LEGACY_ICON_PATH="$LEGACY_ICON_DIR/Andy.svg"

# Create directories if they don't exist
mkdir -p "$APPLICATIONS_DIR"
mkdir -p "$HICOLOR_DIR"
mkdir -p "$LEGACY_ICON_DIR"

# Copy the icon to standard hicolor directory and fallback locations
cp "$ICON_PATH" "$USER_ICON_PATH"
cp "$ICON_PATH" "$LEGACY_HICOLOR_ICON_PATH"
cp "$ICON_PATH" "$LEGACY_ICON_PATH"

# Install AppStream metainfo
METAINFO_DIR="$HOME/.local/share/metainfo"
mkdir -p "$METAINFO_DIR"
if [ -f "$APP_DIR/data/$APP_ID.metainfo.xml" ]; then
    cp "$APP_DIR/data/$APP_ID.metainfo.xml" "$METAINFO_DIR/"
fi

# Generate the desktop file matching the application_id with Desktop Actions
cat <<EOF > "$DESKTOP_FILE_PATH"
[Desktop Entry]
Name=Andy
Comment=GTK4 scrcpy Wrapper for Android Screen Mirroring
Exec=$EXEC_PATH
Path=$APP_DIR
Icon=$APP_ID
Terminal=false
Type=Application
Categories=Utility;System;
Keywords=scrcpy;android;mirror;adb;
StartupNotify=true
StartupWMClass=$APP_ID
X-GNOME-Authors=gitlab.com/wolfsekhar
Actions=ScreenStream;ConnectMK;

[Desktop Action ScreenStream]
Name=Start Screen Mirroring
Exec=$EXEC_PATH --start
Icon=video-display-symbolic

[Desktop Action ConnectMK]
Name=Connect Keyboard & Mouse
Exec=$EXEC_PATH --connect-mk
Icon=input-keyboard-symbolic
EOF

# Make the desktop file executable
chmod +x "$DESKTOP_FILE_PATH"

# Create a symlink for backward compatibility with Andy.desktop
ln -sf "$DESKTOP_FILE_PATH" "$LEGACY_DESKTOP_PATH"

# Update desktop and icon databases if tools are available
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$APPLICATIONS_DIR" 2>/dev/null || true
fi

if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" 2>/dev/null || true
fi

echo "Desktop entry created at: $DESKTOP_FILE_PATH"
echo "Icon stored at: $USER_ICON_PATH"
echo "You can now find Andy in your application menu."
