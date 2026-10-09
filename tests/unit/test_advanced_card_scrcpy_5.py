import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/ui')))

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw

from ui.cards.advanced.advanced_card import AdvancedCard
from core.models import AdvancedConfig


class TestAdvancedCardScrcpy5(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            Adw.init()
        except Exception:
            pass

    def setUp(self):
        self.adv = AdvancedCard()

    def test_widget_aliases_exist(self):
        # Perf section aliases
        self.assertIsNotNone(self.adv.hwdec_row)
        self.assertIsNotNone(self.adv.hwdec_dropdown)
        self.assertIsNotNone(self.adv.param_no_downsize_on_error)

        # Audio section aliases
        self.assertIsNotNone(self.adv.audio_bitrate_row)
        self.assertIsNotNone(self.adv.audio_buffer_row)
        self.assertIsNotNone(self.adv.audio_buffer_dropdown)

        # Device section aliases
        self.assertIsNotNone(self.adv.param_gamepad_uhid)
        self.assertIsNotNone(self.adv.mouse_bind_row)
        self.assertIsNotNone(self.adv.mouse_bind_dropdown)
        self.assertIsNotNone(self.adv.param_legacy_paste)
        self.assertIsNotNone(self.adv.param_no_clipboard_autosync)
        self.assertIsNotNone(self.adv.param_power_off_on_close)
        self.assertIsNotNone(self.adv.param_no_power_on)
        self.assertIsNotNone(self.adv.time_limit_row)

    def test_audio_section_set_no_audio(self):
        # Set values
        self.adv.audio_bitrate_row.set_text("160")
        self.adv.audio_buffer_dropdown.set_selected(2)
        self.adv.param_audio_dup.set_active(True)

        # Toggle no_audio on
        self.adv.param_no_audio.set_active(True)
        self.assertFalse(self.adv.audio_bitrate_row.get_sensitive())
        self.assertFalse(self.adv.audio_buffer_row.get_sensitive())
        self.assertEqual(self.adv.audio_bitrate_row.get_text(), "")
        self.assertEqual(self.adv.audio_buffer_dropdown.get_selected(), 0)
        self.assertFalse(self.adv.param_audio_dup.get_active())

        # Toggle no_audio off
        self.adv.param_no_audio.set_active(False)
        self.assertTrue(self.adv.audio_bitrate_row.get_sensitive())
        self.assertTrue(self.adv.audio_buffer_row.get_sensitive())

    def test_get_config_and_stream_options_scrcpy_5(self):
        self.adv.hwdec_dropdown.set_selected(1)  # vaapi
        self.adv.param_no_downsize_on_error.set_active(True)
        self.adv.audio_bitrate_row.set_text("160")
        self.adv.audio_buffer_dropdown.set_selected(2)  # 40 ms
        self.adv.param_gamepad_uhid.set_active(True)
        self.adv.mouse_bind_dropdown.set_selected(1)  # Gaming ++++:++++
        self.adv.param_legacy_paste.set_active(True)
        self.adv.param_no_clipboard_autosync.set_active(True)
        self.adv.param_power_off_on_close.set_active(True)
        self.adv.param_no_power_on.set_active(True)
        self.adv.time_limit_row.set_text("120")

        cfg = self.adv.get_config()
        self.assertIsInstance(cfg, AdvancedConfig)
        self.assertEqual(cfg.hwdec, 1)
        self.assertTrue(cfg.no_downsize_on_error)
        self.assertEqual(cfg.audio_bitrate, "160")
        self.assertEqual(cfg.audio_buffer, 2)
        self.assertTrue(cfg.gamepad_uhid)
        self.assertEqual(cfg.mouse_bind, 1)
        self.assertTrue(cfg.legacy_paste)
        self.assertTrue(cfg.no_clipboard_autosync)
        self.assertTrue(cfg.power_off_on_close)
        self.assertTrue(cfg.no_power_on)
        self.assertEqual(cfg.time_limit, "120")

        opts = self.adv.get_stream_options()
        self.assertIn("--hwdec=vaapi", opts)
        self.assertIn("--no-downsize-on-error", opts)
        self.assertIn("--audio-bit-rate=160K", opts)
        self.assertIn("--audio-buffer=40", opts)
        self.assertIn("--gamepad=uhid", opts)
        self.assertIn("--mouse-bind=++++:++++", opts)
        self.assertIn("--legacy-paste", opts)
        self.assertIn("--no-clipboard-autosync", opts)
        self.assertIn("--power-off-on-close", opts)
        self.assertIn("--no-power-on", opts)
        self.assertIn("--time-limit=120", opts)

    def test_state_roundtrip(self):
        state_in = {
            "hwdec": 2,  # disabled
            "no_downsize_on_error": True,
            "audio_bitrate": "192",
            "audio_buffer": 3,  # 50 ms
            "gamepad_uhid": True,
            "mouse_bind": 2,  # Android bhsn:++++
            "legacy_paste": True,
            "no_clipboard_autosync": True,
            "power_off_on_close": True,
            "no_power_on": True,
            "time_limit": "45",
            "screen_off": True,
            "stay_awake": True
        }
        self.adv.set_state(state_in)

        # Check UI widgets
        self.assertEqual(self.adv.hwdec_dropdown.get_selected(), 2)
        self.assertTrue(self.adv.param_no_downsize_on_error.get_active())
        self.assertEqual(self.adv.audio_bitrate_row.get_text(), "192")
        self.assertEqual(self.adv.audio_buffer_dropdown.get_selected(), 3)
        self.assertTrue(self.adv.param_gamepad_uhid.get_active())
        self.assertEqual(self.adv.mouse_bind_dropdown.get_selected(), 2)
        self.assertTrue(self.adv.param_legacy_paste.get_active())
        self.assertTrue(self.adv.param_no_clipboard_autosync.get_active())
        self.assertTrue(self.adv.param_power_off_on_close.get_active())
        self.assertTrue(self.adv.param_no_power_on.get_active())
        self.assertEqual(self.adv.time_limit_row.get_text(), "45")

        # Check get_state()
        state_out = self.adv.get_state()
        self.assertEqual(state_out["hwdec"], 2)
        self.assertTrue(state_out["no_downsize_on_error"])
        self.assertEqual(state_out["audio_bitrate"], "192")
        self.assertEqual(state_out["audio_buffer"], 3)
        self.assertTrue(state_out["gamepad_uhid"])
        self.assertEqual(state_out["mouse_bind"], 2)
        self.assertTrue(state_out["legacy_paste"])
        self.assertTrue(state_out["no_clipboard_autosync"])
        self.assertTrue(state_out["power_off_on_close"])
        self.assertTrue(state_out["no_power_on"])
        self.assertEqual(state_out["time_limit"], "45")

    def test_state_fallbacks(self):
        # Test empty or invalid state safely falls back to defaults
        self.adv.set_state({})
        self.assertEqual(self.adv.hwdec_dropdown.get_selected(), 0)
        self.assertFalse(self.adv.param_no_downsize_on_error.get_active())
        self.assertEqual(self.adv.audio_bitrate_row.get_text(), "")
        self.assertEqual(self.adv.audio_buffer_dropdown.get_selected(), 0)
        self.assertFalse(self.adv.param_gamepad_uhid.get_active())
        self.assertEqual(self.adv.mouse_bind_dropdown.get_selected(), 0)
        self.assertFalse(self.adv.param_legacy_paste.get_active())
        self.assertFalse(self.adv.param_no_clipboard_autosync.get_active())
        self.assertFalse(self.adv.param_power_off_on_close.get_active())
        self.assertFalse(self.adv.param_no_power_on.get_active())
        self.assertEqual(self.adv.time_limit_row.get_text(), "")

        # Out-of-bounds indices should fall back to 0
        invalid_state = {
            "hwdec": 999,
            "audio_buffer": 999,
            "mouse_bind": 999,
            "time_limit": None,
            "audio_bitrate": None
        }
        self.adv.set_state(invalid_state)
        self.assertEqual(self.adv.hwdec_dropdown.get_selected(), 0)
        self.assertEqual(self.adv.audio_buffer_dropdown.get_selected(), 0)
        self.assertEqual(self.adv.mouse_bind_dropdown.get_selected(), 0)
        self.assertEqual(self.adv.time_limit_row.get_text(), "")
        self.assertEqual(self.adv.audio_bitrate_row.get_text(), "")


if __name__ == '__main__':
    unittest.main()
