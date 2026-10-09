from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any

@dataclass
class StreamConfig:
    type: int = 0                  # 0: Screen, 1: Camera
    camera: int = 0
    display: int = 0
    fullscreen: bool = False
    borderless: bool = False
    always_on_top: bool = False
    disable_screensaver: bool = False
    codec: int = 0                 # 0: Default, 1: h264, 2: h265, 3: av1
    fps: str = "Default"
    size: str = "Default"
    bitrate: str = ""
    orientation: int = 0           # 0: Default, 1: 0, 2: 90, 3: 180, 4: 270
    record: bool = False
    record_format: int = 0         # 0: mp4, 1: mkv
    new_display: bool = False
    camera_torch: bool = False

    # scrcpy 5.0 additions
    flex_display: bool = False
    render_fit: int = 0            # 0: Default, 1: letterbox, 2: stretched, 3: unscaled
    display_ime_policy: int = 0    # 0: Default, 1: local, 2: fallback, 3: hide
    no_vd_destroy_content: bool = False
    start_app: str = ""
    camera_zoom: str = ""
    camera_fps: int = 0            # 0: Default, 1: 30, 2: 20, 3: 15, 4: 10
    camera_high_speed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> 'StreamConfig':
        if not data:
            return cls()
        fields = cls.__dataclass_fields__.keys()
        filtered = {k: v for k, v in data.items() if k in fields}
        # Handle legacy integer indices for fps/size
        if isinstance(filtered.get("fps"), int):
            fps_presets = ["Default", "60", "30", "15"]
            idx = filtered["fps"]
            filtered["fps"] = fps_presets[idx] if 0 <= idx < len(fps_presets) else "Default"
        if isinstance(filtered.get("size"), int):
            size_presets = ["Default", "3840", "2560", "1920", "1280", "1024"]
            idx = filtered["size"]
            filtered["size"] = size_presets[idx] if 0 <= idx < len(size_presets) else "Default"
        return cls(**filtered)


@dataclass
class AdvancedConfig:
    audio_codec: int = 0          # 0: Default, 1: opus, 2: aac, 3: flac, 4: raw
    audio_dup: bool = False
    audio_source: int = 0         # 0: Default, 1: output, 2: playback, 3: mic, 4: unprocessed...
    gpu_adapter: int = 0          # 0: Default, 1: NVIDIA PRIME, 2: Integrated
    render_driver: int = 0        # 0: Default, 1: opengl, 2: opengles2, 3: software
    backend: int = 0              # 0: Wayland, 1: X11, 2: Auto
    buffer: int = 0               # Index into buffer presets
    print_fps: bool = False
    screen_off: bool = False
    stay_awake: bool = False
    no_audio: bool = False
    read_only: bool = False
    keyboard_uhid: bool = False
    mouse_uhid: bool = False
    show_touches: bool = False
    keep_active: bool = False
    timeout: int = 0              # Index into timeout presets

    # scrcpy 5.0 additions
    hwdec: int = 0                # 0: Default, 1: vaapi, 2: disabled
    no_downsize_on_error: bool = False
    audio_bitrate: str = ""
    audio_buffer: int = 0         # Index into audio buffer presets
    gamepad_uhid: bool = False
    mouse_bind: int = 0           # 0: Default, 1: Gaming (+:++), 2: Android (bhsn:++), 3: Shift (++++:bhsn)
    legacy_paste: bool = False
    no_clipboard_autosync: bool = False
    power_off_on_close: bool = False
    no_power_on: bool = False
    time_limit: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> 'AdvancedConfig':
        if not data:
            return cls()
        fields = cls.__dataclass_fields__.keys()
        filtered = {k: v for k, v in data.items() if k in fields}
        return cls(**filtered)


@dataclass
class DeviceInfo:
    serial: str
    model: str = "Unknown Device"
    version: str = "N/A"
    resolution: str = "N/A"
    aspect_ratio: str = ""
    battery: str = "N/A"
    battery_level: Optional[int] = None
    battery_charging: bool = False
    density: str = "N/A"
    density_val: Optional[int] = None
    connection: str = "USB"
    display_name: str = ""

    def __post_init__(self):
        if not self.display_name:
            self.display_name = f"{self.model} ({self.serial})"
