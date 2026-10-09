import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw
from services.host_telemetry import get_host_telemetry

class TelemetrySection(Adw.PreferencesGroup):
    """
    Host Wayland compositor and GPU display server telemetry.
    """
    def __init__(self, **kwargs):
        super().__init__(title="Host &amp; Wayland Telemetry", **kwargs)

        self.row_compositor = Adw.ActionRow(title="Display Server", subtitle="Wayland")
        self.row_compositor.add_prefix(Gtk.Image.new_from_icon_name("preferences-desktop-display-symbolic"))
        self.add(self.row_compositor)

        self.row_gpu = Adw.ActionRow(title="Host Graphics", subtitle="Auto")
        self.row_gpu.add_prefix(Gtk.Image.new_from_icon_name("video-joined-displays-symbolic"))
        self.add(self.row_gpu)

        self.load_telemetry()

    def load_telemetry(self):
        try:
            telemetry = get_host_telemetry()
            self.row_compositor.set_subtitle(telemetry.get("compositor", "Wayland"))
            self.row_gpu.set_subtitle(telemetry.get("gpu", "Auto"))
        except Exception:
            pass
