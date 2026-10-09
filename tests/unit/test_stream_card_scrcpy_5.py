import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/ui')))

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw

from ui.cards.stream.stream_card import StreamCard
from core.models import StreamConfig


class TestStreamCardScrcpy5(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            Adw.init()
        except Exception:
            pass

    def setUp(self):
        self.card = StreamCard()

    def test_widget_references_exist(self):
        # Verify references exposed on self
        self.assertIsNotNone(self.card.param_render_fit)
        self.assertIsNotNone(self.card.param_camera_fps)
        self.assertIsNotNone(self.card.param_camera_high_speed)
        self.assertIsNotNone(self.card.param_camera_zoom)
        self.assertIsNotNone(self.card.param_flex_display)
        self.assertIsNotNone(self.card.param_display_ime_policy)
        self.assertIsNotNone(self.card.param_no_vd_destroy_content)
        self.assertIsNotNone(self.card.param_start_app)

        # Verify underlying section references
        self.assertIs(self.card.param_render_fit, self.card.window_section.param_render_fit)
        self.assertIs(self.card.param_camera_fps, self.card.camera_section.param_camera_fps)
        self.assertIs(self.card.param_camera_high_speed, self.card.camera_section.param_camera_high_speed)
        self.assertIs(self.card.param_camera_zoom, self.card.camera_section.param_camera_zoom)

    def test_get_stream_options_render_fit_and_start_app(self):
        self.card.param_render_fit.set_selected(2)  # stretched
        self.card.param_start_app.set_text("com.android.calculator2")

        opts = self.card.get_stream_options()
        self.assertIn("--render-fit=stretched", opts)
        self.assertIn("--start-app=com.android.calculator2", opts)

    def test_get_stream_options_virtual_display_features(self):
        # Without new_display, virtual display sub-options are ignored by builder
        self.card.param_new_display.set_active(False)
        self.card.param_flex_display.set_active(True)
        self.card.param_display_ime_policy.set_selected(1)  # local
        self.card.param_no_vd_destroy_content.set_active(True)

        opts = self.card.get_stream_options()
        self.assertNotIn("--flex-display", opts)
        self.assertNotIn("--display-ime-policy=local", opts)
        self.assertNotIn("--no-vd-destroy-content", opts)

        # With new_display active
        self.card.param_new_display.set_active(True)
        opts = self.card.get_stream_options()
        self.assertIn("--new-display", opts)
        self.assertIn("--flex-display", opts)
        self.assertIn("--display-ime-policy=local", opts)
        self.assertIn("--no-vd-destroy-content", opts)

    def test_get_stream_options_camera_features(self):
        self.card.type_dropdown.set_selected(1)  # Camera mode
        self.card.camera_model.splice(0, self.card.camera_model.get_n_items(), ["0 (front camera)"])
        self.card.camera_dropdown.set_selected(0)

        self.card.param_camera_fps.set_selected(1)  # 30 fps
        self.card.param_camera_high_speed.set_active(True)
        self.card.param_camera_zoom.set_text("2.5")

        opts = self.card.get_stream_options()
        self.assertIn("--video-source=camera", opts)
        self.assertIn("--camera-fps=30", opts)
        self.assertIn("--camera-high-speed", opts)
        self.assertIn("--camera-zoom=2.5", opts)

    def test_state_roundtrip(self):
        # Configure non-default state
        self.card.param_render_fit.set_selected(1)  # letterbox
        self.card.param_camera_fps.set_selected(2)  # 20 fps
        self.card.param_camera_high_speed.set_active(True)
        self.card.param_camera_zoom.set_text("1.8")
        self.card.param_flex_display.set_active(True)
        self.card.param_display_ime_policy.set_selected(2)  # fallback
        self.card.param_no_vd_destroy_content.set_active(True)
        self.card.param_start_app.set_text("org.videolan.vlc")

        state = self.card.get_state()
        self.assertEqual(state["render_fit"], 1)
        self.assertEqual(state["camera_fps"], 2)
        self.assertTrue(state["camera_high_speed"])
        self.assertEqual(state["camera_zoom"], "1.8")
        self.assertTrue(state["flex_display"])
        self.assertEqual(state["display_ime_policy"], 2)
        self.assertTrue(state["no_vd_destroy_content"])
        self.assertEqual(state["start_app"], "org.videolan.vlc")

        # Reset widgets
        self.card.param_render_fit.set_selected(0)
        self.card.param_camera_fps.set_selected(0)
        self.card.param_camera_high_speed.set_active(False)
        self.card.param_camera_zoom.set_text("")
        self.card.param_flex_display.set_active(False)
        self.card.param_display_ime_policy.set_selected(0)
        self.card.param_no_vd_destroy_content.set_active(False)
        self.card.param_start_app.set_text("")

        # Restore
        self.card.set_state(state)
        self.assertEqual(self.card.param_render_fit.get_selected(), 1)
        self.assertEqual(self.card.param_camera_fps.get_selected(), 2)
        self.assertTrue(self.card.param_camera_high_speed.get_active())
        self.assertEqual(self.card.param_camera_zoom.get_text(), "1.8")
        self.assertTrue(self.card.param_flex_display.get_active())
        self.assertEqual(self.card.param_display_ime_policy.get_selected(), 2)
        self.assertTrue(self.card.param_no_vd_destroy_content.get_active())
        self.assertEqual(self.card.param_start_app.get_text(), "org.videolan.vlc")

    def test_state_fallbacks(self):
        # Empty dict should safely reset to defaults
        self.card.set_state({})
        self.assertEqual(self.card.param_render_fit.get_selected(), 0)
        self.assertEqual(self.card.param_camera_fps.get_selected(), 0)
        self.assertFalse(self.card.param_camera_high_speed.get_active())
        self.assertEqual(self.card.param_camera_zoom.get_text(), "")
        self.assertFalse(self.card.param_flex_display.get_active())
        self.assertEqual(self.card.param_display_ime_policy.get_selected(), 0)
        self.assertFalse(self.card.param_no_vd_destroy_content.get_active())
        self.assertEqual(self.card.param_start_app.get_text(), "")


if __name__ == '__main__':
    unittest.main()
