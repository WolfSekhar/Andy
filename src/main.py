import sys
import os
import shutil
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gio, GLib, Gdk

APP_ID = 'com.wolfsekhar.Andy'
APP_NAME = 'Andy'

# Wayland / desktop integration workaround:
# In PyGObject applications under Wayland, prgname defaults to python3 unless explicitly set.
# Setting prgname to match the application_id and desktop entry allows Wayland compositors
# (KWin / Mutter) to map the window to its desktop file and task icon.
GLib.set_prgname(APP_ID)
GLib.set_application_name(APP_NAME)

# Add src and src/ui to path so components can find each other
src_dir = os.path.dirname(os.path.abspath(__file__))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)
ui_dir = os.path.join(src_dir, 'ui')
if ui_dir not in sys.path:
    sys.path.insert(0, ui_dir)

from ui.window import AndyWindow


def ensure_desktop_integration():
    """Ensure desktop file and icons are registered in user's XDG directories for Wayland mapping."""
    try:
        home = os.path.expanduser("~")
        apps_dir = os.path.join(home, ".local", "share", "applications")
        icons_dir = os.path.join(home, ".local", "share", "icons", "hicolor", "scalable", "apps")
        legacy_icons_dir = os.path.join(home, ".local", "share", "icons")

        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        exec_path = os.path.join(root_dir, "run.sh")
        icon_source = os.path.join(root_dir, "assets", "icon.svg")

        desktop_file_path = os.path.join(apps_dir, f"{APP_ID}.desktop")
        legacy_desktop_path = os.path.join(apps_dir, "Andy.desktop")
        dest_icon_path = os.path.join(icons_dir, f"{APP_ID}.svg")
        legacy_hicolor_icon = os.path.join(icons_dir, "Andy.svg")
        flat_icon_path = os.path.join(legacy_icons_dir, "Andy.svg")

        os.makedirs(apps_dir, exist_ok=True)
        os.makedirs(icons_dir, exist_ok=True)
        os.makedirs(legacy_icons_dir, exist_ok=True)

        if os.path.exists(icon_source):
            for target in (dest_icon_path, legacy_hicolor_icon, flat_icon_path):
                if not os.path.exists(target) or os.path.getmtime(icon_source) > os.path.getmtime(target):
                    shutil.copy2(icon_source, target)

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
"""
        if not os.path.exists(desktop_file_path):
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
            flags=Gio.ApplicationFlags.NON_UNIQUE
        )
        self.connect('startup', self.on_startup)
        self.connect('activate', self.on_activate)

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

        # Ensure desktop entry and icons exist for Wayland window matching
        ensure_desktop_integration()

    def on_activate(self, app):
        win = AndyWindow(application=self)
        win.present()


if __name__ == "__main__":
    app = AndyApplication()
    app.run(sys.argv)
