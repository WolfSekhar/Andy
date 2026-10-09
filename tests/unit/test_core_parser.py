import unittest
from core.scrcpy_parser import parse_scrcpy_params, parse_scrcpy_to_configs

class TestCoreParser(unittest.TestCase):
    def test_parse_toggles(self):
        raw = "--fullscreen --window-borderless --always-on-top --disable-screensaver --turn-screen-off --stay-awake --no-audio --no-control --keyboard=uhid --mouse=uhid --print-fps"
        state = parse_scrcpy_params(raw)
        self.assertTrue(state["stream"]["fullscreen"])
        self.assertTrue(state["stream"]["borderless"])
        self.assertTrue(state["stream"]["always_on_top"])
        self.assertTrue(state["stream"]["disable_screensaver"])
        self.assertTrue(state["advanced"]["screen_off"])
        self.assertTrue(state["advanced"]["stay_awake"])
        self.assertTrue(state["advanced"]["no_audio"])
        self.assertTrue(state["advanced"]["read_only"])
        self.assertTrue(state["advanced"]["keyboard_uhid"])
        self.assertTrue(state["advanced"]["mouse_uhid"])
        self.assertTrue(state["advanced"]["print_fps"])

    def test_parse_values(self):
        raw = "--video-codec=h265 --max-fps=60 --max-size=1920 --video-bit-rate=14M --orientation=90 --audio-codec=opus --render-driver=opengl --video-buffer=20"
        state = parse_scrcpy_params(raw)
        self.assertEqual(state["stream"]["codec"], 2)  # h265
        self.assertEqual(state["stream"]["fps"], "60")
        self.assertEqual(state["stream"]["size"], "1920")
        self.assertEqual(state["stream"]["bitrate"], "14")
        self.assertEqual(state["stream"]["orientation"], 2) # 90
        self.assertEqual(state["advanced"]["audio_codec"], 1) # opus
        self.assertEqual(state["advanced"]["render_driver"], 1) # opengl
        self.assertEqual(state["advanced"]["buffer"], 2) # 20

    def test_parse_to_configs(self):
        raw = "--fullscreen --max-fps=30 --keyboard=uhid"
        stream_cfg, adv_cfg = parse_scrcpy_to_configs(raw)
        self.assertTrue(stream_cfg.fullscreen)
        self.assertEqual(stream_cfg.fps, "30")
        self.assertTrue(adv_cfg.keyboard_uhid)

    def test_parse_scrcpy_5_options(self):
        raw = (
            "--render-fit=stretched --new-display --flex-display --display-ime-policy=local "
            "--no-vd-destroy-content --start-app=com.android.settings "
            "--video-source=camera --camera-zoom=2.5 --camera-fps=30 --camera-high-speed "
            "--hwdec=vaapi --no-downsize-on-error --gamepad=uhid --mouse-bind=bhsn:++++ "
            "--audio-bit-rate=128K --audio-buffer=40 --legacy-paste --no-clipboard-autosync "
            "--power-off-on-close --no-power-on --time-limit=60"
        )
        stream_cfg, adv_cfg = parse_scrcpy_to_configs(raw)
        self.assertEqual(stream_cfg.render_fit, 2)  # stretched
        self.assertTrue(stream_cfg.new_display)
        self.assertTrue(stream_cfg.flex_display)
        self.assertEqual(stream_cfg.display_ime_policy, 1)  # local
        self.assertTrue(stream_cfg.no_vd_destroy_content)
        self.assertEqual(stream_cfg.start_app, "com.android.settings")
        self.assertEqual(stream_cfg.type, 1)  # camera
        self.assertEqual(stream_cfg.camera_zoom, "2.5")
        self.assertEqual(stream_cfg.camera_fps, 1)  # 30
        self.assertTrue(stream_cfg.camera_high_speed)

        self.assertEqual(adv_cfg.hwdec, 1)  # vaapi
        self.assertTrue(adv_cfg.no_downsize_on_error)
        self.assertTrue(adv_cfg.gamepad_uhid)
        self.assertEqual(adv_cfg.mouse_bind, 2)  # bhsn:++++
        self.assertEqual(adv_cfg.audio_bitrate, "128")
        self.assertEqual(adv_cfg.audio_buffer, 2)  # 40 ms
        self.assertTrue(adv_cfg.legacy_paste)
        self.assertTrue(adv_cfg.no_clipboard_autosync)
        self.assertTrue(adv_cfg.power_off_on_close)
        self.assertTrue(adv_cfg.no_power_on)
        self.assertEqual(adv_cfg.time_limit, "60")

if __name__ == '__main__':
    unittest.main()

