import os
import sys
import time
import re
import threading
from typing import List, Dict, Any, Optional

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gdk, Gio

try:
    from ui.layouts.base_layout import BaseLayout
except ImportError:
    try:
        from .base_layout import BaseLayout
    except ImportError:
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
        from ui.layouts.base_layout import BaseLayout

try:
    from services.device_service import (
        get_detailed_device_info,
        get_device_displays,
        get_device_cameras,
        get_device_resolution
    )
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
    from services.host_telemetry import get_host_telemetry
    from services.profile_service import list_profiles, load_profile, save_profile
    from core.config import DEFAULT_RECORDINGS_DIR
except ImportError:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
    from services.device_service import (
        get_detailed_device_info,
        get_device_displays,
        get_device_cameras,
        get_device_resolution
    )
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
    from services.host_telemetry import get_host_telemetry
    from services.profile_service import list_profiles, load_profile, save_profile
    from core.config import DEFAULT_RECORDINGS_DIR


class ModularHubLayout(BaseLayout):
    """
    Option 4: The Modular Card Hub (Fragments / Pods Style) Layout for Andy.
    Features:
      - Top interactive Profile Chips bar (Default, Work, Gaming, Webcam, Broken Screen + Custom)
      - 3 Refined Card Pods:
          1. Stream & Display (segmented source switcher, virtual display & flex expander)
          2. Engine & Peripherals (HWDEC, audio forwarding, UHID input & lifecycle)
          3. Device & Telemetry (LevelBar battery gauge, density station, remote navigation & tools)
      - Escaped ampersands throughout all Libadwaita markup.
      - Full integration hooks wired to parent AndyWindow.
    """

    PRESET_PROFILES = [
        ("★ Default", "default"),
        ("💼 Office Work", "work"),
        ("🎮 Gaming 120Hz", "gaming"),
        ("📷 Camera Webcam", "webcam"),
        ("📱 Broken Screen", "broken_screen"),
    ]

    def __init__(self, window: Any = None):
        super().__init__(window=window)

        self.current_serial: Optional[str] = None
        self.current_density: Optional[int] = None
        self.chip_buttons: Dict[Gtk.ToggleButton, str] = {}
        self.is_updating_chips: bool = False

        self.container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.container.set_vexpand(True)
        self.container.set_hexpand(True)

        self._build_ui()

    def get_widget(self) -> Gtk.Widget:
        """Return the top-level container widget for this layout."""
        return self.container

    def _build_ui(self):
        # Main scroll container
        self.scroll = Gtk.ScrolledWindow()
        self.scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scroll.set_vexpand(True)
        self.scroll.set_hexpand(True)
        self.container.append(self.scroll)

        # Central Box
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        self.main_box.set_margin_top(14)
        self.main_box.set_margin_bottom(20)
        self.main_box.set_margin_start(16)
        self.main_box.set_margin_end(16)
        self.scroll.set_child(self.main_box)

        # ---------------------------------------------------------------------
        # 1. TOP INTERACTIVE PROFILE CHIPS BAR
        # ---------------------------------------------------------------------
        self._build_profile_chips_bar()

        # ---------------------------------------------------------------------
        # 2. REFINED 3-POD CARD GRID (Gtk.FlowBox)
        # ---------------------------------------------------------------------
        self.flow = Gtk.FlowBox()
        self.flow.set_selection_mode(Gtk.SelectionMode.NONE)
        self.flow.set_homogeneous(False)
        self.flow.set_column_spacing(18)
        self.flow.set_row_spacing(18)
        self.flow.set_min_children_per_line(1)
        self.flow.set_max_children_per_line(3)
        self.flow.set_valign(Gtk.Align.START)
        self.flow.set_halign(Gtk.Align.FILL)
        self.flow.set_hexpand(True)
        self.main_box.append(self.flow)

        # Build the 3 Pods
        self._build_pod_stream_display()
        self._build_pod_engine_peripherals()
        self._build_pod_device_telemetry()

    # =========================================================================
    # POD 1: Stream & Display
    # =========================================================================
    def _build_pod_stream_display(self):
        self.pod1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.pod1.add_css_class("card")
        self.pod1.set_size_request(310, -1)
        self.pod1.set_margin_top(4)
        self.pod1.set_hexpand(True)

        head1 = Adw.ActionRow(
            title="Stream &amp; Display",
            subtitle="Video engine &amp; output geometry"
        )
        head1.add_prefix(Gtk.Image.new_from_icon_name("video-display-symbolic"))
        self.pod1.append(head1)

        # Segmented Source Switcher (Screen vs Camera)
        src_row = Adw.ActionRow(title="Capture Source")
        src_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        src_box.add_css_class("linked")
        src_box.set_valign(Gtk.Align.CENTER)

        self.btn_src_screen = Gtk.ToggleButton(label="Screen", active=True)
        self.btn_src_camera = Gtk.ToggleButton(label="Camera", active=False)
        self.btn_src_screen.connect("toggled", self._on_src_screen_toggled)
        self.btn_src_camera.connect("toggled", self._on_src_camera_toggled)

        src_box.append(self.btn_src_screen)
        src_box.append(self.btn_src_camera)
        src_row.add_suffix(src_box)
        self.pod1.append(src_row)

        # Active Display dropdown
        self.display_model = Gtk.StringList.new(["Display 0 (Internal)", "Virtual Secondary"])
        self.combo_display = Adw.ComboRow(title="Active Display", model=self.display_model)
        self.pod1.append(self.combo_display)

        # Render Fit
        self.render_fit_model = Gtk.StringList.new(["Default", "Letterbox", "Stretched", "Unscaled"])
        self.combo_render_fit = Adw.ComboRow(title="Render Fit", model=self.render_fit_model)
        self.pod1.append(self.combo_render_fit)

        # Resolution Scale
        self.res_model = Gtk.StringList.new(["Native", "1920 (80%)", "1280 (60%)", "1024 (40%)"])
        self.combo_res_scale = Adw.ComboRow(title="Resolution Scale", model=self.res_model)
        self.pod1.append(self.combo_res_scale)

        # Max Framerate
        self.fps_model = Gtk.StringList.new(["Default", "60 FPS", "120 FPS", "90 FPS", "30 FPS"])
        self.combo_max_fps = Adw.ComboRow(title="Max Framerate", model=self.fps_model)
        self.combo_max_fps.set_selected(1)  # 60 FPS default
        self.pod1.append(self.combo_max_fps)

        # Video Codec
        self.codec_model = Gtk.StringList.new(["Default (Auto)", "H.265 (HEVC)", "H.264", "AV1"])
        self.combo_video_codec = Adw.ComboRow(title="Video Codec", model=self.codec_model)
        self.pod1.append(self.combo_video_codec)

        # Expander for scrcpy 5.0 Virtual Display
        self.exp_vd = Adw.ExpanderRow(title="Virtual Display &amp; Flex (scrcpy 5.0)")
        self.switch_vd_mode = Adw.SwitchRow(title="Virtual Display Mode")
        self.switch_flex_display = Adw.SwitchRow(title="Flex Display (Dynamic Resize)")
        self.combo_ime_policy = Adw.ComboRow(
            title="IME Policy",
            model=Gtk.StringList.new(["Local", "Fallback", "Hide"])
        )
        self.switch_no_vd_destroy = Adw.SwitchRow(title="No Destroy Content")
        self.exp_vd.add_row(self.switch_vd_mode)
        self.exp_vd.add_row(self.switch_flex_display)
        self.exp_vd.add_row(self.combo_ime_policy)
        self.exp_vd.add_row(self.switch_no_vd_destroy)
        self.pod1.append(self.exp_vd)

        # Expander for Window & Record
        self.exp_win = Adw.ExpanderRow(title="Window &amp; Record")
        self.switch_fullscreen = Adw.SwitchRow(title="Fullscreen")
        self.switch_always_on_top = Adw.SwitchRow(title="Always On Top")
        self.switch_borderless = Adw.SwitchRow(title="Borderless")
        self.switch_record = Adw.SwitchRow(title="Record MP4")
        self.exp_win.add_row(self.switch_fullscreen)
        self.exp_win.add_row(self.switch_always_on_top)
        self.exp_win.add_row(self.switch_borderless)
        self.exp_win.add_row(self.switch_record)
        self.pod1.append(self.exp_win)

        self.flow.append(self.pod1)

    # =========================================================================
    # POD 2: Engine & Peripherals
    # =========================================================================
    def _build_pod_engine_peripherals(self):
        self.pod2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.pod2.add_css_class("card")
        self.pod2.set_size_request(310, -1)
        self.pod2.set_margin_top(4)
        self.pod2.set_hexpand(True)

        head2 = Adw.ActionRow(
            title="Engine &amp; Peripherals",
            subtitle="HWDEC, Audio &amp; HID passthrough"
        )
        head2.add_prefix(Gtk.Image.new_from_icon_name("applications-utilities-symbolic"))
        self.pod2.append(head2)

        # Hardware Video Decoding
        self.hwdec_model = Gtk.StringList.new([
            "Default (Auto)", "vaapi (VA-API)", "vdpau", "dxva2", "nvdec", "disabled"
        ])
        self.combo_hwdec = Adw.ComboRow(title="Hardware Video Decoding", model=self.hwdec_model)
        self.pod2.append(self.combo_hwdec)

        # Audio Expander
        self.exp_aud = Adw.ExpanderRow(title="Audio Forwarding Engine")
        self.switch_audio_fwd = Adw.SwitchRow(title="Forward Audio", active=True)
        self.combo_audio_codec = Adw.ComboRow(
            title="Audio Codec",
            model=Gtk.StringList.new(["Opus (Recommended)", "AAC", "FLAC", "RAW"])
        )
        self.audio_buffer_model = Gtk.StringList.new([
            "20 ms (Ultra Low)", "50 ms (Normal)", "100 ms", "200 ms"
        ])
        self.combo_audio_buffer = Adw.ComboRow(
            title="Audio Buffer Latency",
            model=self.audio_buffer_model
        )
        self.combo_audio_buffer.set_selected(1)  # 50 ms default
        self.switch_audio_dup = Adw.SwitchRow(title="Duplicate Audio (Phone+PC)")

        self.exp_aud.add_row(self.switch_audio_fwd)
        self.exp_aud.add_row(self.combo_audio_codec)
        self.exp_aud.add_row(self.combo_audio_buffer)
        self.exp_aud.add_row(self.switch_audio_dup)
        self.pod2.append(self.exp_aud)

        # Input & Peripherals (UHID) Expander
        self.exp_hid = Adw.ExpanderRow(title="Input &amp; Peripherals (UHID)")
        self.switch_keyboard_uhid = Adw.SwitchRow(title="Keyboard UHID Mode")
        self.switch_mouse_uhid = Adw.SwitchRow(title="Mouse UHID Mode")
        self.switch_gamepad_uhid = Adw.SwitchRow(title="Gamepad Forwarding (UHID)")
        self.combo_mouse_scheme = Adw.ComboRow(
            title="Mouse Button Scheme",
            model=Gtk.StringList.new(["Default", "Gaming (++++)", "Android (bhsn)"])
        )
        self.exp_hid.add_row(self.switch_keyboard_uhid)
        self.exp_hid.add_row(self.switch_mouse_uhid)
        self.exp_hid.add_row(self.switch_gamepad_uhid)
        self.exp_hid.add_row(self.combo_mouse_scheme)
        self.pod2.append(self.exp_hid)

        # Device Lifecycle & Power Expander
        self.exp_life = Adw.ExpanderRow(title="Device Lifecycle &amp; Power")
        self.switch_screen_off = Adw.SwitchRow(title="Turn Screen Off During Stream", active=True)
        self.switch_stay_awake = Adw.SwitchRow(title="Stay Awake", active=True)
        self.switch_power_off_close = Adw.SwitchRow(title="Power Off on Close")
        self.exp_life.add_row(self.switch_screen_off)
        self.exp_life.add_row(self.switch_stay_awake)
        self.exp_life.add_row(self.switch_power_off_close)
        self.pod2.append(self.exp_life)

        self.flow.append(self.pod2)

    # =========================================================================
    # POD 3: Device Control & Telemetry
    # =========================================================================
    def _build_pod_device_telemetry(self):
        self.pod3 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.pod3.add_css_class("card")
        self.pod3.set_size_request(310, -1)
        self.pod3.set_margin_top(4)
        self.pod3.set_hexpand(True)

        self.head3 = Adw.ActionRow(
            title="Device &amp; Telemetry",
            subtitle="No device connected"
        )
        self.head3.add_prefix(Gtk.Image.new_from_icon_name("phone-symbolic"))
        self.pod3.append(self.head3)

        # Battery Status Row with LevelBar
        self.row_battery = Adw.ActionRow(title="Battery Status", subtitle="N/A")
        self.battery_icon = Gtk.Image.new_from_icon_name("battery-symbolic")
        self.row_battery.add_prefix(self.battery_icon)

        self.level_battery = Gtk.LevelBar(min_value=0.0, max_value=100.0, value=0.0)
        self.level_battery.set_size_request(80, 8)
        self.level_battery.set_valign(Gtk.Align.CENTER)
        self.row_battery.add_suffix(self.level_battery)
        self.pod3.append(self.row_battery)

        # Density Station (-20, Reset, +20)
        self.row_density = Adw.ActionRow(title="Display Density (N/A)")
        self.row_density.add_prefix(Gtk.Image.new_from_icon_name("display-symbolic"))
        self.box_density = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.box_density.add_css_class("linked")
        self.box_density.set_valign(Gtk.Align.CENTER)

        self.btn_dpi_down = Gtk.Button(label="-20")
        self.btn_dpi_down.set_tooltip_text("Decrease Display Density (-20 DPI)")
        self.btn_dpi_down.connect("clicked", lambda b: self.on_density_adjust(-20))

        self.btn_dpi_reset = Gtk.Button(label="Reset")
        self.btn_dpi_reset.set_tooltip_text("Reset Display Density to physical default")
        self.btn_dpi_reset.connect("clicked", lambda b: self.on_density_reset())

        self.btn_dpi_up = Gtk.Button(label="+20")
        self.btn_dpi_up.set_tooltip_text("Increase Display Density (+20 DPI)")
        self.btn_dpi_up.connect("clicked", lambda b: self.on_density_adjust(20))

        self.box_density.append(self.btn_dpi_down)
        self.box_density.append(self.btn_dpi_reset)
        self.box_density.append(self.btn_dpi_up)
        self.row_density.add_suffix(self.box_density)
        self.pod3.append(self.row_density)

        # Remote Navigation Pad (Back, Home, Recents, Notifications)
        self.row_nav = Adw.ActionRow(title="Remote Navigation")
        self.row_nav.add_prefix(Gtk.Image.new_from_icon_name("input-keyboard-symbolic"))
        self.box_nav = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.box_nav.set_valign(Gtk.Align.CENTER)

        self.btn_back = Gtk.Button(icon_name="go-previous-symbolic", tooltip_text="Back (KEYCODE_BACK)")
        self.btn_back.connect("clicked", lambda b: self._execute_remote_keyevent(4, "Back"))

        self.btn_home = Gtk.Button(icon_name="user-home-symbolic", tooltip_text="Home (KEYCODE_HOME)")
        self.btn_home.connect("clicked", lambda b: self._execute_remote_keyevent(3, "Home"))

        self.btn_recents = Gtk.Button(icon_name="view-grid-symbolic", tooltip_text="Recents (KEYCODE_APP_SWITCH)")
        self.btn_recents.connect("clicked", lambda b: self._execute_remote_keyevent(187, "Recents"))

        self.btn_notif = Gtk.Button(icon_name="preferences-system-notifications-symbolic", tooltip_text="Notifications Shade")
        self.btn_notif.connect("clicked", lambda b: self._execute_remote_statusbar("notifications"))

        self.box_nav.append(self.btn_back)
        self.box_nav.append(self.btn_home)
        self.box_nav.append(self.btn_recents)
        self.box_nav.append(self.btn_notif)
        self.row_nav.add_suffix(self.box_nav)
        self.pod3.append(self.row_nav)

        # Remote Tool Actions (Paste, Screenshot, Power, Reboot)
        self.row_tools = Adw.ActionRow(title="Remote Tools")
        self.row_tools.add_prefix(Gtk.Image.new_from_icon_name("system-run-symbolic"))
        self.box_tools = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.box_tools.set_valign(Gtk.Align.CENTER)

        self.btn_paste = Gtk.Button(icon_name="edit-paste-symbolic", tooltip_text="Paste PC Clipboard to Phone")
        self.btn_paste.connect("clicked", lambda b: self._execute_remote_paste())

        self.btn_screenshot = Gtk.Button(icon_name="camera-photo-symbolic", tooltip_text="Take Screenshot")
        self.btn_screenshot.connect("clicked", lambda b: self._execute_remote_screenshot())

        self.btn_power = Gtk.Button(icon_name="system-shutdown-symbolic", tooltip_text="Power Button (Wake/Sleep)")
        self.btn_power.connect("clicked", lambda b: self._execute_remote_power())

        self.btn_reboot = Gtk.Button(icon_name="system-reboot-symbolic", tooltip_text="Reboot Menu")
        self.btn_reboot.connect("clicked", lambda b: self._execute_remote_reboot())

        self.box_tools.append(self.btn_paste)
        self.box_tools.append(self.btn_screenshot)
        self.box_tools.append(self.btn_power)
        self.box_tools.append(self.btn_reboot)
        self.row_tools.add_suffix(self.box_tools)
        self.pod3.append(self.row_tools)

        # Host & Wayland Telemetry
        self.row_telemetry = Adw.ActionRow(
            title="Host &amp; Wayland Telemetry",
            subtitle="Wayland"
        )
        self.row_telemetry.add_prefix(Gtk.Image.new_from_icon_name("preferences-desktop-display-symbolic"))
        self.pod3.append(self.row_telemetry)
        self._load_host_telemetry()

        # Feedback / Status Caption
        self.status_label = Gtk.Label(label="", halign=Gtk.Align.CENTER)
        self.status_label.add_css_class("dim-label")
        self.status_label.add_css_class("caption")
        self.pod3.append(self.status_label)

        self.flow.append(self.pod3)

    # =========================================================================
    # PROFILE CHIPS BAR
    # =========================================================================
    def _build_profile_chips_bar(self):
        self.chips_scroll = Gtk.ScrolledWindow(
            vscrollbar_policy=Gtk.PolicyType.NEVER,
            hscrollbar_policy=Gtk.PolicyType.AUTOMATIC
        )
        self.chips_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.chips_box.set_margin_bottom(6)
        self.chips_scroll.set_child(self.chips_box)
        self.main_box.append(self.chips_scroll)

        self.refresh_profile_chips()

    def refresh_profile_chips(self, active_profile_name: str = "default"):
        # Clear existing
        while child := self.chips_box.get_first_child():
            self.chips_box.remove(child)
        self.chip_buttons.clear()

        # Add presets
        for label, p_id in self.PRESET_PROFILES:
            btn = Gtk.ToggleButton(label=label)
            btn.add_css_class("pill")
            is_active = (p_id == active_profile_name)
            if is_active:
                btn.set_active(True)
                btn.add_css_class("suggested-action")
            btn.connect("toggled", self._on_chip_toggled)
            self.chips_box.append(btn)
            self.chip_buttons[btn] = p_id

        # Add custom profiles from disk
        saved = list_profiles()
        for s_name in saved:
            btn = Gtk.ToggleButton(label=f"⚙ {s_name}")
            btn.add_css_class("pill")
            is_active = (s_name == active_profile_name)
            if is_active:
                btn.set_active(True)
                btn.add_css_class("suggested-action")
            btn.connect("toggled", self._on_chip_toggled)
            self.chips_box.append(btn)
            self.chip_buttons[btn] = s_name

        # Save Current Button
        self.btn_save_current = Gtk.Button(label="+ Save Current", icon_name="document-save-symbolic")
        self.btn_save_current.add_css_class("pill")
        self.btn_save_current.connect("clicked", self._on_save_current_clicked)
        self.chips_box.append(self.btn_save_current)

    def refresh_profiles(self, select_name: Optional[str] = None) -> None:
        """Lifecycle hook to refresh profiles listing."""
        self.refresh_profile_chips(active_profile_name=select_name or "default")

    def _on_chip_toggled(self, active_btn: Gtk.ToggleButton):
        if self.is_updating_chips:
            return

        if not active_btn.get_active():
            # Keep at least one chip selected
            has_active = any(b.get_active() for b in self.chip_buttons)
            if not has_active:
                active_btn.set_active(True)
            return

        self.is_updating_chips = True
        try:
            for btn in self.chip_buttons:
                if btn != active_btn:
                    btn.set_active(False)
                    btn.remove_css_class("suggested-action")
            active_btn.add_css_class("suggested-action")
        finally:
            self.is_updating_chips = False

        profile_key = self.chip_buttons.get(active_btn, "default")
        self.apply_profile(profile_key)

    def apply_profile(self, profile_key: str):
        if profile_key == "default":
            self.set_state({
                "source": "screen",
                "max_fps": 1,  # 60 FPS
                "video_codec": 0,  # Default
                "render_fit": 0,
                "res_scale": 0,  # Native
                "vd_mode": False,
                "flex_display": False,
                "fullscreen": False,
                "always_on_top": False,
                "borderless": False,
                "record": False,
                "hwdec": 0,  # Default
                "audio_fwd": True,
                "audio_codec": 0,  # Opus
                "audio_buffer": 1,  # 50 ms
                "audio_dup": False,
                "keyboard_uhid": False,
                "mouse_uhid": False,
                "gamepad_uhid": False,
                "mouse_scheme": 0,
                "screen_off": True,
                "stay_awake": True,
                "power_off_close": False,
            })
        elif profile_key == "work":
            self.set_state({
                "source": "screen",
                "max_fps": 1,  # 60 FPS
                "video_codec": 2,  # H.264
                "render_fit": 0,
                "res_scale": 0,
                "vd_mode": False,
                "flex_display": False,
                "fullscreen": False,
                "always_on_top": True,
                "borderless": False,
                "record": False,
                "hwdec": 1,  # vaapi
                "audio_fwd": False,
                "keyboard_uhid": True,
                "mouse_uhid": True,
                "gamepad_uhid": False,
                "mouse_scheme": 0,
                "screen_off": True,
                "stay_awake": True,
                "power_off_close": False,
            })
        elif profile_key == "gaming":
            self.set_state({
                "source": "screen",
                "max_fps": 2,  # 120 FPS
                "video_codec": 1,  # H.265 (HEVC)
                "render_fit": 0,
                "res_scale": 0,
                "vd_mode": False,
                "flex_display": False,
                "fullscreen": True,
                "always_on_top": False,
                "borderless": False,
                "record": False,
                "hwdec": 1,  # vaapi
                "audio_fwd": True,
                "audio_codec": 0,  # Opus
                "audio_buffer": 0,  # 20 ms
                "audio_dup": False,
                "keyboard_uhid": True,
                "mouse_uhid": True,
                "gamepad_uhid": True,
                "mouse_scheme": 1,  # Gaming (++++)
                "screen_off": True,
                "stay_awake": True,
                "power_off_close": False,
            })
        elif profile_key == "webcam":
            self.set_state({
                "source": "camera",
                "max_fps": 1,  # 60 FPS
                "video_codec": 2,  # H.264
                "render_fit": 0,
                "res_scale": 1,  # 1920
                "vd_mode": False,
                "flex_display": False,
                "fullscreen": False,
                "always_on_top": True,
                "borderless": False,
                "record": False,
                "hwdec": 0,
                "audio_fwd": True,
                "keyboard_uhid": False,
                "mouse_uhid": False,
                "gamepad_uhid": False,
                "screen_off": False,
                "stay_awake": True,
                "power_off_close": False,
            })
        elif profile_key == "broken_screen":
            self.set_state({
                "source": "screen",
                "max_fps": 1,  # 60 FPS
                "video_codec": 0,
                "render_fit": 0,
                "res_scale": 0,
                "vd_mode": False,
                "flex_display": False,
                "fullscreen": False,
                "always_on_top": True,
                "borderless": False,
                "record": False,
                "hwdec": 0,
                "audio_fwd": True,
                "keyboard_uhid": True,
                "mouse_uhid": True,
                "gamepad_uhid": False,
                "screen_off": False,
                "stay_awake": True,
                "power_off_close": False,
            })
        else:
            # Custom profile from disk
            state = load_profile(profile_key)
            if state:
                self.set_state(state)

        self.status_label.set_text(f"Profile: {profile_key.replace('_', ' ').title()}")

    def _on_save_current_clicked(self, button):
        if self.window and hasattr(self.window, "on_save_profile_clicked"):
            self.window.on_save_profile_clicked()
            return

        # Standalone Save Profile Dialog
        top_window = self.container.get_root()
        dialog = Adw.MessageDialog(
            transient_for=top_window if isinstance(top_window, Gtk.Window) else None,
            heading="Save Profile",
            body="Enter a profile name to save current settings:"
        )
        entry = Gtk.Entry()
        entry.set_placeholder_text("Profile Name")
        entry.set_margin_start(12)
        entry.set_margin_end(12)
        dialog.set_extra_child(entry)
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("save", "Save")
        dialog.set_response_appearance("save", Adw.ResponseAppearance.SUGGESTED)

        def on_response(d, response):
            if response == "save":
                name = entry.get_text().strip()
                if name:
                    save_profile(name, self.get_state())
                    self.refresh_profile_chips(active_profile_name=name)
                    self.status_label.set_text(f"Saved profile: {name}")
            d.destroy()

        dialog.connect("response", on_response)
        dialog.present()

    # =========================================================================
    # SOURCE SWITCHING & DYNAMIC CONTROLS
    # =========================================================================
    def _on_src_screen_toggled(self, btn: Gtk.ToggleButton):
        if btn.get_active():
            if self.btn_src_camera.get_active():
                self.btn_src_camera.set_active(False)
            self._update_source_mode(is_camera=False)
        elif not self.btn_src_camera.get_active():
            btn.set_active(True)

    def _on_src_camera_toggled(self, btn: Gtk.ToggleButton):
        if btn.get_active():
            if self.btn_src_screen.get_active():
                self.btn_src_screen.set_active(False)
            self._update_source_mode(is_camera=True)
        elif not self.btn_src_screen.get_active():
            btn.set_active(True)

    def _update_source_mode(self, is_camera: bool):
        if is_camera:
            self.combo_display.set_title("Active Camera")
            self.exp_vd.set_sensitive(False)
            self.switch_screen_off.set_active(False)
            self.switch_screen_off.set_sensitive(False)
            self._load_device_cameras()
        else:
            self.combo_display.set_title("Active Display")
            self.exp_vd.set_sensitive(True)
            self.switch_screen_off.set_sensitive(True)
            self._load_device_displays()

    # =========================================================================
    # DEVICE SELECTION & TELEMETRY
    # =========================================================================
    def update_devices(self, devices: List[Dict[str, Any]]) -> None:
        """Lifecycle hook when connected devices update."""
        if not devices:
            self.on_device_selected(None)

    def on_device_selected(self, device_info: Optional[Any]) -> None:
        """Lifecycle hook when device selection changes."""
        if isinstance(device_info, dict):
            serial = device_info.get("serial")
        else:
            serial = device_info

        self.current_serial = serial
        if not serial or serial == "No devices found":
            self.head3.set_subtitle("No device connected")
            self.row_battery.set_subtitle("N/A")
            self.level_battery.set_value(0.0)
            self.battery_icon.set_from_icon_name("battery-symbolic")
            self.row_density.set_subtitle("N/A")
            self.status_label.set_text("")
            self.set_tools_sensitive(False)
            return

        self.set_tools_sensitive(True)
        self.head3.set_subtitle("Connecting...")
        self.row_battery.set_subtitle("Loading...")
        self.row_density.set_subtitle("Loading...")

        def fetch(s):
            info = get_detailed_device_info(s)
            if self.current_serial == s:
                GLib.idle_add(self._apply_device_telemetry, info)

        threading.Thread(target=fetch, args=(serial,), daemon=True).start()
        self._load_device_displays()

    def _apply_device_telemetry(self, info: Dict[str, Any]):
        model = info.get("model", "Unknown")
        version = info.get("version", "Android")
        self.head3.set_subtitle(f"{model} • {version}")

        # Battery
        level = info.get("battery_level")
        charging = info.get("battery_charging", False)
        conn = info.get("connection", "USB")

        if level is not None:
            self.level_battery.set_value(float(level))
            sub = f"{level}%"
            if charging:
                sub += " ⚡ Charging"
                icon_name = "battery-full-charging-symbolic" if level >= 80 else "battery-good-charging-symbolic"
            else:
                icon_name = "battery-full-symbolic" if level >= 80 else (
                    "battery-good-symbolic" if level >= 20 else "battery-caution-symbolic"
                )
            if conn and conn != "N/A":
                sub += f" ({conn})"
            self.row_battery.set_subtitle(sub)
            self.battery_icon.set_from_icon_name(icon_name)
        else:
            self.level_battery.set_value(0.0)
            self.row_battery.set_subtitle("N/A")
            self.battery_icon.set_from_icon_name("battery-symbolic")

        # Density
        self.current_density = info.get("density_val")
        dens_str = info.get("density", "N/A")
        self.row_density.set_subtitle(dens_str)
        return False

    def set_tools_sensitive(self, sensitive: bool):
        self.box_density.set_sensitive(sensitive)
        self.box_nav.set_sensitive(sensitive)
        self.box_tools.set_sensitive(sensitive)

    def _load_device_displays(self):
        if not self.current_serial or self.current_serial == "No devices found":
            return
        def fetch():
            displays = get_device_displays(self.current_serial)
            def update_model():
                n = self.display_model.get_n_items()
                self.display_model.splice(0, n, [])
                if displays:
                    for d in displays:
                        self.display_model.append(f"Display {d}")
                else:
                    self.display_model.append("Display 0 (Internal)")
                self.combo_display.set_selected(0)
            GLib.idle_add(update_model)
        threading.Thread(target=fetch, daemon=True).start()

    def _load_device_cameras(self):
        if not self.current_serial or self.current_serial == "No devices found":
            return
        def fetch():
            cameras = get_device_cameras(self.current_serial)
            def update_model():
                n = self.display_model.get_n_items()
                self.display_model.splice(0, n, [])
                if cameras:
                    for c in cameras:
                        self.display_model.append(c)
                else:
                    self.display_model.append("Camera 0 (Back)")
                self.combo_display.set_selected(0)
            GLib.idle_add(update_model)
        threading.Thread(target=fetch, daemon=True).start()

    def _load_host_telemetry(self):
        def fetch():
            telemetry = get_host_telemetry()
            compositor = telemetry.get("compositor", "Wayland")
            gpu = telemetry.get("gpu", "Auto")
            GLib.idle_add(lambda: self.row_telemetry.set_subtitle(f"{compositor} • {gpu}"))
        threading.Thread(target=fetch, daemon=True).start()

    # =========================================================================
    # REMOTE ACTIONS & HANDLERS
    # =========================================================================
    def on_density_adjust(self, delta: int):
        if not self.current_serial:
            return
        base_dens = self.current_density if self.current_density else 420
        new_dens = max(120, min(1000, base_dens + delta))
        self.status_label.set_text(f"Setting density to {new_dens} DPI...")

        def task():
            success, msg = set_device_density(self.current_serial, new_dens)
            def done():
                if success:
                    self.status_label.set_text(f"Density: {new_dens} DPI")
                    self.on_device_selected(self.current_serial)
                else:
                    self.status_label.set_text(f"Density error: {msg}")
            GLib.idle_add(done)
        threading.Thread(target=task, daemon=True).start()

    def on_density_reset(self):
        if not self.current_serial:
            return
        self.status_label.set_text("Resetting density...")

        def task():
            success, msg = reset_device_density(self.current_serial)
            def done():
                if success:
                    self.status_label.set_text("Density reset to physical default")
                    self.on_device_selected(self.current_serial)
                else:
                    self.status_label.set_text(f"Reset error: {msg}")
            GLib.idle_add(done)
        threading.Thread(target=task, daemon=True).start()

    def _execute_remote_keyevent(self, keycode: int, label: str):
        if not self.current_serial:
            return
        def task():
            send_keyevent(self.current_serial, keycode)
            GLib.idle_add(lambda: self.status_label.set_text(f"Key: {label}"))
        threading.Thread(target=task, daemon=True).start()

    def _execute_remote_statusbar(self, target: str):
        if not self.current_serial:
            return
        def task():
            expand_statusbar(self.current_serial, target)
            GLib.idle_add(lambda: self.status_label.set_text(f"Shade: {target}"))
        threading.Thread(target=task, daemon=True).start()

    def _execute_remote_paste(self):
        if not self.current_serial:
            return
        display = Gdk.Display.get_default()
        if not display:
            return
        clipboard = display.get_clipboard()

        def on_clipboard_read(cb, result):
            try:
                text = cb.read_text_finish(result)
                if text:
                    def task():
                        success, msg = inject_clipboard_text(self.current_serial, text)
                        GLib.idle_add(lambda: self.status_label.set_text("Pasted to device" if success else msg))
                    threading.Thread(target=task, daemon=True).start()
                else:
                    self.status_label.set_text("Clipboard is empty")
            except Exception as e:
                self.status_label.set_text(f"Clipboard error: {e}")

        clipboard.read_text_async(None, on_clipboard_read)

    def _execute_remote_screenshot(self):
        if not self.current_serial:
            return
        self.status_label.set_text("Capturing screenshot...")

        def task():
            success, result = take_device_screenshot(self.current_serial)
            def done():
                if success:
                    self.status_label.set_text(f"Screenshot: {os.path.basename(result)}")
                else:
                    self.status_label.set_text(f"Capture failed: {result}")
            GLib.idle_add(done)
        threading.Thread(target=task, daemon=True).start()

    def _execute_remote_power(self):
        if not self.current_serial:
            return
        def task():
            success, msg = toggle_device_screen(self.current_serial)
            GLib.idle_add(lambda: self.status_label.set_text("Screen power toggled" if success else msg))
        threading.Thread(target=task, daemon=True).start()

    def _execute_remote_reboot(self):
        if not self.current_serial:
            return
        def task():
            success, msg = reboot_device(self.current_serial, "normal")
            GLib.idle_add(lambda: self.status_label.set_text(msg))
        threading.Thread(target=task, daemon=True).start()

    # =========================================================================
    # SCRCPY STREAM OPTIONS GENERATOR
    # =========================================================================
    def get_stream_options(self) -> List[str]:
        options: List[str] = []

        # 1. Capture Source
        if self.btn_src_camera.get_active():
            options.append("--video-source=camera")
            cam_idx = self.combo_display.get_selected()
            if cam_idx < self.display_model.get_n_items():
                cam_str = self.display_model.get_string(cam_idx)
                if cam_str:
                    cam_id = cam_str.split()[0]
                    if cam_id.isdigit():
                        options.append(f"--camera-id={cam_id}")
        else:
            disp_idx = self.combo_display.get_selected()
            if disp_idx > 0 and disp_idx < self.display_model.get_n_items():
                disp_str = self.display_model.get_string(disp_idx)
                match = re.search(r'(\d+)', disp_str)
                if match:
                    options.append(f"--display-id={match.group(1)}")

            # Virtual Display (scrcpy 5.0)
            if self.switch_vd_mode.get_active():
                options.append("--new-display")
                if self.switch_flex_display.get_active():
                    options.append("--flex-display")
                ime_idx = self.combo_ime_policy.get_selected()
                policies = ["local", "fallback", "hide"]
                if 0 <= ime_idx < len(policies):
                    options.append(f"--display-ime-policy={policies[ime_idx]}")
                if self.switch_no_vd_destroy.get_active():
                    options.append("--no-vd-destroy-content")

        # 2. Render Fit
        rf_idx = self.combo_render_fit.get_selected()
        fits = ["", "letterbox", "stretched", "unscaled"]
        if 0 < rf_idx < len(fits) and fits[rf_idx]:
            options.append(f"--render-fit={fits[rf_idx]}")

        # 3. Resolution Scale
        res_idx = self.combo_res_scale.get_selected()
        if res_idx < self.res_model.get_n_items():
            res_str = self.res_model.get_string(res_idx)
            if "Native" not in res_str:
                m_size = re.search(r'(\d{3,4})', res_str)
                if m_size:
                    options.append(f"--max-size={m_size.group(1)}")

        # 4. Max Framerate
        fps_idx = self.combo_max_fps.get_selected()
        if fps_idx < self.fps_model.get_n_items():
            fps_str = self.fps_model.get_string(fps_idx)
            if "Default" not in fps_str:
                m_fps = re.search(r'(\d+)', fps_str)
                if m_fps:
                    options.append(f"--max-fps={m_fps.group(1)}")

        # 5. Video Codec
        vc_idx = self.combo_video_codec.get_selected()
        codecs = ["", "h265", "h264", "av1"]
        if 0 < vc_idx < len(codecs) and codecs[vc_idx]:
            options.append(f"--video-codec={codecs[vc_idx]}")

        # 6. Window Settings
        if self.switch_fullscreen.get_active():
            options.append("--fullscreen")
        if self.switch_always_on_top.get_active():
            options.append("--always-on-top")
        if self.switch_borderless.get_active():
            options.append("--window-borderless")
        if self.switch_record.get_active():
            rec_dir = DEFAULT_RECORDINGS_DIR
            try:
                os.makedirs(rec_dir, exist_ok=True)
            except OSError:
                rec_dir = "/tmp"
            rec_path = os.path.join(rec_dir, f"andy_{int(time.time())}.mp4")
            options.append(f"--record={rec_path}")

        # 7. Hardware Video Decoding
        hw_idx = self.combo_hwdec.get_selected()
        hw_modes = ["", "vaapi", "vdpau", "dxva2", "nvdec", "disabled"]
        if 0 < hw_idx < len(hw_modes) and hw_modes[hw_idx]:
            options.append(f"--hwdec={hw_modes[hw_idx]}")

        # 8. Audio
        if not self.switch_audio_fwd.get_active():
            options.append("--no-audio")
        else:
            ac_idx = self.combo_audio_codec.get_selected()
            ac_list = ["opus", "aac", "flac", "raw"]
            if 0 <= ac_idx < len(ac_list):
                options.append(f"--audio-codec={ac_list[ac_idx]}")

            ab_idx = self.combo_audio_buffer.get_selected()
            if ab_idx < self.audio_buffer_model.get_n_items():
                ab_str = self.audio_buffer_model.get_string(ab_idx)
                m_ab = re.search(r'(\d+)', ab_str)
                if m_ab:
                    options.append(f"--audio-buffer={m_ab.group(1)}")

            if self.switch_audio_dup.get_active():
                options.append("--audio-dup")

        # 9. UHID Input
        if self.switch_keyboard_uhid.get_active():
            options.append("--keyboard=uhid")
        if self.switch_mouse_uhid.get_active():
            options.append("--mouse=uhid")
        if self.switch_gamepad_uhid.get_active():
            options.append("--gamepad=uhid")

        mb_idx = self.combo_mouse_scheme.get_selected()
        if mb_idx == 1:
            options.append("--mouse-bind=++++:++++")
        elif mb_idx == 2:
            options.append("--mouse-bind=bhsn:++++")

        # 10. Lifecycle
        if self.switch_screen_off.get_active() and not self.btn_src_camera.get_active():
            options.append("--turn-screen-off")
        if self.switch_stay_awake.get_active():
            options.append("--stay-awake")
        if self.switch_power_off_close.get_active():
            options.append("--power-off-on-close")

        return options

    def get_environment_overrides(self) -> Dict[str, str]:
        return {}

    # =========================================================================
    # STATE SERIALIZATION (FOR PROFILE MANAGEMENT)
    # =========================================================================
    def get_state(self) -> Dict[str, Any]:
        return {
            "source": "camera" if self.btn_src_camera.get_active() else "screen",
            "display": self.combo_display.get_selected(),
            "render_fit": self.combo_render_fit.get_selected(),
            "res_scale": self.combo_res_scale.get_selected(),
            "max_fps": self.combo_max_fps.get_selected(),
            "video_codec": self.combo_video_codec.get_selected(),
            "vd_mode": self.switch_vd_mode.get_active(),
            "flex_display": self.switch_flex_display.get_active(),
            "ime_policy": self.combo_ime_policy.get_selected(),
            "no_vd_destroy": self.switch_no_vd_destroy.get_active(),
            "fullscreen": self.switch_fullscreen.get_active(),
            "always_on_top": self.switch_always_on_top.get_active(),
            "borderless": self.switch_borderless.get_active(),
            "record": self.switch_record.get_active(),
            "hwdec": self.combo_hwdec.get_selected(),
            "audio_fwd": self.switch_audio_fwd.get_active(),
            "audio_codec": self.combo_audio_codec.get_selected(),
            "audio_buffer": self.combo_audio_buffer.get_selected(),
            "audio_dup": self.switch_audio_dup.get_active(),
            "keyboard_uhid": self.switch_keyboard_uhid.get_active(),
            "mouse_uhid": self.switch_mouse_uhid.get_active(),
            "gamepad_uhid": self.switch_gamepad_uhid.get_active(),
            "mouse_scheme": self.combo_mouse_scheme.get_selected(),
            "screen_off": self.switch_screen_off.get_active(),
            "stay_awake": self.switch_stay_awake.get_active(),
            "power_off_close": self.switch_power_off_close.get_active(),
        }

    def set_state(self, state: Dict[str, Any]):
        is_cam = state.get("source") == "camera"
        if is_cam:
            self.btn_src_camera.set_active(True)
        else:
            self.btn_src_screen.set_active(True)

        if "display" in state and isinstance(state["display"], int):
            if state["display"] < self.display_model.get_n_items():
                self.combo_display.set_selected(state["display"])
        if "render_fit" in state and isinstance(state["render_fit"], int):
            self.combo_render_fit.set_selected(state["render_fit"])
        if "res_scale" in state and isinstance(state["res_scale"], int):
            self.combo_res_scale.set_selected(state["res_scale"])
        if "max_fps" in state and isinstance(state["max_fps"], int):
            self.combo_max_fps.set_selected(state["max_fps"])
        if "video_codec" in state and isinstance(state["video_codec"], int):
            self.combo_video_codec.set_selected(state["video_codec"])
        if "vd_mode" in state:
            self.switch_vd_mode.set_active(bool(state["vd_mode"]))
        if "flex_display" in state:
            self.switch_flex_display.set_active(bool(state["flex_display"]))
        if "ime_policy" in state and isinstance(state["ime_policy"], int):
            self.combo_ime_policy.set_selected(state["ime_policy"])
        if "no_vd_destroy" in state:
            self.switch_no_vd_destroy.set_active(bool(state["no_vd_destroy"]))
        if "fullscreen" in state:
            self.switch_fullscreen.set_active(bool(state["fullscreen"]))
        if "always_on_top" in state:
            self.switch_always_on_top.set_active(bool(state["always_on_top"]))
        if "borderless" in state:
            self.switch_borderless.set_active(bool(state["borderless"]))
        if "record" in state:
            self.switch_record.set_active(bool(state["record"]))
        if "hwdec" in state and isinstance(state["hwdec"], int):
            self.combo_hwdec.set_selected(state["hwdec"])
        if "audio_fwd" in state:
            self.switch_audio_fwd.set_active(bool(state["audio_fwd"]))
        if "audio_codec" in state and isinstance(state["audio_codec"], int):
            self.combo_audio_codec.set_selected(state["audio_codec"])
        if "audio_buffer" in state and isinstance(state["audio_buffer"], int):
            self.combo_audio_buffer.set_selected(state["audio_buffer"])
        if "audio_dup" in state:
            self.switch_audio_dup.set_active(bool(state["audio_dup"]))
        if "keyboard_uhid" in state:
            self.switch_keyboard_uhid.set_active(bool(state["keyboard_uhid"]))
        if "mouse_uhid" in state:
            self.switch_mouse_uhid.set_active(bool(state["mouse_uhid"]))
        if "gamepad_uhid" in state:
            self.switch_gamepad_uhid.set_active(bool(state["gamepad_uhid"]))
        if "mouse_scheme" in state and isinstance(state["mouse_scheme"], int):
            self.combo_mouse_scheme.set_selected(state["mouse_scheme"])
        if "screen_off" in state:
            self.switch_screen_off.set_active(bool(state["screen_off"]))
        if "stay_awake" in state:
            self.switch_stay_awake.set_active(bool(state["stay_awake"]))
        if "power_off_close" in state:
            self.switch_power_off_close.set_active(bool(state["power_off_close"]))

    def set_stream_state(self, active: bool, mode: str = "stream") -> None:
        """Lifecycle hook when streaming starts or stops."""
        sensitive = not active
        self.pod1.set_sensitive(sensitive)
        self.pod2.set_sensitive(sensitive)
        self.chips_scroll.set_sensitive(sensitive)

    def on_stream_state_changed(self, active: bool, mode: str = "stream") -> None:
        """Lifecycle hook invoked by BaseLayout when stream changes."""
        self.set_stream_state(active, mode=mode)

    def sync_from_window(self) -> None:
        """Sync controls from parent window state."""
        if not self.window:
            return
        if hasattr(self.window, "devices") and hasattr(self.window, "device_dropdown"):
            idx = self.window.device_dropdown.get_selected()
            if 0 <= idx < len(self.window.devices):
                self.on_device_selected(self.window.devices[idx])
        self.refresh_profile_chips()

    def sync_to_window(self) -> None:
        """Sync window state from this layout."""
        pass


# =============================================================================
# STANDALONE PREVIEW APPLICATION
# =============================================================================
class ModularCardHubWindow(Adw.ApplicationWindow):
    """
    Standalone preview window for testing ModularCardHubLayout directly.
    """
    def __init__(self, **kwargs):
        super().__init__(
            default_width=1080,
            default_height=740,
            title="Andy - Modular Card Hub (Option 4)",
            **kwargs
        )

        self.toolbar_view = Adw.ToolbarView()
        self.set_content(self.toolbar_view)

        # Header Bar
        self.header_bar = Adw.HeaderBar()
        self.header_bar.set_title_widget(
            Adw.WindowTitle(title="Andy", subtitle="Option 4: Modular Card Hub")
        )

        self.dev_model = Gtk.StringList.new(["Pixel 8 Pro (USB 3.0)", "Galaxy Tab S9 (Wi-Fi)"])
        self.dev_dropdown = Gtk.DropDown(model=self.dev_model)
        self.dev_dropdown.connect("notify::selected", self._on_dev_dropdown_selected)
        self.header_bar.pack_start(self.dev_dropdown)

        self.btn_mk = Gtk.Button(label="Connect M/K", icon_name="input-keyboard-symbolic")
        self.btn_mk.add_css_class("pill")
        self.btn_mk.connect("clicked", self._on_mk_clicked)

        self.btn_stream = Gtk.Button(label="STREAM", icon_name="media-playback-start-symbolic")
        self.btn_stream.add_css_class("pill")
        self.btn_stream.add_css_class("suggested-action")
        self.btn_stream.connect("clicked", self._on_stream_clicked)

        self.header_bar.pack_end(self.btn_stream)
        self.header_bar.pack_end(self.btn_mk)
        self.toolbar_view.add_top_bar(self.header_bar)

        # Layout Hub
        self.hub = ModularHubLayout(window=self)
        self.toolbar_view.set_content(self.hub.get_widget())

        # Seed initial selection
        self.hub.on_device_selected("Pixel 8 Pro")

    def _on_dev_dropdown_selected(self, dropdown, pspec):
        idx = dropdown.get_selected()
        dev_name = self.dev_model.get_string(idx)
        self.hub.on_device_selected(dev_name)

    def _on_stream_clicked(self, button):
        opts = self.hub.get_stream_options()
        self.hub.status_label.set_text(f"CLI args: {' '.join(opts[:6])}...")

    def _on_mk_clicked(self, button):
        opts = ["--max-size=128", "--fullscreen", "--no-audio"] + self.hub.get_stream_options()
        self.hub.status_label.set_text(f"M/K mode args: {' '.join(opts[:5])}...")


class ModularCardHubApp(Adw.Application):
    def __init__(self):
        super().__init__(
            application_id="com.wolfsekhar.andy.modularhub",
            flags=Gio.ApplicationFlags.NON_UNIQUE
        )

    def do_activate(self):
        win = ModularCardHubWindow(application=self)
        win.present()


if __name__ == "__main__":
    app = ModularCardHubApp()
    sys.exit(app.run(sys.argv))
