from typing import Callable
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw

class RemoteSection(Gtk.Box):
    """
    Android remote interaction buttons: Navigation Bar, Status Shade, Clipboard, and Quick Controls.
    """
    def __init__(
        self,
        on_keyevent: Callable[[int, str], None],
        on_statusbar: Callable[[str], None],
        on_paste: Callable[[], None],
        on_touches: Callable[[], None],
        on_screenshot: Callable[[], None],
        on_power: Callable[[], None],
        on_volume: Callable[[str], None],
        on_reboot: Callable[[str], None],
        **kwargs
    ):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12, **kwargs)

        # Android Remote Controls Group
        self.remote_group = Adw.PreferencesGroup(title="Android Remote Controls")
        self.append(self.remote_group)

        # Virtual Navigation Bar
        self.nav_row = Adw.ActionRow(title="Navigation Bar")
        self.nav_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.nav_box.add_css_class("linked")
        self.nav_box.set_valign(Gtk.Align.CENTER)

        self.btn_nav_back = Gtk.Button(icon_name="go-previous-symbolic")
        self.btn_nav_back.set_tooltip_text("Back (KEYCODE_BACK)")
        self.btn_nav_back.connect("clicked", lambda b: on_keyevent(4, "Back"))

        self.btn_nav_home = Gtk.Button(icon_name="user-home-symbolic")
        self.btn_nav_home.set_tooltip_text("Home (KEYCODE_HOME)")
        self.btn_nav_home.connect("clicked", lambda b: on_keyevent(3, "Home"))

        self.btn_nav_recents = Gtk.Button(icon_name="view-grid-symbolic")
        self.btn_nav_recents.set_tooltip_text("Recents / App Switcher (KEYCODE_APP_SWITCH)")
        self.btn_nav_recents.connect("clicked", lambda b: on_keyevent(187, "Recents"))

        self.nav_box.append(self.btn_nav_back)
        self.nav_box.append(self.btn_nav_home)
        self.nav_box.append(self.btn_nav_recents)
        self.nav_row.add_suffix(self.nav_box)
        self.remote_group.add(self.nav_row)

        # System Shade & Clipboard
        self.system_row = Adw.ActionRow(title="System &amp; Clipboard")
        self.system_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.system_box.set_valign(Gtk.Align.CENTER)

        self.btn_notifications = Gtk.Button(icon_name="preferences-system-notifications-symbolic")
        self.btn_notifications.set_tooltip_text("Expand Notifications Shade")
        self.btn_notifications.connect("clicked", lambda b: on_statusbar("notifications"))

        self.btn_quicksettings = Gtk.Button(icon_name="emblem-system-symbolic")
        self.btn_quicksettings.set_tooltip_text("Expand Quick Settings Tray")
        self.btn_quicksettings.connect("clicked", lambda b: on_statusbar("settings"))

        self.btn_paste = Gtk.Button(icon_name="edit-paste-symbolic")
        self.btn_paste.set_tooltip_text("Paste PC Clipboard to Phone")
        self.btn_paste.connect("clicked", lambda b: on_paste())

        self.btn_touches = Gtk.Button(icon_name="touchpad-symbolic")
        self.btn_touches.set_tooltip_text("Toggle Show Touches on Device Screen")
        self.btn_touches.connect("clicked", lambda b: on_touches())

        self.system_box.append(self.btn_notifications)
        self.system_box.append(self.btn_quicksettings)
        self.system_box.append(self.btn_paste)
        self.system_box.append(self.btn_touches)
        self.system_row.add_suffix(self.system_box)
        self.remote_group.add(self.system_row)

        # Quick Controls Group
        self.tools_group = Adw.PreferencesGroup(title="Quick Device Controls")
        self.append(self.tools_group)

        self.tools_row = Adw.ActionRow(title="Quick Actions")
        self.tools_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.tools_box.set_valign(Gtk.Align.CENTER)

        self.btn_screenshot = Gtk.Button(icon_name="camera-photo-symbolic")
        self.btn_screenshot.set_tooltip_text("Take Screenshot (saves to Pictures/Andy)")
        self.btn_screenshot.connect("clicked", lambda b: on_screenshot())
        self.tools_box.append(self.btn_screenshot)

        self.btn_power = Gtk.Button(icon_name="system-shutdown-symbolic")
        self.btn_power.set_tooltip_text("Wake / Sleep Screen (Power Key)")
        self.btn_power.connect("clicked", lambda b: on_power())
        self.tools_box.append(self.btn_power)

        self.btn_vol_down = Gtk.Button(icon_name="audio-volume-low-symbolic")
        self.btn_vol_down.set_tooltip_text("Volume Down")
        self.btn_vol_down.connect("clicked", lambda b: on_volume("down"))
        self.tools_box.append(self.btn_vol_down)

        self.btn_vol_up = Gtk.Button(icon_name="audio-volume-high-symbolic")
        self.btn_vol_up.set_tooltip_text("Volume Up")
        self.btn_vol_up.connect("clicked", lambda b: on_volume("up"))
        self.tools_box.append(self.btn_vol_up)

        # Reboot Menu Button & Popover
        self.btn_reboot = Gtk.MenuButton()
        self.btn_reboot.set_icon_name("system-reboot-symbolic")
        self.btn_reboot.set_tooltip_text("Reboot Device...")

        reboot_popover = Gtk.Popover()
        reboot_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        reboot_box.set_margin_top(6)
        reboot_box.set_margin_bottom(6)
        reboot_box.set_margin_start(6)
        reboot_box.set_margin_end(6)

        btn_reboot_normal = Gtk.Button(label="Reboot System")
        btn_reboot_normal.add_css_class("flat")
        btn_reboot_normal.connect("clicked", lambda b: (reboot_popover.popdown(), on_reboot("normal")))

        btn_reboot_rec = Gtk.Button(label="Reboot to Recovery")
        btn_reboot_rec.add_css_class("flat")
        btn_reboot_rec.connect("clicked", lambda b: (reboot_popover.popdown(), on_reboot("recovery")))

        btn_reboot_bootloader = Gtk.Button(label="Reboot to Bootloader")
        btn_reboot_bootloader.add_css_class("flat")
        btn_reboot_bootloader.connect("clicked", lambda b: (reboot_popover.popdown(), on_reboot("bootloader")))

        reboot_box.append(btn_reboot_normal)
        reboot_box.append(btn_reboot_rec)
        reboot_box.append(btn_reboot_bootloader)
        reboot_popover.set_child(reboot_box)
        self.btn_reboot.set_popover(reboot_popover)
        self.tools_box.append(self.btn_reboot)

        self.tools_row.add_suffix(self.tools_box)
        self.tools_group.add(self.tools_row)

    def set_sensitive(self, sensitive: bool):
        self.btn_screenshot.set_sensitive(sensitive)
        self.btn_power.set_sensitive(sensitive)
        self.btn_vol_down.set_sensitive(sensitive)
        self.btn_vol_up.set_sensitive(sensitive)
        self.btn_reboot.set_sensitive(sensitive)
        self.btn_nav_back.set_sensitive(sensitive)
        self.btn_nav_home.set_sensitive(sensitive)
        self.btn_nav_recents.set_sensitive(sensitive)
        self.btn_notifications.set_sensitive(sensitive)
        self.btn_quicksettings.set_sensitive(sensitive)
        self.btn_paste.set_sensitive(sensitive)
        self.btn_touches.set_sensitive(sensitive)
