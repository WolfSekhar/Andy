from typing import Optional
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk


class InhibitService:
    """Manages system sleep and screensaver inhibition during live streaming/recording.

    Prevents Linux desktop from sleeping or locking display when viewing Android screen.
    """

    def __init__(self):
        self._cookie: Optional[int] = None
        self._app: Optional[Gtk.Application] = None

    def set_application(self, app: Gtk.Application):
        self._app = app

    def inhibit(
        self,
        window: Optional[Gtk.Window] = None,
        reason: str = "Andy active Android mirroring"
    ) -> bool:
        """Inhibits system idle and suspend states."""
        if self._cookie is not None:
            return True  # Already inhibited

        if not self._app:
            return False

        # Guard against unregistered / headless applications (e.g. unit tests without D-Bus)
        if hasattr(self._app, "get_is_registered") and not self._app.get_is_registered():
            return False

        try:
            flags = Gtk.ApplicationInhibitFlags.IDLE | Gtk.ApplicationInhibitFlags.SUSPEND
            self._cookie = self._app.inhibit(window, flags, reason)
            return self._cookie is not None and self._cookie > 0
        except Exception:
            return False

    def uninhibit(self) -> bool:
        """Restores normal desktop power and screensaver behavior."""
        if self._cookie is None or not self._app:
            return False

        if hasattr(self._app, "get_is_registered") and not self._app.get_is_registered():
            self._cookie = None
            return False

        try:
            self._app.uninhibit(self._cookie)
            self._cookie = None
            return True
        except Exception:
            self._cookie = None
            return False

    @property
    def is_inhibited(self) -> bool:
        return self._cookie is not None


# Global singleton instance
inhibit_service = InhibitService()
