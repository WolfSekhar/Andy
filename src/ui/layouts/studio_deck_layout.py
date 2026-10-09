"""Studio Command Deck layout for Andy.

Option 2: The Studio Command Deck (Bottles / Amberol style).
Features:
- Hero Device Card: live device banner, battery gauge (Gtk.LevelBar), connection badges,
  and big 1-click Stream &amp; M/K launch triggers.
- Tabs: Adw.ViewSwitcher &amp; Adw.ViewStack with 4 pages: Overview, Stream, Engine, Profiles.
- Scrcpy 5.0 features in expanders: Virtual display, flex display, UHID gamepad, audio latency.
- Strict Pango escaping (all ampersands as &amp;).
- Full integration with AndyWindow methods and remote action services.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import os
import re
import threading
import time

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib, Gdk, Gio

from ui.layouts.base_layout import BaseLayout

from services.device_service import (
    get_detailed_device_info,
    get_device_displays,
    get_device_cameras,
    get_device_resolution,
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
    toggle_show_touches,
)
from services.host_telemetry import get_host_telemetry
from services.orientation_monitor import OrientationMonitor
from services.profile_service import list_profiles, load_profile, save_profile

from core.config import (
    VIDEO_CODECS,
    FPS_PRESETS,
    ORIENTATIONS,
    RENDER_FITS,
    IME_POLICIES,
    CAMERA_FPS_PRESETS,
    AUDIO_CODECS,
    AUDIO_SOURCES,
    AUDIO_BUFFERS,
    GPU_ADAPTERS,
    RENDER_DRIVERS,
    WINDOW_BACKENDS,
    HWDEC_OPTIONS,
    BUFFER_PRESETS,
    TIMEOUT_PRESETS,
    MOUSE_BIND_PRESETS,
    DEFAULT_RECORDINGS_DIR,
)
from core.models import StreamConfig, AdvancedConfig
from core.scrcpy_builder import (
    build_scrcpy_args,
    build_advanced_args,
    build_environment_overrides,
)


class StudioDeckLayout(BaseLayout):
    """Studio Command Deck layout (Option 2).

    A modern, media-deck inspired interface with a persistent Hero Device Card
    and centered ViewSwitcher navigation across Overview, Stream, Engine, and Profiles.
    """

    def __init__(self, window: Any = None) -> None:
        super().__init__(window=window)

        self.current_serial: Optional[str] = None
        self.current_density: Optional[int] = None
        self.devices: List[Dict[str, Any]] = []
        self.last_resolution: Optional[Tuple[int, int, bool]] = None

        # Background Orientation Monitor
        self.orientation_monitor = OrientationMonitor()

        # Root layout widget
        self.widget = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.widget.set_vexpand(True)
        self.widget.set_hexpand(True)

        # Scrolled container for responsive handling
        self.scrolled_window = Gtk.ScrolledWindow()
        self.scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scrolled_window.set_vexpand(True)
        self.scrolled_window.set_hexpand(True)
        self.widget.append(self.scrolled_window)

        # Main clamp box (Bottles / Amberol style centered width)
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        main_box.set_margin_top(14)
        main_box.set_margin_bottom(24)
        main_box.set_margin_start(16)
        main_box.set_margin_end(16)
        self.scrolled_window.set_child(main_box)

        self.clamp = Adw.Clamp(maximum_size=920)
        self.clamp.set_hexpand(True)
        self.clamp_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.clamp.set_child(self.clamp_box)
        main_box.append(self.clamp)

        # ---------------------------------------------------------------------
        # 1. HERO LIVE DEVICE CARD (Bottles Style)
        # ---------------------------------------------------------------------
        self._build_hero_card()

        # ---------------------------------------------------------------------
        # 2. TABBED DECK: Adw.ViewSwitcher + Adw.ViewStack (4 Pages)
        # ---------------------------------------------------------------------
        self.view_stack = Adw.ViewStack()
        self.view_stack.set_vexpand(True)

        self.view_switcher = Adw.ViewSwitcher(stack=self.view_stack)
        self.view_switcher.set_policy(Adw.ViewSwitcherPolicy.WIDE)
        self.view_switcher.set_halign(Gtk.Align.CENTER)
        self.view_switcher.set_margin_top(4)
        self.view_switcher.set_margin_bottom(4)
        self.clamp_box.append(self.view_switcher)

        self.clamp_box.append(self.view_stack)

        # Build 4 pages
        self._build_overview_tab()
        self._build_stream_tab()
        self._build_engine_tab()
        self._build_profiles_tab()

        # Mobile Bottom Bar Breakpoint helper
        self.bottom_bar = Adw.ViewSwitcherBar(stack=self.view_stack)

        # Initial default telemetry load
        self._load_initial_host_telemetry()

    def get_widget(self) -> Gtk.Widget:
        """Return the top-level container widget for this layout."""
        return self.widget

    # =========================================================================
    # HERO CARD CONSTRUCTION
    # =========================================================================

    def _build_hero_card(self) -> None:
        """Builds the persistent hero status card with live banner, battery, &amp; launch triggers."""
        self.hero_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        self.hero_card.add_css_class("card")
        self.hero_card.set_margin_top(2)
        self.hero_card.set_margin_bottom(2)

        # Top row: Avatar + Device Name/Sub + Connection & Battery Badges
        top_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        top_row.set_margin_top(16)
        top_row.set_margin_start(16)
        top_row.set_margin_end(16)

        self.avatar = Gtk.Image.new_from_icon_name("phone-symbolic")
        self.avatar.set_pixel_size(40)
        top_row.append(self.avatar)

        name_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        name_box.set_hexpand(True)
        self.lbl_name = Gtk.Label(label="No Device Selected", xalign=0)
        self.lbl_name.add_css_class("title-3")
        self.lbl_sub = Gtk.Label(
            label="Connect an Android device with USB debugging enabled", xalign=0
        )
        self.lbl_sub.add_css_class("dim-label")
        name_box.append(self.lbl_name)
        name_box.append(self.lbl_sub)
        top_row.append(name_box)

        # Badges box
        badge_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        badge_box.set_valign(Gtk.Align.CENTER)

        self.lbl_conn = Gtk.Label(label="Disconnected")
        self.lbl_conn.add_css_class("accent")
        self.lbl_conn.add_css_class("card")
        self.lbl_conn.set_margin_top(2)
        self.lbl_conn.set_margin_bottom(2)
        self.lbl_conn.set_margin_start(8)
        self.lbl_conn.set_margin_end(8)
        badge_box.append(self.lbl_conn)

        # Battery gauge with Gtk.LevelBar
        self.bat_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.bat_box.add_css_class("card")
        self.bat_box.set_margin_top(2)
        self.bat_box.set_margin_bottom(2)
        self.bat_box.set_margin_start(8)
        self.bat_box.set_margin_end(8)

        self.bat_icon = Gtk.Image.new_from_icon_name("battery-symbolic")
        self.battery_level_bar = Gtk.LevelBar()
        self.battery_level_bar.set_min_value(0.0)
        self.battery_level_bar.set_max_value(100.0)
        self.battery_level_bar.set_value(0.0)
        self.battery_level_bar.set_valign(Gtk.Align.CENTER)
        self.battery_level_bar.set_size_request(60, 8)
        self.battery_level_bar.add_offset_value(Gtk.LEVEL_BAR_OFFSET_LOW, 20.0)
        self.battery_level_bar.add_offset_value(Gtk.LEVEL_BAR_OFFSET_HIGH, 80.0)
        self.battery_level_bar.add_offset_value(Gtk.LEVEL_BAR_OFFSET_FULL, 100.0)

        self.lbl_bat = Gtk.Label(label="--%")

        self.bat_box.append(self.bat_icon)
        self.bat_box.append(self.battery_level_bar)
        self.bat_box.append(self.lbl_bat)
        badge_box.append(self.bat_box)

        top_row.append(badge_box)
        self.hero_card.append(top_row)

        # Metrics strip
        metrics_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=18)
        metrics_box.set_margin_start(16)
        metrics_box.set_margin_end(16)

        self.lbl_res = Gtk.Label(label="📺 No Resolution", css_classes=["dim-label"])
        self.lbl_compositor = Gtk.Label(
            label="🖥 GNOME Mutter (Wayland Native)", css_classes=["dim-label"]
        )
        self.lbl_dpi = Gtk.Label(label="⚡ -- DPI", css_classes=["dim-label"])

        metrics_box.append(self.lbl_res)
        metrics_box.append(self.lbl_compositor)
        metrics_box.append(self.lbl_dpi)
        self.hero_card.append(metrics_box)

        # Divider
        self.hero_card.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        # Bottom row: Big 1-Click Buttons + Satellite Quick Tools
        actions_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        actions_row.set_margin_start(16)
        actions_row.set_margin_end(16)
        actions_row.set_margin_bottom(16)

        # Big 1-click Stream Button
        self.btn_stream = Gtk.Button()
        stream_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.stream_icon = Gtk.Image.new_from_icon_name("media-playback-start-symbolic")
        self.stream_label = Gtk.Label(label="Start Stream")
        self.stream_label.add_css_class("heading")
        stream_box.append(self.stream_icon)
        stream_box.append(self.stream_label)
        self.btn_stream.set_child(stream_box)
        self.btn_stream.add_css_class("suggested-action")
        self.btn_stream.add_css_class("pill")
        self.btn_stream.add_css_class("stream-btn")
        self.btn_stream.set_size_request(160, 42)
        self.btn_stream.connect("clicked", self.on_stream_button_clicked)
        actions_row.append(self.btn_stream)

        # Big 1-click Connect M/K Button
        self.btn_mk = Gtk.Button()
        mk_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.mk_icon = Gtk.Image.new_from_icon_name("input-keyboard-symbolic")
        self.mk_label = Gtk.Label(label="Connect M/K")
        self.mk_label.add_css_class("heading")
        mk_box.append(self.mk_icon)
        mk_box.append(self.mk_label)
        self.btn_mk.set_child(mk_box)
        self.btn_mk.add_css_class("pill")
        self.btn_mk.add_css_class("mk-btn")
        self.btn_mk.set_size_request(140, 42)
        self.btn_mk.set_tooltip_text("Send Mouse &amp; Keyboard without streaming video")
        self.btn_mk.connect("clicked", self.on_mk_button_clicked)
        actions_row.append(self.btn_mk)

        sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        sep.set_margin_start(6)
        sep.set_margin_end(6)
        actions_row.append(sep)

        # Satellite quick tools
        sat_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        sat_box.set_hexpand(True)
        sat_box.set_halign(Gtk.Align.END)

        self.btn_screen_off = Gtk.Button(
            icon_name="weather-clear-night-symbolic", tooltip_text="Screen Off"
        )
        self.btn_screen_off.connect("clicked", self.on_screen_off_clicked)
        sat_box.append(self.btn_screen_off)

        self.btn_power = Gtk.Button(
            icon_name="system-shutdown-symbolic", tooltip_text="Power"
        )
        self.btn_power.connect("clicked", self.on_power_clicked)
        sat_box.append(self.btn_power)

        self.btn_screenshot = Gtk.Button(
            icon_name="camera-photo-symbolic", tooltip_text="Screenshot"
        )
        self.btn_screenshot.connect("clicked", self.on_screenshot_clicked)
        sat_box.append(self.btn_screenshot)

        self.btn_record = Gtk.Button(
            icon_name="media-record-symbolic", tooltip_text="Quick Record"
        )
        self.btn_record.connect("clicked", self.on_quick_record_clicked)
        sat_box.append(self.btn_record)

        self.btn_paste = Gtk.Button(
            icon_name="edit-paste-symbolic", tooltip_text="Paste Clipboard"
        )
        self.btn_paste.connect("clicked", self.on_paste_clicked)
        sat_box.append(self.btn_paste)

        actions_row.append(sat_box)
        self.hero_card.append(actions_row)

        # Status note row
        self.status_label = Gtk.Label(label="", xalign=0.5)
        self.status_label.add_css_class("dim-label")
        self.status_label.add_css_class("caption")
        self.status_label.set_margin_bottom(6)
        self.hero_card.append(self.status_label)

        self.clamp_box.append(self.hero_card)

        # Disable launch until device is connected
        self._set_hero_sensitive(False)

    def _set_hero_sensitive(self, sensitive: bool) -> None:
        """Sets sensitive state for hero buttons."""
        self.btn_stream.set_sensitive(sensitive)
        self.btn_mk.set_sensitive(sensitive)
        self.btn_screen_off.set_sensitive(sensitive)
        self.btn_power.set_sensitive(sensitive)
        self.btn_screenshot.set_sensitive(sensitive)
        self.btn_record.set_sensitive(sensitive)
        self.btn_paste.set_sensitive(sensitive)

    # =========================================================================
    # TAB 1: OVERVIEW & REMOTE
    # =========================================================================

    def _build_overview_tab(self) -> None:
        """Builds Tab 1: Android remote navigation, hardware tools, and host telemetry."""
        page_overview = Adw.PreferencesPage()

        # Android Remote Navigation
        grp_nav = Adw.PreferencesGroup(title="Android Remote Navigation")

        r_nav = Adw.ActionRow(title="Hardware Navigation Keys")
        n_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.btn_back = Gtk.Button(icon_name="go-previous-symbolic", label="Back")
        self.btn_back.connect("clicked", lambda b: self._send_keyevent(4, "Back"))
        self.btn_home = Gtk.Button(icon_name="user-home-symbolic", label="Home")
        self.btn_home.connect("clicked", lambda b: self._send_keyevent(3, "Home"))
        self.btn_recents = Gtk.Button(icon_name="view-grid-symbolic", label="Recents")
        self.btn_recents.connect("clicked", lambda b: self._send_keyevent(187, "Recents"))
        n_box.append(self.btn_back)
        n_box.append(self.btn_home)
        n_box.append(self.btn_recents)
        r_nav.add_suffix(n_box)
        grp_nav.add(r_nav)

        r_quick = Adw.ActionRow(title="System Shade &amp; Tools")
        q_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.btn_notif = Gtk.Button(
            icon_name="preferences-system-notifications-symbolic", label="Notifications"
        )
        self.btn_notif.connect("clicked", lambda b: self._expand_statusbar("notifications"))
        self.btn_qs = Gtk.Button(
            icon_name="emblem-system-symbolic", label="Quick Settings"
        )
        self.btn_qs.connect("clicked", lambda b: self._expand_statusbar("quicksettings"))
        q_box.append(self.btn_notif)
        q_box.append(self.btn_qs)
        r_quick.add_suffix(q_box)
        grp_nav.add(r_quick)
        page_overview.add(grp_nav)

        # Hardware Adjustments
        grp_hw = Adw.PreferencesGroup(title="Hardware Adjustments")

        r_vol = Adw.ActionRow(title="Media Volume")
        v_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.btn_vol_down = Gtk.Button(icon_name="audio-volume-low-symbolic", label="Down")
        self.btn_vol_down.connect("clicked", lambda b: self._adjust_volume("down"))
        self.btn_vol_up = Gtk.Button(icon_name="audio-volume-high-symbolic", label="Up")
        self.btn_vol_up.connect("clicked", lambda b: self._adjust_volume("up"))
        v_box.append(self.btn_vol_down)
        v_box.append(self.btn_vol_up)
        r_vol.add_suffix(v_box)
        grp_hw.add(r_vol)

        r_dpi = Adw.ActionRow(
            title="Display Density (DPI)", subtitle="Live ADB Density Override"
        )
        d_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.btn_dpi_down = Gtk.Button(label="-20")
        self.btn_dpi_down.connect("clicked", lambda b: self._adjust_density(-20))
        self.btn_dpi_up = Gtk.Button(label="+20")
        self.btn_dpi_up.connect("clicked", lambda b: self._adjust_density(20))
        self.btn_dpi_reset = Gtk.Button(label="Reset")
        self.btn_dpi_reset.connect("clicked", lambda b: self._reset_density())
        d_box.append(self.btn_dpi_down)
        d_box.append(self.btn_dpi_up)
        d_box.append(self.btn_dpi_reset)
        r_dpi.add_suffix(d_box)
        grp_hw.add(r_dpi)

        self.switch_show_touches = Adw.SwitchRow(
            title="Show Visual Touches",
            subtitle="Display circle touches on Android screen",
        )
        self.switch_show_touches.connect("notify::active", self._on_show_touches_toggled)
        grp_hw.add(self.switch_show_touches)

        page_overview.add(grp_hw)

        # Telemetry & System Specs
        grp_telem = Adw.PreferencesGroup(title="Device Telemetry &amp; Specs")

        self.row_telemetry_compositor = Adw.ActionRow(
            title="Host Wayland Compositor", subtitle="Detecting..."
        )
        self.row_telemetry_compositor.add_prefix(
            Gtk.Image.new_from_icon_name("video-display-symbolic")
        )
        grp_telem.add(self.row_telemetry_compositor)

        self.row_telemetry_gpu = Adw.ActionRow(
            title="GPU Driver &amp; Renderer", subtitle="Detecting..."
        )
        self.row_telemetry_gpu.add_prefix(
            Gtk.Image.new_from_icon_name("preferences-system-symbolic")
        )
        grp_telem.add(self.row_telemetry_gpu)

        self.row_device_details = Adw.ActionRow(
            title="Android OS &amp; Architecture", subtitle="N/A"
        )
        self.row_device_details.add_prefix(
            Gtk.Image.new_from_icon_name("phone-symbolic")
        )
        grp_telem.add(self.row_device_details)

        page_overview.add(grp_telem)

        self.view_stack.add_titled_with_icon(
            page_overview, "overview", "Overview", "phone-symbolic"
        )

    # =========================================================================
    # TAB 2: STREAM & DISPLAY (Includes Scrcpy 5.0 Virtual Display Expander)
    # =========================================================================

    def _build_stream_tab(self) -> None:
        """Builds Tab 2: Display &amp; Stream parameters with scrcpy 5.0 Virtual Display expander."""
        self.stream_page = Adw.PreferencesPage()

        grp_str = Adw.PreferencesGroup(title="Display &amp; Stream Settings")

        # Capture Source (Screen vs Camera)
        self.type_row = Adw.ComboRow(
            title="Capture Source",
            model=Gtk.StringList.new(["Screen", "Camera"]),
        )
        self.type_row.connect("notify::selected", self._on_source_type_changed)
        grp_str.add(self.type_row)

        # Screen Display output selector
        self.display_model = Gtk.StringList.new(["0 (Default)"])
        self.display_row = Adw.ComboRow(
            title="Display Output", model=self.display_model
        )
        grp_str.add(self.display_row)

        # Camera selection row (hidden when in Screen mode)
        self.camera_model = Gtk.StringList.new(["0 (Default)"])
        self.camera_row = Adw.ComboRow(
            title="Camera Lens", model=self.camera_model
        )
        self.camera_row.set_visible(False)
        grp_str.add(self.camera_row)

        # Resolution Presets (Combo with entry child)
        self.size_row = Adw.ActionRow(title="Resolution Preset")
        self.size_combo = Gtk.ComboBoxText.new_with_entry()
        self.size_combo.set_valign(Gtk.Align.CENTER)
        self.size_combo.append_text("Default")
        for s in ["100% Native", "80% Balanced", "60% Smooth", "40% Lite", "20% Minimal"]:
            self.size_combo.append_text(s)
        self.size_combo.set_active(0)
        self.size_row.add_suffix(self.size_combo)
        grp_str.add(self.size_row)

        # Max Framerate
        self.fps_row = Adw.ActionRow(title="Max Framerate")
        self.fps_combo = Gtk.ComboBoxText.new_with_entry()
        self.fps_combo.set_valign(Gtk.Align.CENTER)
        for f in FPS_PRESETS:
            self.fps_combo.append_text(f)
        self.fps_combo.set_active(0)
        self.fps_row.add_suffix(self.fps_combo)
        grp_str.add(self.fps_row)

        # Video Codec
        self.codec_model = Gtk.StringList()
        for c in VIDEO_CODECS:
            self.codec_model.append(c)
        self.codec_row = Adw.ComboRow(title="Video Codec", model=self.codec_model)
        grp_str.add(self.codec_row)

        # Bitrate
        self.bitrate_row = Adw.EntryRow(title="Video Bitrate (Mbps)")
        grp_str.add(self.bitrate_row)

        # Orientation
        self.orient_model = Gtk.StringList()
        for o in ORIENTATIONS:
            self.orient_model.append(o)
        self.orient_row = Adw.ComboRow(title="Display Orientation", model=self.orient_model)
        grp_str.add(self.orient_row)

        # Start App
        self.entry_start_app = Adw.EntryRow(title="Start App (Package Name)")
        grp_str.add(self.entry_start_app)

        # Window Presentation Settings
        self.switch_fullscreen = Adw.SwitchRow(title="Fullscreen")
        self.switch_borderless = Adw.SwitchRow(title="Borderless Window")
        self.switch_always_on_top = Adw.SwitchRow(title="Always on Top")
        self.switch_disable_screensaver = Adw.SwitchRow(title="Disable Screensaver")

        grp_str.add(self.switch_fullscreen)
        grp_str.add(self.switch_borderless)
        grp_str.add(self.switch_always_on_top)
        grp_str.add(self.switch_disable_screensaver)

        self.stream_page.add(grp_str)

        # Scrcpy 5.0 Virtual Display & Flex Resizing Expander
        grp_vd = Adw.PreferencesGroup(title="Auxiliary &amp; Virtual Displays (scrcpy 5.0)")

        self.exp_vd = Adw.ExpanderRow(title="Virtual Display &amp; Flex Resizing")
        self.switch_new_display = Adw.SwitchRow(
            title="Virtual Display Mode",
            subtitle="Create secondary headless desktop (Android 13+)",
        )
        self.switch_flex_display = Adw.SwitchRow(
            title="Flex Display",
            subtitle="Dynamic window resizing for virtual display",
        )

        self.ime_policy_model = Gtk.StringList()
        for p in IME_POLICIES:
            self.ime_policy_model.append(p)
        self.ime_policy_row = Adw.ComboRow(
            title="Virtual Display IME Policy", model=self.ime_policy_model
        )

        self.render_fit_model = Gtk.StringList()
        for r in RENDER_FITS:
            self.render_fit_model.append(r)
        self.render_fit_row = Adw.ComboRow(
            title="Render Fit", model=self.render_fit_model
        )

        self.switch_preserve_content = Adw.SwitchRow(
            title="Preserve Display Content",
            subtitle="Do not destroy content when virtual display closes",
        )

        self.exp_vd.add_row(self.switch_new_display)
        self.exp_vd.add_row(self.switch_flex_display)
        self.exp_vd.add_row(self.ime_policy_row)
        self.exp_vd.add_row(self.render_fit_row)
        self.exp_vd.add_row(self.switch_preserve_content)
        grp_vd.add(self.exp_vd)

        # Camera Special Features Expander
        self.exp_cam = Adw.ExpanderRow(title="Camera Streaming Controls (scrcpy 5.0)")
        self.switch_camera_torch = Adw.SwitchRow(title="Camera Torch / Flashlight")
        self.camera_fps_model = Gtk.StringList()
        for cf in CAMERA_FPS_PRESETS:
            self.camera_fps_model.append(cf)
        self.camera_fps_row = Adw.ComboRow(
            title="Camera Framerate", model=self.camera_fps_model
        )
        self.switch_camera_high_speed = Adw.SwitchRow(title="Camera High Speed")
        self.entry_camera_zoom = Adw.EntryRow(title="Camera Zoom (e.g. 1.0, 2.0)")

        self.exp_cam.add_row(self.switch_camera_torch)
        self.exp_cam.add_row(self.camera_fps_row)
        self.exp_cam.add_row(self.switch_camera_high_speed)
        self.exp_cam.add_row(self.entry_camera_zoom)
        grp_vd.add(self.exp_cam)
        self.exp_cam.set_visible(False)

        self.stream_page.add(grp_vd)

        self.view_stack.add_titled_with_icon(
            self.stream_page, "stream", "Stream", "video-display-symbolic"
        )

    def _on_source_type_changed(self, combo, pspec) -> None:
        """Toggle UI between Screen and Camera modes."""
        is_camera = (combo.get_selected() == 1)
        self.display_row.set_visible(not is_camera)
        self.camera_row.set_visible(is_camera)
        self.exp_vd.set_visible(not is_camera)
        self.exp_cam.set_visible(is_camera)

    # =========================================================================
    # TAB 3: ENGINE & AUDIO (Includes UHID Gamepad & Audio Latency)
    # =========================================================================

    def _build_engine_tab(self) -> None:
        """Builds Tab 3: Audio engine, HID peripherals, and hardware decoding pipeline."""
        self.engine_page = Adw.PreferencesPage()

        # Audio Forwarding Engine
        grp_aud = Adw.PreferencesGroup(title="Audio Forwarding Engine")

        self.switch_forward_audio = Adw.SwitchRow(title="Forward Audio", active=True)
        grp_aud.add(self.switch_forward_audio)

        self.audio_codec_model = Gtk.StringList()
        for ac in AUDIO_CODECS:
            self.audio_codec_model.append(ac)
        self.audio_codec_row = Adw.ComboRow(
            title="Audio Codec", model=self.audio_codec_model
        )
        grp_aud.add(self.audio_codec_row)

        self.audio_source_model = Gtk.StringList()
        for asrc in AUDIO_SOURCES:
            self.audio_source_model.append(asrc)
        self.audio_source_row = Adw.ComboRow(
            title="Audio Source", model=self.audio_source_model
        )
        grp_aud.add(self.audio_source_row)

        # Scrcpy 5.0 Audio Buffer Latency
        self.audio_buffer_model = Gtk.StringList()
        for ab in AUDIO_BUFFERS:
            self.audio_buffer_model.append(ab)
        self.audio_buffer_row = Adw.ComboRow(
            title="Audio Buffer Latency", model=self.audio_buffer_model
        )
        grp_aud.add(self.audio_buffer_row)

        self.entry_audio_bitrate = Adw.EntryRow(title="Audio Bitrate (Kbps)")
        grp_aud.add(self.entry_audio_bitrate)

        self.switch_audio_dup = Adw.SwitchRow(
            title="Duplicate Audio",
            subtitle="Play audio on both computer and Android device",
        )
        grp_aud.add(self.switch_audio_dup)

        self.engine_page.add(grp_aud)

        # Scrcpy 5.0 Hardware Input & Peripherals (UHID Gamepad)
        grp_hid = Adw.PreferencesGroup(
            title="Hardware Input &amp; Peripherals (scrcpy 5.0)"
        )

        self.exp_hid = Adw.ExpanderRow(
            title="HID Emulation &amp; Controller Passthrough"
        )

        self.switch_keyboard_uhid = Adw.SwitchRow(
            title="Keyboard UHID Mode",
            subtitle="Physical HID keyboard emulation via USB/Bluetooth",
        )
        self.switch_mouse_uhid = Adw.SwitchRow(
            title="Mouse UHID Mode",
            subtitle="Physical HID mouse emulation with raw cursor capture",
        )
        self.switch_gamepad_uhid = Adw.SwitchRow(
            title="Gamepad Forwarding (UHID)",
            subtitle="Forward host controller as Android gamepad (scrcpy 5.0)",
        )

        self.mouse_bind_model = Gtk.StringList()
        for mb in MOUSE_BIND_PRESETS:
            self.mouse_bind_model.append(mb)
        self.mouse_bind_row = Adw.ComboRow(
            title="Mouse Button Bindings", model=self.mouse_bind_model
        )

        self.switch_legacy_paste = Adw.SwitchRow(
            title="Legacy Paste Mode",
            subtitle="Inject clipboard as key events instead of sync",
        )
        self.switch_no_clipboard_sync = Adw.SwitchRow(
            title="Disable Clipboard Autosync"
        )
        self.switch_read_only = Adw.SwitchRow(
            title="Read-Only Mode",
            subtitle="Disable all keyboard and mouse interactions",
        )

        self.exp_hid.add_row(self.switch_keyboard_uhid)
        self.exp_hid.add_row(self.switch_mouse_uhid)
        self.exp_hid.add_row(self.switch_gamepad_uhid)
        self.exp_hid.add_row(self.mouse_bind_row)
        self.exp_hid.add_row(self.switch_legacy_paste)
        self.exp_hid.add_row(self.switch_no_clipboard_sync)
        self.exp_hid.add_row(self.switch_read_only)
        grp_hid.add(self.exp_hid)

        self.engine_page.add(grp_hid)

        # Hardware Video Decoding & Pipeline
        grp_hw = Adw.PreferencesGroup(
            title="Hardware Video Decoding &amp; Pipeline"
        )

        self.hwdec_model = Gtk.StringList()
        for hw in HWDEC_OPTIONS:
            self.hwdec_model.append(hw)
        self.hwdec_row = Adw.ComboRow(
            title="Hardware Video Decoder", model=self.hwdec_model
        )
        grp_hw.add(self.hwdec_row)

        self.render_driver_model = Gtk.StringList()
        for rd in RENDER_DRIVERS:
            self.render_driver_model.append(rd)
        self.render_driver_row = Adw.ComboRow(
            title="Render Driver", model=self.render_driver_model
        )
        grp_hw.add(self.render_driver_row)

        self.backend_model = Gtk.StringList()
        for wb in WINDOW_BACKENDS:
            self.backend_model.append(wb)
        self.backend_row = Adw.ComboRow(
            title="Window Backend", model=self.backend_model
        )
        grp_hw.add(self.backend_row)

        self.gpu_model = Gtk.StringList()
        for ga in GPU_ADAPTERS:
            self.gpu_model.append(ga)
        self.gpu_row = Adw.ComboRow(title="GPU Adapter", model=self.gpu_model)
        grp_hw.add(self.gpu_row)

        self.buffer_model = Gtk.StringList()
        for b in BUFFER_PRESETS:
            self.buffer_model.append(b)
        self.buffer_row = Adw.ComboRow(title="Video Buffer", model=self.buffer_model)
        grp_hw.add(self.buffer_row)

        self.switch_screen_off = Adw.SwitchRow(
            title="Turn Screen Off During Session", active=True
        )
        self.switch_stay_awake = Adw.SwitchRow(
            title="Stay Awake", subtitle="Prevent Android device from sleeping"
        )
        self.switch_power_off_close = Adw.SwitchRow(
            title="Power Off on Close",
            subtitle="Turn off device screen when session ends",
        )
        self.switch_no_power_on = Adw.SwitchRow(
            title="No Power On", subtitle="Do not turn screen on at startup"
        )
        self.switch_print_fps = Adw.SwitchRow(title="Print FPS Counter")
        self.switch_no_downsize = Adw.SwitchRow(
            title="No Downsize on Error",
            subtitle="Prevent automatic resolution downsizing on encoder crash",
        )

        grp_hw.add(self.switch_screen_off)
        grp_hw.add(self.switch_stay_awake)
        grp_hw.add(self.switch_power_off_close)
        grp_hw.add(self.switch_no_power_on)
        grp_hw.add(self.switch_print_fps)
        grp_hw.add(self.switch_no_downsize)

        self.timeout_model = Gtk.StringList()
        for t in TIMEOUT_PRESETS:
            self.timeout_model.append(t)
        self.timeout_row = Adw.ComboRow(
            title="Screen Off Timeout", model=self.timeout_model
        )
        grp_hw.add(self.timeout_row)

        self.entry_time_limit = Adw.EntryRow(title="Session Time Limit (seconds)")
        grp_hw.add(self.entry_time_limit)

        self.switch_keep_active = Adw.SwitchRow(
            title="Keep Active", subtitle="Prevent display sleep while scrcpy runs"
        )
        grp_hw.add(self.switch_keep_active)

        self.engine_page.add(grp_hw)

        self.view_stack.add_titled_with_icon(
            self.engine_page, "engine", "Engine", "multimedia-player-symbolic"
        )

    # =========================================================================
    # TAB 4: PROFILES & RECORDS
    # =========================================================================

    def _build_profiles_tab(self) -> None:
        """Builds Tab 4: Lossless session recording and active profile selector."""
        self.profiles_page = Adw.PreferencesPage()

        # Lossless Session Recording
        grp_rec = Adw.PreferencesGroup(title="Lossless Session Recording")

        self.switch_record = Adw.SwitchRow(title="Record Stream to Disk")
        grp_rec.add(self.switch_record)

        self.record_format_model = Gtk.StringList.new(
            ["MP4 (Universal)", "MKV (Crash Safe)"]
        )
        self.record_format_row = Adw.ComboRow(
            title="Container Format", model=self.record_format_model
        )
        grp_rec.add(self.record_format_row)

        self.row_record_dir = Adw.ActionRow(
            title="Recordings Directory", subtitle=DEFAULT_RECORDINGS_DIR
        )
        btn_open_rec = Gtk.Button(icon_name="folder-open-symbolic", tooltip_text="Open Folder")
        btn_open_rec.connect("clicked", self._open_recordings_dir)
        self.row_record_dir.add_suffix(btn_open_rec)
        grp_rec.add(self.row_record_dir)

        self.profiles_page.add(grp_rec)

        # Profile Management
        grp_p = Adw.PreferencesGroup(title="Active Profiles")

        self.profile_model = Gtk.StringList.new(["Default"])
        self.profile_row = Adw.ComboRow(title="Load Profile", model=self.profile_model)
        self.profile_row.connect("notify::selected", self._on_profile_combo_changed)
        grp_p.add(self.profile_row)

        r_actions = Adw.ActionRow(title="Profile Quick Actions")
        p_act_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        btn_save_prof = Gtk.Button(
            icon_name="document-save-symbolic", label="Save Profile"
        )
        btn_save_prof.connect("clicked", self._on_save_profile_clicked)
        p_act_box.append(btn_save_prof)

        btn_manage_prof = Gtk.Button(
            icon_name="emblem-system-symbolic", label="Settings"
        )
        btn_manage_prof.connect("clicked", self._on_settings_clicked)
        p_act_box.append(btn_manage_prof)

        r_actions.add_suffix(p_act_box)
        grp_p.add(r_actions)

        self.profiles_page.add(grp_p)

        self.view_stack.add_titled_with_icon(
            self.profiles_page, "profiles", "Profiles", "document-save-symbolic"
        )

        self.refresh_profiles()

    def _open_recordings_dir(self, button) -> None:
        """Opens recordings folder in default system file manager."""
        try:
            os.makedirs(DEFAULT_RECORDINGS_DIR, exist_ok=True)
            Gio.AppInfo.launch_default_for_uri(f"file://{DEFAULT_RECORDINGS_DIR}", None)
        except Exception as e:
            self._set_status(f"Error opening directory: {e}")

    # =========================================================================
    # ACTIONS & WINDOW DELEGATION
    # =========================================================================

    def on_stream_button_clicked(self, button) -> None:
        """Handles 1-click Stream button click; connects directly to window methods."""
        if self.window and hasattr(self.window, "process_manager") and self.window.process_manager.is_running:
            self.window.process_manager.stop()
            return

        if not self.current_serial or self.current_serial == "No devices found":
            if self.window and hasattr(self.window, "show_error_dialog"):
                self.window.show_error_dialog(
                    "No Device", "Please connect and select an Android device first."
                )
            else:
                self._set_status("Please connect an Android device first.")
            return

        options = self.get_stream_options()
        if self.window and hasattr(self.window, "launch_scrcpy"):
            self.window.launch_scrcpy(self.current_serial, options, mode="stream")
        elif self.window and hasattr(self.window, "on_play_clicked"):
            self.window.on_play_clicked(button)

    def on_mk_button_clicked(self, button) -> None:
        """Handles 1-click Connect M/K button click; connects directly to window methods."""
        if self.window and hasattr(self.window, "process_manager") and self.window.process_manager.is_running:
            self.window.process_manager.stop()
            return

        if not self.current_serial or self.current_serial == "No devices found":
            if self.window and hasattr(self.window, "show_error_dialog"):
                self.window.show_error_dialog(
                    "No Device", "Please connect and select an Android device first."
                )
            else:
                self._set_status("Please connect an Android device first.")
            return

        adv_cfg = self._get_advanced_config()
        options = ["--max-size=128", "--fullscreen", "--no-audio"] + build_advanced_args(adv_cfg)
        if self.window and hasattr(self.window, "launch_scrcpy"):
            self.window.launch_scrcpy(self.current_serial, options, mode="mk")
        elif self.window and hasattr(self.window, "on_connect_mk_clicked"):
            self.window.on_connect_mk_clicked(button)

    def set_stream_state(self, active: bool, mode: str = "stream") -> None:
        """Reflect whether scrcpy or M/K mode is running across hero and option cards."""
        if active:
            if mode == "stream":
                self.stream_label.set_text("Stop Stream")
                self.stream_icon.set_from_icon_name("media-playback-stop-symbolic")
                self.btn_stream.remove_css_class("suggested-action")
                self.btn_stream.remove_css_class("stream-btn")
                self.btn_stream.add_css_class("destructive-action")
                self.btn_stream.add_css_class("stop-btn")
                self.btn_mk.set_sensitive(False)
            else:
                self.mk_label.set_text("Disconnect")
                self.mk_icon.set_from_icon_name("media-playback-stop-symbolic")
                self.btn_mk.add_css_class("destructive-action")
                self.btn_mk.add_css_class("stop-btn")
                self.btn_stream.set_sensitive(False)

            self.stream_page.set_sensitive(False)
            self.engine_page.set_sensitive(False)
            self._set_status(f"Session active ({mode})")
        else:
            self.stream_label.set_text("Start Stream")
            self.stream_icon.set_from_icon_name("media-playback-start-symbolic")
            self.btn_stream.remove_css_class("destructive-action")
            self.btn_stream.remove_css_class("stop-btn")
            self.btn_stream.add_css_class("suggested-action")
            self.btn_stream.add_css_class("stream-btn")
            self.btn_stream.set_sensitive(bool(self.current_serial and self.current_serial != "No devices found"))

            self.mk_label.set_text("Connect M/K")
            self.mk_icon.set_from_icon_name("input-keyboard-symbolic")
            self.btn_mk.remove_css_class("destructive-action")
            self.btn_mk.remove_css_class("stop-btn")
            self.btn_mk.set_sensitive(bool(self.current_serial and self.current_serial != "No devices found"))

            self.stream_page.set_sensitive(True)
            self.engine_page.set_sensitive(True)
            self._set_status("")

    # =========================================================================
    # SATELLITE & REMOTE TOOLS IMPLEMENTATION
    # =========================================================================

    def on_screen_off_clicked(self, button) -> None:
        """Toggle device screen power state."""
        if not self.current_serial:
            return
        self._set_status("Toggling screen...")

        def _task():
            success, msg = toggle_device_screen(self.current_serial)
            GLib.idle_add(
                lambda: self._set_status("Screen toggled" if success else f"Error: {msg}")
            )

        threading.Thread(target=_task, daemon=True).start()

    def on_power_clicked(self, button) -> None:
        """Send hardware power keyevent."""
        if not self.current_serial:
            return
        self._set_status("Sending Power key...")

        def _task():
            success, msg = send_keyevent(self.current_serial, 26)  # KEYCODE_POWER
            GLib.idle_add(
                lambda: self._set_status("Power key sent" if success else f"Error: {msg}")
            )

        threading.Thread(target=_task, daemon=True).start()

    def on_screenshot_clicked(self, button) -> None:
        """Capture high-resolution screenshot to disk."""
        if not self.current_serial:
            return
        self._set_status("Capturing screenshot...")

        def _task():
            success, result = take_device_screenshot(self.current_serial)
            GLib.idle_add(
                lambda: self._set_status(
                    f"Screenshot saved: {os.path.basename(result)}"
                    if success
                    else f"Capture failed: {result}"
                )
            )

        threading.Thread(target=_task, daemon=True).start()

    def on_quick_record_clicked(self, button) -> None:
        """Toggle disk recording mode."""
        is_rec = not self.switch_record.get_active()
        self.switch_record.set_active(is_rec)
        self._set_status("Lossless Recording Enabled" if is_rec else "Lossless Recording Disabled")

    def on_paste_clicked(self, button) -> None:
        """Paste host clipboard text to Android device."""
        if not self.current_serial:
            return
        display = Gdk.Display.get_default()
        if not display:
            return
        clipboard = display.get_clipboard()

        def _on_text(cb, res):
            try:
                text = cb.read_text_finish(res)
                if text:
                    def _inject():
                        success, msg = inject_clipboard_text(self.current_serial, text)
                        GLib.idle_add(
                            lambda: self._set_status(
                                "Clipboard pasted" if success else f"Paste error: {msg}"
                            )
                        )
                    threading.Thread(target=_inject, daemon=True).start()
                else:
                    self._set_status("Clipboard is empty")
            except Exception as e:
                self._set_status(f"Clipboard error: {e}")

        clipboard.read_text_async(None, _on_text)

    def _send_keyevent(self, keycode: int, name: str) -> None:
        """Send an Android navigation keyevent."""
        if not self.current_serial:
            return
        self._set_status(f"Sending {name}...")

        def _task():
            success, msg = send_keyevent(self.current_serial, keycode)
            GLib.idle_add(
                lambda: self._set_status(f"{name} sent" if success else f"Error: {msg}")
            )

        threading.Thread(target=_task, daemon=True).start()

    def _expand_statusbar(self, target: str) -> None:
        """Expand Android notification shade or quick settings."""
        if not self.current_serial:
            return

        def _task():
            success, msg = expand_statusbar(self.current_serial, target)
            name = "Notifications" if target == "notifications" else "Quick Settings"
            GLib.idle_add(
                lambda: self._set_status(
                    f"{name} expanded" if success else f"Statusbar error: {msg}"
                )
            )

        threading.Thread(target=_task, daemon=True).start()

    def _adjust_volume(self, direction: str) -> None:
        """Adjust media volume up or down."""
        if not self.current_serial:
            return

        def _task():
            success, msg = adjust_device_volume(self.current_serial, direction)
            GLib.idle_add(
                lambda: self._set_status(
                    f"Volume {direction}" if success else f"Volume error: {msg}"
                )
            )

        threading.Thread(target=_task, daemon=True).start()

    def _adjust_density(self, delta: int) -> None:
        """Adjust display density by delta."""
        if not self.current_serial:
            return
        base_density = self.current_density if self.current_density else 420
        new_density = max(120, min(1000, base_density + delta))
        self._set_status(f"Setting density to {new_density} DPI...")

        def _task():
            success, msg = set_device_density(self.current_serial, new_density)

            def _done():
                if success:
                    self._set_status(f"Density set to {new_density} DPI")
                    self.on_device_selected(self.current_serial)
                else:
                    self._set_status(f"Density error: {msg}")

            GLib.idle_add(_done)

        threading.Thread(target=_task, daemon=True).start()

    def _reset_density(self) -> None:
        """Reset display density to default."""
        if not self.current_serial:
            return
        self._set_status("Resetting density...")

        def _task():
            success, msg = reset_device_density(self.current_serial)

            def _done():
                if success:
                    self._set_status("Density reset to physical default")
                    self.on_device_selected(self.current_serial)
                else:
                    self._set_status(f"Reset error: {msg}")

            GLib.idle_add(_done)

        threading.Thread(target=_task, daemon=True).start()

    def _on_show_touches_toggled(self, switch, pspec) -> None:
        """Toggle touch indicator on device."""
        if not self.current_serial:
            return

        def _task():
            success, msg = toggle_show_touches(self.current_serial)
            GLib.idle_add(lambda: self._set_status(msg if success else f"Touch error: {msg}"))

        threading.Thread(target=_task, daemon=True).start()

    def _set_status(self, text: str) -> None:
        """Update subtitle status feedback label."""
        if hasattr(self, "status_label"):
            self.status_label.set_text(text)

    # =========================================================================
    # DEVICE LIFECYCLE & TELEMETRY
    # =========================================================================

    def update_devices(self, devices: List[Dict[str, Any]]) -> None:
        """Update layout with newly enumerated devices."""
        self.devices = devices
        if devices and not self.current_serial:
            self.on_device_selected(devices[0])
        elif not devices:
            self.on_device_selected(None)

    def on_device_selected(self, device_info: Optional[Any]) -> None:
        """Callback when active device selection changes."""
        serial: Optional[str] = None
        if isinstance(device_info, dict):
            serial = device_info.get("serial")
        elif isinstance(device_info, str):
            serial = device_info
        elif device_info is None:
            serial = None

        self.current_serial = serial
        self.orientation_monitor.stop()
        self.last_resolution = None

        if not serial or serial == "No devices found":
            self.lbl_name.set_text("No Device Selected")
            self.lbl_sub.set_text("Connect an Android device with USB debugging enabled")
            self.lbl_conn.set_text("Disconnected")
            self.lbl_bat.set_text("--%")
            self.battery_level_bar.set_value(0.0)
            self.bat_icon.set_from_icon_name("battery-symbolic")
            self.lbl_res.set_text("📺 No Resolution")
            self.lbl_dpi.set_text("⚡ -- DPI")
            self._set_hero_sensitive(False)
            return

        self._set_hero_sensitive(True)
        if isinstance(device_info, dict) and device_info.get("model"):
            self.lbl_name.set_text(device_info.get("model", "Connecting..."))
            ver = device_info.get("version", "")
            self.lbl_sub.set_text(f"Serial: {serial}" + (f" • {ver}" if ver else ""))
            if device_info.get("connection"):
                self.lbl_conn.set_text(device_info.get("connection", "Connecting..."))
            if device_info.get("battery_level") is not None:
                self.battery_level_bar.set_value(float(device_info.get("battery_level")))
                chg = " ⚡" if device_info.get("battery_charging") else ""
                self.lbl_bat.set_text(f"{device_info.get('battery_level')}%{chg}")
        else:
            self.lbl_name.set_text("Connecting...")
            self.lbl_sub.set_text(f"Serial: {serial}")
            self.lbl_conn.set_text("Connecting...")

        # Async query detailed info, displays, cameras, and resolution
        def _fetch(target_serial: str):
            info = get_detailed_device_info(target_serial)
            displays = get_device_displays(target_serial)
            cameras = get_device_cameras(target_serial)
            resolution = get_device_resolution(target_serial)

            if self.current_serial != target_serial:
                return

            GLib.idle_add(self._apply_device_data, info, displays, cameras, resolution)

            # Start real-time orientation polling
            self.orientation_monitor.start(
                target_serial, lambda res: self._on_orientation_changed(res)
            )

        threading.Thread(target=_fetch, args=(serial,), daemon=True).start()

    def _apply_device_data(
        self,
        info: Dict[str, Any],
        displays: List[str],
        cameras: List[str],
        resolution: Optional[Tuple[int, int, bool]],
    ) -> bool:
        """Apply newly fetched device details to Hero Card and tabs."""
        model = info.get("model", "Unknown Device")
        self.lbl_name.set_text(model)

        version = info.get("version", "N/A")
        self.lbl_sub.set_text(f"Serial: {self.current_serial} • {version}")
        self.row_device_details.set_subtitle(f"{model} • {version}")

        # Connection Badge
        conn = info.get("connection", "USB")
        self.lbl_conn.set_text(conn)

        # Battery gauge
        bat_level = info.get("battery_level")
        bat_charging = info.get("battery_charging", False)
        if bat_level is not None:
            self.battery_level_bar.set_value(float(bat_level))
            bolt = " ⚡" if bat_charging else ""
            self.lbl_bat.set_text(f"{bat_level}%{bolt}")

            if bat_level >= 80:
                icon_name = "battery-full-charging-symbolic" if bat_charging else "battery-full-symbolic"
            elif bat_level >= 50:
                icon_name = "battery-good-charging-symbolic" if bat_charging else "battery-good-symbolic"
            elif bat_level >= 20:
                icon_name = "battery-low-charging-symbolic" if bat_charging else "battery-low-symbolic"
            else:
                icon_name = "battery-caution-charging-symbolic" if bat_charging else "battery-caution-symbolic"
            self.bat_icon.set_from_icon_name(icon_name)
        else:
            self.battery_level_bar.set_value(0.0)
            self.lbl_bat.set_text("--%")
            self.bat_icon.set_from_icon_name("battery-symbolic")

        # Resolution & Aspect Ratio
        self.last_resolution = resolution
        res_str = info.get("resolution", "N/A")
        ratio = info.get("aspect_ratio", "")
        ratio_tag = f" ({ratio})" if ratio else ""
        self.lbl_res.set_text(f"📺 {res_str} Native{ratio_tag}")

        # Density
        density = info.get("density", "-- DPI")
        self.lbl_dpi.set_text(f"⚡ {density}")
        self.current_density = info.get("density_val")

        # Update Displays dropdown
        self.display_model.splice(0, self.display_model.get_n_items(), [])
        if not displays:
            self.display_model.append("0 (Default)")
        else:
            for d in displays:
                self.display_model.append(str(d))

        # Update Cameras dropdown
        self.camera_model.splice(0, self.camera_model.get_n_items(), [])
        if not cameras:
            self.camera_model.append("None Found")
            self.camera_row.set_sensitive(False)
        else:
            for c in cameras:
                self.camera_model.append(str(c))
            self.camera_row.set_sensitive(True)

        # Update dynamic resolution presets
        self._update_resolution_presets(resolution)

        return False

    def _on_orientation_changed(self, resolution: Tuple[int, int, bool]) -> None:
        """Triggered when OrientationMonitor detects device rotation."""
        self.last_resolution = resolution
        w, h, _ = resolution
        self.lbl_res.set_text(f"📺 {w}x{h} Live")
        self._update_resolution_presets(resolution)

    def _update_resolution_presets(
        self, resolution: Optional[Tuple[int, int, bool]]
    ) -> None:
        """Calculates 5 proportional resolution levels based on device resolution."""
        if not resolution:
            return
        w, h, _ = resolution

        current_text = (
            self.size_combo.get_child().get_text()
            if self.size_combo.get_child()
            else ""
        )
        self.size_combo.remove_all()
        self.size_combo.append_text("Default")

        percentages = [1.0, 0.8, 0.6, 0.4, 0.2]
        labels = ["Native 100%", "Balanced 80%", "Smooth 60%", "Lite 40%", "Minimal 20%"]
        for i, p in enumerate(percentages):
            calc_w = int(w * p)
            calc_h = int(h * p)
            self.size_combo.append_text(f"{calc_w}x{calc_h} ({labels[i]})")

        if current_text and current_text not in ("Calculating...", "Default"):
            if self.size_combo.get_child():
                self.size_combo.get_child().set_text(current_text)
        else:
            self.size_combo.set_active(0)

    def _load_initial_host_telemetry(self) -> None:
        """Loads host compositor and GPU details."""
        def _task():
            telem = get_host_telemetry()
            comp = telem.get("compositor", "Wayland")
            gpu = telem.get("gpu", "Auto (Mesa / DRI)")

            def _apply():
                self.lbl_compositor.set_text(f"🖥 {comp}")
                self.row_telemetry_compositor.set_subtitle(comp)
                self.row_telemetry_gpu.set_subtitle(gpu)

            GLib.idle_add(_apply)

        threading.Thread(target=_task, daemon=True).start()

    # =========================================================================
    # STATE & PROFILES
    # =========================================================================

    def sync_from_window(self) -> None:
        """Synchronize with parent AndyWindow state."""
        if not self.window:
            return
        if hasattr(self.window, "devices") and self.window.devices:
            self.update_devices(self.window.devices)
        if hasattr(self.window, "device_dropdown"):
            idx = self.window.device_dropdown.get_selected()
            if hasattr(self.window, "devices") and 0 <= idx < len(self.window.devices):
                self.on_device_selected(self.window.devices[idx])

    def refresh_profiles(self, select_name: Optional[str] = None) -> None:
        """Refresh profile listings."""
        profiles = list_profiles()
        self.profile_model.splice(0, self.profile_model.get_n_items(), ["Default"])
        target_idx = 0
        for i, p in enumerate(profiles):
            self.profile_model.append(p)
            if select_name and p == select_name:
                target_idx = i + 1

        self.profile_row.set_selected(target_idx)

    def _on_profile_combo_changed(self, combo, pspec) -> None:
        """Load selected profile."""
        idx = combo.get_selected()
        if idx <= 0 or idx >= self.profile_model.get_n_items():
            return
        name = self.profile_model.get_string(idx)
        state = load_profile(name)
        if state:
            self.set_state(state)
            self._set_status(f"Profile loaded: {name}")

    def _on_save_profile_clicked(self, button) -> None:
        """Save current configuration to profile."""
        if self.window and hasattr(self.window, "on_save_profile_clicked"):
            self.window.on_save_profile_clicked()
        else:
            self._prompt_save_profile_dialog()

    def _prompt_save_profile_dialog(self) -> None:
        """Fallback dialog for saving profiles."""
        parent_win = self.window if isinstance(self.window, Gtk.Window) else None
        dialog = Adw.MessageDialog(
            transient_for=parent_win,
            heading="Save Profile",
            body="Enter a name for this profile:",
        )
        entry = Gtk.Entry()
        entry.set_placeholder_text("Profile Name")
        entry.set_margin_start(12)
        entry.set_margin_end(12)
        dialog.set_extra_child(entry)
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("save", "Save")
        dialog.set_response_appearance("save", Adw.ResponseAppearance.SUGGESTED)

        def _on_response(d, resp):
            if resp == "save":
                name = entry.get_text().strip()
                if name:
                    save_profile(name, self.get_state())
                    self.refresh_profiles(select_name=name)
                    self._set_status(f"Profile saved: {name}")
            d.destroy()

        dialog.connect("response", _on_response)
        dialog.present()

    def _on_settings_clicked(self, button) -> None:
        """Open settings dialog."""
        if self.window and hasattr(self.window, "on_settings_clicked"):
            self.window.on_settings_clicked()

    # =========================================================================
    # SCRCPY BUILDER & CONFIG EXTRACTION
    # =========================================================================

    def _get_stream_config(self) -> StreamConfig:
        """Constructs StreamConfig model instance from active UI widgets."""
        fps_val = (
            self.fps_combo.get_active_text()
            or (self.fps_combo.get_child().get_text() if self.fps_combo.get_child() else "Default")
        )
        size_val = (
            self.size_combo.get_active_text()
            or (self.size_combo.get_child().get_text() if self.size_combo.get_child() else "Default")
        )

        return StreamConfig(
            type=self.type_row.get_selected(),
            camera=self.camera_row.get_selected(),
            display=self.display_row.get_selected(),
            fullscreen=self.switch_fullscreen.get_active(),
            borderless=self.switch_borderless.get_active(),
            always_on_top=self.switch_always_on_top.get_active(),
            disable_screensaver=self.switch_disable_screensaver.get_active(),
            codec=self.codec_row.get_selected(),
            fps=fps_val,
            size=size_val,
            bitrate=self.bitrate_row.get_text().strip(),
            orientation=self.orient_row.get_selected(),
            record=self.switch_record.get_active(),
            record_format=self.record_format_row.get_selected(),
            new_display=self.switch_new_display.get_active(),
            camera_torch=self.switch_camera_torch.get_active(),
            flex_display=self.switch_flex_display.get_active(),
            render_fit=self.render_fit_row.get_selected(),
            display_ime_policy=self.ime_policy_row.get_selected(),
            no_vd_destroy_content=self.switch_preserve_content.get_active(),
            start_app=self.entry_start_app.get_text().strip(),
            camera_zoom=self.entry_camera_zoom.get_text().strip(),
            camera_fps=self.camera_fps_row.get_selected(),
            camera_high_speed=self.switch_camera_high_speed.get_active(),
        )

    def _get_advanced_config(self) -> AdvancedConfig:
        """Constructs AdvancedConfig model instance from active UI widgets."""
        return AdvancedConfig(
            audio_codec=self.audio_codec_row.get_selected(),
            audio_dup=self.switch_audio_dup.get_active(),
            audio_source=self.audio_source_row.get_selected(),
            gpu_adapter=self.gpu_row.get_selected(),
            render_driver=self.render_driver_row.get_selected(),
            backend=self.backend_row.get_selected(),
            buffer=self.buffer_row.get_selected(),
            print_fps=self.switch_print_fps.get_active(),
            screen_off=self.switch_screen_off.get_active(),
            stay_awake=self.switch_stay_awake.get_active(),
            no_audio=not self.switch_forward_audio.get_active(),
            read_only=self.switch_read_only.get_active(),
            keyboard_uhid=self.switch_keyboard_uhid.get_active(),
            mouse_uhid=self.switch_mouse_uhid.get_active(),
            gamepad_uhid=self.switch_gamepad_uhid.get_active(),
            mouse_bind=self.mouse_bind_row.get_selected(),
            legacy_paste=self.switch_legacy_paste.get_active(),
            no_clipboard_autosync=self.switch_no_clipboard_sync.get_active(),
            power_off_on_close=self.switch_power_off_close.get_active(),
            no_power_on=self.switch_no_power_on.get_active(),
            time_limit=self.entry_time_limit.get_text().strip(),
            show_touches=self.switch_show_touches.get_active(),
            keep_active=self.switch_keep_active.get_active(),
            timeout=self.timeout_row.get_selected(),
            hwdec=self.hwdec_row.get_selected(),
            no_downsize_on_error=self.switch_no_downsize.get_active(),
            audio_bitrate=self.entry_audio_bitrate.get_text().strip(),
            audio_buffer=self.audio_buffer_row.get_selected(),
        )

    def get_stream_options(self) -> List[str]:
        """Aggregate scrcpy CLI flags from layout settings."""
        stream_cfg = self._get_stream_config()
        adv_cfg = self._get_advanced_config()

        display_str = None
        d_idx = self.display_row.get_selected()
        if d_idx != Gtk.INVALID_LIST_POSITION and self.display_model.get_n_items() > 0:
            display_str = self.display_model.get_string(d_idx)

        camera_str = None
        c_idx = self.camera_row.get_selected()
        if c_idx != Gtk.INVALID_LIST_POSITION and self.camera_model.get_n_items() > 0:
            camera_str = self.camera_model.get_string(c_idx)

        return build_scrcpy_args(
            serial=self.current_serial or "",
            stream=stream_cfg,
            advanced=adv_cfg,
            mode="stream",
            camera_id_str=camera_str,
            display_id_str=display_str,
        )

    def get_environment_overrides(self) -> Dict[str, str]:
        """Aggregate environment variable overrides for GPU PRIME and Wayland backend."""
        return build_environment_overrides(self._get_advanced_config())

    def get_state(self) -> Dict[str, Any]:
        """Serialize layout state for profile saving."""
        return {
            "stream": self._get_stream_config().to_dict(),
            "advanced": self._get_advanced_config().to_dict(),
        }

    def set_state(self, state: Dict[str, Any]) -> None:
        """Restore layout state from profile."""
        if not state:
            return

        stream_state = state.get("stream", {})
        if stream_state:
            self.type_row.set_selected(stream_state.get("type", 0))
            self.camera_row.set_selected(stream_state.get("camera", 0))
            self.display_row.set_selected(stream_state.get("display", 0))
            self.switch_fullscreen.set_active(stream_state.get("fullscreen", False))
            self.switch_borderless.set_active(stream_state.get("borderless", False))
            self.switch_always_on_top.set_active(stream_state.get("always_on_top", False))
            self.switch_disable_screensaver.set_active(stream_state.get("disable_screensaver", False))
            self.codec_row.set_selected(stream_state.get("codec", 0))

            fps = stream_state.get("fps", "Default")
            if self.fps_combo.get_child():
                self.fps_combo.get_child().set_text(str(fps))

            size = stream_state.get("size", "Default")
            if self.size_combo.get_child():
                self.size_combo.get_child().set_text(str(size))

            self.bitrate_row.set_text(str(stream_state.get("bitrate", "")))
            self.orient_row.set_selected(stream_state.get("orientation", 0))
            self.switch_record.set_active(stream_state.get("record", False))
            self.record_format_row.set_selected(stream_state.get("record_format", 0))
            self.switch_new_display.set_active(stream_state.get("new_display", False))
            self.switch_camera_torch.set_active(stream_state.get("camera_torch", False))
            self.switch_flex_display.set_active(stream_state.get("flex_display", False))
            self.render_fit_row.set_selected(stream_state.get("render_fit", 0))
            self.ime_policy_row.set_selected(stream_state.get("display_ime_policy", 0))
            self.switch_preserve_content.set_active(stream_state.get("no_vd_destroy_content", False))
            self.entry_start_app.set_text(str(stream_state.get("start_app") or ""))
            self.entry_camera_zoom.set_text(str(stream_state.get("camera_zoom") or ""))
            self.camera_fps_row.set_selected(stream_state.get("camera_fps", 0))
            self.switch_camera_high_speed.set_active(stream_state.get("camera_high_speed", False))

        adv_state = state.get("advanced", {})
        if adv_state:
            self.audio_codec_row.set_selected(adv_state.get("audio_codec", 0))
            self.switch_audio_dup.set_active(adv_state.get("audio_dup", False))
            self.audio_source_row.set_selected(adv_state.get("audio_source", 0))
            self.gpu_row.set_selected(adv_state.get("gpu_adapter", 0))
            self.render_driver_row.set_selected(adv_state.get("render_driver", 0))
            self.backend_row.set_selected(adv_state.get("backend", 0))
            self.buffer_row.set_selected(adv_state.get("buffer", 0))
            self.switch_print_fps.set_active(adv_state.get("print_fps", False))
            self.switch_screen_off.set_active(adv_state.get("screen_off", False))
            self.switch_stay_awake.set_active(adv_state.get("stay_awake", False))
            self.switch_forward_audio.set_active(not adv_state.get("no_audio", False))
            self.switch_read_only.set_active(adv_state.get("read_only", False))
            self.switch_keyboard_uhid.set_active(adv_state.get("keyboard_uhid", False))
            self.switch_mouse_uhid.set_active(adv_state.get("mouse_uhid", False))
            self.switch_gamepad_uhid.set_active(adv_state.get("gamepad_uhid", False))
            self.mouse_bind_row.set_selected(adv_state.get("mouse_bind", 0))
            self.switch_legacy_paste.set_active(adv_state.get("legacy_paste", False))
            self.switch_no_clipboard_sync.set_active(adv_state.get("no_clipboard_autosync", False))
            self.switch_power_off_close.set_active(adv_state.get("power_off_on_close", False))
            self.switch_no_power_on.set_active(adv_state.get("no_power_on", False))
            self.entry_time_limit.set_text(str(adv_state.get("time_limit", "") or ""))
            self.switch_show_touches.set_active(adv_state.get("show_touches", False))
            self.switch_keep_active.set_active(adv_state.get("keep_active", False))
            self.timeout_row.set_selected(adv_state.get("timeout", 0))
            self.hwdec_row.set_selected(adv_state.get("hwdec", 0))
            self.switch_no_downsize.set_active(adv_state.get("no_downsize_on_error", False))
            self.entry_audio_bitrate.set_text(str(adv_state.get("audio_bitrate", "") or ""))
            self.audio_buffer_row.set_selected(adv_state.get("audio_buffer", 0))

    def cleanup(self) -> None:
        """Stop background monitors upon window close."""
        if hasattr(self, "orientation_monitor"):
            self.orientation_monitor.stop()
