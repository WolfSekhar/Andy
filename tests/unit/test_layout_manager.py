"""Unit tests for Andy's LayoutManager, HeaderBar Layout Selector, and Settings Persistence.

Tests:
1. Layout registration and instantiation (lazy loading, caching, ViewStack attachment, error handling).
2. Layout switching across all 6 layout options (state synchronization, device & stream event delegation).
3. AndyHeaderBar layout selector interactions (dropdown model, set_active_layout, callback invocation).
4. Active layout persistence in settings (defaults, round-trip persistence, fallback).
"""

import json
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio, GLib

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
from ui.header_bar import AndyHeaderBar
from services.settings_service import (
    get_setting,
    set_setting,
    load_settings,
    save_settings,
    DEFAULT_LAYOUT,
    DEFAULT_SETTINGS,
)
import settings_manager


class DummyLayout(BaseLayout):
    """Test layout implementing BaseLayout for isolated unit testing."""

    def __init__(self, window=None, tag="dummy", **kwargs):
        super().__init__(window=window, **kwargs)
        self.tag = tag
        self.widget = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.sync_from_window_called = False
        self.sync_to_window_called = False
        self.selected_device = None
        self.stream_active = False
        self.stream_mode = None

    def get_widget(self) -> Gtk.Widget:
        return self.widget

    def on_device_selected(self, device_info):
        self.selected_device = device_info

    def on_stream_state_changed(self, active: bool, mode: str = "stream"):
        self.stream_active = active
        self.stream_mode = mode

    def sync_from_window(self):
        self.sync_from_window_called = True

    def sync_to_window(self):
        self.sync_to_window_called = True


class TestLayoutRegistrationAndInstantiation(unittest.TestCase):
    """Tests for layout registration and lazy instantiation."""

    @classmethod
    def setUpClass(cls):
        try:
            Adw.init()
        except Exception:
            pass

    def setUp(self):
        self.mock_window = MagicMock()
        self.view_stack = Adw.ViewStack()
        self.manager = LayoutManager(self.mock_window, view_stack=self.view_stack)

    def test_registration_with_subclass_lazy_instantiation(self):
        """Layouts registered as BaseLayout subclasses are instantiated lazily on first access."""
        self.manager.register_layout("subclass_layout", DummyLayout)
        self.assertNotIn("subclass_layout", self.manager._instances)

        # Trigger instantiation
        layout = self.manager.get_layout("subclass_layout")
        self.assertIsInstance(layout, DummyLayout)
        self.assertEqual(layout.window, self.mock_window)
        self.assertIn("subclass_layout", self.manager._instances)
        self.assertIs(self.manager._instances["subclass_layout"], layout)

    def test_registration_with_callable_factory(self):
        """Layouts registered via callable factory functions instantiate correctly."""
        factory_called = False

        def factory(win):
            nonlocal factory_called
            factory_called = True
            return DummyLayout(win, tag="factory_tag")

        self.manager.register_layout("factory_layout", factory)
        self.assertFalse(factory_called)

        layout = self.manager.get_layout("factory_layout")
        self.assertTrue(factory_called)
        self.assertIsInstance(layout, DummyLayout)
        self.assertEqual(layout.tag, "factory_tag")

    def test_registration_with_pre_instantiated_instance(self):
        """Registering an existing BaseLayout instance caches it immediately and adds to ViewStack."""
        inst = DummyLayout(self.mock_window, tag="pre_instantiated")
        self.manager.register_layout("pre_inst", inst)

        self.assertIn("pre_inst", self.manager._instances)
        self.assertIs(self.manager.get_layout("pre_inst"), inst)
        self.assertIsNotNone(self.view_stack.get_child_by_name("pre_inst"))

    def test_get_layout_caching_returns_identical_instance(self):
        """Repeated calls to get_layout return the exact same cached instance."""
        self.manager.register_layout("cached_layout", DummyLayout)
        first_call = self.manager.get_layout("cached_layout")
        second_call = self.manager.get_layout("cached_layout")
        self.assertIs(first_call, second_call)

    def test_get_layout_unregistered_raises_key_error(self):
        """Requesting an unregistered layout raises KeyError."""
        with self.assertRaises(KeyError):
            self.manager.get_layout("nonexistent_layout")

    def test_register_invalid_factory_raises_type_error(self):
        """Registering an invalid factory raises TypeError upon instantiation."""
        self.manager.register_layout("invalid_factory", 42)
        with self.assertRaises(TypeError):
            self.manager.get_layout("invalid_factory")

    def test_view_stack_integration_on_instantiation(self):
        """When ViewStack is present, get_layout attaches root widget with title and name."""
        self.manager.register_layout(LAYOUT_CLASSIC, DummyLayout)
        layout = self.manager.get_layout(LAYOUT_CLASSIC)

        child = self.view_stack.get_child_by_name(LAYOUT_CLASSIC)
        self.assertIsNotNone(child)
        self.assertIs(child, layout.get_widget())

    def test_manager_without_view_stack(self):
        """LayoutManager functions properly even without an Adw.ViewStack."""
        manager_headless = LayoutManager(self.mock_window, view_stack=None)
        manager_headless.register_layout("headless_layout", DummyLayout)
        layout = manager_headless.get_layout("headless_layout")
        self.assertIsInstance(layout, DummyLayout)
        switched = manager_headless.switch_to_layout("headless_layout")
        self.assertIs(switched, layout)
        self.assertEqual(manager_headless.get_active_layout_id(), "headless_layout")


class TestLayoutSwitching(unittest.TestCase):
    """Tests for switching between all 6 layout options and delegating state/events."""

    @classmethod
    def setUpClass(cls):
        try:
            Adw.init()
        except Exception:
            pass

    def setUp(self):
        self.mock_window = MagicMock()
        self.view_stack = Adw.ViewStack()
        self.manager = LayoutManager(self.mock_window, view_stack=self.view_stack)

        # Register all 6 canonical layouts
        self.layouts = {}
        for layout_id in LAYOUT_ORDER:
            def make_factory(lid):
                return lambda win: DummyLayout(win, tag=lid)
            self.manager.register_layout(layout_id, make_factory(layout_id))

    def test_layout_constants_and_order_completeness(self):
        """LAYOUT_ORDER contains exactly the 6 defined layout constants."""
        expected = [
            LAYOUT_CLASSIC,
            LAYOUT_WORKSTATION,
            LAYOUT_STUDIO,
            LAYOUT_INSPECTOR,
            LAYOUT_MODULAR_HUB,
            LAYOUT_ACTION_ASSISTANT,
        ]
        self.assertEqual(LAYOUT_ORDER, expected)
        self.assertEqual(len(LAYOUT_ORDER), 6)

    def test_layout_metadata_completeness(self):
        """Every layout ID has corresponding name, icon, and description in LAYOUT_METADATA."""
        for layout_id in LAYOUT_ORDER:
            self.assertIn(layout_id, LAYOUT_METADATA)
            meta = LAYOUT_METADATA[layout_id]
            self.assertIn("name", meta)
            self.assertIn("icon", meta)
            self.assertIn("description", meta)
            self.assertTrue(len(meta["name"]) > 0)
            self.assertTrue(len(meta["icon"]) > 0)

    def test_switch_to_all_six_layout_options(self):
        """Switching between all 6 options updates active ID, active layout, and ViewStack visible child."""
        for layout_id in LAYOUT_ORDER:
            active = self.manager.switch_to_layout(layout_id)
            self.assertIsInstance(active, DummyLayout)
            self.assertEqual(active.tag, layout_id)
            self.assertEqual(self.manager.get_active_layout_id(), layout_id)
            self.assertIs(self.manager.get_active_layout(), active)
            self.assertEqual(self.view_stack.get_visible_child_name(), layout_id)
            self.assertTrue(active.sync_from_window_called)

    def test_switch_back_and_forth_between_layouts(self):
        """Switching back and forth multiple times maintains consistent active states."""
        self.manager.switch_to_layout(LAYOUT_WORKSTATION)
        self.assertEqual(self.manager.get_active_layout_id(), LAYOUT_WORKSTATION)

        self.manager.switch_to_layout(LAYOUT_MODULAR_HUB)
        self.assertEqual(self.manager.get_active_layout_id(), LAYOUT_MODULAR_HUB)

        self.manager.switch_to_layout(LAYOUT_CLASSIC)
        self.assertEqual(self.manager.get_active_layout_id(), LAYOUT_CLASSIC)

    def test_event_delegation_to_active_layout(self):
        """Device selection and stream state events delegate directly to active layout."""
        self.manager.switch_to_layout(LAYOUT_STUDIO)
        active_layout = self.manager.get_active_layout()

        device_data = {"serial": "test-device-123", "model": "Pixel 7"}
        self.manager.on_device_selected(device_data)
        self.assertEqual(active_layout.selected_device, device_data)

        self.manager.on_stream_state_changed(True, mode="stream")
        self.assertTrue(active_layout.stream_active)
        self.assertEqual(active_layout.stream_mode, "stream")

        self.manager.on_stream_state_changed(False)
        self.assertFalse(active_layout.stream_active)

    def test_switching_propagates_existing_device_state(self):
        """When switching to a new layout, pre-existing device info is immediately propagated."""
        device_data = {"serial": "persisted-serial", "model": "Galaxy S23"}
        self.manager.on_device_selected(device_data)

        new_layout = self.manager.switch_to_layout(LAYOUT_INSPECTOR)
        self.assertEqual(new_layout.selected_device, device_data)

    def test_switching_propagates_existing_stream_state(self):
        """When switching to a new layout, pre-existing stream state is immediately propagated."""
        self.manager.on_stream_state_changed(True, mode="mk")

        new_layout = self.manager.switch_to_layout(LAYOUT_ACTION_ASSISTANT)
        self.assertTrue(new_layout.stream_active)
        self.assertEqual(new_layout.stream_mode, "mk")

    def test_view_stack_notify_visible_child_name_change(self):
        """Changing ViewStack visible child name triggers internal listener and activates layout."""
        # Pre-instantiate target layout in stack
        self.manager.get_layout(LAYOUT_WORKSTATION)
        self.view_stack.set_visible_child_name(LAYOUT_WORKSTATION)

        self.assertEqual(self.manager.get_active_layout_id(), LAYOUT_WORKSTATION)
        self.assertEqual(self.manager.get_active_layout().tag, LAYOUT_WORKSTATION)


class TestHeaderBarLayoutSelector(unittest.TestCase):
    """Tests for AndyHeaderBar layout selector dropdown and interactions."""

    @classmethod
    def setUpClass(cls):
        try:
            Adw.init()
        except Exception:
            pass

    def setUp(self):
        self.on_theme = MagicMock()
        self.on_profile = MagicMock()
        self.on_save = MagicMock()
        self.on_settings = MagicMock()
        self.on_layout = MagicMock()

        self.header_bar = AndyHeaderBar(
            on_theme_toggled=self.on_theme,
            on_profile_selected=self.on_profile,
            on_save_profile_clicked=self.on_save,
            on_settings_clicked=self.on_settings,
            on_layout_selected=self.on_layout,
        )

    def test_header_bar_has_layout_dropdown_and_model(self):
        """Header bar creates layout dropdown with all 6 options in model."""
        self.assertIsNotNone(self.header_bar.layout_dropdown)
        self.assertIsInstance(self.header_bar.layout_dropdown, Gtk.DropDown)
        self.assertEqual(self.header_bar.layout_model.get_n_items(), 6)

        expected_titles = [
            "Classic Cards",
            "Modern Workstation",
            "Studio Command Deck",
            "Compact Inspector",
            "Modular Card Hub",
            "Action Assistant",
        ]
        actual_titles = [self.header_bar.layout_model.get_string(i) for i in range(6)]
        self.assertEqual(actual_titles, expected_titles)

    def test_header_bar_set_active_layout_all_six_options(self):
        """AndyHeaderBar set_active_layout handles all 6 layout identifiers cleanly."""
        test_cases = [
            (LAYOUT_CLASSIC, 0, "Classic Cards"),
            (LAYOUT_WORKSTATION, 1, "Modern Workstation"),
            (LAYOUT_STUDIO, 2, "Studio Command Deck"),
            (LAYOUT_INSPECTOR, 3, "Compact Inspector"),
            (LAYOUT_MODULAR_HUB, 4, "Modular Card Hub"),
            (LAYOUT_ACTION_ASSISTANT, 5, "Action Assistant"),
        ]

        for layout_id, expected_index, expected_title in test_cases:
            success = self.header_bar.set_active_layout(layout_id)
            self.assertTrue(success, f"Failed to set active layout: {layout_id}")
            self.assertEqual(self.header_bar.get_selected_layout_index(), expected_index)
            self.assertEqual(self.header_bar.get_layout_name(), expected_title)
            self.assertEqual(self.header_bar.get_active_layout_id(), layout_id)

    def test_header_bar_set_active_layout_by_title_and_index(self):
        """AndyHeaderBar set_active_layout allows selection by title string and integer index."""
        # By title
        self.assertTrue(self.header_bar.set_active_layout("Modern Workstation"))
        self.assertEqual(self.header_bar.get_selected_layout_index(), 1)

        # By integer index
        self.assertTrue(self.header_bar.set_active_layout(3))
        self.assertEqual(self.header_bar.get_selected_layout_index(), 3)
        self.assertEqual(self.header_bar.get_active_layout_id(), LAYOUT_INSPECTOR)

    def test_header_bar_set_active_layout_invalid_returns_false(self):
        """Passing an invalid layout identifier returns False without crashing."""
        self.assertFalse(self.header_bar.set_active_layout("invalid_layout_xyz"))
        self.assertFalse(self.header_bar.set_active_layout(999))
        self.assertFalse(self.header_bar.set_active_layout(None))

    def test_header_bar_callback_invocation_single_arg(self):
        """Header bar on_layout_selected callback receives layout_id when selection changes."""
        mock_cb = MagicMock()
        hb = AndyHeaderBar(
            self.on_theme, self.on_profile, self.on_save, self.on_settings,
            on_layout_selected=mock_cb
        )

        hb.set_active_layout(LAYOUT_STUDIO)
        mock_cb.assert_called()
        call_arg = mock_cb.call_args[0][0]
        self.assertEqual(call_arg, LAYOUT_STUDIO)

    def test_header_bar_callback_invocation_two_args(self):
        """Header bar on_layout_selected callback supports (layout_id, index) or (dropdown, pspec)."""
        mock_two_args = MagicMock()
        def callback_two_args(layout_id, index):
            mock_two_args(layout_id, index)

        hb = AndyHeaderBar(
            self.on_theme, self.on_profile, self.on_save, self.on_settings,
            on_layout_selected=callback_two_args
        )

        hb.set_active_layout(LAYOUT_ACTION_ASSISTANT)
        mock_two_args.assert_called()
        self.assertEqual(mock_two_args.call_args[0][0], LAYOUT_ACTION_ASSISTANT)
        self.assertEqual(mock_two_args.call_args[0][1], 5)

    def test_header_bar_and_layout_manager_integration(self):
        """Wiring HeaderBar on_layout_selected to LayoutManager switch_to_layout synchronizes state."""
        view_stack = Adw.ViewStack()
        manager = LayoutManager(MagicMock(), view_stack=view_stack)
        for lid in LAYOUT_ORDER:
            manager.register_layout(lid, lambda win, l=lid: DummyLayout(win, tag=l))

        def on_selected(layout_id):
            # LayoutID equality matches canonical string layout_id
            manager.switch_to_layout(str(layout_id))

        hb = AndyHeaderBar(
            self.on_theme, self.on_profile, self.on_save, self.on_settings,
            on_layout_selected=on_selected
        )

        for layout_id in LAYOUT_ORDER:
            hb.set_active_layout(layout_id)
            self.assertEqual(manager.get_active_layout_id(), layout_id)
            self.assertEqual(view_stack.get_visible_child_name(), layout_id)


class TestActiveLayoutSettingsPersistence(unittest.TestCase):
    """Tests for active layout persistence and retrieval via settings_service."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_settings_file = os.path.join(self.temp_dir.name, "settings.json")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_default_active_layout_is_classic(self):
        """When no settings file exists, default active_layout is 'classic'."""
        with patch("services.settings_service.DATA_DIR", self.temp_dir.name):
            with patch("services.settings_service.SETTINGS_FILE", self.test_settings_file):
                self.assertEqual(DEFAULT_LAYOUT, "classic")
                settings = load_settings()
                self.assertEqual(settings.get("active_layout"), "classic")
                self.assertEqual(get_setting("active_layout"), "classic")
                self.assertEqual(get_setting("active_layout", "custom_fallback"), "classic")

    def test_active_layout_persistence_roundtrip_all_six_options(self):
        """All 6 layout options can be persisted to disk and retrieved reliably."""
        with patch("services.settings_service.DATA_DIR", self.temp_dir.name):
            with patch("services.settings_service.SETTINGS_FILE", self.test_settings_file):
                for layout_id in LAYOUT_ORDER:
                    set_setting("active_layout", layout_id)
                    retrieved = get_setting("active_layout")
                    self.assertEqual(retrieved, layout_id)

                    # Read raw JSON directly to confirm disk persistence
                    with open(self.test_settings_file, "r") as f:
                        data = json.load(f)
                    self.assertEqual(data.get("active_layout"), layout_id)

    def test_settings_without_active_layout_falls_back_to_classic(self):
        """If an existing settings file lacks active_layout, load_settings merges default 'classic'."""
        with open(self.test_settings_file, "w") as f:
            json.dump({"theme": "dark", "ui_scale": 1.1}, f)

        with patch("services.settings_service.DATA_DIR", self.temp_dir.name):
            with patch("services.settings_service.SETTINGS_FILE", self.test_settings_file):
                settings = load_settings()
                self.assertEqual(settings.get("theme"), "dark")
                self.assertEqual(settings.get("ui_scale"), 1.1)
                self.assertEqual(settings.get("active_layout"), "classic")
                self.assertEqual(get_setting("active_layout"), "classic")

    def test_settings_manager_re_exports_active_layout(self):
        """settings_manager compatibility shim re-exports DEFAULT_LAYOUT and settings functions."""
        self.assertTrue(hasattr(settings_manager, "DEFAULT_LAYOUT"))
        self.assertEqual(settings_manager.DEFAULT_LAYOUT, "classic")
        self.assertTrue(hasattr(settings_manager, "get_setting"))
        self.assertTrue(hasattr(settings_manager, "set_setting"))
        self.assertTrue(hasattr(settings_manager, "load_settings"))

    def test_layout_switch_and_settings_persistence_flow(self):
        """End-to-end simulation: user switches layout, setting is saved, and reloaded on start."""
        with patch("services.settings_service.DATA_DIR", self.temp_dir.name):
            with patch("services.settings_service.SETTINGS_FILE", self.test_settings_file):
                # 1. First app launch: load saved or default layout
                saved_layout = get_setting("active_layout", DEFAULT_LAYOUT)
                self.assertEqual(saved_layout, "classic")

                # 2. User switches to Modern Workstation
                set_setting("active_layout", LAYOUT_WORKSTATION)

                # 3. Next app launch reads persisted layout
                reloaded_layout = get_setting("active_layout", DEFAULT_LAYOUT)
                self.assertEqual(reloaded_layout, LAYOUT_WORKSTATION)


if __name__ == "__main__":
    unittest.main()
