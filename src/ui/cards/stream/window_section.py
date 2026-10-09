import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw
from core.config import RENDER_FITS

class WindowSection(Adw.PreferencesGroup):
    """
    Window display toggles (Fullscreen, Borderless, Always on top, Disable screensaver, Render Fit).
    """
    def __init__(self, **kwargs):
        super().__init__(title="Window Settings", **kwargs)

        self.param_fullscreen = Adw.SwitchRow(title="Fullscreen")
        self.param_borderless = Adw.SwitchRow(title="Borderless")
        self.param_always_on_top = Adw.SwitchRow(title="Always On Top")
        self.param_disable_screensaver = Adw.SwitchRow(title="Disable Screensaver")

        self.render_fit_model = Gtk.StringList()
        for f in RENDER_FITS:
            self.render_fit_model.append(f)
        self.param_render_fit = Adw.ComboRow(title="Render Fit", model=self.render_fit_model)
        self.param_render_fit.dropdown = self.param_render_fit
        self.render_fit_row = self.param_render_fit
        self.render_fit_dropdown = self.param_render_fit

        self.add(self.param_fullscreen)
        self.add(self.param_borderless)
        self.add(self.param_always_on_top)
        self.add(self.param_disable_screensaver)
        self.add(self.param_render_fit)
