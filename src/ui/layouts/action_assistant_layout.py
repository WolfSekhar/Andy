#!/usr/bin/env python3
"""
Andy UI Layout - Option 5: The Action-Driven Assistant
Workflow &amp; Goal-Oriented Task Cards with Inline Fine-Tuning (Pika Backup / Upscaler Style).
"""
import threading
from typing import Any, Dict, List, Optional

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib

from ui.layouts.base_layout import BaseLayout
from services.device_service import (
    get_detailed_device_info,
    get_device_cameras,
    get_device_resolution,
)
from services.remote_actions import (
    send_keyevent,
    set_device_density,
    reset_device_density,
    reboot_device,
)


class ActionAssistantLayout(BaseLayout):
    """
    Action-Driven Assistant Layout (Option 5).
    Features 5 Goal-Oriented Workflow Cards:
    1. Desktop Mirroring
    2. Productivity &amp; 2nd Display
    3. HD Webcam &amp; Studio Mic
    4. Mobile Gaming Station
    5. Rescue &amp; Recovery Hub
    Each card includes a 1-click CTA button and an inline fine-tuning expander.
    """

    def __init__(self, window: Any = None):
        super().__init__(window=window)

        self.current_serial: Optional[str] = None
        self.active_workflow: Optional[str] = None
        self.is_streaming: bool = False
        self.camera_list: List[Dict[str, str]] = []

        # Top-level container
        self.main_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.main_container.set_vexpand(True)
        self.main_container.set_hexpand(True)
        self.main_container.add_css_class("action-assistant-layout")

        self._build_ui()
        self.sync_from_window()

    def get_widget(self) -> Gtk.Widget:
        """Return the top-level container widget for this layout."""
        return self.main_container

    def _build_ui(self):
        # Scrolled window container
        self.scroll = Gtk.ScrolledWindow()
        self.scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scroll.set_hexpand(True)
        self.scroll.set_vexpand(True)

        clamp = Adw.Clamp(maximum_size=880)
        clamp.set_hexpand(True)
        self.scroll.set_child(clamp)

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.main_box.set_margin_top(16)
        self.main_box.set_margin_bottom(24)
        self.main_box.set_margin_start(16)
        self.main_box.set_margin_end(16)
        clamp.set_child(self.main_box)

        # 1. Connected Device Banner
        self._build_device_banner()

        # 2. Section Header
        lbl_section = Gtk.Label(
            label="CHOOSE A WORKFLOW GOAL:",
            xalign=0,
            css_classes=["title-4", "dim-label"]
        )
        lbl_section.set_margin_top(4)
        self.main_box.append(lbl_section)

        # 3. The 5 Goal-Oriented Workflow Cards
        self._build_mirroring_card()
        self._build_productivity_card()
        self._build_webcam_card()
        self._build_gaming_card()
        self._build_rescue_card()

        self.main_container.append(self.scroll)

    # -------------------------------------------------------------------------
    # Device Banner
    # -------------------------------------------------------------------------
    def _build_device_banner(self):
        self.banner_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.banner_box.add_css_class("card")
        self.banner_box.set_margin_bottom(4)

        b_icon = Gtk.Image.new_from_icon_name("phone-symbolic")
        b_icon.set_margin_start(16)
        b_icon.set_pixel_size(24)
        self.banner_box.append(b_icon)

        b_text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        b_text.set_hexpand(True)
        b_text.set_margin_top(12)
        b_text.set_margin_bottom(12)

        self.lbl_device_title = Gtk.Label(
            label="⚪ No Device Connected",
            xalign=0,
            css_classes=["title-4"]
        )
        self.lbl_device_subtitle = Gtk.Label(
            label="Connect an Android device via USB &amp; ADB to begin.",
            xalign=0,
            css_classes=["dim-label"]
        )
        b_text.append(self.lbl_device_title)
        b_text.append(self.lbl_device_subtitle)
        self.banner_box.append(b_text)

        self.btn_refresh_banner = Gtk.Button(
            icon_name="view-refresh-symbolic",
            tooltip_text="Scan Devices"
        )
        self.btn_refresh_banner.set_margin_end(16)
        self.btn_refresh_banner.set_valign(Gtk.Align.CENTER)
        self.btn_refresh_banner.connect("clicked", self._on_refresh_clicked)
        self.banner_box.append(self.btn_refresh_banner)

        self.main_box.append(self.banner_box)

    # -------------------------------------------------------------------------
    # Card 1: Desktop Mirroring
    # -------------------------------------------------------------------------
    def _build_mirroring_card(self):
        self.mirror_res_combo = Adw.ComboRow(
            title="Resolution Scale",
            model=Gtk.StringList.new(["100% Native", "80% Balanced", "60% Fast", "40% Performance"])
        )
        self.mirror_fps_combo = Adw.ComboRow(
            title="Max FPS Cap",
            model=Gtk.StringList.new(["60 FPS", "30 FPS", "120 FPS", "No Limit"])
        )
        self.mirror_screen_off = Adw.SwitchRow(
            title="Turn Device Screen Off",
            active=True
        )
        self.mirror_touches = Adw.SwitchRow(
            title="Show Touch Ripples",
            active=False
        )
        self.mirror_stay_awake = Adw.SwitchRow(
            title="Stay Awake",
            active=True
        )

        self.btn_mirror = Gtk.Button(label="Mirror Screen 🚀")
        self.btn_mirror.add_css_class("pill")
        self.btn_mirror.add_css_class("suggested-action")
        self.btn_mirror.set_valign(Gtk.Align.CENTER)
        self.btn_mirror.connect("clicked", self._on_mirror_clicked)

        card = self._create_workflow_card(
            title="Desktop Mirroring",
            subtitle="Standard screen projection with automatic resolution, 60 FPS, and lossless audio pass-through.",
            icon_name="video-display-symbolic",
            badges=["Auto Res", "60 FPS", "Low Latency"],
            action_button=self.btn_mirror,
            fine_tune_rows=[
                self.mirror_res_combo,
                self.mirror_fps_combo,
                self.mirror_screen_off,
                self.mirror_touches,
                self.mirror_stay_awake,
            ]
        )
        self.main_box.append(card)

    # -------------------------------------------------------------------------
    # Card 2: Productivity &amp; 2nd Display
    # -------------------------------------------------------------------------
    def _build_productivity_card(self):
        self.prod_geom_entry = Adw.EntryRow(
            title="Virtual Display Geometry (e.g. 1920x1080/400)"
        )
        self.prod_flex_switch = Adw.SwitchRow(
            title="Flex Display (Dynamic Window Resizing)",
            active=True
        )
        self.prod_ime_combo = Adw.ComboRow(
            title="Virtual Display IME",
            model=Gtk.StringList.new(["Local (PC Keyboard)", "Fallback", "Hide"])
        )
        self.prod_keep_content_switch = Adw.SwitchRow(
            title="Keep Content on Exit",
            subtitle="Preserve background apps when closing window",
            active=True
        )
        self.prod_app_entry = Adw.EntryRow(
            title="Direct App Launch (e.g. com.android.chrome)"
        )
        self.prod_keyboard_switch = Adw.SwitchRow(
            title="Keyboard Forwarding (UHID)",
            active=True
        )
        self.prod_mouse_switch = Adw.SwitchRow(
            title="Mouse Forwarding (UHID)",
            active=True
        )

        self.btn_productivity = Gtk.Button(label="Launch Workspace 🚀")
        self.btn_productivity.add_css_class("pill")
        self.btn_productivity.add_css_class("suggested-action")
        self.btn_productivity.set_valign(Gtk.Align.CENTER)
        self.btn_productivity.connect("clicked", self._on_productivity_clicked)

        card = self._create_workflow_card(
            title="Productivity &amp; 2nd Display",
            subtitle="Create an independent virtual secondary display with physical mouse and keyboard pass-through.",
            icon_name="display-projector-symbolic",
            badges=["Virtual Display", "UHID Pass", "Borderless"],
            action_button=self.btn_productivity,
            fine_tune_rows=[
                self.prod_geom_entry,
                self.prod_flex_switch,
                self.prod_ime_combo,
                self.prod_keep_content_switch,
                self.prod_app_entry,
                self.prod_keyboard_switch,
                self.prod_mouse_switch,
            ]
        )
        self.main_box.append(card)

    # -------------------------------------------------------------------------
    # Card 3: HD Webcam &amp; Studio Mic
    # -------------------------------------------------------------------------
    def _build_webcam_card(self):
        self.webcam_optics_model = Gtk.StringList.new([
            "Back Camera 0 (4K 60fps)",
            "Front Camera 1 (1080p)"
        ])
        self.webcam_optics_combo = Adw.ComboRow(
            title="Camera Optics",
            model=self.webcam_optics_model
        )
        self.webcam_torch_switch = Adw.SwitchRow(
            title="Camera Torch (Ring Light)",
            subtitle="Activate LED flash during stream",
            active=False
        )
        self.webcam_zoom_entry = Adw.EntryRow(
            title="Camera Zoom Factor (e.g. 1.0, 2.5)"
        )
        self.webcam_audio_combo = Adw.ComboRow(
            title="Audio Profile",
            model=Gtk.StringList.new([
                "mic-camcorder (Directional)",
                "mic (Standard)",
                "mic-unprocessed (Raw)"
            ])
        )
        self.webcam_high_speed_switch = Adw.SwitchRow(
            title="Camera High Speed Capture",
            active=False
        )
        self.webcam_fps_combo = Adw.ComboRow(
            title="Target FPS",
            model=Gtk.StringList.new(["60 FPS", "30 FPS"])
        )

        self.btn_webcam = Gtk.Button(label="Start Webcam 📹")
        self.btn_webcam.add_css_class("pill")
        self.btn_webcam.add_css_class("suggested-action")
        self.btn_webcam.set_valign(Gtk.Align.CENTER)
        self.btn_webcam.connect("clicked", self._on_webcam_clicked)

        card = self._create_workflow_card(
            title="HD Webcam &amp; Studio Mic",
            subtitle="Stream camera sensors directly to PC as an ultra-high definition webcam with studio microphone.",
            icon_name="camera-web-symbolic",
            badges=["1080p60", "Studio Mic", "High Speed"],
            action_button=self.btn_webcam,
            fine_tune_rows=[
                self.webcam_optics_combo,
                self.webcam_torch_switch,
                self.webcam_zoom_entry,
                self.webcam_audio_combo,
                self.webcam_high_speed_switch,
                self.webcam_fps_combo,
            ]
        )
        self.main_box.append(card)

    # -------------------------------------------------------------------------
    # Card 4: Mobile Gaming Station
    # -------------------------------------------------------------------------
    def _build_gaming_card(self):
        self.gaming_fps_combo = Adw.ComboRow(
            title="Refresh Rate Target",
            model=Gtk.StringList.new(["120 FPS (High-Refresh)", "90 FPS", "60 FPS"])
        )
        self.gaming_gamepad_switch = Adw.SwitchRow(
            title="Gamepad Forwarding (UHID)",
            active=True
        )
        self.gaming_mouse_combo = Adw.ComboRow(
            title="Mouse Button Scheme",
            model=Gtk.StringList.new(["Gaming Forward Clicks (++++)", "Android Actions (bhsn)"])
        )
        self.gaming_hwdec_combo = Adw.ComboRow(
            title="Hardware Video Decoding",
            model=Gtk.StringList.new(["vaapi (Hardware)", "Default"])
        )
        self.gaming_audio_dup_switch = Adw.SwitchRow(
            title="Audio Duplication",
            subtitle="Hear audio on phone headphones &amp; PC",
            active=False
        )
        self.gaming_buffer_combo = Adw.ComboRow(
            title="Video Buffer (Latency)",
            model=Gtk.StringList.new(["0ms (Ultra Low)", "50ms", "100ms"])
        )

        self.btn_gaming = Gtk.Button(label="Play Game 🎮")
        self.btn_gaming.add_css_class("pill")
        self.btn_gaming.add_css_class("suggested-action")
        self.btn_gaming.set_valign(Gtk.Align.CENTER)
        self.btn_gaming.connect("clicked", self._on_gaming_clicked)

        card = self._create_workflow_card(
            title="Mobile Gaming Station",
            subtitle="High-framerate 120Hz stream with hardware gamepad emulation, VA-API decode, and 0ms buffer.",
            icon_name="input-gaming-symbolic",
            badges=["120 FPS", "Gamepad UHID", "VA-API 0ms"],
            action_button=self.btn_gaming,
            fine_tune_rows=[
                self.gaming_fps_combo,
                self.gaming_gamepad_switch,
                self.gaming_mouse_combo,
                self.gaming_hwdec_combo,
                self.gaming_audio_dup_switch,
                self.gaming_buffer_combo,
            ]
        )
        self.main_box.append(card)

    # -------------------------------------------------------------------------
    # Card 5: Rescue &amp; Recovery Hub
    # -------------------------------------------------------------------------
    def _build_rescue_card(self):
        self.rescue_otg_switch = Adw.SwitchRow(
            title="Headless OTG Mode",
            subtitle="Forward keyboard &amp; mouse without starting video stream",
            active=False
        )
        self.rescue_screen_off_switch = Adw.SwitchRow(
            title="Force Turn Screen Off (AMOLED Protect)",
            subtitle="Prevent screen burn-in on cracked glass",
            active=True
        )
        self.rescue_stay_awake_switch = Adw.SwitchRow(
            title="Keep Awake while Connected",
            active=True
        )

        # Interactive Unlock Row
        self.rescue_unlock_row = Adw.ActionRow(
            title="Screen Unlock Bypass",
            subtitle="Inject Keyevent 82 (Menu / Wake)"
        )
        btn_unlock = Gtk.Button(label="Wake &amp; Unlock")
        btn_unlock.add_css_class("pill")
        btn_unlock.set_valign(Gtk.Align.CENTER)
        btn_unlock.connect("clicked", self._on_unlock_clicked)
        self.rescue_unlock_row.add_suffix(btn_unlock)

        # Interactive Density Row
        self.rescue_density_row = Adw.ActionRow(
            title="Display Density Modifier (DPI)",
            subtitle="Live ADB override for oversized or broken layouts"
        )
        density_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        density_box.set_valign(Gtk.Align.CENTER)

        btn_dpi_320 = Gtk.Button(label="320")
        btn_dpi_320.add_css_class("flat")
        btn_dpi_320.connect("clicked", lambda b: self._on_set_density(320))
        density_box.append(btn_dpi_320)

        btn_dpi_400 = Gtk.Button(label="400")
        btn_dpi_400.add_css_class("flat")
        btn_dpi_400.connect("clicked", lambda b: self._on_set_density(400))
        density_box.append(btn_dpi_400)

        btn_dpi_480 = Gtk.Button(label="480")
        btn_dpi_480.add_css_class("flat")
        btn_dpi_480.connect("clicked", lambda b: self._on_set_density(480))
        density_box.append(btn_dpi_480)

        btn_dpi_reset = Gtk.Button(label="Reset")
        btn_dpi_reset.add_css_class("pill")
        btn_dpi_reset.connect("clicked", lambda b: self._on_reset_density())
        density_box.append(btn_dpi_reset)

        self.rescue_density_row.add_suffix(density_box)

        # Interactive Reboot Row
        self.rescue_reboot_row = Adw.ActionRow(
            title="Remote Reboot Trigger",
            subtitle="Normal Reboot / Recovery / Bootloader"
        )
        reboot_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        reboot_box.set_valign(Gtk.Align.CENTER)

        btn_reboot_normal = Gtk.Button(label="Reboot")
        btn_reboot_normal.add_css_class("flat")
        btn_reboot_normal.connect("clicked", lambda b: self._on_reboot("normal"))
        reboot_box.append(btn_reboot_normal)

        btn_reboot_rec = Gtk.Button(label="Recovery")
        btn_reboot_rec.add_css_class("flat")
        btn_reboot_rec.connect("clicked", lambda b: self._on_reboot("recovery"))
        reboot_box.append(btn_reboot_rec)

        btn_reboot_boot = Gtk.Button(label="Bootloader")
        btn_reboot_boot.add_css_class("flat")
        btn_reboot_boot.connect("clicked", lambda b: self._on_reboot("bootloader"))
        reboot_box.append(btn_reboot_boot)

        self.rescue_reboot_row.add_suffix(reboot_box)

        self.btn_rescue = Gtk.Button(label="Enter Rescue Hub 🛠️")
        self.btn_rescue.add_css_class("pill")
        self.btn_rescue.add_css_class("destructive-action")
        self.btn_rescue.set_valign(Gtk.Align.CENTER)
        self.btn_rescue.connect("clicked", self._on_rescue_clicked)

        card = self._create_workflow_card(
            title="Rescue &amp; Recovery Hub",
            subtitle="Broken AMOLED recovery, headless OTG mouse/keyboard fallback, live DPI adjustment, and fast reboot.",
            icon_name="system-run-symbolic",
            badges=["Broken AMOLED", "OTG Headless", "Density Slider"],
            action_button=self.btn_rescue,
            fine_tune_rows=[
                self.rescue_otg_switch,
                self.rescue_screen_off_switch,
                self.rescue_stay_awake_switch,
                self.rescue_unlock_row,
                self.rescue_density_row,
                self.rescue_reboot_row,
            ]
        )
        self.main_box.append(card)

    # -------------------------------------------------------------------------
    # Card Builder Helper
    # -------------------------------------------------------------------------
    def _create_workflow_card(
        self,
        title: str,
        subtitle: str,
        icon_name: str,
        badges: List[str],
        action_button: Gtk.Button,
        fine_tune_rows: List[Gtk.Widget],
    ) -> Gtk.Box:
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        card.add_css_class("card")
        card.set_margin_bottom(6)

        # Header with icon and action button
        head = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        head.set_margin_top(14)
        head.set_margin_start(16)
        head.set_margin_end(16)

        icon = Gtk.Image.new_from_icon_name(icon_name)
        icon.set_pixel_size(32)
        head.append(icon)

        t_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        t_box.set_hexpand(True)
        # Ensure ampersands are safely escaped for Pango markup
        safe_title = title.replace("&", "&amp;").replace("&amp;amp;", "&amp;")
        safe_subtitle = subtitle.replace("&", "&amp;").replace("&amp;amp;", "&amp;")

        lbl_t = Gtk.Label(label=safe_title, xalign=0, css_classes=["title-4"])
        lbl_s = Gtk.Label(label=safe_subtitle, xalign=0, wrap=True, css_classes=["dim-label"])
        t_box.append(lbl_t)
        t_box.append(lbl_s)
        head.append(t_box)

        head.append(action_button)
        card.append(head)

        # Badges Row
        badge_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        badge_box.set_margin_start(58)
        badge_box.set_margin_end(16)
        for b in badges:
            safe_b = b.replace("&", "&amp;").replace("&amp;amp;", "&amp;")
            lbl = Gtk.Label(label=safe_b)
            lbl.add_css_class("card")
            lbl.set_margin_top(2)
            lbl.set_margin_bottom(2)
            lbl.set_margin_start(6)
            lbl.set_margin_end(6)
            badge_box.append(lbl)
        card.append(badge_box)

        # Inline Fine-Tuning Expander
        expander = Adw.ExpanderRow(title="Advanced Fine-Tuning")
        expander.set_margin_start(16)
        expander.set_margin_end(16)
        expander.set_margin_bottom(12)
        for r in fine_tune_rows:
            expander.add_row(r)

        # Wrap in preferences group for Adw styling
        grp = Adw.PreferencesGroup()
        grp.add(expander)
        card.append(grp)

        return card

    # -------------------------------------------------------------------------
    # Window Synchronization &amp; Lifecycle
    # -------------------------------------------------------------------------
    def sync_from_window(self) -> None:
        """Synchronize this layout's UI controls with the parent window state."""
        if self.window is None:
            return

        if hasattr(self.window, "devices"):
            self.update_devices(self.window.devices)

        if hasattr(self.window, "device_dropdown"):
            idx = self.window.device_dropdown.get_selected()
            if hasattr(self.window, "devices") and 0 <= idx < len(self.window.devices):
                self.on_device_selected(self.window.devices[idx])

        if hasattr(self.window, "process_manager"):
            is_running = getattr(self.window.process_manager, "is_running", False)
            self.set_stream_state(is_running)

    def get_active_serial(self) -> Optional[str]:
        """Resolves the currently active device serial."""
        if self.current_serial:
            return self.current_serial

        if self.window is not None:
            if hasattr(self.window, "device_dropdown") and hasattr(self.window, "devices"):
                idx = self.window.device_dropdown.get_selected()
                if 0 <= idx < len(self.window.devices):
                    return self.window.devices[idx].get("serial")
        return None

    def update_devices(self, devices: List[Dict[str, Any]]):
        """Called when connected devices list updates."""
        if not devices:
            self.current_serial = None
            self.lbl_device_title.set_label("⚪ No Device Connected")
            self.lbl_device_subtitle.set_label("Connect an Android device via USB &amp; ADB to begin.")
            return

        if self.current_serial is None or not any(d.get("serial") == self.current_serial for d in devices):
            first_serial = devices[0].get("serial")
            self.on_device_selected(first_serial)

    def on_device_selected(self, device_info_or_serial: Any):
        """Called when active device selection changes."""
        if isinstance(device_info_or_serial, dict):
            serial = device_info_or_serial.get("serial")
        else:
            serial = device_info_or_serial

        self.current_serial = serial
        if not serial or serial == "No devices found":
            self.lbl_device_title.set_label("⚪ No Device Connected")
            self.lbl_device_subtitle.set_label("Connect an Android device via USB &amp; ADB to begin.")
            return

        self.lbl_device_title.set_label(f"🔄 Reading Device: {serial}...")

        def fetch_details():
            info = get_detailed_device_info(serial)
            cams = get_device_cameras(serial)
            GLib.idle_add(self._apply_device_details, info, cams)

        threading.Thread(target=fetch_details, daemon=True).start()

    def _apply_device_details(self, info: Dict[str, Any], cameras: List[Dict[str, str]]):
        model = info.get("model", "Android Device")
        version = info.get("version", "N/A")
        conn = info.get("connection", "USB")
        res = info.get("resolution", "N/A")
        batt = info.get("battery", "N/A")

        self.lbl_device_title.set_label(f"🟢 Connected: {model}")
        self.lbl_device_subtitle.set_label(
            f"Android {version} • {conn} • {res} • Battery: {batt} ⚡"
        )

        self.camera_list = cameras
        if cameras:
            n_items = self.webcam_optics_model.get_n_items()
            self.webcam_optics_model.splice(0, n_items, [c["desc"] for c in cameras])

        return False

    def _on_refresh_clicked(self, button):
        if self.window is not None and hasattr(self.window, "refresh_devices"):
            self.window.refresh_devices()

    # -------------------------------------------------------------------------
    # Stream State Lifecycle
    # -------------------------------------------------------------------------
    def on_stream_state_changed(self, active: bool, mode: str = "stream") -> None:
        """Lifecycle hook invoked when streaming begins or stops."""
        self.set_stream_state(active, mode=mode)

    def set_stream_state(self, active: bool, mode: str = "stream"):
        """Updates UI CTA buttons according to scrcpy running state."""
        self.is_streaming = active

        all_buttons = [
            (self.btn_mirror, "Mirror Screen 🚀", "suggested-action"),
            (self.btn_productivity, "Launch Workspace 🚀", "suggested-action"),
            (self.btn_webcam, "Start Webcam 📹", "suggested-action"),
            (self.btn_gaming, "Play Game 🎮", "suggested-action"),
            (self.btn_rescue, "Enter Rescue Hub 🛠️", "destructive-action"),
        ]

        if active:
            # Running state: active workflow gets Stop button; others disabled
            workflow_map = {
                "mirror": self.btn_mirror,
                "productivity": self.btn_productivity,
                "webcam": self.btn_webcam,
                "gaming": self.btn_gaming,
                "rescue": self.btn_rescue,
            }
            active_btn = workflow_map.get(self.active_workflow, self.btn_mirror)

            for btn, _, orig_cls in all_buttons:
                if btn == active_btn:
                    btn.set_label("Stop Session ⏹️")
                    btn.remove_css_class(orig_cls)
                    btn.add_css_class("destructive-action")
                    btn.set_sensitive(True)
                else:
                    btn.set_sensitive(False)
        else:
            # Idle state: restore all buttons
            self.active_workflow = None
            for btn, label, orig_cls in all_buttons:
                btn.set_label(label)
                btn.remove_css_class("destructive-action")
                btn.remove_css_class("suggested-action")
                btn.add_css_class(orig_cls)
                btn.set_sensitive(True)

    # -------------------------------------------------------------------------
    # Execution Dispatcher
    # -------------------------------------------------------------------------
    def _execute_workflow(self, workflow_name: str, options: List[str], mode: str = "stream"):
        if self.is_streaming:
            if self.window is not None and hasattr(self.window, "process_manager"):
                self.window.process_manager.stop()
            return

        serial = self.get_active_serial()
        if not serial or serial == "No devices found":
            if self.window is not None and hasattr(self.window, "show_error_dialog"):
                self.window.show_error_dialog(
                    "No Device Connected",
                    "Please connect and select an Android device via USB/ADB before starting."
                )
            return

        self.active_workflow = workflow_name
        if self.window is not None and hasattr(self.window, "launch_scrcpy"):
            self.window.launch_scrcpy(serial, options, mode=mode)
        else:
            self.set_stream_state(True, mode=mode)

    # -------------------------------------------------------------------------
    # Workflow Launch Handlers
    # -------------------------------------------------------------------------
    def _on_mirror_clicked(self, button):
        options: List[str] = []

        res_idx = self.mirror_res_combo.get_selected()
        if res_idx == 1:
            options.append("--max-size=1920")
        elif res_idx == 2:
            options.append("--max-size=1440")
        elif res_idx == 3:
            options.append("--max-size=1080")

        fps_idx = self.mirror_fps_combo.get_selected()
        if fps_idx == 0:
            options.append("--max-fps=60")
        elif fps_idx == 1:
            options.append("--max-fps=30")
        elif fps_idx == 2:
            options.append("--max-fps=120")

        if self.mirror_screen_off.get_active():
            options.append("--turn-screen-off")
        if self.mirror_touches.get_active():
            options.append("--show-touches")
        if self.mirror_stay_awake.get_active():
            options.append("--stay-awake")

        self._execute_workflow("mirror", options, mode="stream")

    def _on_productivity_clicked(self, button):
        options: List[str] = []

        geom = self.prod_geom_entry.get_text().strip()
        if geom:
            options.append(f"--new-display={geom}")
        else:
            options.append("--new-display")

        if self.prod_flex_switch.get_active():
            options.append("--flex-display")

        ime_idx = self.prod_ime_combo.get_selected()
        if ime_idx == 0:
            options.append("--display-ime-policy=local")
        elif ime_idx == 1:
            options.append("--display-ime-policy=fallback")
        elif ime_idx == 2:
            options.append("--display-ime-policy=hide")

        if self.prod_keep_content_switch.get_active():
            options.append("--no-vd-destroy-content")

        app = self.prod_app_entry.get_text().strip()
        if app:
            options.append(f"--start-app={app}")

        if self.prod_keyboard_switch.get_active():
            options.append("--keyboard=uhid")
        if self.prod_mouse_switch.get_active():
            options.append("--mouse=uhid")

        self._execute_workflow("productivity", options, mode="stream")

    def _on_webcam_clicked(self, button):
        options: List[str] = ["--video-source=camera"]

        cam_idx = self.webcam_optics_combo.get_selected()
        if self.camera_list and 0 <= cam_idx < len(self.camera_list):
            cam_id = self.camera_list[cam_idx].get("id", str(cam_idx))
            options.append(f"--camera-id={cam_id}")
        else:
            options.append(f"--camera-id={cam_idx}")

        if self.webcam_torch_switch.get_active():
            options.append("--camera-torch")

        zoom = self.webcam_zoom_entry.get_text().strip()
        if zoom:
            options.append(f"--camera-zoom={zoom}")

        audio_idx = self.webcam_audio_combo.get_selected()
        if audio_idx == 0:
            options.append("--audio-source=mic-camcorder")
        elif audio_idx == 1:
            options.append("--audio-source=mic")
        elif audio_idx == 2:
            options.append("--audio-source=mic-unprocessed")

        if self.webcam_high_speed_switch.get_active():
            options.append("--camera-high-speed")

        fps_idx = self.webcam_fps_combo.get_selected()
        if fps_idx == 0:
            options.append("--camera-fps=60")
        elif fps_idx == 1:
            options.append("--camera-fps=30")

        options.append("--max-size=1920")

        self._execute_workflow("webcam", options, mode="stream")

    def _on_gaming_clicked(self, button):
        options: List[str] = []

        fps_idx = self.gaming_fps_combo.get_selected()
        if fps_idx == 0:
            options.append("--max-fps=120")
        elif fps_idx == 1:
            options.append("--max-fps=90")
        elif fps_idx == 2:
            options.append("--max-fps=60")

        if self.gaming_gamepad_switch.get_active():
            options.append("--gamepad=uhid")

        mouse_idx = self.gaming_mouse_combo.get_selected()
        if mouse_idx == 0:
            options.append("--mouse-bind=++++:++++")
        elif mouse_idx == 1:
            options.append("--mouse-bind=bhsn:++++")

        hwdec_idx = self.gaming_hwdec_combo.get_selected()
        if hwdec_idx == 0:
            options.append("--hwdec=vaapi")

        if self.gaming_audio_dup_switch.get_active():
            options.append("--audio-dup")

        buf_idx = self.gaming_buffer_combo.get_selected()
        if buf_idx == 0:
            options.append("--video-buffer=0")
        elif buf_idx == 1:
            options.append("--video-buffer=50")
        elif buf_idx == 2:
            options.append("--video-buffer=100")

        options.extend(["--keyboard=uhid", "--mouse=uhid"])

        self._execute_workflow("gaming", options, mode="stream")

    def _on_rescue_clicked(self, button):
        is_headless = self.rescue_otg_switch.get_active()
        if is_headless:
            mode = "mk"
            options = ["--max-size=128", "--fullscreen", "--no-audio", "--keyboard=uhid", "--mouse=uhid"]
        else:
            mode = "stream"
            options = ["--max-size=1080", "--no-audio", "--keyboard=uhid", "--mouse=uhid"]

        if self.rescue_screen_off_switch.get_active():
            options.append("--turn-screen-off")
        if self.rescue_stay_awake_switch.get_active():
            options.append("--stay-awake")

        self._execute_workflow("rescue", options, mode=mode)

    # -------------------------------------------------------------------------
    # Rescue Hub ADB Quick Actions
    # -------------------------------------------------------------------------
    def _on_unlock_clicked(self, button):
        serial = self.get_active_serial()
        if not serial:
            return

        def run_unlock():
            send_keyevent(serial, 82)  # Menu / Wake unlock
            send_keyevent(serial, 26)  # Power wake
            send_keyevent(serial, 82)

        threading.Thread(target=run_unlock, daemon=True).start()

    def _on_set_density(self, density: int):
        serial = self.get_active_serial()
        if not serial:
            return
        threading.Thread(target=lambda: set_device_density(serial, density), daemon=True).start()

    def _on_reset_density(self):
        serial = self.get_active_serial()
        if not serial:
            return
        threading.Thread(target=lambda: reset_device_density(serial), daemon=True).start()

    def _on_reboot(self, mode: str):
        serial = self.get_active_serial()
        if not serial:
            return
        threading.Thread(target=lambda: reboot_device(serial, mode), daemon=True).start()

    # -------------------------------------------------------------------------
    # Profile State Serialization
    # -------------------------------------------------------------------------
    def get_state(self) -> Dict[str, Any]:
        """Serializes current layout options into a profile dictionary."""
        return {
            "mirror_res": self.mirror_res_combo.get_selected(),
            "mirror_fps": self.mirror_fps_combo.get_selected(),
            "mirror_screen_off": self.mirror_screen_off.get_active(),
            "mirror_touches": self.mirror_touches.get_active(),
            "mirror_stay_awake": self.mirror_stay_awake.get_active(),
            "prod_geom": self.prod_geom_entry.get_text(),
            "prod_flex": self.prod_flex_switch.get_active(),
            "prod_ime": self.prod_ime_combo.get_selected(),
            "prod_keep_content": self.prod_keep_content_switch.get_active(),
            "prod_app": self.prod_app_entry.get_text(),
            "prod_keyboard": self.prod_keyboard_switch.get_active(),
            "prod_mouse": self.prod_mouse_switch.get_active(),
            "webcam_torch": self.webcam_torch_switch.get_active(),
            "webcam_zoom": self.webcam_zoom_entry.get_text(),
            "webcam_audio": self.webcam_audio_combo.get_selected(),
            "webcam_high_speed": self.webcam_high_speed_switch.get_active(),
            "webcam_fps": self.webcam_fps_combo.get_selected(),
            "gaming_fps": self.gaming_fps_combo.get_selected(),
            "gaming_gamepad": self.gaming_gamepad_switch.get_active(),
            "gaming_mouse": self.gaming_mouse_combo.get_selected(),
            "gaming_hwdec": self.gaming_hwdec_combo.get_selected(),
            "gaming_audio_dup": self.gaming_audio_dup_switch.get_active(),
            "gaming_buffer": self.gaming_buffer_combo.get_selected(),
            "rescue_otg": self.rescue_otg_switch.get_active(),
            "rescue_screen_off": self.rescue_screen_off_switch.get_active(),
            "rescue_stay_awake": self.rescue_stay_awake_switch.get_active(),
        }

    def set_state(self, state: Dict[str, Any]):
        """Restores layout options from a profile dictionary."""
        if not isinstance(state, dict):
            return

        if "mirror_res" in state:
            self.mirror_res_combo.set_selected(state["mirror_res"])
        if "mirror_fps" in state:
            self.mirror_fps_combo.set_selected(state["mirror_fps"])
        if "mirror_screen_off" in state:
            self.mirror_screen_off.set_active(bool(state["mirror_screen_off"]))
        if "mirror_touches" in state:
            self.mirror_touches.set_active(bool(state["mirror_touches"]))
        if "mirror_stay_awake" in state:
            self.mirror_stay_awake.set_active(bool(state["mirror_stay_awake"]))

        if "prod_geom" in state:
            self.prod_geom_entry.set_text(str(state["prod_geom"]))
        if "prod_flex" in state:
            self.prod_flex_switch.set_active(bool(state["prod_flex"]))
        if "prod_ime" in state:
            self.prod_ime_combo.set_selected(state["prod_ime"])
        if "prod_keep_content" in state:
            self.prod_keep_content_switch.set_active(bool(state["prod_keep_content"]))
        if "prod_app" in state:
            self.prod_app_entry.set_text(str(state["prod_app"]))
        if "prod_keyboard" in state:
            self.prod_keyboard_switch.set_active(bool(state["prod_keyboard"]))
        if "prod_mouse" in state:
            self.prod_mouse_switch.set_active(bool(state["prod_mouse"]))

        if "webcam_torch" in state:
            self.webcam_torch_switch.set_active(bool(state["webcam_torch"]))
        if "webcam_zoom" in state:
            self.webcam_zoom_entry.set_text(str(state["webcam_zoom"]))
        if "webcam_audio" in state:
            self.webcam_audio_combo.set_selected(state["webcam_audio"])
        if "webcam_high_speed" in state:
            self.webcam_high_speed_switch.set_active(bool(state["webcam_high_speed"]))
        if "webcam_fps" in state:
            self.webcam_fps_combo.set_selected(state["webcam_fps"])

        if "gaming_fps" in state:
            self.gaming_fps_combo.set_selected(state["gaming_fps"])
        if "gaming_gamepad" in state:
            self.gaming_gamepad_switch.set_active(bool(state["gaming_gamepad"]))
        if "gaming_mouse" in state:
            self.gaming_mouse_combo.set_selected(state["gaming_mouse"])
        if "gaming_hwdec" in state:
            self.gaming_hwdec_combo.set_selected(state["gaming_hwdec"])
        if "gaming_audio_dup" in state:
            self.gaming_audio_dup_switch.set_active(bool(state["gaming_audio_dup"]))
        if "gaming_buffer" in state:
            self.gaming_buffer_combo.set_selected(state["gaming_buffer"])

        if "rescue_otg" in state:
            self.rescue_otg_switch.set_active(bool(state["rescue_otg"]))
        if "rescue_screen_off" in state:
            self.rescue_screen_off_switch.set_active(bool(state["rescue_screen_off"]))
        if "rescue_stay_awake" in state:
            self.rescue_stay_awake_switch.set_active(bool(state["rescue_stay_awake"]))


if __name__ == "__main__":
    import sys
    app = Adw.Application(application_id="com.wolfsekhar.andy.action_assistant")

    def on_activate(app):
        win = Adw.ApplicationWindow(application=app, title="Andy - Action-Driven Assistant", default_width=920, default_height=740)
        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        toolbar.add_top_bar(header)
        layout = ActionAssistantLayout(window=win)
        toolbar.set_content(layout.get_widget())
        win.set_content(toolbar)
        win.present()

    app.connect("activate", on_activate)
    sys.exit(app.run(sys.argv))
