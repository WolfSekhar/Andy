"""
Compatibility Shim for profile_manager.
Re-exports profile management functions from services.profile_service.
"""
from services.profile_service import (
    ensure_profiles_dir,
    sanitize_filename,
    save_profile,
    load_profile,
    list_profiles,
    delete_profile,
    rename_profile
)

__all__ = [
    'ensure_profiles_dir',
    'sanitize_filename',
    'save_profile',
    'load_profile',
    'list_profiles',
    'delete_profile',
    'rename_profile'
]
