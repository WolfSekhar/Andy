import os
import re
import time
from typing import List, Dict, Optional
from core.models import StreamConfig, AdvancedConfig
from core.config import (
    VIDEO_CODECS, ORIENTATIONS, RENDER_FITS, IME_POLICIES, CAMERA_FPS_PRESETS,
    AUDIO_CODECS, AUDIO_SOURCES, AUDIO_BUFFERS, RENDER_DRIVERS,
    BUFFER_PRESETS, TIMEOUT_PRESETS, HWDEC_OPTIONS, DEFAULT_RECORDINGS_DIR
)

def build_scrcpy_args(
    serial: str,
    stream: StreamConfig,
    advanced: AdvancedConfig,
    mode: str = "stream",
    record_dir: Optional[str] = None,
    camera_id_str: Optional[str] = None,
    display_id_str: Optional[str] = None
) -> List[str]:
    """
    Pure function that constructs the scrcpy command line arguments.
    """
    options: List[str] = []

    if mode == "mk":
        options.extend(["--max-size=128", "--fullscreen", "--no-audio"])
        options.extend(build_advanced_args(advanced))
        return options

    # 1. Stream Source (Screen vs Camera)
    if stream.type == 1:  # Camera
        options.append("--video-source=camera")
        if camera_id_str and camera_id_str not in ("None Found", "Loading..."):
            cam_id = camera_id_str.split()[0]
            options.append(f"--camera-id={cam_id}")
        elif stream.camera >= 0 and camera_id_str is None:
            options.append(f"--camera-id={stream.camera}")

        if stream.camera_torch:
            options.append("--camera-torch")

        zoom_val = str(stream.camera_zoom).strip()
        if zoom_val:
            options.append(f"--camera-zoom={zoom_val}")

        if 0 < stream.camera_fps < len(CAMERA_FPS_PRESETS):
            fps_c = CAMERA_FPS_PRESETS[stream.camera_fps]
            options.append(f"--camera-fps={fps_c}")

        if stream.camera_high_speed:
            options.append("--camera-high-speed")
    else:  # Screen
        if display_id_str and display_id_str not in ("0 (Default)", "Loading...", "0"):
            options.append(f"--display-id={display_id_str}")
        elif stream.display > 0 and display_id_str is None:
            options.append(f"--display-id={stream.display}")

        if stream.new_display:
            options.append("--new-display")
            if stream.flex_display:
                options.append("--flex-display")
            if 0 < stream.display_ime_policy < len(IME_POLICIES):
                ime_pol = IME_POLICIES[stream.display_ime_policy]
                options.append(f"--display-ime-policy={ime_pol}")
            if stream.no_vd_destroy_content:
                options.append("--no-vd-destroy-content")

    # Start Specific App
    app_val = str(stream.start_app).strip()
    if app_val:
        options.append(f"--start-app={app_val}")

    # 2. Window Settings
    if stream.fullscreen:
        options.append("--fullscreen")
    if stream.borderless:
        options.append("--window-borderless")
    if stream.always_on_top:
        options.append("--always-on-top")
    if stream.disable_screensaver:
        options.append("--disable-screensaver")

    if 0 < stream.render_fit < len(RENDER_FITS):
        r_fit = RENDER_FITS[stream.render_fit]
        options.append(f"--render-fit={r_fit}")

    # 3. Video Settings
    if 0 < stream.codec < len(VIDEO_CODECS):
        codec = VIDEO_CODECS[stream.codec]
        options.append(f"--video-codec={codec}")

    fps_str = str(stream.fps).strip()
    if fps_str and fps_str != "Default":
        options.append(f"--max-fps={fps_str}")

    size_str = str(stream.size).strip()
    if size_str and size_str != "Default":
        matches = re.findall(r'(\d+)', size_str)
        if matches:
            max_val = max(int(m) for m in matches)
            options.append(f"--max-size={max_val}")
    elif stream.type == 1:
        # Camera mode requires default max-size for reliable initialization
        options.append("--max-size=1920")

    bitrate = str(stream.bitrate).strip()
    if bitrate:
        if bitrate.isdigit():
            options.append(f"--video-bit-rate={bitrate}M")
        else:
            options.append(f"--video-bit-rate={bitrate}")

    if 0 < stream.orientation < len(ORIENTATIONS):
        orient = ORIENTATIONS[stream.orientation]
        options.append(f"--orientation={orient}")

    # 4. Recording Settings
    if stream.record:
        rec_dir = record_dir or DEFAULT_RECORDINGS_DIR
        try:
            os.makedirs(rec_dir, exist_ok=True)
        except Exception:
            rec_dir = "/tmp"
        fmt = "mp4" if stream.record_format == 0 else "mkv"
        rec_path = os.path.join(rec_dir, f"andy_{int(time.time())}.{fmt}")
        options.append(f"--record={rec_path}")
        options.append(f"--record-format={fmt}")

    # 5. Advanced Settings
    options.extend(build_advanced_args(advanced))

    return options


def build_advanced_args(advanced: AdvancedConfig) -> List[str]:
    """
    Constructs CLI options from AdvancedConfig.
    """
    options: List[str] = []

    # Audio Settings
    if not advanced.no_audio:
        if 0 < advanced.audio_codec < len(AUDIO_CODECS):
            codec = AUDIO_CODECS[advanced.audio_codec]
            options.append(f"--audio-codec={codec}")

        if advanced.audio_dup:
            options.append("--audio-dup")

        if advanced.audio_source > 0:
            sources = [
                "output", "playback", "mic", "mic-unprocessed",
                "mic-camcorder", "mic-voice-recognition", "mic-voice-communication"
            ]
            if advanced.audio_source - 1 < len(sources):
                src_val = sources[advanced.audio_source - 1]
                options.append(f"--audio-source={src_val}")

        audio_br = str(advanced.audio_bitrate).strip()
        if audio_br:
            if audio_br.isdigit():
                options.append(f"--audio-bit-rate={audio_br}K")
            else:
                options.append(f"--audio-bit-rate={audio_br}")

        if 0 < advanced.audio_buffer < len(AUDIO_BUFFERS):
            match = re.search(r'(\d+)', AUDIO_BUFFERS[advanced.audio_buffer])
            if match:
                options.append(f"--audio-buffer={match.group(1)}")

    # Performance Settings
    if 0 < advanced.hwdec < len(HWDEC_OPTIONS):
        hw_val = "vaapi" if advanced.hwdec == 1 else "disabled"
        options.append(f"--hwdec={hw_val}")

    if advanced.no_downsize_on_error:
        options.append("--no-downsize-on-error")

    if 0 < advanced.render_driver < len(RENDER_DRIVERS):
        driver = RENDER_DRIVERS[advanced.render_driver]
        options.append(f"--render-driver={driver}")

    if 0 < advanced.buffer < len(BUFFER_PRESETS):
        buffer_str = BUFFER_PRESETS[advanced.buffer]
        match = re.search(r'(\d+)', buffer_str)
        if match:
            options.append(f"--video-buffer={match.group(1)}")

    if advanced.print_fps:
        options.append("--print-fps")

    # Device Parameters
    if advanced.screen_off:
        options.append("--turn-screen-off")
    if advanced.stay_awake:
        options.append("--stay-awake")
    if advanced.no_audio:
        options.append("--no-audio")
    if advanced.read_only:
        options.append("--no-control")
    if advanced.keyboard_uhid:
        options.append("--keyboard=uhid")
    if advanced.mouse_uhid:
        options.append("--mouse=uhid")
    if advanced.gamepad_uhid:
        options.append("--gamepad=uhid")

    if advanced.mouse_bind == 1:
        options.append("--mouse-bind=++++:++++")
    elif advanced.mouse_bind == 2:
        options.append("--mouse-bind=bhsn:++++")
    elif advanced.mouse_bind == 3:
        options.append("--mouse-bind=++++:bhsn")

    if advanced.legacy_paste:
        options.append("--legacy-paste")
    if advanced.no_clipboard_autosync:
        options.append("--no-clipboard-autosync")
    if advanced.power_off_on_close:
        options.append("--power-off-on-close")
    if advanced.no_power_on:
        options.append("--no-power-on")

    time_limit_val = str(advanced.time_limit).strip()
    if time_limit_val:
        options.append(f"--time-limit={time_limit_val}")

    if advanced.show_touches:
        options.append("--show-touches")
    if advanced.keep_active:
        options.append("--keep-active")

    if 0 < advanced.timeout < len(TIMEOUT_PRESETS):
        sec_list = ["10", "30", "60", "120", "300"]
        if advanced.timeout - 1 < len(sec_list):
            options.append(f"--screen-off-timeout={sec_list[advanced.timeout - 1]}")

    return options


def build_environment_overrides(advanced: AdvancedConfig) -> Dict[str, str]:
    """
    Builds environment variable overrides for GPU PRIME offloading and window backends.
    """
    overrides: Dict[str, str] = {}

    # Window backend: 0 = Wayland, 1 = XWayland (X11), 2 = Auto
    if advanced.backend == 0:
        overrides["SDL_VIDEODRIVER"] = "wayland"
    elif advanced.backend == 1:
        overrides["SDL_VIDEODRIVER"] = "x11"
    elif advanced.backend == 2:
        overrides["SDL_VIDEODRIVER"] = ""

    # GPU Adapter: 0 = Auto, 1 = NVIDIA PRIME offload, 2 = Integrated AMD/Intel
    if advanced.gpu_adapter == 1:
        overrides["__NV_PRIME_RENDER_OFFLOAD"] = "1"
        overrides["__GLX_VENDOR_LIBRARY_NAME"] = "nvidia"
        overrides["__VK_LAYER_NV_optimus"] = "NVIDIA_only"
    elif advanced.gpu_adapter == 2:
        overrides["DRI_PRIME"] = "0"
        overrides["__NV_PRIME_RENDER_OFFLOAD"] = "0"

    return overrides
