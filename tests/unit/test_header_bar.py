"""Unit tests for AndyHeaderBar layout selector and functionality."""

import pytest
from unittest.mock import MagicMock
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw

from ui.header_bar import AndyHeaderBar, LayoutID


@pytest.fixture(scope="module", autouse=True)
def init_adw():
    try:
        Adw.init()
    except Exception:
        pass


@pytest.fixture
def dummy_callbacks():
    return {
        "on_theme_toggled": MagicMock(),
        "on_profile_selected": MagicMock(),
        "on_save_profile_clicked": MagicMock(),
        "on_settings_clicked": MagicMock(),
    }


class TestAndyHeaderBarLayouts:
    """Test suite for AndyHeaderBar layout selector dropdown and integration."""

    def test_header_bar_initialization_defaults(self, dummy_callbacks):
        hb = AndyHeaderBar(**dummy_callbacks)
        assert hb.widget is not None
        assert isinstance(hb.layout_dropdown, Gtk.DropDown)
        assert hb.layout_model.get_n_items() == 6

        # Check options match required names
        expected_titles = [
            "Classic Cards",
            "Modern Workstation",
            "Studio Command Deck",
            "Compact Inspector",
            "Modular Card Hub",
            "Action Assistant",
        ]
        actual_titles = [hb.layout_model.get_string(i) for i in range(6)]
        assert actual_titles == expected_titles

        # Check default layout is index 0
        assert hb.get_selected_layout_index() == 0
        layout_id = hb.get_active_layout_id()
        assert layout_id == "classic"
        assert layout_id == "classic_cards"
        assert layout_id == "Classic Cards"
        assert layout_id == 0

    def test_set_active_layout_by_canonical_ids(self, dummy_callbacks):
        hb = AndyHeaderBar(**dummy_callbacks)
        
        # Test switching to each canonical id
        assert hb.set_active_layout("workstation") is True
        assert hb.get_selected_layout_index() == 1
        assert hb.get_active_layout_id() == "workstation"

        assert hb.set_active_layout("studio") is True
        assert hb.get_selected_layout_index() == 2
        assert hb.get_active_layout_id() == "studio"

        assert hb.set_active_layout("inspector") is True
        assert hb.get_selected_layout_index() == 3
        assert hb.get_active_layout_id() == "inspector"

        assert hb.set_active_layout("modular_hub") is True
        assert hb.get_selected_layout_index() == 4
        assert hb.get_active_layout_id() == "modular_hub"

        assert hb.set_active_layout("action_assistant") is True
        assert hb.get_selected_layout_index() == 5
        assert hb.get_active_layout_id() == "action_assistant"

        assert hb.set_active_layout("classic") is True
        assert hb.get_selected_layout_index() == 0
        assert hb.get_active_layout_id() == "classic"

    def test_set_active_layout_by_aliases_and_titles(self, dummy_callbacks):
        hb = AndyHeaderBar(**dummy_callbacks)

        # Full snake_case aliases
        assert hb.set_active_layout("modern_workstation") is True
        assert hb.get_selected_layout_index() == 1

        assert hb.set_active_layout("studio_command_deck") is True
        assert hb.get_selected_layout_index() == 2

        assert hb.set_active_layout("compact_inspector") is True
        assert hb.get_selected_layout_index() == 3

        assert hb.set_active_layout("modular_card_hub") is True
        assert hb.get_selected_layout_index() == 4

        # Full display titles
        assert hb.set_active_layout("Classic Cards") is True
        assert hb.get_selected_layout_index() == 0

        assert hb.set_active_layout("Modern Workstation") is True
        assert hb.get_selected_layout_index() == 1

        assert hb.set_active_layout("Studio Command Deck") is True
        assert hb.get_selected_layout_index() == 2

        assert hb.set_active_layout("Compact Inspector") is True
        assert hb.get_selected_layout_index() == 3

        assert hb.set_active_layout("Modular Card Hub") is True
        assert hb.get_selected_layout_index() == 4

        assert hb.set_active_layout("Action Assistant") is True
        assert hb.get_selected_layout_index() == 5

    def test_set_active_layout_by_indices(self, dummy_callbacks):
        hb = AndyHeaderBar(**dummy_callbacks)

        for i in range(6):
            assert hb.set_active_layout(i) is True
            assert hb.get_selected_layout_index() == i

        # String digits
        assert hb.set_active_layout("2") is True
        assert hb.get_selected_layout_index() == 2

        # Invalid index
        assert hb.set_active_layout(10) is False
        assert hb.set_active_layout(-1) is False
        assert hb.set_active_layout("unknown_layout_xyz") is False
        assert hb.set_active_layout(None) is False

    def test_layout_callback_single_argument(self, dummy_callbacks):
        calls = []
        def on_layout(layout_id):
            calls.append(layout_id)

        hb = AndyHeaderBar(**dummy_callbacks, on_layout_selected=on_layout)
        hb.set_active_layout("workstation")

        assert len(calls) == 1
        assert calls[0] == "workstation"
        assert calls[0] == "modern_workstation"

    def test_layout_callback_two_arguments_gtk_style(self, dummy_callbacks):
        calls = []
        def on_layout(dropdown, pspec):
            calls.append((dropdown, pspec))

        hb = AndyHeaderBar(**dummy_callbacks, on_layout_selected=on_layout)
        hb.set_active_layout("studio")

        assert len(calls) == 1
        assert calls[0][0] == hb.layout_dropdown

    def test_layout_callback_two_arguments_id_and_index(self, dummy_callbacks):
        calls = []
        def on_layout(layout_id, index):
            calls.append((layout_id, index))

        hb = AndyHeaderBar(**dummy_callbacks, on_layout_selected=on_layout)
        hb.set_active_layout("inspector")

        assert len(calls) == 1
        assert calls[0][0] == "inspector"
        assert calls[0][1] == 3

    def test_backward_compatibility_intact(self, dummy_callbacks):
        """Ensure existing buttons, dropdowns, and methods operate as expected."""
        hb = AndyHeaderBar(**dummy_callbacks)

        # Theme button
        assert hb.theme_button is not None
        hb.theme_button.emit("clicked")
        dummy_callbacks["on_theme_toggled"].assert_called_once()

        # Save profile button
        assert hb.save_button is not None
        hb.save_button.emit("clicked")
        dummy_callbacks["on_save_profile_clicked"].assert_called_once()

        # Settings button
        assert hb.settings_button is not None
        hb.settings_button.emit("clicked")
        dummy_callbacks["on_settings_clicked"].assert_called_once()

        # Profile management
        profiles = ["Work", "Gaming", "Webcam"]
        hb.set_profiles(profiles, select_name="Gaming")
        assert hb.get_selected_profile_index() == 2
        assert hb.get_profile_name(2) == "Gaming"

        # Layout titles helper
        assert hb.get_layout_name(0) == "Classic Cards"
        assert hb.get_layout_name(1) == "Modern Workstation"
