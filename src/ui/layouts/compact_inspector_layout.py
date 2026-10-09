"""
Compact Floating Inspector Layout for Andy (Option 3).
Inspired by GNOME Boxes & Clapper video player OSD styling.

Features:
- Central minimal canvas with responsive device card &amp; quick preset chips
- Floating OSD capsule bar at bottom (Stream, Connect M/K, Toggle Inspector, Quick Actions)
- Collapsible Adw.OverlaySplitView right drawer containing stream engine, virtual display,
  and audio/HW acceleration preferences
- Full action wiring to AndyWindow, remote ADB actions, and scrcpy argument builder
"""

import os
import threading
from typing import List, Dict, Any, Optional, Union

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gdk

from ui.layouts.base_layout import BaseLayout
from services.device_service import get_detailed_device_info
from services.remote_actions import (
    send_keyevent,
    expand_statusbar,
    take_device_screenshot,
    toggle_device_screen,
    inject_clipboard_text,
    adjust_device_volume,
)


class CompactInspectorLayout(BaseLayout):
    """
    Option 3: Compact Floating Inspector layout.
    Presents a focused device canvas with a floating pill OSD and an expandable
    inspector drawer for granular scrcpy configurations.
    """

    def __init__(self, window: Any = None) -> None:
        super().__init__(window=window)

        self.current_serial: Optional[str] = None
        self.current_device_info: Optional[Dict[str, Any]] = None
        self.active_preset: Optional[str] = "60fps"
        self._updating_preset: bool = False
        self.stream_active: bool = False
        self.stream_mode: str = "stream"
        self.devices: List[Dict[str, Any]] = []

        # Root split view
        self.split_view = Adw.OverlaySplitView(
            sidebar_position=Gtk.PackType.END,
            min_sidebar_width=350,
            max_sidebar_width=400,
        )
        self.split_view.set_vexpand(True)
        self.split_view.set_hexpand(True)
        self.split_view.add_css_class("compact-inspector-layout")

        # ---------------------------------------------------------------------
        # 1. Content Slot: Minimal Canvas + Floating Action OSD Pill
        # ---------------------------------------------------------------------
        self.canvas_overlay = Gtk.Overlay()
        self.canvas_overlay.set_vexpand(True)
        self.canvas_overlay.set_hexpand(True)
        self.split_view.set_content(self.canvas_overlay)

        # Scrolled container for canvas box
        self.canvas_scroll = Gtk.ScrolledWindow()
        self.canvas_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.canvas_scroll.set_vexpand(True)
        self.canvas_scroll.set_hexpand(True)
        self.canvas_overlay.set_child(self.canvas_scroll)

        # Canvas vertical layout
        self.canvas_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        self.canvas_box.set_margin_top(16)
        self.canvas_box.set_margin_bottom(90)  # Generous padding to clear floating OSD
        self.canvas_box.set_margin_start(16)
        self.canvas_box.set_margin_end(16)
        self.canvas_scroll.set_child(self.canvas_box)

        # Top Quick Preset Chips
        self._setup_preset_chips()

        # Center Mockup / Interactive Device Hub
        self._setup_device_hub()

        # Floating Action OSD Pill
        self._setup_floating_osd()

        # ---------------------------------------------------------------------
        # 2. Sidebar Slot: Collapsible Inspector Drawer
        # ---------------------------------------------------------------------
        self._setup_inspector_drawer()

        # Initial drawer state (closed)
        self.set_drawer_open(False)

        # Apply initial preset parameters
        self._apply_preset_settings("60fps")

    # -------------------------------------------------------------------------
    # Base Widget Accessors
    # -------------------------------------------------------------------------
    def get_widget(self) -> Gtk.Widget:
        """Return the top-level container widget for this layout."""
        return self.split_view

    @property
    def widget(self) -> Gtk.Widget:
        """Convenience property for root widget."""
        return self.split_view

    # -------------------------------------------------------------------------
    # UI Setup Helpers
    # -------------------------------------------------------------------------
    def _setup_preset_chips(self) -> None:
        """Build top horizontal preset chips."""
        self.chips_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.chips_box.set_halign(Gtk.Align.CENTER)
        self.chips_box.set_margin_top(4)

        self.preset_buttons: Dict[str, Gtk.ToggleButton] = {}
        presets = [
            ("60fps", "🚀 60 FPS Smooth"),
            ("lowlatency", "💼 Low Latency"),
            ("gaming", "🎮 Gaming 120Hz"),
            ("webcam", "📹 4K Webcam"),
        ]

        for pid, label in presets:
            btn = Gtk.ToggleButton(label=label)
            btn.add_css_class("pill")
            btn.connect("toggled", self._on_preset_toggled, pid)
            self.chips_box.append(btn)
            self.preset_buttons[pid] = btn

        self.canvas_box.append(self.chips_box)

        # Set initial active chip
        self._set_active_preset_chip("60fps")

    def _setup_device_hub(self) -> None:
        """Build center device silhouette and status card."""
        self.mockup_clamp = Adw.Clamp(maximum_size=520)
        self.mockup_clamp.set_margin_top(8)

        self.mockup_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        self.mockup_box.add_css_class("card")
        self.mockup_clamp.set_child(self.mockup_box)
        self.canvas_box.append(self.mockup_clamp)

        # Mockup Header
        m_head = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        m_head.set_margin_top(14)
        m_head.set_margin_start(16)
        m_head.set_margin_end(16)

        img_phone = Gtk.Image.new_from_icon_name("phone-symbolic")
        img_phone.set_pixel_size(28)
        m_head.append(img_phone)

        m_title = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        m_title.set_hexpand(True)
        self.lbl_device_title = Gtk.Label(
            label="No Device Selected",
            xalign=0,
            css_classes=["title-4"],
        )
        self.lbl_device_sub = Gtk.Label(
            label="Connect an Android device via USB or Wi-Fi • Disconnected",
            xalign=0,
            css_classes=["dim-label"],
        )
        m_title.append(self.lbl_device_title)
        m_title.append(self.lbl_device_sub)
        m_head.append(m_title)

        self.lbl_battery = Gtk.Label(label="🔋 --%", css_classes=["card", "accent"])
        self.lbl_battery.set_valign(Gtk.Align.CENTER)
        m_head.append(self.lbl_battery)
        self.mockup_box.append(m_head)

        # Visual Screen Silhouette Frame
        self.frame_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.frame_box.set_halign(Gtk.Align.CENTER)
        self.frame_box.set_size_request(240, 150)
        self.frame_box.add_css_class("card")
        self.frame_box.set_margin_top(4)
        self.frame_box.set_margin_bottom(4)

        img_disp = Gtk.Image.new_from_icon_name("video-display-symbolic")
        img_disp.set_pixel_size(32)
        self.frame_box.append(img_disp)

        self.lbl_geom = Gtk.Label(
            label="Display 0 (Internal)\nNo Geometry Available\nDisconnected",
            justify=Gtk.Justification.CENTER,
        )
        self.lbl_geom.add_css_class("dim-label")
        self.frame_box.append(self.lbl_geom)
        self.mockup_box.append(self.frame_box)

        # Integrated Chin Remote Buttons
        self.remote_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.remote_row.set_halign(Gtk.Align.CENTER)
        self.remote_row.set_margin_bottom(14)

        self.btn_chin_back = Gtk.Button(icon_name="go-previous-symbolic", label="Back")
        self.btn_chin_back.connect("clicked", lambda b: self._send_keyevent(4, "Back"))
        self.remote_row.append(self.btn_chin_back)

        self.btn_chin_home = Gtk.Button(icon_name="user-home-symbolic", label="Home")
        self.btn_chin_home.connect("clicked", lambda b: self._send_keyevent(3, "Home"))
        self.remote_row.append(self.btn_chin_home)

        self.btn_chin_recents = Gtk.Button(icon_name="view-grid-symbolic", label="Recents")
        self.btn_chin_recents.connect("clicked", lambda b: self._send_keyevent(187, "Recents"))
        self.remote_row.append(self.btn_chin_recents)

        self.btn_chin_notif = Gtk.Button(
            icon_name="preferences-system-notifications-symbolic",
            tooltip_text="Notifications",
        )
        self.btn_chin_notif.connect("clicked", self.on_notifications_clicked)
        self.remote_row.append(self.btn_chin_notif)

        self.btn_chin_vol = Gtk.Button(
            icon_name="audio-volume-high-symbolic",
            tooltip_text="Volume Up",
        )
        self.btn_chin_vol.connect("clicked", self.on_volume_clicked)
        self.remote_row.append(self.btn_chin_vol)

        self.mockup_box.append(self.remote_row)

    def _setup_floating_osd(self) -> None:
        """Build Clapper-style floating action pill at bottom of canvas overlay."""
        self.osd_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.osd_box.add_css_class("osd")
        self.osd_box.add_css_class("pill")
        self.osd_box.set_halign(Gtk.Align.CENTER)
        self.osd_box.set_valign(Gtk.Align.END)
        self.osd_box.set_margin_bottom(24)

        # 1. STREAM Button
        self.btn_stream = Gtk.Button()
        self.stream_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.stream_icon = Gtk.Image.new_from_icon_name("media-playback-start-symbolic")
        self.stream_label = Gtk.Label(label="STREAM")
        self.stream_box.append(self.stream_icon)
        self.stream_box.append(self.stream_label)
        self.btn_stream.set_child(self.stream_box)
        self.btn_stream.add_css_class("pill")
        self.btn_stream.add_css_class("suggested-action")
        self.btn_stream.connect("clicked", self.on_stream_clicked)
        self.osd_box.append(self.btn_stream)

        # 2. Connect M/K Button
        self.btn_mk = Gtk.Button()
        self.mk_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.mk_icon = Gtk.Image.new_from_icon_name("input-keyboard-symbolic")
        self.mk_label = Gtk.Label(label="Connect M/K")
        self.mk_box.append(self.mk_icon)
        self.mk_box.append(self.mk_label)
        self.btn_mk.set_child(self.mk_box)
        self.btn_mk.add_css_class("pill")
        self.btn_mk.set_tooltip_text("Send Mouse and Keyboard without streaming video")
        self.btn_mk.connect("clicked", self.on_connect_mk_clicked)
        self.osd_box.append(self.btn_mk)

        # 3. Toggle Inspector Button
        self.btn_toggle_inspector = Gtk.ToggleButton()
        insp_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        insp_icon = Gtk.Image.new_from_icon_name("view-right-pane-symbolic")
        insp_label = Gtk.Label(label="Inspector")
        insp_box.append(insp_icon)
        insp_box.append(insp_label)
        self.btn_toggle_inspector.set_child(insp_box)
        self.btn_toggle_inspector.add_css_class("pill")
        self.btn_toggle_inspector.set_tooltip_text("Toggle Inspector Drawer")
        self.btn_toggle_inspector.connect("toggled", self.on_toggle_drawer)
        self.osd_box.append(self.btn_toggle_inspector)

        # Vertical Separator
        self.osd_box.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))

        # 4. Quick Action Buttons
        self.btn_screenshot = Gtk.Button(
            icon_name="camera-photo-symbolic",
            tooltip_text="Take Screenshot",
        )
        self.btn_screenshot.add_css_class("flat")
        self.btn_screenshot.connect("clicked", self.on_screenshot_clicked)
        self.osd_box.append(self.btn_screenshot)

        self.btn_screen_off = Gtk.Button(
            icon_name="weather-clear-night-symbolic",
            tooltip_text="Turn Screen Off / On",
        )
        self.btn_screen_off.add_css_class("flat")
        self.btn_screen_off.connect("clicked", self.on_screen_off_clicked)
        self.osd_box.append(self.btn_screen_off)

        self.btn_paste = Gtk.Button(
            icon_name="edit-paste-symbolic",
            tooltip_text="Paste Clipboard to Device",
        )
        self.btn_paste.add_css_class("flat")
        self.btn_paste.connect("clicked", self.on_paste_clicked)
        self.osd_box.append(self.btn_paste)

        self.canvas_overlay.add_overlay(self.osd_box)

    def _setup_inspector_drawer(self) -> None:
        """Build collapsible right drawer containing scrcpy parameters."""
        inspector_toolbar = Adw.ToolbarView()

        # HeaderBar with title and close button (Ampersand escaped as &amp;)
        inspector_head = Adw.HeaderBar(show_end_title_buttons=False)
        inspector_head.set_title_widget(
            Adw.WindowTitle(title="Inspector &amp; Parameters")
        )

        btn_close = Gtk.Button(
            icon_name="window-close-symbolic",
            tooltip_text="Close Inspector",
        )
        btn_close.connect("clicked", lambda b: self.set_drawer_open(False))
        inspector_head.pack_end(btn_close)
        inspector_toolbar.add_top_bar(inspector_head)

        # Scrollable Preferences Page
        inspector_scroll = Gtk.ScrolledWindow()
        inspector_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        page = Adw.PreferencesPage()
        inspector_scroll.set_child(page)
        inspector_toolbar.set_content(inspector_scroll)

        # Group 1: Video Stream Engine
        grp1 = Adw.PreferencesGroup(title="Video Stream Engine")
        self.row_source = Adw.ComboRow(
            title="Source",
            model=Gtk.StringList.new(["Screen", "Camera"]),
        )
        grp1.add(self.row_source)

        self.row_res = Adw.ComboRow(
            title="Resolution Limit",
            model=Gtk.StringList.new(["Native 100%", "High 80%", "Balanced 60%", "Low 40%"]),
        )
        grp1.add(self.row_res)

        self.row_fps = Adw.ComboRow(
            title="Max FPS",
            model=Gtk.StringList.new(["60 FPS", "120 FPS", "90 FPS", "30 FPS"]),
        )
        grp1.add(self.row_fps)

        self.row_codec = Adw.ComboRow(
            title="Video Codec",
            model=Gtk.StringList.new(["H.264", "H.265", "AV1"]),
        )
        grp1.add(self.row_codec)

        self.row_start_app = Adw.EntryRow(title="Start App (Package Name)")
        grp1.add(self.row_start_app)
        page.add(grp1)

        # Group 2: scrcpy 5.0 Virtual Display
        grp2 = Adw.PreferencesGroup(title="scrcpy 5.0 Virtual Display")
        self.row_vdisplay = Adw.SwitchRow(title="Virtual Display Mode")
        grp2.add(self.row_vdisplay)

        self.row_flex_display = Adw.SwitchRow(title="Flex Display (Dynamic Resize)")
        grp2.add(self.row_flex_display)

        self.row_vdisplay_ime = Adw.ComboRow(
            title="Virtual Display IME",
            model=Gtk.StringList.new(["Local", "Fallback", "Hide"]),
        )
        grp2.add(self.row_vdisplay_ime)

        self.row_render_fit = Adw.ComboRow(
            title="Render Fit",
            model=Gtk.StringList.new(["Default", "Letterbox", "Stretched"]),
        )
        grp2.add(self.row_render_fit)
        page.add(grp2)

        # Group 3: Audio &amp; HW Acceleration (Ampersand escaped as &amp;)
        grp3 = Adw.PreferencesGroup(title="Audio &amp; HW Acceleration")
        self.row_audio = Adw.SwitchRow(title="Forward Audio", active=True)
        grp3.add(self.row_audio)

        self.row_audio_codec = Adw.ComboRow(
            title="Audio Codec",
            model=Gtk.StringList.new(["Opus", "AAC", "RAW"]),
        )
        grp3.add(self.row_audio_codec)

        self.row_hwdec = Adw.ComboRow(
            title="Hardware Video Decoding",
            model=Gtk.StringList.new(["vaapi (VA-API)", "Default (Auto)", "disabled"]),
        )
        grp3.add(self.row_hwdec)

        self.row_gamepad = Adw.SwitchRow(title="Gamepad Forwarding (UHID)")
        grp3.add(self.row_gamepad)

        self.row_turn_screen_off = Adw.SwitchRow(title="Turn Screen Off")
        grp3.add(self.row_turn_screen_off)
        page.add(grp3)

        self.split_view.set_sidebar(inspector_toolbar)

    # -------------------------------------------------------------------------
    # Drawer Management
    # -------------------------------------------------------------------------
    def on_toggle_drawer(self, btn: Gtk.ToggleButton) -> None:
        """Handle toggle button state change."""
        self.set_drawer_open(btn.get_active())

    def set_drawer_open(self, open_state: bool) -> None:
        """Open or close the right inspector drawer."""
        self.split_view.set_show_sidebar(open_state)
        if self.btn_toggle_inspector.get_active() != open_state:
            self.btn_toggle_inspector.set_active(open_state)

    # -------------------------------------------------------------------------
    # Preset Chips Logic
    # -------------------------------------------------------------------------
    def _on_preset_toggled(self, button: Gtk.ToggleButton, preset_id: str) -> None:
        """Handle click on preset chip."""
        if self._updating_preset:
            return

        if button.get_active():
            self._set_active_preset_chip(preset_id)
            self._apply_preset_settings(preset_id)
        else:
            # Prevent unchecking the currently active preset without another being selected
            if self.active_preset == preset_id:
                button.set_active(True)

    def _set_active_preset_chip(self, preset_id: str) -> None:
        """Update toggle button visual states."""
        self._updating_preset = True
        self.active_preset = preset_id

        for pid, btn in self.preset_buttons.items():
            is_target = pid == preset_id
            btn.set_active(is_target)
            if is_target:
                btn.add_css_class("suggested-action")
            else:
                btn.remove_css_class("suggested-action")

        self._updating_preset = False

    def _apply_preset_settings(self, preset_id: str) -> None:
        """Apply preset parameters to inspector controls."""
        if preset_id == "60fps":
            self.row_source.set_selected(0)      # Screen
            self.row_res.set_selected(1)         # High 80%
            self.row_fps.set_selected(0)         # 60 FPS
            self.row_codec.set_selected(0)       # H.264
            self.row_audio.set_active(True)
            self.row_gamepad.set_active(False)
            self.row_turn_screen_off.set_active(False)
        elif preset_id == "lowlatency":
            self.row_source.set_selected(0)      # Screen
            self.row_res.set_selected(2)         # Balanced 60%
            self.row_fps.set_selected(0)         # 60 FPS
            self.row_codec.set_selected(0)       # H.264
            self.row_hwdec.set_selected(0)       # vaapi
            self.row_audio.set_active(False)
            self.row_gamepad.set_active(False)
        elif preset_id == "gaming":
            self.row_source.set_selected(0)      # Screen
            self.row_res.set_selected(0)         # Native 100%
            self.row_fps.set_selected(1)         # 120 FPS
            self.row_codec.set_selected(1)       # H.265
            self.row_audio.set_active(True)
            self.row_gamepad.set_active(True)
        elif preset_id == "webcam":
            self.row_source.set_selected(1)      # Camera
            self.row_res.set_selected(0)         # Native 100%
            self.row_fps.set_selected(0)         # 60 FPS
            self.row_codec.set_selected(0)       # H.264
            self.row_turn_screen_off.set_active(True)

    # -------------------------------------------------------------------------
    # Window Action Wiring
    # -------------------------------------------------------------------------
    def on_stream_clicked(self, button=None) -> None:
        """Trigger scrcpy stream session via window."""
        if self.window and hasattr(self.window, "on_play_clicked"):
            self.window.on_play_clicked(button)
        elif self.window and hasattr(self.window, "launch_scrcpy") and self.current_serial:
            if self.stream_active:
                if hasattr(self.window, "process_manager"):
                    self.window.process_manager.stop()
            else:
                opts = self.get_stream_options()
                self.window.launch_scrcpy(self.current_serial, opts, mode="stream")

    def on_connect_mk_clicked(self, button=None) -> None:
        """Trigger Mouse/Keyboard bridge mode via window."""
        if self.window and hasattr(self.window, "on_connect_mk_clicked"):
            self.window.on_connect_mk_clicked(button)
        elif self.window and hasattr(self.window, "launch_scrcpy") and self.current_serial:
            if self.stream_active:
                if hasattr(self.window, "process_manager"):
                    self.window.process_manager.stop()
            else:
                opts = ["--max-size=128", "--fullscreen", "--no-audio"] + self.get_stream_options()
                self.window.launch_scrcpy(self.current_serial, opts, mode="mk")

    def on_screenshot_clicked(self, button=None) -> None:
        """Capture screenshot of the connected device."""
        if self.window and hasattr(self.window, "details_card") and hasattr(self.window.details_card, "on_screenshot_clicked"):
            self.window.details_card.on_screenshot_clicked()
        elif self.current_serial:
            threading.Thread(target=take_device_screenshot, args=(self.current_serial,), daemon=True).start()

    def on_screen_off_clicked(self, button=None) -> None:
        """Toggle device screen power state."""
        if self.window and hasattr(self.window, "details_card") and hasattr(self.window.details_card, "on_power_clicked"):
            self.window.details_card.on_power_clicked()
        elif self.current_serial:
            threading.Thread(target=toggle_device_screen, args=(self.current_serial,), daemon=True).start()

    def on_paste_clicked(self, button=None) -> None:
        """Paste system clipboard into active device input."""
        if self.window and hasattr(self.window, "details_card") and hasattr(self.window.details_card, "on_paste_clipboard_clicked"):
            self.window.details_card.on_paste_clipboard_clicked()
        elif self.current_serial:
            display = Gdk.Display.get_default()
            if display:
                clipboard = display.get_clipboard()
                def on_read_text(cb, result):
                    try:
                        text = cb.read_text_finish(result)
                        if text:
                            threading.Thread(
                                target=inject_clipboard_text,
                                args=(self.current_serial, text),
                                daemon=True
                            ).start()
                    except Exception:
                        pass
                clipboard.read_text_async(None, on_read_text)

    def on_notifications_clicked(self, button=None) -> None:
        """Expand status shade notifications."""
        if self.window and hasattr(self.window, "details_card") and hasattr(self.window.details_card, "on_statusbar_clicked"):
            self.window.details_card.on_statusbar_clicked("notifications")
        elif self.current_serial:
            threading.Thread(
                target=expand_statusbar,
                args=(self.current_serial, "notifications"),
                daemon=True,
            ).start()

    def on_volume_clicked(self, button=None) -> None:
        """Adjust device volume upwards."""
        if self.window and hasattr(self.window, "details_card") and hasattr(self.window.details_card, "on_volume_clicked"):
            self.window.details_card.on_volume_clicked("up")
        elif self.current_serial:
            threading.Thread(
                target=adjust_device_volume,
                args=(self.current_serial, "up"),
                daemon=True,
            ).start()

    def _send_keyevent(self, keycode: int, name: str) -> None:
        """Send virtual navigation keyevent to active device."""
        if self.window and hasattr(self.window, "details_card") and hasattr(self.window.details_card, "on_keyevent_clicked"):
            self.window.details_card.on_keyevent_clicked(keycode, name)
        elif self.current_serial:
            threading.Thread(
                target=send_keyevent,
                args=(self.current_serial, keycode),
                daemon=True,
            ).start()

    # -------------------------------------------------------------------------
    # BaseLayout Protocol Implementations
    # -------------------------------------------------------------------------
    def update_devices(self, devices: List[Dict[str, Any]]) -> None:
        """Receive list of currently enumerated ADB devices."""
        self.devices = devices or []
        if not self.devices:
            self.on_device_selected(None)
        elif not self.current_serial:
            self.on_device_selected(self.devices[0])

    def on_device_selected(self, device_data: Optional[Any] = None) -> None:
        """Update layout with newly selected device."""
        if isinstance(device_data, dict):
            serial = device_data.get("serial")
            display_name = device_data.get("display_name")
        else:
            serial = device_data
            display_name = None

        self.current_serial = serial
        if not serial or serial == "No devices found":
            self.lbl_device_title.set_text("No Device Connected")
            self.lbl_device_sub.set_text("Connect an Android device via USB or Wi-Fi • Disconnected")
            self.lbl_battery.set_text("🔋 --%")
            self.lbl_geom.set_text("Display 0 (Internal)\nNo Geometry Available\nDisconnected")
            self.set_controls_sensitive(False)
            return

        self.set_controls_sensitive(True)
        self.lbl_device_title.set_text(display_name or "Android Device")
        self.lbl_device_sub.set_text(f"Serial: {serial} • Fetching hardware specs...")
        self.lbl_battery.set_text("🔋 ...")

        def fetch(target_serial):
            info = get_detailed_device_info(target_serial)
            if self.current_serial == target_serial:
                GLib.idle_add(self._apply_device_info, info)

        threading.Thread(target=fetch, args=(serial,), daemon=True).start()

    def _apply_device_info(self, info: Dict[str, Any]) -> bool:
        """Render device hardware info returned from async probe."""
        model = info.get("model", "Android Device")
        version = info.get("version", "Android")
        res = info.get("resolution", "Native")
        conn = info.get("connection", "USB")
        battery = info.get("battery", "--")
        aspect = info.get("aspect_ratio", "")
        density = info.get("density", "")

        self.lbl_device_title.set_text(model)
        self.lbl_device_sub.set_text(f"Connected via {conn} • {res} Native • {version}")
        self.lbl_battery.set_text(f"🔋 {battery} ⚡" if battery != "N/A" else "🔋 --%")

        geom_lines = ["Display 0 (Internal)"]
        if res != "N/A":
            geom_lines.append(f"{res} ({aspect})" if aspect else res)
        if density != "N/A":
            geom_lines.append(f"Density: {density}")
        self.lbl_geom.set_text("\n".join(geom_lines))
        return False

    def set_controls_sensitive(self, sensitive: bool) -> None:
        """Enable or disable interactive widgets depending on connection."""
        self.btn_stream.set_sensitive(sensitive)
        self.btn_mk.set_sensitive(sensitive)
        self.btn_screenshot.set_sensitive(sensitive)
        self.btn_screen_off.set_sensitive(sensitive)
        self.btn_paste.set_sensitive(sensitive)
        self.btn_chin_back.set_sensitive(sensitive)
        self.btn_chin_home.set_sensitive(sensitive)
        self.btn_chin_recents.set_sensitive(sensitive)
        self.btn_chin_notif.set_sensitive(sensitive)
        self.btn_chin_vol.set_sensitive(sensitive)

    def set_stream_state(self, active: bool, mode: str = "stream") -> None:
        """Reflect scrcpy running status in the floating OSD pill."""
        self.stream_active = active
        self.stream_mode = mode

        if active:
            if mode == "stream":
                self.stream_label.set_text("STOP")
                self.stream_icon.set_from_icon_name("media-playback-stop-symbolic")
                self.btn_stream.remove_css_class("suggested-action")
                self.btn_stream.add_css_class("destructive-action")
                self.btn_mk.set_sensitive(False)
            else:
                self.mk_label.set_text("DISCONNECT")
                self.mk_icon.set_from_icon_name("media-playback-stop-symbolic")
                self.btn_mk.add_css_class("destructive-action")
                self.btn_stream.set_sensitive(False)
        else:
            self.stream_label.set_text("STREAM")
            self.stream_icon.set_from_icon_name("media-playback-start-symbolic")
            self.btn_stream.remove_css_class("destructive-action")
            self.btn_stream.add_css_class("suggested-action")
            self.btn_stream.set_sensitive(self.current_serial is not None)

            self.mk_label.set_text("Connect M/K")
            self.mk_icon.set_from_icon_name("input-keyboard-symbolic")
            self.btn_mk.remove_css_class("destructive-action")
            self.btn_mk.set_sensitive(self.current_serial is not None)

    def sync_from_window(self) -> None:
        """Synchronize active state and device from parent AndyWindow."""
        if not self.window:
            return

        if hasattr(self.window, "devices") and self.window.devices:
            idx = 0
            if hasattr(self.window, "device_dropdown"):
                idx = self.window.device_dropdown.get_selected()
            if 0 <= idx < len(self.window.devices):
                self.on_device_selected(self.window.devices[idx])

        if hasattr(self.window, "process_manager"):
            is_running = self.window.process_manager.is_running
            mode = getattr(self.window.process_manager, "current_mode", "stream")
            self.set_stream_state(is_running, mode=mode)

    def get_stream_options(self) -> List[str]:
        """Aggregate scrcpy CLI flags configured in the Inspector drawer."""
        options: List[str] = []

        # 1. Source (Screen vs Camera)
        if self.row_source.get_selected() == 1:
            options.append("--video-source=camera")

        # 2. Resolution Limit
        res_idx = self.row_res.get_selected()
        if res_idx == 1:
            options.append("--max-size=1920")
        elif res_idx == 2:
            options.append("--max-size=1280")
        elif res_idx == 3:
            options.append("--max-size=960")

        # 3. Max FPS
        fps_presets = ["60", "120", "90", "30"]
        fps_idx = self.row_fps.get_selected()
        if 0 <= fps_idx < len(fps_presets):
            options.append(f"--max-fps={fps_presets[fps_idx]}")

        # 4. Video Codec
        codec_presets = ["h264", "h265", "av1"]
        codec_idx = self.row_codec.get_selected()
        if 0 <= codec_idx < len(codec_presets):
            options.append(f"--video-codec={codec_presets[codec_idx]}")

        # 5. Start App
        app = self.row_start_app.get_text().strip()
        if app:
            options.append(f"--start-app={app}")

        # 6. Virtual Display
        if self.row_vdisplay.get_active():
            options.append("--new-display")

        if self.row_flex_display.get_active():
            options.append("--display-buffer=0")

        # Virtual Display IME
        ime_opts = ["local", "fallback", "hide"]
        ime_idx = self.row_vdisplay_ime.get_selected()
        if 0 <= ime_idx < len(ime_opts) and ime_opts[ime_idx] != "local":
            options.append(f"--display-ime={ime_opts[ime_idx]}")

        # Render Fit
        fit_opts = ["default", "letterbox", "stretched"]
        fit_idx = self.row_render_fit.get_selected()
        if 0 <= fit_idx < len(fit_opts) and fit_opts[fit_idx] != "default":
            options.append(f"--render-fit={fit_opts[fit_idx]}")

        # 7. Audio &amp; Forwarding
        if not self.row_audio.get_active():
            options.append("--no-audio")
        else:
            audio_codecs = ["opus", "aac", "raw"]
            a_idx = self.row_audio_codec.get_selected()
            if 0 <= a_idx < len(audio_codecs):
                options.append(f"--audio-codec={audio_codecs[a_idx]}")

        # 8. HW Video Decoding
        hw_idx = self.row_hwdec.get_selected()
        if hw_idx == 0:
            options.append("--video-codec-options=hwdec=vaapi")
        elif hw_idx == 2:
            options.append("--no-video-playback")

        # 9. Gamepad Forwarding
        if self.row_gamepad.get_active():
            options.append("--gamepad=uhid")

        # 10. Turn Screen Off
        if self.row_turn_screen_off.get_active():
            options.append("--turn-screen-off")

        return options

    def get_environment_overrides(self) -> Dict[str, str]:
        """Aggregate environment variables from layout."""
        overrides: Dict[str, str] = {}
        if self.row_hwdec.get_selected() == 0:
            overrides["LIBVA_DRIVER_NAME"] = "radeonsi"
        return overrides

    def get_state(self) -> Dict[str, Any]:
        """Serialize layout state for saving profile."""
        return {
            "source": self.row_source.get_selected(),
            "resolution": self.row_res.get_selected(),
            "fps": self.row_fps.get_selected(),
            "codec": self.row_codec.get_selected(),
            "start_app": self.row_start_app.get_text(),
            "virtual_display": self.row_vdisplay.get_active(),
            "flex_display": self.row_flex_display.get_active(),
            "vdisplay_ime": self.row_vdisplay_ime.get_selected(),
            "render_fit": self.row_render_fit.get_selected(),
            "audio": self.row_audio.get_active(),
            "audio_codec": self.row_audio_codec.get_selected(),
            "hwdec": self.row_hwdec.get_selected(),
            "gamepad": self.row_gamepad.get_active(),
            "turn_screen_off": self.row_turn_screen_off.get_active(),
            "active_preset": self.active_preset,
        }

    def set_state(self, state: Dict[str, Any]) -> None:
        """Restore layout state from profile."""
        if not state:
            return

        if "source" in state:
            self.row_source.set_selected(state["source"])
        if "resolution" in state:
            self.row_res.set_selected(state["resolution"])
        if "fps" in state:
            self.row_fps.set_selected(state["fps"])
        if "codec" in state:
            self.row_codec.set_selected(state["codec"])
        if "start_app" in state:
            self.row_start_app.set_text(state["start_app"])
        if "virtual_display" in state:
            self.row_vdisplay.set_active(state["virtual_display"])
        if "flex_display" in state:
            self.row_flex_display.set_active(state["flex_display"])
        if "vdisplay_ime" in state:
            self.row_vdisplay_ime.set_selected(state["vdisplay_ime"])
        if "render_fit" in state:
            self.row_render_fit.set_selected(state["render_fit"])
        if "audio" in state:
            self.row_audio.set_active(state["audio"])
        if "audio_codec" in state:
            self.row_audio_codec.set_selected(state["audio_codec"])
        if "hwdec" in state:
            self.row_hwdec.set_selected(state["hwdec"])
        if "gamepad" in state:
            self.row_gamepad.set_active(state["gamepad"])
        if "turn_screen_off" in state:
            self.row_turn_screen_off.set_active(state["turn_screen_off"])
        if "active_preset" in state and state["active_preset"]:
            self._set_active_preset_chip(state["active_preset"])
