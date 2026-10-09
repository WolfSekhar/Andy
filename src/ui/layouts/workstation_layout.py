"""
Workstation Layout for Andy (Option 1: The Modern Workstation).
Adaptive Two-Pane Adw.NavigationSplitView in GNOME Settings / Cartridges style.
"""
from typing import Any, Dict, List, Optional
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gdk, Gio

from ui.layouts.base_layout import BaseLayout
from core.config import (
    VIDEO_CODECS,
    FPS_PRESETS,
    ORIENTATIONS,
    RENDER_FITS,
    CAMERA_FPS_PRESETS,
    IME_POLICIES,
    AUDIO_SOURCES,
    AUDIO_CODECS,
    AUDIO_BUFFERS,
    BUFFER_PRESETS,
    RENDER_DRIVERS,
    TIMEOUT_PRESETS,
)


def _safe_model(obj: Any, attr_name: str, default_items: list) -> Gio.ListModel:
    """Safely retrieve a Gio.ListModel from an object attribute with fallback."""
    if obj is not None and hasattr(obj, attr_name):
        val = getattr(obj, attr_name)
        if isinstance(val, Gio.ListModel):
            return val
    return Gtk.StringList.new(list(default_items))


class WorkstationLayout(BaseLayout):
    """
    Modern Workstation Layout (Adaptive NavigationSplitView).
    Organized into 6 focused categories:
    - Device &amp; Remote
    - Display &amp; Video
    - Camera Studio
    - Audio &amp; Media
    - Input &amp; Peripherals
    - Engine &amp; System
    """

    def __init__(self, window=None, **kwargs):
        super().__init__(window=window)

        self._is_syncing: bool = False
        self._current_serial: Optional[str] = None
        self._current_device_info: Optional[Dict[str, Any]] = None

        # Root NavigationSplitView
        self.split_view = Adw.NavigationSplitView(
            min_sidebar_width=280,
            max_sidebar_width=360
        )
        self.split_view.set_hexpand(True)
        self.split_view.set_vexpand(True)

        # ---------------------------------------------------------------------
        # 1. Sidebar Setup
        # ---------------------------------------------------------------------
        self._build_sidebar()

        # ---------------------------------------------------------------------
        # 2. Content Area Setup
        # ---------------------------------------------------------------------
        self._build_content()

        # ---------------------------------------------------------------------
        # 3. Initial sync
        # ---------------------------------------------------------------------
        self._load_host_telemetry()
        self.sync_from_window()

        # Select first category by default
        first_row = self.nav_list.get_row_at_index(0)
        if first_row:
            self.nav_list.select_row(first_row)
            self.stack.set_visible_child_name("device")

    def get_widget(self) -> Gtk.Widget:
        """Return the root widget for display in ViewStack."""
        return self.split_view

    # =========================================================================
    # Sidebar Construction
    # =========================================================================

    def _build_sidebar(self):
        sidebar_toolbar = Adw.ToolbarView()
        sidebar_header = Adw.HeaderBar(show_end_title_buttons=False)
        sidebar_header.set_title_widget(
            Adw.WindowTitle(title="Andy", subtitle="scrcpy Controller")
        )

        self.btn_refresh = Gtk.Button(
            icon_name="view-refresh-symbolic",
            tooltip_text="Scan Devices"
        )
        self.btn_refresh.connect("clicked", self._on_refresh_clicked)
        sidebar_header.pack_end(self.btn_refresh)
        sidebar_toolbar.add_top_bar(sidebar_header)

        sidebar_scroll = Gtk.ScrolledWindow()
        sidebar_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        sidebar_box.set_margin_top(12)
        sidebar_box.set_margin_bottom(12)
        sidebar_box.set_margin_start(12)
        sidebar_box.set_margin_end(12)
        sidebar_scroll.set_child(sidebar_box)
        sidebar_toolbar.set_content(sidebar_scroll)

        # Active Device Group
        self.device_group = Adw.PreferencesGroup(title="Active Device")
        self.device_row = Adw.ActionRow(
            title="No devices detected",
            subtitle="Connect an Android device via USB or Wi-Fi"
        )
        self.device_icon = Gtk.Image.new_from_icon_name("phone-symbolic")
        self.device_row.add_prefix(self.device_icon)

        # Device dropdown model
        self.device_model = _safe_model(self.window, "device_model", ["No devices found"])
        self.device_dropdown = Gtk.DropDown(model=self.device_model)
        self.device_dropdown.set_valign(Gtk.Align.CENTER)
        self.device_dropdown.connect("notify::selected", self._on_device_dropdown_changed)
        self.device_row.add_suffix(self.device_dropdown)
        self.device_group.add(self.device_row)
        sidebar_box.append(self.device_group)

        # Navigation Categories
        categories_group = Adw.PreferencesGroup(title="Categories")
        self.nav_list = Gtk.ListBox()
        self.nav_list.add_css_class("navigation-sidebar")
        self.nav_list.set_selection_mode(Gtk.SelectionMode.SINGLE)

        self.categories = [
            ("device", "Device &amp; Remote", "phone-symbolic"),
            ("display", "Display &amp; Video", "display-symbolic"),
            ("camera", "Camera Studio", "camera-web-symbolic"),
            ("audio", "Audio &amp; Media", "audio-speakers-symbolic"),
            ("input", "Input &amp; Peripherals", "input-gaming-symbolic"),
            ("engine", "Engine &amp; System", "preferences-system-symbolic"),
        ]

        for cat_id, title, icon in self.categories:
            row = Adw.ActionRow(title=title)
            row.add_prefix(Gtk.Image.new_from_icon_name(icon))
            row.add_suffix(Gtk.Image.new_from_icon_name("go-next-symbolic"))
            row.cat_id = cat_id
            self.nav_list.append(row)

        self.nav_list.connect("row-activated", self._on_category_selected)
        categories_group.add(self.nav_list)
        sidebar_box.append(categories_group)

        # Host Telemetry Group
        telemetry_group = Adw.PreferencesGroup(title="Host Telemetry")
        self.host_row = Adw.ActionRow(
            title="Wayland Native",
            subtitle="Detecting display server &amp; GPU..."
        )
        self.host_row.add_prefix(Gtk.Image.new_from_icon_name("computer-symbolic"))
        telemetry_group.add(self.host_row)
        sidebar_box.append(telemetry_group)

        self.sidebar_page = Adw.NavigationPage(child=sidebar_toolbar, title="Andy")
        self.split_view.set_sidebar(self.sidebar_page)

    # =========================================================================
    # Content Area Construction
    # =========================================================================

    def _build_content(self):
        content_toolbar = Adw.ToolbarView()
        self.content_header = Adw.HeaderBar()
        self.window_title = Adw.WindowTitle(
            title="Device &amp; Remote",
            subtitle="Modern Workstation"
        )
        self.content_header.set_title_widget(self.window_title)

        # Persistent Action Hub in Content Header
        self.btn_mk = Gtk.Button()
        mk_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.mk_icon = Gtk.Image.new_from_icon_name("input-keyboard-symbolic")
        self.mk_label = Gtk.Label(label="Connect M/K")
        mk_box.append(self.mk_icon)
        mk_box.append(self.mk_label)
        self.btn_mk.set_child(mk_box)
        self.btn_mk.add_css_class("pill")
        self.btn_mk.set_tooltip_text("Send Mouse and Keyboard without streaming video")
        self.btn_mk.connect("clicked", self._on_connect_mk_clicked)
        self.btn_mk.get_label = lambda: self.mk_label.get_text()
        self.btn_mk.set_label = lambda txt: self.mk_label.set_text(txt)

        self.btn_stream = Gtk.Button()
        stream_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.stream_icon = Gtk.Image.new_from_icon_name("media-playback-start-symbolic")
        self.stream_label = Gtk.Label(label="STREAM")
        stream_box.append(self.stream_icon)
        stream_box.append(self.stream_label)
        self.btn_stream.set_child(stream_box)
        self.btn_stream.add_css_class("pill")
        self.btn_stream.add_css_class("suggested-action")
        self.btn_stream.connect("clicked", self._on_stream_clicked)
        self.btn_stream.get_label = lambda: self.stream_label.get_text()
        self.btn_stream.set_label = lambda txt: self.stream_label.set_text(txt)

        self.content_header.pack_end(self.btn_stream)
        self.content_header.pack_end(self.btn_mk)
        content_toolbar.add_top_bar(self.content_header)

        # Scrolled content view
        content_scroll = Gtk.ScrolledWindow()
        content_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        content_clamp = Adw.Clamp(maximum_size=840)
        content_clamp.set_margin_top(16)
        content_clamp.set_margin_bottom(24)
        content_clamp.set_margin_start(16)
        content_clamp.set_margin_end(16)

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        content_clamp.set_child(self.stack)
        content_scroll.set_child(content_clamp)
        content_toolbar.set_content(content_scroll)

        # Build each content page
        self._build_page_device()
        self._build_page_display()
        self._build_page_camera()
        self._build_page_audio()
        self._build_page_input()
        self._build_page_engine()

        self.content_page = Adw.NavigationPage(child=content_toolbar, title="Workstation")
        self.split_view.set_content(self.content_page)

    # =========================================================================
    # Page 1: Device & Remote
    # =========================================================================

    def _build_page_device(self):
        page = Adw.PreferencesPage()

        # Telemetry & Specs
        grp_spec = Adw.PreferencesGroup(title="Device Telemetry &amp; Specs")
        self.row_spec_model = Adw.ActionRow(title="Model", subtitle="N/A")
        self.row_spec_model.add_prefix(Gtk.Image.new_from_icon_name("phone-symbolic"))
        grp_spec.add(self.row_spec_model)

        self.row_spec_version = Adw.ActionRow(title="Android Version", subtitle="N/A")
        self.row_spec_version.add_prefix(Gtk.Image.new_from_icon_name("emblem-system-symbolic"))
        grp_spec.add(self.row_spec_version)

        self.row_spec_res = Adw.ActionRow(title="Display Resolution", subtitle="N/A")
        self.row_spec_res.add_prefix(Gtk.Image.new_from_icon_name("video-display-symbolic"))
        grp_spec.add(self.row_spec_res)

        self.row_spec_battery = Adw.ActionRow(title="Battery", subtitle="N/A")
        self.row_spec_battery.add_prefix(Gtk.Image.new_from_icon_name("battery-symbolic"))
        grp_spec.add(self.row_spec_battery)

        self.row_spec_density = Adw.ActionRow(title="Screen Density (DPI)", subtitle="N/A")
        self.row_spec_density.add_prefix(Gtk.Image.new_from_icon_name("display-symbolic"))

        density_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        density_box.add_css_class("linked")
        density_box.set_valign(Gtk.Align.CENTER)
        btn_d_down = Gtk.Button(label="-20")
        btn_d_down.set_tooltip_text("Decrease Screen Density (-20 DPI)")
        btn_d_down.connect("clicked", lambda b: self._on_density_adjust(-20))
        btn_d_up = Gtk.Button(label="+20")
        btn_d_up.set_tooltip_text("Increase Screen Density (+20 DPI)")
        btn_d_up.connect("clicked", lambda b: self._on_density_adjust(20))
        btn_d_reset = Gtk.Button(label="Reset")
        btn_d_reset.set_tooltip_text("Reset Screen Density to physical default")
        btn_d_reset.connect("clicked", lambda b: self._on_density_reset())
        density_box.append(btn_d_down)
        density_box.append(btn_d_up)
        density_box.append(btn_d_reset)
        self.row_spec_density.add_suffix(density_box)
        grp_spec.add(self.row_spec_density)
        page.add(grp_spec)

        # Quick Remote Navigation
        grp_nav = Adw.PreferencesGroup(title="Quick Remote Control")
        row_nav = Adw.ActionRow(title="Virtual Navigation Bar")
        btn_nav_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        btn_nav_box.set_valign(Gtk.Align.CENTER)

        btn_back = Gtk.Button(icon_name="go-previous-symbolic", tooltip_text="Back (KEYCODE_BACK)")
        btn_back.connect("clicked", lambda b: self._on_keyevent(4, "Back"))
        btn_home = Gtk.Button(icon_name="user-home-symbolic", tooltip_text="Home (KEYCODE_HOME)")
        btn_home.connect("clicked", lambda b: self._on_keyevent(3, "Home"))
        btn_recents = Gtk.Button(icon_name="view-grid-symbolic", tooltip_text="Recents (KEYCODE_APP_SWITCH)")
        btn_recents.connect("clicked", lambda b: self._on_keyevent(187, "Recents"))
        btn_nav_box.append(btn_back)
        btn_nav_box.append(btn_home)
        btn_nav_box.append(btn_recents)
        row_nav.add_suffix(btn_nav_box)
        grp_nav.add(row_nav)

        # System & Clipboard Actions
        row_tools = Adw.ActionRow(title="System &amp; Quick Actions")
        tools_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        tools_box.set_valign(Gtk.Align.CENTER)

        btn_notif = Gtk.Button(icon_name="preferences-system-notifications-symbolic", tooltip_text="Notifications")
        btn_notif.connect("clicked", lambda b: self._on_statusbar("notifications"))
        btn_settings = Gtk.Button(icon_name="emblem-system-symbolic", tooltip_text="Quick Settings")
        btn_settings.connect("clicked", lambda b: self._on_statusbar("settings"))
        btn_paste = Gtk.Button(icon_name="edit-paste-symbolic", tooltip_text="Paste PC Clipboard")
        btn_paste.connect("clicked", lambda b: self._on_paste())
        btn_shot = Gtk.Button(icon_name="camera-photo-symbolic", tooltip_text="Take Screenshot")
        btn_shot.connect("clicked", lambda b: self._on_screenshot())
        btn_power = Gtk.Button(icon_name="system-shutdown-symbolic", tooltip_text="Power Screen Toggle")
        btn_power.connect("clicked", lambda b: self._on_power())

        tools_box.append(btn_notif)
        tools_box.append(btn_settings)
        tools_box.append(btn_paste)
        tools_box.append(btn_shot)
        tools_box.append(btn_power)
        row_tools.add_suffix(tools_box)
        grp_nav.add(row_tools)

        page.add(grp_nav)
        self.stack.add_named(page, "device")

    # =========================================================================
    # Page 2: Display & Video
    # =========================================================================

    def _build_page_display(self):
        page = Adw.PreferencesPage()

        # Display Source & Quality
        grp_disp = Adw.PreferencesGroup(title="Display Source &amp; Quality")

        self.row_stream_type = Adw.ComboRow(
            title="Stream Mode",
            model=Gtk.StringList.new(["Screen Stream", "Camera Stream"])
        )
        self.row_stream_type.connect("notify::selected", self._on_stream_type_changed)
        grp_disp.add(self.row_stream_type)

        # Display Target
        from gi.repository import Gio
        sc = getattr(self.window, "stream_card", None)
        _disp_model = getattr(sc, "display_model", None)
        disp_model = _disp_model if isinstance(_disp_model, Gio.ListModel) else Gtk.StringList.new(["0 (Default)"])
        self.row_display = Adw.ComboRow(title="Active Display Target", model=disp_model)
        self.row_display.connect("notify::selected", lambda r, p: self._sync_to_window())
        grp_disp.add(self.row_display)

        # Codec
        _codec_model = getattr(sc, "codec_model", None)
        codec_model = _codec_model if isinstance(_codec_model, Gio.ListModel) else Gtk.StringList.new(list(VIDEO_CODECS))
        self.row_codec = Adw.ComboRow(title="Video Codec", model=codec_model)
        self.row_codec.connect("notify::selected", lambda r, p: self._sync_to_window())
        grp_disp.add(self.row_codec)

        # Max FPS
        self.row_fps = Adw.ComboRow(
            title="Maximum Framerate",
            model=Gtk.StringList.new(list(FPS_PRESETS))
        )
        self.row_fps.connect("notify::selected", self._on_fps_changed)
        grp_disp.add(self.row_fps)

        # Max Size
        self.row_size = Adw.EntryRow(title="Max Resolution Size (e.g. 1920, 1280)")
        self.row_size.connect("notify::text", lambda r, p: self._sync_to_window())
        grp_disp.add(self.row_size)

        # Bitrate
        self.row_bitrate = Adw.EntryRow(title="Video Bitrate Limit (e.g. 8M, 16M)")
        self.row_bitrate.connect("notify::text", lambda r, p: self._sync_to_window())
        grp_disp.add(self.row_bitrate)

        # Orientation
        _orient_model = getattr(sc, "orient_model", None)
        orient_model = _orient_model if isinstance(_orient_model, Gio.ListModel) else Gtk.StringList.new(list(ORIENTATIONS))
        self.row_orient = Adw.ComboRow(title="Lock Video Orientation", model=orient_model)
        self.row_orient.connect("notify::selected", lambda r, p: self._sync_to_window())
        grp_disp.add(self.row_orient)

        # Start App
        self.entry_start_app = Adw.EntryRow(title="Start App (Package Name)")
        self.entry_start_app.connect("notify::text", lambda r, p: self._sync_to_window())
        grp_disp.add(self.entry_start_app)

        page.add(grp_disp)

        # Virtual Display & Window Settings
        grp_vd = Adw.PreferencesGroup(title="Virtual Display &amp; Window (scrcpy 5.0)")
        exp_vd = Adw.ExpanderRow(title="Virtual Secondary Display Controls")

        self.row_new_display = Adw.SwitchRow(
            title="Virtual Display Mode",
            subtitle="Create new secondary virtual screen (Android 13+)"
        )
        self.row_new_display.connect("notify::active", lambda r, p: self._sync_to_window())
        exp_vd.add_row(self.row_new_display)

        self.row_flex_display = Adw.SwitchRow(
            title="Flex Display",
            subtitle="Allow dynamic display resizing for virtual display"
        )
        self.row_flex_display.connect("notify::active", lambda r, p: self._sync_to_window())
        exp_vd.add_row(self.row_flex_display)

        _ime_model = getattr(sc, "display_ime_policy_model", None)
        ime_model = _ime_model if isinstance(_ime_model, Gio.ListModel) else Gtk.StringList.new(list(IME_POLICIES))
        self.row_ime_policy = Adw.ComboRow(title="Virtual Display IME Policy", model=ime_model)
        self.row_ime_policy.connect("notify::selected", lambda r, p: self._sync_to_window())
        exp_vd.add_row(self.row_ime_policy)

        self.row_no_vd_destroy = Adw.SwitchRow(
            title="Preserve Display Content",
            subtitle="Do not destroy content when virtual display closes"
        )
        self.row_no_vd_destroy.connect("notify::active", lambda r, p: self._sync_to_window())
        exp_vd.add_row(self.row_no_vd_destroy)

        _fit_model = getattr(getattr(sc, "window_section", None), "render_fit_model", None)
        fit_model = _fit_model if isinstance(_fit_model, Gio.ListModel) else Gtk.StringList.new(list(RENDER_FITS))
        self.row_render_fit = Adw.ComboRow(title="Render Fit", model=fit_model)
        self.row_render_fit.connect("notify::selected", lambda r, p: self._sync_to_window())
        exp_vd.add_row(self.row_render_fit)

        grp_vd.add(exp_vd)

        self.row_fullscreen = Adw.SwitchRow(title="Fullscreen Mode")
        self.row_fullscreen.connect("notify::active", lambda r, p: self._sync_to_window())
        grp_vd.add(self.row_fullscreen)

        self.row_borderless = Adw.SwitchRow(title="Borderless Window")
        self.row_borderless.connect("notify::active", lambda r, p: self._sync_to_window())
        grp_vd.add(self.row_borderless)

        self.row_always_on_top = Adw.SwitchRow(title="Always On Top")
        self.row_always_on_top.connect("notify::active", lambda r, p: self._sync_to_window())
        grp_vd.add(self.row_always_on_top)

        self.row_screensaver = Adw.SwitchRow(title="Disable Screensaver")
        self.row_screensaver.connect("notify::active", lambda r, p: self._sync_to_window())
        grp_vd.add(self.row_screensaver)

        page.add(grp_vd)

        # Video Recording
        grp_rec = Adw.PreferencesGroup(title="Video Recording")
        self.row_record = Adw.SwitchRow(
            title="Record Stream Session",
            subtitle="Save video/audio directly to file"
        )
        self.row_record.connect("notify::active", lambda r, p: self._sync_to_window())
        grp_rec.add(self.row_record)

        _rec_model = getattr(sc, "record_format_model", None)
        rec_model = _rec_model if isinstance(_rec_model, Gio.ListModel) else Gtk.StringList.new(["mp4", "mkv"])
        self.row_record_format = Adw.ComboRow(title="Recording Container Format", model=rec_model)
        self.row_record_format.connect("notify::selected", lambda r, p: self._sync_to_window())
        grp_rec.add(self.row_record_format)

        page.add(grp_rec)
        self.stack.add_named(page, "display")

    # =========================================================================
    # Page 3: Camera Studio
    # =========================================================================

    def _build_page_camera(self):
        page = Adw.PreferencesPage()
        grp_cam = Adw.PreferencesGroup(title="Camera Forwarding")

        sc = getattr(self.window, "stream_card", None)
        _cam_model = getattr(sc, "camera_model", None)
        cam_model = _cam_model if isinstance(_cam_model, Gio.ListModel) else Gtk.StringList.new(["0 (Back Camera)", "1 (Front Camera)"])
        self.row_camera = Adw.ComboRow(title="Select Camera", model=cam_model)
        self.row_camera.connect("notify::selected", lambda r, p: self._sync_to_window())
        grp_cam.add(self.row_camera)

        self.row_camera_torch = Adw.SwitchRow(
            title="Camera Torch (Flashlight)",
            subtitle="Turn on flashlight during stream"
        )
        self.row_camera_torch.connect("notify::active", lambda r, p: self._sync_to_window())
        grp_cam.add(self.row_camera_torch)

        _fps_model = getattr(getattr(sc, "camera_section", None), "camera_fps_model", None)
        fps_model = _fps_model if isinstance(_fps_model, Gio.ListModel) else Gtk.StringList.new(list(CAMERA_FPS_PRESETS))
        self.row_camera_fps = Adw.ComboRow(title="Camera Framerate", model=fps_model)
        self.row_camera_fps.connect("notify::selected", lambda r, p: self._sync_to_window())
        grp_cam.add(self.row_camera_fps)

        self.row_camera_high_speed = Adw.SwitchRow(
            title="High-Speed Sensor Mode",
            subtitle="Enable high-speed camera sensor profile"
        )
        self.row_camera_high_speed.connect("notify::active", lambda r, p: self._sync_to_window())
        grp_cam.add(self.row_camera_high_speed)

        self.row_camera_zoom = Adw.EntryRow(title="Camera Zoom Multiplier (e.g. 1.0, 2.5)")
        self.row_camera_zoom.connect("notify::text", lambda r, p: self._sync_to_window())
        grp_cam.add(self.row_camera_zoom)

        page.add(grp_cam)
        self.stack.add_named(page, "camera")

    # =========================================================================
    # Page 4: Audio & Media
    # =========================================================================

    def _build_page_audio(self):
        page = Adw.PreferencesPage()
        grp_aud = Adw.PreferencesGroup(title="Audio Forwarding &amp; Latency")

        ac = getattr(self.window, "advanced_card", None)

        self.row_forward_audio = Adw.SwitchRow(
            title="Forward Audio",
            subtitle="Stream device sound to host speakers"
        )
        self.row_forward_audio.set_active(True)
        self.row_forward_audio.connect("notify::active", lambda r, p: self._sync_to_window())
        grp_aud.add(self.row_forward_audio)

        src_model = _safe_model(ac, "audio_source_model", list(AUDIO_SOURCES))
        self.row_audio_source = Adw.ComboRow(title="Audio Source", model=src_model)
        self.row_audio_source.connect("notify::selected", lambda r, p: self._sync_to_window())
        grp_aud.add(self.row_audio_source)

        aud_codec_model = _safe_model(ac, "audio_codec_model", list(AUDIO_CODECS))
        self.row_audio_codec = Adw.ComboRow(title="Audio Codec", model=aud_codec_model)
        self.row_audio_codec.connect("notify::selected", lambda r, p: self._sync_to_window())
        grp_aud.add(self.row_audio_codec)

        buf_model = _safe_model(ac, "audio_buffer_model", list(AUDIO_BUFFERS))
        self.row_audio_buffer = Adw.ComboRow(title="Audio Buffer Latency", model=buf_model)
        self.row_audio_buffer.connect("notify::selected", lambda r, p: self._sync_to_window())
        grp_aud.add(self.row_audio_buffer)

        self.row_audio_bitrate = Adw.EntryRow(title="Audio Bitrate (e.g. 128K, 192K)")
        self.row_audio_bitrate.connect("notify::text", lambda r, p: self._sync_to_window())
        grp_aud.add(self.row_audio_bitrate)

        self.row_audio_dup = Adw.SwitchRow(
            title="Duplicate Audio",
            subtitle="Play on phone and PC simultaneously"
        )
        self.row_audio_dup.connect("notify::active", lambda r, p: self._sync_to_window())
        grp_aud.add(self.row_audio_dup)

        page.add(grp_aud)
        self.stack.add_named(page, "audio")

    # =========================================================================
    # Page 5: Input & Peripherals
    # =========================================================================

    def _build_page_input(self):
        page = Adw.PreferencesPage()
        grp_inp = Adw.PreferencesGroup(title="HID Hardware Passthrough")

        ac = getattr(self.window, "advanced_card", None)

        self.row_keyboard_uhid = Adw.SwitchRow(
            title="Keyboard UHID Mode",
            subtitle="Forward Linux keyboard as native hardware"
        )
        self.row_keyboard_uhid.connect("notify::active", lambda r, p: self._sync_to_window())
        grp_inp.add(self.row_keyboard_uhid)

        self.row_mouse_uhid = Adw.SwitchRow(
            title="Mouse UHID Mode",
            subtitle="Forward mouse with raw relative motion"
        )
        self.row_mouse_uhid.connect("notify::active", lambda r, p: self._sync_to_window())
        grp_inp.add(self.row_mouse_uhid)

        self.row_gamepad_uhid = Adw.SwitchRow(
            title="Gamepad UHID Mode (scrcpy 5.0)",
            subtitle="Forward Xbox/DualSense controller as Android gamepad"
        )
        self.row_gamepad_uhid.connect("notify::active", lambda r, p: self._sync_to_window())
        grp_inp.add(self.row_gamepad_uhid)

        bind_model = _safe_model(ac, "mouse_bind_model", ["Default", "Forward/Back", "None"])
        self.row_mouse_bind = Adw.ComboRow(title="Mouse Button Bindings", model=bind_model)
        self.row_mouse_bind.connect("notify::selected", lambda r, p: self._sync_to_window())
        grp_inp.add(self.row_mouse_bind)

        self.row_legacy_paste = Adw.SwitchRow(
            title="Legacy Paste",
            subtitle="Inject keystrokes for restricted password fields"
        )
        self.row_legacy_paste.connect("notify::active", lambda r, p: self._sync_to_window())
        grp_inp.add(self.row_legacy_paste)

        self.row_no_clip = Adw.SwitchRow(
            title="Disable Clipboard Autosync",
            subtitle="Do not synchronize clipboard between PC and phone"
        )
        self.row_no_clip.connect("notify::active", lambda r, p: self._sync_to_window())
        grp_inp.add(self.row_no_clip)

        self.row_read_only = Adw.SwitchRow(
            title="Read-Only Mode",
            subtitle="Disable all touch, keyboard, and mouse inputs"
        )
        self.row_read_only.connect("notify::active", lambda r, p: self._sync_to_window())
        grp_inp.add(self.row_read_only)

        self.row_show_touches = Adw.SwitchRow(
            title="Show Touches",
            subtitle="Display touch point circles on screen"
        )
        self.row_show_touches.connect("notify::active", lambda r, p: self._sync_to_window())
        grp_inp.add(self.row_show_touches)

        page.add(grp_inp)
        self.stack.add_named(page, "input")

    # =========================================================================
    # Page 6: Engine & System
    # =========================================================================

    def _build_page_engine(self):
        page = Adw.PreferencesPage()
        grp_eng = Adw.PreferencesGroup(title="Hardware Acceleration &amp; System")

        ac = getattr(self.window, "advanced_card", None)

        hw_model = _safe_model(ac, "hwdec_model", ["Auto", "vaapi", "disabled"])
        self.row_hwdec = Adw.ComboRow(title="Hardware Video Decoding", model=hw_model)
        self.row_hwdec.connect("notify::selected", lambda r, p: self._sync_to_window())
        grp_eng.add(self.row_hwdec)

        driver_model = _safe_model(ac, "render_driver_model", list(RENDER_DRIVERS))
        self.row_render_driver = Adw.ComboRow(title="Render Driver", model=driver_model)
        self.row_render_driver.connect("notify::selected", lambda r, p: self._sync_to_window())
        grp_eng.add(self.row_render_driver)

        gpu_model = _safe_model(ac, "gpu_model", ["Default", "Auto"])
        self.row_gpu = Adw.ComboRow(title="GPU Adapter Selection", model=gpu_model)
        self.row_gpu.connect("notify::selected", lambda r, p: self._sync_to_window())
        grp_eng.add(self.row_gpu)

        vbuf_model = _safe_model(ac, "buffer_model", list(BUFFER_PRESETS))
        self.row_vbuf = Adw.ComboRow(title="Video Buffer Latency", model=vbuf_model)
        self.row_vbuf.connect("notify::selected", lambda r, p: self._sync_to_window())
        grp_eng.add(self.row_vbuf)

        self.row_no_downsize = Adw.SwitchRow(
            title="Disable Downsize on Error",
            subtitle="Prevent automatic resolution drop on encoder error"
        )
        self.row_no_downsize.connect("notify::active", lambda r, p: self._sync_to_window())
        grp_eng.add(self.row_no_downsize)

        self.row_screen_off = Adw.SwitchRow(
            title="Turn Screen Off During Stream",
            subtitle="Save battery and prevent AMOLED burn-in"
        )
        self.row_screen_off.set_active(True)
        self.row_screen_off.connect("notify::active", lambda r, p: self._sync_to_window())
        grp_eng.add(self.row_screen_off)

        self.row_stay_awake = Adw.SwitchRow(
            title="Stay Awake While Connected",
            subtitle="Prevent Android device from sleeping"
        )
        self.row_stay_awake.set_active(True)
        self.row_stay_awake.connect("notify::active", lambda r, p: self._sync_to_window())
        grp_eng.add(self.row_stay_awake)

        self.row_power_off_close = Adw.SwitchRow(
            title="Power Off Device on Close",
            subtitle="Lock phone when stream session ends"
        )
        self.row_power_off_close.connect("notify::active", lambda r, p: self._sync_to_window())
        grp_eng.add(self.row_power_off_close)

        self.row_no_power_on = Adw.SwitchRow(
            title="Do Not Power On at Start",
            subtitle="Do not turn screen on when launching session"
        )
        self.row_no_power_on.connect("notify::active", lambda r, p: self._sync_to_window())
        grp_eng.add(self.row_no_power_on)

        self.row_print_fps = Adw.SwitchRow(
            title="Print FPS Telemetry",
            subtitle="Log real-time framerate to terminal"
        )
        self.row_print_fps.connect("notify::active", lambda r, p: self._sync_to_window())
        grp_eng.add(self.row_print_fps)

        self.row_time_limit = Adw.EntryRow(title="Session Time Limit (seconds)")
        self.row_time_limit.connect("notify::text", lambda r, p: self._sync_to_window())
        grp_eng.add(self.row_time_limit)

        timeout_model = _safe_model(ac, "timeout_model", list(TIMEOUT_PRESETS))
        self.row_timeout = Adw.ComboRow(title="Display Inactivity Timeout", model=timeout_model)
        self.row_timeout.connect("notify::selected", lambda r, p: self._sync_to_window())
        grp_eng.add(self.row_timeout)

        page.add(grp_eng)
        self.stack.add_named(page, "engine")

    # =========================================================================
    # Navigation & Event Handlers
    # =========================================================================

    def _on_category_selected(self, listbox, row):
        if row and hasattr(row, 'cat_id'):
            self.stack.set_visible_child_name(row.cat_id)
            self.window_title.set_title(row.get_title())
            if self.split_view.get_collapsed():
                self.split_view.set_show_content(True)

    def _on_stream_type_changed(self, combo, pspec):
        is_cam = (combo.get_selected() == 1)
        if self.window and hasattr(self.window, "stream_card"):
            self.window.stream_card.type_dropdown.set_selected(combo.get_selected())
        # Automatically navigate to camera tab if selected
        if is_cam:
            self.stack.set_visible_child_name("camera")
            self.window_title.set_title("Camera Studio")
            camera_row = self.nav_list.get_row_at_index(2)
            if camera_row:
                self.nav_list.select_row(camera_row)

    def _on_fps_changed(self, combo, pspec):
        if self._is_syncing:
            return
        idx = combo.get_selected()
        if 0 <= idx < len(FPS_PRESETS):
            fps_val = FPS_PRESETS[idx]
            if self.window and hasattr(self.window, "stream_card"):
                try:
                    self.window.stream_card.fps_combo.get_child().set_text(fps_val)
                except Exception:
                    pass

    def _on_device_dropdown_changed(self, dropdown, pspec):
        if self._is_syncing:
            return
        idx = dropdown.get_selected()
        if idx != Gtk.INVALID_LIST_POSITION and self.window:
            if hasattr(self.window, "device_dropdown"):
                if self.window.device_dropdown.get_selected() != idx:
                    self.window.device_dropdown.set_selected(idx)

    def _on_refresh_clicked(self, button):
        if self.window and hasattr(self.window, "refresh_devices"):
            self.window.refresh_devices()

    def _on_stream_clicked(self, button):
        if self.window and hasattr(self.window, "on_play_clicked"):
            self.sync_to_window()
            self.window.on_play_clicked(button)

    def _on_connect_mk_clicked(self, button):
        if self.window and hasattr(self.window, "on_connect_mk_clicked"):
            self.sync_to_window()
            self.window.on_connect_mk_clicked(button)

    # =========================================================================
    # Device and Lifecycle Hooks (from BaseLayout)
    # =========================================================================

    def update_devices(self, devices: List[Dict[str, Any]]):
        """Called when connected devices list updates."""
        has_devices = bool(devices)
        self.btn_stream.set_sensitive(has_devices)
        self.btn_mk.set_sensitive(has_devices)
        self.device_dropdown.set_sensitive(has_devices)

        if has_devices:
            first = devices[0]
            self.on_device_selected(first)
        else:
            self._current_serial = None
            self._current_device_info = None
            self.device_row.set_title("No devices found")
            self.device_row.set_subtitle("Connect an Android device via USB or Wi-Fi")
            self.row_spec_model.set_subtitle("N/A")
            self.row_spec_version.set_subtitle("N/A")
            self.row_spec_res.set_subtitle("N/A")
            self.row_spec_battery.set_subtitle("N/A")
            self.row_spec_density.set_subtitle("N/A")

    def on_device_selected(self, device_info: Optional[Any] = None):
        """Called when active Android device is selected."""
        serial = None
        self._current_device_info = None
        if isinstance(device_info, dict):
            serial = device_info.get("serial")
            self._current_device_info = device_info
        elif isinstance(device_info, str):
            serial = device_info
            if self.window and hasattr(self.window, "devices"):
                for d in self.window.devices:
                    if d.get("serial") == serial:
                        self._current_device_info = d
                        break
        elif device_info is None and self.window and hasattr(self.window, "devices") and self.window.devices:
            idx = self.window.device_dropdown.get_selected() if hasattr(self.window, "device_dropdown") else 0
            if 0 <= idx < len(self.window.devices):
                self._current_device_info = self.window.devices[idx]
                serial = self._current_device_info.get("serial")

        self._current_serial = serial

        if self._current_device_info:
            dev_name = self._current_device_info.get("display_name", self._current_device_info.get("model", "Android Device"))
            state = self._current_device_info.get("state", "device")
            self.device_row.set_title(dev_name)
            self.device_row.set_subtitle(f"{serial or ''} • {state}")
            self.btn_stream.set_sensitive(True)
            self.btn_mk.set_sensitive(True)
        else:
            self.device_row.set_title("No devices found")
            self.device_row.set_subtitle("Connect an Android device via USB or Wi-Fi")
            self.btn_stream.set_sensitive(False)
            self.btn_mk.set_sensitive(False)

        # Update specs from window.details_card if available
        self._update_specs_ui()

    def _update_specs_ui(self):
        dc = getattr(self.window, "details_card", None)
        if dc:
            if hasattr(dc, "row_model"):
                self.row_spec_model.set_subtitle(dc.row_model.get_subtitle() or "N/A")
            if hasattr(dc, "row_version"):
                self.row_spec_version.set_subtitle(dc.row_version.get_subtitle() or "N/A")
            if hasattr(dc, "row_resolution"):
                self.row_spec_res.set_subtitle(dc.row_resolution.get_subtitle() or "N/A")
            if hasattr(dc, "row_battery"):
                self.row_spec_battery.set_subtitle(dc.row_battery.get_subtitle() or "N/A")
            if hasattr(dc, "row_density"):
                self.row_spec_density.set_subtitle(dc.row_density.get_subtitle() or "N/A")

    def set_stream_state(self, active: bool, mode: str = "stream"):
        """Updates Stream / M/K buttons and widget sensitivity during streaming."""
        if active:
            if mode == "stream":
                self.btn_stream.set_label("STOP")
                self.btn_stream.set_icon_name("media-playback-stop-symbolic")
                self.btn_stream.remove_css_class("suggested-action")
                self.btn_stream.add_css_class("destructive-action")
                self.btn_mk.set_sensitive(False)
            else:
                self.btn_mk.set_label("DISCONNECT")
                self.btn_mk.set_icon_name("media-playback-stop-symbolic")
                self.btn_mk.add_css_class("destructive-action")
                self.btn_stream.set_sensitive(False)

            self.btn_refresh.set_sensitive(False)
            self.device_dropdown.set_sensitive(False)
            self.stack.set_sensitive(False)
        else:
            self.btn_stream.set_label("STREAM")
            self.btn_stream.set_icon_name("media-playback-start-symbolic")
            self.btn_stream.remove_css_class("destructive-action")
            self.btn_stream.add_css_class("suggested-action")
            self.btn_stream.set_sensitive(bool(self._current_serial))

            self.btn_mk.set_label("Connect M/K")
            self.btn_mk.set_icon_name("input-keyboard-symbolic")
            self.btn_mk.remove_css_class("destructive-action")
            self.btn_mk.set_sensitive(bool(self._current_serial))

            self.btn_refresh.set_sensitive(True)
            self.device_dropdown.set_sensitive(True)
            self.stack.set_sensitive(True)

    # =========================================================================
    # Synchronization with Window / Cards
    # =========================================================================

    def sync_from_window(self):
        """Pulls settings from window.stream_card and window.advanced_card into layout widgets."""
        if self._is_syncing or not self.window:
            return
        self._is_syncing = True
        try:
            def _safe_set_sel(combo_row, val):
                try:
                    if isinstance(val, int) and combo_row.get_model() and 0 <= val < combo_row.get_model().get_n_items():
                        combo_row.set_selected(val)
                except Exception:
                    pass

            def _safe_set_active(switch_row, val):
                try:
                    if isinstance(val, bool):
                        switch_row.set_active(val)
                except Exception:
                    pass

            def _safe_set_text(entry_row, val):
                try:
                    if isinstance(val, str):
                        entry_row.set_text(val)
                except Exception:
                    pass

            sc = getattr(self.window, "stream_card", None)
            ac = getattr(self.window, "advanced_card", None)

            if sc:
                _safe_set_sel(self.row_stream_type, sc.type_dropdown.get_selected())
                if hasattr(sc, "display_dropdown"):
                    _safe_set_sel(self.row_display, sc.display_dropdown.get_selected())
                _safe_set_sel(self.row_codec, sc.codec_dropdown.get_selected())
                _safe_set_sel(self.row_orient, sc.orient_dropdown.get_selected())
                _safe_set_text(self.row_bitrate, sc.bitrate_row.get_text())
                _safe_set_text(self.entry_start_app, sc.param_start_app.get_text())
                _safe_set_active(self.row_new_display, sc.param_new_display.get_active())
                _safe_set_active(self.row_flex_display, sc.param_flex_display.get_active())
                _safe_set_sel(self.row_ime_policy, sc.param_display_ime_policy.get_selected())
                _safe_set_active(self.row_no_vd_destroy, sc.param_no_vd_destroy_content.get_active())
                _safe_set_sel(self.row_render_fit, sc.render_fit_dropdown.get_selected())
                _safe_set_active(self.row_fullscreen, sc.param_fullscreen.get_active())
                _safe_set_active(self.row_borderless, sc.param_borderless.get_active())
                _safe_set_active(self.row_always_on_top, sc.param_always_on_top.get_active())
                _safe_set_active(self.row_screensaver, sc.param_disable_screensaver.get_active())
                _safe_set_active(self.row_record, sc.param_record.get_active())
                _safe_set_sel(self.row_record_format, sc.record_format_dropdown.get_selected())
                if hasattr(sc, "camera_dropdown"):
                    _safe_set_sel(self.row_camera, sc.camera_dropdown.get_selected())
                _safe_set_active(self.row_camera_torch, sc.param_camera_torch.get_active())
                _safe_set_sel(self.row_camera_fps, sc.param_camera_fps.get_selected())
                _safe_set_active(self.row_camera_high_speed, sc.param_camera_high_speed.get_active())
                _safe_set_text(self.row_camera_zoom, sc.param_camera_zoom.get_text())

                # FPS preset sync
                try:
                    fps_text = sc.fps_combo.get_active_text() or (sc.fps_combo.get_child().get_text() if hasattr(sc.fps_combo, "get_child") and sc.fps_combo.get_child() else None)
                    if isinstance(fps_text, str) and fps_text in FPS_PRESETS:
                        self.row_fps.set_selected(FPS_PRESETS.index(fps_text))
                except Exception:
                    pass

                # Size sync
                try:
                    size_text = sc.size_combo.get_active_text() or (sc.size_combo.get_child().get_text() if hasattr(sc.size_combo, "get_child") and sc.size_combo.get_child() else None)
                    _safe_set_text(self.row_size, size_text)
                except Exception:
                    pass

            if ac:
                try:
                    no_aud = ac.param_no_audio.get_active()
                    if isinstance(no_aud, bool):
                        self.row_forward_audio.set_active(not no_aud)
                except Exception:
                    pass
                _safe_set_sel(self.row_audio_source, ac.audio_source_dropdown.get_selected())
                _safe_set_sel(self.row_audio_codec, ac.audio_codec_dropdown.get_selected())
                _safe_set_sel(self.row_audio_buffer, ac.audio_buffer_dropdown.get_selected())
                _safe_set_text(self.row_audio_bitrate, ac.audio_bitrate_row.get_text())
                _safe_set_active(self.row_audio_dup, ac.param_audio_dup.get_active())
                _safe_set_active(self.row_keyboard_uhid, ac.param_keyboard_uhid.get_active())
                _safe_set_active(self.row_mouse_uhid, ac.param_mouse_uhid.get_active())
                _safe_set_active(self.row_gamepad_uhid, ac.param_gamepad_uhid.get_active())
                _safe_set_sel(self.row_mouse_bind, ac.mouse_bind_dropdown.get_selected())
                _safe_set_active(self.row_legacy_paste, ac.param_legacy_paste.get_active())
                _safe_set_active(self.row_no_clip, ac.param_no_clipboard_autosync.get_active())
                _safe_set_active(self.row_read_only, ac.param_read_only.get_active())
                _safe_set_active(self.row_show_touches, ac.param_show_touches.get_active())
                _safe_set_sel(self.row_hwdec, ac.hwdec_dropdown.get_selected())
                _safe_set_sel(self.row_render_driver, ac.render_driver_dropdown.get_selected())
                _safe_set_sel(self.row_gpu, ac.gpu_dropdown.get_selected())
                _safe_set_sel(self.row_vbuf, ac.buffer_dropdown.get_selected())
                _safe_set_active(self.row_no_downsize, ac.param_no_downsize_on_error.get_active())
                _safe_set_active(self.row_screen_off, ac.param_screen_off.get_active())
                _safe_set_active(self.row_stay_awake, ac.param_stay_awake.get_active())
                _safe_set_active(self.row_power_off_close, ac.param_power_off_on_close.get_active())
                _safe_set_active(self.row_no_power_on, ac.param_no_power_on.get_active())
                _safe_set_active(self.row_print_fps, ac.param_print_fps.get_active())
                _safe_set_text(self.row_time_limit, ac.time_limit_row.get_text())
                _safe_set_sel(self.row_timeout, ac.timeout_dropdown.get_selected())

            self._update_specs_ui()
        except Exception:
            pass
        finally:
            self._is_syncing = False

    def sync_to_window(self):
        """Pushes layout widget values into window.stream_card and window.advanced_card."""
        if self._is_syncing or not self.window:
            return
        self._is_syncing = True
        try:
            sc = getattr(self.window, "stream_card", None)
            ac = getattr(self.window, "advanced_card", None)

            if sc:
                sc.type_dropdown.set_selected(self.row_stream_type.get_selected())
                if hasattr(sc, "display_dropdown") and self.row_display.get_selected() != Gtk.INVALID_LIST_POSITION:
                    sc.display_dropdown.set_selected(self.row_display.get_selected())
                sc.codec_dropdown.set_selected(self.row_codec.get_selected())
                sc.orient_dropdown.set_selected(self.row_orient.get_selected())
                sc.bitrate_row.set_text(self.row_bitrate.get_text() or "")
                sc.param_start_app.set_text(self.entry_start_app.get_text() or "")
                sc.param_new_display.set_active(self.row_new_display.get_active())
                sc.param_flex_display.set_active(self.row_flex_display.get_active())
                sc.param_display_ime_policy.set_selected(self.row_ime_policy.get_selected())
                sc.param_no_vd_destroy_content.set_active(self.row_no_vd_destroy.get_active())
                sc.render_fit_dropdown.set_selected(self.row_render_fit.get_selected())
                sc.param_fullscreen.set_active(self.row_fullscreen.get_active())
                sc.param_borderless.set_active(self.row_borderless.get_active())
                sc.param_always_on_top.set_active(self.row_always_on_top.get_active())
                sc.param_disable_screensaver.set_active(self.row_screensaver.get_active())
                sc.param_record.set_active(self.row_record.get_active())
                sc.record_format_dropdown.set_selected(self.row_record_format.get_selected())
                if hasattr(sc, "camera_dropdown") and self.row_camera.get_selected() != Gtk.INVALID_LIST_POSITION:
                    sc.camera_dropdown.set_selected(self.row_camera.get_selected())
                sc.param_camera_torch.set_active(self.row_camera_torch.get_active())
                sc.param_camera_fps.set_selected(self.row_camera_fps.get_selected())
                sc.param_camera_high_speed.set_active(self.row_camera_high_speed.get_active())
                sc.param_camera_zoom.set_text(self.row_camera_zoom.get_text() or "")

                # Max size text
                size_val = self.row_size.get_text()
                if size_val:
                    sc.size_combo.get_child().set_text(size_val)

                # FPS text
                fps_idx = self.row_fps.get_selected()
                if 0 <= fps_idx < len(FPS_PRESETS):
                    sc.fps_combo.get_child().set_text(FPS_PRESETS[fps_idx])

            if ac:
                ac.param_no_audio.set_active(not self.row_forward_audio.get_active())
                ac.audio_source_dropdown.set_selected(self.row_audio_source.get_selected())
                ac.audio_codec_dropdown.set_selected(self.row_audio_codec.get_selected())
                ac.audio_buffer_dropdown.set_selected(self.row_audio_buffer.get_selected())
                ac.audio_bitrate_row.set_text(self.row_audio_bitrate.get_text() or "")
                ac.param_audio_dup.set_active(self.row_audio_dup.get_active())
                ac.param_keyboard_uhid.set_active(self.row_keyboard_uhid.get_active())
                ac.param_mouse_uhid.set_active(self.row_mouse_uhid.get_active())
                ac.param_gamepad_uhid.set_active(self.row_gamepad_uhid.get_active())
                ac.mouse_bind_dropdown.set_selected(self.row_mouse_bind.get_selected())
                ac.param_legacy_paste.set_active(self.row_legacy_paste.get_active())
                ac.param_no_clipboard_autosync.set_active(self.row_no_clip.get_active())
                ac.param_read_only.set_active(self.row_read_only.get_active())
                ac.param_show_touches.set_active(self.row_show_touches.get_active())
                ac.hwdec_dropdown.set_selected(self.row_hwdec.get_selected())
                ac.render_driver_dropdown.set_selected(self.row_render_driver.get_selected())
                ac.gpu_dropdown.set_selected(self.row_gpu.get_selected())
                ac.buffer_dropdown.set_selected(self.row_vbuf.get_selected())
                ac.param_no_downsize_on_error.set_active(self.row_no_downsize.get_active())
                ac.param_screen_off.set_active(self.row_screen_off.get_active())
                ac.param_stay_awake.set_active(self.row_stay_awake.get_active())
                ac.param_power_off_on_close.set_active(self.row_power_off_close.get_active())
                ac.param_no_power_on.set_active(self.row_no_power_on.get_active())
                ac.param_print_fps.set_active(self.row_print_fps.get_active())
                ac.time_limit_row.set_text(self.row_time_limit.get_text() or "")
                ac.timeout_dropdown.set_selected(self.row_timeout.get_selected())
        except Exception:
            pass
        finally:
            self._is_syncing = False

    def get_stream_options(self) -> List[str]:
        """Aggregate CLI options through window cards."""
        self.sync_to_window()
        opts = []
        if self.window:
            sc = getattr(self.window, "stream_card", None)
            ac = getattr(self.window, "advanced_card", None)
            if sc:
                opts.extend(sc.get_stream_options())
            if ac:
                opts.extend(ac.get_stream_options())
        return opts

    def get_environment_overrides(self) -> Dict[str, str]:
        """Aggregate environment variables through window cards."""
        self.sync_to_window()
        if self.window and hasattr(self.window, "advanced_card"):
            return self.window.advanced_card.get_environment_overrides()
        return {}

    def get_state(self) -> Dict[str, Any]:
        """Serialize configuration state."""
        self.sync_to_window()
        state: Dict[str, Any] = {}
        if self.window:
            sc = getattr(self.window, "stream_card", None)
            ac = getattr(self.window, "advanced_card", None)
            if sc:
                state["stream"] = sc.get_state()
            if ac:
                state["advanced"] = ac.get_state()
        return state

    def set_state(self, state: Dict[str, Any]):
        """Restore configuration state."""
        if not state:
            return
        if self.window:
            sc = getattr(self.window, "stream_card", None)
            ac = getattr(self.window, "advanced_card", None)
            if sc and "stream" in state:
                sc.set_state(state["stream"])
            if ac and "advanced" in state:
                ac.set_state(state["advanced"])
        self.sync_from_window()

    # =========================================================================
    # Remote Actions & Telemetry Helpers
    # =========================================================================

    def _get_active_serial(self) -> Optional[str]:
        return self._current_serial

    def _on_keyevent(self, keycode: int, name: str):
        dc = getattr(self.window, "details_card", None)
        if dc and hasattr(dc, "on_keyevent"):
            dc.on_keyevent(keycode, name)
        else:
            serial = self._get_active_serial()
            if serial:
                from services.remote_actions import send_keyevent
                send_keyevent(serial, keycode)

    def _on_statusbar(self, target: str):
        dc = getattr(self.window, "details_card", None)
        if dc and hasattr(dc, "on_statusbar"):
            dc.on_statusbar(target)
        else:
            serial = self._get_active_serial()
            if serial:
                from services.remote_actions import expand_statusbar
                expand_statusbar(serial, target)

    def _on_paste(self):
        dc = getattr(self.window, "details_card", None)
        if dc and hasattr(dc, "on_paste"):
            dc.on_paste()
        else:
            serial = self._get_active_serial()
            if serial:
                from services.remote_actions import inject_clipboard_text
                # Inject current clipboard text
                display = Gdk.Display.get_default() if hasattr(Gdk, "Display") else None
                if display:
                    clip = display.get_clipboard()
                    clip.read_text_async(None, lambda c, res: inject_clipboard_text(serial, c.read_text_finish(res) or ""))

    def _on_screenshot(self):
        dc = getattr(self.window, "details_card", None)
        if dc and hasattr(dc, "on_screenshot"):
            dc.on_screenshot()
        else:
            serial = self._get_active_serial()
            if serial:
                from services.remote_actions import take_device_screenshot
                take_device_screenshot(serial)

    def _on_power(self):
        dc = getattr(self.window, "details_card", None)
        if dc and hasattr(dc, "on_power"):
            dc.on_power()
        else:
            serial = self._get_active_serial()
            if serial:
                from services.remote_actions import toggle_device_screen
                toggle_device_screen(serial)

    def _on_density_adjust(self, delta: int):
        dc = getattr(self.window, "details_card", None)
        if dc and hasattr(dc, "on_density_adjust_clicked"):
            dc.on_density_adjust_clicked(delta)

    def _on_density_reset(self):
        dc = getattr(self.window, "details_card", None)
        if dc and hasattr(dc, "on_density_reset_clicked"):
            dc.on_density_reset_clicked()

    def _load_host_telemetry(self):
        try:
            from services.host_telemetry import get_host_telemetry
            telem = get_host_telemetry()
            comp = telem.get("compositor", "Wayland")
            gpu = telem.get("gpu", "Auto (Mesa / DRI)")
            self.host_row.set_title(comp)
            self.host_row.set_subtitle(f"GPU: {gpu}")
        except Exception:
            self.host_row.set_title("Wayland Native")
            self.host_row.set_subtitle("Host Graphics Accelerated")
