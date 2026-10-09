from unittest.mock import MagicMock

class FakeAdbRunner:
    """
    Simulates realistic ADB and scrcpy outputs for testing without physical devices.
    """
    DEFAULT_WM_SIZE = "Physical size: 1084x2412\n"
    DEFAULT_WM_DENSITY = "Physical density: 420\nOverride density: 400\n"
    DEFAULT_BATTERY = "Current Battery Service state:\n  level: 85\n  status: 2\n  USB powered: true\n"
    DEFAULT_DISPLAYS = "    --display-id=0    (1084x2412)\n"
    DEFAULT_CAMERAS = "    --camera-id=0    (back, 4080x3072, fps={30})\n    --camera-id=1    (front, 3280x2464, fps={30})\n"

    @classmethod
    def create_mock(cls, stdout: str = "", returncode: int = 0):
        mock = MagicMock()
        mock.returncode = returncode
        mock.stdout = stdout
        mock.stderr = ""
        return mock

    @classmethod
    def dispatch(cls, cmd, **kwargs):
        cmd_str = " ".join(cmd)
        if "devices -l" in cmd_str:
            return cls.create_mock("List of devices attached\nemulator-5554 device product:sdk model:Emulator device:generic\n")
        elif "wm size" in cmd_str:
            return cls.create_mock(cls.DEFAULT_WM_SIZE)
        elif "wm density" in cmd_str:
            return cls.create_mock(cls.DEFAULT_WM_DENSITY)
        elif "dumpsys battery" in cmd_str:
            return cls.create_mock(cls.DEFAULT_BATTERY)
        elif "--list-displays" in cmd_str:
            return cls.create_mock(cls.DEFAULT_DISPLAYS)
        elif "--list-cameras" in cmd_str:
            return cls.create_mock(cls.DEFAULT_CAMERAS)
        elif "ro.product.model" in cmd_str:
            return cls.create_mock("Nothing Phone (2a)\n")
        elif "ro.build.version.release" in cmd_str:
            return cls.create_mock("16\n")
        elif "ro.build.version.sdk" in cmd_str:
            return cls.create_mock("36\n")
        return cls.create_mock("")
