"""Unit tests for ClassicLayout."""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gio

import pytest
from unittest.mock import MagicMock, patch

from ui.layouts.base_layout import BaseLayout
from ui.layouts.classic_layout import ClassicLayout
from ui.cards.stream.stream_card import StreamCard
from ui.cards.advanced.advanced_card import AdvancedCard
from ui.cards.details.details_card import DetailsCard


class TestClassicLayout:
    @classmethod
    def setup_class(cls):
        try:
            Adw.init()
        except Exception:
            pass

    def test_inheritance(self):
        """ClassicLayout must inherit from BaseLayout."""
        assert issubclass(ClassicLayout, BaseLayout)

    def test_initialization_without_window(self):
        """ClassicLayout can be instantiated standalone without a window."""
        layout = ClassicLayout(window=None)

        widget = layout.get_widget()
        assert isinstance(widget, Gtk.Box)
        assert widget.get_orientation() == Gtk.Orientation.VERTICAL
        assert layout.card_flow is not None
        assert isinstance(layout.card_flow, Gtk.FlowBox)

        # Core 3 cards are present
        assert isinstance(layout.stream_card, StreamCard)
        assert isinstance(layout.advanced_card, AdvancedCard)
        assert isinstance(layout.details_card, DetailsCard)

        # Top controls
        assert isinstance(layout.top_breakpoint_bin, Adw.BreakpointBin)
        assert isinstance(layout.device_dropdown, Gtk.DropDown)
        assert isinstance(layout.refresh_button, Gtk.Button)
        assert isinstance(layout.stream_button, Gtk.Button)
        assert isinstance(layout.connect_mk_button, Gtk.Button)
        assert isinstance(layout.scale_control, Gtk.Widget)

        # Backward compatibility alias
        assert layout.split_hbox is layout.card_flow

    def test_initialization_with_window(self):
        """ClassicLayout binds references to the parent window."""
        mock_win = MagicMock()
        mock_win.stream_card = None
        mock_win.advanced_card = None
        mock_win.details_card = None
        mock_win.devices = []

        layout = ClassicLayout(window=mock_win)

        # References attached to mock_win
        assert mock_win.stream_card is layout.stream_card
        assert mock_win.advanced_card is layout.advanced_card
        assert mock_win.details_card is layout.details_card
        assert mock_win.card_flow is layout.card_flow
        assert mock_win.stream_button is layout.stream_button
        assert mock_win.connect_mk_button is layout.connect_mk_button
        assert mock_win.device_dropdown is layout.device_dropdown

    def test_reuses_existing_window_cards(self):
        """ClassicLayout reuses cards if already present on window."""
        mock_win = MagicMock()
        existing_stream = StreamCard()
        existing_adv = AdvancedCard()
        existing_det = DetailsCard()

        mock_win.stream_card = existing_stream
        mock_win.advanced_card = existing_adv
        mock_win.details_card = existing_det
        mock_win.devices = []

        layout = ClassicLayout(window=mock_win)

        assert layout.stream_card is existing_stream
        assert layout.advanced_card is existing_adv
        assert layout.details_card is existing_det

    def test_on_device_selected_updates_cards(self):
        """on_device_selected updates details_card and stream_card."""
        layout = ClassicLayout(window=None)

        with patch.object(layout.details_card, "update_details") as mock_details, \
             patch.object(layout.stream_card, "update_displays") as mock_displays:

            # Dict argument
            layout.on_device_selected({"serial": "device-123", "model": "Pixel"})
            mock_details.assert_called_with("device-123")
            mock_displays.assert_called_with("device-123")

            # String argument
            layout.on_device_selected("serial-456")
            mock_details.assert_called_with("serial-456")
            mock_displays.assert_called_with("serial-456")

            # None argument
            layout.on_device_selected(None)
            mock_details.assert_called_with(None)
            mock_displays.assert_called_with(None)

    def test_on_stream_state_changed_stream_mode(self):
        """on_stream_state_changed modifies UI controls for full video stream mode."""
        layout = ClassicLayout(window=None)

        # Active stream
        layout.on_stream_state_changed(True, mode="stream")
        assert layout.stream_label.get_text() == "STOP"
        assert layout.connect_mk_button.get_sensitive() is False
        assert layout.stream_card.get_sensitive() is False
        assert layout.advanced_card.get_sensitive() is False
        assert layout.device_dropdown.get_sensitive() is False
        assert layout.refresh_button.get_sensitive() is False

        # Inactive stream
        layout.on_stream_state_changed(False, mode="stream")
        assert layout.stream_label.get_text() == "STREAM"
        assert layout.connect_mk_button.get_sensitive() is True
        assert layout.stream_card.get_sensitive() is True
        assert layout.advanced_card.get_sensitive() is True
        assert layout.device_dropdown.get_sensitive() is True
        assert layout.refresh_button.get_sensitive() is True

    def test_on_stream_state_changed_mk_mode(self):
        """on_stream_state_changed modifies UI controls for Connect M/K mode."""
        layout = ClassicLayout(window=None)

        # Active M/K
        layout.on_stream_state_changed(True, mode="mk")
        assert layout.mk_label.get_text() == "DISCONNECT"
        assert layout.stream_button.get_sensitive() is False
        assert layout.stream_card.get_sensitive() is False
        assert layout.advanced_card.get_sensitive() is False

        # Inactive M/K
        layout.on_stream_state_changed(False, mode="mk")
        assert layout.mk_label.get_text() == "Connect M/K"
        assert layout.stream_button.get_sensitive() is True
        assert layout.stream_card.get_sensitive() is True
        assert layout.advanced_card.get_sensitive() is True

    def test_set_stream_state_alias(self):
        """set_stream_state delegates to on_stream_state_changed."""
        layout = ClassicLayout(window=None)
        with patch.object(layout, "on_stream_state_changed") as mock_changed:
            layout.set_stream_state(True, mode="stream")
            mock_changed.assert_called_once_with(True, mode="stream")

    def test_update_devices_empty_and_populated(self):
        """update_devices handles empty device list and populated device list."""
        layout = ClassicLayout(window=None)

        # Empty
        layout.update_devices([])
        assert layout.device_model.get_string(0) == "No devices found"
        assert layout.device_dropdown.get_sensitive() is False
        assert layout.stream_button.get_sensitive() is False
        assert layout.connect_mk_button.get_sensitive() is False

        # Populated
        devices = [
            {"serial": "dev1", "display_name": "Phone One (dev1)"},
            {"serial": "dev2", "display_name": "Tablet Two (dev2)"},
        ]
        layout.update_devices(devices)
        assert layout.device_model.get_n_items() == 2
        assert layout.device_model.get_string(0) == "Phone One (dev1)"
        assert layout.device_dropdown.get_sensitive() is True
        assert layout.stream_button.get_sensitive() is True
        assert layout.connect_mk_button.get_sensitive() is True

    def test_get_stream_options_and_overrides(self):
        """get_stream_options aggregates options from stream and advanced cards."""
        layout = ClassicLayout(window=None)
        opts = layout.get_stream_options()
        assert isinstance(opts, list)

        env = layout.get_environment_overrides()
        assert isinstance(env, dict)

    def test_get_and_set_state(self):
        """get_state and set_state round-trip properly."""
        layout = ClassicLayout(window=None)
        state = layout.get_state()
        assert "stream" in state
        assert "advanced" in state

        # Mutate and restore
        layout.set_state(state)
