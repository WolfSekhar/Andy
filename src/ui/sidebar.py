from typing import Optional, Callable
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw

from core.config import APP_NAME, VERSION


class AndySidebar(Gtk.Box):
    """
    Permanent, non-collapsible slim utility sidebar for Andy.
    Houses profile management, appearance/theme switching, preferences,
    and system actions, keeping the top titlebar clean and focused.
    """

    def __init__(
        self,
        theme_button: Gtk.Button,
        profile_dropdown: Gtk.DropDown,
        save_button: Gtk.Button,
        settings_button: Gtk.Button,
        on_about_clicked: Optional[Callable[[], None]] = None,
        **kwargs
    ):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=14, **kwargs)
        self.add_css_class("sidebar-pane")
        self.set_size_request(220, -1)
        self.set_hexpand(False)
        self.set_vexpand(True)

        self.theme_button = theme_button
        self.profile_dropdown = profile_dropdown
        self.save_button = save_button
        self.settings_button = settings_button
        self.on_about_clicked = on_about_clicked

        # 1. Branding Header
        brand_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        brand_box.set_margin_bottom(4)

        brand_icon = Gtk.Image.new_from_icon_name("phone-symbolic")
        brand_icon.set_pixel_size(24)
        brand_box.append(brand_icon)

        brand_text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        brand_title = Gtk.Label(label=APP_NAME)
        brand_title.add_css_class("title-3")
        brand_title.set_xalign(0)
        brand_text_box.append(brand_title)

        brand_sub = Gtk.Label(label="Wayland scrcpy")
        brand_sub.add_css_class("caption")
        brand_sub.add_css_class("dim-label")
        brand_sub.set_xalign(0)
        brand_text_box.append(brand_sub)

        brand_box.append(brand_text_box)
        self.append(brand_box)

        # Separator
        self.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        # 2. Profiles Section
        sec_profiles = Gtk.Label(label="PROFILES")
        sec_profiles.add_css_class("dim-label")
        sec_profiles.add_css_class("caption")
        sec_profiles.set_xalign(0)
        self.append(sec_profiles)

        prof_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.profile_dropdown.set_hexpand(True)
        self.profile_dropdown.add_css_class("sidebar-dropdown")
        prof_row.append(self.profile_dropdown)

        self.save_button.set_tooltip_text("Save Active Profile")
        self.save_button.add_css_class("sidebar-btn")
        self.save_button.add_css_class("sidebar-save-btn")
        prof_row.append(self.save_button)
        self.append(prof_row)

        # 3. Appearance Section
        sec_theme = Gtk.Label(label="APPEARANCE")
        sec_theme.add_css_class("dim-label")
        sec_theme.add_css_class("caption")
        sec_theme.set_xalign(0)
        sec_theme.set_margin_top(6)
        self.append(sec_theme)

        self.theme_button.set_halign(Gtk.Align.FILL)
        self.theme_button.add_css_class("sidebar-btn")
        self.theme_button.add_css_class("sidebar-theme-btn")
        self.append(self.theme_button)

        # 4. System & Preferences Section
        sec_sys = Gtk.Label(label="PREFERENCES")
        sec_sys.add_css_class("dim-label")
        sec_sys.add_css_class("caption")
        sec_sys.set_xalign(0)
        sec_sys.set_margin_top(6)
        self.append(sec_sys)

        self.settings_button.set_halign(Gtk.Align.FILL)
        self.settings_button.add_css_class("sidebar-btn")
        self.settings_button.add_css_class("sidebar-settings-btn")
        self.append(self.settings_button)

        self.about_button = Gtk.Button(label="About Andy", icon_name="help-about-symbolic")
        self.about_button.set_halign(Gtk.Align.FILL)
        self.about_button.add_css_class("sidebar-btn")
        self.about_button.add_css_class("sidebar-about-btn")
        if on_about_clicked:
            self.about_button.connect("clicked", lambda b: on_about_clicked())
        self.append(self.about_button)

        # Push spacer
        spacer = Gtk.Box(vexpand=True)
        self.append(spacer)

        # Version tag at bottom
        ver_label = Gtk.Label(label=f"Andy v{VERSION}")
        ver_label.add_css_class("caption")
        ver_label.add_css_class("dim-label")
        ver_label.set_halign(Gtk.Align.CENTER)
        self.append(ver_label)
