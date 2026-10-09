from core.models import StreamConfig, AdvancedConfig, DeviceInfo

def get_sample_stream_config() -> StreamConfig:
    return StreamConfig(
        type=0,
        camera=0,
        display=0,
        fullscreen=True,
        borderless=False,
        always_on_top=True,
        disable_screensaver=True,
        codec=1,  # h264
        fps="60",
        size="1920",
        bitrate="16",
        orientation=0,
        record=False,
        record_format=0,
        new_display=False,
        camera_torch=False
    )

def get_sample_advanced_config() -> AdvancedConfig:
    return AdvancedConfig(
        audio_codec=1,  # opus
        audio_dup=True,
        audio_source=2, # playback
        gpu_adapter=1,  # NVIDIA PRIME
        render_driver=1,# opengl
        backend=0,      # Wayland
        buffer=2,       # 20ms
        print_fps=True,
        screen_off=True,
        stay_awake=True,
        no_audio=False,
        read_only=False,
        keyboard_uhid=True,
        mouse_uhid=True,
        show_touches=True,
        keep_active=True,
        timeout=2       # 30s
    )

def get_sample_device_info() -> DeviceInfo:
    return DeviceInfo(
        serial="emulator-5554",
        model="Nothing Phone (2a)",
        version="Android 16 (API 36)",
        resolution="1084x2412",
        aspect_ratio="20:9 (Portrait)",
        battery="85% ⚡ (Charging)",
        battery_level=85,
        battery_charging=True,
        density="400 DPI (Override)",
        density_val=400,
        connection="USB"
    )
