import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw
from core.config import AUDIO_CODECS, AUDIO_SOURCES, AUDIO_BUFFERS

class AudioSection(Adw.PreferencesGroup):
    """
    Audio stream settings (Codec, Audio Duplication, Audio Source, Bitrate, Buffer).
    """
    def __init__(self, **kwargs):
        super().__init__(title="Audio Settings", **kwargs)

        # Audio Codec
        self.audio_codec_row = Adw.ActionRow(title="Audio Codec")
        self.audio_codec_model = Gtk.StringList()
        for c in AUDIO_CODECS:
            self.audio_codec_model.append(c)
        self.audio_codec_dropdown = Gtk.DropDown(model=self.audio_codec_model)
        self.audio_codec_dropdown.set_valign(Gtk.Align.CENTER)
        self.audio_codec_row.add_suffix(self.audio_codec_dropdown)
        self.add(self.audio_codec_row)

        # Audio Duplication
        self.param_audio_dup = Adw.SwitchRow(
            title="Duplicate Audio",
            subtitle="Keep sound playing on device while streaming"
        )
        self.add(self.param_audio_dup)

        # Audio Source
        self.audio_source_row = Adw.ActionRow(title="Audio Source")
        self.audio_source_model = Gtk.StringList()
        for s in AUDIO_SOURCES:
            self.audio_source_model.append(s)
        self.audio_source_dropdown = Gtk.DropDown(model=self.audio_source_model)
        self.audio_source_dropdown.set_valign(Gtk.Align.CENTER)
        self.audio_source_row.add_suffix(self.audio_source_dropdown)
        self.add(self.audio_source_row)

        # Audio Bitrate
        self.audio_bitrate_row = Adw.EntryRow(title="Audio Bitrate (Kbps)")
        self.add(self.audio_bitrate_row)

        # Audio Buffer
        self.audio_buffer_row = Adw.ActionRow(title="Audio Buffer")
        self.audio_buffer_model = Gtk.StringList()
        for b in AUDIO_BUFFERS:
            self.audio_buffer_model.append(b)
        self.audio_buffer_dropdown = Gtk.DropDown(model=self.audio_buffer_model)
        self.audio_buffer_dropdown.set_valign(Gtk.Align.CENTER)
        self.audio_buffer_row.add_suffix(self.audio_buffer_dropdown)
        self.add(self.audio_buffer_row)

    def set_no_audio(self, is_no_audio: bool):
        self.audio_codec_row.set_sensitive(not is_no_audio)
        self.param_audio_dup.set_sensitive(not is_no_audio)
        self.audio_source_row.set_sensitive(not is_no_audio)
        self.audio_bitrate_row.set_sensitive(not is_no_audio)
        self.audio_buffer_row.set_sensitive(not is_no_audio)
        if is_no_audio:
            self.audio_codec_dropdown.set_selected(0)
            self.param_audio_dup.set_active(False)
            self.audio_source_dropdown.set_selected(0)
            self.audio_bitrate_row.set_text("")
            self.audio_buffer_dropdown.set_selected(0)
