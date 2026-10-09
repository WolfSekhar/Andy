import unittest
from unittest.mock import patch, MagicMock
from services.remote_actions import (
    send_keyevent,
    expand_statusbar,
    inject_clipboard_text,
    set_device_density,
    reset_device_density,
    reboot_device,
    toggle_show_touches,
    toggle_device_screen,
    adjust_device_volume
)

class TestServicesRemote(unittest.TestCase):
    def test_disconnected_safeguards(self):
        for serial in [None, "", "No devices found"]:
            self.assertFalse(send_keyevent(serial, 3)[0])
            self.assertFalse(expand_statusbar(serial, "notifications")[0])
            self.assertFalse(inject_clipboard_text(serial, "test")[0])
            self.assertFalse(set_device_density(serial, 400)[0])
            self.assertFalse(reset_device_density(serial)[0])
            self.assertFalse(reboot_device(serial)[0])
            self.assertFalse(toggle_show_touches(serial)[0])
            self.assertFalse(toggle_device_screen(serial)[0])
            self.assertFalse(adjust_device_volume(serial)[0])

    @patch('subprocess.run')
    def test_send_keyevent(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        success, _ = send_keyevent("test-serial", 3)
        self.assertTrue(success)
        mock_run.assert_called_with(
            ['adb', '-s', 'test-serial', 'shell', 'input', 'keyevent', '3'],
            capture_output=True, check=True, timeout=3
        )

    @patch('subprocess.run')
    def test_expand_statusbar(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        success, _ = expand_statusbar("test-serial", "notifications")
        self.assertTrue(success)
        mock_run.assert_called_with(
            ['adb', '-s', 'test-serial', 'shell', 'cmd', 'statusbar', 'expand-notifications'],
            capture_output=True, check=True, timeout=3
        )

    @patch('subprocess.run')
    def test_set_and_reset_density(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        self.assertTrue(set_device_density("test-serial", 480)[0])
        mock_run.assert_called_with(
            ['adb', '-s', 'test-serial', 'shell', 'wm', 'density', '480'],
            capture_output=True, check=True, timeout=3
        )

        self.assertTrue(reset_device_density("test-serial")[0])
        mock_run.assert_called_with(
            ['adb', '-s', 'test-serial', 'shell', 'wm', 'density', 'reset'],
            capture_output=True, check=True, timeout=3
        )

    @patch('subprocess.run')
    def test_reboot_modes(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        self.assertTrue(reboot_device("test-serial", "normal")[0])
        mock_run.assert_called_with(
            ['adb', '-s', 'test-serial', 'reboot'],
            capture_output=True, check=True, timeout=5
        )

        self.assertTrue(reboot_device("test-serial", "recovery")[0])
        mock_run.assert_called_with(
            ['adb', '-s', 'test-serial', 'reboot', 'recovery'],
            capture_output=True, check=True, timeout=5
        )

if __name__ == '__main__':
    unittest.main()
