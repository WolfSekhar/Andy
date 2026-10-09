import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw


class AndyHeaderBar:
    """Header bar component for Andy.

    Provides theme toggle, profile selector & save, window title, and settings.
    """

    def __init__(self, on_theme_toggled, on_profile_selected, on_save_profile_clicked, on_settings_clicked):
        self.widget = Adw.HeaderBar()
        self.style_manager = Adw.StyleManager.get_default()

        # Theme Mode Toggle Button (Light/Dark)
        self.theme_button = Gtk.Button()
        self.theme_button.set_valign(Gtk.Align.CENTER)
        self.theme_button.connect("clicked", lambda b: on_theme_toggled())
        self.update_theme_icon()

        # Profile Selection Dropdown
        self.profile_model = Gtk.StringList()
        self.profile_dropdown = Gtk.DropDown(model=self.profile_model)
        self.profile_dropdown.set_valign(Gtk.Align.CENTER)
        self.profile_dropdown.set_tooltip_text("Load Saved Profile")
        self.profile_dropdown.connect("notify::selected", lambda d, p: on_profile_selected(d, p))

        # Save Profile Button
        self.save_button = Gtk.Button(icon_name="document-save-symbolic")
        self.save_button.set_valign(Gtk.Align.CENTER)
        self.save_button.set_tooltip_text("Save Profile")
        self.save_button.connect("clicked", lambda b: on_save_profile_clicked())

        # Settings Button
        self.settings_button = Gtk.Button(label="Settings", icon_name="emblem-system-symbolic")
        self.settings_button.set_valign(Gtk.Align.CENTER)
        self.settings_button.set_tooltip_text("Settings & Profiles")
        self.settings_button.connect("clicked", lambda b: on_settings_clicked())

        # Title widget (HeaderBar only hosts the centered window title and system window controls)
        self.window_title = Adw.WindowTitle(
            title="Andy",
            subtitle="scrcpy Wayland Controller"
        )
        self.widget.set_title_widget(self.window_title)

    def update_theme_icon(self):
        if self.style_manager.get_dark():
            self.theme_button.set_icon_name("display-brightness-symbolic")
            self.theme_button.set_tooltip_text("Switch to Light Mode")
        else:
            self.theme_button.set_icon_name("weather-clear-night-symbolic")
            self.theme_button.set_tooltip_text("Switch to Dark Mode")

    def set_profiles(self, profiles, select_name=None):
        n_items = self.profile_model.get_n_items()
        self.profile_model.splice(0, n_items, ["Default"])
        for p in profiles:
            self.profile_model.append(p)

        if select_name:
            for i in range(self.profile_model.get_n_items()):
                if self.profile_model.get_string(i) == select_name:
                    self.profile_dropdown.set_selected(i)
                    break

    def get_selected_profile_index(self):
        return self.profile_dropdown.get_selected()

    def get_profile_name(self, index):
        return self.profile_model.get_string(index)
