"""Exhaustive unit test suite for ALL toggles, switches, dropdowns, and controls

Tests:
1. Window & Display Toggles (fullscreen, borderless, always on top, disable screensaver, render fit, start app, virtual display, flex display, ime policy, vd destroy)
2. Video & Stream Toggles (codec, bitrate, rotation, max-fps, max-size)
3. Camera Toggles (camera id, facing, camera fps, high speed, zoom, torch)
4. Record Toggles (record switch, format mp4/mkv)
5. Performance & Audio Toggles (hwdec, no downsize, buffer presets, audio buffer, audio toggle, audio sources, codecs, bitrate, dup)
6. HID, Input & Lifecycle Toggles (stay awake, screen off, keyboard/mouse uhid, gamepad uhid, mouse bindings, legacy paste, no clipboard autosync, otg/read-only, power off on close, no power on, time limit, timeout, show touches, keep active)
7. Remote & Details Controls (keyevents, status bar expand, density, reboot)
8. Command Builder & Launch Combinations
9. Complete Toggle State Roundtrip (saving and restoring state with all toggles customized)
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio

from ui.cards.stream.stream_card import StreamCard
from ui.cards.advanced.advanced_card import AdvancedCard
from ui.cards.details.details_card import DetailsCard
from core.scrcpy_builder import build_scrcpy_args
from core.models import StreamConfig, AdvancedConfig, DeviceInfo
import device_manager


class TestAllClassicToggles(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            Adw.init()
        except Exception:
            pass

    def setUp(self):
        self.stream_card = StreamCard()
        self.advanced_card = AdvancedCard()
        self.details_card = DetailsCard()

    # =========================================================================
    # 1. Window & Display Toggles (StreamCard)
    # =========================================================================
    def test_window_display_switches(self):
        sc = self.stream_card

        # Fullscreen
        sc.param_fullscreen.set_active(True)
        self.assertIn("--fullscreen", sc.get_stream_options())
        sc.param_fullscreen.set_active(False)
        self.assertNotIn("--fullscreen", sc.get_stream_options())

        # Borderless
        sc.param_borderless.set_active(True)
        self.assertIn("--window-borderless", sc.get_stream_options())
        sc.param_borderless.set_active(False)
        self.assertNotIn("--window-borderless", sc.get_stream_options())

        # Always On Top
        sc.param_always_on_top.set_active(True)
        self.assertIn("--always-on-top", sc.get_stream_options())
        sc.param_always_on_top.set_active(False)
        self.assertNotIn("--always-on-top", sc.get_stream_options())

        # Disable Screensaver
        sc.param_disable_screensaver.set_active(True)
        self.assertIn("--disable-screensaver", sc.get_stream_options())
        sc.param_disable_screensaver.set_active(False)
        self.assertNotIn("--disable-screensaver", sc.get_stream_options())

    def test_render_fit_and_start_app(self):
        sc = self.stream_card

        # Render Fit (0=Default, 1=letterbox, 2=stretched, 3=unscaled)
        sc.param_render_fit.set_selected(0)
        self.assertFalse(any(o.startswith("--render-fit") for o in sc.get_stream_options()))

        sc.param_render_fit.set_selected(1)
        self.assertIn("--render-fit=letterbox", sc.get_stream_options())

        sc.param_render_fit.set_selected(2)
        self.assertIn("--render-fit=stretched", sc.get_stream_options())

        sc.param_render_fit.set_selected(3)
        self.assertIn("--render-fit=unscaled", sc.get_stream_options())

        # Start App
        sc.param_start_app.set_text("com.android.vending")
        self.assertIn("--start-app=com.android.vending", sc.get_stream_options())
        sc.param_start_app.set_text("")
        self.assertFalse(any(o.startswith("--start-app") for o in sc.get_stream_options()))

    def test_virtual_display_all_subtoggles(self):
        sc = self.stream_card

        # Enable virtual display
        sc.param_new_display.set_active(True)
        opts = sc.get_stream_options()
        self.assertIn("--new-display", opts)

        # Flex Display
        sc.param_flex_display.set_active(True)
        self.assertIn("--flex-display", sc.get_stream_options())
        sc.param_flex_display.set_active(False)
        self.assertNotIn("--flex-display", sc.get_stream_options())

        # Display IME Policy (0=Default, 1=local, 2=fallback, 3=hide)
        sc.param_display_ime_policy.set_selected(1)
        self.assertIn("--display-ime-policy=local", sc.get_stream_options())
        sc.param_display_ime_policy.set_selected(2)
        self.assertIn("--display-ime-policy=fallback", sc.get_stream_options())
        sc.param_display_ime_policy.set_selected(3)
        self.assertIn("--display-ime-policy=hide", sc.get_stream_options())

        # No VD Destroy Content
        sc.param_no_vd_destroy_content.set_active(True)
        self.assertIn("--no-vd-destroy-content", sc.get_stream_options())
        sc.param_no_vd_destroy_content.set_active(False)
        self.assertNotIn("--no-vd-destroy-content", sc.get_stream_options())

        # Turn OFF virtual display -> all VD flags omitted
        sc.param_new_display.set_active(False)
        opts = sc.get_stream_options()
        self.assertNotIn("--new-display", opts)
        self.assertNotIn("--flex-display", opts)
        self.assertNotIn("--display-ime-policy=local", opts)
        self.assertNotIn("--no-vd-destroy-content", opts)

    # =========================================================================
    # 2. Video & Stream Toggles (StreamCard)
    # =========================================================================
    def test_video_section_dropdowns(self):
        sc = self.stream_card

        # Video Codec: 0=Default, 1=h264, 2=h265, 3=av1
        sc.codec_dropdown.set_selected(1)
        self.assertIn("--video-codec=h264", sc.get_stream_options())
        sc.codec_dropdown.set_selected(2)
        self.assertIn("--video-codec=h265", sc.get_stream_options())
        sc.codec_dropdown.set_selected(3)
        self.assertIn("--video-codec=av1", sc.get_stream_options())

        # Video Bitrate
        sc.bitrate_row.set_text("16")
        self.assertIn("--video-bit-rate=16M", sc.get_stream_options())
        sc.bitrate_row.set_text("")
        self.assertFalse(any(o.startswith("--video-bit-rate") for o in sc.get_stream_options()))

        # Rotation: 0=Default, 1=0, 2=90, 3=180, 4=270
        sc.orient_dropdown.set_selected(1)
        self.assertIn("--orientation=0", sc.get_stream_options())
        sc.orient_dropdown.set_selected(2)
        self.assertIn("--orientation=90", sc.get_stream_options())
        sc.orient_dropdown.set_selected(3)
        self.assertIn("--orientation=180", sc.get_stream_options())
        sc.orient_dropdown.set_selected(4)
        self.assertIn("--orientation=270", sc.get_stream_options())

    # =========================================================================
    # 3. Camera Toggles (StreamCard)
    # =========================================================================
    def test_camera_mode_and_subtoggles(self):
        sc = self.stream_card
        adv = self.advanced_card

        # Switch to Camera Mode (index 1)
        sc.type_dropdown.set_selected(1)
        adv.set_camera_mode(True)
        opts = sc.get_stream_options()
        self.assertIn("--video-source=camera", opts)

        # Apply cameras and select
        sc.camera_section.apply_cameras([
            {'id': '0', 'desc': '0 (front, 1920x1080)'},
            {'id': '1', 'desc': '1 (back, 3840x2160)'}
        ])
        sc.camera_dropdown.set_selected(0)
        self.assertIn("--camera-id=0", sc.get_stream_options())
        sc.camera_dropdown.set_selected(1)
        self.assertIn("--camera-id=1", sc.get_stream_options())

        # Camera FPS
        sc.param_camera_fps.set_selected(1)  # 30 fps
        self.assertIn("--camera-fps=30", sc.get_stream_options())
        sc.param_camera_fps.set_selected(2)  # 20 fps
        self.assertIn("--camera-fps=20", sc.get_stream_options())

        # Camera High-Speed
        sc.param_camera_high_speed.set_active(True)
        self.assertIn("--camera-high-speed", sc.get_stream_options())
        sc.param_camera_high_speed.set_active(False)
        self.assertNotIn("--camera-high-speed", sc.get_stream_options())

        # Camera Torch
        sc.param_camera_torch.set_active(True)
        self.assertIn("--camera-torch", sc.get_stream_options())
        sc.param_camera_torch.set_active(False)
        self.assertNotIn("--camera-torch", sc.get_stream_options())

        # Camera Zoom
        sc.param_camera_zoom.set_text("2.5")
        self.assertIn("--camera-zoom=2.5", sc.get_stream_options())
        sc.param_camera_zoom.set_text("")
        self.assertFalse(any(o.startswith("--camera-zoom") for o in sc.get_stream_options()))

        # Switch back to Screen Mode
        sc.type_dropdown.set_selected(0)
        adv.set_camera_mode(False)
        self.assertNotIn("--video-source=camera", sc.get_stream_options())

    # =========================================================================
    # 4. Recording Toggles (StreamCard)
    # =========================================================================
    def test_record_toggle_and_format(self):
        sc = self.stream_card

        sc.param_record.set_active(True)
        sc.record_format_dropdown.set_selected(0)  # mp4
        opts = sc.get_stream_options()
        self.assertTrue(any(o.startswith("--record=") and o.endswith(".mp4") for o in opts))
        self.assertIn("--record-format=mp4", opts)

        sc.record_format_dropdown.set_selected(1)  # mkv
        opts = sc.get_stream_options()
        self.assertTrue(any(o.startswith("--record=") and o.endswith(".mkv") for o in opts))
        self.assertIn("--record-format=mkv", opts)

        sc.param_record.set_active(False)
        opts = sc.get_stream_options()
        self.assertFalse(any(o.startswith("--record") for o in opts))

    # =========================================================================
    # 5. Performance & Audio Toggles (AdvancedCard)
    # =========================================================================
    def test_performance_toggles(self):
        adv = self.advanced_card

        # Hardware Decoding (0=Auto, 1=vaapi, 2=disabled)
        adv.hwdec_dropdown.set_selected(0)
        self.assertFalse(any(o.startswith("--hwdec") for o in adv.get_stream_options()))
        adv.hwdec_dropdown.set_selected(1)
        self.assertIn("--hwdec=vaapi", adv.get_stream_options())
        adv.hwdec_dropdown.set_selected(2)
        self.assertIn("--hwdec=disabled", adv.get_stream_options())

        # No downsize on error
        adv.param_no_downsize_on_error.set_active(True)
        self.assertIn("--no-downsize-on-error", adv.get_stream_options())
        adv.param_no_downsize_on_error.set_active(False)
        self.assertNotIn("--no-downsize-on-error", adv.get_stream_options())

        # Video Buffer (0=Default, 1=0ms, 2=20ms, 3=30ms, 4=50ms)
        adv.buffer_dropdown.set_selected(2)
        self.assertIn("--video-buffer=20", adv.get_stream_options())
        adv.buffer_dropdown.set_selected(4)
        self.assertIn("--video-buffer=50", adv.get_stream_options())
        adv.buffer_dropdown.set_selected(0)
        self.assertNotIn("--video-buffer", adv.get_stream_options())

        # Audio Buffer (0=Auto, 1=20ms, 2=40ms, 3=50ms, 4=100ms)
        adv.audio_buffer_dropdown.set_selected(1)
        self.assertIn("--audio-buffer=20", adv.get_stream_options())
        adv.audio_buffer_dropdown.set_selected(2)
        self.assertIn("--audio-buffer=40", adv.get_stream_options())
        adv.audio_buffer_dropdown.set_selected(0)
        self.assertFalse(any(o.startswith("--audio-buffer") for o in adv.get_stream_options()))

    def test_audio_toggles_and_codecs(self):
        adv = self.advanced_card

        # Audio On/Off (param_no_audio: True means disable audio, i.e., --no-audio)
        adv.param_no_audio.set_active(True)
        self.assertIn("--no-audio", adv.get_stream_options())
        adv.param_no_audio.set_active(False)
        self.assertNotIn("--no-audio", adv.get_stream_options())

        # Audio Codec (0=Default, 1=opus, 2=aac, 3=flac, 4=raw)
        adv.audio_codec_dropdown.set_selected(1)
        self.assertIn("--audio-codec=opus", adv.get_stream_options())
        adv.audio_codec_dropdown.set_selected(2)
        self.assertIn("--audio-codec=aac", adv.get_stream_options())
        adv.audio_codec_dropdown.set_selected(3)
        self.assertIn("--audio-codec=flac", adv.get_stream_options())
        adv.audio_codec_dropdown.set_selected(4)
        self.assertIn("--audio-codec=raw", adv.get_stream_options())

        # Audio Source (0=Default, 1=output, 2=playback, 3=mic)
        adv.audio_source_dropdown.set_selected(1)
        self.assertIn("--audio-source=output", adv.get_stream_options())
        adv.audio_source_dropdown.set_selected(2)
        self.assertIn("--audio-source=playback", adv.get_stream_options())
        adv.audio_source_dropdown.set_selected(3)
        self.assertIn("--audio-source=mic", adv.get_stream_options())

        # Audio Bitrate
        adv.audio_bitrate_row.set_text("192")
        self.assertIn("--audio-bit-rate=192K", adv.get_stream_options())
        adv.audio_bitrate_row.set_text("")
        self.assertFalse(any(o.startswith("--audio-bit-rate") for o in adv.get_stream_options()))

        # Audio Dup
        adv.param_audio_dup.set_active(True)
        self.assertIn("--audio-dup", adv.get_stream_options())
        adv.param_audio_dup.set_active(False)
        self.assertNotIn("--audio-dup", adv.get_stream_options())

    # =========================================================================
    # 6. HID, Input & Lifecycle Toggles (AdvancedCard)
    # =========================================================================
    def test_hid_and_peripherals_toggles(self):
        adv = self.advanced_card

        # Gamepad UHID
        adv.param_gamepad_uhid.set_active(True)
        self.assertIn("--gamepad=uhid", adv.get_stream_options())
        adv.param_gamepad_uhid.set_active(False)
        self.assertNotIn("--gamepad=uhid", adv.get_stream_options())

        # Keyboard & Mouse UHID
        adv.param_keyboard_uhid.set_active(True)
        self.assertIn("--keyboard=uhid", adv.get_stream_options())
        adv.param_keyboard_uhid.set_active(False)

        adv.param_mouse_uhid.set_active(True)
        self.assertIn("--mouse=uhid", adv.get_stream_options())
        adv.param_mouse_uhid.set_active(False)

        # Mouse Bindings (1=Gaming ++++:++++, 2=Android bhsn:++++, 3=Shift ++++:bhsn)
        adv.mouse_bind_dropdown.set_selected(1)
        self.assertIn("--mouse-bind=++++:++++", adv.get_stream_options())
        adv.mouse_bind_dropdown.set_selected(2)
        self.assertIn("--mouse-bind=bhsn:++++", adv.get_stream_options())
        adv.mouse_bind_dropdown.set_selected(3)
        self.assertIn("--mouse-bind=++++:bhsn", adv.get_stream_options())
        adv.mouse_bind_dropdown.set_selected(0)
        self.assertFalse(any(o.startswith("--mouse-bind") for o in adv.get_stream_options()))

        # Legacy Paste
        adv.param_legacy_paste.set_active(True)
        self.assertIn("--legacy-paste", adv.get_stream_options())
        adv.param_legacy_paste.set_active(False)
        self.assertNotIn("--legacy-paste", adv.get_stream_options())

        # No Clipboard Autosync
        adv.param_no_clipboard_autosync.set_active(True)
        self.assertIn("--no-clipboard-autosync", adv.get_stream_options())
        adv.param_no_clipboard_autosync.set_active(False)
        self.assertNotIn("--no-clipboard-autosync", adv.get_stream_options())

        # Read-only / No control
        adv.param_read_only.set_active(True)
        self.assertIn("--no-control", adv.get_stream_options())
        adv.param_read_only.set_active(False)
        self.assertNotIn("--no-control", adv.get_stream_options())

    def test_lifecycle_and_timeout_toggles(self):
        adv = self.advanced_card

        # Stay Awake
        adv.param_stay_awake.set_active(True)
        self.assertIn("--stay-awake", adv.get_stream_options())
        adv.param_stay_awake.set_active(False)
        self.assertNotIn("--stay-awake", adv.get_stream_options())

        # Screen Off
        adv.param_screen_off.set_active(True)
        self.assertIn("--turn-screen-off", adv.get_stream_options())
        adv.param_screen_off.set_active(False)
        self.assertNotIn("--turn-screen-off", adv.get_stream_options())

        # Power Off on Close
        adv.param_power_off_on_close.set_active(True)
        self.assertIn("--power-off-on-close", adv.get_stream_options())
        adv.param_power_off_on_close.set_active(False)
        self.assertNotIn("--power-off-on-close", adv.get_stream_options())

        # No Power On
        adv.param_no_power_on.set_active(True)
        self.assertIn("--no-power-on", adv.get_stream_options())
        adv.param_no_power_on.set_active(False)
        self.assertNotIn("--no-power-on", adv.get_stream_options())

        # Time Limit
        adv.time_limit_row.set_text("60")
        self.assertIn("--time-limit=60", adv.get_stream_options())
        adv.time_limit_row.set_text("")
        self.assertFalse(any(o.startswith("--time-limit") for o in adv.get_stream_options()))

        # Screen off timeout (index 1 = 10s, index 2 = 30s)
        adv.timeout_dropdown.set_selected(1)
        self.assertIn("--screen-off-timeout=10", adv.get_stream_options())
        adv.timeout_dropdown.set_selected(2)
        self.assertIn("--screen-off-timeout=30", adv.get_stream_options())

        # Show touches & Keep active
        adv.param_show_touches.set_active(True)
        self.assertIn("--show-touches", adv.get_stream_options())
        adv.param_show_touches.set_active(False)

        adv.param_keep_active.set_active(True)
        self.assertIn("--keep-active", adv.get_stream_options())
        adv.param_keep_active.set_active(False)

    # =========================================================================
    # 7. Details & Remote Device Actions
    # =========================================================================
    @patch('subprocess.run')
    def test_remote_keyevents_and_statusbar(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="")
        serial = "test-serial-123"

        # Keyevents
        device_manager.send_keyevent(serial, 3)    # Home
        mock_run.assert_called_with(['adb', '-s', serial, 'shell', 'input', 'keyevent', '3'], capture_output=True, check=True, timeout=3)

        device_manager.send_keyevent(serial, 4)    # Back
        mock_run.assert_called_with(['adb', '-s', serial, 'shell', 'input', 'keyevent', '4'], capture_output=True, check=True, timeout=3)

        device_manager.send_keyevent(serial, 187)  # AppSwitch
        mock_run.assert_called_with(['adb', '-s', serial, 'shell', 'input', 'keyevent', '187'], capture_output=True, check=True, timeout=3)

        device_manager.send_keyevent(serial, 26)   # Power
        mock_run.assert_called_with(['adb', '-s', serial, 'shell', 'input', 'keyevent', '26'], capture_output=True, check=True, timeout=3)

        device_manager.send_keyevent(serial, 24)   # Volume Up
        mock_run.assert_called_with(['adb', '-s', serial, 'shell', 'input', 'keyevent', '24'], capture_output=True, check=True, timeout=3)

        device_manager.send_keyevent(serial, 25)   # Volume Down
        mock_run.assert_called_with(['adb', '-s', serial, 'shell', 'input', 'keyevent', '25'], capture_output=True, check=True, timeout=3)

        # Statusbar
        device_manager.expand_statusbar(serial, "notifications")
        mock_run.assert_called_with(['adb', '-s', serial, 'shell', 'cmd', 'statusbar', 'expand-notifications'], capture_output=True, check=True, timeout=3)

        device_manager.expand_statusbar(serial, "settings")
        mock_run.assert_called_with(['adb', '-s', serial, 'shell', 'cmd', 'statusbar', 'expand-settings'], capture_output=True, check=True, timeout=3)

    @patch('subprocess.run')
    def test_remote_density_and_reboot(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="")
        serial = "test-serial-123"

        # Set density
        device_manager.set_device_density(serial, 420)
        mock_run.assert_called_with(['adb', '-s', serial, 'shell', 'wm', 'density', '420'], capture_output=True, check=True, timeout=3)

        # Reset density
        device_manager.reset_device_density(serial)
        mock_run.assert_called_with(['adb', '-s', serial, 'shell', 'wm', 'density', 'reset'], capture_output=True, check=True, timeout=3)

        # Reboot modes
        device_manager.reboot_device(serial, "normal")
        mock_run.assert_called_with(['adb', '-s', serial, 'reboot'], capture_output=True, check=True, timeout=5)

        device_manager.reboot_device(serial, "recovery")
        mock_run.assert_called_with(['adb', '-s', serial, 'reboot', 'recovery'], capture_output=True, check=True, timeout=5)

        device_manager.reboot_device(serial, "bootloader")
        mock_run.assert_called_with(['adb', '-s', serial, 'reboot', 'bootloader'], capture_output=True, check=True, timeout=5)

    # =========================================================================
    # 8. Command Builder & Launch Combinations
    # =========================================================================
    def test_command_builder_combinations(self):
        s_cfg = StreamConfig(
            type=0,
            size="1080",
            fps="60",
            codec=2,  # h265
            bitrate="16M",
            orientation=1,  # 0 deg
            fullscreen=True,
            borderless=True,
            always_on_top=True,
            render_fit=1,  # letterbox
            start_app="com.android.settings",
            new_display=True,
            flex_display=True,
            display_ime_policy=1,  # local
            no_vd_destroy_content=True,
            record=True,
            record_format=0,
        )

        a_cfg = AdvancedConfig(
            hwdec=1,  # vaapi
            no_downsize_on_error=True,
            buffer=2,  # 20ms
            audio_buffer=2,  # 40ms
            no_audio=False,
            audio_codec=1,  # opus
            audio_bitrate="192",
            audio_source=3,  # mic
            audio_dup=True,
            gamepad_uhid=True,
            mouse_bind=1,  # ++++:++++
            legacy_paste=True,
            no_clipboard_autosync=True,
            power_off_on_close=True,
            no_power_on=True,
            time_limit="120",
            stay_awake=True,
            screen_off=True,
            show_touches=True,
        )

        cmd = build_scrcpy_args(serial="phone-xyz", stream=s_cfg, advanced=a_cfg, mode="stream")
        self.assertIn("--max-size=1080", cmd)
        self.assertIn("--max-fps=60", cmd)
        self.assertIn("--video-codec=h265", cmd)
        self.assertIn("--video-bit-rate=16M", cmd)
        self.assertIn("--orientation=0", cmd)
        self.assertIn("--stay-awake", cmd)
        self.assertIn("--turn-screen-off", cmd)
        self.assertIn("--always-on-top", cmd)
        self.assertIn("--show-touches", cmd)
        self.assertIn("--window-borderless", cmd)
        self.assertIn("--fullscreen", cmd)
        self.assertIn("--render-fit=letterbox", cmd)
        self.assertIn("--start-app=com.android.settings", cmd)
        self.assertIn("--new-display", cmd)
        self.assertIn("--flex-display", cmd)
        self.assertIn("--display-ime-policy=local", cmd)
        self.assertIn("--no-vd-destroy-content", cmd)
        self.assertIn("--hwdec=vaapi", cmd)
        self.assertIn("--no-downsize-on-error", cmd)
        self.assertIn("--video-buffer=20", cmd)
        self.assertIn("--audio-buffer=40", cmd)
        self.assertIn("--audio-codec=opus", cmd)
        self.assertIn("--audio-bit-rate=192K", cmd)
        self.assertIn("--audio-source=mic", cmd)
        self.assertIn("--audio-dup", cmd)
        self.assertIn("--gamepad=uhid", cmd)
        self.assertIn("--mouse-bind=++++:++++", cmd)
        self.assertIn("--legacy-paste", cmd)
        self.assertIn("--no-clipboard-autosync", cmd)
        self.assertIn("--power-off-on-close", cmd)
        self.assertIn("--no-power-on", cmd)
        self.assertIn("--time-limit=120", cmd)

    def test_connect_mk_command_builder(self):
        s_cfg = StreamConfig()
        a_cfg = AdvancedConfig()

        cmd = build_scrcpy_args(serial="phone-xyz", stream=s_cfg, advanced=a_cfg, mode="mk")
        self.assertIn("--max-size=300", cmd)
        self.assertIn("--no-audio", cmd)
        self.assertIn("--fullscreen", cmd)

    # =========================================================================
    # 9. Complete Toggle State Roundtrip
    # =========================================================================
    def test_all_toggles_state_roundtrip(self):
        sc = self.stream_card
        adv = self.advanced_card

        # Set stream card toggles
        sc.param_fullscreen.set_active(True)
        sc.param_borderless.set_active(True)
        sc.param_always_on_top.set_active(True)
        sc.param_disable_screensaver.set_active(True)
        sc.param_render_fit.set_selected(2)
        sc.param_start_app.set_text("com.test.app")
        sc.param_new_display.set_active(True)
        sc.param_flex_display.set_active(True)
        sc.param_display_ime_policy.set_selected(1)
        sc.param_no_vd_destroy_content.set_active(True)
        sc.codec_dropdown.set_selected(2)
        sc.bitrate_row.set_text("16")
        sc.orient_dropdown.set_selected(2)
        sc.param_record.set_active(True)
        sc.record_format_dropdown.set_selected(1)

        # Set advanced card toggles
        adv.hwdec_dropdown.set_selected(1)
        adv.param_no_downsize_on_error.set_active(True)
        adv.buffer_dropdown.set_selected(2)
        adv.audio_buffer_dropdown.set_selected(3)
        adv.param_no_audio.set_active(False)
        adv.audio_codec_dropdown.set_selected(2)
        adv.audio_source_dropdown.set_selected(3)
        adv.audio_bitrate_row.set_text("256")
        adv.param_audio_dup.set_active(True)
        adv.param_gamepad_uhid.set_active(True)
        adv.mouse_bind_dropdown.set_selected(1)
        adv.param_legacy_paste.set_active(True)
        adv.param_no_clipboard_autosync.set_active(True)
        adv.param_power_off_on_close.set_active(True)
        adv.param_no_power_on.set_active(True)
        adv.time_limit_row.set_text("300")
        adv.param_stay_awake.set_active(True)
        adv.param_screen_off.set_active(True)
        adv.param_show_touches.set_active(True)

        # Capture snapshot
        stream_state = sc.get_state()
        adv_state = adv.get_state()

        # Reset all toggles back to defaults
        sc.param_fullscreen.set_active(False)
        sc.param_borderless.set_active(False)
        sc.param_always_on_top.set_active(False)
        sc.param_disable_screensaver.set_active(False)
        sc.param_render_fit.set_selected(0)
        sc.param_start_app.set_text("")
        sc.param_new_display.set_active(False)
        sc.param_flex_display.set_active(False)
        sc.param_display_ime_policy.set_selected(0)
        sc.param_no_vd_destroy_content.set_active(False)
        sc.codec_dropdown.set_selected(0)
        sc.bitrate_row.set_text("")
        sc.orient_dropdown.set_selected(0)
        sc.param_record.set_active(False)
        sc.record_format_dropdown.set_selected(0)

        adv.hwdec_dropdown.set_selected(0)
        adv.param_no_downsize_on_error.set_active(False)
        adv.buffer_dropdown.set_selected(0)
        adv.audio_buffer_dropdown.set_selected(0)
        adv.param_no_audio.set_active(True)
        adv.audio_codec_dropdown.set_selected(0)
        adv.audio_source_dropdown.set_selected(0)
        adv.audio_bitrate_row.set_text("")
        adv.param_audio_dup.set_active(False)
        adv.param_gamepad_uhid.set_active(False)
        adv.mouse_bind_dropdown.set_selected(0)
        adv.param_legacy_paste.set_active(False)
        adv.param_no_clipboard_autosync.set_active(False)
        adv.param_power_off_on_close.set_active(False)
        adv.param_no_power_on.set_active(False)
        adv.time_limit_row.set_text("")
        adv.param_stay_awake.set_active(False)
        adv.param_screen_off.set_active(False)
        adv.param_show_touches.set_active(False)

        # Restore snapshot
        sc.set_state(stream_state)
        adv.set_state(adv_state)

        # Assert every single toggle was restored accurately
        self.assertTrue(sc.param_fullscreen.get_active())
        self.assertTrue(sc.param_borderless.get_active())
        self.assertTrue(sc.param_always_on_top.get_active())
        self.assertTrue(sc.param_disable_screensaver.get_active())
        self.assertEqual(sc.param_render_fit.get_selected(), 2)
        self.assertEqual(sc.param_start_app.get_text(), "com.test.app")
        self.assertTrue(sc.param_new_display.get_active())
        self.assertTrue(sc.param_flex_display.get_active())
        self.assertEqual(sc.param_display_ime_policy.get_selected(), 1)
        self.assertTrue(sc.param_no_vd_destroy_content.get_active())
        self.assertEqual(sc.codec_dropdown.get_selected(), 2)
        self.assertEqual(sc.bitrate_row.get_text(), "16")
        self.assertEqual(sc.orient_dropdown.get_selected(), 2)
        self.assertTrue(sc.param_record.get_active())
        self.assertEqual(sc.record_format_dropdown.get_selected(), 1)

        self.assertEqual(adv.hwdec_dropdown.get_selected(), 1)
        self.assertTrue(adv.param_no_downsize_on_error.get_active())
        self.assertEqual(adv.buffer_dropdown.get_selected(), 2)
        self.assertEqual(adv.audio_buffer_dropdown.get_selected(), 3)
        self.assertFalse(adv.param_no_audio.get_active())
        self.assertEqual(adv.audio_codec_dropdown.get_selected(), 2)
        self.assertEqual(adv.audio_source_dropdown.get_selected(), 3)
        self.assertEqual(adv.audio_bitrate_row.get_text(), "256")
        self.assertTrue(adv.param_audio_dup.get_active())
        self.assertTrue(adv.param_gamepad_uhid.get_active())
        self.assertEqual(adv.mouse_bind_dropdown.get_selected(), 1)
        self.assertTrue(adv.param_legacy_paste.get_active())
        self.assertTrue(adv.param_no_clipboard_autosync.get_active())
        self.assertTrue(adv.param_power_off_on_close.get_active())
        self.assertTrue(adv.param_no_power_on.get_active())
        self.assertEqual(adv.time_limit_row.get_text(), "300")
        self.assertTrue(adv.param_stay_awake.get_active())
        self.assertTrue(adv.param_screen_off.get_active())
        self.assertTrue(adv.param_show_touches.get_active())


if __name__ == '__main__':
    unittest.main()
