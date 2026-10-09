"""Unit tests for AndyHeaderBar functionality."""

import pytest
from unittest.mock import MagicMock
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw

from ui.header_bar import AndyHeaderBar


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


class TestAndyHeaderBar:
    """Test suite for AndyHeaderBar."""

    def test_header_bar_initialization_defaults(self, dummy_callbacks):
        hb = AndyHeaderBar(**dummy_callbacks)
        assert hb.widget is not None
        assert isinstance(hb.widget, Adw.HeaderBar)

        # Theme button
        assert isinstance(hb.theme_button, Gtk.Button)
        assert hb.theme_button.get_valign() == Gtk.Align.CENTER

        # Profile controls
        assert isinstance(hb.profile_dropdown, Gtk.DropDown)
        assert isinstance(hb.profile_model, Gtk.StringList)

        # Action buttons
        assert isinstance(hb.save_button, Gtk.Button)
        assert isinstance(hb.settings_button, Gtk.Button)

        # Title widget
        assert isinstance(hb.window_title, Adw.WindowTitle)
        assert hb.window_title.get_title() == "Andy"
        assert hb.window_title.get_subtitle() == "scrcpy Wayland Controller"

    def test_theme_button_triggers_callback(self, dummy_callbacks):
        hb = AndyHeaderBar(**dummy_callbacks)
        hb.theme_button.emit("clicked")
        dummy_callbacks["on_theme_toggled"].assert_called_once()

    def test_save_button_triggers_callback(self, dummy_callbacks):
        hb = AndyHeaderBar(**dummy_callbacks)
        hb.save_button.emit("clicked")
        dummy_callbacks["on_save_profile_clicked"].assert_called_once()

    def test_settings_button_triggers_callback(self, dummy_callbacks):
        hb = AndyHeaderBar(**dummy_callbacks)
        hb.settings_button.emit("clicked")
        dummy_callbacks["on_settings_clicked"].assert_called_once()

    def test_profile_management(self, dummy_callbacks):
        hb = AndyHeaderBar(**dummy_callbacks)
        profiles = ["Gaming 120Hz", "Webcam Mode", "Low Latency"]
        hb.set_profiles(profiles, select_name="Webcam Mode")

        # Total items: Default + 3 profiles = 4
        assert hb.profile_model.get_n_items() == 4
        assert hb.get_profile_name(0) == "Default"
        assert hb.get_profile_name(1) == "Gaming 120Hz"
        assert hb.get_profile_name(2) == "Webcam Mode"
        assert hb.get_profile_name(3) == "Low Latency"

        # Selected should be index 2 ("Webcam Mode")
        assert hb.get_selected_profile_index() == 2

    def test_update_theme_icon(self, dummy_callbacks):
        hb = AndyHeaderBar(**dummy_callbacks)
        # Should execute without errors
        hb.update_theme_icon()
        assert hb.theme_button.get_icon_name() in [
            "display-brightness-symbolic",
            "weather-clear-night-symbolic",
        ]
