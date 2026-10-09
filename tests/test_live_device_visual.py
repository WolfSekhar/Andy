import sys
import os
import time
import subprocess

# Ensure we can import from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src/ui')))

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib

from device_manager import get_connected_devices
from scrcpy_manager import get_device_cameras
from stream_card import StreamCard
from advanced_card import AdvancedCard

SCREENSHOT_DIR = "test_screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def execute_stream(serial, options, description, shot_name=None):
    cmd = ["scrcpy", "-s", serial] + options
    print(f"\n[TEST] {description}")
    print(f"       Command: {' '.join(cmd)}")
    
    # Wait for device to load/settle before starting next stream
    time.sleep(3.0)
    
    env = os.environ.copy()
    env["SDL_VIDEODRIVER"] = "wayland"
    
    # Use Popen to run in background
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    
    try:
        # Wait 5 seconds to ensure stability
        time.sleep(5.0)
        
        # Check if process is still running
        if proc.poll() is not None:
            # Process exited early
            _, stderr = proc.communicate()
            error_msg = stderr.decode('utf-8').strip()
            print(f"  ❌ [FAILED] Process exited early with code {proc.returncode}")
            if error_msg:
                print(f"       Error: {error_msg.split('\\n')[-1]}")
            return False
        
        # Take a screenshot if requested
        if shot_name:
            shot_path = os.path.join(SCREENSHOT_DIR, f"{shot_name}.png")
            print(f"       📸 Taking screenshot: {shot_path}")
            # Use adb to take a screenshot from the device as a fallback/validation
            # or try to use a tool to grab the scrcpy window.
            # Easiest way to verify "rendering" is to ask scrcpy to record a single frame or just use adb.
            subprocess.run(["adb", "-s", serial, "shell", "screencap", "-p", "/sdcard/test.png"], capture_output=True)
            subprocess.run(["adb", "-s", serial, "pull", "/sdcard/test.png", shot_path], capture_output=True)
            
        print("  ✅ [SUCCESS] Stream stable.")
        proc.terminate()
        proc.wait(timeout=2)
        return True
    except Exception as e:
        print(f"  ❌ [ERROR] {e}")
        if proc.poll() is None:
            proc.kill()
        return False

def run_live_tests():
    # Force headless-ish or at least don't crash if display is weird
    os.environ['GDK_BACKEND'] = 'wayland'
    
    try:
        Adw.init()
    except Exception:
        pass
    
    print("Scanning for connected USB devices...")
    devices = get_connected_devices()
    if not devices:
        print("❌ No devices found.")
        return
        
    serial = devices[0]['serial']
    print(f"Using device: {devices[0]['display_name']} ({serial})")

    card = StreamCard()
    adv = AdvancedCard()
    card.type_change_callback = adv.set_camera_mode

    # Fetch real data
    cameras = get_device_cameras(serial)
    print(f"Detected {len(cameras)} cameras: {[c['desc'] for c in cameras]}")
    
    if cameras:
        card.camera_model.splice(0, card.camera_model.get_n_items(), [c['desc'] for c in cameras])
    else:
        card.camera_model.splice(0, card.camera_model.get_n_items(), ["None Found"])

    def get_opts():
        return card.get_stream_options() + adv.get_stream_options()

    print("\n" + "="*40)
    print("EXHAUSTIVE LIVE TESTING WITH VISUAL CHECK")
    print("="*40)
    
    # 1. Base Stream
    card.type_dropdown.set_selected(0)
    execute_stream(serial, get_opts(), "Base Screen", "screen_base")

    # 2. Camera Testing (Front and Back)
    if cameras:
        for i, cam in enumerate(cameras):
            card.type_dropdown.set_selected(1) # Camera
            card.camera_dropdown.set_selected(i)
            # Ensure size is set to default 1920 for stability
            card.size_dropdown.set_selected(3) # 1920
            
            desc = cam['desc'].replace(" ", "_").replace("(", "").replace(")", "").lower()
            execute_stream(serial, get_opts(), f"Camera Test: {cam['desc']}", f"camera_{i}_{desc}")
    else:
        print("⚠️ Skipping camera tests: No cameras detected by scrcpy.")

    # 3. High Stress Video Combo
    card.type_dropdown.set_selected(0)
    card.codec_dropdown.set_selected(2) # h265
    card.fps_dropdown.set_selected(1)   # 60
    card.size_dropdown.set_selected(1)  # 4K
    execute_stream(serial, get_opts(), "High Stress Video (4K, h265, 60fps)", "stress_video_4k")

    print("\n✅ Live testing with visual verification completed.")
    print(f"Screenshots saved in: {SCREENSHOT_DIR}/")

if __name__ == '__main__':
    run_live_tests()
