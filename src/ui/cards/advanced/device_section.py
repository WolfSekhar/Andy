import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw
from core.config import TIMEOUT_PRESETS, MOUSE_BIND_PRESETS

class DeviceSection(Adw.PreferencesGroup):
    """
    Android device runtime parameters (Screen Off, UHID, Touches, Timeout, Gamepad, Mouse Binds, Power/Lifecycle).
    """
    def __init__(self, **kwargs):
        super().__init__(title="Device Parameters", **kwargs)

        self.param_screen_off = Adw.SwitchRow(title="Turn Screen Off")
        self.param_stay_awake = Adw.SwitchRow(title="Stay Awake")
        self.param_no_audio = Adw.SwitchRow(title="No Audio")
        self.param_read_only = Adw.SwitchRow(title="Read-Only Mode")
        self.param_keyboard_uhid = Adw.SwitchRow(title="Keyboard (HID/OTG Mode)")
        self.param_mouse_uhid = Adw.SwitchRow(title="Mouse (HID/OTG Mode)")
        self.param_gamepad_uhid = Adw.SwitchRow(
            title="Gamepad (UHID Mode)",
            subtitle="Forward physical or simulated gamepad as UHID"
        )

        self.mouse_bind_row = Adw.ActionRow(title="Mouse Bindings")
        self.mouse_bind_model = Gtk.StringList()
        for m in MOUSE_BIND_PRESETS:
            self.mouse_bind_model.append(m)
        self.mouse_bind_dropdown = Gtk.DropDown(model=self.mouse_bind_model)
        self.mouse_bind_dropdown.set_valign(Gtk.Align.CENTER)
        self.mouse_bind_row.add_suffix(self.mouse_bind_dropdown)

        self.param_legacy_paste = Adw.SwitchRow(
            title="Legacy Paste",
            subtitle="Inject key events instead of clipboard synchronization"
        )
        self.param_no_clipboard_autosync = Adw.SwitchRow(
            title="Disable Clipboard Autosync",
            subtitle="Do not synchronize clipboard automatically"
        )
        self.param_power_off_on_close = Adw.SwitchRow(
            title="Power Off on Close",
            subtitle="Turn screen off and lock device when session ends"
        )
        self.param_no_power_on = Adw.SwitchRow(
            title="No Power On",
            subtitle="Do not turn the screen on when scrcpy starts"
        )

        self.time_limit_row = Adw.EntryRow(title="Time Limit (seconds)")

        self.param_show_touches = Adw.SwitchRow(
            title="Show Touches During Stream",
            subtitle="Display physical touch circles on screen"
        )
        self.param_keep_active = Adw.SwitchRow(
            title="Keep Device Active",
            subtitle="Simulate user activity to prevent device lock/idle"
        )

        self.timeout_row = Adw.ActionRow(title="Screen Off Timeout")
        self.timeout_model = Gtk.StringList()
        for t in TIMEOUT_PRESETS:
            self.timeout_model.append(t)
        self.timeout_dropdown = Gtk.DropDown(model=self.timeout_model)
        self.timeout_dropdown.set_valign(Gtk.Align.CENTER)
        self.timeout_row.add_suffix(self.timeout_dropdown)

        self.add(self.param_screen_off)
        self.add(self.param_stay_awake)
        self.add(self.param_no_audio)
        self.add(self.param_read_only)
        self.add(self.param_keyboard_uhid)
        self.add(self.param_mouse_uhid)
        self.add(self.param_gamepad_uhid)
        self.add(self.mouse_bind_row)
        self.add(self.param_legacy_paste)
        self.add(self.param_no_clipboard_autosync)
        self.add(self.param_power_off_on_close)
        self.add(self.param_no_power_on)
        self.add(self.time_limit_row)
        self.add(self.param_show_touches)
        self.add(self.param_keep_active)
        self.add(self.timeout_row)

        self.param_read_only.connect("notify::active", self.on_read_only_toggled)

    def on_read_only_toggled(self, switch, pspec):
        is_read_only = switch.get_active()
        self.param_keyboard_uhid.set_sensitive(not is_read_only)
        self.param_mouse_uhid.set_sensitive(not is_read_only)
        self.param_gamepad_uhid.set_sensitive(not is_read_only)
        if is_read_only:
            self.param_keyboard_uhid.set_active(False)
            self.param_mouse_uhid.set_active(False)
            self.param_gamepad_uhid.set_active(False)

    def set_camera_mode(self, enabled: bool):
        sensitive = not enabled
        self.param_screen_off.set_sensitive(sensitive)
        self.param_read_only.set_sensitive(sensitive)
        self.param_keyboard_uhid.set_sensitive(sensitive)
        self.param_mouse_uhid.set_sensitive(sensitive)
        self.param_gamepad_uhid.set_sensitive(sensitive)
        self.param_show_touches.set_sensitive(sensitive)
        self.timeout_row.set_sensitive(sensitive)

        if enabled:
            self.param_screen_off.set_active(False)
            self.param_read_only.set_active(False)
            self.param_keyboard_uhid.set_active(False)
            self.param_mouse_uhid.set_active(False)
            self.param_gamepad_uhid.set_active(False)
            self.param_show_touches.set_active(False)
            self.timeout_dropdown.set_selected(0)
