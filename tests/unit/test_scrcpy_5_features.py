import unittest
from core.models import StreamConfig, AdvancedConfig
from core.scrcpy_builder import build_scrcpy_args

class TestScrcpy5Features(unittest.TestCase):
    def setUp(self):
        self.stream = StreamConfig()
        self.advanced = AdvancedConfig()

    def test_virtual_display_and_flex(self):
        self.stream.new_display = True
        self.stream.flex_display = True
        self.stream.display_ime_policy = 1  # local
        self.stream.no_vd_destroy_content = True

        opts = build_scrcpy_args("test-serial", self.stream, self.advanced)
        self.assertIn("--new-display", opts)
        self.assertIn("--flex-display", opts)
        self.assertIn("--display-ime-policy=local", opts)
        self.assertIn("--no-vd-destroy-content", opts)

    def test_render_fit(self):
        self.stream.render_fit = 2  # stretched
        opts = build_scrcpy_args("test-serial", self.stream, self.advanced)
        self.assertIn("--render-fit=stretched", opts)

        self.stream.render_fit = 3  # unscaled
        opts = build_scrcpy_args("test-serial", self.stream, self.advanced)
        self.assertIn("--render-fit=unscaled", opts)

    def test_app_launch(self):
        self.stream.start_app = "com.android.calculator2"
        opts = build_scrcpy_args("test-serial", self.stream, self.advanced)
        self.assertIn("--start-app=com.android.calculator2", opts)

    def test_camera_scrcpy_5_features(self):
        self.stream.type = 1  # Camera mode
        self.stream.camera_zoom = "2.5"
        self.stream.camera_fps = 1  # 30 fps
        self.stream.camera_high_speed = True

        opts = build_scrcpy_args("test-serial", self.stream, self.advanced)
        self.assertIn("--video-source=camera", opts)
        self.assertIn("--camera-zoom=2.5", opts)
        self.assertIn("--camera-fps=30", opts)
        self.assertIn("--camera-high-speed", opts)

    def test_audio_scrcpy_5_features(self):
        self.advanced.audio_bitrate = "160"
        self.advanced.audio_buffer = 2  # 40 ms
        self.advanced.audio_source = 4  # mic-unprocessed

        opts = build_scrcpy_args("test-serial", self.stream, self.advanced)
        self.assertIn("--audio-bit-rate=160K", opts)
        self.assertIn("--audio-buffer=40", opts)
        self.assertIn("--audio-source=mic-unprocessed", opts)

    def test_hardware_decoding_and_downsize(self):
        self.advanced.hwdec = 1  # vaapi
        self.advanced.no_downsize_on_error = True
        opts = build_scrcpy_args("test-serial", self.stream, self.advanced)
        self.assertIn("--hwdec=vaapi", opts)
        self.assertIn("--no-downsize-on-error", opts)

        self.advanced.hwdec = 2  # disabled
        opts = build_scrcpy_args("test-serial", self.stream, self.advanced)
        self.assertIn("--hwdec=disabled", opts)

    def test_gamepad_and_mouse_bindings(self):
        self.advanced.gamepad_uhid = True
        self.advanced.mouse_bind = 1  # Gaming ++++:++++
        opts = build_scrcpy_args("test-serial", self.stream, self.advanced)
        self.assertIn("--gamepad=uhid", opts)
        self.assertIn("--mouse-bind=++++:++++", opts)

        self.advanced.mouse_bind = 2  # Android bhsn:++++
        opts = build_scrcpy_args("test-serial", self.stream, self.advanced)
        self.assertIn("--mouse-bind=bhsn:++++", opts)

    def test_lifecycle_and_power_options(self):
        self.advanced.legacy_paste = True
        self.advanced.no_clipboard_autosync = True
        self.advanced.power_off_on_close = True
        self.advanced.no_power_on = True
        self.advanced.time_limit = "120"

        opts = build_scrcpy_args("test-serial", self.stream, self.advanced)
        self.assertIn("--legacy-paste", opts)
        self.assertIn("--no-clipboard-autosync", opts)
        self.assertIn("--power-off-on-close", opts)
        self.assertIn("--no-power-on", opts)
        self.assertIn("--time-limit=120", opts)

if __name__ == '__main__':
    unittest.main()
