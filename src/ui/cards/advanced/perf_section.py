import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw
from core.config import GPU_ADAPTERS, RENDER_DRIVERS, WINDOW_BACKENDS, BUFFER_PRESETS, HWDEC_OPTIONS

class PerfSection(Adw.PreferencesGroup):
    """
    Performance, rendering drivers, buffer delay, and window backend options.
    """
    def __init__(self, **kwargs):
        super().__init__(title="Performance &amp; Rendering", **kwargs)

        # GPU Adapter (PRIME Offload)
        self.gpu_row = Adw.ActionRow(title="GPU Adapter")
        self.gpu_model = Gtk.StringList()
        for g in GPU_ADAPTERS:
            self.gpu_model.append(g)
        self.gpu_dropdown = Gtk.DropDown(model=self.gpu_model)
        self.gpu_dropdown.set_valign(Gtk.Align.CENTER)
        self.gpu_row.add_suffix(self.gpu_dropdown)
        self.add(self.gpu_row)

        # Render Driver
        self.render_driver_row = Adw.ActionRow(title="Render Driver")
        self.render_driver_model = Gtk.StringList()
        for r in RENDER_DRIVERS:
            self.render_driver_model.append(r)
        self.render_driver_dropdown = Gtk.DropDown(model=self.render_driver_model)
        self.render_driver_dropdown.set_valign(Gtk.Align.CENTER)
        self.render_driver_row.add_suffix(self.render_driver_dropdown)
        self.add(self.render_driver_row)

        # Hardware Decoding
        self.hwdec_row = Adw.ActionRow(title="Hardware Decoding")
        self.hwdec_model = Gtk.StringList()
        for h in HWDEC_OPTIONS:
            self.hwdec_model.append(h)
        self.hwdec_dropdown = Gtk.DropDown(model=self.hwdec_model)
        self.hwdec_dropdown.set_valign(Gtk.Align.CENTER)
        self.hwdec_row.add_suffix(self.hwdec_dropdown)
        self.add(self.hwdec_row)

        # Window Backend
        self.backend_row = Adw.ActionRow(title="Window Backend")
        self.backend_model = Gtk.StringList()
        for b in WINDOW_BACKENDS:
            self.backend_model.append(b)
        self.backend_dropdown = Gtk.DropDown(model=self.backend_model)
        self.backend_dropdown.set_valign(Gtk.Align.CENTER)
        self.backend_row.add_suffix(self.backend_dropdown)
        self.add(self.backend_row)

        # Display Buffer
        self.buffer_row = Adw.ActionRow(title="Display Buffer")
        self.buffer_model = Gtk.StringList()
        for b in BUFFER_PRESETS:
            self.buffer_model.append(b)
        self.buffer_dropdown = Gtk.DropDown(model=self.buffer_model)
        self.buffer_dropdown.set_valign(Gtk.Align.CENTER)
        self.buffer_row.add_suffix(self.buffer_dropdown)
        self.add(self.buffer_row)

        # Disable Downsize on Error
        self.param_no_downsize_on_error = Adw.SwitchRow(
            title="Disable Downsize on Error",
            subtitle="Do not downsize resolution automatically on encoder error"
        )
        self.add(self.param_no_downsize_on_error)

        # Show FPS Counter
        self.param_print_fps = Adw.SwitchRow(title="Show FPS Logs")
        self.add(self.param_print_fps)
