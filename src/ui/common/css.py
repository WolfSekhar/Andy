import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk

APPLICATION_CSS = b"""
    /* GNOME Circle Action Buttons */
    .stream-btn {
        background-color: @accent_bg_color;
        color: @accent_fg_color;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        padding: 10px 28px;
        font-size: 14px;
        border-radius: 9999px;
        border: 1px solid alpha(white, 0.18);
        box-shadow: 0 2px 8px alpha(@accent_bg_color, 0.35);
        transition: all 180ms cubic-bezier(0.25, 1, 0.5, 1);
    }
    .stream-btn:hover {
        box-shadow: 0 4px 14px alpha(@accent_bg_color, 0.50);
        filter: brightness(1.08);
    }
    .stream-btn:active {
        box-shadow: 0 1px 4px alpha(@accent_bg_color, 0.30);
        filter: brightness(0.95);
    }

    .stop-btn {
        background-color: @destructive_bg_color;
        color: @destructive_fg_color;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        padding: 10px 28px;
        font-size: 14px;
        border-radius: 9999px;
        border: 1px solid alpha(white, 0.18);
        box-shadow: 0 2px 8px alpha(@destructive_bg_color, 0.40);
        transition: all 180ms cubic-bezier(0.25, 1, 0.5, 1);
    }
    .stop-btn:hover {
        box-shadow: 0 4px 14px alpha(@destructive_bg_color, 0.55);
        filter: brightness(1.08);
    }
    .stop-btn:active {
        box-shadow: 0 1px 4px alpha(@destructive_bg_color, 0.30);
        filter: brightness(0.95);
    }

    .mk-btn {
        font-weight: 600;
        padding: 9px 22px;
        font-size: 14px;
        border-radius: 9999px;
        border: 1px solid @borders;
        transition: all 180ms cubic-bezier(0.25, 1, 0.5, 1);
    }
    .mk-btn:hover {
        background-color: alpha(currentColor, 0.08);
    }
    .mk-btn:active {
        background-color: alpha(currentColor, 0.14);
    }

    /* GNOME Circle Status Badges & Chips */
    .theme-badge {
        font-weight: 600;
        font-size: 11px;
        padding: 3px 10px;
        border-radius: 9999px;
        background-color: alpha(@accent_bg_color, 0.15);
        color: @accent_color;
        border: 1px solid alpha(@accent_color, 0.25);
        transition: all 150ms ease-in-out;
    }
    .badge-connected, .badge-usb {
        background-color: alpha(@success_bg_color, 0.16);
        color: @success_color;
        border: 1px solid alpha(@success_color, 0.28);
    }
    .badge-wifi {
        background-color: alpha(@accent_bg_color, 0.16);
        color: @accent_color;
        border: 1px solid alpha(@accent_color, 0.28);
    }
    .badge-disconnected {
        background-color: alpha(currentColor, 0.07);
        color: alpha(currentColor, 0.55);
        border: 1px solid alpha(currentColor, 0.12);
    }
    .ratio-badge {
        background-color: alpha(currentColor, 0.07);
        color: alpha(currentColor, 0.72);
        border: 1px solid alpha(currentColor, 0.12);
        font-weight: 600;
        font-size: 11px;
        padding: 2px 8px;
        border-radius: 9999px;
    }

    /* Stepper & Zoom Controls */
    .zoom-btn {
        min-width: 28px;
        min-height: 28px;
        padding: 2px 6px;
        font-weight: 600;
        border-radius: 6px;
        transition: all 120ms ease;
    }
    .zoom-reset-btn {
        min-width: 40px;
        min-height: 28px;
        padding: 2px 6px;
        font-size: 11px;
        font-weight: 600;
        border-radius: 6px;
        transition: all 120ms ease;
    }

    /* Terminal & Monospace Error Views */
    .error-log {
        font-family: monospace;
        background-color: alpha(@window_fg_color, 0.05);
        color: @window_fg_color;
        border: 1px solid @borders;
        padding: 12px;
        border-radius: 8px;
    }

    /* FlowBox and Card Geometry */
    flowboxchild {
        padding: 0;
        margin: 0;
        background: none;
    }
    flowboxchild:focus, flowboxchild:selected {
        outline: none;
        background: none;
    }
    .boxed-list {
        border-radius: 12px;
    }
    .linked > button {
        transition: all 150ms ease-in-out;
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
