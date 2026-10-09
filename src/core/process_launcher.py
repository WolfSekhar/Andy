import os
import sys
import threading
import subprocess
from typing import List, Dict, Optional, Callable
from gi.repository import GLib

class ScrcpyProcessManager:
    """
    Supervises the scrcpy subprocess lifecycle, environment variables,
    real-time stderr capture, and process exit notifications.
    """
    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.stderr_thread: Optional[threading.Thread] = None
        self.error_output: str = ""
        self._lock = threading.Lock()
        self.is_stopping_intentionally: bool = False
        self.current_mode: str = "stream"

    @property
    def is_running(self) -> bool:
        return self.process is not None and self.process.poll() is None

    def launch(
        self,
        serial: str,
        options: List[str],
        env_overrides: Optional[Dict[str, str]] = None,
        mode: str = "stream",
        on_exit_callback: Optional[Callable[[int, str, bool], None]] = None
    ) -> bool:
        """
        Spawns the scrcpy process with the specified serial, flags, and environment overrides.
        """
        cmd = ["scrcpy", "-s", serial] + options
        print(f"Executing ({mode}): {' '.join(cmd)}")

        env = os.environ.copy()
        env["SDL_VIDEODRIVER"] = "wayland"

        if env_overrides:
            for k, v in env_overrides.items():
                if v == "" and k in env:
                    del env[k]
                elif v != "":
                    env[k] = v

        with self._lock:
            self.error_output = ""
            self.is_stopping_intentionally = False
            self.current_mode = mode

        try:
            self.process = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )

            def read_stderr(proc):
                if not proc.stderr:
                    return
                for line in proc.stderr:
                    with self._lock:
                        self.error_output += line
                    sys.stderr.write(f"[scrcpy] {line}")

            self.stderr_thread = threading.Thread(
                target=read_stderr,
                args=(self.process,),
                daemon=True
            )
            self.stderr_thread.start()

            if on_exit_callback:
                def _handle_exit(pid, status):
                    exit_code = os.waitstatus_to_exitcode(status)
                    is_intentional = self.is_stopping_intentionally
                    with self._lock:
                        err_out = self.error_output.strip()
                    self.process = None
                    on_exit_callback(exit_code, err_out, is_intentional)

                GLib.child_watch_add(self.process.pid, _handle_exit)

            return True

        except Exception as e:
            with self._lock:
                self.error_output = str(e)
            self.process = None
            if on_exit_callback:
                on_exit_callback(-1, str(e), False)
            return False

    def stop(self):
        """
        Gracefully terminates the running scrcpy process, escalating to kill if needed.
        """
        self.is_stopping_intentionally = True
        if self.process is not None:
            self.process.terminate()
            try:
                self.process.wait(timeout=1.0)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None
