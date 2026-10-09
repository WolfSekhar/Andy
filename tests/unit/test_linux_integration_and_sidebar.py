"""Unit test suite for Linux desktop standards, XDG paths, notifications,
inhibit service, about dialog, and the permanent slim sidebar.
"""

import os
import unittest
from unittest.mock import MagicMock, patch

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('Gio', '2.0')
from gi.repository import Gtk, Adw, Gio

from core.config import (
    APP_ID, APP_NAME, VERSION,
    XDG_CONFIG_HOME, XDG_DATA_HOME, XDG_CACHE_HOME,
    DATA_DIR, PROFILES_DIR, SETTINGS_FILE, LEGACY_DATA_DIR
)
from services.notification_service import NotificationService
from services.inhibit_service import InhibitService
from services.settings_service import load_settings, save_settings
from services.profile_service import ensure_profiles_dir, save_profile, load_profile
from ui.header_bar import AndyHeaderBar
from ui.sidebar import AndySidebar
from ui.about_dialog import show_about_dialog


class TestLinuxIntegrationAndSidebar(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            Adw.init()
        except Exception:
            pass

    # =========================================================================
    # 1. XDG Base Directory Specification
    # =========================================================================
    def test_xdg_directory_paths(self):
        """Verifies that XDG paths are correctly formed according to freedesktop specs."""
        self.assertTrue(os.path.isabs(XDG_CONFIG_HOME))
        self.assertTrue(os.path.isabs(XDG_DATA_HOME))
        self.assertTrue(os.path.isabs(XDG_CACHE_HOME))
        self.assertTrue(os.path.isabs(DATA_DIR))
        self.assertTrue(os.path.isabs(PROFILES_DIR))
        self.assertTrue(os.path.isabs(SETTINGS_FILE))
        self.assertEqual(os.path.dirname(SETTINGS_FILE), DATA_DIR)
        self.assertEqual(os.path.dirname(PROFILES_DIR), DATA_DIR)

    def test_settings_service_loads_defaults(self):
        """Verifies load_settings returns expected default dictionary."""
        settings = load_settings()
        self.assertIn("theme", settings)
        self.assertIn("ui_scale", settings)
        self.assertIn("active_layout", settings)

    # =========================================================================
    # 2. Desktop Notification Service
    # =========================================================================
    def test_notification_service_graceful_without_app(self):
        """Verifies notification methods return False gracefully when app is None."""
        service = NotificationService(application=None)
        self.assertFalse(service.notify_screenshot("/tmp/test.png"))
        self.assertFalse(service.notify_recording("/tmp/test.mp4"))
        self.assertFalse(service.notify_device_event("TestDevice", True))
        self.assertFalse(service.notify_error("Error", "Something went wrong"))

    def test_notification_service_dispatches_with_app(self):
        """Verifies notification methods invoke app.send_notification."""
        mock_app = MagicMock(spec=Gio.Application)
        service = NotificationService(application=mock_app)

        res = service.notify_screenshot("/tmp/shot.png")
        self.assertTrue(res)
        mock_app.send_notification.assert_called_once()
        args = mock_app.send_notification.call_args[0]
        self.assertEqual(args[0], "andy-screenshot")

    # =========================================================================
    # 3. System Sleep & Screensaver Inhibit Service
    # =========================================================================
    def test_inhibit_service_lifecycle(self):
        """Verifies InhibitService inhibit and uninhibit cycle."""
        service = InhibitService()
        self.assertFalse(service.is_inhibited)

        # Inhibit without app fails gracefully
        self.assertFalse(service.inhibit(None, "Testing"))

        # Inhibit with mock app
        mock_app = MagicMock(spec=Gtk.Application)
        mock_app.inhibit.return_value = 42
        service.set_application(mock_app)

        self.assertTrue(service.inhibit(None, "Testing Mirroring"))
        self.assertTrue(service.is_inhibited)
        mock_app.inhibit.assert_called_once()

        # Repeated inhibit returns True without duplicating cookie
        self.assertTrue(service.inhibit(None, "Testing again"))
        self.assertEqual(mock_app.inhibit.call_count, 1)

        # Uninhibit restores state
        self.assertTrue(service.uninhibit())
        self.assertFalse(service.is_inhibited)
        mock_app.uninhibit.assert_called_once_with(42)

    # =========================================================================
    # 4. Clean Titlebar (AndyHeaderBar)
    # =========================================================================
    def test_clean_header_bar_structure(self):
        """Verifies that AndyHeaderBar has Amberol-style textless seamless headerbar."""
        hb = AndyHeaderBar(
            on_theme_toggled=lambda: None,
            on_profile_selected=lambda d, p: None,
            on_save_profile_clicked=lambda: None,
            on_settings_clicked=lambda: None
        )
        # HeaderBar widget is valid and textless (Amberol-style)
        self.assertIsInstance(hb.widget, Adw.HeaderBar)
        self.assertFalse(hb.widget.get_show_title())
        self.assertIsNone(hb.widget.get_title_widget())
        self.assertIsNone(hb.window_title)
        self.assertTrue(hb.widget.has_css_class("flat"))
        self.assertTrue(hb.widget.has_css_class("amberol-header"))

        # Controls exist as references ready for the sidebar
        self.assertIsInstance(hb.theme_button, Gtk.Button)
        self.assertIsInstance(hb.profile_dropdown, Gtk.DropDown)
        self.assertIsInstance(hb.save_button, Gtk.Button)
        self.assertIsInstance(hb.settings_button, Gtk.Button)

    # =========================================================================
    # 5. Permanent Slim Sidebar (AndySidebar)
    # =========================================================================
    def test_sidebar_initialization_and_geometry(self):
        """Verifies that AndySidebar is constructed with proper width request and CSS."""
        theme_btn = Gtk.Button(icon_name="weather-clear-night-symbolic")
        prof_dd = Gtk.DropDown()
        save_btn = Gtk.Button(icon_name="document-save-symbolic")
        settings_btn = Gtk.Button(icon_name="emblem-system-symbolic")
        about_called = []

        sidebar = AndySidebar(
            theme_button=theme_btn,
            profile_dropdown=prof_dd,
            save_button=save_btn,
            settings_button=settings_btn,
            on_about_clicked=lambda: about_called.append(True)
        )

        self.assertIsInstance(sidebar, Gtk.Box)
        self.assertEqual(sidebar.get_orientation(), Gtk.Orientation.VERTICAL)
        self.assertTrue(sidebar.has_css_class("sidebar-pane"))
        self.assertEqual(sidebar.get_size_request(), (220, -1))
        self.assertFalse(sidebar.get_hexpand())
        self.assertTrue(sidebar.get_vexpand())

        # Verify about button triggers callback
        sidebar.about_button.emit("clicked")
        self.assertEqual(about_called, [True])

    # =========================================================================
    # 6. About Dialog
    # =========================================================================
    def test_about_dialog_creation(self):
        """Verifies show_about_dialog executes cleanly without raising exceptions."""
        try:
            window = Gtk.Window()
            show_about_dialog(window)
        except Exception as e:
            self.fail(f"show_about_dialog raised an exception: {e}")


if __name__ == '__main__':
    unittest.main()
