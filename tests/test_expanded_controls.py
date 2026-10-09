import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Ensure we can import from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src/ui')))

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio, GLib

from window import AndyWindow
AndyWindow.setup_css = lambda self: None
from settings_manager import get_setting, set_setting
import device_manager

class TestExpandedControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            Adw.init()
        except Exception:
            pass

    def setUp(self):
        import uuid
        app_id = f'com.wolfsekhar.test{uuid.uuid4().hex[:8]}'
        self.app = Adw.Application(application_id=app_id, flags=Gio.ApplicationFlags.NON_UNIQUE)
        
        with patch('gi.repository.Gdk.Display.get_default', return_value=MagicMock()):
            with patch('scrcpy_manager.get_device_displays', return_value=[]):
                with patch('scrcpy_manager.get_device_cameras', return_value=[]):
                    self.win = AndyWindow(application=self.app)

        self.win.devices = [{'serial': 'test-serial-1', 'display_name': 'Test Phone (test-serial-1)'}]
        self.win.device_model.append("Test Phone (test-serial-1)")
        self.win.device_dropdown.set_selected(0)

    # -------------------------------------------------------------------------
    # 1. UI Scaling Controls
    # -------------------------------------------------------------------------
    def test_ui_scale_stepping_and_clamping(self):
        # Reset to 1.0
        self.win.on_zoom_reset_clicked(self.win.btn_zoom_reset)
        self.assertAlmostEqual(self.win.current_scale, 1.0)
        self.assertEqual(self.win.btn_zoom_reset.get_label(), "100%")

        # Step Up: 1.0 -> 1.10 -> 1.25 -> 1.40 -> 1.50
        self.win.on_zoom_in_clicked(self.win.btn_zoom_in)
        self.assertAlmostEqual(self.win.current_scale, 1.10)
        self.assertEqual(self.win.btn_zoom_reset.get_label(), "110%")

        self.win.on_zoom_in_clicked(self.win.btn_zoom_in)
        self.assertAlmostEqual(self.win.current_scale, 1.25)

        self.win.on_zoom_in_clicked(self.win.btn_zoom_in)
        self.assertAlmostEqual(self.win.current_scale, 1.40)

        self.win.on_zoom_in_clicked(self.win.btn_zoom_in)
        self.assertAlmostEqual(self.win.current_scale, 1.50)
        self.assertEqual(self.win.btn_zoom_reset.get_label(), "150%")
        self.assertFalse(self.win.btn_zoom_in.get_sensitive())

        # Step up while at max should remain clamped at 1.50
        self.win.on_zoom_in_clicked(self.win.btn_zoom_in)
        self.assertAlmostEqual(self.win.current_scale, 1.50)

        # Step Down towards min: 1.50 -> 1.40 -> 1.25 -> 1.10 -> 1.0 -> 0.90 -> 0.85 -> 0.75
        for _ in range(7):
            self.win.on_zoom_out_clicked(self.win.btn_zoom_out)

        self.assertAlmostEqual(self.win.current_scale, 0.75)
        self.assertEqual(self.win.btn_zoom_reset.get_label(), "75%")
        self.assertFalse(self.win.btn_zoom_out.get_sensitive())

        # Step down while at min should remain clamped at 0.75
        self.win.on_zoom_out_clicked(self.win.btn_zoom_out)
        self.assertAlmostEqual(self.win.current_scale, 0.75)

        # Reset back to 100%
        self.win.on_zoom_reset_clicked(self.win.btn_zoom_reset)
        self.assertAlmostEqual(self.win.current_scale, 1.0)
        self.assertEqual(self.win.btn_zoom_reset.get_label(), "100%")
        self.assertTrue(self.win.btn_zoom_in.get_sensitive())
        self.assertTrue(self.win.btn_zoom_out.get_sensitive())

        # Test settings persistence
        self.assertAlmostEqual(get_setting("ui_scale"), 1.0)

    # -------------------------------------------------------------------------
    # 2. Device Manager Remote ADB Controls
    # -------------------------------------------------------------------------
    def test_adb_safeguards_when_disconnected(self):
        # Empty/None serial safeguards
        success, _ = device_manager.send_keyevent(None, 3)
        self.assertFalse(success)
        success, _ = device_manager.expand_statusbar("No devices found", "notifications")
        self.assertFalse(success)
        success, _ = device_manager.inject_clipboard_text("", "Hello")
        self.assertFalse(success)
        density = device_manager.get_device_density(None)
        self.assertIsNone(density['current'])
        success, _ = device_manager.set_device_density(None, 400)
        self.assertFalse(success)
        success, _ = device_manager.reset_device_density(None)
        self.assertFalse(success)
        success, _ = device_manager.reboot_device(None)
        self.assertFalse(success)
        success, _ = device_manager.toggle_show_touches(None)
        self.assertFalse(success)

    @patch('subprocess.run')
    def test_adb_keyevent_and_statusbar_calls(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="")
        
        # Test Keyevent Home (3), Back (4), App Switch (187)
        success, _ = device_manager.send_keyevent("test-serial", 3)
        self.assertTrue(success)
        mock_run.assert_called_with(['adb', '-s', 'test-serial', 'shell', 'input', 'keyevent', '3'], capture_output=True, check=True, timeout=3)

        success, _ = device_manager.send_keyevent("test-serial", 4)
        self.assertTrue(success)
        mock_run.assert_called_with(['adb', '-s', 'test-serial', 'shell', 'input', 'keyevent', '4'], capture_output=True, check=True, timeout=3)

        # Test statusbar expand-notifications and expand-settings
        success, _ = device_manager.expand_statusbar("test-serial", "notifications")
        self.assertTrue(success)
        mock_run.assert_called_with(['adb', '-s', 'test-serial', 'shell', 'cmd', 'statusbar', 'expand-notifications'], capture_output=True, check=True, timeout=3)

        success, _ = device_manager.expand_statusbar("test-serial", "settings")
        self.assertTrue(success)
        mock_run.assert_called_with(['adb', '-s', 'test-serial', 'shell', 'cmd', 'statusbar', 'expand-settings'], capture_output=True, check=True, timeout=3)

    @patch('subprocess.run')
    def test_adb_density_and_reboot_calls(self, mock_run):
        # Mock get density output
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Physical density: 420\nOverride density: 400\n"
        )
        density = device_manager.get_device_density("test-serial")
        self.assertEqual(density['physical'], 420)
        self.assertEqual(density['override'], 400)
        self.assertEqual(density['current'], 400)

        # Test set density
        success, _ = device_manager.set_device_density("test-serial", 460)
        self.assertTrue(success)
        mock_run.assert_called_with(['adb', '-s', 'test-serial', 'shell', 'wm', 'density', '460'], capture_output=True, check=True, timeout=3)

        # Test reset density
        success, _ = device_manager.reset_device_density("test-serial")
        self.assertTrue(success)
        mock_run.assert_called_with(['adb', '-s', 'test-serial', 'shell', 'wm', 'density', 'reset'], capture_output=True, check=True, timeout=3)

        # Test reboot modes
        success, _ = device_manager.reboot_device("test-serial", "normal")
        self.assertTrue(success)
        mock_run.assert_called_with(['adb', '-s', 'test-serial', 'reboot'], capture_output=True, check=True, timeout=5)

        success, _ = device_manager.reboot_device("test-serial", "recovery")
        self.assertTrue(success)
        mock_run.assert_called_with(['adb', '-s', 'test-serial', 'reboot', 'recovery'], capture_output=True, check=True, timeout=5)

        success, _ = device_manager.reboot_device("test-serial", "bootloader")
        self.assertTrue(success)
        mock_run.assert_called_with(['adb', '-s', 'test-serial', 'reboot', 'bootloader'], capture_output=True, check=True, timeout=5)

    # -------------------------------------------------------------------------
    # 3. scrcpy 4.1 Flags Generation
    # -------------------------------------------------------------------------
    def test_stream_card_scrcpy_4_1_flags(self):
        card = self.win.stream_card
        
        # Virtual Display mode
        card.type_dropdown.set_selected(0) # Screen mode
        card.param_new_display.set_active(True)
        opts = card.get_stream_options()
        self.assertIn("--new-display", opts)

        card.param_new_display.set_active(False)
        opts = card.get_stream_options()
        self.assertNotIn("--new-display", opts)

        # Camera Torch mode
        card.type_dropdown.set_selected(1) # Camera mode
        card.param_camera_torch.set_active(True)
        opts = card.get_stream_options()
        self.assertIn("--camera-torch", opts)

        card.param_camera_torch.set_active(False)
        opts = card.get_stream_options()
        self.assertNotIn("--camera-torch", opts)

        # Recording
        card.type_dropdown.set_selected(0)
        card.param_record.set_active(True)
        card.record_format_dropdown.set_selected(0) # mp4
        opts = card.get_stream_options()
        self.assertTrue(any(o.startswith("--record=") and o.endswith(".mp4") for o in opts))
        self.assertIn("--record-format=mp4", opts)

        card.record_format_dropdown.set_selected(1) # mkv
        opts = card.get_stream_options()
        self.assertTrue(any(o.startswith("--record=") and o.endswith(".mkv") for o in opts))
        self.assertIn("--record-format=mkv", opts)

    def test_advanced_card_scrcpy_4_1_flags(self):
        adv = self.win.advanced_card
        
        # Audio Duplication
        adv.param_audio_dup.set_active(True)
        opts = adv.get_stream_options()
        self.assertIn("--audio-dup", opts)

        adv.param_audio_dup.set_active(False)
        opts = adv.get_stream_options()
        self.assertNotIn("--audio-dup", opts)

        # Audio Source: 1 = output, 2 = playback, 3 = mic
        adv.audio_source_dropdown.set_selected(1)
        self.assertIn("--audio-source=output", adv.get_stream_options())

        adv.audio_source_dropdown.set_selected(2)
        self.assertIn("--audio-source=playback", adv.get_stream_options())

        adv.audio_source_dropdown.set_selected(3)
        self.assertIn("--audio-source=mic", adv.get_stream_options())

        # Show touches & Keep active
        adv.param_show_touches.set_active(True)
        adv.param_keep_active.set_active(True)
        opts = adv.get_stream_options()
        self.assertIn("--show-touches", opts)
        self.assertIn("--keep-active", opts)

        # Screen off timeout: 1 = 10s, 3 = 60s
        adv.timeout_dropdown.set_selected(3)
        self.assertIn("--screen-off-timeout=60", adv.get_stream_options())

    def test_scrcpy_5_flags_in_expanded_controls(self):
        card = self.win.stream_card
        adv = self.win.advanced_card

        # Stream scrcpy 5 flags
        card.param_render_fit.set_selected(1) # letterbox
        card.param_start_app.set_text("com.android.settings")
        card.param_new_display.set_active(True)
        card.param_flex_display.set_active(True)
        card.param_display_ime_policy.set_selected(1) # local
        card.param_no_vd_destroy_content.set_active(True)

        opts = card.get_stream_options()
        self.assertIn("--render-fit=letterbox", opts)
        self.assertIn("--start-app=com.android.settings", opts)
        self.assertIn("--new-display", opts)
        self.assertIn("--flex-display", opts)
        self.assertIn("--display-ime-policy=local", opts)
        self.assertIn("--no-vd-destroy-content", opts)

        # Advanced scrcpy 5 flags
        adv.hwdec_dropdown.set_selected(1) # vaapi
        adv.param_no_downsize_on_error.set_active(True)
        adv.audio_bitrate_row.set_text("128")
        adv.audio_buffer_dropdown.set_selected(2) # 40 ms
        adv.param_gamepad_uhid.set_active(True)
        adv.mouse_bind_dropdown.set_selected(1) # ++++:++++
        adv.param_legacy_paste.set_active(True)
        adv.param_no_clipboard_autosync.set_active(True)
        adv.param_power_off_on_close.set_active(True)
        adv.param_no_power_on.set_active(True)
        adv.time_limit_row.set_text("45")

        adv_opts = adv.get_stream_options()
        self.assertIn("--hwdec=vaapi", adv_opts)
        self.assertIn("--no-downsize-on-error", adv_opts)
        self.assertIn("--audio-bit-rate=128K", adv_opts)
        self.assertIn("--audio-buffer=40", adv_opts)
        self.assertIn("--gamepad=uhid", adv_opts)
        self.assertIn("--mouse-bind=++++:++++", adv_opts)
        self.assertIn("--legacy-paste", adv_opts)
        self.assertIn("--no-clipboard-autosync", adv_opts)
        self.assertIn("--power-off-on-close", adv_opts)
        self.assertIn("--no-power-on", adv_opts)
        self.assertIn("--time-limit=45", adv_opts)

    # -------------------------------------------------------------------------
    # 4. State Persistence and Profile Round-trip
    # -------------------------------------------------------------------------
    def test_stream_and_advanced_state_roundtrip(self):
        card = self.win.stream_card
        adv = self.win.advanced_card

        # Set customized state including scrcpy 5.0 fields
        card.param_record.set_active(True)
        card.record_format_dropdown.set_selected(1)
        card.param_new_display.set_active(True)
        card.param_camera_torch.set_active(True)
        card.param_render_fit.set_selected(2)
        card.param_flex_display.set_active(True)
        card.param_display_ime_policy.set_selected(1)
        card.param_no_vd_destroy_content.set_active(True)
        card.param_start_app.set_text("com.android.settings")

        adv.param_audio_dup.set_active(True)
        adv.audio_source_dropdown.set_selected(2)
        adv.param_show_touches.set_active(True)
        adv.param_keep_active.set_active(True)
        adv.timeout_dropdown.set_selected(3)
        adv.hwdec_dropdown.set_selected(1)
        adv.param_no_downsize_on_error.set_active(True)
        adv.audio_bitrate_row.set_text("160")
        adv.audio_buffer_dropdown.set_selected(2)
        adv.param_gamepad_uhid.set_active(True)
        adv.mouse_bind_dropdown.set_selected(2)
        adv.param_legacy_paste.set_active(True)
        adv.param_no_clipboard_autosync.set_active(True)
        adv.param_power_off_on_close.set_active(True)
        adv.param_no_power_on.set_active(True)
        adv.time_limit_row.set_text("120")

        stream_state = card.get_state()
        adv_state = adv.get_state()

        # Reset states
        card.param_record.set_active(False)
        card.record_format_dropdown.set_selected(0)
        card.param_new_display.set_active(False)
        card.param_camera_torch.set_active(False)
        card.param_render_fit.set_selected(0)
        card.param_flex_display.set_active(False)
        card.param_display_ime_policy.set_selected(0)
        card.param_no_vd_destroy_content.set_active(False)
        card.param_start_app.set_text("")

        adv.param_audio_dup.set_active(False)
        adv.audio_source_dropdown.set_selected(0)
        adv.param_show_touches.set_active(False)
        adv.param_keep_active.set_active(False)
        adv.timeout_dropdown.set_selected(0)
        adv.hwdec_dropdown.set_selected(0)
        adv.param_no_downsize_on_error.set_active(False)
        adv.audio_bitrate_row.set_text("")
        adv.audio_buffer_dropdown.set_selected(0)
        adv.param_gamepad_uhid.set_active(False)
        adv.mouse_bind_dropdown.set_selected(0)
        adv.param_legacy_paste.set_active(False)
        adv.param_no_clipboard_autosync.set_active(False)
        adv.param_power_off_on_close.set_active(False)
        adv.param_no_power_on.set_active(False)
        adv.time_limit_row.set_text("")

        # Restore states
        card.set_state(stream_state)
        adv.set_state(adv_state)

        self.assertTrue(card.param_record.get_active())
        self.assertEqual(card.record_format_dropdown.get_selected(), 1)
        self.assertTrue(card.param_new_display.get_active())
        self.assertTrue(card.param_camera_torch.get_active())
        self.assertEqual(card.param_render_fit.get_selected(), 2)
        self.assertTrue(card.param_flex_display.get_active())
        self.assertEqual(card.param_display_ime_policy.get_selected(), 1)
        self.assertTrue(card.param_no_vd_destroy_content.get_active())
        self.assertEqual(card.param_start_app.get_text(), "com.android.settings")

        self.assertTrue(adv.param_audio_dup.get_active())
        self.assertEqual(adv.audio_source_dropdown.get_selected(), 2)
        self.assertTrue(adv.param_show_touches.get_active())
        self.assertTrue(adv.param_keep_active.get_active())
        self.assertEqual(adv.timeout_dropdown.get_selected(), 3)
        self.assertEqual(adv.hwdec_dropdown.get_selected(), 1)
        self.assertTrue(adv.param_no_downsize_on_error.get_active())
        self.assertEqual(adv.audio_bitrate_row.get_text(), "160")
        self.assertEqual(adv.audio_buffer_dropdown.get_selected(), 2)
        self.assertTrue(adv.param_gamepad_uhid.get_active())
        self.assertEqual(adv.mouse_bind_dropdown.get_selected(), 2)
        self.assertTrue(adv.param_legacy_paste.get_active())
        self.assertTrue(adv.param_no_clipboard_autosync.get_active())
        self.assertTrue(adv.param_power_off_on_close.get_active())
        self.assertTrue(adv.param_no_power_on.get_active())
        self.assertEqual(adv.time_limit_row.get_text(), "120")

if __name__ == '__main__':
    unittest.main()

