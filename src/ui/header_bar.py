import inspect
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw

try:
    from ui.layouts.layout_manager import (
        LAYOUT_CLASSIC,
        LAYOUT_WORKSTATION,
        LAYOUT_STUDIO,
        LAYOUT_INSPECTOR,
        LAYOUT_MODULAR_HUB,
        LAYOUT_ACTION_ASSISTANT,
    )
except ImportError:
    LAYOUT_CLASSIC = "classic"
    LAYOUT_WORKSTATION = "workstation"
    LAYOUT_STUDIO = "studio"
    LAYOUT_INSPECTOR = "inspector"
    LAYOUT_MODULAR_HUB = "modular_hub"
    LAYOUT_ACTION_ASSISTANT = "action_assistant"


class LayoutID(str):
    """
    Rich string wrapper for layout identifiers allowing flexible comparisons
    against canonical IDs, snake_case aliases, display titles, and integer indices.
    """
    def __new__(cls, val, aliases=(), index=0, title=""):
        obj = super().__new__(cls, val)
        obj.id = val
        obj.index = index
        obj.title = title
        obj._aliases = {str(a).lower().replace("-", "_").replace(" ", "_") for a in aliases}
        obj._aliases.add(val.lower().replace("-", "_").replace(" ", "_"))
        return obj

    def __eq__(self, other):
        if isinstance(other, str) and super().__eq__(other):
            return True
        if other is None:
            return False
        cleaned = str(other).lower().replace("-", "_").replace(" ", "_")
        return cleaned in self._aliases

    def __hash__(self):
        return super().__hash__()


class AndyHeaderBar:
    LAYOUT_DEFINITIONS = [
        {
            "id": LAYOUT_CLASSIC,
            "title": "Classic Cards",
            "aliases": ["classic_cards", "classic-cards", "cards", 0, "0"],
        },
        {
            "id": LAYOUT_WORKSTATION,
            "title": "Modern Workstation",
            "aliases": ["modern_workstation", "modern-workstation", 1, "1"],
        },
        {
            "id": LAYOUT_STUDIO,
            "title": "Studio Command Deck",
            "aliases": ["studio_command_deck", "studio-command-deck", "command_deck", "deck", 2, "2"],
        },
        {
            "id": LAYOUT_INSPECTOR,
            "title": "Compact Inspector",
            "aliases": ["compact_inspector", "compact-inspector", "compact", 3, "3"],
        },
        {
            "id": LAYOUT_MODULAR_HUB,
            "title": "Modular Card Hub",
            "aliases": ["modular_card_hub", "modular-card-hub", "modular", "card_hub", "hub", 4, "4"],
        },
        {
            "id": LAYOUT_ACTION_ASSISTANT,
            "title": "Action Assistant",
            "aliases": ["action-assistant", "assistant", "action", 5, "5"],
        },
    ]

    def __init__(self, on_theme_toggled, on_profile_selected, on_save_profile_clicked, on_settings_clicked, on_layout_selected=None):
        self.widget = Adw.HeaderBar()
        self.style_manager = Adw.StyleManager.get_default()
        self.on_layout_selected = on_layout_selected
        
        # Theme Mode Toggle Button (Light/Dark)
        self.theme_button = Gtk.Button()
        self.theme_button.set_valign(Gtk.Align.CENTER)
        self.theme_button.connect("clicked", lambda b: on_theme_toggled())
        self.update_theme_icon()
        self.widget.pack_start(self.theme_button)

        # Profile Selection Dropdown
        self.profile_model = Gtk.StringList()
        self.profile_dropdown = Gtk.DropDown(model=self.profile_model)
        self.profile_dropdown.set_valign(Gtk.Align.CENTER)
        self.profile_dropdown.set_tooltip_text("Load Saved Profile")
        self.profile_dropdown.connect("notify::selected", lambda d, p: on_profile_selected(d, p))
        self.widget.pack_start(self.profile_dropdown)

        # Save Profile Button
        self.save_button = Gtk.Button(icon_name="document-save-symbolic")
        self.save_button.set_valign(Gtk.Align.CENTER)
        self.save_button.set_tooltip_text("Save Profile")
        self.save_button.connect("clicked", lambda b: on_save_profile_clicked())
        self.widget.pack_start(self.save_button)

        # Settings Button
        self.settings_button = Gtk.Button(icon_name="emblem-system-symbolic")
        self.settings_button.set_valign(Gtk.Align.CENTER)
        self.settings_button.set_tooltip_text("Settings & Profiles")
        self.settings_button.connect("clicked", lambda b: on_settings_clicked())
        self.widget.pack_end(self.settings_button)

        # Layout Selection Dropdown
        self.layout_model = Gtk.StringList.new([item["title"] for item in self.LAYOUT_DEFINITIONS])
        self.layout_dropdown = Gtk.DropDown(model=self.layout_model)
        self.layout_dropdown.set_valign(Gtk.Align.CENTER)
        self.layout_dropdown.set_tooltip_text("Switch UI Layout")
        self.layout_dropdown.connect("notify::selected", self._on_layout_changed)
        self.widget.pack_end(self.layout_dropdown)

        # Title widget
        self.window_title = Adw.WindowTitle(
            title="Andy",
            subtitle="scrcpy Wayland Controller"
        )
        self.widget.set_title_widget(self.window_title)

    def _on_layout_changed(self, dropdown, pspec):
        if not self.on_layout_selected:
            return
        layout_id = self.get_active_layout_id()
        idx = dropdown.get_selected()

        try:
            sig = inspect.signature(self.on_layout_selected)
            params = list(sig.parameters.values())
            n_params = len(params)
            param_names = [p.name for p in params]
        except (ValueError, TypeError):
            n_params = None
            param_names = []

        if n_params == 0:
            self.on_layout_selected()
        elif n_params == 1:
            self.on_layout_selected(layout_id)
        elif n_params == 2:
            if 'dropdown' in param_names or 'pspec' in param_names or param_names == ['d', 'p']:
                self.on_layout_selected(dropdown, pspec)
            else:
                self.on_layout_selected(layout_id, idx)
        else:
            try:
                self.on_layout_selected(layout_id)
            except TypeError as e:
                if "positional argument" in str(e) or "takes" in str(e):
                    try:
                        self.on_layout_selected(dropdown, pspec)
                    except TypeError:
                        self.on_layout_selected()
                else:
                    raise

    def set_active_layout(self, layout_id):
        """
        Sets the active layout by ID, title, or index.
        Returns True if a matching layout was found and set, False otherwise.
        """
        def _apply(idx):
            current = self.layout_dropdown.get_selected()
            self.layout_dropdown.set_selected(idx)
            if current == idx:
                self._on_layout_changed(self.layout_dropdown, None)
            return True

        if isinstance(layout_id, int):
            if 0 <= layout_id < len(self.LAYOUT_DEFINITIONS):
                return _apply(layout_id)
            return False

        if layout_id is None:
            return False

        s = str(layout_id).strip()
        if s.isdigit():
            idx = int(s)
            if 0 <= idx < len(self.LAYOUT_DEFINITIONS):
                return _apply(idx)

        target = s.lower().replace("-", "_").replace(" ", "_")
        for idx, item in enumerate(self.LAYOUT_DEFINITIONS):
            if target == item["id"]:
                return _apply(idx)
            title_norm = item["title"].lower().replace("-", "_").replace(" ", "_")
            if target == title_norm:
                return _apply(idx)
            for alias in item.get("aliases", []):
                alias_norm = str(alias).lower().replace("-", "_").replace(" ", "_")
                if target == alias_norm:
                    return _apply(idx)
        return False

    def get_active_layout_id(self):
        """
        Returns the LayoutID of the currently selected layout.
        """
        idx = self.layout_dropdown.get_selected()
        if 0 <= idx < len(self.LAYOUT_DEFINITIONS):
            item = self.LAYOUT_DEFINITIONS[idx]
            aliases = list(item.get("aliases", [])) + [item["title"], str(idx)]
            return LayoutID(item["id"], aliases=aliases, index=idx, title=item["title"])
        return LayoutID(LAYOUT_CLASSIC, aliases=["classic_cards", "0", 0, "Classic Cards"], index=0, title="Classic Cards")

    def get_selected_layout_index(self):
        return self.layout_dropdown.get_selected()

    def get_layout_name(self, index=None):
        if index is None:
            index = self.layout_dropdown.get_selected()
        if 0 <= index < len(self.LAYOUT_DEFINITIONS):
            return self.LAYOUT_DEFINITIONS[index]["title"]
        return ""

    def update_theme_icon(self):
        if self.style_manager.get_dark():
            self.theme_button.set_icon_name("display-brightness-symbolic")
            self.theme_button.set_tooltip_text("Switch to Light Mode")
        else:
            self.theme_button.set_icon_name("weather-clear-night-symbolic")
            self.theme_button.set_tooltip_text("Switch to Dark Mode")
            
    def set_profiles(self, profiles, select_name=None):
        n_items = self.profile_model.get_n_items()
        self.profile_model.splice(0, n_items, ["Default"])
        for p in profiles:
            self.profile_model.append(p)
            
        if select_name:
            for i in range(self.profile_model.get_n_items()):
                if self.profile_model.get_string(i) == select_name:
                    self.profile_dropdown.set_selected(i)
                    break
                    
    def get_selected_profile_index(self):
        return self.profile_dropdown.get_selected()
        
    def get_profile_name(self, index):
        return self.profile_model.get_string(index)
