import os
import re
from typing import Dict

def get_host_telemetry() -> Dict[str, str]:
    """
    Detects host Wayland compositor and primary GPU adapters.
    """
    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "")
    session_type = os.environ.get("XDG_SESSION_TYPE", "")
    wayland_display = os.environ.get("WAYLAND_DISPLAY", "")

    compositor = "Wayland"
    if desktop:
        compositor = f"Wayland ({desktop})"
    elif wayland_display:
        compositor = f"Wayland ({wayland_display})"
    elif session_type:
        compositor = f"{session_type.capitalize()}"

    gpu_desc = "Auto (Mesa / DRI)"
    try:
        cards = [f for f in os.listdir("/sys/class/drm") if f.startswith("card") and "-" not in f]
        gpus = []
        for card in cards:
            uevent_path = f"/sys/class/drm/{card}/device/uevent"
            if os.path.exists(uevent_path):
                with open(uevent_path, "r") as f:
                    content = f.read()
                    m = re.search(r"DRIVER=(\w+)", content)
                    if m:
                        driver = m.group(1).lower()
                        if "nvidia" in driver:
                            gpus.append("NVIDIA dGPU")
                        elif "amdgpu" in driver or "radeon" in driver:
                            gpus.append("AMD iGPU" if len(cards) > 1 else "AMD GPU")
                        elif "i915" in driver or "xe" in driver:
                            gpus.append("Intel iGPU" if len(cards) > 1 else "Intel GPU")
                        elif driver not in gpus:
                            gpus.append(driver.capitalize())
        if gpus:
            gpu_desc = " + ".join(dict.fromkeys(gpus))
    except Exception:
        pass

    return {
        "compositor": compositor,
        "gpu": gpu_desc
    }
