import unittest
from unittest.mock import patch, MagicMock
from services.device_service import (
    get_connected_devices,
    get_detailed_device_info,
    get_device_density,
    get_device_displays,
    get_device_cameras,
    get_device_resolution
)
from tests.framework.fake_adb import FakeAdbRunner

class TestServicesDevice(unittest.TestCase):
    @patch('subprocess.run')
    def test_get_connected_devices(self, mock_run):
        mock_run.return_value = FakeAdbRunner.create_mock(
            "List of devices attached\nABC123XYZ device product:pacman model:Nothing_A142 device:pacman\n"
        )
        devices = get_connected_devices()
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0]['serial'], "ABC123XYZ")
        self.assertEqual(devices[0]['model'], "Nothing A142")

    @patch('subprocess.run')
    def test_get_detailed_device_info(self, mock_run):
        mock_run.side_effect = FakeAdbRunner.dispatch
        info = get_detailed_device_info("test-serial")
        self.assertEqual(info['model'], "Nothing Phone (2a)")
        self.assertIn("Android 16", info['version'])
        self.assertEqual(info['resolution'], "1084x2412")
        self.assertEqual(info['battery_level'], 85)
        self.assertTrue(info['battery_charging'])
        self.assertEqual(info['density_val'], 400)

    @patch('subprocess.run')
    def test_get_device_density(self, mock_run):
        mock_run.side_effect = FakeAdbRunner.dispatch
        density = get_device_density("test-serial")
        self.assertEqual(density['physical'], 420)
        self.assertEqual(density['override'], 400)
        self.assertEqual(density['current'], 400)

    @patch('subprocess.run')
    def test_get_device_displays(self, mock_run):
        mock_run.side_effect = FakeAdbRunner.dispatch
        displays = get_device_displays("test-serial")
        self.assertEqual(displays, ["0"])

    @patch('subprocess.run')
    def test_get_device_cameras(self, mock_run):
        mock_run.side_effect = FakeAdbRunner.dispatch
        cameras = get_device_cameras("test-serial")
        self.assertEqual(len(cameras), 2)
        self.assertEqual(cameras[0]['id'], "0")
        self.assertIn("back", cameras[0]['desc'])
        self.assertEqual(cameras[1]['id'], "1")
        self.assertIn("front", cameras[1]['desc'])

if __name__ == '__main__':
    unittest.main()
