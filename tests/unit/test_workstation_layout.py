"""Unit tests for WorkstationLayout."""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

import pytest
from unittest.mock import MagicMock

from ui.layouts.base_layout import BaseLayout
from ui.layouts.workstation_layout import WorkstationLayout


class TestWorkstationLayout:
    @classmethod
    def setup_class(cls):
        try:
            Adw.init()
        except Exception:
            pass

    def test_inheritance(self):
        """WorkstationLayout must inherit from BaseLayout."""
        assert issubclass(WorkstationLayout, BaseLayout)

    def test_initialization_standalone(self):
        """WorkstationLayout initializes properly without a window."""
        layout = WorkstationLayout(window=None)

        root = layout.get_widget()
        assert isinstance(root, Adw.NavigationSplitView)

        # Check split view sidebar & content pages
        assert isinstance(layout.sidebar_page, Adw.NavigationPage)
        assert isinstance(layout.content_page, Adw.NavigationPage)

        # Check navigation categories
        assert layout.nav_list is not None
        assert len(layout.categories) == 6
        cat_ids = [cat[0] for cat in layout.categories]
        assert cat_ids == ["device", "display", "camera", "audio", "input", "engine"]

        # Check top persistent action buttons
        assert isinstance(layout.btn_stream, Gtk.Button)
        assert isinstance(layout.btn_mk, Gtk.Button)
        assert layout.btn_stream.get_label() == "STREAM"
        assert layout.btn_mk.get_label() == "Connect M/K"

        # Check content stack has 6 named pages
        assert layout.stack.get_child_by_name("device") is not None
        assert layout.stack.get_child_by_name("display") is not None
        assert layout.stack.get_child_by_name("camera") is not None
        assert layout.stack.get_child_by_name("audio") is not None
        assert layout.stack.get_child_by_name("input") is not None
        assert layout.stack.get_child_by_name("engine") is not None

    def test_pango_ampersand_escaping(self):
        """All categories with ampersands must be properly escaped as &amp;."""
        layout = WorkstationLayout(window=None)

        for cat_id, title, icon in layout.categories:
            if "&" in title:
                assert "&amp;" in title
                assert " & " not in title

        # Verify header title escaping
        assert "&amp;" in layout.window_title.get_title()

    def test_stream_and_mk_delegation(self):
        """Clicking Stream and M/K buttons delegates to window handlers."""
        mock_win = MagicMock()
        mock_win.on_play_clicked = MagicMock()
        mock_win.on_connect_mk_clicked = MagicMock()
        mock_win.refresh_devices = MagicMock()

        layout = WorkstationLayout(window=mock_win)

        layout.btn_stream.emit("clicked")
        mock_win.on_play_clicked.assert_called_once()

        layout.btn_mk.emit("clicked")
        mock_win.on_connect_mk_clicked.assert_called_once()

        layout.btn_refresh.emit("clicked")
        mock_win.refresh_devices.assert_called_once()

    def test_on_device_selected(self):
        """on_device_selected updates active device row and enables buttons."""
        layout = WorkstationLayout(window=None)

        dev_info = {
            "serial": "192.168.1.50:5555",
            "model": "Pixel 8 Pro",
            "state": "device",
            "display_name": "Pixel 8 Pro (192.168.1.50:5555)"
        }

        layout.on_device_selected(dev_info)

        assert layout.device_row.get_title() == "Pixel 8 Pro (192.168.1.50:5555)"
        assert "192.168.1.50:5555" in layout.device_row.get_subtitle()
        assert layout.btn_stream.get_sensitive() is True
        assert layout.btn_mk.get_sensitive() is True

        # Test disconnect / None
        layout.on_device_selected(None)
        assert layout.device_row.get_title() == "No devices found"
        assert layout.btn_stream.get_sensitive() is False
        assert layout.btn_mk.get_sensitive() is False

    def test_on_stream_state_changed(self):
        """on_stream_state_changed toggles button appearance and sensitivity."""
        layout = WorkstationLayout(window=None)
        layout.on_device_selected({"serial": "device-1", "model": "Test", "state": "device"})

        # Stream running
        layout.on_stream_state_changed(True, mode="stream")
        assert layout.btn_stream.get_label() == "STOP"
        assert layout.btn_mk.get_sensitive() is False
        assert layout.device_dropdown.get_sensitive() is False

        # Stream stopped
        layout.on_stream_state_changed(False)
        assert layout.btn_stream.get_label() == "STREAM"
        assert layout.btn_mk.get_sensitive() is True
        assert layout.device_dropdown.get_sensitive() is True

        # M/K mode running
        layout.on_stream_state_changed(True, mode="mk")
        assert layout.btn_mk.get_label() == "DISCONNECT"
        assert layout.btn_stream.get_sensitive() is False

        # M/K mode stopped
        layout.on_stream_state_changed(False)
        assert layout.btn_mk.get_label() == "Connect M/K"
        assert layout.btn_stream.get_sensitive() is True

    def test_sync_with_cards(self):
        """sync_from_window and sync_to_window exchange state with stream and advanced cards."""
        mock_win = MagicMock()
        mock_sc = MagicMock()
        mock_ac = MagicMock()
        mock_win.stream_card = mock_sc
        mock_win.advanced_card = mock_ac

        mock_sc.type_dropdown.get_selected.return_value = 0
        mock_sc.codec_dropdown.get_selected.return_value = 1
        mock_sc.orient_dropdown.get_selected.return_value = 2
        mock_sc.bitrate_row.get_text.return_value = "12M"
        mock_sc.param_start_app.get_text.return_value = "com.android.settings"
        mock_sc.param_new_display.get_active.return_value = True
        mock_sc.param_flex_display.get_active.return_value = True
        mock_sc.param_fullscreen.get_active.return_value = False
        mock_sc.param_borderless.get_active.return_value = True
        mock_sc.param_always_on_top.get_active.return_value = False
        mock_sc.param_disable_screensaver.get_active.return_value = True
        mock_sc.param_record.get_active.return_value = True
        mock_sc.record_format_dropdown.get_selected.return_value = 1
        mock_sc.param_camera_torch.get_active.return_value = False
        mock_sc.param_camera_fps.get_selected.return_value = 0
        mock_sc.param_camera_high_speed.get_active.return_value = True
        mock_sc.param_camera_zoom.get_text.return_value = "2.0"
        mock_sc.fps_combo.get_active_text.return_value = "60"
        mock_sc.size_combo.get_active_text.return_value = "1920"

        mock_ac.param_no_audio.get_active.return_value = False
        mock_ac.audio_source_dropdown.get_selected.return_value = 1
        mock_ac.audio_codec_dropdown.get_selected.return_value = 0
        mock_ac.audio_buffer_dropdown.get_selected.return_value = 2
        mock_ac.audio_bitrate_row.get_text.return_value = "192K"
        mock_ac.param_audio_dup.get_active.return_value = True
        mock_ac.param_keyboard_uhid.get_active.return_value = True
        mock_ac.param_mouse_uhid.get_active.return_value = False
        mock_ac.param_gamepad_uhid.get_active.return_value = True
        mock_ac.mouse_bind_dropdown.get_selected.return_value = 1
        mock_ac.param_legacy_paste.get_active.return_value = False
        mock_ac.param_no_clipboard_autosync.get_active.return_value = True
        mock_ac.param_read_only.get_active.return_value = False
        mock_ac.param_show_touches.get_active.return_value = True
        mock_ac.hwdec_dropdown.get_selected.return_value = 1
        mock_ac.render_driver_dropdown.get_selected.return_value = 0
        mock_ac.gpu_dropdown.get_selected.return_value = 0
        mock_ac.buffer_dropdown.get_selected.return_value = 0
        mock_ac.param_no_downsize_on_error.get_active.return_value = True
        mock_ac.param_screen_off.get_active.return_value = True
        mock_ac.param_stay_awake.get_active.return_value = True
        mock_ac.param_power_off_on_close.get_active.return_value = True
        mock_ac.param_no_power_on.get_active.return_value = False
        mock_ac.param_print_fps.get_active.return_value = True
        mock_ac.time_limit_row.get_text.return_value = "120"
        mock_ac.timeout_dropdown.get_selected.return_value = 2

        layout = WorkstationLayout(window=mock_win)
        layout.sync_from_window()

        # Check synced values in layout widgets
        assert layout.row_bitrate.get_text() == "12M"
        assert layout.entry_start_app.get_text() == "com.android.settings"
        assert layout.row_new_display.get_active() is True
        assert layout.row_flex_display.get_active() is True
        assert layout.row_borderless.get_active() is True
        assert layout.row_record.get_active() is True
        assert layout.row_camera_high_speed.get_active() is True
        assert layout.row_camera_zoom.get_text() == "2.0"
        assert layout.row_size.get_text() == "1920"

        assert layout.row_forward_audio.get_active() is True
        assert layout.row_audio_bitrate.get_text() == "192K"
        assert layout.row_audio_dup.get_active() is True
        assert layout.row_keyboard_uhid.get_active() is True
        assert layout.row_gamepad_uhid.get_active() is True
        assert layout.row_no_clip.get_active() is True
        assert layout.row_show_touches.get_active() is True
        assert layout.row_no_downsize.get_active() is True
        assert layout.row_screen_off.get_active() is True
        assert layout.row_stay_awake.get_active() is True
        assert layout.row_power_off_close.get_active() is True
        assert layout.row_print_fps.get_active() is True
        assert layout.row_time_limit.get_text() == "120"
