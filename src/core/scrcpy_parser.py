from typing import Dict, Any, Tuple
import re
from core.models import StreamConfig, AdvancedConfig
from core.config import (
    VIDEO_CODECS, AUDIO_CODECS, RENDER_DRIVERS, BUFFER_PRESETS, ORIENTATIONS,
    RENDER_FITS, IME_POLICIES, CAMERA_FPS_PRESETS, AUDIO_SOURCES, AUDIO_BUFFERS,
    HWDEC_OPTIONS, TIMEOUT_PRESETS
)

def parse_scrcpy_params(param_string: str) -> Dict[str, Any]:
    """
    Parses a raw scrcpy parameter string into the app's internal state dictionary.
    Preserves exact backward compatibility with existing profile schemas.
    """
    state = {
        "stream": {
            "type": 0, "camera": 0, "display": 0, "fullscreen": False, "borderless": False,
            "always_on_top": False, "disable_screensaver": False,
            "codec": 0, "fps": "Default", "size": "Default", "bitrate": "", "orientation": 0,
            "record": False, "record_format": 0, "new_display": False, "camera_torch": False,
            "flex_display": False, "render_fit": 0, "display_ime_policy": 0,
            "no_vd_destroy_content": False, "start_app": "", "camera_zoom": "",
            "camera_fps": 0, "camera_high_speed": False
        },
        "advanced": {
            "audio_codec": 0, "audio_dup": False, "audio_source": 0,
            "gpu_adapter": 0, "render_driver": 0, "backend": 0,
            "buffer": 0, "print_fps": False, "screen_off": False,
            "stay_awake": False, "no_audio": False, "read_only": False,
            "keyboard_uhid": False, "mouse_uhid": False, "show_touches": False,
            "keep_active": False, "timeout": 0,
            "hwdec": 0, "no_downsize_on_error": False, "audio_bitrate": "",
            "audio_buffer": 0, "gamepad_uhid": False, "mouse_bind": 0,
            "legacy_paste": False, "no_clipboard_autosync": False,
            "power_off_on_close": False, "no_power_on": False, "time_limit": ""
        }
    }

    if not param_string:
        return state

    params = param_string.split()

    def find_index(model_list, value):
        for i, item in enumerate(model_list):
            if value.lower() in item.lower():
                return i
        return 0

    def find_numeric_index(model_list, value):
        v_num = re.sub(r'\D', '', value)
        for i, item in enumerate(model_list):
            item_num = re.sub(r'\D', '', item)
            if v_num and item_num and v_num == item_num:
                return i
        return 0

    for p in params:
        # Stream Toggles
        if p == "--fullscreen": state["stream"]["fullscreen"] = True
        elif p == "--window-borderless": state["stream"]["borderless"] = True
        elif p == "--always-on-top": state["stream"]["always_on_top"] = True
        elif p == "--disable-screensaver": state["stream"]["disable_screensaver"] = True
        elif p == "--video-source=camera": state["stream"]["type"] = 1
        elif p == "--camera-torch": state["stream"]["camera_torch"] = True
        elif p == "--camera-high-speed": state["stream"]["camera_high_speed"] = True
        elif p == "--new-display": state["stream"]["new_display"] = True
        elif p == "--flex-display": state["stream"]["flex_display"] = True
        elif p == "--no-vd-destroy-content": state["stream"]["no_vd_destroy_content"] = True

        # Advanced Toggles
        elif p == "--turn-screen-off": state["advanced"]["screen_off"] = True
        elif p == "--stay-awake": state["advanced"]["stay_awake"] = True
        elif p == "--no-audio": state["advanced"]["no_audio"] = True
        elif p == "--no-control": state["advanced"]["read_only"] = True
        elif p == "--keyboard=uhid": state["advanced"]["keyboard_uhid"] = True
        elif p == "--mouse=uhid": state["advanced"]["mouse_uhid"] = True
        elif p == "--gamepad=uhid": state["advanced"]["gamepad_uhid"] = True
        elif p == "--print-fps": state["advanced"]["print_fps"] = True
        elif p == "--show-touches": state["advanced"]["show_touches"] = True
        elif p == "--keep-active": state["advanced"]["keep_active"] = True
        elif p == "--audio-dup": state["advanced"]["audio_dup"] = True
        elif p == "--no-downsize-on-error": state["advanced"]["no_downsize_on_error"] = True
        elif p == "--legacy-paste": state["advanced"]["legacy_paste"] = True
        elif p == "--no-clipboard-autosync": state["advanced"]["no_clipboard_autosync"] = True
        elif p == "--power-off-on-close": state["advanced"]["power_off_on_close"] = True
        elif p == "--no-power-on": state["advanced"]["no_power_on"] = True

        # Stream Values
        elif p.startswith("--camera-id="):
            val = p.split("=")[1]
            try: state["stream"]["camera"] = int(val)
            except: pass
        elif p.startswith("--camera-zoom="):
            state["stream"]["camera_zoom"] = p.split("=")[1]
        elif p.startswith("--camera-fps="):
            val = p.split("=")[1]
            state["stream"]["camera_fps"] = find_index(CAMERA_FPS_PRESETS, val)
        elif p.startswith("--display-id="):
            val = p.split("=")[1]
            try: state["stream"]["display"] = int(val)
            except: pass
        elif p.startswith("--display-ime-policy="):
            val = p.split("=")[1]
            state["stream"]["display_ime_policy"] = find_index(IME_POLICIES, val)
        elif p.startswith("--start-app="):
            state["stream"]["start_app"] = p.split("=")[1]
        elif p.startswith("--render-fit="):
            val = p.split("=")[1]
            state["stream"]["render_fit"] = find_index(RENDER_FITS, val)
        elif p.startswith("--video-codec="):
            val = p.split("=")[1]
            state["stream"]["codec"] = find_index(VIDEO_CODECS, val)
        elif p.startswith("--max-fps="):
            state["stream"]["fps"] = p.split("=")[1]
        elif p.startswith("--max-size="):
            state["stream"]["size"] = p.split("=")[1]
        elif p.startswith("--video-bit-rate="):
            state["stream"]["bitrate"] = p.split("=")[1].replace("M", "").replace("m", "")
        elif p.startswith("--orientation="):
            val = p.split("=")[1]
            state["stream"]["orientation"] = find_index(ORIENTATIONS, val)
        elif p.startswith("--record="):
            state["stream"]["record"] = True
        elif p.startswith("--record-format="):
            val = p.split("=")[1].lower()
            state["stream"]["record_format"] = 1 if "mkv" in val else 0

        # Advanced Values
        elif p.startswith("--audio-codec="):
            val = p.split("=")[1]
            state["advanced"]["audio_codec"] = find_index(AUDIO_CODECS, val)
        elif p.startswith("--audio-source="):
            val = p.split("=")[1]
            state["advanced"]["audio_source"] = find_index(AUDIO_SOURCES, val)
        elif p.startswith("--audio-bit-rate="):
            state["advanced"]["audio_bitrate"] = p.split("=")[1].replace("K", "").replace("k", "")
        elif p.startswith("--audio-buffer="):
            val = p.split("=")[1]
            state["advanced"]["audio_buffer"] = find_numeric_index(AUDIO_BUFFERS, val)
        elif p.startswith("--hwdec="):
            val = p.split("=")[1].lower()
            state["advanced"]["hwdec"] = 1 if "vaapi" in val else 2 if "disabled" in val else 0
        elif p.startswith("--render-driver="):
            val = p.split("=")[1]
            state["advanced"]["render_driver"] = find_index(RENDER_DRIVERS, val)
        elif p.startswith("--video-buffer="):
            val = p.split("=")[1]
            state["advanced"]["buffer"] = find_numeric_index(BUFFER_PRESETS, val)
        elif p.startswith("--mouse-bind="):
            val = p.split("=")[1]
            if val == "++++:++++": state["advanced"]["mouse_bind"] = 1
            elif val == "bhsn:++++": state["advanced"]["mouse_bind"] = 2
            elif val == "++++:bhsn": state["advanced"]["mouse_bind"] = 3
        elif p.startswith("--time-limit="):
            state["advanced"]["time_limit"] = p.split("=")[1]
        elif p.startswith("--screen-off-timeout="):
            val = p.split("=")[1]
            state["advanced"]["timeout"] = find_numeric_index(TIMEOUT_PRESETS, val)

    return state


def parse_scrcpy_to_configs(param_string: str) -> Tuple[StreamConfig, AdvancedConfig]:
    """
    Parses a raw scrcpy parameter string into typed StreamConfig and AdvancedConfig objects.
    """
    state_dict = parse_scrcpy_params(param_string)
    return (
        StreamConfig.from_dict(state_dict.get("stream")),
        AdvancedConfig.from_dict(state_dict.get("advanced"))
    )

