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

# Mock AndyWindow's setup_css which requires a display
from window import AndyWindow
AndyWindow.setup_css = lambda self: None

class TestAndyUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # We try to initialize, but don't fail if it doesn't work headlessly
        try:
            Adw.init()
        except Exception:
            pass

    def setUp(self):
        # Use a unique valid app ID for each test to avoid "object already exported" error
        import uuid
        app_id = f'com.wolfsekhar.test{uuid.uuid4().hex[:8]}'
        self.app = Adw.Application(application_id=app_id, flags=Gio.ApplicationFlags.NON_UNIQUE)
        
        # We need to mock display for window creation
        with patch('gi.repository.Gdk.Display.get_default', return_value=MagicMock()):
            # Mock scrcpy manager calls during initialization
            with patch('scrcpy_manager.get_device_displays', return_value=[]):
                with patch('scrcpy_manager.get_device_cameras', return_value=[]):
                    self.win = AndyWindow(application=self.app)
        
        # Mock connected devices
        self.win.devices = [{'serial': 'emulator-5554', 'display_name': 'Test Emulator (emulator-5554)'}]
        self.win.device_model.append("Test Emulator (emulator-5554)")
        self.win.device_dropdown.set_selected(0)
        
    def tearDown(self):
        pass

    @patch('subprocess.Popen')
    @patch('gi.repository.GLib.child_watch_add')
    def test_all_toggle_combinations(self, mock_watch, mock_popen):
        """
        Tests each toggle and various combinations, simulating stream start/stop.
        """
        mock_proc = MagicMock()
        mock_proc.pid = 12345
        mock_popen.return_value = mock_proc
        
        card = self.win.stream_card
        adv = self.win.advanced_card
        
        def run_test(expected_flags, description):
            print(f"Running test: {description}")
            self.win.on_play_clicked(self.win.stream_button)
            mock_popen.assert_called_once()
            cmd = mock_popen.call_args[0][0]
            
            for flag in expected_flags:
                self.assertIn(flag, cmd, f"Missing flag {flag} in {description}")
                
            # Simulate process exit
            self.win.on_process_exit(12345, 0)
            self.assertIsNone(self.win.scrcpy_process)
            mock_popen.reset_mock()

        # 1. Base test
        run_test(["scrcpy", "-s", "emulator-5554"], "Basic Stream")
        
        # 2. Window Settings Toggles
        card.param_fullscreen.set_active(True)
        run_test(["--fullscreen"], "Fullscreen Toggle")
        
        card.param_borderless.set_active(True)
        run_test(["--fullscreen", "--window-borderless"], "Fullscreen + Borderless")
        
        card.param_fullscreen.set_active(False)
        run_test(["--window-borderless"], "Borderless only")
        card.param_borderless.set_active(False)

        # 3. Video Settings
        card.codec_dropdown.set_selected(1) # h264
        card.fps_combo.get_child().set_text("60")
        card.size_combo.get_child().set_text("3840")
        card.orient_dropdown.set_selected(2) # 90
        run_test(["--video-codec=h264", "--max-fps=60", "--max-size=3840", "--orientation=90"], "Full Video Settings")
        card.fps_combo.get_child().set_text("Default")
        card.size_combo.get_child().set_text("Default")
        
        # 4. Audio Settings
        adv.audio_codec_dropdown.set_selected(1) # opus
        run_test(["--audio-codec=opus"], "Audio Codec Opus")
        
        adv.param_no_audio.set_active(True)
        run_test(["--no-audio"], "No Audio Toggle")
        adv.param_no_audio.set_active(False)

        # 5. Device Parameters
        adv.param_screen_off.set_active(True)
        adv.param_stay_awake.set_active(True)
        run_test(["--turn-screen-off", "--stay-awake"], "Screen Off + Stay Awake")
        
        # 6. Stress Test: Multiple toggles mixed
        card.param_fullscreen.set_active(True)
        adv.param_read_only.set_active(True)
        adv.buffer_dropdown.set_selected(4) # 50ms
        run_test(["--fullscreen", "--no-control", "--video-buffer=50"], "Complex Combination")

    @patch('subprocess.Popen')
    @patch('gi.repository.GLib.child_watch_add')
    def test_camera_mode_logic(self, mock_watch, mock_popen):
        """
        Tests if switching to Camera mode disables unsupported options.
        """
        card = self.win.stream_card
        adv = self.win.advanced_card
        
        # 1. Switch to Camera
        card.type_dropdown.set_selected(1)
        self.assertTrue(adv.param_screen_off.get_sensitive() == False, "Screen Off should be disabled in Camera mode")
        self.assertTrue(adv.param_keyboard_uhid.get_sensitive() == False, "Keyboard UHID should be disabled in Camera mode")
        
        # 2. Verify command has camera-id
        # Clear model first to avoid "None Found" at index 0
        card.camera_model.splice(0, card.camera_model.get_n_items(), ["0 (mock camera)"])
        card.camera_dropdown.set_selected(0)
        
        self.win.on_play_clicked(self.win.stream_button)
        cmd = mock_popen.call_args[0][0]
        self.assertIn("--video-source=camera", cmd)
        self.assertIn("--camera-id=0", cmd)
        
        self.win.on_process_exit(123, 0)
        mock_popen.reset_mock()
        
        # 3. Switch back to Screen
        card.type_dropdown.set_selected(0)
        self.assertTrue(adv.param_screen_off.get_sensitive() == True, "Screen Off should be enabled in Screen mode")

    @patch('subprocess.Popen')
    @patch('gi.repository.GLib.child_watch_add')
    def test_exhaustive_individual_settings(self, mock_watch, mock_popen):
        """
        Iterates through every single option in every dropdown and every toggle
        to ensure no runtime errors and correct flag generation.
        """
        mock_proc = MagicMock()
        mock_proc.pid = 999
        mock_popen.return_value = mock_proc
        card = self.win.stream_card
        adv = self.win.advanced_card

        # Helper to test a dropdown
        def test_dropdown(dropdown, model, flag_prefix, start_index=1):
            n = model.get_n_items()
            for i in range(start_index, n):
                val = model.get_string(i)
                import re
                match = re.search(r'(\d+)', val)
                clean_val = match.group(1) if match else val
                
                print(f"Testing Dropdown {flag_prefix}: {val}")
                dropdown.set_selected(i)
                self.win.on_play_clicked(self.win.stream_button)
                
                cmd = mock_popen.call_args[0][0]
                self.assertTrue(any(clean_val in f for f in cmd), f"Flag {flag_prefix}={clean_val} not found in {cmd}")
                
                self.win.on_process_exit(999, 0)
                mock_popen.reset_mock()
            dropdown.set_selected(0) # Reset to default

        # Helper to test ComboBoxText with entry
        def test_combo_text(combo, values, flag_name):
            for val in values:
                combo.get_child().set_text(val)
                self.win.on_play_clicked(self.win.stream_button)
                cmd = mock_popen.call_args[0][0]
                self.assertTrue(any(f"--{flag_name}={val}" in f for f in cmd), f"Flag --{flag_name}={val} not found in {cmd}")
                self.win.on_process_exit(999, 0)
                mock_popen.reset_mock()
            combo.get_child().set_text("Default")

        # Helper to test a switch
        def test_switch(switch, flag, description):
            print(f"Testing Switch: {description}")
            switch.set_active(True)
            self.win.on_play_clicked(self.win.stream_button)
            
            cmd = mock_popen.call_args[0][0]
            self.assertIn(flag, cmd)
            
            self.win.on_process_exit(999, 0)
            mock_popen.reset_mock()
            switch.set_active(False)

        # Execute tests for all widgets
        test_switch(card.param_fullscreen, "--fullscreen", "Fullscreen")
        test_switch(card.param_borderless, "--window-borderless", "Borderless")
        test_switch(card.param_always_on_top, "--always-on-top", "Always On Top")
        test_switch(card.param_disable_screensaver, "--disable-screensaver", "Disable Screensaver")
        
        test_dropdown(card.codec_dropdown, card.codec_model, "--video-codec")
        test_combo_text(card.fps_combo, ["60", "30", "15"], "max-fps")
        test_combo_text(card.size_combo, ["3840", "2560", "1920", "1280"], "max-size")
        test_dropdown(card.orient_dropdown, card.orient_model, "--orientation")
        
        # Advanced Card tests
        test_dropdown(adv.audio_codec_dropdown, adv.audio_codec_model, "--audio-codec")
        test_dropdown(adv.render_driver_dropdown, adv.render_driver_model, "--render-driver")
        test_dropdown(adv.buffer_dropdown, adv.buffer_model, "--video-buffer")

        test_switch(adv.param_print_fps, "--print-fps", "Show FPS Logs")
        test_switch(adv.param_screen_off, "--turn-screen-off", "Screen Off")
        test_switch(adv.param_stay_awake, "--stay-awake", "Stay Awake")
        test_switch(adv.param_no_audio, "--no-audio", "No Audio")
        test_switch(adv.param_read_only, "--no-control", "Read Only")
        test_switch(adv.param_keyboard_uhid, "--keyboard=uhid", "Keyboard UHID")
        test_switch(adv.param_mouse_uhid, "--mouse=uhid", "Mouse UHID")

    @patch('subprocess.Popen')
    @patch('gi.repository.GLib.child_watch_add')
    def test_gpu_and_backend_environment_overrides(self, mock_watch, mock_popen):
        """
        Tests that GPU Adapter and Window Backend correctly set environment variables on launch.
        """
        mock_proc = MagicMock()
        mock_proc.pid = 456
        mock_popen.return_value = mock_proc

        adv = self.win.advanced_card

        # 1. NVIDIA PRIME offload
        adv.gpu_dropdown.set_selected(1) # Discrete NVIDIA
        self.win.on_play_clicked(self.win.stream_button)
        env = mock_popen.call_args[1].get('env', {})
        self.assertEqual(env.get("__NV_PRIME_RENDER_OFFLOAD"), "1")
        self.assertEqual(env.get("__GLX_VENDOR_LIBRARY_NAME"), "nvidia")
        self.win.on_process_exit(456, 0)
        mock_popen.reset_mock()
        adv.gpu_dropdown.set_selected(0)

        # 2. XWayland Backend
        adv.backend_dropdown.set_selected(1) # XWayland (X11)
        self.win.on_play_clicked(self.win.stream_button)
        env = mock_popen.call_args[1].get('env', {})
        self.assertEqual(env.get("SDL_VIDEODRIVER"), "x11")
        self.win.on_process_exit(456, 0)
        mock_popen.reset_mock()

        # 3. Auto Backend (clears SDL_VIDEODRIVER)
        adv.backend_dropdown.set_selected(2) # Auto
        self.win.on_play_clicked(self.win.stream_button)
        env = mock_popen.call_args[1].get('env', {})
        self.assertNotIn("SDL_VIDEODRIVER", env)
        self.win.on_process_exit(456, 0)
        mock_popen.reset_mock()
        adv.backend_dropdown.set_selected(0) # Reset to Native Wayland

    @patch('subprocess.Popen')
    @patch('gi.repository.GLib.child_watch_add')
    def test_scrcpy_5_features_in_window(self, mock_watch, mock_popen):
        """
        Tests that newly integrated scrcpy 5.0 flags in AndyWindow correctly generate CLI args.
        """
        mock_proc = MagicMock()
        mock_proc.pid = 789
        mock_popen.return_value = mock_proc

        card = self.win.stream_card
        adv = self.win.advanced_card

        # Configure Stream Card scrcpy 5 options
        card.param_render_fit.set_selected(1) # letterbox
        card.param_start_app.set_text("com.android.settings")
        card.param_new_display.set_active(True)
        card.param_flex_display.set_active(True)
        card.param_display_ime_policy.set_selected(1) # local
        card.param_no_vd_destroy_content.set_active(True)

        # Configure Advanced Card scrcpy 5 options
        adv.hwdec_dropdown.set_selected(1) # vaapi
        adv.param_no_downsize_on_error.set_active(True)
        adv.audio_bitrate_row.set_text("128")
        adv.audio_buffer_dropdown.set_selected(1) # 20 ms
        adv.param_gamepad_uhid.set_active(True)
        adv.mouse_bind_dropdown.set_selected(1) # ++++:++++
        adv.param_legacy_paste.set_active(True)
        adv.param_no_clipboard_autosync.set_active(True)
        adv.param_power_off_on_close.set_active(True)
        adv.param_no_power_on.set_active(True)
        adv.time_limit_row.set_text("30")

        self.win.on_play_clicked(self.win.stream_button)
        mock_popen.assert_called_once()
        cmd = mock_popen.call_args[0][0]

        expected_flags = [
            "--render-fit=letterbox",
            "--start-app=com.android.settings",
            "--new-display",
            "--flex-display",
            "--display-ime-policy=local",
            "--no-vd-destroy-content",
            "--hwdec=vaapi",
            "--no-downsize-on-error",
            "--audio-bit-rate=128K",
            "--audio-buffer=20",
            "--gamepad=uhid",
            "--mouse-bind=++++:++++",
            "--legacy-paste",
            "--no-clipboard-autosync",
            "--power-off-on-close",
            "--no-power-on",
            "--time-limit=30"
        ]
        for flag in expected_flags:
            self.assertIn(flag, cmd, f"Expected scrcpy 5 flag '{flag}' not in command {cmd}")

        self.win.on_process_exit(789, 0)

if __name__ == '__main__':
    os.environ['GDK_BACKEND'] = 'x11' 
    unittest.main()

