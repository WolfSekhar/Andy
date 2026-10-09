import unittest
from core.models import StreamConfig, AdvancedConfig, DeviceInfo

class TestCoreModels(unittest.TestCase):
    def test_stream_config_defaults_and_serialization(self):
        cfg = StreamConfig()
        self.assertEqual(cfg.type, 0)
        self.assertEqual(cfg.codec, 0)
        self.assertEqual(cfg.fps, "Default")
        self.assertEqual(cfg.size, "Default")
        self.assertFalse(cfg.fullscreen)
        self.assertFalse(cfg.new_display)

        d = cfg.to_dict()
        self.assertIsInstance(d, dict)
        self.assertEqual(d["fps"], "Default")

        restored = StreamConfig.from_dict(d)
        self.assertEqual(restored.to_dict(), d)

    def test_stream_config_legacy_index_migration(self):
        # Legacy profiles where fps and size were integer indices
        legacy_dict = {"fps": 1, "size": 3}
        cfg = StreamConfig.from_dict(legacy_dict)
        self.assertEqual(cfg.fps, "60")
        self.assertEqual(cfg.size, "1920")

    def test_advanced_config_defaults_and_serialization(self):
        adv = AdvancedConfig()
        self.assertEqual(adv.audio_codec, 0)
        self.assertFalse(adv.audio_dup)
        self.assertEqual(adv.gpu_adapter, 0)
        self.assertFalse(adv.screen_off)

        d = adv.to_dict()
        restored = AdvancedConfig.from_dict(d)
        self.assertEqual(restored.to_dict(), d)

    def test_device_info_display_name_generation(self):
        dev = DeviceInfo(serial="ABC123", model="Pixel 8")
        self.assertEqual(dev.display_name, "Pixel 8 (ABC123)")

if __name__ == '__main__':
    unittest.main()
