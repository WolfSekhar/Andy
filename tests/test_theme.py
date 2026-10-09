import sys
import os
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src/ui')))

import settings_manager
from device_manager import get_host_telemetry, take_device_screenshot, toggle_device_screen

class TestTelemetryToolsAndSettings(unittest.TestCase):
    def test_settings_theme_persistence(self):
        """Verify settings_manager correctly loads and stores theme preference."""
        with patch('builtins.open', unittest.mock.mock_open(read_data='{"theme": "dark"}')):
            with patch('os.path.exists', return_value=True):
                settings = settings_manager.load_settings()
                self.assertEqual(settings.get("theme"), "dark")

    def test_host_telemetry_detection(self):
        """Verify host telemetry returns compositor and GPU strings without crashing."""
        telemetry = get_host_telemetry()
        self.assertIn("compositor", telemetry)
        self.assertIn("gpu", telemetry)
        self.assertIsInstance(telemetry["compositor"], str)
        self.assertIsInstance(telemetry["gpu"], str)
        self.assertTrue(len(telemetry["compositor"]) > 0)
        self.assertTrue(len(telemetry["gpu"]) > 0)

    def test_device_tools_safeguards(self):
        """Verify device quick actions return safe errors when no device is connected."""
        success, msg = take_device_screenshot(None)
        self.assertFalse(success)
        self.assertIn("No device", msg)

        success, msg = toggle_device_screen(None)
        self.assertFalse(success)
        self.assertIn("No device", msg)

if __name__ == '__main__':
    unittest.main()
