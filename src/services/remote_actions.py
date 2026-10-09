import os
import time
import subprocess
from typing import Tuple, Optional
from core.config import DEFAULT_SCREENSHOTS_DIR

def take_device_screenshot(serial: Optional[str], destination_dir: Optional[str] = None) -> Tuple[bool, str]:
    """
    Captures device screen via ADB screencap and saves to destination_dir.
    """
    if not serial or serial == "No devices found":
        return False, "No device connected"

    dest_dir = destination_dir or DEFAULT_SCREENSHOTS_DIR
    try:
        os.makedirs(dest_dir, exist_ok=True)
    except Exception:
        dest_dir = "/tmp"

    filename = f"andy_{int(time.time())}.png"
    filepath = os.path.join(dest_dir, filename)

    try:
        cmd = ['adb', '-s', serial, 'exec-out', 'screencap', '-p']
        with open(filepath, 'wb') as f:
            subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, check=True, timeout=8)
        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            return True, filepath
        else:
            return False, "Empty screenshot captured"
    except Exception as e:
        return False, str(e)

def toggle_device_screen(serial: Optional[str]) -> Tuple[bool, str]:
    """
    Toggles device screen power (Keyevent 26).
    """
    if not serial or serial == "No devices found":
        return False, "No device connected"
    try:
        cmd = ['adb', '-s', serial, 'shell', 'input', 'keyevent', '26']
        subprocess.run(cmd, capture_output=True, check=True, timeout=3)
        return True, "Screen toggled"
    except Exception as e:
        return False, str(e)

def adjust_device_volume(serial: Optional[str], direction: str = "up") -> Tuple[bool, str]:
    """
    Adjusts device volume (Keyevent 24 for Up, 25 for Down).
    """
    if not serial or serial == "No devices found":
        return False, "No device connected"
    keycode = '24' if direction == "up" else '25'
    try:
        cmd = ['adb', '-s', serial, 'shell', 'input', 'keyevent', keycode]
        subprocess.run(cmd, capture_output=True, check=True, timeout=3)
        return True, f"Volume {direction}"
    except Exception as e:
        return False, str(e)

def send_keyevent(serial: Optional[str], keycode: int) -> Tuple[bool, str]:
    """
    Sends a keyevent to the device (e.g. 3 for Home, 4 for Back, 187 for App Switcher).
    """
    if not serial or serial == "No devices found":
        return False, "No device connected"
    try:
        cmd = ['adb', '-s', serial, 'shell', 'input', 'keyevent', str(keycode)]
        subprocess.run(cmd, capture_output=True, check=True, timeout=3)
        return True, f"Keyevent {keycode} sent"
    except Exception as e:
        return False, str(e)

def expand_statusbar(serial: Optional[str], target: str = "notifications") -> Tuple[bool, str]:
    """
    Expands or collapses the Android status bar.
    target can be: 'notifications', 'settings', or 'collapse'.
    """
    if not serial or serial == "No devices found":
        return False, "No device connected"
    action = f"expand-{target}" if target in ("notifications", "settings") else "collapse"
    try:
        cmd = ['adb', '-s', serial, 'shell', 'cmd', 'statusbar', action]
        subprocess.run(cmd, capture_output=True, check=True, timeout=3)
        return True, f"Statusbar {action}"
    except Exception as e:
        return False, str(e)

def inject_clipboard_text(serial: Optional[str], text: str) -> Tuple[bool, str]:
    """
    Injects text into the active Android input field.
    """
    if not serial or serial == "No devices found":
        return False, "No device connected"
    if not text:
        return False, "Clipboard is empty"
    escaped = text.replace('\\', '\\\\').replace('"', '\\"').replace(' ', '%s').replace('&', '\\&').replace(';', '\\;')
    try:
        cmd = ['adb', '-s', serial, 'shell', 'input', 'text', escaped]
        subprocess.run(cmd, capture_output=True, check=True, timeout=4)
        return True, "Clipboard text injected"
    except Exception as e:
        return False, str(e)

def set_device_density(serial: Optional[str], density: int) -> Tuple[bool, str]:
    """
    Sets device display density via wm density.
    """
    if not serial or serial == "No devices found":
        return False, "No device connected"
    try:
        cmd = ['adb', '-s', serial, 'shell', 'wm', 'density', str(density)]
        subprocess.run(cmd, capture_output=True, check=True, timeout=3)
        return True, f"Density set to {density}"
    except Exception as e:
        return False, str(e)

def reset_device_density(serial: Optional[str]) -> Tuple[bool, str]:
    """
    Resets device display density to physical default via wm density reset.
    """
    if not serial or serial == "No devices found":
        return False, "No device connected"
    try:
        cmd = ['adb', '-s', serial, 'shell', 'wm', 'density', 'reset']
        subprocess.run(cmd, capture_output=True, check=True, timeout=3)
        return True, "Density reset"
    except Exception as e:
        return False, str(e)

def reboot_device(serial: Optional[str], mode: str = "normal") -> Tuple[bool, str]:
    """
    Reboots device: 'normal', 'recovery', or 'bootloader'.
    """
    if not serial or serial == "No devices found":
        return False, "No device connected"
    cmd = ['adb', '-s', serial, 'reboot']
    if mode in ("recovery", "bootloader"):
        cmd.append(mode)
    try:
        subprocess.run(cmd, capture_output=True, check=True, timeout=5)
        return True, f"Rebooting ({mode})..."
    except Exception as e:
        return False, str(e)

def toggle_show_touches(serial: Optional[str], enable: Optional[bool] = None) -> Tuple[bool, str]:
    """
    Toggles or sets the Android system show_touches setting.
    """
    if not serial or serial == "No devices found":
        return False, "No device connected"
    try:
        if enable is None:
            cmd = ['adb', '-s', serial, 'shell', 'settings', 'get', 'system', 'show_touches']
            val = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=3).stdout.strip()
            enable = (val != "1")
        val_str = "1" if enable else "0"
        cmd = ['adb', '-s', serial, 'shell', 'settings', 'put', 'system', 'show_touches', val_str]
        subprocess.run(cmd, capture_output=True, check=True, timeout=3)
        return True, f"Touches {'enabled' if enable else 'disabled'}"
    except Exception as e:
        return False, str(e)
