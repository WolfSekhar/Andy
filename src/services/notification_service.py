import os
import sys
from typing import Optional
import gi
gi.require_version('Gio', '2.0')
from gi.repository import Gio, GLib


class NotificationService:
    """Native Linux desktop notification manager using Gio.Notification.

    Provides zero-overhead, asynchronous notification dispatch for screenshots,
    recordings, and device lifecycle events.
    """

    def __init__(self, application: Optional[Gio.Application] = None):
        self.application = application

    def set_application(self, application: Gio.Application):
        self.application = application

    def send_notification(
        self,
        title: str,
        body: str,
        notification_id: str = "andy-status",
        icon_name: str = "com.wolfsekhar.Andy"
    ) -> bool:
        """Sends a native desktop notification asynchronously."""
        if not self.application:
            return False

        try:
            notification = Gio.Notification.new(title)
            notification.set_body(body)
            if icon_name:
                notification.set_icon(Gio.ThemedIcon.new(icon_name))

            self.application.send_notification(notification_id, notification)
            return True
        except Exception as e:
            # Headless or missing notification daemon gracefully ignored
            print(f"Notification notice: {e}", file=sys.stderr)
            return False

    def notify_screenshot(self, file_path: str) -> bool:
        """Notification for captured device screenshot."""
        filename = os.path.basename(file_path)
        return self.send_notification(
            title="Screenshot Captured",
            body=f"Saved to {filename}",
            notification_id="andy-screenshot",
            icon_name="camera-photo-symbolic"
        )

    def notify_recording(self, file_path: str) -> bool:
        """Notification for completed video recording."""
        filename = os.path.basename(file_path)
        return self.send_notification(
            title="Recording Completed",
            body=f"Saved to {filename}",
            notification_id="andy-recording",
            icon_name="video-x-generic-symbolic"
        )

    def notify_device_event(self, device_name: str, connected: bool = True) -> bool:
        """Notification for device connection/disconnection."""
        status = "Connected" if connected else "Disconnected"
        return self.send_notification(
            title=f"Device {status}",
            body=f"{device_name} is now {status.lower()}",
            notification_id="andy-device",
            icon_name="phone-symbolic"
        )

    def notify_error(self, title: str, message: str) -> bool:
        """Notification for streaming or ADB failures."""
        return self.send_notification(
            title=title,
            body=message,
            notification_id="andy-error",
            icon_name="dialog-error-symbolic"
        )


# Global singleton instance
notification_service = NotificationService()
