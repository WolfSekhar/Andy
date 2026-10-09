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

    /* Permanent Slim Utility Sidebar (Unified with App Background) */
    .sidebar-pane {
        background-color: transparent;
        background: transparent;
        border-right: 1px solid alpha(currentColor, 0.08);
        padding: 16px 14px;
    }
    .sidebar-pane .dim-label {
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.8px;
    }
    .sidebar-btn {
        padding: 8px 12px;
        border-radius: 9px;
        font-weight: 600;
        transition: all 160ms cubic-bezier(0.25, 1, 0.5, 1);
    }

    /* Beautified Colored Sidebar Elements */
    .sidebar-dropdown > button {
        background-color: alpha(@accent_bg_color, 0.14);
        color: @accent_color;
        border: 1px solid alpha(@accent_color, 0.28);
        border-radius: 9px;
        font-weight: 600;
        transition: all 160ms cubic-bezier(0.25, 1, 0.5, 1);
    }
    .sidebar-dropdown > button:hover {
        background-color: alpha(@accent_bg_color, 0.22);
        border-color: alpha(@accent_color, 0.42);
    }
    .sidebar-dropdown > button:active {
        background-color: alpha(@accent_bg_color, 0.28);
    }

    .sidebar-save-btn {
        background-color: alpha(@success_bg_color, 0.16);
        color: @success_color;
        border: 1px solid alpha(@success_color, 0.28);
        padding: 8px 10px;
    }
    .sidebar-save-btn:hover {
        background-color: alpha(@success_bg_color, 0.26);
        border-color: alpha(@success_color, 0.44);
    }
    .sidebar-save-btn:active {
        background-color: alpha(@success_bg_color, 0.32);
    }

    .sidebar-theme-btn {
        background-color: alpha(@warning_bg_color, 0.16);
        color: @warning_color;
        border: 1px solid alpha(@warning_color, 0.28);
    }
    .sidebar-theme-btn:hover {
        background-color: alpha(@warning_bg_color, 0.26);
        border-color: alpha(@warning_color, 0.42);
    }
    .sidebar-theme-btn:active {
        background-color: alpha(@warning_bg_color, 0.32);
    }

    .sidebar-settings-btn {
        background-color: alpha(@accent_bg_color, 0.14);
        color: @accent_color;
        border: 1px solid alpha(@accent_color, 0.28);
    }
    .sidebar-settings-btn:hover {
        background-color: alpha(@accent_bg_color, 0.24);
        border-color: alpha(@accent_color, 0.42);
    }
    .sidebar-settings-btn:active {
        background-color: alpha(@accent_bg_color, 0.30);
    }

    .sidebar-about-btn {
        background-color: alpha(currentColor, 0.07);
        color: @window_fg_color;
        border: 1px solid alpha(currentColor, 0.14);
    }
    .sidebar-about-btn:hover {
        background-color: alpha(currentColor, 0.14);
        border-color: alpha(currentColor, 0.24);
    }
    .sidebar-about-btn:active {
        background-color: alpha(currentColor, 0.20);
    }

    /* Amberol-Style Immersive Seamless HeaderBar */
    headerbar,
    headerbar.flat,
    headerbar.amberol-header {
        background: transparent;
        background-color: transparent;
        background-image: none;
        box-shadow: none;
        border: none;
        border-bottom: none;
        border-style: none;
        border-width: 0;
    }

    headerbar windowhandle {
        background: transparent;
    }

    /* Floating window controls */
    headerbar button.titlebutton {
        background: transparent;
        border-radius: 9999px;
        transition: background-color 150ms cubic-bezier(0.25, 1, 0.5, 1);
    }
    headerbar button.titlebutton:hover {
        background-color: alpha(currentColor, 0.12);
    }
    headerbar button.titlebutton:active {
        background-color: alpha(currentColor, 0.22);
    }

    /* Ambient window surface gradient */
    window.background {
        background: linear-gradient(180deg, alpha(@accent_bg_color, 0.04) 0%, transparent 140px), @window_bg_color;
    }

    /* True Pure Light Mode (Crisp & Bright, Zero Grey) */
    window.light-theme,
    window.background.light-theme,
    .light-theme,
    .light-theme .sidebar-pane,
    window.light-theme .sidebar-pane {
        background-color: #ffffff;
        background: #ffffff;
        background-image: none;
        color: #1a1a1a;
    }
    window.light-theme .boxed-list,
    window.light-theme .card {
        background-color: #f7f8fa;
        color: #1a1a1a;
        border: 1px solid rgba(0, 0, 0, 0.07);
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
    }

    /* True Deep Dark Mode (Sleek & Obsidian, Zero Mid-Grey) */
    window.dark-theme,
    window.background.dark-theme,
    .dark-theme,
    .dark-theme .sidebar-pane,
    window.dark-theme .sidebar-pane {
        background-color: #121214;
        background: #121214;
        background-image: none;
        color: #f4f4f5;
    }
    window.dark-theme .boxed-list,
    window.dark-theme .card {
        background-color: #1e1e24;
        color: #f4f4f5;
        border: 1px solid rgba(255, 255, 255, 0.08);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.28);
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
            Gtk.STYLE_PROVIDER_PRIORITY_USER
        )
