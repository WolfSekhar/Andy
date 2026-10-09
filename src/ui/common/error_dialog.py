import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw

def show_error_dialog(parent: Gtk.Window, title: str, message: str):
    """
    Displays an Adw.MessageDialog with a scrollable monospace error log view.
    """
    dialog = Adw.MessageDialog(transient_for=parent, heading=title)
    scrolled = Gtk.ScrolledWindow()
    scrolled.set_min_content_height(200)
    scrolled.set_min_content_width(400)
    scrolled.set_propagate_natural_height(True)

    text_view = Gtk.TextView()
    text_view.set_editable(False)
    text_view.set_cursor_visible(False)
    text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
    text_view.add_css_class("error-log")
    text_view.get_buffer().set_text(message)

    scrolled.set_child(text_view)
    dialog.set_extra_child(scrolled)
    dialog.add_response("close", "Close")
    dialog.set_default_response("close")
    dialog.connect("response", lambda d, r: d.destroy())
    dialog.present()
