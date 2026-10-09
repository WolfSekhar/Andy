#!/usr/bin/env python3
import sys
import os
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio, GLib

# Add preview dir to sys.path
preview_dir = os.path.dirname(os.path.abspath(__file__))
if preview_dir not in sys.path:
    sys.path.insert(0, preview_dir)

from design_1_sidebar import Design1Sidebar
from design_2_tabbed import Design2TabbedDeck
from design_3_hero_studio import Design3HeroStudio
from design_4_compact import Design4CompactCompanion
from design_5_pro_console import Design5ProConsole

APP_ID = "com.wolfsekhar.AndyDesignPreview"

class PreviewWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.set_title("Andy - UX Design Showcase (5 Concepts)")
        self.set_default_size(1050, 720)

        self.style_manager = Adw.StyleManager.get_default()

        # Main Layout
        self.toolbar_view = Adw.ToolbarView()
        self.set_content(self.toolbar_view)

        # Header Bar
        self.header_bar = Adw.HeaderBar()
        self.toolbar_view.add_top_bar(self.header_bar)

        # Theme toggle button
        self.theme_btn = Gtk.Button()
        self.theme_btn.connect("clicked", self.on_theme_toggle)
        self.update_theme_icon()
        self.header_bar.pack_start(self.theme_btn)

        # Design Selector in Header
        selector_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        lbl = Gtk.Label(label="Preview Concept:")
        lbl.add_css_class("heading")
        selector_box.append(lbl)

        self.design_dropdown = Gtk.DropDown()
        self.design_model = Gtk.StringList()
        designs = [
            "1. Sidebar Split (GNOME NavigationSplitView)",
            "2. Tabbed Deck (ViewSwitcher + Pinned Action Dock)",
            "3. Hero Studio (1-Click Presets + Accordion Drawers)",
            "4. Compact Companion (Floating Widget 460px)",
            "5. Pro Media Console (Studio Dual Deck & Telemetry)"
        ]
        for d in designs:
            self.design_model.append(d)
        self.design_dropdown.set_model(self.design_model)
        self.design_dropdown.connect("notify::selected", self.on_design_changed)
        selector_box.append(self.design_dropdown)

        self.header_bar.set_title_widget(selector_box)

        # Info Button
        info_btn = Gtk.Button(icon_name="help-about-symbolic")
        info_btn.set_tooltip_text("Concept Details")
        info_btn.connect("clicked", self.show_concept_info)
        self.header_bar.pack_end(info_btn)

        # Stack container for the 5 designs
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_transition_duration(250)
        self.toolbar_view.set_content(self.stack)

        # Instantiating the 5 live designs
        self.d1 = Design1Sidebar()
        self.d2 = Design2TabbedDeck()
        self.d3 = Design3HeroStudio()
        self.d4 = Design4CompactCompanion()
        self.d5 = Design5ProConsole()

        self.stack.add_named(self.d1, "d1")
        self.stack.add_named(self.d2, "d2")
        self.stack.add_named(self.d3, "d3")
        self.stack.add_named(self.d4, "d4")
        self.stack.add_named(self.d5, "d5")

        # Initial selection
        self.stack.set_visible_child_name("d1")

    def on_design_changed(self, dropdown, pspec):
        idx = dropdown.get_selected()
        mapping = {0: "d1", 1: "d2", 2: "d3", 3: "d4", 4: "d5"}
        name = mapping.get(idx, "d1")
        self.stack.set_visible_child_name(name)

        # Dynamic window sizing hint for Compact Companion
        if idx == 3: # Compact
            self.set_default_size(520, 680)
        elif idx == 4: # Pro Console
            self.set_default_size(1100, 750)
        else:
            self.set_default_size(1000, 700)

    def on_theme_toggle(self, btn):
        if self.style_manager.get_dark():
            self.style_manager.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
        else:
            self.style_manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
        self.update_theme_icon()

    def update_theme_icon(self):
        if self.style_manager.get_dark():
            self.theme_btn.set_icon_name("display-brightness-symbolic")
            self.theme_btn.set_tooltip_text("Switch to Light Mode")
        else:
            self.theme_btn.set_icon_name("weather-clear-night-symbolic")
            self.theme_btn.set_tooltip_text("Switch to Dark Mode")

    def show_concept_info(self, btn):
        idx = self.design_dropdown.get_selected()
        info_texts = [
            ("Concept 1: Modern GNOME NavigationSplitView",
             "• Inspired by GNOME Settings & Cartridges.\n• Left sidebar provides persistent device telemetry and mode switcher.\n• Right canvas presents spacious, uncluttered Libadwaita preference cards.\n• Eliminates 3-column squeeze on standard displays."),
            ("Concept 2: Tabbed Deck with Pinned Footer Dock",
             "• Inspired by modern media decks (Amberol, Decibels).\n• Centered ViewSwitcher breaks settings into focused zero-scroll tabs.\n• Pinned bottom dock ensures the STREAM button and battery meter are always visible.\n• Prevents hunting for the launch trigger."),
            ("Concept 3: Quick-Launch Hero Studio",
             "• Expressive Hero Status card with live connection badges.\n• 1-Click presets for instant launch (Gaming, Office, Smooth Media, Battery Saver).\n• Deep fine-tuning neatly folded inside expandable drawers (Adw.ExpanderRow)."),
            ("Concept 4: Compact Companion (Floating 460px Widget)",
             "• Ultra-compact utility window ideal for Wayland tiling WMs (Sway/Hyprland) and laptop screens.\n• Interactive quick-tiles for Resolution, FPS, GPU, and Codec.\n• Full-width vibrant launch button at the bottom."),
            ("Concept 5: Pro Media Console / Split Studio",
             "• Inspired by broadcast control rooms and OBS Studio.\n• Left panel: Real-time telemetry, master triggers, and live diagnostics.\n• Right panel: Dual-deck controls for display pipeline and GPU/Wayland latency tuning.")
        ]
        title, text = info_texts[idx]
        dialog = Adw.MessageDialog(transient_for=self, heading=title, body=text)
        dialog.add_response("ok", "Got It")
        dialog.present()

class PreviewApplication(Adw.Application):
    def __init__(self):
        super().__init__(
            application_id=APP_ID,
            flags=Gio.ApplicationFlags.NON_UNIQUE
        )

    def do_activate(self):
        win = PreviewWindow(application=self)
        win.present()

if __name__ == "__main__":
    app = PreviewApplication()
    app.run(sys.argv)
