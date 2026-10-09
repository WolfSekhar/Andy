import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw

class RecordSection(Adw.PreferencesGroup):
    """
    Stream recording configuration (Record Stream, Format mp4/mkv).
    """
    def __init__(self, **kwargs):
        super().__init__(title="Recording", **kwargs)

        self.param_record = Adw.SwitchRow(
            title="Record Stream to File",
            subtitle="Save video to ~/Videos/Andy"
        )
        self.add(self.param_record)

        self.record_format_row = Adw.ActionRow(title="Record Format")
        self.record_format_model = Gtk.StringList()
        for fmt in ["mp4", "mkv"]:
            self.record_format_model.append(fmt)
        self.record_format_dropdown = Gtk.DropDown(model=self.record_format_model)
        self.record_format_dropdown.set_valign(Gtk.Align.CENTER)
        self.record_format_row.add_suffix(self.record_format_dropdown)
        self.add(self.record_format_row)

        self.record_format_row.set_sensitive(False)
        self.param_record.connect("notify::active", lambda s, p: self.record_format_row.set_sensitive(s.get_active()))
