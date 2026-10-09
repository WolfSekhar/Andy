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

def execute_stream(serial, options, description):
    cmd = ["scrcpy", "-s", serial] + options
    print(f"\n[TEST] {description}")
    print(f"       Command: {' '.join(cmd)}")
    
    # Wait for device to load/settle before starting next stream
    time.sleep(3.0)
    
    env = os.environ.copy()
    # Enforce Wayland for the test process
    env["SDL_VIDEODRIVER"] = "wayland"
    
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    
    try:
        # Wait at least 5 seconds.
        proc.wait(timeout=5.0)
        # If it reached here, it exited early
        _, stderr = proc.communicate()
        error_msg = stderr.decode('utf-8').strip()
        print(f"  ❌ [FAILED] Process exited early with code {proc.returncode}")
        if error_msg:
            last_lines = error_msg.split('\n')[-3:]
            print(f"       Error: {' | '.join(last_lines)}")
        return False
    except subprocess.TimeoutExpired:
        # It's running stably
        print("  ✅ [SUCCESS] Stream stable.")
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except:
            proc.kill()
        return True

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
        print("❌ No devices found. Please connect a device via USB and authorize ADB.")
        return
        
    serial = devices[0]['serial']
    print(f"Using device: {devices[0]['display_name']} ({serial})")

    card = StreamCard()
    adv = AdvancedCard()
    card.type_change_callback = adv.set_camera_mode

    # Initialize models for testing
    card.display_model.splice(0, card.display_model.get_n_items(), ["0 (Default)"])
    card.display_dropdown.set_selected(0)
    
    cameras = get_device_cameras(serial)
    if cameras:
        card.camera_model.splice(0, card.camera_model.get_n_items(), [cam['desc'] for cam in cameras])
    else:
        card.camera_model.splice(0, card.camera_model.get_n_items(), ["0 (Fallback)"])
    card.camera_dropdown.set_selected(0)

    # Helper to clean UI state
    def reset_ui():
        card.type_dropdown.set_selected(0)
        card.param_fullscreen.set_active(False)
        card.param_borderless.set_active(False)
        card.param_always_on_top.set_active(False)
        card.param_disable_screensaver.set_active(False)
        card.codec_dropdown.set_selected(0)
        card.fps_dropdown.set_selected(0)
        card.size_dropdown.set_selected(0)
        card.bitrate_row.set_text("")
        card.orient_dropdown.set_selected(0)
        
        adv.audio_codec_dropdown.set_selected(0)
        adv.buffer_dropdown.set_selected(0)
        adv.param_screen_off.set_active(False)
        adv.param_stay_awake.set_active(False)
        adv.param_no_audio.set_active(False)
        adv.param_read_only.set_active(False)
        adv.param_keyboard_uhid.set_active(False)
        adv.param_mouse_uhid.set_active(False)

    def get_opts():
        return card.get_stream_options() + adv.get_stream_options()

    print("\n" + "="*40)
    print("PHASE 1: SCREEN MODE EXHAUSTIVE TESTING")
    print("="*40)
    
    # 1. Base Stream
    reset_ui()
    execute_stream(serial, get_opts(), "Base Screen Stream")

    # 2. Toggle Matrix
    toggles = [
        (card.param_fullscreen, "Fullscreen"),
        (card.param_borderless, "Borderless"),
        (card.param_disable_screensaver, "Disable Screensaver"),
        (adv.param_screen_off, "Turn Screen Off"),
        (adv.param_stay_awake, "Stay Awake"),
        (adv.param_no_audio, "No Audio"),
        (adv.param_keyboard_uhid, "Keyboard UHID"),
        (adv.param_mouse_uhid, "Mouse UHID")
    ]
    
    for widget, name in toggles:
        reset_ui()
        widget.set_active(True)
        execute_stream(serial, get_opts(), f"Toggle: {name}")

    # 3. Video Codec Matrix
    for i in range(1, card.codec_model.get_n_items()):
        reset_ui()
        card.codec_dropdown.set_selected(i)
        codec_name = card.codec_model.get_string(i)
        execute_stream(serial, get_opts(), f"Video Codec: {codec_name}")

    # 4. Max Size Matrix
    for i in range(1, card.size_model.get_n_items()):
        reset_ui()
        card.size_dropdown.set_selected(i)
        size_name = card.size_model.get_string(i)
        execute_stream(serial, get_opts(), f"Max Size: {size_name}")

    # 5. Audio Codec Matrix
    for i in range(1, adv.audio_codec_model.get_n_items()):
        reset_ui()
        adv.audio_codec_dropdown.set_selected(i)
        audio_name = adv.audio_codec_model.get_string(i)
        execute_stream(serial, get_opts(), f"Audio Codec: {audio_name}")

    # 6. High Stress Combination
    reset_ui()
    card.param_fullscreen.set_active(True)
    card.codec_dropdown.set_selected(2) # h265
    card.fps_dropdown.set_selected(1)   # 60
    adv.param_stay_awake.set_active(True)
    adv.buffer_dropdown.set_selected(2) # 50ms
    execute_stream(serial, get_opts(), "High Stress Combo (Fullscreen, h265, 60fps, 50ms buffer)")

    print("\n" + "="*40)
    print("PHASE 2: CAMERA MODE EXHAUSTIVE TESTING")
    print("="*40)
    
    # 1. Base Camera (will now have default max-size=1920)
    reset_ui()
    card.type_dropdown.set_selected(1)
    execute_stream(serial, get_opts(), "Base Camera Stream (Default 1920 size)")

    # 2. Camera Codec Matrix
    for i in range(1, card.codec_model.get_n_items()):
        reset_ui()
        card.type_dropdown.set_selected(1)
        card.codec_dropdown.set_selected(i)
        codec_name = card.codec_model.get_string(i)
        execute_stream(serial, get_opts(), f"Camera Video Codec: {codec_name}")

    # 3. Camera Size Matrix
    for i in range(1, card.size_model.get_n_items()):
        reset_ui()
        card.type_dropdown.set_selected(1)
        card.size_dropdown.set_selected(i)
        size_name = card.size_model.get_string(i)
        execute_stream(serial, get_opts(), f"Camera Max Size: {size_name}")

    print("\n✅ Live Device Testing Sequence Completed.")

if __name__ == '__main__':
    run_live_tests()
