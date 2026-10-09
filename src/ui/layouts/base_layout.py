"""Base layout class for Andy's modular layout system.

Provides the abstract base class BaseLayout that all custom UI layouts must implement.
Adheres to composition over inheritance, providing a root GTK widget alongside
lifecycle and synchronization hooks.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw


class BaseLayout(ABC):
    """Abstract base class for all Andy UI layouts.

    Subclasses represent distinct layout configurations (e.g. Classic,
    Workstation, Studio, Inspector, Modular Hub, Action Assistant) that
    organize cards, controls, and workflows.

    Attributes:
        window: Reference to the parent AndyWindow instance.
    """

    def __init__(self, window: Any = None) -> None:
        """Initialize the layout with a reference to the main window.

        Args:
            window: The parent AndyWindow instance.
        """
        self.window = window

    @abstractmethod
    def get_widget(self) -> Gtk.Widget:
        """Return the top-level container widget for this layout.

        Returns:
            Gtk.Widget: The root widget to be placed inside the view stack or window.
        """
        pass

    def on_device_selected(self, device_info: Optional[Any]) -> None:
        """Lifecycle hook invoked when a device is selected or disconnected.

        Args:
            device_info: Dictionary containing device properties (e.g., 'serial',
                         'model', 'display_name'), device serial string, or None.
        """
        pass

    def on_stream_state_changed(self, active: bool, mode: str = "stream") -> None:
        """Lifecycle hook invoked when streaming begins or stops.

        Args:
            active: True if scrcpy stream/session is currently active, False otherwise.
            mode: Streaming mode ('stream' for full video or 'mk' for mouse/keyboard bridge).
        """
        self.set_stream_state(active, mode=mode)

    def set_stream_state(self, active: bool, mode: str = "stream") -> None:
        """Reflect whether scrcpy or M/K mode is running.

        Args:
            active: True if scrcpy stream/session is currently active, False otherwise.
            mode: Streaming mode ('stream' or 'mk').
        """
        pass

    def sync_from_window(self) -> None:
        """Synchronize this layout's UI controls with the parent window state.

        Called when activating the layout to ensure its controls reflect current
        application state (e.g., selected device, profiles, stream settings).
        """
        pass

    def sync_to_window(self) -> None:
        """Synchronize the parent window's state from this layout's controls.

        Called when user updates parameters within the layout that affect window-level
        state or persistent settings.
        """
        pass

    def update_devices(self, devices: List[Dict[str, Any]]) -> None:
        """Update layout with newly enumerated devices.

        Args:
            devices: List of connected device information dictionaries.
        """
        pass

    def refresh_profiles(self, select_name: Optional[str] = None) -> None:
        """Refresh profile listings.

        Args:
            select_name: Optional profile name to select after refresh.
        """
        pass

    def get_stream_options(self) -> List[str]:
        """Aggregate scrcpy CLI flags from layout settings.

        Returns:
            List[str]: List of CLI arguments.
        """
        return []

    def get_environment_overrides(self) -> Dict[str, str]:
        """Aggregate environment variable overrides.

        Returns:
            Dict[str, str]: Dictionary of environment variable key-value pairs.
        """
        return {}

    def get_state(self) -> Dict[str, Any]:
        """Serialize layout state for profile saving.

        Returns:
            Dict[str, Any]: State dictionary.
        """
        return {}

    def set_state(self, state: Dict[str, Any]) -> None:
        """Restore layout state from profile.

        Args:
            state: State dictionary to restore.
        """
        pass
