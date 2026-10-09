import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk
from core.config import UI_SCALE_STEPS
from services.settings_service import get_setting, set_setting

class ScaleControl(Gtk.Box):
    """
    Linked segmented button control for scaling application UI font and DPI.
    [ - | 100% | + ]
    """
    def __init__(self, **kwargs):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, **kwargs)
        self.add_css_class("linked")
        self.set_valign(Gtk.Align.CENTER)
        self.set_halign(Gtk.Align.CENTER)

        self.current_scale = float(get_setting("ui_scale", 1.0))

        self.btn_zoom_out = Gtk.Button(icon_name="zoom-out-symbolic")
        self.btn_zoom_out.set_tooltip_text("Zoom Out App UI (-)")
        self.btn_zoom_out.connect("clicked", self.on_zoom_out_clicked)

        self.btn_zoom_reset = Gtk.Button(label=f"{int(round(self.current_scale * 100))}%")
        self.btn_zoom_reset.set_tooltip_text("Reset App UI Scale to 100%")
        self.btn_zoom_reset.connect("clicked", self.on_zoom_reset_clicked)

        self.btn_zoom_in = Gtk.Button(icon_name="zoom-in-symbolic")
        self.btn_zoom_in.set_tooltip_text("Zoom In App UI (+)")
        self.btn_zoom_in.connect("clicked", self.on_zoom_in_clicked)

        self.append(self.btn_zoom_out)
        self.append(self.btn_zoom_reset)
        self.append(self.btn_zoom_in)

        self.apply_scale(self.current_scale)

    def on_zoom_in_clicked(self, button):
        current = round(self.current_scale, 2)
        for step in UI_SCALE_STEPS:
            if step > current + 0.01:
                self.apply_scale(step)
                return
        self.apply_scale(UI_SCALE_STEPS[-1])

    def on_zoom_out_clicked(self, button):
        current = round(self.current_scale, 2)
        for step in reversed(UI_SCALE_STEPS):
            if step < current - 0.01:
                self.apply_scale(step)
                return
        self.apply_scale(UI_SCALE_STEPS[0])

    def on_zoom_reset_clicked(self, button):
        self.apply_scale(1.0)

    def apply_scale(self, scale: float):
        scale = max(UI_SCALE_STEPS[0], min(UI_SCALE_STEPS[-1], round(scale, 2)))
        self.current_scale = scale
        self.btn_zoom_reset.set_label(f"{int(round(scale * 100))}%")
        self.btn_zoom_out.set_sensitive(scale > UI_SCALE_STEPS[0] + 0.01)
        self.btn_zoom_in.set_sensitive(scale < UI_SCALE_STEPS[-1] - 0.01)

        settings = Gtk.Settings.get_default()
        if settings:
            dpi_val = int(98304 * scale)
            settings.set_property("gtk-xft-dpi", dpi_val)

        set_setting("ui_scale", scale)
