import sys
import os
import shutil
import signal
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gio, GLib, Gdk, GLibUnix

# Add src and src/ui to path so components can find each other
src_dir = os.path.dirname(os.path.abspath(__file__))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)
ui_dir = os.path.join(src_dir, 'ui')
if ui_dir not in sys.path:
    sys.path.insert(0, ui_dir)

from core.config import APP_ID, APP_NAME, VERSION
from ui.window import AndyWindow

# Wayland / desktop integration:
# Setting prgname to match the application_id and desktop entry allows Wayland compositors
# (KWin / Mutter) to map the window to its desktop file and task icon.
GLib.set_prgname(APP_ID)
GLib.set_application_name(APP_NAME)


def ensure_desktop_integration():
    """Ensure desktop file, AppStream metadata, and icons are registered in user's XDG directories."""
    try:
        home = os.path.expanduser("~")
        apps_dir = os.path.join(home, ".local", "share", "applications")
        icons_dir = os.path.join(home, ".local", "share", "icons", "hicolor", "scalable", "apps")
        legacy_icons_dir = os.path.join(home, ".local", "share", "icons")
        metainfo_dir = os.path.join(home, ".local", "share", "metainfo")

        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        exec_path = os.path.join(root_dir, "run.sh")
        icon_source = os.path.join(root_dir, "assets", "icon.svg")
        metainfo_source = os.path.join(root_dir, "data", f"{APP_ID}.metainfo.xml")

        desktop_file_path = os.path.join(apps_dir, f"{APP_ID}.desktop")
        legacy_desktop_path = os.path.join(apps_dir, "Andy.desktop")
        dest_icon_path = os.path.join(icons_dir, f"{APP_ID}.svg")
        legacy_hicolor_icon = os.path.join(icons_dir, "Andy.svg")
        flat_icon_path = os.path.join(legacy_icons_dir, "Andy.svg")
        dest_metainfo_path = os.path.join(metainfo_dir, f"{APP_ID}.metainfo.xml")

        os.makedirs(apps_dir, exist_ok=True)
        os.makedirs(icons_dir, exist_ok=True)
        os.makedirs(legacy_icons_dir, exist_ok=True)
        os.makedirs(metainfo_dir, exist_ok=True)

        if os.path.exists(icon_source):
            for target in (dest_icon_path, legacy_hicolor_icon, flat_icon_path):
                if not os.path.exists(target) or os.path.getmtime(icon_source) > os.path.getmtime(target):
                    shutil.copy2(icon_source, target)

        if os.path.exists(metainfo_source):
            shutil.copy2(metainfo_source, dest_metainfo_path)

        desktop_content = f"""[Desktop Entry]
Name=Andy
Comment=GTK4 scrcpy Wrapper for Android Screen Mirroring
Exec={exec_path}
Path={root_dir}
Icon={APP_ID}
Terminal=false
Type=Application
Categories=Utility;System;
Keywords=scrcpy;android;mirror;adb;
StartupNotify=true
StartupWMClass={APP_ID}
X-GNOME-Authors=gitlab.com/wolfsekhar
Actions=ScreenStream;ConnectMK;

[Desktop Action ScreenStream]
Name=Start Screen Mirroring
Exec={exec_path} --start
Icon=video-display-symbolic

[Desktop Action ConnectMK]
Name=Connect Keyboard & Mouse
Exec={exec_path} --connect-mk
Icon=input-keyboard-symbolic
"""
        with open(desktop_file_path, "w") as f:
            f.write(desktop_content)
        os.chmod(desktop_file_path, 0o755)

        if not os.path.exists(legacy_desktop_path):
            try:
                os.symlink(desktop_file_path, legacy_desktop_path)
            except OSError:
                with open(legacy_desktop_path, "w") as f:
                    f.write(desktop_content)
                os.chmod(legacy_desktop_path, 0o755)
    except Exception as e:
        print(f"Desktop integration notice: {e}", file=sys.stderr)


class AndyApplication(Adw.Application):
    def __init__(self):
        super().__init__(
            application_id=APP_ID,
            flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE
        )
        self.win: AndyWindow = None
        self.connect('startup', self.on_startup)
        self.connect('activate', self.on_activate)
        self.connect('command-line', self.on_command_line)

    def on_startup(self, app):
        # Register local assets directory with Gtk.IconTheme
        display = Gdk.Display.get_default()
        if display:
            theme = Gtk.IconTheme.get_for_display(display)
            assets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets')
            if os.path.exists(assets_dir):
                theme.add_search_path(assets_dir)

        # Set default window icon name to match APP_ID and icon theme
        Gtk.Window.set_default_icon_name(APP_ID)

        # Ensure desktop entry, actions, and icons exist
        ensure_desktop_integration()

        # Graceful UNIX signal termination
        try:
            GLibUnix.signal_add(GLib.PRIORITY_DEFAULT, signal.SIGINT, self.on_unix_signal)
            GLibUnix.signal_add(GLib.PRIORITY_DEFAULT, signal.SIGTERM, self.on_unix_signal)
        except Exception:
            pass

    def on_unix_signal(self):
        if self.win and self.win.process_manager.is_running:
            self.win.process_manager.stop()
        self.quit()
        return GLib.SOURCE_REMOVE

    def on_activate(self, app):
        if not self.win:
            self.win = AndyWindow(application=self)
        self.win.present()

    def on_command_line(self, app, command_line: Gio.ApplicationCommandLine):
        args = command_line.get_arguments()

        if "--version" in args:
            command_line.print_literal(f"Andy {VERSION}\n")
            return 0

        if "--help" in args or "-h" in args:
            command_line.print_literal(
                f"Andy {VERSION} - GTK4 scrcpy Wayland Controller\n\n"
                "Usage: andy [OPTIONS]\n\n"
                "Options:\n"
                "  --start             Automatically start screen stream on launch\n"
                "  --connect-mk        Start lightweight Keyboard & Mouse HID bridge\n"
                "  -s, --device SERIAL Target specific Android device serial\n"
                "  --version           Print version information and exit\n"
                "  -h, --help          Show this help message and exit\n"
            )
            return 0

        # Activate primary window
        self.activate()

        # Handle specific device selection
        target_serial = None
        for i, arg in enumerate(args):
            if arg in ("-s", "--device") and i + 1 < len(args):
                target_serial = args[i + 1]
            elif arg.startswith("--device="):
                target_serial = arg.split("=", 1)[1]

        if target_serial and self.win:
            for idx, dev in enumerate(self.win.devices):
                if dev.get('serial') == target_serial:
                    self.win.device_dropdown.set_selected(idx)
                    break

        # Handle auto-start triggers
        if "--start" in args and self.win:
            GLib.idle_add(self.win.on_play_clicked, self.win.stream_button)
        elif "--connect-mk" in args and self.win:
            GLib.idle_add(self.win.on_connect_mk_clicked, self.win.connect_mk_button)

        return 0


if __name__ == "__main__":
    app = AndyApplication()
    sys.exit(app.run(sys.argv))
