import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw

from ui.cards.advanced.audio_section import AudioSection
from ui.cards.advanced.perf_section import PerfSection
from ui.cards.advanced.device_section import DeviceSection

from core.models import AdvancedConfig
from core.scrcpy_builder import build_advanced_args, build_environment_overrides

class AdvancedCard(Gtk.Box):
    def __init__(self, **kwargs):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12, **kwargs)

        # Header
        self.label = Gtk.Label(label="Advanced")
        self.label.add_css_class("title-4")
        self.label.set_halign(Gtk.Align.CENTER)
        self.append(self.label)

        # Audio Section
        self.audio_section = AudioSection()
        self.append(self.audio_section)
        self.audio_group = self.audio_section
        self.audio_codec_row = self.audio_section.audio_codec_row
        self.audio_codec_model = self.audio_section.audio_codec_model
        self.audio_codec_dropdown = self.audio_section.audio_codec_dropdown
        self.param_audio_dup = self.audio_section.param_audio_dup
        self.audio_source_row = self.audio_section.audio_source_row
        self.audio_source_model = self.audio_section.audio_source_model
        self.audio_source_dropdown = self.audio_section.audio_source_dropdown
        self.audio_bitrate_row = self.audio_section.audio_bitrate_row
        self.audio_buffer_row = self.audio_section.audio_buffer_row
        self.audio_buffer_model = self.audio_section.audio_buffer_model
        self.audio_buffer_dropdown = self.audio_section.audio_buffer_dropdown

        # Performance Section
        self.perf_section = PerfSection()
        self.append(self.perf_section)
        self.perf_group = self.perf_section
        self.gpu_row = self.perf_section.gpu_row
        self.gpu_model = self.perf_section.gpu_model
        self.gpu_dropdown = self.perf_section.gpu_dropdown
        self.render_driver_row = self.perf_section.render_driver_row
        self.render_driver_model = self.perf_section.render_driver_model
        self.render_driver_dropdown = self.perf_section.render_driver_dropdown
        self.hwdec_row = self.perf_section.hwdec_row
        self.hwdec_model = self.perf_section.hwdec_model
        self.hwdec_dropdown = self.perf_section.hwdec_dropdown
        self.backend_row = self.perf_section.backend_row
        self.backend_model = self.perf_section.backend_model
        self.backend_dropdown = self.perf_section.backend_dropdown
        self.buffer_row = self.perf_section.buffer_row
        self.buffer_model = self.perf_section.buffer_model
        self.buffer_dropdown = self.perf_section.buffer_dropdown
        self.param_no_downsize_on_error = self.perf_section.param_no_downsize_on_error
        self.param_print_fps = self.perf_section.param_print_fps

        # Device Section
        self.device_section = DeviceSection()
        self.append(self.device_section)
        self.parameters_group = self.device_section
        self.param_screen_off = self.device_section.param_screen_off
        self.param_stay_awake = self.device_section.param_stay_awake
        self.param_no_audio = self.device_section.param_no_audio
        self.param_read_only = self.device_section.param_read_only
        self.param_keyboard_uhid = self.device_section.param_keyboard_uhid
        self.param_mouse_uhid = self.device_section.param_mouse_uhid
        self.param_gamepad_uhid = self.device_section.param_gamepad_uhid
        self.mouse_bind_row = self.device_section.mouse_bind_row
        self.mouse_bind_model = self.device_section.mouse_bind_model
        self.mouse_bind_dropdown = self.device_section.mouse_bind_dropdown
        self.param_legacy_paste = self.device_section.param_legacy_paste
        self.param_no_clipboard_autosync = self.device_section.param_no_clipboard_autosync
        self.param_power_off_on_close = self.device_section.param_power_off_on_close
        self.param_no_power_on = self.device_section.param_no_power_on
        self.time_limit_row = self.device_section.time_limit_row
        self.param_show_touches = self.device_section.param_show_touches
        self.param_keep_active = self.device_section.param_keep_active
        self.timeout_row = self.device_section.timeout_row
        self.timeout_model = self.device_section.timeout_model
        self.timeout_dropdown = self.device_section.timeout_dropdown

        # Dynamic Dependencies
        self.param_no_audio.connect("notify::active", self.on_no_audio_toggled)

    def on_no_audio_toggled(self, switch, pspec):
        self.audio_section.set_no_audio(switch.get_active())

    def set_camera_mode(self, enabled: bool):
        self.device_section.set_camera_mode(enabled)

    def get_config(self) -> AdvancedConfig:
        return AdvancedConfig(
            audio_codec=self.audio_codec_dropdown.get_selected(),
            audio_dup=self.param_audio_dup.get_active(),
            audio_source=self.audio_source_dropdown.get_selected(),
            gpu_adapter=self.gpu_dropdown.get_selected(),
            render_driver=self.render_driver_dropdown.get_selected(),
            backend=self.backend_dropdown.get_selected(),
            buffer=self.buffer_dropdown.get_selected(),
            print_fps=self.param_print_fps.get_active(),
            screen_off=self.param_screen_off.get_active(),
            stay_awake=self.param_stay_awake.get_active(),
            no_audio=self.param_no_audio.get_active(),
            read_only=self.param_read_only.get_active(),
            keyboard_uhid=self.param_keyboard_uhid.get_active(),
            mouse_uhid=self.param_mouse_uhid.get_active(),
            show_touches=self.param_show_touches.get_active(),
            keep_active=self.param_keep_active.get_active(),
            timeout=self.timeout_dropdown.get_selected(),
            hwdec=self.hwdec_dropdown.get_selected(),
            no_downsize_on_error=self.param_no_downsize_on_error.get_active(),
            audio_bitrate=(self.audio_bitrate_row.get_text() or "").strip(),
            audio_buffer=self.audio_buffer_dropdown.get_selected(),
            gamepad_uhid=self.param_gamepad_uhid.get_active(),
            mouse_bind=self.mouse_bind_dropdown.get_selected(),
            legacy_paste=self.param_legacy_paste.get_active(),
            no_clipboard_autosync=self.param_no_clipboard_autosync.get_active(),
            power_off_on_close=self.param_power_off_on_close.get_active(),
            no_power_on=self.param_no_power_on.get_active(),
            time_limit=(self.time_limit_row.get_text() or "").strip()
        )

    def get_environment_overrides(self):
        return build_environment_overrides(self.get_config())

    def get_stream_options(self):
        return build_advanced_args(self.get_config())

    def get_state(self):
        return self.get_config().to_dict()

    def set_state(self, state):
        if not state:
            state = {}
        self.audio_codec_dropdown.set_selected(state.get("audio_codec", 0))
        self.param_audio_dup.set_active(state.get("audio_dup", False))
        self.audio_source_dropdown.set_selected(state.get("audio_source", 0))
        self.audio_bitrate_row.set_text(str(state.get("audio_bitrate", "") or ""))

        abuf = state.get("audio_buffer", 0)
        if isinstance(abuf, int) and 0 <= abuf < self.audio_buffer_model.get_n_items():
            self.audio_buffer_dropdown.set_selected(abuf)
        else:
            self.audio_buffer_dropdown.set_selected(0)

        self.gpu_dropdown.set_selected(state.get("gpu_adapter", 0))
        self.render_driver_dropdown.set_selected(state.get("render_driver", 0))
        self.backend_dropdown.set_selected(state.get("backend", 0))

        hw = state.get("hwdec", 0)
        if isinstance(hw, int) and 0 <= hw < self.hwdec_model.get_n_items():
            self.hwdec_dropdown.set_selected(hw)
        else:
            self.hwdec_dropdown.set_selected(0)

        self.param_no_downsize_on_error.set_active(state.get("no_downsize_on_error", False))

        buf = state.get("buffer", 0)
        if isinstance(buf, int) and 0 <= buf < self.buffer_model.get_n_items():
            self.buffer_dropdown.set_selected(buf)
        else:
            self.buffer_dropdown.set_selected(0)

        self.param_print_fps.set_active(state.get("print_fps", False))
        self.param_screen_off.set_active(state.get("screen_off", False))
        self.param_stay_awake.set_active(state.get("stay_awake", False))
        self.param_no_audio.set_active(state.get("no_audio", False))
        self.audio_section.set_no_audio(self.param_no_audio.get_active())

        self.param_read_only.set_active(state.get("read_only", False))
        self.param_keyboard_uhid.set_active(state.get("keyboard_uhid", False))
        self.param_mouse_uhid.set_active(state.get("mouse_uhid", False))
        self.param_gamepad_uhid.set_active(state.get("gamepad_uhid", False))

        mbind = state.get("mouse_bind", 0)
        if isinstance(mbind, int) and 0 <= mbind < self.mouse_bind_model.get_n_items():
            self.mouse_bind_dropdown.set_selected(mbind)
        else:
            self.mouse_bind_dropdown.set_selected(0)

        self.param_legacy_paste.set_active(state.get("legacy_paste", False))
        self.param_no_clipboard_autosync.set_active(state.get("no_clipboard_autosync", False))
        self.param_power_off_on_close.set_active(state.get("power_off_on_close", False))
        self.param_no_power_on.set_active(state.get("no_power_on", False))
        self.time_limit_row.set_text(str(state.get("time_limit", "") or ""))

        self.param_show_touches.set_active(state.get("show_touches", False))
        self.param_keep_active.set_active(state.get("keep_active", False))
        self.timeout_dropdown.set_selected(state.get("timeout", 0))
