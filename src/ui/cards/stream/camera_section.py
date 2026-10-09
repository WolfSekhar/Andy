import re
from typing import List, Dict, Optional, Tuple
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw
from core.config import CAMERA_FPS_PRESETS

class CameraSection(Adw.PreferencesGroup):
    """
    Camera streaming options (Select Camera, Camera Torch, Camera FPS, High-Speed Capture, Camera Zoom).
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.camera_row = Adw.ActionRow(title="Select Camera")
        self.camera_model = Gtk.StringList()
        self.camera_dropdown = Gtk.DropDown(model=self.camera_model)
        self.camera_dropdown.set_valign(Gtk.Align.CENTER)
        self.camera_row.add_suffix(self.camera_dropdown)
        self.add(self.camera_row)

        self.param_camera_torch = Adw.SwitchRow(
            title="Camera Torch (Flashlight)",
            subtitle="Turn on flashlight during camera stream"
        )
        self.add(self.param_camera_torch)

        self.camera_fps_model = Gtk.StringList()
        for f in CAMERA_FPS_PRESETS:
            self.camera_fps_model.append(f)
        self.param_camera_fps = Adw.ComboRow(title="Camera FPS", model=self.camera_fps_model)
        self.param_camera_fps.dropdown = self.param_camera_fps
        self.camera_fps_row = self.param_camera_fps
        self.camera_fps_dropdown = self.param_camera_fps
        self.add(self.param_camera_fps)

        self.param_camera_high_speed = Adw.SwitchRow(
            title="High-Speed Capture",
            subtitle="Enable high speed camera streaming mode"
        )
        self.add(self.param_camera_high_speed)

        self.param_camera_zoom = Adw.EntryRow(title="Camera Zoom")
        self.param_camera_zoom.set_tooltip_text("e.g. 1.0, 2.5 (Android 11+)")
        self.param_camera_zoom.subtitle = "e.g. 1.0, 2.5 (Android 11+)"
        self.add(self.param_camera_zoom)

    def apply_cameras(self, cameras: List[Dict[str, str]]):
        n_cam_items = self.camera_model.get_n_items()
        self.camera_model.splice(0, n_cam_items, [])
        if not cameras:
            self.camera_model.append("None Found")
            self.camera_dropdown.set_sensitive(False)
        else:
            for cam in cameras:
                self.camera_model.append(cam['desc'])
            self.camera_dropdown.set_sensitive(True)

    def get_selected_camera_resolution(self) -> Optional[Tuple[int, int, bool]]:
        idx = self.camera_dropdown.get_selected()
        if idx != Gtk.INVALID_LIST_POSITION and self.camera_model.get_n_items() > 0:
            desc = self.camera_model.get_string(idx)
            match = re.search(r'(\d+)x(\d+)', desc)
            if match:
                w, h = int(match.group(1)), int(match.group(2))
                return (w, h, h > w)
        return None
