#!/usr/bin/env python3
"""
Andy UI Preview - Option 5: The Action-Driven Assistant
Workflow & Goal-Oriented Task Cards with Inline Fine-Tuning (Pika Backup / Upscaler Style)
"""
import sys
import os

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio, GLib

class ActionAssistantWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(default_width=960, default_height=740, title="Andy - Action-Driven Assistant Preview", **kwargs)

        self.toolbar_view = Adw.ToolbarView()
        self.set_content(self.toolbar_view)

        # ---------------------------------------------------------------------
        # 1. HeaderBar
        # ---------------------------------------------------------------------
        self.header_bar = Adw.HeaderBar()
        self.header_bar.set_title_widget(Adw.WindowTitle(title="Andy", subtitle="Option 5: Action-Driven Assistant"))

        dev_dropdown = Gtk.DropDown(model=Gtk.StringList.new(["Pixel 8 Pro (USB 3.0)", "Galaxy Tab S9"]))
        self.header_bar.pack_start(dev_dropdown)

        btn_prefs = Gtk.Button(icon_name="emblem-system-symbolic", tooltip_text="Preferences")
        self.header_bar.pack_end(btn_prefs)

        self.toolbar_view.add_top_bar(self.header_bar)

        # ---------------------------------------------------------------------
        # 2. Main Scroll & Content Box
        # ---------------------------------------------------------------------
        scroll = Gtk.ScrolledWindow()
        clamp = Adw.Clamp(maximum_size=880)
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        main_box.set_margin_top(16)
        main_box.set_margin_bottom(24)
        main_box.set_margin_start(16)
        main_box.set_margin_end(16)
        clamp.set_child(main_box)
        scroll.set_child(clamp)
        self.toolbar_view.set_content(scroll)

        # ---------------------------------------------------------------------
        # 3. Connected Device Banner
        # ---------------------------------------------------------------------
        banner_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        banner_box.add_css_class("card")
        banner_box.set_margin_bottom(4)

        b_icon = Gtk.Image.new_from_icon_name("phone-symbolic")
        b_icon.set_margin_start(16)
        b_icon.set_pixel_size(24)
        banner_box.append(b_icon)

        b_text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        b_text.set_hexpand(True)
        b_text.set_margin_top(12)
        b_text.set_margin_bottom(12)
        b_text.append(Gtk.Label(label="🟢 Connected: Google Pixel 8 Pro", xalign=0, css_classes=["title-4"]))
        b_text.append(Gtk.Label(label="Android 16 • USB 3.0 • 1440x3120 @ 120Hz • Battery: 88% ⚡", xalign=0, css_classes=["dim-label"]))
        banner_box.append(b_text)

        b_btn = Gtk.Button(icon_name="view-refresh-symbolic", tooltip_text="Scan Devices")
        b_btn.set_margin_end(16)
        b_btn.set_valign(Gtk.Align.CENTER)
        banner_box.append(b_btn)

        main_box.append(banner_box)

        lbl_section = Gtk.Label(label="CHOOSE A WORKFLOW GOAL:", xalign=0, css_classes=["title-4", "dim-label"])
        lbl_section.set_margin_top(6)
        main_box.append(lbl_section)

        # ---------------------------------------------------------------------
        # 4. THE 5 GOAL WORKFLOW CARDS
        # ---------------------------------------------------------------------
        # Workflow 1: Desktop Mirroring
        main_box.append(self.create_workflow_card(
            title="Desktop Mirroring",
            subtitle="Standard screen projection with automatic resolution, 60 FPS, and lossless audio pass-through.",
            icon_name="video-display-symbolic",
            badges=["Auto Res", "60 FPS", "Low Latency"],
            action_label="Mirror Screen 🚀",
            fine_tune_rows=[
                Adw.ComboRow(title="Resolution Scale", model=Gtk.StringList.new(["100% Native", "80% Balanced", "60% Fast"])),
                Adw.ComboRow(title="Max FPS Cap", model=Gtk.StringList.new(["60 FPS", "30 FPS"])),
                Adw.SwitchRow(title="Turn Device Screen Off", active=True),
                Adw.SwitchRow(title="Show Touch Ripples"),
            ]
        ))

        # Workflow 2: Productivity & 2nd Display
        main_box.append(self.create_workflow_card(
            title="Productivity &amp; 2nd Display",
            subtitle="Create an independent virtual secondary display with physical mouse and keyboard pass-through.",
            icon_name="display-projector-symbolic",
            badges=["Virtual Display", "UHID Pass", "Borderless"],
            action_label="Launch Workspace 🚀",
            fine_tune_rows=[
                Adw.EntryRow(title="Virtual Display Geometry (e.g. 1920x1080/400)"),
                Adw.SwitchRow(title="Flex Display (Dynamic Window Resizing)", active=True),
                Adw.ComboRow(title="Virtual Display IME", model=Gtk.StringList.new(["Local (PC Keyboard)", "Fallback", "Hide"])),
                Adw.SwitchRow(title="Keep Content on Exit", subtitle="Preserve background apps when closing window", active=True),
                Adw.EntryRow(title="Direct App Launch (e.g. com.android.chrome)"),
            ]
        ))

        # Workflow 3: HD Webcam & Studio Mic
        main_box.append(self.create_workflow_card(
            title="HD Webcam &amp; Studio Mic",
            subtitle="Stream camera sensors directly to PC as an ultra-high definition webcam with studio microphone.",
            icon_name="camera-web-symbolic",
            badges=["1080p60", "Studio Mic", "High Speed"],
            action_label="Start Webcam 📹",
            fine_tune_rows=[
                Adw.ComboRow(title="Camera Optics", model=Gtk.StringList.new(["Back Camera 0 (4K 60fps)", "Front Camera 1 (1080p)"])),
                Adw.SwitchRow(title="Camera Torch (Ring Light)", subtitle="Activate LED flash during stream"),
                Adw.EntryRow(title="Camera Zoom Factor (e.g. 1.0, 2.5)"),
                Adw.ComboRow(title="Audio Profile", model=Gtk.StringList.new(["mic-camcorder (Directional)", "mic (Standard)", "mic-unprocessed (Raw)"])),
            ]
        ))

        # Workflow 4: Mobile Gaming Station
        main_box.append(self.create_workflow_card(
            title="Mobile Gaming Station",
            subtitle="High-framerate 120Hz stream with hardware gamepad emulation, VA-API decode, and 0ms buffer.",
            icon_name="input-gaming-symbolic",
            badges=["120 FPS", "Gamepad UHID", "VA-API 0ms"],
            action_label="Play Game 🎮",
            fine_tune_rows=[
                Adw.ComboRow(title="Refresh Rate Target", model=Gtk.StringList.new(["120 FPS (High-Refresh)", "90 FPS", "60 FPS"])),
                Adw.SwitchRow(title="Gamepad Forwarding (UHID)", active=True),
                Adw.ComboRow(title="Mouse Button Scheme", model=Gtk.StringList.new(["Gaming Forward Clicks (++++)", "Android Actions (bhsn)"])),
                Adw.ComboRow(title="Hardware Video Decoding", model=Gtk.StringList.new(["vaapi (Hardware)", "Default"])),
                Adw.SwitchRow(title="Audio Duplication", subtitle="Hear audio on phone headphones + PC"),
            ]
        ))

        # Workflow 5: Rescue & Recovery Hub
        main_box.append(self.create_workflow_card(
            title="Rescue &amp; Recovery Hub",
            subtitle="Broken AMOLED recovery, headless OTG mouse/keyboard fallback, live DPI adjustment, and fast reboot.",
            icon_name="system-run-symbolic",
            badges=["Broken AMOLED", "OTG Headless", "Density Slider"],
            action_label="Enter Rescue Hub 🛠️",
            is_destructive=True,
            fine_tune_rows=[
                Adw.SwitchRow(title="Headless OTG Mode", subtitle="Forward keyboard/mouse without starting video stream"),
                Adw.ActionRow(title="Display Density Modifier (DPI)", subtitle="Live ADB override for oversized or broken layouts"),
                Adw.ActionRow(title="Screen Unlock Bypass", subtitle="Inject Keyevent 82 (Menu / Wake)"),
                Adw.ActionRow(title="Remote Reboot Trigger", subtitle="Normal Reboot / Recovery / Fastboot"),
            ]
        ))

    def create_workflow_card(self, title, subtitle, icon_name, badges, action_label, fine_tune_rows, is_destructive=False):
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        card.add_css_class("card")
        card.set_margin_bottom(6)

        # Header with icon and action
        head = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        head.set_margin_top(14)
        head.set_margin_start(16)
        head.set_margin_end(16)

        icon = Gtk.Image.new_from_icon_name(icon_name)
        icon.set_pixel_size(32)
        head.append(icon)

        t_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        t_box.set_hexpand(True)
        lbl_t = Gtk.Label(label=title, use_markup=True, xalign=0, css_classes=["title-4"])
        lbl_s = Gtk.Label(label=subtitle, xalign=0, wrap=True, css_classes=["dim-label"])
        t_box.append(lbl_t)
        t_box.append(lbl_s)
        head.append(t_box)

        # CTA Button
        btn = Gtk.Button(label=action_label)
        btn.add_css_class("pill")
        if is_destructive:
            btn.add_css_class("destructive-action")
        else:
            btn.add_css_class("suggested-action")
        btn.set_valign(Gtk.Align.CENTER)
        head.append(btn)
        card.append(head)

        # Badges Row
        badge_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        badge_box.set_margin_start(58)
        badge_box.set_margin_end(16)
        for b in badges:
            lbl = Gtk.Label(label=b)
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

        # Wrap in a preferences group to fit Libadwaita styling
        grp = Adw.PreferencesGroup()
        grp.add(expander)
        card.append(grp)

        return card

class PreviewApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.wolfsekhar.andy.preview5", flags=Gio.ApplicationFlags.NON_UNIQUE)
    def do_activate(self):
        win = ActionAssistantWindow(application=self)
        win.present()

if __name__ == "__main__":
    app = PreviewApp()
    sys.exit(app.run(sys.argv))
