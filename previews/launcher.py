#!/usr/bin/env python3
"""
Andy UI Preview Hub - Interactive Layout Switcher
Launch and compare all 5 GNOME Circle layout redesign proposals interactively.
"""
import sys
import os
import subprocess

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio, GLib

class PreviewHubWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(default_width=760, default_height=680, title="Andy - UI Overhaul Preview Hub", **kwargs)

        toolbar_view = Adw.ToolbarView()
        self.set_content(toolbar_view)

        header = Adw.HeaderBar()
        header.set_title_widget(Adw.WindowTitle(title="Andy UI Preview Hub", subtitle="Test and Compare 5 Layout Proposals"))
        toolbar_view.add_top_bar(header)

        scroll = Gtk.ScrolledWindow()
        clamp = Adw.Clamp(maximum_size=720)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        box.set_margin_top(16)
        box.set_margin_bottom(24)
        box.set_margin_start(16)
        box.set_margin_end(16)
        clamp.set_child(box)
        scroll.set_child(clamp)
        toolbar_view.set_content(scroll)

        # Introduction Banner
        banner_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        banner_box.add_css_class("card")
        banner_box.set_margin_bottom(8)
        
        b_in = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        b_in.set_margin_top(14)
        b_in.set_margin_bottom(14)
        b_in.set_margin_start(16)
        b_in.set_margin_end(16)
        lbl_head = Gtk.Label(label="✨ Interactive GNOME Circle Layout Previews", xalign=0, css_classes=["title-3"])
        lbl_sub = Gtk.Label(
            label="Click 'Open Preview Window' on any layout below to launch an interactive, fully functioning window. You can run multiple windows side-by-side to compare visual ergonomics, widget hierarchies, and responsiveness.",
            xalign=0, wrap=True, css_classes=["dim-label"]
        )
        b_in.append(lbl_head)
        b_in.append(lbl_sub)
        banner_box.append(b_in)
        box.append(banner_box)

        # 5 Proposals List
        proposals = [
            (
                "Option 1: The Modern Workstation",
                "GNOME Settings & Cartridges Style • Adaptive 2-pane Adw.NavigationSplitView with persistent header action hub and zero scrolling clutter.",
                "preview_1_modern_workstation.py",
                "view-split-left-symbolic",
                ["2-Pane SplitView", "Zero Scroll", "Adaptive Mobile Stack"]
            ),
            (
                "Option 2: The Studio Command Deck",
                "Bottles & Amberol Style • High-impact Hero Live Device Card (battery, USB/Wi-Fi telemetry, 1-click Stream & M/K) with top Adw.ViewSwitcherTitle tabs.",
                "preview_2_studio_command_deck.py",
                "multimedia-player-symbolic",
                ["Hero Live Deck", "Top ViewSwitcher", "Bottles Aesthetic"]
            ),
            (
                "Option 3: The Compact Floating Inspector",
                "GNOME Boxes & Clapper Style • Minimal central phone canvas with top preset chips, bottom floating action OSD pill, and slide-over Adw.OverlaySplitView drawer.",
                "preview_3_compact_inspector.py",
                "view-right-pane-symbolic",
                ["Minimal Canvas", "Overlay Drawer", "Floating Pill OSD"]
            ),
            (
                "Option 4: The Modular Card Hub",
                "Fragments & Pods Style • Refined 3-pod Libadwaita cards with interactive top Profile Chips bar (Default, Work, Gaming, Webcam, Broken Screen) and LevelBar telemetry.",
                "preview_4_modular_card_hub.py",
                "view-grid-symbolic",
                ["Profile Chips Bar", "3-Pod Grid", "Visual Segmented Buttons"]
            ),
            (
                "Option 5: The Action-Driven Assistant",
                "Pika Backup & Upscaler Style • 5 task-oriented human goal cards (Mirroring, 2nd Display, HD Webcam, Gaming, Rescue) with inline fine-tuning expanders.",
                "preview_5_action_assistant.py",
                "system-run-symbolic",
                ["5 Goal Workflows", "1-Click Launch", "Inline Fine-Tuning"]
            ),
        ]

        grp = Adw.PreferencesGroup(title="Layout Overhaul Designs")
        for title, desc, script_name, icon, tags in proposals:
            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            card.add_css_class("card")
            card.set_margin_bottom(8)

            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            row.set_margin_top(12)
            row.set_margin_start(14)
            row.set_margin_end(14)

            img = Gtk.Image.new_from_icon_name(icon)
            img.set_pixel_size(28)
            row.append(img)

            t_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            t_box.set_hexpand(True)
            t_box.append(Gtk.Label(label=title, xalign=0, css_classes=["title-4"]))
            t_box.append(Gtk.Label(label=desc, xalign=0, wrap=True, css_classes=["dim-label"]))
            row.append(t_box)

            btn = Gtk.Button(label="Open Preview", icon_name="media-playback-start-symbolic")
            btn.add_css_class("pill")
            btn.add_css_class("suggested-action")
            btn.set_valign(Gtk.Align.CENTER)
            btn.connect("clicked", self.make_launch_handler(script_name))
            row.append(btn)
            card.append(row)

            # Tags row
            tag_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            tag_box.set_margin_start(54)
            tag_box.set_margin_bottom(12)
            for t in tags:
                lbl_t = Gtk.Label(label=t)
                lbl_t.add_css_class("card")
                lbl_t.set_margin_top(2)
                lbl_t.set_margin_bottom(2)
                lbl_t.set_margin_start(6)
                lbl_t.set_margin_end(6)
                tag_box.append(lbl_t)
            card.append(tag_box)

            grp.add(card)

        box.append(grp)

    def make_launch_handler(self, script_name):
        def _launch(btn):
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), script_name)
            venv_python = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "venv", "bin", "python3")
            python_bin = venv_python if os.path.isfile(venv_python) else sys.executable
            env = os.environ.copy()
            env["GDK_BACKEND"] = "wayland,x11"
            subprocess.Popen([python_bin, script_path], env=env)
        return _launch

class PreviewHubApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.wolfsekhar.andy.previewhub", flags=Gio.ApplicationFlags.NON_UNIQUE)
    def do_activate(self):
        win = PreviewHubWindow(application=self)
        win.present()

if __name__ == "__main__":
    app = PreviewHubApp()
    sys.exit(app.run(sys.argv))
