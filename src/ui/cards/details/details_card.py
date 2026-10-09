import os
import threading
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gdk

from ui.cards.details.specs_section import SpecsSection
from ui.cards.details.telemetry_section import TelemetrySection
from ui.cards.details.remote_section import RemoteSection

from services.device_service import get_detailed_device_info
from services.remote_actions import (
    take_device_screenshot,
    toggle_device_screen,
    adjust_device_volume,
    send_keyevent,
    expand_statusbar,
    inject_clipboard_text,
    set_device_density,
    reset_device_density,
    reboot_device,
    toggle_show_touches
)

class DetailsCard(Gtk.Box):
    def __init__(self, **kwargs):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12, **kwargs)
        self.current_serial = None
        self.current_density = None

        # Title & Header
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        header_box.set_halign(Gtk.Align.CENTER)

        self.label = Gtk.Label(label="Device Details")
        self.label.add_css_class("title-4")
        header_box.append(self.label)

        self.conn_badge = Gtk.Label(label="Disconnected")
        self.conn_badge.add_css_class("theme-badge")
        self.conn_badge.set_valign(Gtk.Align.CENTER)
        header_box.append(self.conn_badge)

        self.append(header_box)

        # Specs Section
        self.specs_section = SpecsSection(
            on_density_adjust=self.on_density_adjust_clicked,
            on_density_reset=self.on_density_reset_clicked
        )
        self.append(self.specs_section)
        self.group = self.specs_section
        self.row_model = self.specs_section.row_model
        self.row_version = self.specs_section.row_version
        self.row_resolution = self.specs_section.row_resolution
        self.ratio_badge = self.specs_section.ratio_badge
        self.row_battery = self.specs_section.row_battery
        self.battery_icon = self.specs_section.battery_icon
        self.row_density = self.specs_section.row_density
        self.btn_density_down = self.specs_section.btn_density_down
        self.btn_density_up = self.specs_section.btn_density_up
        self.btn_density_reset = self.specs_section.btn_density_reset

        # Host Telemetry Section
        self.telemetry_section = TelemetrySection()
        self.append(self.telemetry_section)
        self.host_group = self.telemetry_section
        self.row_compositor = self.telemetry_section.row_compositor
        self.row_gpu = self.telemetry_section.row_gpu

        # Remote Section
        self.remote_section = RemoteSection(
            on_keyevent=self.on_keyevent_clicked,
            on_statusbar=self.on_statusbar_clicked,
            on_paste=self.on_paste_clipboard_clicked,
            on_touches=self.on_toggle_touches_clicked,
            on_screenshot=self.on_screenshot_clicked,
            on_power=self.on_power_clicked,
            on_volume=self.on_volume_clicked,
            on_reboot=self.on_reboot_clicked
        )
        self.append(self.remote_section)
        self.remote_group = self.remote_section.remote_group
        self.tools_group = self.remote_section.tools_group
        self.btn_nav_back = self.remote_section.btn_nav_back
        self.btn_nav_home = self.remote_section.btn_nav_home
        self.btn_nav_recents = self.remote_section.btn_nav_recents
        self.btn_notifications = self.remote_section.btn_notifications
        self.btn_quicksettings = self.remote_section.btn_quicksettings
        self.btn_paste = self.remote_section.btn_paste
        self.btn_touches = self.remote_section.btn_touches
        self.btn_screenshot = self.remote_section.btn_screenshot
        self.btn_power = self.remote_section.btn_power
        self.btn_vol_down = self.remote_section.btn_vol_down
        self.btn_vol_up = self.remote_section.btn_vol_up
        self.btn_reboot = self.remote_section.btn_reboot

        # Status note
        self.status_label = Gtk.Label(label="")
        self.status_label.add_css_class("dim-label")
        self.status_label.add_css_class("caption")
        self.status_label.set_halign(Gtk.Align.CENTER)
        self.append(self.status_label)

        self.set_tools_sensitive(False)

    def set_tools_sensitive(self, sensitive: bool):
        self.btn_density_down.set_sensitive(sensitive)
        self.btn_density_up.set_sensitive(sensitive)
        self.btn_density_reset.set_sensitive(sensitive)
        self.remote_section.set_sensitive(sensitive)

    def update_details(self, serial: str):
        self.current_serial = serial
        if not serial or serial == "No devices found":
            self.set_tools_sensitive(False)
            self.apply_info({
                'model': 'N/A',
                'version': 'N/A',
                'resolution': 'N/A',
                'battery': 'N/A',
                'density': 'N/A',
                'density_val': None,
                'connection': 'Disconnected',
                'aspect_ratio': ''
            })
            return

        self.set_tools_sensitive(True)
        self.row_model.set_subtitle("Loading...")
        self.row_version.set_subtitle("Loading...")
        self.row_resolution.set_subtitle("Loading...")
        self.row_battery.set_subtitle("Loading...")
        self.row_density.set_subtitle("Loading...")
        self.conn_badge.set_text("Connecting...")
        self.ratio_badge.set_text("")

        def fetch(target_serial):
            info = get_detailed_device_info(target_serial)
            if self.current_serial == target_serial:
                GLib.idle_add(self.apply_info, info)

        threading.Thread(target=fetch, args=(serial,), daemon=True).start()

    def apply_info(self, info):
        self.specs_section.apply_info(info)
        self.current_density = info.get('density_val')

        conn = info.get('connection', 'Disconnected')
        self.conn_badge.set_text(conn)
        return False

    def on_screenshot_clicked(self):
        if not self.current_serial: return
        self.status_label.set_text("Capturing screenshot...")
        def task():
            success, result = take_device_screenshot(self.current_serial)
            def update_ui():
                if success:
                    self.status_label.set_text(f"Screenshot: {os.path.basename(result)}")
                else:
                    self.status_label.set_text(f"Capture failed: {result}")
            GLib.idle_add(update_ui)
        threading.Thread(target=task, daemon=True).start()

    def on_power_clicked(self):
        if not self.current_serial: return
        def task():
            success, msg = toggle_device_screen(self.current_serial)
            GLib.idle_add(lambda: self.status_label.set_text("Screen toggled" if success else f"Error: {msg}"))
        threading.Thread(target=task, daemon=True).start()

    def on_volume_clicked(self, direction):
        if not self.current_serial: return
        def task():
            success, msg = adjust_device_volume(self.current_serial, direction)
            GLib.idle_add(lambda: self.status_label.set_text(f"Volume {direction}" if success else f"Error: {msg}"))
        threading.Thread(target=task, daemon=True).start()

    def on_density_adjust_clicked(self, delta):
        if not self.current_serial: return
        base_density = self.current_density if self.current_density else 420
        new_density = max(120, min(1000, base_density + delta))
        self.status_label.set_text(f"Setting density to {new_density} DPI...")
        def task():
            success, msg = set_device_density(self.current_serial, new_density)
            def update_ui():
                if success:
                    self.status_label.set_text(f"Density: {new_density} DPI")
                    self.update_details(self.current_serial)
                else:
                    self.status_label.set_text(f"Density error: {msg}")
            GLib.idle_add(update_ui)
        threading.Thread(target=task, daemon=True).start()

    def on_density_reset_clicked(self):
        if not self.current_serial: return
        self.status_label.set_text("Resetting density...")
        def task():
            success, msg = reset_device_density(self.current_serial)
            def update_ui():
                if success:
                    self.status_label.set_text("Density reset to physical default")
                    self.update_details(self.current_serial)
                else:
                    self.status_label.set_text(f"Density reset error: {msg}")
            GLib.idle_add(update_ui)
        threading.Thread(target=task, daemon=True).start()

    def on_keyevent_clicked(self, keycode, name):
        if not self.current_serial: return
        def task():
            success, msg = send_keyevent(self.current_serial, keycode)
            GLib.idle_add(lambda: self.status_label.set_text(f"Key {name} sent" if success else f"Key error: {msg}"))
        threading.Thread(target=task, daemon=True).start()

    def on_statusbar_clicked(self, target):
        if not self.current_serial: return
        def task():
            success, msg = expand_statusbar(self.current_serial, target)
            label = "Notifications expanded" if target == "notifications" else "Quick Settings expanded"
            GLib.idle_add(lambda: self.status_label.set_text(label if success else f"Statusbar error: {msg}"))
        threading.Thread(target=task, daemon=True).start()

    def on_paste_clipboard_clicked(self):
        if not self.current_serial: return
        display = Gdk.Display.get_default()
        if not display: return
        clipboard = display.get_clipboard()
        def on_read_text(cb, result):
            try:
                text = cb.read_text_finish(result)
                if text:
                    def task():
                        success, msg = inject_clipboard_text(self.current_serial, text)
                        GLib.idle_add(lambda: self.status_label.set_text("Clipboard pasted" if success else f"Paste error: {msg}"))
                    threading.Thread(target=task, daemon=True).start()
                else:
                    self.status_label.set_text("PC Clipboard is empty")
            except Exception as e:
                self.status_label.set_text(f"Clipboard read error: {e}")
        clipboard.read_text_async(None, on_read_text)

    def on_toggle_touches_clicked(self):
        if not self.current_serial: return
        def task():
            success, msg = toggle_show_touches(self.current_serial)
            GLib.idle_add(lambda: self.status_label.set_text(msg if success else f"Touch toggle error: {msg}"))
        threading.Thread(target=task, daemon=True).start()

    def on_reboot_clicked(self, mode):
        if not self.current_serial: return
        self.status_label.set_text(f"Rebooting device ({mode})...")
        def task():
            success, msg = reboot_device(self.current_serial, mode)
            GLib.idle_add(lambda: self.status_label.set_text(f"Rebooting ({mode})" if success else f"Reboot error: {msg}"))
        threading.Thread(target=task, daemon=True).start()
