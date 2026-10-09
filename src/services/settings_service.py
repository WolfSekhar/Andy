import os
import json
from typing import Dict, Any, Optional
from core.config import DATA_DIR, SETTINGS_FILE, LEGACY_DATA_DIR

DEFAULT_LAYOUT: str = "classic"

DEFAULT_SETTINGS: Dict[str, Any] = {
    "theme": "default",
    "ui_scale": 1.0,
    "active_layout": DEFAULT_LAYOUT,
}

def load_settings() -> Dict[str, Any]:
    try:
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR, exist_ok=True)
    except OSError:
        pass

    defaults = {
        "theme": "default",
        "ui_scale": 1.0,
        "active_layout": DEFAULT_LAYOUT,
    }

    # Seamless migration from legacy repository data directory
    if not os.path.exists(SETTINGS_FILE) and os.path.exists(LEGACY_DATA_DIR):
        legacy_file = os.path.join(LEGACY_DATA_DIR, 'settings.json')
        if os.path.exists(legacy_file):
            try:
                with open(legacy_file, 'r') as f:
                    legacy_data = json.load(f)
                    defaults.update(legacy_data)
                save_settings(defaults)
                return defaults
            except Exception:
                pass

    if not os.path.exists(SETTINGS_FILE):
        return defaults

    try:
        with open(SETTINGS_FILE, 'r') as f:
            data = json.load(f)
            defaults.update(data)
            return defaults
    except (json.JSONDecodeError, IOError):
        return defaults

def save_settings(settings: Dict[str, Any]):
    try:
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR, exist_ok=True)
    except OSError:
        pass

    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=4)
    except IOError:
        pass

def get_setting(key: str, default: Any = None) -> Any:
    settings = load_settings()
    return settings.get(key, default)

def set_setting(key: str, value: Any):
    settings = load_settings()
    settings[key] = value
    save_settings(settings)
