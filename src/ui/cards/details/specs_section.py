from typing import Dict, Any, Callable
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw

class SpecsSection(Adw.PreferencesGroup):
    """
    Primary device hardware specifications (Model, Version, Resolution, Battery, DPI).
    """
    def __init__(self, on_density_adjust: Callable[[int], None], on_density_reset: Callable[[], None], **kwargs):
        super().__init__(**kwargs)

        self.row_model = Adw.ActionRow(title="Model", subtitle="N/A")
        self.row_model.add_prefix(Gtk.Image.new_from_icon_name("phone-symbolic"))

        self.row_version = Adw.ActionRow(title="Android Version", subtitle="N/A")
        self.row_version.add_prefix(Gtk.Image.new_from_icon_name("emblem-system-symbolic"))

        self.row_resolution = Adw.ActionRow(title="Display Resolution", subtitle="N/A")
        self.row_resolution.add_prefix(Gtk.Image.new_from_icon_name("video-display-symbolic"))
        self.ratio_badge = Gtk.Label(label="")
        self.ratio_badge.add_css_class("theme-badge")
        self.ratio_badge.add_css_class("ratio-badge")
        self.ratio_badge.set_valign(Gtk.Align.CENTER)
        self.row_resolution.add_suffix(self.ratio_badge)

        self.row_battery = Adw.ActionRow(title="Battery", subtitle="N/A")
        self.battery_icon = Gtk.Image.new_from_icon_name("battery-symbolic")
        self.row_battery.add_prefix(self.battery_icon)

        # Screen Density (DPI)
        self.row_density = Adw.ActionRow(title="Screen Density (DPI)", subtitle="N/A")
        self.row_density.add_prefix(Gtk.Image.new_from_icon_name("display-symbolic"))
        self.density_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.density_box.add_css_class("linked")
        self.density_box.set_valign(Gtk.Align.CENTER)

        self.btn_density_down = Gtk.Button(label="-20")
        self.btn_density_down.set_tooltip_text("Decrease Screen Density (-20 DPI)")
        self.btn_density_down.connect("clicked", lambda b: on_density_adjust(-20))

        self.btn_density_up = Gtk.Button(label="+20")
        self.btn_density_up.set_tooltip_text("Increase Screen Density (+20 DPI)")
        self.btn_density_up.connect("clicked", lambda b: on_density_adjust(20))

        self.btn_density_reset = Gtk.Button(label="Reset")
        self.btn_density_reset.set_tooltip_text("Reset Screen Density to physical default")
        self.btn_density_reset.connect("clicked", lambda b: on_density_reset())

        self.density_box.append(self.btn_density_down)
        self.density_box.append(self.btn_density_up)
        self.density_box.append(self.btn_density_reset)
        self.row_density.add_suffix(self.density_box)

        self.add(self.row_model)
        self.add(self.row_version)
        self.add(self.row_resolution)
        self.add(self.row_battery)
        self.add(self.row_density)

    def apply_info(self, info: Dict[str, Any]):
        self.row_model.set_subtitle(info.get('model', 'N/A'))
        self.row_version.set_subtitle(info.get('version', 'N/A'))
        self.row_resolution.set_subtitle(info.get('resolution', 'N/A'))
        self.row_battery.set_subtitle(info.get('battery', 'N/A'))
        self.row_density.set_subtitle(info.get('density', 'N/A'))

        ratio = info.get('aspect_ratio', '')
        self.ratio_badge.set_text(ratio)
        self.ratio_badge.set_visible(bool(ratio))

        level = info.get('battery_level')
        charging = info.get('battery_charging', False)
        if level is not None:
            if level >= 80:
                icon_name = "battery-full-charging-symbolic" if charging else "battery-full-symbolic"
            elif level >= 50:
                icon_name = "battery-good-charging-symbolic" if charging else "battery-good-symbolic"
            elif level >= 20:
                icon_name = "battery-low-charging-symbolic" if charging else "battery-low-symbolic"
            else:
                icon_name = "battery-caution-charging-symbolic" if charging else "battery-caution-symbolic"
            self.battery_icon.set_from_icon_name(icon_name)
        else:
            self.battery_icon.set_from_icon_name("battery-symbolic")
