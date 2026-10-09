import time
import threading
from typing import Optional, Callable, Tuple
from gi.repository import GLib
from services.device_service import get_device_resolution

class OrientationMonitor:
    """
    Manages a background daemon thread that polls the connected Android device
    for orientation or resolution changes, dispatching updates to GTK's main loop.
    """
    def __init__(self):
        self.monitor_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.current_serial: Optional[str] = None
        self.last_resolution: Optional[Tuple[int, int, bool]] = None

    def start(self, serial: str, callback: Callable[[Tuple[int, int, bool]], None]):
        """
        Starts monitoring the given serial device.
        """
        self.stop()
        if not serial or serial == "No devices found":
            return

        self.current_serial = serial
        self.stop_event.clear()
        self.last_resolution = None

        def _worker():
            while not self.stop_event.is_set():
                time.sleep(2.0)
                if self.stop_event.is_set() or self.current_serial != serial:
                    break

                res = get_device_resolution(serial)
                if res and res != self.last_resolution:
                    if self.stop_event.is_set() or self.current_serial != serial:
                        break
                    self.last_resolution = res
                    GLib.idle_add(callback, res)

        self.monitor_thread = threading.Thread(target=_worker, daemon=True)
        self.monitor_thread.start()

    def stop(self):
        """
        Signals the monitor thread to stop.
        """
        self.stop_event.set()
        self.current_serial = None
