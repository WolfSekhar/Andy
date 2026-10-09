import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk

APPLICATION_CSS = b"""
    .stream-btn {
        background-color: #3584e4;
        color: white;
        font-weight: 700;
        text-transform: uppercase;
        padding: 9px 26px;
        font-size: 15px;
        border-radius: 9999px;
        box-shadow: 0 0 12px rgba(53, 132, 228, 0.35);
        transition: all 180ms ease-in-out;
    }
    .stream-btn:hover {
        background-color: #2a6ac1;
    }
    .stop-btn {
        background-color: #e01b24;
        color: white;
        font-weight: 700;
        text-transform: uppercase;
        padding: 9px 26px;
        font-size: 15px;
        border-radius: 9999px;
        box-shadow: 0 0 14px rgba(224, 27, 36, 0.5);
        transition: all 180ms ease-in-out;
    }
    .stop-btn:hover {
        background-color: #c01c28;
    }
    .mk-btn {
        font-weight: 600;
        padding: 9px 20px;
        font-size: 14px;
        border-radius: 9999px;
    }
    .theme-badge {
        background-color: rgba(53, 132, 228, 0.18);
        color: #78aeed;
        font-weight: 600;
        font-size: 11px;
        padding: 3px 8px;
        border-radius: 6px;
    }
    .zoom-btn {
        min-width: 24px;
        padding-left: 4px;
        padding-right: 4px;
        padding-top: 2px;
        padding-bottom: 2px;
    }
    .zoom-reset-btn {
        min-width: 38px;
        padding-left: 3px;
        padding-right: 3px;
        font-size: 11px;
    }
    .error-log {
        font-family: monospace;
        background-color: #1e1e1e;
        color: #f8f8f2;
        padding: 10px;
        border-radius: 8px;
    }
    flowboxchild {
        padding: 0;
        margin: 0;
        background: none;
    }
    flowboxchild:focus, flowboxchild:selected {
        outline: none;
        background: none;
    }
"""

def apply_application_css():
    """
    Applies custom styling to the default Gdk display.
    """
    display = Gdk.Display.get_default()
    if display and isinstance(display, Gdk.Display):
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(APPLICATION_CSS)
        Gtk.StyleContext.add_provider_for_display(
            display,
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
