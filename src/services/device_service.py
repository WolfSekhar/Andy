import os
import subprocess
import re
from typing import List, Dict, Optional, Tuple, Any

def get_connected_devices() -> List[Dict[str, str]]:
    """
    Returns a list of dictionaries containing device information.
    Example: [{'serial': '...', 'model': '...', 'display_name': '...'}]
    """
    try:
        result = subprocess.run(['adb', 'devices', '-l'], capture_output=True, text=True, check=True, timeout=4)
        lines = result.stdout.strip().split('\n')
        devices = []
        for line in lines[1:]:
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            serial = parts[0]
            status = parts[1]
            if status != 'device':
                continue

            model = "Unknown Device"
            model_match = re.search(r'model:(\S+)', line)
            if model_match:
                model = model_match.group(1).replace('_', ' ')

            devices.append({
                'serial': serial,
                'model': model,
                'display_name': f"{model} ({serial})"
            })
        return devices
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return []

def get_detailed_device_info(serial: Optional[str]) -> Dict[str, Any]:
    """
    Fetches detailed hardware and status info for a specific device serial.
    """
    info: Dict[str, Any] = {
        'model': 'N/A',
        'version': 'N/A',
        'resolution': 'N/A',
        'battery': 'N/A',
        'aspect_ratio': 'N/A',
        'connection': 'N/A',
        'density': 'N/A',
        'density_val': None,
        'battery_level': None,
        'battery_charging': False
    }

    if not serial or serial == "No devices found":
        return info

    def run_adb(args):
        try:
            cmd = ['adb', '-s', serial] + args
            return subprocess.run(cmd, capture_output=True, text=True, timeout=3).stdout.strip()
        except Exception:
            return "N/A"

    # Connection type
    if ":" in serial or (serial.replace('.', '').isdigit() and '.' in serial):
        info['connection'] = "Wi-Fi (TCP/IP)"
    else:
        info['connection'] = "USB"

    # Model
    model = run_adb(['shell', 'getprop', 'ro.product.model'])
    info['model'] = model if model != "N/A" else "Unknown Model"

    # Android Version & SDK
    ver = run_adb(['shell', 'getprop', 'ro.build.version.release'])
    sdk = run_adb(['shell', 'getprop', 'ro.build.version.sdk'])
    if ver != "N/A":
        info['version'] = f"Android {ver}" + (f" (API {sdk})" if sdk != "N/A" else "")
    else:
        info['version'] = "N/A"

    # Resolution & Aspect Ratio
    res_output = run_adb(['shell', 'wm', 'size'])
    if "Physical size:" in res_output:
        res_str = res_output.split(":")[-1].strip()
        info['resolution'] = res_str
        dims = res_str.split('x')
        if len(dims) == 2 and dims[0].isdigit() and dims[1].isdigit():
            w, h = int(dims[0]), int(dims[1])
            is_portrait = h > w
            long_edge = max(w, h)
            short_edge = min(w, h)
            ratio = round(long_edge / short_edge, 2)
            ratio_label = ""
            if 1.76 <= ratio <= 1.80: ratio_label = "16:9"
            elif 1.98 <= ratio <= 2.02: ratio_label = "18:9"
            elif 2.14 <= ratio <= 2.18: ratio_label = "19.5:9"
            elif 2.20 <= ratio <= 2.24: ratio_label = "20:9"
            elif 2.30 <= ratio <= 2.35: ratio_label = "21:9"
            elif 1.30 <= ratio <= 1.35: ratio_label = "4:3"
            else: ratio_label = f"{ratio}:1"

            orient = "Portrait" if is_portrait else "Landscape"
            info['aspect_ratio'] = f"{ratio_label} ({orient})"

    # Battery
    batt_output = run_adb(['shell', 'dumpsys', 'battery'])
    level = None
    charging = False
    for line in batt_output.split('\n'):
        if "level:" in line:
            val = line.split(':')[-1].strip()
            if val.isdigit():
                level = int(val)
        if "status:" in line:
            status_val = line.split(':')[-1].strip()
            if status_val in ("2", "5"):
                charging = True
        if "AC powered: true" in line or "USB powered: true" in line or "Wireless powered: true" in line:
            charging = True

    if level is not None:
        info['battery_level'] = level
        info['battery_charging'] = charging
        info['battery'] = f"{level}%" + (" ⚡ (Charging)" if charging else "")

    # Density
    d_info = get_device_density(serial)
    if d_info.get('current'):
        info['density_val'] = d_info['current']
        info['density'] = f"{d_info['current']} DPI" + (" (Override)" if d_info.get('override') else "")

    return info

def get_device_density(serial: Optional[str]) -> Dict[str, Optional[int]]:
    """
    Returns dict with physical and override density for device:
    {'physical': 420, 'override': 480, 'current': 480}
    """
    res = {'physical': None, 'override': None, 'current': None}
    if not serial or serial == "No devices found":
        return res
    try:
        cmd = ['adb', '-s', serial, 'shell', 'wm', 'density']
        out = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=3).stdout
        for line in out.splitlines():
            if "Physical density:" in line:
                m = re.search(r'(\d+)', line)
                if m: res['physical'] = int(m.group(1))
            elif "Override density:" in line:
                m = re.search(r'(\d+)', line)
                if m: res['override'] = int(m.group(1))
        res['current'] = res['override'] if res['override'] is not None else res['physical']
        return res
    except Exception:
        return res

def get_device_displays(serial: Optional[str]) -> List[str]:
    """
    Executes scrcpy --list-displays and parses the output to find display IDs.
    """
    if not serial or serial == "No devices found":
        return []
    try:
        result = subprocess.run(
            ['scrcpy', '-s', serial, '--list-displays'],
            capture_output=True, text=True, timeout=4
        )
        output = result.stdout + result.stderr
        pattern = r'(?:--)?display[_-]id=(\d+)'
        matches = re.findall(pattern, output)
        if matches:
            return sorted(set(matches))
        return []
    except Exception:
        return []

def get_device_cameras(serial: Optional[str]) -> List[Dict[str, str]]:
    """
    Executes scrcpy --list-cameras and parses the output to find camera IDs and descriptions.
    """
    if not serial or serial == "No devices found":
        return []
    try:
        result = subprocess.run(
            ['scrcpy', '-s', serial, '--list-cameras'],
            capture_output=True, text=True, timeout=4
        )
        output = result.stdout + result.stderr
        cameras = []
        pattern = r'--camera-id=(\d+)\s*\(([^,]+),\s*([^,)]+)'
        matches = re.findall(pattern, output)
        for match in matches:
            cameras.append({
                'id': match[0],
                'desc': f"{match[0]} ({match[1]}, {match[2]})"
            })
        return cameras
    except Exception:
        return []

def get_device_resolution(serial: Optional[str]) -> Optional[Tuple[int, int, bool]]:
    """
    Fetches the native resolution and current orientation of the device.
    Returns (width, height, is_portrait)
    """
    if not serial or serial == "No devices found":
        return None
    try:
        res_result = subprocess.run(['adb', '-s', serial, 'shell', 'wm', 'size'], capture_output=True, text=True, timeout=3)
        matches = re.findall(r'(\d+)x(\d+)', res_result.stdout)
        if not matches:
            return None
        native_w, native_h = int(matches[-1][0]), int(matches[-1][1])

        # Check dumpsys display
        rect_result = subprocess.run(
            ['adb', '-s', serial, 'shell', 'dumpsys display | grep -E "mCurrentDisplayRect|mDisplayRect|mCurrentOrientation"'],
            capture_output=True, text=True, timeout=3
        )
        match = re.search(r'Rect\(\d+,\s*\d+\s*[-,\s]+\s*(\d+),\s*(\d+)\)', rect_result.stdout)
        if match:
            current_w, current_h = int(match.group(1)), int(match.group(2))
            is_portrait = current_h > current_w
            if is_portrait:
                return (min(native_w, native_h), max(native_w, native_h), True)
            else:
                return (max(native_w, native_h), min(native_w, native_h), False)

        # Fallback: check rotation via dumpsys window
        rot_result = subprocess.run(
            ['adb', '-s', serial, 'shell', 'dumpsys window | grep -E "mCurrentRotation|rotation"'],
            capture_output=True, text=True, timeout=3
        )
        rot_match = re.search(r'(?:mCurrentRotation|rotation)=(\d)', rot_result.stdout)
        if rot_match:
            rot = int(rot_match.group(1))
            is_rotated = (rot in (1, 3))
            base_portrait = native_h > native_w
            is_portrait = not base_portrait if is_rotated else base_portrait
            if is_portrait:
                return (min(native_w, native_h), max(native_w, native_h), True)
            else:
                return (max(native_w, native_h), min(native_w, native_h), False)

        return (native_w, native_h, native_h > native_w)
    except Exception:
        return None
