#!/usr/bin/env python3
"""
Andy UI Preview - Option 3: The Compact Floating Inspector
Minimal Canvas + Slide-Over Overlay Drawer (GNOME Boxes / Clapper Style)
"""
import sys
import os

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio, GLib

class CompactInspectorWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(default_width=880, default_height=660, title="Andy - Compact Floating Inspector Preview", **kwargs)

        self.toolbar_view = Adw.ToolbarView()
        self.set_content(self.toolbar_view)

        # ---------------------------------------------------------------------
        # 1. Top HeaderBar
        # ---------------------------------------------------------------------
        self.header_bar = Adw.HeaderBar()
        self.header_bar.set_title_widget(Adw.WindowTitle(title="Andy", subtitle="Option 3: Compact Floating Inspector"))

        # Device selector
        dev_dropdown = Gtk.DropDown(model=Gtk.StringList.new(["Pixel 8 Pro (USB 3.0)", "Galaxy Tab S9"]))
        self.header_bar.pack_start(dev_dropdown)

        # Inspector drawer toggle
        self.btn_inspector = Gtk.ToggleButton(icon_name="view-right-pane-symbolic", tooltip_text="Toggle Inspector Drawer")
        self.btn_inspector.connect("toggled", self.on_toggle_drawer)
        self.header_bar.pack_end(self.btn_inspector)

        self.toolbar_view.add_top_bar(self.header_bar)

        # ---------------------------------------------------------------------
        # 2. Main OverlaySplitView
        # ---------------------------------------------------------------------
        self.split_view = Adw.OverlaySplitView(sidebar_position=Gtk.PackType.END, min_sidebar_width=350, max_sidebar_width=380)
        self.toolbar_view.set_content(self.split_view)

        # ---------------------------------------------------------------------
        # 3. Content Slot: Minimal Canvas + Floating Action OSD
        # ---------------------------------------------------------------------
        canvas_overlay = Gtk.Overlay()
        self.split_view.set_content(canvas_overlay)

        # Canvas base vertical container
        canvas_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        canvas_box.set_margin_top(16)
        canvas_box.set_margin_bottom(20)
        canvas_box.set_margin_start(16)
        canvas_box.set_margin_end(16)
        canvas_overlay.set_child(canvas_box)

        # Top Quick Preset Chips
        chips_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        chips_box.set_halign(Gtk.Align.CENTER)

        chips = [
            ("🚀 60 FPS Smooth", True),
            ("💼 Low Latency", False),
            ("🎮 Gaming 120Hz", False),
            ("📹 4K Webcam", False),
        ]
        for label, active in chips:
            btn = Gtk.ToggleButton(label=label)
            btn.add_css_class("pill")
            if active:
                btn.set_active(True)
                btn.add_css_class("suggested-action")
            chips_box.append(btn)
        canvas_box.append(chips_box)

        # Center Mockup / Interactive Device Hub
        mockup_clamp = Adw.Clamp(maximum_size=520)
        mockup_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        mockup_box.add_css_class("card")
        mockup_box.set_margin_top(8)
        mockup_clamp.set_child(mockup_box)
        canvas_box.append(mockup_clamp)

        # Mockup Header
        m_head = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        m_head.set_margin_top(14)
        m_head.set_margin_start(16)
        m_head.set_margin_end(16)
        img_phone = Gtk.Image.new_from_icon_name("phone-symbolic")
        img_phone.set_pixel_size(28)
        m_head.append(img_phone)
        m_title = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        m_title.set_hexpand(True)
        m_title.append(Gtk.Label(label="Google Pixel 8 Pro", xalign=0, css_classes=["title-4"]))
        m_title.append(Gtk.Label(label="Connected via USB 3.0 • 1440x3120 Native", xalign=0, css_classes=["dim-label"]))
        m_head.append(m_title)
        m_head.append(Gtk.Label(label="🔋 88% ⚡", css_classes=["card", "accent"]))
        mockup_box.append(m_head)

        # Visual Screen Silhouette Frame
        frame_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        frame_box.set_halign(Gtk.Align.CENTER)
        frame_box.set_size_request(200, 160)
        frame_box.add_css_class("card")
        frame_box.append(Gtk.Image.new_from_icon_name("video-display-symbolic"))
        lbl_geom = Gtk.Label(label="Display 0 (Internal)\n1440 x 3120 (20:9)\nPortrait 0°", justify=Gtk.Justification.CENTER)
        lbl_geom.add_css_class("dim-label")
        frame_box.append(lbl_geom)
        mockup_box.append(frame_box)

        # Integrated Chin Remote Buttons
        remote_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        remote_row.set_halign(Gtk.Align.CENTER)
        remote_row.set_margin_bottom(14)
        remote_row.append(Gtk.Button(icon_name="go-previous-symbolic", label="Back"))
        remote_row.append(Gtk.Button(icon_name="user-home-symbolic", label="Home"))
        remote_row.append(Gtk.Button(icon_name="view-grid-symbolic", label="Recents"))
        remote_row.append(Gtk.Button(icon_name="preferences-system-notifications-symbolic", tooltip_text="Notifications"))
        remote_row.append(Gtk.Button(icon_name="audio-volume-high-symbolic", tooltip_text="Volume"))
        mockup_box.append(remote_row)

        # Floating Pill Action Bar (Clapper OSD Style)
        osd_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        osd_box.add_css_class("osd")
        osd_box.add_css_class("pill")
        osd_box.set_halign(Gtk.Align.CENTER)
        osd_box.set_valign(Gtk.Align.END)
        osd_box.set_margin_bottom(24)

        btn_stream = Gtk.Button(label="STREAM", icon_name="media-playback-start-symbolic")
        btn_stream.add_css_class("pill")
        btn_stream.add_css_class("suggested-action")
        osd_box.append(btn_stream)

        btn_mk = Gtk.Button(label="Connect M/K", icon_name="input-keyboard-symbolic")
        btn_mk.add_css_class("pill")
        osd_box.append(btn_mk)

        osd_box.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))
        osd_box.append(Gtk.Button(icon_name="camera-photo-symbolic", tooltip_text="Screenshot"))
        osd_box.append(Gtk.Button(icon_name="weather-clear-night-symbolic", tooltip_text="Screen Off"))
        osd_box.append(Gtk.Button(icon_name="edit-paste-symbolic", tooltip_text="Paste Clipboard"))

        canvas_overlay.add_overlay(osd_box)

        # ---------------------------------------------------------------------
        # 4. Sidebar Slot: Collapsible Inspector Drawer
        # ---------------------------------------------------------------------
        inspector_toolbar = Adw.ToolbarView()
        inspector_head = Adw.HeaderBar(show_end_title_buttons=False)
        inspector_head.set_title_widget(Adw.WindowTitle(title="Inspector &amp; Parameters"))
        btn_close = Gtk.Button(icon_name="window-close-symbolic", tooltip_text="Close Inspector")
        btn_close.connect("clicked", lambda b: self.set_drawer_open(False))
        inspector_head.pack_end(btn_close)
        inspector_toolbar.add_top_bar(inspector_head)

        inspector_scroll = Gtk.ScrolledWindow()
        page = Adw.PreferencesPage()
        inspector_scroll.set_child(page)
        inspector_toolbar.set_content(inspector_scroll)

        # Groups inside Inspector
        grp1 = Adw.PreferencesGroup(title="Video Stream Engine")
        grp1.add(Adw.ComboRow(title="Source", model=Gtk.StringList.new(["Screen", "Camera"])))
        grp1.add(Adw.ComboRow(title="Resolution Limit", model=Gtk.StringList.new(["Native 100%", "High 80%", "Balanced 60%"])))
        grp1.add(Adw.ComboRow(title="Max FPS", model=Gtk.StringList.new(["60 FPS", "120 FPS", "90 FPS", "30 FPS"])))
        grp1.add(Adw.ComboRow(title="Video Codec", model=Gtk.StringList.new(["H.264", "H.265", "AV1"])))
        grp1.add(Adw.EntryRow(title="Start App (Package Name)"))
        page.add(grp1)

        grp2 = Adw.PreferencesGroup(title="scrcpy 5.0 Virtual Display")
        grp2.add(Adw.SwitchRow(title="Virtual Display Mode"))
        grp2.add(Adw.SwitchRow(title="Flex Display (Dynamic Resize)"))
        grp2.add(Adw.ComboRow(title="Virtual Display IME", model=Gtk.StringList.new(["Local", "Fallback", "Hide"])))
        grp2.add(Adw.ComboRow(title="Render Fit", model=Gtk.StringList.new(["Default", "Letterbox", "Stretched"])))
        page.add(grp2)

        grp3 = Adw.PreferencesGroup(title="Audio &amp; HW Acceleration")
        grp3.add(Adw.SwitchRow(title="Forward Audio", active=True))
        grp3.add(Adw.ComboRow(title="Audio Codec", model=Gtk.StringList.new(["Opus", "AAC", "RAW"])))
        grp3.add(Adw.ComboRow(title="Hardware Video Decoding", model=Gtk.StringList.new(["vaapi (VA-API)", "Default (Auto)", "disabled"])))
        grp3.add(Adw.SwitchRow(title="Gamepad Forwarding (UHID)"))
        grp3.add(Adw.SwitchRow(title="Turn Screen Off"))
        page.add(grp3)

        self.split_view.set_sidebar(inspector_toolbar)
        self.set_drawer_open(False)

    def on_toggle_drawer(self, btn):
        self.set_drawer_open(btn.get_active())

    def set_drawer_open(self, open_state):
        self.split_view.set_show_sidebar(open_state)
        self.btn_inspector.set_active(open_state)

class PreviewApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.wolfsekhar.andy.preview3", flags=Gio.ApplicationFlags.NON_UNIQUE)
    def do_activate(self):
        win = CompactInspectorWindow(application=self)
        win.present()

if __name__ == "__main__":
    app = PreviewApp()
    sys.exit(app.run(sys.argv))
