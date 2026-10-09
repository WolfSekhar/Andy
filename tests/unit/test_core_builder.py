import unittest
from core.models import StreamConfig, AdvancedConfig
from core.scrcpy_builder import build_scrcpy_args, build_environment_overrides

class TestCoreBuilder(unittest.TestCase):
    def setUp(self):
        self.stream = StreamConfig()
        self.advanced = AdvancedConfig()

    def test_base_screen_stream(self):
        opts = build_scrcpy_args("test-serial", self.stream, self.advanced)
        self.assertEqual(opts, [])

    def test_window_settings_flags(self):
        self.stream.fullscreen = True
        self.stream.borderless = True
        self.stream.always_on_top = True
        self.stream.disable_screensaver = True

        opts = build_scrcpy_args("test-serial", self.stream, self.advanced)
        self.assertIn("--fullscreen", opts)
        self.assertIn("--window-borderless", opts)
        self.assertIn("--always-on-top", opts)
        self.assertIn("--disable-screensaver", opts)

    def test_video_settings_options(self):
        self.stream.codec = 1  # h264
        self.stream.fps = "60"
        self.stream.size = "2560x1440 (Balanced)"
        self.stream.bitrate = "12"
        self.stream.orientation = 2  # 90

        opts = build_scrcpy_args("test-serial", self.stream, self.advanced)
        self.assertIn("--video-codec=h264", opts)
        self.assertIn("--max-fps=60", opts)
        self.assertIn("--max-size=2560", opts)
        self.assertIn("--video-bit-rate=12M", opts)
        self.assertIn("--orientation=90", opts)

    def test_camera_mode_options(self):
        self.stream.type = 1
        self.stream.camera = 0
        self.stream.camera_torch = True

        opts = build_scrcpy_args(
            "test-serial",
            self.stream,
            self.advanced,
            camera_id_str="0 (back, 4000x3000)"
        )
        self.assertIn("--video-source=camera", opts)
        self.assertIn("--camera-id=0", opts)
        self.assertIn("--camera-torch", opts)
        self.assertIn("--max-size=1920", opts)

    def test_record_options(self):
        self.stream.record = True
        self.stream.record_format = 1  # mkv

        opts = build_scrcpy_args(
            "test-serial",
            self.stream,
            self.advanced,
            record_dir="/tmp/test_rec"
        )
        self.assertTrue(any(o.startswith("--record=") and o.endswith(".mkv") for o in opts))
        self.assertIn("--record-format=mkv", opts)

    def test_advanced_audio_and_perf_options(self):
        self.advanced.audio_codec = 1  # opus
        self.advanced.audio_dup = True
        self.advanced.audio_source = 2  # playback
        self.advanced.render_driver = 1 # opengl
        self.advanced.buffer = 2        # 20ms
        self.advanced.print_fps = True

        opts = build_scrcpy_args("test-serial", self.stream, self.advanced)
        self.assertIn("--audio-codec=opus", opts)
        self.assertIn("--audio-dup", opts)
        self.assertIn("--audio-source=playback", opts)
        self.assertIn("--render-driver=opengl", opts)
        self.assertIn("--video-buffer=20", opts)
        self.assertIn("--print-fps", opts)

    def test_advanced_device_parameters(self):
        self.advanced.screen_off = True
        self.advanced.stay_awake = True
        self.advanced.keyboard_uhid = True
        self.advanced.mouse_uhid = True
        self.advanced.show_touches = True
        self.advanced.keep_active = True
        self.advanced.timeout = 2  # 30s

        opts = build_scrcpy_args("test-serial", self.stream, self.advanced)
        self.assertIn("--turn-screen-off", opts)
        self.assertIn("--stay-awake", opts)
        self.assertIn("--keyboard=uhid", opts)
        self.assertIn("--mouse=uhid", opts)
        self.assertIn("--show-touches", opts)
        self.assertIn("--keep-active", opts)
        self.assertIn("--screen-off-timeout=30", opts)

    def test_connect_mk_mode(self):
        opts = build_scrcpy_args("test-serial", self.stream, self.advanced, mode="mk")
        self.assertIn("--max-size=128", opts)
        self.assertIn("--fullscreen", opts)
        self.assertIn("--no-audio", opts)

    def test_environment_overrides(self):
        # 1. NVIDIA PRIME
        self.advanced.gpu_adapter = 1
        env = build_environment_overrides(self.advanced)
        self.assertEqual(env.get("__NV_PRIME_RENDER_OFFLOAD"), "1")
        self.assertEqual(env.get("__GLX_VENDOR_LIBRARY_NAME"), "nvidia")

        # 2. XWayland
        self.advanced.backend = 1
        env = build_environment_overrides(self.advanced)
        self.assertEqual(env.get("SDL_VIDEODRIVER"), "x11")

        # 3. Auto
        self.advanced.backend = 2
        env = build_environment_overrides(self.advanced)
        self.assertEqual(env.get("SDL_VIDEODRIVER"), "")

if __name__ == '__main__':
    unittest.main()
