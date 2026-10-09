"""Placeholder and preview layout implementation for Andy."""

from typing import Any, Optional
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

from ui.layouts.base_layout import BaseLayout
from ui.layouts.layout_manager import LAYOUT_METADATA


class PlaceholderLayout(BaseLayout):
    """
    Placeholder and preview layout for designs pending dedicated implementation.
    Presents an Adw.StatusPage with metadata and quick return action.
    """

    def __init__(self, window: Any = None, layout_id: str = "workstation") -> None:
        super().__init__(window)
        self.layout_id = layout_id
        self._container: Optional[Gtk.Widget] = None

    def get_widget(self) -> Gtk.Widget:
        if self._container is not None:
            return self._container

        meta = LAYOUT_METADATA.get(self.layout_id, {})
        title = meta.get("name", self.layout_id.replace("_", " ").title())
        icon = meta.get("icon", "video-display-symbolic")
        desc = meta.get("description", f"{title} UI layout for Andy.")

        clamp = Adw.Clamp()
        clamp.set_maximum_size(800)
        clamp.set_vexpand(True)
        clamp.set_hexpand(True)
        clamp.set_margin_top(24)
        clamp.set_margin_bottom(24)
        clamp.set_margin_start(16)
        clamp.set_margin_end(16)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        box.set_valign(Gtk.Align.CENTER)
        clamp.set_child(box)

        status = Adw.StatusPage()
        status.set_icon_name(icon)
        status.set_title(title)
        status.set_description(desc)

        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        action_box.set_halign(Gtk.Align.CENTER)

        btn_classic = Gtk.Button(label="Switch to Classic Cards")
        btn_classic.add_css_class("pill")
        btn_classic.add_css_class("suggested-action")
        btn_classic.connect(
            "clicked",
            lambda b: self.window.switch_layout("classic") if self.window else None,
        )
        action_box.append(btn_classic)

        status.set_child(action_box)
        box.append(status)

        self._container = clamp
        return self._container
