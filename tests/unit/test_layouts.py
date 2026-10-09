"""Unit tests for BaseLayout and ClassicLayout contract."""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

import pytest
from typing import Optional, Dict, Any

from ui.layouts.base_layout import BaseLayout
from ui.layouts.classic_layout import ClassicLayout
from ui.layouts import LAYOUT_CLASSIC


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

    def test_concrete_dummy_layout_delegation(self):
        layout = DummyLayout(None)
        layout.on_device_selected({"serial": "phone1"})
        assert layout.device_selected_calls == [{"serial": "phone1"}]

        layout.on_stream_state_changed(True, mode="stream")
        assert layout.stream_state_calls == [(True, "stream")]

        layout.sync_from_window()
        assert layout.sync_from_window_count == 1

        layout.sync_to_window()
        assert layout.sync_to_window_count == 1


class TestClassicLayoutContract:
    """Test suite for ClassicLayout adhering to BaseLayout."""

    def test_classic_layout_subclasses_base(self):
        assert issubclass(ClassicLayout, BaseLayout)
        assert LAYOUT_CLASSIC == "classic"

    def test_classic_layout_standalone_widget(self):
        layout = ClassicLayout(window=None)
        widget = layout.get_widget()
        assert isinstance(widget, Gtk.Widget)
        assert layout.stream_card is not None
        assert layout.advanced_card is not None
        assert layout.details_card is not None
