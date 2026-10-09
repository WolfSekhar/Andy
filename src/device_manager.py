"""
Compatibility Shim for device_manager.
Re-exports device discovery, host telemetry, and remote actions from services.
"""
from services.device_service import (
    get_connected_devices,
    get_detailed_device_info,
    get_device_density
)
from services.host_telemetry import get_host_telemetry
from services.remote_actions import (
    take_device_screenshot,
    toggle_device_screen,
    adjust_device_volume,
    send_keyevent,
    expand_statusbar,
    inject_clipboard_text,
    set_device_density,
    reset_device_density,
    reboot_device,
    toggle_show_touches
)

__all__ = [
    'get_connected_devices',
    'get_detailed_device_info',
    'get_device_density',
    'get_host_telemetry',
    'take_device_screenshot',
    'toggle_device_screen',
    'adjust_device_volume',
    'send_keyevent',
    'expand_statusbar',
    'inject_clipboard_text',
    'set_device_density',
    'reset_device_density',
    'reboot_device',
    'toggle_show_touches'
]
