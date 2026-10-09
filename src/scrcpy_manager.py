"""
Compatibility Shim for scrcpy_manager.
Re-exports device discovery from services.device_service and parser from core.scrcpy_parser.
"""
from core.scrcpy_parser import parse_scrcpy_params
from services.device_service import (
    get_device_displays,
    get_device_cameras,
    get_device_resolution
)

__all__ = [
    'get_device_displays',
    'get_device_cameras',
    'get_device_resolution',
    'parse_scrcpy_params'
]
