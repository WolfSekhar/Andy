import threading
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib

from ui.cards.stream.window_section import WindowSection
from ui.cards.stream.video_section import VideoSection
from ui.cards.stream.camera_section import CameraSection
from ui.cards.stream.record_section import RecordSection

from core.config import RENDER_FITS, CAMERA_FPS_PRESETS, IME_POLICIES
from core.models import StreamConfig
from core.scrcpy_builder import build_scrcpy_args
from core.models import AdvancedConfig
from services.device_service import get_device_displays, get_device_cameras, get_device_resolution
from services.orientation_monitor import OrientationMonitor

class StreamCard(Gtk.Box):
    def __init__(self, **kwargs):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12, **kwargs)

        self.type_change_callback = None
        self.current_serial = None
        self.last_resolution = None

        # Background Orientation Monitor
        self.orientation_monitor = OrientationMonitor()
        self.stop_monitor_event = self.orientation_monitor.stop_event

        # Header
        self.label = Gtk.Label(label="Stream")
        self.label.add_css_class("title-4")
        self.label.set_halign(Gtk.Align.CENTER)
        self.append(self.label)

        # Main Stream Options Group
        self.main_group = Adw.PreferencesGroup()
        self.append(self.main_group)

        # Type Selection Row
        self.type_row = Adw.ActionRow(title="Type ->")
        self.type_model = Gtk.StringList()
        self.type_model.append("Screen")
        self.type_model.append("Camera")
        self.type_dropdown = Gtk.DropDown(model=self.type_model)
        self.type_dropdown.set_valign(Gtk.Align.CENTER)
        self.type_dropdown.connect("notify::selected", self.on_type_changed)
        self.type_row.add_suffix(self.type_dropdown)
        self.main_group.add(self.type_row)

        self.param_start_app = Adw.EntryRow(title="Start App (Package Name)")
        self.main_group.add(self.param_start_app)

        # Stack for dynamic options based on Type
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.append(self.stack)

        # Screen Options Page
        self.screen_page = Adw.PreferencesGroup()
        self.stack.add_named(self.screen_page, "screen")

        self.select_row = Adw.ActionRow(title="Select Display")
        self.display_model = Gtk.StringList()
        self.display_dropdown = Gtk.DropDown(model=self.display_model)
        self.display_dropdown.set_valign(Gtk.Align.CENTER)
        self.select_row.add_suffix(self.display_dropdown)
        self.screen_page.add(self.select_row)

        self.param_new_display = Adw.SwitchRow(
            title="Virtual Display Mode",
            subtitle="Create new secondary virtual display (Android 13+)"
        )
        self.screen_page.add(self.param_new_display)

        self.param_flex_display = Adw.SwitchRow(
            title="Flex Display",
            subtitle="Allow dynamic display resizing for virtual display"
        )
        self.screen_page.add(self.param_flex_display)

        self.display_ime_policy_model = Gtk.StringList()
        for p in IME_POLICIES:
            self.display_ime_policy_model.append(p)
        self.param_display_ime_policy = Adw.ComboRow(
            title="Virtual Display IME Policy",
            model=self.display_ime_policy_model
        )
        self.param_display_ime_policy.dropdown = self.param_display_ime_policy
        self.display_ime_policy_row = self.param_display_ime_policy
        self.display_ime_policy_dropdown = self.param_display_ime_policy
        self.screen_page.add(self.param_display_ime_policy)

        self.param_no_vd_destroy_content = Adw.SwitchRow(
            title="Preserve Display Content",
            subtitle="Do not destroy content when virtual display closes"
        )
        self.screen_page.add(self.param_no_vd_destroy_content)

        # Camera Options Page
        self.camera_section = CameraSection()
        self.stack.add_named(self.camera_section, "camera")
        self.camera_row = self.camera_section.camera_row
        self.camera_model = self.camera_section.camera_model
        self.camera_dropdown = self.camera_section.camera_dropdown
        self.camera_dropdown.connect("notify::selected", self.on_camera_selected)
        self.param_camera_torch = self.camera_section.param_camera_torch
        self.param_camera_fps = self.camera_section.param_camera_fps
        self.camera_fps_dropdown = self.camera_section.camera_fps_dropdown
        self.param_camera_high_speed = self.camera_section.param_camera_high_speed
        self.param_camera_zoom = self.camera_section.param_camera_zoom

        # Window Settings
        self.window_section = WindowSection()
        self.append(self.window_section)
        self.window_group = self.window_section
        self.param_fullscreen = self.window_section.param_fullscreen
        self.param_borderless = self.window_section.param_borderless
        self.param_always_on_top = self.window_section.param_always_on_top
        self.param_disable_screensaver = self.window_section.param_disable_screensaver
        self.param_render_fit = self.window_section.param_render_fit
        self.render_fit_dropdown = self.window_section.render_fit_dropdown

        # Video Settings
        self.video_section = VideoSection()
        self.append(self.video_section)
        self.video_group = self.video_section
        self.codec_row = self.video_section.codec_row
        self.codec_model = self.video_section.codec_model
        self.codec_dropdown = self.video_section.codec_dropdown
        self.fps_row = self.video_section.fps_row
        self.fps_combo = self.video_section.fps_combo
        self.size_row = self.video_section.size_row
        self.size_combo = self.video_section.size_combo
        self.bitrate_row = self.video_section.bitrate_row
        self.orient_row = self.video_section.orient_row
        self.orient_model = self.video_section.orient_model
        self.orient_dropdown = self.video_section.orient_dropdown

        # Recording Settings
        self.record_section = RecordSection()
        self.append(self.record_section)
        self.record_group = self.record_section
        self.param_record = self.record_section.param_record
        self.record_format_row = self.record_section.record_format_row
        self.record_format_model = self.record_section.record_format_model
        self.record_format_dropdown = self.record_section.record_format_dropdown

        self.stack.set_visible_child_name("screen")

    def reset_size_dropdown(self):
        self.video_section.reset_size_dropdown()

    def on_type_changed(self, dropdown, pspec):
        is_camera = (dropdown.get_selected() == 1)
        if is_camera:
            self.stack.set_visible_child_name("camera")
            self.update_resolution_for_camera()
        else:
            self.stack.set_visible_child_name("screen")
            if self.last_resolution:
                self.video_section.update_resolution_ui(self.last_resolution, is_camera_mode=False)

        if self.type_change_callback:
            self.type_change_callback(is_camera)

    def on_camera_selected(self, dropdown, pspec):
        if self.type_dropdown.get_selected() == 1:
            self.update_resolution_for_camera()

    def update_resolution_for_camera(self):
        res = self.camera_section.get_selected_camera_resolution()
        self.video_section.update_resolution_ui(res, is_camera_mode=False)

    def update_resolution_ui(self, resolution):
        is_cam = (self.type_dropdown.get_selected() != 0)
        return self.video_section.update_resolution_ui(resolution, is_camera_mode=is_cam)

    def update_displays(self, serial: str):
        self.current_serial = serial
        self.orientation_monitor.stop()
        self.last_resolution = None

        n_items = self.display_model.get_n_items()
        self.display_model.splice(0, n_items, ["Loading..."])
        self.display_dropdown.set_sensitive(False)

        n_cam_items = self.camera_model.get_n_items()
        self.camera_model.splice(0, n_cam_items, ["Loading..."])
        self.camera_dropdown.set_sensitive(False)

        self.size_combo.get_child().set_text("Calculating...")
        self.size_combo.set_sensitive(False)

        def fetch(target_serial):
            displays = get_device_displays(target_serial)
            cameras = get_device_cameras(target_serial)
            resolution = get_device_resolution(target_serial)

            if self.current_serial != target_serial:
                return

            GLib.idle_add(self.apply_data, displays, cameras, resolution)

            if target_serial and target_serial != "No devices found":
                self.orientation_monitor.start(
                    target_serial,
                    lambda res: self.on_orientation_changed(res)
                )

        threading.Thread(target=fetch, args=(serial,), daemon=True).start()

    def on_orientation_changed(self, resolution):
        self.last_resolution = resolution
        self.update_resolution_ui(resolution)

    def apply_data(self, displays, cameras, resolution):
        n_items = self.display_model.get_n_items()
        self.display_model.splice(0, n_items, [])
        if not displays:
            self.display_model.append("0 (Default)")
            self.display_dropdown.set_sensitive(False)
        else:
            for d in displays:
                self.display_model.append(d)
            self.display_dropdown.set_sensitive(True)

        self.camera_section.apply_cameras(cameras)

        self.last_resolution = resolution
        if self.type_dropdown.get_selected() == 1:
            self.update_resolution_for_camera()
        elif resolution:
            self.video_section.update_resolution_ui(resolution, is_camera_mode=False)
            self.size_combo.set_sensitive(True)
        else:
            self.size_combo.remove_all()
            self.size_combo.append_text("Default")
            for s in ["1920", "1280", "1024"]:
                self.size_combo.append_text(s)
            self.size_combo.set_active(0)
            self.size_combo.set_sensitive(True)

        return False

    def get_stream_options(self):
        cfg = StreamConfig(
            type=self.type_dropdown.get_selected(),
            camera=self.camera_dropdown.get_selected(),
            display=self.display_dropdown.get_selected(),
            fullscreen=self.param_fullscreen.get_active(),
            borderless=self.param_borderless.get_active(),
            always_on_top=self.param_always_on_top.get_active(),
            disable_screensaver=self.param_disable_screensaver.get_active(),
            codec=self.codec_dropdown.get_selected(),
            fps=self.fps_combo.get_active_text() or self.fps_combo.get_child().get_text(),
            size=self.size_combo.get_active_text() or self.size_combo.get_child().get_text(),
            bitrate=self.bitrate_row.get_text(),
            orientation=self.orient_dropdown.get_selected(),
            record=self.param_record.get_active(),
            record_format=self.record_format_dropdown.get_selected(),
            new_display=self.param_new_display.get_active(),
            camera_torch=self.param_camera_torch.get_active(),
            flex_display=self.param_flex_display.get_active(),
            render_fit=self.param_render_fit.get_selected(),
            display_ime_policy=self.param_display_ime_policy.get_selected(),
            no_vd_destroy_content=self.param_no_vd_destroy_content.get_active(),
            start_app=self.param_start_app.get_text(),
            camera_zoom=self.param_camera_zoom.get_text(),
            camera_fps=self.param_camera_fps.get_selected(),
            camera_high_speed=self.param_camera_high_speed.get_active()
        )

        # Get active display / camera strings if selected
        display_str = None
        d_idx = self.display_dropdown.get_selected()
        if d_idx != Gtk.INVALID_LIST_POSITION and self.display_model.get_n_items() > 0:
            display_str = self.display_model.get_string(d_idx)

        camera_str = None
        c_idx = self.camera_dropdown.get_selected()
        if c_idx != Gtk.INVALID_LIST_POSITION and self.camera_model.get_n_items() > 0:
            camera_str = self.camera_model.get_string(c_idx)

        # Delegate pure option generation to scrcpy_builder
        adv_dummy = AdvancedConfig()
        all_options = build_scrcpy_args(
            serial=self.current_serial or "",
            stream=cfg,
            advanced=adv_dummy,
            mode="stream",
            camera_id_str=camera_str,
            display_id_str=display_str
        )
        return all_options

    def get_state(self):
        return {
            "type": self.type_dropdown.get_selected(),
            "camera": self.camera_dropdown.get_selected(),
            "display": self.display_dropdown.get_selected(),
            "fullscreen": self.param_fullscreen.get_active(),
            "borderless": self.param_borderless.get_active(),
            "always_on_top": self.param_always_on_top.get_active(),
            "disable_screensaver": self.param_disable_screensaver.get_active(),
            "codec": self.codec_dropdown.get_selected(),
            "fps": self.fps_combo.get_active_text() or self.fps_combo.get_child().get_text(),
            "size": self.size_combo.get_active_text() or self.size_combo.get_child().get_text(),
            "bitrate": self.bitrate_row.get_text(),
            "orientation": self.orient_dropdown.get_selected(),
            "record": self.param_record.get_active(),
            "record_format": self.record_format_dropdown.get_selected(),
            "new_display": self.param_new_display.get_active(),
            "camera_torch": self.param_camera_torch.get_active(),
            "flex_display": self.param_flex_display.get_active(),
            "render_fit": self.param_render_fit.get_selected(),
            "display_ime_policy": self.param_display_ime_policy.get_selected(),
            "no_vd_destroy_content": self.param_no_vd_destroy_content.get_active(),
            "start_app": self.param_start_app.get_text(),
            "camera_zoom": self.param_camera_zoom.get_text(),
            "camera_fps": self.param_camera_fps.get_selected(),
            "camera_high_speed": self.param_camera_high_speed.get_active()
        }

    def set_state(self, state):
        self.type_dropdown.set_selected(state.get("type", 0))
        self.camera_dropdown.set_selected(state.get("camera", 0))
        self.display_dropdown.set_selected(state.get("display", 0))
        self.param_fullscreen.set_active(state.get("fullscreen", False))
        self.param_borderless.set_active(state.get("borderless", False))
        self.param_always_on_top.set_active(state.get("always_on_top", False))
        self.param_disable_screensaver.set_active(state.get("disable_screensaver", False))
        self.codec_dropdown.set_selected(state.get("codec", 0))

        fps = state.get("fps", "Default")
        if isinstance(fps, int):
            fps_presets = ["Default", "60", "30", "15"]
            fps = fps_presets[fps] if 0 <= fps < len(fps_presets) else "Default"
        self.fps_combo.get_child().set_text(str(fps))

        size = state.get("size", "Default")
        if isinstance(size, int):
            size_presets = ["Default", "3840", "2560", "1920", "1280", "1024"]
            size = size_presets[size] if 0 <= size < len(size_presets) else "Default"
        self.size_combo.get_child().set_text(str(size))

        self.bitrate_row.set_text(str(state.get("bitrate", "")))
        self.orient_dropdown.set_selected(state.get("orientation", 0))
        self.param_record.set_active(state.get("record", False))
        self.record_format_dropdown.set_selected(state.get("record_format", 0))
        self.record_format_row.set_sensitive(self.param_record.get_active())
        self.param_new_display.set_active(state.get("new_display", False))
        self.param_camera_torch.set_active(state.get("camera_torch", False))

        # scrcpy 5.0 additions
        render_fit = state.get("render_fit", 0)
        if isinstance(render_fit, str) and render_fit in RENDER_FITS:
            render_fit = RENDER_FITS.index(render_fit)
        elif not isinstance(render_fit, int) or not (0 <= render_fit < len(RENDER_FITS)):
            render_fit = 0
        self.param_render_fit.set_selected(render_fit)

        camera_fps = state.get("camera_fps", 0)
        if isinstance(camera_fps, str) and camera_fps in CAMERA_FPS_PRESETS:
            camera_fps = CAMERA_FPS_PRESETS.index(camera_fps)
        elif not isinstance(camera_fps, int) or not (0 <= camera_fps < len(CAMERA_FPS_PRESETS)):
            camera_fps = 0
        self.param_camera_fps.set_selected(camera_fps)

        self.param_camera_high_speed.set_active(bool(state.get("camera_high_speed", False)))
        self.param_camera_zoom.set_text(str(state.get("camera_zoom") or ""))

        self.param_flex_display.set_active(bool(state.get("flex_display", False)))

        display_ime_policy = state.get("display_ime_policy", 0)
        if isinstance(display_ime_policy, str) and display_ime_policy in IME_POLICIES:
            display_ime_policy = IME_POLICIES.index(display_ime_policy)
        elif not isinstance(display_ime_policy, int) or not (0 <= display_ime_policy < len(IME_POLICIES)):
            display_ime_policy = 0
        self.param_display_ime_policy.set_selected(display_ime_policy)

        self.param_no_vd_destroy_content.set_active(bool(state.get("no_vd_destroy_content", False)))
        self.param_start_app.set_text(str(state.get("start_app") or ""))
