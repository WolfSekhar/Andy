import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw
from core.config import VIDEO_CODECS, FPS_PRESETS, ORIENTATIONS

class VideoSection(Adw.PreferencesGroup):
    """
    Video stream encoding and resolution settings.
    """
    def __init__(self, **kwargs):
        super().__init__(title="Video Settings", **kwargs)

        # Codec
        self.codec_row = Adw.ActionRow(title="Codec")
        self.codec_model = Gtk.StringList()
        for c in VIDEO_CODECS:
            self.codec_model.append(c)
        self.codec_dropdown = Gtk.DropDown(model=self.codec_model)
        self.codec_dropdown.set_valign(Gtk.Align.CENTER)
        self.codec_row.add_suffix(self.codec_dropdown)
        self.add(self.codec_row)

        # Max FPS
        self.fps_row = Adw.ActionRow(title="Max FPS")
        self.fps_combo = Gtk.ComboBoxText.new_with_entry()
        self.fps_combo.set_valign(Gtk.Align.CENTER)
        for f in FPS_PRESETS:
            self.fps_combo.append_text(f)
        self.fps_combo.set_active(0)
        self.fps_row.add_suffix(self.fps_combo)
        self.add(self.fps_row)

        # Max Size
        self.size_row = Adw.ActionRow(title="Max Size")
        self.size_combo = Gtk.ComboBoxText.new_with_entry()
        self.size_combo.set_valign(Gtk.Align.CENTER)
        self.size_row.add_suffix(self.size_combo)
        self.add(self.size_row)
        self.reset_size_dropdown()

        # Bit Rate
        self.bitrate_row = Adw.EntryRow(title="Bit Rate (Mbps)")
        self.add(self.bitrate_row)

        # Orientation
        self.orient_row = Adw.ActionRow(title="Orientation")
        self.orient_model = Gtk.StringList()
        for o in ORIENTATIONS:
            self.orient_model.append(o)
        self.orient_dropdown = Gtk.DropDown(model=self.orient_model)
        self.orient_dropdown.set_valign(Gtk.Align.CENTER)
        self.orient_row.add_suffix(self.orient_dropdown)
        self.add(self.orient_row)

    def reset_size_dropdown(self):
        self.size_combo.remove_all()
        for s in ["Default", "High", "Mid", "Low", "Mobile"]:
            self.size_combo.append_text(s)
        self.size_combo.set_active(0)

    def update_resolution_ui(self, resolution, is_camera_mode: bool = False) -> bool:
        if not resolution:
            return False

        if is_camera_mode:
            return False

        # Save current typed text to avoid overwriting user custom input
        current_text = self.size_combo.get_child().get_text()
        is_custom = True

        model = self.size_combo.get_model()
        n_items = model.iter_n_children(None)
        for i in range(n_items):
            it = model.iter_nth_child(None, i)
            if model.get_value(it, 0) == current_text:
                is_custom = False
                break

        self.size_combo.remove_all()
        self.size_combo.append_text("Default")

        w, h, _ = resolution
        percentages = [1.0, 0.8, 0.6, 0.4, 0.2]
        labels = ["Native", "Balanced", "Smooth", "Lite", "Minimal"]
        for i, p in enumerate(percentages):
            calc_w = int(w * p)
            calc_h = int(h * p)
            self.size_combo.append_text(f"{calc_w}x{calc_h} ({labels[i]})")

        if is_custom:
            self.size_combo.get_child().set_text(current_text)
        else:
            self.size_combo.set_active(0)

        return False
