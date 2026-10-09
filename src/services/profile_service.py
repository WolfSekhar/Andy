import os
import json
import shutil
from typing import List, Optional, Dict, Any
from core.config import DATA_DIR, PROFILES_DIR

def ensure_profiles_dir():
    """
    Ensures the profiles directory exists and migrates any legacy profile files
    from DATA_DIR to PROFILES_DIR (excluding settings.json).
    """
    try:
        if not os.path.exists(PROFILES_DIR):
            os.makedirs(PROFILES_DIR, exist_ok=True)
    except OSError:
        return

    if os.path.exists(DATA_DIR) and os.path.exists(PROFILES_DIR):
        try:
            for item in os.listdir(DATA_DIR):
                item_path = os.path.join(DATA_DIR, item)
                if os.path.isfile(item_path) and item.endswith('.json') and item != 'settings.json':
                    dest_path = os.path.join(PROFILES_DIR, item)
                    if not os.path.exists(dest_path):
                        shutil.move(item_path, dest_path)
        except OSError:
            pass

def sanitize_filename(name: str) -> str:
    """
    Prevents path traversal by returning only the filename component.
    """
    return os.path.basename(name)

def save_profile(name: str, state: Dict[str, Any]):
    ensure_profiles_dir()
    safe_name = sanitize_filename(name)
    if not safe_name or safe_name == "settings":
        return

    target_dir = PROFILES_DIR if os.path.exists(PROFILES_DIR) else DATA_DIR
    file_path = os.path.join(target_dir, f"{safe_name}.json")
    try:
        with open(file_path, 'w') as f:
            json.dump(state, f, indent=4)
    except OSError:
        pass

def load_profile(name: str) -> Optional[Dict[str, Any]]:
    ensure_profiles_dir()
    safe_name = sanitize_filename(name)
    if not safe_name or safe_name == "settings":
        return None

    file_path = os.path.join(PROFILES_DIR, f"{safe_name}.json")
    if not os.path.exists(file_path):
        file_path = os.path.join(DATA_DIR, f"{safe_name}.json")
        if not os.path.exists(file_path):
            return None

    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None

def list_profiles() -> List[str]:
    ensure_profiles_dir()
    search_dir = PROFILES_DIR if os.path.exists(PROFILES_DIR) else DATA_DIR
    if not os.path.exists(search_dir):
        return []

    profiles = []
    try:
        for f in os.listdir(search_dir):
            if f.endswith('.json') and f != 'settings.json':
                profiles.append(f[:-5])
    except OSError:
        return []

    return sorted(profiles)

def delete_profile(name: str):
    ensure_profiles_dir()
    safe_name = sanitize_filename(name)
    if not safe_name or safe_name == "settings":
        return
    for d in (PROFILES_DIR, DATA_DIR):
        file_path = os.path.join(d, f"{safe_name}.json")
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except OSError:
            pass

def rename_profile(old_name: str, new_name: str):
    ensure_profiles_dir()
    old_safe = sanitize_filename(old_name)
    new_safe = sanitize_filename(new_name)
    if not old_safe or not new_safe or old_safe == "settings" or new_safe == "settings":
        return
    for d in (PROFILES_DIR, DATA_DIR):
        old_path = os.path.join(d, f"{old_safe}.json")
        new_path = os.path.join(d, f"{new_safe}.json")
        try:
            if os.path.exists(old_path):
                os.rename(old_path, new_path)
        except OSError:
            pass
