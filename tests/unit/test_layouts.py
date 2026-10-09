"""Unit tests for BaseLayout and LayoutManager."""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

import pytest
from typing import Optional, Dict, Any
from unittest.mock import MagicMock

from ui.layouts.base_layout import BaseLayout
from ui.layouts.layout_manager import (
    LayoutManager,
    LAYOUT_CLASSIC,
    LAYOUT_WORKSTATION,
    LAYOUT_STUDIO,
    LAYOUT_INSPECTOR,
    LAYOUT_MODULAR_HUB,
    LAYOUT_ACTION_ASSISTANT,
    LAYOUT_ORDER,
    LAYOUT_METADATA,
)


class DummyLayout(BaseLayout):
    """Concrete implementation of BaseLayout for testing."""

    def __init__(self, window: Any = None) -> None:
        super().__init__(window)
        self.box = Gtk.Box()
        self.device_selected_calls = []
        self.stream_state_calls = []
        self.sync_from_window_count = 0
        self.sync_to_window_count = 0

    def get_widget(self) -> Gtk.Widget:
        return self.box

    def on_device_selected(self, device_info: Optional[Dict[str, Any]]) -> None:
        self.device_selected_calls.append(device_info)

    def on_stream_state_changed(self, active: bool, mode: str = "stream") -> None:
        self.stream_state_calls.append((active, mode))

    def sync_from_window(self) -> None:
        self.sync_from_window_count += 1

    def sync_to_window(self) -> None:
        self.sync_to_window_count += 1


class MinimalLayout(BaseLayout):
    """Minimal implementation relying on default hooks."""

    def __init__(self, window: Any = None) -> None:
        super().__init__(window)
        self.box = Gtk.Box()

    def get_widget(self) -> Gtk.Widget:
        return self.box


class TestBaseLayout:
    """Test suite for BaseLayout abstract base class."""

    def test_cannot_instantiate_abstract_class(self):
        with pytest.raises(TypeError):
            BaseLayout(None)

    def test_subclass_defaults(self):
        layout = MinimalLayout(None)
        assert layout.get_widget() is not None
        # Default hooks must execute without raising exceptions
        layout.on_device_selected({"serial": "1234"})
        layout.on_device_selected(None)
        layout.on_stream_state_changed(True, mode="stream")
        layout.on_stream_state_changed(False, mode="mk")
        layout.sync_from_window()
        layout.sync_to_window()


class TestLayoutManagerMetadata:
    """Test suite for layout constants, ordering, and metadata."""

    def test_constants_values(self):
        assert LAYOUT_CLASSIC == "classic"
        assert LAYOUT_WORKSTATION == "workstation"
        assert LAYOUT_STUDIO == "studio"
        assert LAYOUT_INSPECTOR == "inspector"
        assert LAYOUT_MODULAR_HUB == "modular_hub"
        assert LAYOUT_ACTION_ASSISTANT == "action_assistant"

    def test_layout_order(self):
        assert LAYOUT_ORDER == [
            "classic",
            "workstation",
            "studio",
            "inspector",
            "modular_hub",
            "action_assistant",
        ]

    def test_layout_metadata_keys_and_fields(self):
        for layout_id in LAYOUT_ORDER:
            assert layout_id in LAYOUT_METADATA
            meta = LAYOUT_METADATA[layout_id]
            assert "name" in meta and isinstance(meta["name"], str)
            assert "icon" in meta and isinstance(meta["icon"], str)
            assert "description" in meta and isinstance(meta["description"], str)


class TestLayoutManagerFunctionality:
    """Test suite for LayoutManager logic and lifecycle delegation."""

    def test_register_and_lazy_instantiation(self):
        manager = LayoutManager(window=None, view_stack=None)
        manager.register_layout(LAYOUT_CLASSIC, DummyLayout)

        # Before calling get_layout, not yet instantiated
        assert LAYOUT_CLASSIC not in manager._instances

        layout1 = manager.get_layout(LAYOUT_CLASSIC)
        assert isinstance(layout1, DummyLayout)
        assert layout1.window is None
        assert LAYOUT_CLASSIC in manager._instances

        # Second retrieval returns cached instance
        layout2 = manager.get_layout(LAYOUT_CLASSIC)
        assert layout1 is layout2

    def test_register_instance_directly(self):
        manager = LayoutManager(window=None, view_stack=None)
        existing_layout = DummyLayout(window=None)
        manager.register_layout(LAYOUT_STUDIO, existing_layout)

        assert manager.get_layout(LAYOUT_STUDIO) is existing_layout

    def test_unknown_layout_raises_key_error(self):
        manager = LayoutManager(window=None, view_stack=None)
        with pytest.raises(KeyError):
            manager.get_layout("nonexistent_layout")

    def test_switch_to_layout(self):
        manager = LayoutManager(window=None, view_stack=None)
        manager.register_layout(LAYOUT_WORKSTATION, DummyLayout)

        assert manager.get_active_layout_id() == ""
        assert manager.get_active_layout() is None

        layout = manager.switch_to_layout(LAYOUT_WORKSTATION)
        assert isinstance(layout, DummyLayout)
        assert manager.get_active_layout_id() == LAYOUT_WORKSTATION
        assert manager.get_active_layout() is layout
        # Should have called sync_from_window
        assert layout.sync_from_window_count == 1

    def test_device_selection_delegation(self):
        manager = LayoutManager(window=None, view_stack=None)
        manager.register_layout(LAYOUT_CLASSIC, DummyLayout)

        # Event before active layout doesn't crash
        manager.on_device_selected({"serial": "111", "model": "Pixel"})

        # Switch to layout should receive previously selected device
        layout = manager.switch_to_layout(LAYOUT_CLASSIC)
        assert len(layout.device_selected_calls) == 1
        assert layout.device_selected_calls[0] == {"serial": "111", "model": "Pixel"}

        # Subsequent device selection notifies active layout
        manager.on_device_selected({"serial": "222", "model": "Galaxy"})
        assert len(layout.device_selected_calls) == 2
        assert layout.device_selected_calls[1] == {"serial": "222", "model": "Galaxy"}

    def test_stream_state_changed_delegation(self):
        manager = LayoutManager(window=None, view_stack=None)
        manager.register_layout(LAYOUT_STUDIO, DummyLayout)

        manager.on_stream_state_changed(True, mode="mk")
        layout = manager.switch_to_layout(LAYOUT_STUDIO)

        # Caught current state upon activation
        assert (True, "mk") in layout.stream_state_calls

        # Direct event
        manager.on_stream_state_changed(False, mode="stream")
        assert (False, "stream") in layout.stream_state_calls

    def test_with_adw_view_stack(self):
        Adw.init()
        stack = Adw.ViewStack()
        mock_window = MagicMock()

        manager = LayoutManager(window=mock_window, view_stack=stack)
        manager.register_layout(LAYOUT_CLASSIC, DummyLayout)
        manager.register_layout(LAYOUT_INSPECTOR, DummyLayout)

        # Switch to Classic
        classic = manager.switch_to_layout(LAYOUT_CLASSIC)
        assert stack.get_visible_child_name() == LAYOUT_CLASSIC
        assert stack.get_child_by_name(LAYOUT_CLASSIC) == classic.get_widget()

        # Switch to Inspector
        inspector = manager.switch_to_layout(LAYOUT_INSPECTOR)
        assert stack.get_visible_child_name() == LAYOUT_INSPECTOR
        assert stack.get_child_by_name(LAYOUT_INSPECTOR) == inspector.get_widget()
        assert manager.get_active_layout_id() == LAYOUT_INSPECTOR
        assert manager.get_active_layout() is inspector

        # External change to visible child
        stack.set_visible_child_name(LAYOUT_CLASSIC)
        assert manager.get_active_layout_id() == LAYOUT_CLASSIC
        assert manager.get_active_layout() is classic
