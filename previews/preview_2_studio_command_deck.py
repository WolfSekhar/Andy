#!/usr/bin/env python3
"""
Andy UI Preview - Option 2: The Studio Command Deck
Top ViewSwitcher + Persistent Hero Live Device Deck (Bottles / Amberol Style)
"""
import sys
import os

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio, GLib

class StudioCommandDeckWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(default_width=920, default_height=720, title="Andy - Studio Command Deck Preview", **kwargs)

        # Main ToolbarView
        self.toolbar_view = Adw.ToolbarView()
        self.set_content(self.toolbar_view)

        # ---------------------------------------------------------------------
        # 1. HeaderBar with Adw.ViewSwitcherTitle
        # ---------------------------------------------------------------------
        self.header_bar = Adw.HeaderBar()
        self.view_stack = Adw.ViewStack()

        self.switcher_title = Adw.ViewSwitcherTitle(stack=self.view_stack, title="Andy")
        self.header_bar.set_title_widget(self.switcher_title)

        # Device selector dropdown in header
        device_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        dev_dropdown = Gtk.DropDown(model=Gtk.StringList.new(["Pixel 8 Pro (USB)", "Galaxy Tab S9 (Wi-Fi)"]))
        btn_refresh = Gtk.Button(icon_name="view-refresh-symbolic", tooltip_text="Scan Devices")
        device_box.append(dev_dropdown)
        device_box.append(btn_refresh)
        self.header_bar.pack_start(device_box)

        # Profile menu
        btn_profile = Gtk.MenuButton(icon_name="document-save-symbolic", tooltip_text="Profiles")
        self.header_bar.pack_end(btn_profile)
        self.toolbar_view.add_top_bar(self.header_bar)

        # ---------------------------------------------------------------------
        # 2. Main Content: Hero Card + ViewStack
        # ---------------------------------------------------------------------
        main_scroll = Gtk.ScrolledWindow()
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        main_box.set_margin_top(16)
        main_box.set_margin_bottom(24)
        main_box.set_margin_start(16)
        main_box.set_margin_end(16)
        main_scroll.set_child(main_box)
        self.toolbar_view.set_content(main_scroll)

        # Clamp container
        clamp = Adw.Clamp(maximum_size=880)
        clamp_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        clamp.set_child(clamp_box)
        main_box.append(clamp)

        # ---------------------------------------------------------------------
        # 3. HERO LIVE DEVICE CARD (Bottles Style)
        # ---------------------------------------------------------------------
        hero_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        hero_card.add_css_class("card")
        hero_card.set_margin_top(4)
        hero_card.set_margin_bottom(4)

        # Top row: Device Info + Badges
        top_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        top_row.set_margin_top(16)
        top_row.set_margin_start(16)
        top_row.set_margin_end(16)

        avatar = Gtk.Image.new_from_icon_name("phone-symbolic")
        avatar.set_pixel_size(36)
        top_row.append(avatar)

        name_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        name_box.set_hexpand(True)
        lbl_name = Gtk.Label(label="Google Pixel 8 Pro", xalign=0)
        lbl_name.add_css_class("title-3")
        lbl_sub = Gtk.Label(label="Serial: 00045345J000073 • Android 16 (API 36)", xalign=0)
        lbl_sub.add_css_class("dim-label")
        name_box.append(lbl_name)
        name_box.append(lbl_sub)
        top_row.append(name_box)

        # Badges
        badge_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        lbl_usb = Gtk.Label(label="USB 3.0")
        lbl_usb.add_css_class("accent")
        lbl_usb.add_css_class("card")
        lbl_usb.set_margin_top(2)
        lbl_usb.set_margin_bottom(2)
        lbl_usb.set_margin_start(8)
        lbl_usb.set_margin_end(8)
        
        lbl_bat = Gtk.Label(label="🔋 88% ⚡")
        lbl_bat.add_css_class("card")
        lbl_bat.set_margin_top(2)
        lbl_bat.set_margin_bottom(2)
        lbl_bat.set_margin_start(8)
        lbl_bat.set_margin_end(8)

        badge_box.append(lbl_usb)
        badge_box.append(lbl_bat)
        top_row.append(badge_box)
        hero_card.append(top_row)

        # Metrics strip
        metrics_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=18)
        metrics_box.set_margin_start(16)
        metrics_box.set_margin_end(16)
        metrics_box.append(Gtk.Label(label="📺 1440x3120 Native (20:9)", css_classes=["dim-label"]))
        metrics_box.append(Gtk.Label(label="🖥 GNOME Mutter (Wayland Native)", css_classes=["dim-label"]))
        metrics_box.append(Gtk.Label(label="⚡ 480 DPI", css_classes=["dim-label"]))
        hero_card.append(metrics_box)

        # Divider
        hero_card.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        # Bottom row: Action Buttons + Satellite Tools
        actions_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        actions_row.set_margin_start(16)
        actions_row.set_margin_end(16)
        actions_row.set_margin_bottom(16)

        btn_stream = Gtk.Button(label="Start Stream", icon_name="media-playback-start-symbolic")
        btn_stream.add_css_class("suggested-action")
        btn_stream.add_css_class("pill")
        btn_stream.set_size_request(160, 42)
        actions_row.append(btn_stream)

        btn_mk = Gtk.Button(label="Connect M/K", icon_name="input-keyboard-symbolic")
        btn_mk.add_css_class("pill")
        btn_mk.set_size_request(140, 42)
        actions_row.append(btn_mk)

        sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        sep.set_margin_start(6)
        sep.set_margin_end(6)
        actions_row.append(sep)

        # Satellite quick tools
        sat_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        sat_box.set_hexpand(True)
        sat_box.set_halign(Gtk.Align.END)
        sat_box.append(Gtk.Button(icon_name="weather-clear-night-symbolic", tooltip_text="Screen Off"))
        sat_box.append(Gtk.Button(icon_name="system-shutdown-symbolic", tooltip_text="Power"))
        sat_box.append(Gtk.Button(icon_name="camera-photo-symbolic", tooltip_text="Screenshot"))
        sat_box.append(Gtk.Button(icon_name="media-record-symbolic", tooltip_text="Quick Record"))
        sat_box.append(Gtk.Button(icon_name="edit-paste-symbolic", tooltip_text="Paste Clipboard"))
        actions_row.append(sat_box)

        hero_card.append(actions_row)
        clamp_box.append(hero_card)

        # ---------------------------------------------------------------------
        # 4. ViewStack Tabs
        # ---------------------------------------------------------------------
        clamp_box.append(self.view_stack)
        self.build_tabs()

        # Mobile Bottom Bar Breakpoint
        self.bottom_bar = Adw.ViewSwitcherBar(stack=self.view_stack)
        self.toolbar_view.add_bottom_bar(self.bottom_bar)

    def build_tabs(self):
        # Tab 1: Overview & Remote
        page_rem = Adw.PreferencesPage()
        grp_nav = Adw.PreferencesGroup(title="Android Remote Navigation")
        r_nav = Adw.ActionRow(title="Hardware Navigation Keys")
        n_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        n_box.append(Gtk.Button(icon_name="go-previous-symbolic", label="Back"))
        n_box.append(Gtk.Button(icon_name="user-home-symbolic", label="Home"))
        n_box.append(Gtk.Button(icon_name="view-grid-symbolic", label="Recents"))
        r_nav.add_suffix(n_box)
        grp_nav.add(r_nav)

        r_quick = Adw.ActionRow(title="System Shade &amp; Tools")
        q_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        q_box.append(Gtk.Button(icon_name="preferences-system-notifications-symbolic", label="Notifications"))
        q_box.append(Gtk.Button(icon_name="emblem-system-symbolic", label="Quick Settings"))
        r_quick.add_suffix(q_box)
        grp_nav.add(r_quick)
        page_rem.add(grp_nav)

        grp_hw = Adw.PreferencesGroup(title="Hardware Adjustments")
        r_vol = Adw.ActionRow(title="Media Volume")
        v_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        v_box.append(Gtk.Button(icon_name="audio-volume-low-symbolic", label="Down"))
        v_box.append(Gtk.Button(icon_name="audio-volume-high-symbolic", label="Up"))
        r_vol.add_suffix(v_box)
        grp_hw.add(r_vol)

        r_dpi = Adw.ActionRow(title="Display Density (DPI)", subtitle="Live ADB Density Override")
        d_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        d_box.append(Gtk.Button(label="-20"))
        d_box.append(Gtk.Button(label="+20"))
        d_box.append(Gtk.Button(label="Reset"))
        r_dpi.add_suffix(d_box)
        grp_hw.add(r_dpi)
        page_rem.add(grp_hw)

        self.view_stack.add_titled_with_icon(page_rem, "overview", "Overview", "phone-symbolic")

        # Tab 2: Stream & Display
        page_stream = Adw.PreferencesPage()
        grp_str = Adw.PreferencesGroup(title="Display &amp; Stream Settings")
        grp_str.add(Adw.ComboRow(title="Capture Source", model=Gtk.StringList.new(["Screen", "Camera"])))
        grp_str.add(Adw.ComboRow(title="Resolution Preset", model=Gtk.StringList.new(["Native 100% (1440x3120)", "High 80%", "Balanced 60%", "Fast 40%"])))
        grp_str.add(Adw.ComboRow(title="Max Framerate", model=Gtk.StringList.new(["60 FPS", "120 FPS", "90 FPS", "30 FPS"])))
        grp_str.add(Adw.ComboRow(title="Video Codec", model=Gtk.StringList.new(["H.265 (HEVC)", "H.264", "AV1"])))
        grp_str.add(Adw.EntryRow(title="Start App (Package Name)"))
        page_stream.add(grp_str)

        grp_vd = Adw.PreferencesGroup(title="Auxiliary &amp; Virtual Displays (scrcpy 5.0)")
        exp_vd = Adw.ExpanderRow(title="Virtual Display &amp; Flex Resizing")
        exp_vd.add_row(Adw.SwitchRow(title="Virtual Display Mode", subtitle="Secondary headless desktop"))
        exp_vd.add_row(Adw.SwitchRow(title="Flex Display", subtitle="Dynamic window resizing for virtual display"))
        exp_vd.add_row(Adw.ComboRow(title="IME Policy", model=Gtk.StringList.new(["Local", "Fallback", "Hide"])))
        exp_vd.add_row(Adw.ComboRow(title="Render Fit", model=Gtk.StringList.new(["Default", "Letterbox", "Stretched", "Unscaled"])))
        grp_vd.add(exp_vd)
        page_stream.add(grp_vd)

        self.view_stack.add_titled_with_icon(page_stream, "stream", "Stream", "video-display-symbolic")

        # Tab 3: Engine & Audio
        page_eng = Adw.PreferencesPage()
        grp_aud = Adw.PreferencesGroup(title="Audio Forwarding Engine")
        grp_aud.add(Adw.SwitchRow(title="Forward Audio", active=True))
        grp_aud.add(Adw.ComboRow(title="Audio Codec", model=Gtk.StringList.new(["Opus (Recommended)", "AAC", "FLAC", "RAW"])))
        grp_aud.add(Adw.ComboRow(title="Audio Source", model=Gtk.StringList.new(["output", "playback", "mic", "mic-camcorder"])))
        grp_aud.add(Adw.ComboRow(title="Audio Buffer Latency", model=Gtk.StringList.new(["20 ms (Ultra Low)", "40 ms", "50 ms", "100 ms"])))
        page_eng.add(grp_aud)

        grp_hid = Adw.PreferencesGroup(title="Hardware Input &amp; Peripherals (scrcpy 5.0)")
        exp_hid = Adw.ExpanderRow(title="HID Emulation &amp; Controller Passthrough")
        exp_hid.add_row(Adw.SwitchRow(title="Keyboard UHID Mode"))
        exp_hid.add_row(Adw.SwitchRow(title="Mouse UHID Mode"))
        exp_hid.add_row(Adw.SwitchRow(title="Gamepad Forwarding (UHID)", subtitle="Forward host controller as Android gamepad"))
        exp_hid.add_row(Adw.ComboRow(title="Mouse Button Bindings", model=Gtk.StringList.new(["Default", "Gaming Forward Clicks", "Android Navigation"])))
        grp_hid.add(exp_hid)
        page_eng.add(grp_hid)

        grp_hw = Adw.PreferencesGroup(title="Hardware Video Decoding")
        grp_hw.add(Adw.ComboRow(title="Hardware Video Decoder", model=Gtk.StringList.new(["vaapi (Hardware)", "Default (Auto)", "disabled (Software)"])))
        grp_hw.add(Adw.SwitchRow(title="Turn Screen Off During Session", active=True))
        grp_hw.add(Adw.SwitchRow(title="Power Off on Close"))
        page_eng.add(grp_hw)

        self.view_stack.add_titled_with_icon(page_eng, "engine", "Engine", "multimedia-player-symbolic")

        # Tab 4: Profiles & Records
        page_prof = Adw.PreferencesPage()
        grp_rec = Adw.PreferencesGroup(title="Lossless Session Recording")
        grp_rec.add(Adw.SwitchRow(title="Record Stream to Disk"))
        grp_rec.add(Adw.ComboRow(title="Container Format", model=Gtk.StringList.new(["MP4 (Universal)", "MKV (Crash Safe)"])))
        grp_rec.add(Adw.ActionRow(title="Recordings Directory", subtitle="~/Videos/Andy/"))
        page_prof.add(grp_rec)

        grp_p = Adw.PreferencesGroup(title="Active Profiles")
        grp_p.add(Adw.ComboRow(title="Load Profile", model=Gtk.StringList.new(["Default", "Low Latency Gaming", "High Fidelity Presentation", "Headless Desk Dock"])))
        page_prof.add(grp_p)

        self.view_stack.add_titled_with_icon(page_prof, "profiles", "Profiles", "document-save-symbolic")

class PreviewApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.wolfsekhar.andy.preview2", flags=Gio.ApplicationFlags.NON_UNIQUE)
    def do_activate(self):
        win = StudioCommandDeckWindow(application=self)
        win.present()

if __name__ == "__main__":
    app = PreviewApp()
    sys.exit(app.run(sys.argv))
