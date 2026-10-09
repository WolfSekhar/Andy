import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw

from core.config import APP_ID, APP_NAME, VERSION


def show_about_dialog(parent_window: Gtk.Window):
    """Presents modern Libadwaita About dialog."""
    dialog = Adw.AboutDialog()
    dialog.set_application_name(APP_NAME)
    dialog.set_version(VERSION)
    dialog.set_developer_name("Sekhar")
    dialog.set_application_icon(APP_ID)
    dialog.set_comments("Modern GTK4 &amp; Wayland-native scrcpy GUI controller for Android")
    dialog.set_website("https://github.com/wolfsekhar/andy")
    dialog.set_issue_url("https://github.com/wolfsekhar/andy/issues")
    dialog.set_license_type(Gtk.License.GPL_3_0)
    dialog.set_copyright("© 2026 Sekhar")
    dialog.add_acknowledgement_section(
        "Powered By",
        ["Romain Vimont (@rom1v) and the scrcpy open-source contributors"]
    )
    dialog.present(parent_window)
