import os
import sys
import threading
from typing import List, Optional

from gi.repository import Gtk, Adw, GLib, Gdk

from core.process_launcher import ScrcpyProcessManager
from core.config import UI_SCALE_STEPS
from services.device_service import get_connected_devices
from services.profile_service import save_profile, load_profile, list_profiles
from services.settings_service import get_setting, set_setting
from services.notification_service import notification_service
from services.inhibit_service import inhibit_service

from ui.common.css import apply_application_css
from ui.common.scale_control import ScaleControl
from ui.common.error_dialog import show_error_dialog
from ui.about_dialog import show_about_dialog

from ui.cards.stream.stream_card import StreamCard
from ui.cards.advanced.advanced_card import AdvancedCard
from ui.cards.details.details_card import DetailsCard

from ui.header_bar import AndyHeaderBar
from ui.sidebar import AndySidebar
from ui.settings_dialog import SettingsDialog
from ui.layouts import ClassicLayout, LAYOUT_CLASSIC

class AndyWindow(Gtk.ApplicationWindow):
    SCALE_STEPS = UI_SCALE_STEPS

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.set_title("Andy")
        self.set_icon_name("com.wolfsekhar.Andy")
        self.set_resizable(True)
        self.set_decorated(True)
        self.set_default_size(1050, 680)

        # Process supervisor
        self.process_manager = ScrcpyProcessManager()

        # Theme Management (Libadwaita)
        self.style_manager = Adw.StyleManager.get_default()
        self.apply_saved_theme()

        # Custom CSS
        self.setup_css()

        # Amberol-style seamless titlebar (textless, flat, immersed into window surface)
        self.add_css_class("amberol-window")
        self.header_bar = AndyHeaderBar(
            on_theme_toggled=self.on_theme_toggled,
            on_profile_selected=self.on_profile_selected,
            on_save_profile_clicked=self.on_save_profile_clicked,
            on_settings_clicked=self.on_settings_clicked,
        )
        self.set_titlebar(self.header_bar.widget)

        # Permanent slim utility sidebar
        self.sidebar = AndySidebar(
            theme_button=self.header_bar.theme_button,
            profile_dropdown=self.header_bar.profile_dropdown,
            save_button=self.header_bar.save_button,
            settings_button=self.header_bar.settings_button,
            on_about_clicked=self.on_about_clicked,
        )

        # Main layout container
        self.toolbar_view = Adw.ToolbarView()
        self.set_child(self.toolbar_view)

        # Horizontal paning: Left = Permanent Slim Sidebar, Right = Main Content
        self.content_panes = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.content_panes.set_vexpand(True)
        self.content_panes.set_hexpand(True)
        self.toolbar_view.set_content(self.content_panes)

        # Append permanent non-collapsible slim sidebar on the left
        self.content_panes.append(self.sidebar)

        # Right side: Main vertical box with device bar and classic cards
        self.main_scroll = Gtk.ScrolledWindow()
        self.main_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.main_scroll.set_hexpand(True)
        self.main_scroll.set_vexpand(True)
        self.content_panes.append(self.main_scroll)

        self.main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.main_vbox.set_vexpand(True)
        self.main_vbox.set_hexpand(True)
        self.main_scroll.set_child(self.main_vbox)

        # Top section & split view (builds classic card widgets on self and main_vbox)
        self.setup_device_selection()
        self.setup_split_view()

        # Initial device and profile load
        self.devices = []
        self.refresh_devices()
        self.refresh_profiles()

        # Services application reference
        app = self.get_application()
        if app:
            notification_service.set_application(app)
            inhibit_service.set_application(app)
        self.connect("notify::application", self._on_application_set)

        # Keyboard shortcuts controller
        key_controller = Gtk.EventControllerKey.new()
        key_controller.connect("key-pressed", self.on_key_pressed)
        self.add_controller(key_controller)

        # Handle window close to cleanup subprocess
        self.connect("close-request", self.on_close_request)

    @property
    def scrcpy_process(self):
        return self.process_manager.process

    @scrcpy_process.setter
    def scrcpy_process(self, val):
        self.process_manager.process = val

    @property
    def current_scale(self):
        return self.scale_control.current_scale

    @current_scale.setter
    def current_scale(self, val):
        self.scale_control.current_scale = val

    def setup_css(self):
        apply_application_css()

    def setup_device_selection(self):
        self.top_clamp = Adw.Clamp()
        self.top_clamp.set_maximum_size(1200)
        self.top_clamp.set_tightening_threshold(1200)
        self.top_clamp.set_margin_top(24)
        self.top_clamp.set_margin_start(12)
        self.top_clamp.set_margin_end(12)
        self.main_vbox.append(self.top_clamp)

        self.top_breakpoint_bin = Adw.BreakpointBin()
        self.top_breakpoint_bin.set_size_request(320, 50)
        self.top_clamp.set_child(self.top_breakpoint_bin)

        self.top_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.top_breakpoint_bin.set_child(self.top_hbox)

        self.device_list_box = Gtk.ListBox()
        self.device_list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self.device_list_box.add_css_class("boxed-list")
        self.device_list_box.set_hexpand(True)
        self.top_hbox.append(self.device_list_box)

        self.device_row = Adw.ActionRow(title="Device")
        self.device_list_box.append(self.device_row)

        self.device_model = Gtk.StringList()
        self.device_dropdown = Gtk.DropDown(model=self.device_model)
        self.device_dropdown.set_valign(Gtk.Align.CENTER)
        self.device_dropdown.connect("notify::selected", self.on_device_selected)
        self.device_row.add_suffix(self.device_dropdown)

        self.refresh_button = Gtk.Button(icon_name="view-refresh-symbolic")
        self.refresh_button.set_valign(Gtk.Align.CENTER)
        self.refresh_button.connect("clicked", self.on_refresh_clicked)
        self.device_row.add_suffix(self.refresh_button)

        # Scale Row inside boxed-list
        self.scale_row = Adw.ActionRow(title="Display Scale")
        self.device_list_box.append(self.scale_row)

        self.scale_control = ScaleControl()
        self.scale_box = self.scale_control
        self.btn_zoom_out = self.scale_control.btn_zoom_out
        self.btn_zoom_reset = self.scale_control.btn_zoom_reset
        self.btn_zoom_in = self.scale_control.btn_zoom_in
        self.scale_row.add_suffix(self.scale_control)

        # Top action buttons container
        self.top_buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.top_buttons_box.set_valign(Gtk.Align.CENTER)
        self.top_hbox.append(self.top_buttons_box)

        self.stream_button = Gtk.Button()
        self.stream_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.stream_icon = Gtk.Image.new_from_icon_name("media-playback-start-symbolic")
        self.stream_label = Gtk.Label(label="STREAM")
        self.stream_box.append(self.stream_icon)
        self.stream_box.append(self.stream_label)
        self.stream_button.set_child(self.stream_box)
        self.stream_button.add_css_class("pill")
        self.stream_button.add_css_class("suggested-action")
        self.stream_button.add_css_class("stream-btn")
        self.stream_button.set_valign(Gtk.Align.CENTER)
        self.stream_button.set_hexpand(True)
        self.stream_button.connect("clicked", self.on_play_clicked)
        self.top_buttons_box.append(self.stream_button)

        self.connect_mk_button = Gtk.Button()
        self.mk_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.mk_icon = Gtk.Image.new_from_icon_name("input-keyboard-symbolic")
        self.mk_label = Gtk.Label(label="Connect M/K")
        self.mk_box.append(self.mk_icon)
        self.mk_box.append(self.mk_label)
        self.connect_mk_button.set_child(self.mk_box)
        self.connect_mk_button.add_css_class("pill")
        self.connect_mk_button.add_css_class("mk-btn")
        self.connect_mk_button.set_valign(Gtk.Align.CENTER)
        self.connect_mk_button.set_hexpand(True)
        self.connect_mk_button.set_tooltip_text("Send Mouse and Keyboard without streaming video")
        self.connect_mk_button.connect("clicked", self.on_connect_mk_clicked)
        self.top_buttons_box.append(self.connect_mk_button)

        # Responsive breakpoint: stack vertically on narrow screens
        top_bp = Adw.Breakpoint.new(Adw.BreakpointCondition.parse("max-width: 750px"))
        top_bp.add_setter(self.top_hbox, "orientation", Gtk.Orientation.VERTICAL)
        top_bp.add_setter(self.top_buttons_box, "homogeneous", True)
        self.top_breakpoint_bin.add_breakpoint(top_bp)

    def on_zoom_in_clicked(self, button):
        self.scale_control.on_zoom_in_clicked(button)

    def on_zoom_out_clicked(self, button):
        self.scale_control.on_zoom_out_clicked(button)

    def on_zoom_reset_clicked(self, button):
        self.scale_control.on_zoom_reset_clicked(button)

    def apply_ui_scale(self, scale: float):
        self.scale_control.apply_scale(scale)

    def setup_split_view(self):
        self.split_clamp = Adw.Clamp()
        self.split_clamp.set_maximum_size(1920)
        self.split_clamp.set_hexpand(True)
        self.split_clamp.set_vexpand(True)
        self.split_clamp.set_margin_bottom(24)
        self.split_clamp.set_margin_start(12)
        self.split_clamp.set_margin_end(12)
        self.main_vbox.append(self.split_clamp)

        self.scrolled_window = Gtk.ScrolledWindow()
        self.scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scrolled_window.set_hexpand(True)
        self.scrolled_window.set_vexpand(True)
        self.split_clamp.set_child(self.scrolled_window)

        # Adaptive reflowing card container (Desktop 3 cols -> Tablet 2 cols -> Mobile 1 col)
        self.card_flow = Gtk.FlowBox()
        self.card_flow.set_selection_mode(Gtk.SelectionMode.NONE)
        self.card_flow.set_homogeneous(False)
        self.card_flow.set_column_spacing(24)
        self.card_flow.set_row_spacing(24)
        self.card_flow.set_min_children_per_line(1)
        self.card_flow.set_max_children_per_line(3)
        self.card_flow.set_hexpand(True)
        self.card_flow.set_vexpand(True)
        self.card_flow.set_valign(Gtk.Align.START)
        self.card_flow.set_halign(Gtk.Align.FILL)
        self.scrolled_window.set_child(self.card_flow)

        self.split_hbox = self.card_flow  # Backward compatibility alias

        self.stream_card = StreamCard()
        self.advanced_card = AdvancedCard()
        self.details_card = DetailsCard()

        for card in [self.stream_card, self.advanced_card, self.details_card]:
            card.set_hexpand(True)
            card.set_halign(Gtk.Align.FILL)
            self.card_flow.append(card)

        for i in range(3):
            child = self.card_flow.get_child_at_index(i)
            if child:
                child.set_focusable(False)
                child.set_hexpand(True)
                child.set_halign(Gtk.Align.FILL)

        self.stream_card.type_change_callback = self.advanced_card.set_camera_mode
        self.advanced_card.set_camera_mode(self.stream_card.type_dropdown.get_selected() == 1)

    def on_close_request(self, window):
        inhibit_service.uninhibit()
        if hasattr(self, 'stream_card') and hasattr(self.stream_card, 'stop_monitor_event'):
            self.stream_card.stop_monitor_event.set()
        self.process_manager.stop()
        return False

    def refresh_devices(self):
        n_items = self.device_model.get_n_items()
        self.device_model.splice(0, n_items, ["Scanning for devices..."])
        self.device_dropdown.set_sensitive(False)
        self.refresh_button.set_sensitive(False)
        self.stream_button.set_sensitive(False)
        self.connect_mk_button.set_sensitive(False)

        def fetch():
            devices = get_connected_devices()
            GLib.idle_add(self.apply_devices, devices)
        threading.Thread(target=fetch, daemon=True).start()

    def apply_devices(self, devices):
        self.devices = devices
        n_items = self.device_model.get_n_items()
        self.device_model.splice(0, n_items, [])
        self.refresh_button.set_sensitive(True)
        if not self.devices:
            self.device_model.append("No devices found")
            self.device_dropdown.set_sensitive(False)
            self.stream_button.set_sensitive(False)
            self.connect_mk_button.set_sensitive(False)
            self.on_device_selected(self.device_dropdown, None)
        else:
            for dev in self.devices:
                self.device_model.append(dev['display_name'])
            self.device_dropdown.set_sensitive(True)
            self.device_dropdown.set_selected(0)
            self.stream_button.set_sensitive(True)
            self.connect_mk_button.set_sensitive(True)
        if hasattr(self, "layout_manager"):
            self.layout_manager.on_device_selected(self.devices[0] if self.devices else None)
        return False

    def on_device_selected(self, dropdown, pspec):
        index = dropdown.get_selected()
        serial = self.devices[index]['serial'] if 0 <= index < len(self.devices) else None
        self.details_card.update_details(serial)
        self.stream_card.update_displays(serial)
        if hasattr(self, "layout_manager"):
            dev_info = self.devices[index] if 0 <= index < len(self.devices) else None
            self.layout_manager.on_device_selected(dev_info)

    def on_play_clicked(self, button=None):
        if self.process_manager.is_running:
            self.process_manager.stop()
            return
        index = self.device_dropdown.get_selected()
        if index == Gtk.INVALID_LIST_POSITION or not self.devices:
            return
        serial = self.devices[index]['serial']
        active_layout = getattr(self, "layout_manager", None) and self.layout_manager.get_active_layout()
        if active_layout and hasattr(active_layout, "get_stream_options") and self.layout_manager.get_active_layout_id() != LAYOUT_CLASSIC:
            options = active_layout.get_stream_options()
        else:
            options = self.stream_card.get_stream_options() + self.advanced_card.get_stream_options()
        self.launch_scrcpy(serial, options, mode="stream")

    def on_connect_mk_clicked(self, button):
        if self.process_manager.is_running:
            self.process_manager.stop()
            return
        index = self.device_dropdown.get_selected()
        if index == Gtk.INVALID_LIST_POSITION or not self.devices:
            return
        serial = self.devices[index]['serial']
        options = ["--max-size=300", "--fullscreen", "--no-audio"] + self.advanced_card.get_stream_options()
        self.launch_scrcpy(serial, options, mode="mk")

    def launch_scrcpy(self, serial: str, options: List[str], mode: str = "stream"):
        active_layout = getattr(self, "layout_manager", None) and self.layout_manager.get_active_layout()
        if active_layout and hasattr(active_layout, "get_environment_overrides") and self.layout_manager.get_active_layout_id() != LAYOUT_CLASSIC:
            env_overrides = active_layout.get_environment_overrides()
        else:
            env_overrides = self.advanced_card.get_environment_overrides()
        self.set_stream_state(True, mode)

        def on_exit(exit_code: int, error_msg: str, is_intentional: bool):
            is_normal = is_intentional or exit_code in (0, -15, 143, -2)
            if not is_normal:
                msg = error_msg or f"Process exited with code {exit_code}"
                GLib.idle_add(self.show_error_dialog, "scrcpy Error", msg)
            GLib.idle_add(self.set_stream_state, False)

        success = self.process_manager.launch(
            serial=serial,
            options=options,
            env_overrides=env_overrides,
            mode=mode,
            on_exit_callback=on_exit
        )
        if not success:
            self.show_error_dialog("Failed to Launch scrcpy", self.process_manager.error_output)
            self.set_stream_state(False)

    def on_process_exit(self, pid: int, status: int):
        exit_code = os.waitstatus_to_exitcode(status)
        is_normal = self.process_manager.is_stopping_intentionally or exit_code in (0, -15, 143, -2)
        if not is_normal:
            err = self.process_manager.error_output.strip() or f"Process exited with code {exit_code}"
            GLib.idle_add(self.show_error_dialog, "scrcpy Error", err)
        self.process_manager.is_stopping_intentionally = False
        self.process_manager.process = None
        self.set_stream_state(False)

    def show_error_dialog(self, title: str, message: str):
        show_error_dialog(self, title, message)

    def set_stream_state(self, active: bool, mode: str = "stream"):
        if hasattr(self, "layout_manager"):
            self.layout_manager.on_stream_state_changed(active, mode)
        if active:
            inhibit_service.inhibit(self, "Mirroring Android Display")
            if mode == "stream":
                self.stream_label.set_text("STOP")
                self.stream_icon.set_from_icon_name("media-playback-stop-symbolic")
                self.stream_button.remove_css_class("stream-btn")
                self.stream_button.add_css_class("stop-btn")
                self.stream_button.remove_css_class("suggested-action")
                self.stream_button.add_css_class("destructive-action")
                self.connect_mk_button.set_sensitive(False)
            else:
                self.mk_label.set_text("DISCONNECT")
                self.mk_icon.set_from_icon_name("media-playback-stop-symbolic")
                self.connect_mk_button.add_css_class("stop-btn")
                self.connect_mk_button.add_css_class("destructive-action")
                self.stream_button.set_sensitive(False)

            self.stream_card.set_sensitive(False)
            self.advanced_card.set_sensitive(False)
            self.device_dropdown.set_sensitive(False)
            self.refresh_button.set_sensitive(False)
        else:
            inhibit_service.uninhibit()
            self.stream_label.set_text("STREAM")
            self.stream_icon.set_from_icon_name("media-playback-start-symbolic")
            self.stream_button.remove_css_class("stop-btn")
            self.stream_button.add_css_class("stream-btn")
            self.stream_button.remove_css_class("destructive-action")
            self.stream_button.add_css_class("suggested-action")
            self.stream_button.set_sensitive(True)

            self.mk_label.set_text("Connect M/K")
            self.mk_icon.set_from_icon_name("input-keyboard-symbolic")
            self.connect_mk_button.remove_css_class("stop-btn")
            self.connect_mk_button.remove_css_class("destructive-action")
            self.connect_mk_button.set_sensitive(True)

            self.stream_card.set_sensitive(True)
            self.advanced_card.set_sensitive(True)
            self.device_dropdown.set_sensitive(True)
            self.refresh_button.set_sensitive(True)
            self.process_manager.process = None

    def on_refresh_clicked(self, button):
        self.refresh_devices()

    def _update_theme_classes(self):
        if self.style_manager.get_dark():
            self.add_css_class("dark-theme")
            self.remove_css_class("light-theme")
        else:
            self.add_css_class("light-theme")
            self.remove_css_class("dark-theme")

    def apply_saved_theme(self):
        theme = get_setting("theme", "default")
        if theme == "dark":
            self.style_manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
        elif theme == "light":
            self.style_manager.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
        else:
            self.style_manager.set_color_scheme(Adw.ColorScheme.DEFAULT)
        self._update_theme_classes()

    def on_theme_toggled(self):
        if self.style_manager.get_dark():
            self.style_manager.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
            set_setting("theme", "light")
        else:
            self.style_manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
            set_setting("theme", "dark")
        self._update_theme_classes()
        self.header_bar.update_theme_icon()

    def refresh_profiles(self, select_name: Optional[str] = None):
        self.header_bar.set_profiles(list_profiles(), select_name)
        active_layout = getattr(self, "layout_manager", None) and self.layout_manager.get_active_layout()
        if active_layout and hasattr(active_layout, "refresh_profiles"):
            try:
                active_layout.refresh_profiles()
            except Exception:
                pass

    def on_profile_selected(self, dropdown, pspec):
        idx = dropdown.get_selected()
        if idx == 0:
            return
        name = self.header_bar.get_profile_name(idx)
        state = load_profile(name)
        if state:
            if "stream" in state:
                self.stream_card.set_state(state["stream"])
            if "advanced" in state:
                self.advanced_card.set_state(state["advanced"])

    def on_save_profile_clicked(self):
        dialog = Adw.MessageDialog(transient_for=self, heading="Save Profile", body="Enter a name for this profile:")
        entry = Gtk.Entry()
        entry.set_placeholder_text("Profile Name")
        entry.set_margin_start(12)
        entry.set_margin_end(12)
        dialog.set_extra_child(entry)
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("save", "Save")
        dialog.set_response_appearance("save", Adw.ResponseAppearance.SUGGESTED)

        def on_response(d, response):
            if response == "save":
                name = entry.get_text().strip()
                if name:
                    state = {
                        "stream": self.stream_card.get_state(),
                        "advanced": self.advanced_card.get_state()
                    }
                    save_profile(name, state)
                    self.refresh_profiles(select_name=name)
            d.destroy()

        dialog.connect("response", on_response)
        dialog.present()

    def on_settings_clicked(self):
        dialog = SettingsDialog(self, self.refresh_profiles)
        dialog.present()

    def _on_application_set(self, window, pspec):
        app = self.get_application()
        if app:
            notification_service.set_application(app)
            inhibit_service.set_application(app)

    def on_about_clicked(self):
        show_about_dialog(self)

    def on_key_pressed(self, controller, keyval, keycode, state):
        modifiers = state & Gtk.accelerator_get_default_mod_mask()
        if modifiers == Gdk.ModifierType.CONTROL_MASK:
            if keyval == Gdk.KEY_q:
                self.close()
                return True
            elif keyval == Gdk.KEY_s:
                self.on_save_profile_clicked()
                return True
            elif keyval == Gdk.KEY_r:
                self.on_refresh_clicked(self.refresh_button)
                return True
            elif keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
                self.on_play_clicked(self.stream_button)
                return True
            elif keyval == Gdk.KEY_comma:
                self.on_settings_clicked()
                return True
        elif keyval == Gdk.KEY_F1:
            self.on_about_clicked()
            return True
        return False
