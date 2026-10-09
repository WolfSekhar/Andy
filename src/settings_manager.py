"""
Compatibility Shim for settings_manager.
Re-exports settings management functions from services.settings_service.
"""
from services.settings_service import (
    load_settings,
    save_settings,
    get_setting,
    set_setting,
    DEFAULT_LAYOUT,
    DEFAULT_SETTINGS
)

__all__ = [
    'load_settings',
    'save_settings',
    'get_setting',
    'set_setting',
    'DEFAULT_LAYOUT',
    'DEFAULT_SETTINGS'
]
