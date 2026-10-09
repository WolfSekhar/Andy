import os

APP_ID = 'com.wolfsekhar.Andy'
APP_NAME = 'Andy'
VERSION = '1.2.0'

# Standard directory paths & FreeDesktop XDG Base Directory Specification
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LEGACY_DATA_DIR = os.path.join(ROOT_DIR, 'data')

XDG_CONFIG_HOME = os.environ.get('XDG_CONFIG_HOME') or os.path.expanduser('~/.config')
XDG_DATA_HOME = os.environ.get('XDG_DATA_HOME') or os.path.expanduser('~/.local/share')
XDG_CACHE_HOME = os.environ.get('XDG_CACHE_HOME') or os.path.expanduser('~/.cache')

# Use local repo data when ANDY_LOCAL_DATA=1 (e.g. tests/isolated development), otherwise XDG standard
if os.environ.get('ANDY_LOCAL_DATA') == '1':
    DATA_DIR = LEGACY_DATA_DIR
else:
    DATA_DIR = os.path.join(XDG_CONFIG_HOME, 'andy')

PROFILES_DIR = os.path.join(DATA_DIR, 'profiles')
SETTINGS_FILE = os.path.join(DATA_DIR, 'settings.json')
ASSETS_DIR = os.path.join(ROOT_DIR, 'assets')
CACHE_DIR = os.path.join(XDG_CACHE_HOME, 'andy')
DEFAULT_RECORDINGS_DIR = os.path.expanduser('~/Videos/Andy')
DEFAULT_SCREENSHOTS_DIR = os.path.expanduser('~/Pictures/Andy')

# Presets and options
VIDEO_CODECS = ["Default", "h264", "h265", "av1"]
FPS_PRESETS = ["Default", "60", "30", "15"]
ORIENTATIONS = ["Default", "0", "90", "180", "270"]
RENDER_FITS = ["Default", "letterbox", "stretched", "unscaled"]
IME_POLICIES = ["Default", "local", "fallback", "hide"]
CAMERA_FPS_PRESETS = ["Default", "30", "20", "15", "10"]

AUDIO_CODECS = ["Default", "opus", "aac", "flac", "raw"]
AUDIO_SOURCES = [
    "Default",
    "output (Device Audio)",
    "playback (Apps Only)",
    "mic (Device Mic)",
    "mic-unprocessed",
    "mic-camcorder",
    "mic-voice-recognition",
    "mic-voice-communication"
]
AUDIO_BUFFERS = ["Default", "20 ms", "40 ms", "50 ms", "100 ms"]
AUDIO_BUFFER_PRESETS = AUDIO_BUFFERS

GPU_ADAPTERS = ["Default (Auto)", "Discrete (NVIDIA PRIME)", "Integrated (AMD / Intel)"]
RENDER_DRIVERS = ["Default", "opengl", "opengles2", "software"]
WINDOW_BACKENDS = ["Wayland (Native)", "XWayland (X11)", "Auto"]
HWDEC_OPTIONS = ["Default (Auto)", "vaapi (Hardware)", "disabled (Software)"]

BUFFER_PRESETS = ["Default", "0 ms", "20 ms", "30 ms", "50 ms", "100 ms", "250 ms"]
TIMEOUT_PRESETS = ["Default", "10s", "30s", "60s", "120s", "300s"]
MOUSE_BIND_PRESETS = [
    "Default",
    "Forward Clicks (Gaming: ++++:++++)",
    "Android Actions (bhsn:++++)",
    "Shortcuts on Shift (++++:bhsn)"
]

UI_SCALE_STEPS = [0.75, 0.85, 0.90, 1.0, 1.10, 1.25, 1.40, 1.50]
