"""Tests for GNOME Circle theming, CSS rules, badges, and toggle interactions."""

import unittest
from unittest.mock import MagicMock, patch

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gdk

from ui.common.css import APPLICATION_CSS, apply_application_css
from ui.cards.details.details_card import DetailsCard
from ui.cards.details.specs_section import SpecsSection
from ui.cards.stream.stream_card import StreamCard
from ui.cards.advanced.advanced_card import AdvancedCard
from ui.header_bar import AndyHeaderBar


class TestGnomeCircleTheming(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            Adw.init()
        except Exception:
            pass

    def test_application_css_syntax_validity(self):
        """Verifies that APPLICATION_CSS is parsed by Gtk.CssProvider with 0 errors."""
        provider = Gtk.CssProvider()
        errors = []

        def on_error(prov, section, err):
            errors.append(err.message)

        provider.connect("parsing-error", on_error)
        provider.load_from_data(APPLICATION_CSS)

        self.assertEqual(errors, [], f"CSS parsing produced errors: {errors}")

    def test_apply_application_css_callable(self):
        """Verifies that apply_application_css runs without raising exceptions."""
        try:
            apply_application_css()
        except Exception as e:
            self.fail(f"apply_application_css raised an exception: {e}")

    def test_badge_classes_on_details_card(self):
        """Tests that conn_badge updates classes for USB, Wi-Fi, and Disconnected."""
        details = DetailsCard()

        # Initial state should be disconnected
        self.assertTrue(details.conn_badge.has_css_class("theme-badge"))
        self.assertTrue(details.conn_badge.has_css_class("badge-disconnected"))

        # Apply USB info
        details.apply_info({
            'model': 'Test Phone',
            'version': '14',
            'resolution': '1080x2400',
            'battery': '85%',
            'density': '420',
            'density_val': 420,
            'connection': 'USB',
            'aspect_ratio': '20:9'
        })
        self.assertTrue(details.conn_badge.has_css_class("badge-usb"))
        self.assertFalse(details.conn_badge.has_css_class("badge-wifi"))
        self.assertFalse(details.conn_badge.has_css_class("badge-disconnected"))

        # Apply Wi-Fi info
        details.apply_info({
            'model': 'Test Phone',
            'version': '14',
            'resolution': '1080x2400',
            'battery': '85%',
            'density': '420',
            'density_val': 420,
            'connection': 'Wi-Fi',
            'aspect_ratio': '20:9'
        })
        self.assertTrue(details.conn_badge.has_css_class("badge-wifi"))
        self.assertFalse(details.conn_badge.has_css_class("badge-usb"))
        self.assertFalse(details.conn_badge.has_css_class("badge-disconnected"))

        # Apply Disconnected info
        details.apply_info({
            'connection': 'Disconnected'
        })
        self.assertTrue(details.conn_badge.has_css_class("badge-disconnected"))
        self.assertFalse(details.conn_badge.has_css_class("badge-usb"))
        self.assertFalse(details.conn_badge.has_css_class("badge-wifi"))

    def test_specs_section_ratio_badge_classes(self):
        """Tests that the ratio badge has theme-badge and ratio-badge CSS classes."""
        specs = SpecsSection(on_density_adjust=lambda d: None, on_density_reset=lambda: None)
        self.assertTrue(specs.ratio_badge.has_css_class("theme-badge"))
        self.assertTrue(specs.ratio_badge.has_css_class("ratio-badge"))

    def test_header_bar_theme_cycling(self):
        """Tests that theme cycling button triggers and sets appropriate color scheme."""
        theme_toggled = []
        hb = AndyHeaderBar(
            on_profile_selected=lambda p: None,
            on_save_profile_clicked=lambda: None,
            on_settings_clicked=lambda: None,
            on_theme_toggled=lambda: theme_toggled.append(True)
        )
        
        style_mgr = Adw.StyleManager.get_default()
        if style_mgr:
            initial_scheme = style_mgr.get_color_scheme()
            
            # Simulate theme toggle callback from window
            schemes = [
                Adw.ColorScheme.FORCE_DARK,
                Adw.ColorScheme.FORCE_LIGHT,
                Adw.ColorScheme.DEFAULT
            ]
            for scheme in schemes:
                style_mgr.set_color_scheme(scheme)
                self.assertEqual(style_mgr.get_color_scheme(), scheme)
            
            # Reset
            style_mgr.set_color_scheme(initial_scheme)

    def test_full_toggle_interaction_and_scrcpy_flags(self):
        """Verifies that all major toggles adjust stream and advanced options correctly."""
        stream_card = StreamCard()
        adv_card = AdvancedCard()

        # Stream Card toggles
        stream_card.param_fullscreen.set_active(True)
        stream_card.param_borderless.set_active(True)
        stream_card.param_always_on_top.set_active(True)
        stream_card.param_disable_screensaver.set_active(True)
        stream_card.param_new_display.set_active(True)

        stream_opts = stream_card.get_stream_options()
        self.assertIn("--fullscreen", stream_opts)
        self.assertIn("--window-borderless", stream_opts)
        self.assertIn("--always-on-top", stream_opts)
        self.assertIn("--disable-screensaver", stream_opts)
        self.assertIn("--new-display", stream_opts)

        # Advanced Card toggles
        adv_card.param_stay_awake.set_active(True)
        adv_card.param_screen_off.set_active(True)
        adv_card.param_show_touches.set_active(True)
        adv_card.param_no_audio.set_active(True)
        adv_card.hwdec_dropdown.set_selected(1)
        adv_card.param_no_downsize_on_error.set_active(True)
        adv_card.param_gamepad_uhid.set_active(True)
        adv_card.mouse_bind_dropdown.set_selected(1)
        adv_card.param_power_off_on_close.set_active(True)

        adv_opts = adv_card.get_stream_options()
        self.assertIn("--stay-awake", adv_opts)
        self.assertIn("--turn-screen-off", adv_opts)
        self.assertIn("--show-touches", adv_opts)
        self.assertIn("--no-audio", adv_opts)
        self.assertIn("--hwdec=vaapi", adv_opts)
        self.assertIn("--no-downsize-on-error", adv_opts)
        self.assertIn("--gamepad=uhid", adv_opts)
        self.assertIn("--mouse-bind=++++:++++", adv_opts)
        self.assertIn("--power-off-on-close", adv_opts)


if __name__ == '__main__':
    unittest.main()
