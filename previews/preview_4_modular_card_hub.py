#!/usr/bin/env python3
"""
Andy UI Preview - Option 4: The Modular Card Hub
Refined 3-Pod Libadwaita Cards + Interactive Profile Chips Bar (Fragments / Pods Style)
"""
import sys
import os

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio, GLib

class ModularCardHubWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(default_width=1080, default_height=740, title="Andy - Modular Card Hub Preview", **kwargs)

        self.toolbar_view = Adw.ToolbarView()
        self.set_content(self.toolbar_view)

        # ---------------------------------------------------------------------
        # 1. HeaderBar
        # ---------------------------------------------------------------------
        self.header_bar = Adw.HeaderBar()
        self.header_bar.set_title_widget(Adw.WindowTitle(title="Andy", subtitle="Option 4: Modular Card Hub"))

        dev_dropdown = Gtk.DropDown(model=Gtk.StringList.new(["Pixel 8 Pro (USB 3.0)", "Galaxy Tab S9 (Wi-Fi)"]))
        self.header_bar.pack_start(dev_dropdown)

        btn_mk = Gtk.Button(label="Connect M/K", icon_name="input-keyboard-symbolic")
        btn_mk.add_css_class("pill")
        btn_stream = Gtk.Button(label="STREAM", icon_name="media-playback-start-symbolic")
        btn_stream.add_css_class("pill")
        btn_stream.add_css_class("suggested-action")
        self.header_bar.pack_end(btn_stream)
        self.header_bar.pack_end(btn_mk)

        self.toolbar_view.add_top_bar(self.header_bar)

        # ---------------------------------------------------------------------
        # 2. Main Scroll & Content Box
        # ---------------------------------------------------------------------
        scroll = Gtk.ScrolledWindow()
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        main_box.set_margin_top(14)
        main_box.set_margin_bottom(20)
        main_box.set_margin_start(16)
        main_box.set_margin_end(16)
        scroll.set_child(main_box)
        self.toolbar_view.set_content(scroll)

        # ---------------------------------------------------------------------
        # 3. TOP INTERACTIVE PROFILE CHIPS BAR (Fragments / Pods Style)
        # ---------------------------------------------------------------------
        chips_scroll = Gtk.ScrolledWindow(vscrollbar_policy=Gtk.PolicyType.NEVER, hscrollbar_policy=Gtk.PolicyType.AUTOMATIC)
        chips_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        chips_box.set_margin_bottom(6)
        chips_scroll.set_child(chips_box)

        profiles = [
            ("★ Default", True),
            ("💼 Office Work", False),
            ("🎮 Gaming 120Hz", False),
            ("📷 Camera Webcam", False),
            ("📱 Broken Screen", False),
            ("⚙ Custom 1", False),
        ]
        self.chip_buttons = []
        for name, active in profiles:
            btn = Gtk.ToggleButton(label=name)
            btn.add_css_class("pill")
            if active:
                btn.set_active(True)
                btn.add_css_class("suggested-action")
            btn.connect("toggled", self.on_chip_toggled)
            chips_box.append(btn)
            self.chip_buttons.append(btn)

        btn_save = Gtk.Button(label="+ Save Current", icon_name="document-save-symbolic")
        btn_save.add_css_class("pill")
        chips_box.append(btn_save)

        main_box.append(chips_scroll)

        # ---------------------------------------------------------------------
        # 4. REFINED 3-POD CARD GRID (Gtk.FlowBox)
        # ---------------------------------------------------------------------
        flow = Gtk.FlowBox()
        flow.set_selection_mode(Gtk.SelectionMode.NONE)
        flow.set_homogeneous(False)
        flow.set_column_spacing(18)
        flow.set_row_spacing(18)
        flow.set_min_children_per_line(1)
        flow.set_max_children_per_line(3)
        flow.set_valign(Gtk.Align.START)
        flow.set_halign(Gtk.Align.FILL)
        main_box.append(flow)

        # --- POD 1: Stream & Display ---
        pod1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        pod1.add_css_class("card")
        pod1.set_size_request(310, -1)
        pod1.set_margin_top(4)

        head1 = Adw.ActionRow(title="Stream &amp; Display", subtitle="Video engine &amp; output geometry")
        head1.add_prefix(Gtk.Image.new_from_icon_name("video-display-symbolic"))
        pod1.append(head1)

        # Segmented Source Switcher
        src_row = Adw.ActionRow(title="Capture Source")
        src_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        src_box.add_css_class("linked")
        btn_src_s = Gtk.ToggleButton(label="Screen", active=True)
        btn_src_c = Gtk.ToggleButton(label="Camera")
        src_box.append(btn_src_s)
        src_box.append(btn_src_c)
        src_row.add_suffix(src_box)
        pod1.append(src_row)

        pod1.append(Adw.ComboRow(title="Active Display", model=Gtk.StringList.new(["Display 0 (Internal)", "Virtual Secondary"])))
        pod1.append(Adw.ComboRow(title="Render Fit", model=Gtk.StringList.new(["Default", "Letterbox", "Stretched", "Unscaled"])))
        pod1.append(Adw.ComboRow(title="Resolution Scale", model=Gtk.StringList.new(["Native (1440x3120)", "1920 (80%)", "1280 (60%)"])))
        pod1.append(Adw.ComboRow(title="Max Framerate", model=Gtk.StringList.new(["60 FPS", "120 FPS", "90 FPS", "30 FPS"])))
        pod1.append(Adw.ComboRow(title="Video Codec", model=Gtk.StringList.new(["H.265 (HEVC)", "H.264", "AV1"])))

        # Expander for scrcpy 5.0 Virtual Display
        exp_vd = Adw.ExpanderRow(title="Virtual Display &amp; Flex (scrcpy 5.0)")
        exp_vd.add_row(Adw.SwitchRow(title="Virtual Display Mode"))
        exp_vd.add_row(Adw.SwitchRow(title="Flex Display (Dynamic Resize)"))
        exp_vd.add_row(Adw.ComboRow(title="IME Policy", model=Gtk.StringList.new(["Local", "Fallback", "Hide"])))
        pod1.append(exp_vd)

        exp_win = Adw.ExpanderRow(title="Window &amp; Record")
        exp_win.add_row(Adw.SwitchRow(title="Fullscreen"))
        exp_win.add_row(Adw.SwitchRow(title="Always On Top"))
        exp_win.add_row(Adw.SwitchRow(title="Record MP4"))
        pod1.append(exp_win)

        flow.append(pod1)

        # --- POD 2: Engine & Peripherals ---
        pod2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        pod2.add_css_class("card")
        pod2.set_size_request(310, -1)
        pod2.set_margin_top(4)

        head2 = Adw.ActionRow(title="Engine &amp; Peripherals", subtitle="HWDEC, Audio &amp; HID passthrough")
        head2.add_prefix(Gtk.Image.new_from_icon_name("applications-utilities-symbolic"))
        pod2.append(head2)

        pod2.append(Adw.ComboRow(title="Hardware Video Decoding", model=Gtk.StringList.new(["vaapi (VA-API)", "Default (Auto)", "disabled"])))

        # Audio Expander
        exp_aud = Adw.ExpanderRow(title="Audio Forwarding Engine")
        exp_aud.add_row(Adw.SwitchRow(title="Forward Audio", active=True))
        exp_aud.add_row(Adw.ComboRow(title="Audio Codec", model=Gtk.StringList.new(["Opus (Recommended)", "AAC", "RAW"])))
        exp_aud.add_row(Adw.ComboRow(title="Audio Buffer Latency", model=Gtk.StringList.new(["20 ms (Ultra Low)", "50 ms (Normal)"])))
        exp_aud.add_row(Adw.SwitchRow(title="Duplicate Audio (Phone+PC)"))
        pod2.append(exp_aud)

        # Input & UHID Expander
        exp_hid = Adw.ExpanderRow(title="Input &amp; Peripherals (UHID)")
        exp_hid.add_row(Adw.SwitchRow(title="Keyboard UHID Mode"))
        exp_hid.add_row(Adw.SwitchRow(title="Mouse UHID Mode"))
        exp_hid.add_row(Adw.SwitchRow(title="Gamepad Forwarding (UHID)"))
        exp_hid.add_row(Adw.ComboRow(title="Mouse Button Scheme", model=Gtk.StringList.new(["Default", "Gaming (++++)", "Android (bhsn)"])))
        pod2.append(exp_hid)

        # Lifecycle Expander
        exp_life = Adw.ExpanderRow(title="Device Lifecycle &amp; Power")
        exp_life.add_row(Adw.SwitchRow(title="Turn Screen Off During Stream", active=True))
        exp_life.add_row(Adw.SwitchRow(title="Stay Awake", active=True))
        exp_life.add_row(Adw.SwitchRow(title="Power Off on Close"))
        pod2.append(exp_life)

        flow.append(pod2)

        # --- POD 3: Device Control & Telemetry ---
        pod3 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        pod3.add_css_class("card")
        pod3.set_size_request(310, -1)
        pod3.set_margin_top(4)

        head3 = Adw.ActionRow(title="Device &amp; Telemetry", subtitle="Pixel 8 Pro • Android 16")
        head3.add_prefix(Gtk.Image.new_from_icon_name("phone-symbolic"))
        pod3.append(head3)

        # Battery Gauge with LevelBar
        bat_row = Adw.ActionRow(title="Battery Status", subtitle="88% Charging (USB 3.0)")
        level = Gtk.LevelBar(min_value=0, max_value=100, value=88)
        level.set_size_request(80, 8)
        bat_row.add_suffix(level)
        pod3.append(bat_row)

        # Density Station
        dpi_row = Adw.ActionRow(title="Display Density (480 DPI)")
        dpi_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        dpi_box.append(Gtk.Button(label="-20"))
        dpi_box.append(Gtk.Button(label="Reset"))
        dpi_box.append(Gtk.Button(label="+20"))
        dpi_row.add_suffix(dpi_box)
        pod3.append(dpi_row)

        # Remote Navigation Pad
        nav_row = Adw.ActionRow(title="Remote Navigation")
        n_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        n_box.append(Gtk.Button(icon_name="go-previous-symbolic", tooltip_text="Back"))
        n_box.append(Gtk.Button(icon_name="user-home-symbolic", tooltip_text="Home"))
        n_box.append(Gtk.Button(icon_name="view-grid-symbolic", tooltip_text="Recents"))
        n_box.append(Gtk.Button(icon_name="preferences-system-notifications-symbolic", tooltip_text="Notifications"))
        nav_row.add_suffix(n_box)
        pod3.append(nav_row)

        # Remote Tool Actions
        tool_row = Adw.ActionRow(title="Remote Tools")
        t_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        t_box.append(Gtk.Button(icon_name="edit-paste-symbolic", tooltip_text="Paste Clipboard"))
        t_box.append(Gtk.Button(icon_name="camera-photo-symbolic", tooltip_text="Screenshot"))
        t_box.append(Gtk.Button(icon_name="system-shutdown-symbolic", tooltip_text="Power Button"))
        t_box.append(Gtk.Button(icon_name="system-reboot-symbolic", tooltip_text="Reboot Menu"))
        tool_row.add_suffix(t_box)
        pod3.append(tool_row)

        flow.append(pod3)

    def on_chip_toggled(self, active_btn):
        if active_btn.get_active():
            for btn in self.chip_buttons:
                if btn != active_btn:
                    btn.set_active(False)
                    btn.remove_css_class("suggested-action")
            active_btn.add_css_class("suggested-action")

class PreviewApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.wolfsekhar.andy.preview4", flags=Gio.ApplicationFlags.NON_UNIQUE)
    def do_activate(self):
        win = ModularCardHubWindow(application=self)
        win.present()

if __name__ == "__main__":
    app = PreviewApp()
    sys.exit(app.run(sys.argv))
