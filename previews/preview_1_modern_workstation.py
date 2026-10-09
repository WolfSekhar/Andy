#!/usr/bin/env python3
"""
Andy UI Preview - Option 1: The Modern Workstation
Adaptive Two-Pane Adw.NavigationSplitView (GNOME Settings / Cartridges Style)
"""
import sys
import os

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio, GLib

class ModernWorkstationWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(default_width=1000, default_height=700, title="Andy - Modern Workstation Preview", **kwargs)

        # Main SplitView
        self.split_view = Adw.NavigationSplitView(min_sidebar_width=280, max_sidebar_width=340)
        self.set_content(self.split_view)

        # ---------------------------------------------------------------------
        # 1. Sidebar Page
        # ---------------------------------------------------------------------
        sidebar_toolbar = Adw.ToolbarView()
        sidebar_header = Adw.HeaderBar(show_end_title_buttons=False)
        sidebar_header.set_title_widget(Adw.WindowTitle(title="Andy", subtitle="scrcpy Controller"))

        # Header buttons
        btn_refresh = Gtk.Button(icon_name="view-refresh-symbolic", tooltip_text="Scan Devices")
        sidebar_header.pack_end(btn_refresh)
        sidebar_toolbar.add_top_bar(sidebar_header)

        # Sidebar content
        sidebar_scroll = Gtk.ScrolledWindow()
        sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        sidebar_box.set_margin_top(12)
        sidebar_box.set_margin_bottom(12)
        sidebar_box.set_margin_start(12)
        sidebar_box.set_margin_end(12)
        sidebar_scroll.set_child(sidebar_box)
        sidebar_toolbar.set_content(sidebar_scroll)

        # Connected Device Group
        device_group = Adw.PreferencesGroup(title="Active Device")
        self.device_row = Adw.ActionRow(title="Google Pixel 8 Pro", subtitle="USB 3.0 • 88% ⚡ • 1440x3120")
        self.device_row.add_prefix(Gtk.Image.new_from_icon_name("phone-symbolic"))
        device_dropdown = Gtk.DropDown(model=Gtk.StringList.new(["Pixel 8 Pro (USB)", "Galaxy Tab S9 (Wi-Fi)"]))
        self.device_row.add_suffix(device_dropdown)
        device_group.add(self.device_row)
        sidebar_box.append(device_group)

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

        self.nav_list.connect("row-activated", self.on_category_selected)
        categories_group.add(self.nav_list)
        sidebar_box.append(categories_group)

        # Host Telemetry
        telemetry_group = Adw.PreferencesGroup(title="Host Telemetry")
        t_row = Adw.ActionRow(title="GNOME Mutter (Wayland Native)", subtitle="GPU: Intel Iris Xe • OpenGL 4.6")
        t_row.add_prefix(Gtk.Image.new_from_icon_name("computer-symbolic"))
        telemetry_group.add(t_row)
        sidebar_box.append(telemetry_group)

        self.sidebar_page = Adw.NavigationPage(child=sidebar_toolbar, title="Andy")
        self.split_view.set_sidebar(self.sidebar_page)

        # ---------------------------------------------------------------------
        # 2. Content Page & HeaderBar
        # ---------------------------------------------------------------------
        content_toolbar = Adw.ToolbarView()
        self.content_header = Adw.HeaderBar()
        self.window_title = Adw.WindowTitle(title="Display &amp; Video", subtitle="Option 1: Modern Workstation")
        self.content_header.set_title_widget(self.window_title)

        # Persistent Action Hub in Content Header
        self.btn_mk = Gtk.Button(label="Connect M/K", icon_name="input-keyboard-symbolic")
        self.btn_mk.add_css_class("pill")
        self.btn_stream = Gtk.Button(label="STREAM", icon_name="media-playback-start-symbolic")
        self.btn_stream.add_css_class("pill")
        self.btn_stream.add_css_class("suggested-action")

        self.content_header.pack_end(self.btn_stream)
        self.content_header.pack_end(self.btn_mk)
        content_toolbar.add_top_bar(self.content_header)

        # ViewStack for Content Pages
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        content_toolbar.set_content(self.stack)

        self.build_pages()

        self.content_page = Adw.NavigationPage(child=content_toolbar, title="Content")
        self.split_view.set_content(self.content_page)

        # Select second category by default (Display & Video)
        second_row = self.nav_list.get_row_at_index(1)
        self.nav_list.select_row(second_row)
        self.stack.set_visible_child_name("display")

    def on_category_selected(self, listbox, row):
        if row and hasattr(row, 'cat_id'):
            self.stack.set_visible_child_name(row.cat_id)
            self.window_title.set_title(row.get_title())
            if self.split_view.get_collapsed():
                self.split_view.set_show_content(True)

    def build_pages(self):
        # 1. Device & Remote Page
        page_dev = Adw.PreferencesPage()
        grp_spec = Adw.PreferencesGroup(title="Device Telemetry")
        r_bat = Adw.ActionRow(title="Battery Level", subtitle="88% • AC Fast Charging (18W)")
        r_bat.add_prefix(Gtk.Image.new_from_icon_name("battery-level-90-charging-symbolic"))
        grp_spec.add(r_bat)
        r_res = Adw.ActionRow(title="Display Resolution", subtitle="1440x3120 Native (20:9 Aspect Ratio)")
        r_res.add_prefix(Gtk.Image.new_from_icon_name("video-display-symbolic"))
        grp_spec.add(r_res)
        page_dev.add(grp_spec)

        grp_nav = Adw.PreferencesGroup(title="Quick Remote Control")
        r_nav = Adw.ActionRow(title="Navigation Bar")
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        btn_box.append(Gtk.Button(icon_name="go-previous-symbolic", tooltip_text="Back"))
        btn_box.append(Gtk.Button(icon_name="user-home-symbolic", tooltip_text="Home"))
        btn_box.append(Gtk.Button(icon_name="view-grid-symbolic", tooltip_text="Recents"))
        r_nav.add_suffix(btn_box)
        grp_nav.add(r_nav)

        r_tools = Adw.ActionRow(title="System Actions")
        t_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        t_box.append(Gtk.Button(icon_name="preferences-system-notifications-symbolic", tooltip_text="Notifications"))
        t_box.append(Gtk.Button(icon_name="emblem-system-symbolic", tooltip_text="Quick Settings"))
        t_box.append(Gtk.Button(icon_name="system-shutdown-symbolic", tooltip_text="Power"))
        r_tools.add_suffix(t_box)
        grp_nav.add(r_tools)
        page_dev.add(grp_nav)
        self.stack.add_named(page_dev, "device")

        # 2. Display & Video Page
        page_vid = Adw.PreferencesPage()
        grp_disp = Adw.PreferencesGroup(title="Display Source &amp; Quality")
        grp_disp.add(Adw.ComboRow(title="Active Display Target", model=Gtk.StringList.new(["Display 0 (Internal)", "Virtual Display"])))
        grp_disp.add(Adw.ComboRow(title="Dynamic Resolution Preset", model=Gtk.StringList.new(["Native 100% (1440x3120)", "High 80% (1152x2496)", "Balanced 60%", "Fast 40%"])))
        grp_disp.add(Adw.ComboRow(title="Maximum Framerate", model=Gtk.StringList.new(["60 FPS", "120 FPS (High-Refresh)", "90 FPS", "30 FPS"])))
        grp_disp.add(Adw.ComboRow(title="Video Codec", model=Gtk.StringList.new(["H.264 (Default)", "H.265 (HEVC)", "AV1"])))
        grp_disp.add(Adw.EntryRow(title="Start App (Package Name)"))
        page_vid.add(grp_disp)

        grp_vd = Adw.PreferencesGroup(title="Virtual Display &amp; Window (scrcpy 5.0)")
        exp_vd = Adw.ExpanderRow(title="Virtual Secondary Display Controls")
        exp_vd.add_row(Adw.SwitchRow(title="Virtual Display Mode", subtitle="Create new secondary virtual screen"))
        exp_vd.add_row(Adw.SwitchRow(title="Flex Display", subtitle="Allow dynamic display resizing"))
        exp_vd.add_row(Adw.ComboRow(title="Virtual Display IME Policy", model=Gtk.StringList.new(["Local (PC Keyboard)", "Fallback", "Hide"])))
        exp_vd.add_row(Adw.ComboRow(title="Render Fit", model=Gtk.StringList.new(["Default", "Letterbox", "Stretched", "Unscaled"])))
        grp_vd.add(exp_vd)
        grp_vd.add(Adw.SwitchRow(title="Fullscreen Mode"))
        grp_vd.add(Adw.SwitchRow(title="Always On Top"))
        page_vid.add(grp_vd)
        self.stack.add_named(page_vid, "display")

        # 3. Camera Studio Page
        page_cam = Adw.PreferencesPage()
        grp_cam = Adw.PreferencesGroup(title="Camera Forwarding")
        grp_cam.add(Adw.ComboRow(title="Select Camera", model=Gtk.StringList.new(["Back Camera (4K 60fps)", "Front Camera (1080p 30fps)"])))
        grp_cam.add(Adw.SwitchRow(title="Camera Torch (Flashlight)", subtitle="Turn on flashlight during stream"))
        grp_cam.add(Adw.ComboRow(title="Camera FPS", model=Gtk.StringList.new(["Default", "60 FPS", "30 FPS", "20 FPS"])))
        grp_cam.add(Adw.SwitchRow(title="High-Speed Sensor Mode", subtitle="Enable high speed camera sensor profile"))
        grp_cam.add(Adw.EntryRow(title="Camera Zoom Multiplier (e.g. 1.0, 2.5)"))
        page_cam.add(grp_cam)
        self.stack.add_named(page_cam, "camera")

        # 4. Audio Page
        page_aud = Adw.PreferencesPage()
        grp_aud = Adw.PreferencesGroup(title="Audio Forwarding &amp; Latency")
        grp_aud.add(Adw.SwitchRow(title="Forward Audio", active=True))
        grp_aud.add(Adw.ComboRow(title="Audio Source", model=Gtk.StringList.new(["output (Device Sound)", "playback (Apps)", "mic (Device Mic)", "mic-camcorder"])))
        grp_aud.add(Adw.ComboRow(title="Audio Codec", model=Gtk.StringList.new(["Opus (Recommended)", "AAC", "FLAC", "RAW PCM"])))
        grp_aud.add(Adw.ComboRow(title="Audio Buffer Latency", model=Gtk.StringList.new(["Default (50 ms)", "Ultra Low (20 ms)", "Low (40 ms)", "Safe (100 ms)"])))
        grp_aud.add(Adw.SwitchRow(title="Duplicate Audio", subtitle="Play on phone and PC simultaneously"))
        page_aud.add(grp_aud)
        self.stack.add_named(page_aud, "audio")

        # 5. Input Page
        page_inp = Adw.PreferencesPage()
        grp_inp = Adw.PreferencesGroup(title="HID Hardware Passthrough")
        grp_inp.add(Adw.SwitchRow(title="Keyboard UHID Mode", subtitle="Forward Linux keyboard as native hardware"))
        grp_inp.add(Adw.SwitchRow(title="Mouse UHID Mode", subtitle="Forward mouse with raw relative motion"))
        grp_inp.add(Adw.SwitchRow(title="Gamepad UHID Mode (scrcpy 5.0)", subtitle="Forward Xbox/DualSense controller as Android gamepad"))
        grp_inp.add(Adw.ComboRow(title="Mouse Button Bindings", model=Gtk.StringList.new(["Default", "Gaming Forward Clicks (++++)", "Android Actions (bhsn)"])))
        grp_inp.add(Adw.SwitchRow(title="Legacy Paste", subtitle="Inject keystrokes for restricted password fields"))
        page_inp.add(grp_inp)
        self.stack.add_named(page_inp, "input")

        # 6. Engine & Performance Page
        page_eng = Adw.PreferencesPage()
        grp_eng = Adw.PreferencesGroup(title="Hardware Acceleration &amp; System")
        grp_eng.add(Adw.ComboRow(title="Hardware Video Decoding", model=Gtk.StringList.new(["Default (Auto)", "vaapi (Hardware)", "disabled (Software)"])))
        grp_eng.add(Adw.SwitchRow(title="Disable Downsize on Error", subtitle="Prevent automatic resolution drop on encoder error"))
        grp_eng.add(Adw.SwitchRow(title="Turn Screen Off During Stream", subtitle="Save battery and prevent AMOLED burn-in", active=True))
        grp_eng.add(Adw.SwitchRow(title="Stay Awake While Connected", active=True))
        grp_eng.add(Adw.SwitchRow(title="Power Off Device on Close", subtitle="Lock phone when stream session ends"))
        page_eng.add(grp_eng)
        self.stack.add_named(page_eng, "engine")


class PreviewApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.wolfsekhar.andy.preview1", flags=Gio.ApplicationFlags.NON_UNIQUE)
    def do_activate(self):
        win = ModernWorkstationWindow(application=self)
        win.present()

if __name__ == "__main__":
    app = PreviewApp()
    sys.exit(app.run(sys.argv))
