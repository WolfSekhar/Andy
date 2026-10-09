"""Classic cards layout implementation for Andy.

The original Andy 3-card reflowing layout (StreamCard, AdvancedCard, DetailsCard)
wrapped as a standalone BaseLayout component that can also bind to an existing
AndyWindow instance for full backward compatibility.
"""

from typing import Any, Dict, List, Optional
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gio

from ui.layouts.base_layout import BaseLayout
from ui.common.scale_control import ScaleControl
from ui.cards.stream.stream_card import StreamCard
from ui.cards.advanced.advanced_card import AdvancedCard
from ui.cards.details.details_card import DetailsCard


class ClassicLayout(BaseLayout):
    """Classic Andy layout: top device selection bar + 3-column FlowBox card grid.

    Works standalone (window=None) or as a proxy to an existing AndyWindow.
    """

    def __init__(self, window: Any = None) -> None:
        super().__init__(window)
        self._root: Optional[Gtk.Widget] = None
        self._build()

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build(self) -> None:
        """Create all widgets, adopting window's existing widgets if already built."""
        if self.window is not None and hasattr(self.window, "main_vbox") and hasattr(self.window, "card_flow"):
            self._root = self.window.main_vbox
            self.card_flow = self.window.card_flow
            self.split_hbox = getattr(self.window, "split_hbox", self.card_flow)
            self.stream_card = self.window.stream_card
            self.advanced_card = self.window.advanced_card
            self.details_card = self.window.details_card
            self.device_model = getattr(self.window, "device_model", None) or Gtk.StringList()
            self.device_dropdown = self.window.device_dropdown
            self.refresh_button = self.window.refresh_button
            self.scale_control = self.window.scale_control
            self.stream_button = self.window.stream_button
            self.connect_mk_button = self.window.connect_mk_button
            self.stream_label = getattr(self.window, "stream_label", None)
            self.mk_label = getattr(self.window, "mk_label", None)
            self.stream_icon = getattr(self.window, "stream_icon", None)
            self.mk_icon = getattr(self.window, "mk_icon", None)
            self.top_breakpoint_bin = getattr(self.window, "top_breakpoint_bin", None)
            return

        self._root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._root.set_vexpand(True)
        self._root.set_hexpand(True)

        # ---- Top device selection row ----
        top_clamp = Adw.Clamp()
        top_clamp.set_maximum_size(1200)
        top_clamp.set_tightening_threshold(1200)
        top_clamp.set_margin_top(24)
        top_clamp.set_margin_start(12)
        top_clamp.set_margin_end(12)
        self._root.append(top_clamp)

        self.top_breakpoint_bin = Adw.BreakpointBin()
        self.top_breakpoint_bin.set_size_request(320, 50)
        top_clamp.set_child(self.top_breakpoint_bin)

        top_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.top_breakpoint_bin.set_child(top_hbox)

        # Device listbox
        device_list_box = Gtk.ListBox()
        device_list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        device_list_box.add_css_class("boxed-list")
        device_list_box.set_hexpand(True)
        top_hbox.append(device_list_box)

        device_row = Adw.ActionRow(title="Device")

        self.device_model = Gtk.StringList()
        self.device_dropdown = Gtk.DropDown(model=self.device_model)
        self.device_dropdown.set_valign(Gtk.Align.CENTER)
        self.device_dropdown.connect("notify::selected", self._on_device_selected)
        device_row.add_suffix(self.device_dropdown)

        self.refresh_button = Gtk.Button(icon_name="view-refresh-symbolic")
        self.refresh_button.set_valign(Gtk.Align.CENTER)
        self.refresh_button.connect("clicked", self._on_refresh_clicked)
        device_row.add_suffix(self.refresh_button)
        device_list_box.append(device_row)

        # Scale row
        scale_row = Adw.ActionRow(title="Display Scale")
        self.scale_control = ScaleControl()
        scale_row.add_suffix(self.scale_control)
        device_list_box.append(scale_row)

        # Action buttons
        top_buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        top_buttons_box.set_valign(Gtk.Align.CENTER)
        top_hbox.append(top_buttons_box)

        # Stream button
        self.stream_button = Gtk.Button()
        stream_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.stream_icon = Gtk.Image.new_from_icon_name("media-playback-start-symbolic")
        self.stream_label = Gtk.Label(label="STREAM")
        stream_box.append(self.stream_icon)
        stream_box.append(self.stream_label)
        self.stream_button.set_child(stream_box)
        self.stream_button.add_css_class("pill")
        self.stream_button.add_css_class("suggested-action")
        self.stream_button.add_css_class("stream-btn")
        self.stream_button.set_valign(Gtk.Align.CENTER)
        self.stream_button.set_hexpand(True)
        self.stream_button.connect("clicked", self._on_play_clicked)
        top_buttons_box.append(self.stream_button)

        # M/K button
        self.connect_mk_button = Gtk.Button()
        mk_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.mk_icon = Gtk.Image.new_from_icon_name("input-keyboard-symbolic")
        self.mk_label = Gtk.Label(label="Connect M/K")
        mk_box.append(self.mk_icon)
        mk_box.append(self.mk_label)
        self.connect_mk_button.set_child(mk_box)
        self.connect_mk_button.add_css_class("pill")
        self.connect_mk_button.add_css_class("mk-btn")
        self.connect_mk_button.set_valign(Gtk.Align.CENTER)
        self.connect_mk_button.set_hexpand(True)
        self.connect_mk_button.set_tooltip_text("Send Mouse and Keyboard without streaming video")
        self.connect_mk_button.connect("clicked", self._on_connect_mk_clicked)
        top_buttons_box.append(self.connect_mk_button)

        # Responsive breakpoint
        top_bp = Adw.Breakpoint.new(Adw.BreakpointCondition.parse("max-width: 750px"))
        top_bp.add_setter(top_hbox, "orientation", Gtk.Orientation.VERTICAL)
        top_bp.add_setter(top_buttons_box, "homogeneous", True)
        self.top_breakpoint_bin.add_breakpoint(top_bp)

        # ---- Scrollable card area ----
        split_clamp = Adw.Clamp()
        split_clamp.set_maximum_size(1920)
        split_clamp.set_hexpand(True)
        split_clamp.set_vexpand(True)
        split_clamp.set_margin_bottom(24)
        split_clamp.set_margin_start(12)
        split_clamp.set_margin_end(12)
        self._root.append(split_clamp)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_hexpand(True)
        scrolled_window.set_vexpand(True)
        split_clamp.set_child(scrolled_window)

        # Adaptive FlowBox
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
        scrolled_window.set_child(self.card_flow)

        self.split_hbox = self.card_flow  # backward compat alias

        # ---- Cards ----
        # Reuse existing window cards if present, otherwise create fresh ones
        if self.window is not None and isinstance(getattr(self.window, "stream_card", None), StreamCard):
            self.stream_card = self.window.stream_card
        else:
            self.stream_card = StreamCard()

        if self.window is not None and isinstance(getattr(self.window, "advanced_card", None), AdvancedCard):
            self.advanced_card = self.window.advanced_card
        else:
            self.advanced_card = AdvancedCard()

        if self.window is not None and isinstance(getattr(self.window, "details_card", None), DetailsCard):
            self.details_card = self.window.details_card
        else:
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

        # Camera mode link
        self.stream_card.type_change_callback = self.advanced_card.set_camera_mode
        self.advanced_card.set_camera_mode(self.stream_card.type_dropdown.get_selected() == 1)

        # Bind all references onto window if provided
        if self.window is not None:
            self.window.stream_card = self.stream_card
            self.window.advanced_card = self.advanced_card
            self.window.details_card = self.details_card
            self.window.card_flow = self.card_flow
            self.window.split_hbox = self.card_flow
            self.window.stream_button = self.stream_button
            self.window.connect_mk_button = self.connect_mk_button
            self.window.device_dropdown = self.device_dropdown
            self.window.stream_label = self.stream_label
            self.window.mk_label = self.mk_label
            self.window.stream_icon = self.stream_icon
            self.window.mk_icon = self.mk_icon
            self.window.scale_control = self.scale_control
            self.window.refresh_button = self.refresh_button

    # ------------------------------------------------------------------
    # BaseLayout interface
    # ------------------------------------------------------------------

    def get_widget(self) -> Gtk.Widget:
        return self._root

    def on_device_selected(self, device_info: Optional[Any] = None) -> None:
        serial = None
        if isinstance(device_info, dict):
            serial = device_info.get("serial")
        elif isinstance(device_info, str):
            serial = device_info
        self.details_card.update_details(serial)
        self.stream_card.update_displays(serial)

    def on_stream_state_changed(self, active: bool, mode: str = "stream") -> None:
        if active:
            if mode == "stream":
                self.stream_label.set_text("STOP")
                self.stream_icon.set_from_icon_name("media-playback-stop-symbolic")
                self.stream_button.remove_css_class("stream-btn")
                self.stream_button.remove_css_class("suggested-action")
                self.stream_button.add_css_class("stop-btn")
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

    def set_stream_state(self, active: bool, mode: str = "stream") -> None:
        """Alias that delegates to on_stream_state_changed."""
        self.on_stream_state_changed(active, mode=mode)

    def update_devices(self, devices: List[Dict[str, Any]]) -> None:
        n = self.device_model.get_n_items()
        self.device_model.splice(0, n, [])
        if not devices:
            self.device_model.append("No devices found")
            self.device_dropdown.set_sensitive(False)
            self.stream_button.set_sensitive(False)
            self.connect_mk_button.set_sensitive(False)
        else:
            for dev in devices:
                self.device_model.append(dev["display_name"])
            self.device_dropdown.set_sensitive(True)
            self.device_dropdown.set_selected(0)
            self.stream_button.set_sensitive(True)
            self.connect_mk_button.set_sensitive(True)

    def sync_from_window(self) -> None:
        pass

    def sync_to_window(self) -> None:
        pass

    def get_stream_options(self) -> List[str]:
        return (
            self.stream_card.get_stream_options()
            + self.advanced_card.get_stream_options()
        )

    def get_environment_overrides(self) -> Dict[str, str]:
        return self.advanced_card.get_environment_overrides()

    def get_state(self) -> Dict[str, Any]:
        return {
            "stream": self.stream_card.get_state(),
            "advanced": self.advanced_card.get_state(),
        }

    def set_state(self, state: Dict[str, Any]) -> None:
        if "stream" in state:
            self.stream_card.set_state(state["stream"])
        if "advanced" in state:
            self.advanced_card.set_state(state["advanced"])

    # ------------------------------------------------------------------
    # Private callbacks
    # ------------------------------------------------------------------

    def _on_device_selected(self, dropdown: Gtk.DropDown, pspec: Any) -> None:
        if self.window is not None and hasattr(self.window, "on_device_selected"):
            self.window.on_device_selected(dropdown, pspec)
        else:
            index = dropdown.get_selected()
            devices = getattr(self.window, "devices", []) if self.window else []
            serial = devices[index]["serial"] if 0 <= index < len(devices) else None
            self.on_device_selected({"serial": serial} if serial else None)

    def _on_refresh_clicked(self, button: Gtk.Button) -> None:
        if self.window is not None and hasattr(self.window, "on_refresh_clicked"):
            self.window.on_refresh_clicked(button)

    def _on_play_clicked(self, button: Gtk.Button) -> None:
        if self.window is not None and hasattr(self.window, "on_play_clicked"):
            self.window.on_play_clicked(button)

    def _on_connect_mk_clicked(self, button: Gtk.Button) -> None:
        if self.window is not None and hasattr(self.window, "on_connect_mk_clicked"):
            self.window.on_connect_mk_clicked(button)
