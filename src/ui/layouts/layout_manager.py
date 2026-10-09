"""Layout manager for Andy's modular layout system.

Coordinates available layout definitions, lazy initialization, view stack switching,
and event delegation across layouts.
"""

from typing import Any, Callable, Dict, List, Optional, Type, Union
from gi.repository import Gtk, Adw

from ui.layouts.base_layout import BaseLayout

# Layout Identifiers
LAYOUT_CLASSIC = "classic"
LAYOUT_WORKSTATION = "workstation"
LAYOUT_STUDIO = "studio"
LAYOUT_INSPECTOR = "inspector"
LAYOUT_MODULAR_HUB = "modular_hub"
LAYOUT_ACTION_ASSISTANT = "action_assistant"

# Standard layout order
LAYOUT_ORDER: List[str] = [
    LAYOUT_CLASSIC,
    LAYOUT_WORKSTATION,
    LAYOUT_STUDIO,
    LAYOUT_INSPECTOR,
    LAYOUT_MODULAR_HUB,
    LAYOUT_ACTION_ASSISTANT,
]

# Layout metadata with human-readable names, icons, and descriptions
LAYOUT_METADATA: Dict[str, Dict[str, str]] = {
    LAYOUT_CLASSIC: {
        "name": "Classic",
        "icon": "view-column-symbolic",
        "description": "Standard 3-column control view with Stream, Advanced, and Details cards",
    },
    LAYOUT_WORKSTATION: {
        "name": "Workstation",
        "icon": "video-display-symbolic",
        "description": "Productivity-focused workspace layout with quick tools and multi-window access",
    },
    LAYOUT_STUDIO: {
        "name": "Studio",
        "icon": "camera-video-symbolic",
        "description": "Media capture, camera streaming, and recording studio configuration",
    },
    LAYOUT_INSPECTOR: {
        "name": "Inspector",
        "icon": "system-search-symbolic",
        "description": "In-depth device diagnostics, system metrics, and real-time logs",
    },
    LAYOUT_MODULAR_HUB: {
        "name": "Modular Hub",
        "icon": "view-grid-symbolic",
        "description": "Customizable dashboard layout with flexible, reconfigurable widget cards",
    },
    LAYOUT_ACTION_ASSISTANT: {
        "name": "Action Assistant",
        "icon": "input-keyboard-symbolic",
        "description": "Rapid device automation, macros, shortcuts, and input assistant mode",
    },
}


class LayoutManager:
    """Manages available UI layouts for Andy.

    Handles lazy instantiation of layout instances, registration of layout factories,
    binding to Adw.ViewStack, switching active views, and delegating device/stream events.
    """

    def __init__(self, window: Any, view_stack: Optional[Adw.ViewStack] = None) -> None:
        """Initialize the LayoutManager.

        Args:
            window: Parent AndyWindow instance.
            view_stack: Adw.ViewStack instance used to display active layout widgets.
        """
        self.window = window
        self.view_stack = view_stack
        self._registry: Dict[str, Callable[..., BaseLayout]] = {}
        self._instances: Dict[str, BaseLayout] = {}
        self._active_layout_id: str = ""
        self._current_device_info: Optional[dict] = None
        self._stream_active: bool = False
        self._stream_mode: str = "stream"

        if self.view_stack is not None and hasattr(self.view_stack, "connect"):
            self.view_stack.connect(
                "notify::visible-child-name", self._on_visible_child_name_changed
            )

    def register_layout(
        self,
        layout_id: str,
        layout_factory: Union[Type[BaseLayout], Callable[..., BaseLayout], BaseLayout],
    ) -> None:
        """Register a layout factory or instance for a layout ID.

        Args:
            layout_id: Unique string identifier for the layout.
            layout_factory: Subclass of BaseLayout, a callable factory producing a BaseLayout,
                            or an existing BaseLayout instance.
        """
        if isinstance(layout_factory, BaseLayout):
            self._instances[layout_id] = layout_factory
            if self.view_stack is not None:
                self._add_to_view_stack(layout_id, layout_factory)
        else:
            self._registry[layout_id] = layout_factory

    def get_layout(self, layout_id: str) -> BaseLayout:
        """Get or lazily instantiate a layout by its ID.

        If the layout has not been created yet, it is instantiated using its
        registered factory, cached, and attached to the view stack.

        Args:
            layout_id: Unique identifier for the layout.

        Returns:
            BaseLayout: The instantiated layout instance.

        Raises:
            KeyError: If layout_id is not registered or already created.
            TypeError: If the registered factory cannot be invoked.
        """
        if layout_id in self._instances:
            return self._instances[layout_id]

        if layout_id not in self._registry:
            raise KeyError(f"Layout '{layout_id}' is not registered.")

        factory = self._registry[layout_id]
        if isinstance(factory, type) and issubclass(factory, BaseLayout):
            layout = factory(self.window)
        elif callable(factory):
            try:
                layout = factory(self.window)
            except TypeError:
                layout = factory()
        else:
            raise TypeError(
                f"Registered layout factory for '{layout_id}' is neither a BaseLayout subclass nor callable."
            )

        self._instances[layout_id] = layout

        if self.view_stack is not None:
            self._add_to_view_stack(layout_id, layout)

        return layout

    def switch_to_layout(self, layout_id: str) -> BaseLayout:
        """Switch the active layout to the specified layout ID.

        Lazily instantiates the layout if needed, displays it in the view stack,
        synchronizes its state from the window, and notifies it of any current
        device or stream state.

        Args:
            layout_id: Unique identifier of the layout to switch to.

        Returns:
            BaseLayout: The activated layout instance.
        """
        layout = self.get_layout(layout_id)
        self._active_layout_id = layout_id

        if self.view_stack is not None and hasattr(self.view_stack, "get_visible_child_name"):
            if self.view_stack.get_visible_child_name() != layout_id:
                self.view_stack.set_visible_child_name(layout_id)

        # Synchronize layout with current window state
        layout.sync_from_window()
        if self._current_device_info is not None:
            layout.on_device_selected(self._current_device_info)
        if self._stream_active:
            layout.on_stream_state_changed(self._stream_active, mode=self._stream_mode)

        return layout

    def get_active_layout_id(self) -> str:
        """Get the ID of the currently active layout.

        Returns:
            str: Identifier of the active layout, or empty string if none active.
        """
        if self._active_layout_id:
            return self._active_layout_id
        if self.view_stack is not None and hasattr(self.view_stack, "get_visible_child_name"):
            visible = self.view_stack.get_visible_child_name()
            if visible:
                return visible
        return ""

    def get_active_layout(self) -> Optional[BaseLayout]:
        """Get the currently active BaseLayout instance.

        Returns:
            Optional[BaseLayout]: Active layout instance if available, otherwise None.
        """
        active_id = self.get_active_layout_id()
        if active_id and active_id in self._instances:
            return self._instances[active_id]
        return None

    def on_device_selected(self, device_info: Optional[dict]) -> None:
        """Delegate device selection change event to the active layout.

        Args:
            device_info: Device properties dictionary, or None if disconnected.
        """
        self._current_device_info = device_info
        active_layout = self.get_active_layout()
        if active_layout is not None:
            active_layout.on_device_selected(device_info)

    def on_stream_state_changed(self, active: bool, mode: str = "stream") -> None:
        """Delegate stream state change event to the active layout.

        Args:
            active: True if stream is running, False if stopped.
            mode: Operational mode ('stream' or 'mk').
        """
        self._stream_active = active
        self._stream_mode = mode
        active_layout = self.get_active_layout()
        if active_layout is not None:
            active_layout.on_stream_state_changed(active, mode=mode)

    def _add_to_view_stack(self, layout_id: str, layout: BaseLayout) -> None:
        """Helper to attach a layout's root widget to the Adw.ViewStack.

        Args:
            layout_id: Unique identifier for the layout.
            layout: The BaseLayout instance whose widget will be added.
        """
        if self.view_stack is None:
            return

        if hasattr(self.view_stack, "get_child_by_name") and self.view_stack.get_child_by_name(layout_id) is not None:
            return

        widget = layout.get_widget()
        if widget is None:
            return

        meta = LAYOUT_METADATA.get(layout_id, {})
        title = meta.get("name", layout_id)
        icon = meta.get("icon")

        if icon and hasattr(self.view_stack, "add_titled_with_icon"):
            self.view_stack.add_titled_with_icon(widget, layout_id, title, icon)
        elif title and hasattr(self.view_stack, "add_titled"):
            self.view_stack.add_titled(widget, layout_id, title)
        elif hasattr(self.view_stack, "add_named"):
            self.view_stack.add_named(widget, layout_id)

    def _on_visible_child_name_changed(self, stack: Any, pspec: Any) -> None:
        """Handle visible child changes from ViewStack (e.g. user toggles ViewSwitcher).

        Args:
            stack: The Adw.ViewStack instance.
            pspec: Property specification for visible-child-name.
        """
        name = stack.get_visible_child_name()
        if name and name != self._active_layout_id:
            self._active_layout_id = name
            if name in self._instances or name in self._registry:
                layout = self.get_layout(name)
                layout.sync_from_window()
                if self._current_device_info is not None:
                    layout.on_device_selected(self._current_device_info)
                if self._stream_active:
                    layout.on_stream_state_changed(self._stream_active, mode=self._stream_mode)
