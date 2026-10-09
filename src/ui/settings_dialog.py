import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw
from services.profile_service import save_profile, list_profiles, delete_profile, rename_profile
from core.scrcpy_parser import parse_scrcpy_params

class SettingsDialog:
    def __init__(self, parent, refresh_profiles_callback):
        self.parent = parent
        self.refresh_profiles_callback = refresh_profiles_callback
        self.win = Adw.PreferencesWindow(transient_for=parent)
        self.win.set_title("Settings")

        self.setup_import_page()
        self.setup_manage_page()

    def setup_import_page(self):
        import_page = Adw.PreferencesPage(title="Import Profile", icon_name="document-import-symbolic")
        self.win.add(import_page)

        import_group = Adw.PreferencesGroup(title="Import from Raw Parameters")
        import_page.add(import_group)

        self.name_row = Adw.EntryRow(title="Profile Name")
        import_group.add(self.name_row)

        self.param_row = Adw.EntryRow(title="Raw Parameters")
        self.param_row.set_tooltip_text("e.g. --fullscreen --max-fps=60")
        import_group.add(self.param_row)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        btn_box.set_halign(Gtk.Align.CENTER)
        btn_box.set_margin_top(12)

        save_btn = Gtk.Button(label="Import & Save")
        save_btn.add_css_class("suggested-action")
        save_btn.connect("clicked", self.on_import_clicked)
        btn_box.append(save_btn)
        import_group.add(btn_box)

    def setup_manage_page(self):
        manage_page = Adw.PreferencesPage(title="Manage Profiles", icon_name="folder-symbolic")
        self.win.add(manage_page)

        self.manage_group = Adw.PreferencesGroup(title="Saved Profiles")
        manage_page.add(self.manage_group)
        self.refresh_manage_list()

    def on_import_clicked(self, btn):
        name = self.name_row.get_text().strip()
        params = self.param_row.get_text().strip()
        if name and params:
            state = parse_scrcpy_params(params)
            save_profile(name, state)
            self.refresh_profiles_callback(select_name=name)
            self.refresh_manage_list()
            self.name_row.set_text("")
            self.param_row.set_text("")

    def refresh_manage_list(self):
        group = self.manage_group
        child = group.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            group.remove(child)
            child = next_child

        profiles = list_profiles()
        if not profiles:
            row = Adw.ActionRow(title="No profiles saved")
            group.add(row)
            return

        for name in profiles:
            row = Adw.ActionRow(title=name)

            edit_btn = Gtk.Button(icon_name="document-edit-symbolic")
            edit_btn.set_valign(Gtk.Align.CENTER)
            edit_btn.add_css_class("flat")

            def make_rename_handler(current_name):
                def on_rename(btn):
                    dialog = Adw.MessageDialog(transient_for=self.win, heading="Rename Profile")
                    entry = Gtk.Entry(text=current_name)
                    dialog.set_extra_child(entry)
                    dialog.add_response("cancel", "Cancel")
                    dialog.add_response("rename", "Rename")

                    def on_rename_resp(d, resp):
                        if resp == "rename":
                            new_name = entry.get_text().strip()
                            if new_name and new_name != current_name:
                                rename_profile(current_name, new_name)
                                self.refresh_profiles_callback()
                                self.refresh_manage_list()
                        d.destroy()
                    dialog.connect("response", on_rename_resp)
                    dialog.present()
                return on_rename

            edit_btn.connect("clicked", make_rename_handler(name))
            row.add_suffix(edit_btn)

            del_btn = Gtk.Button(icon_name="user-trash-symbolic")
            del_btn.set_valign(Gtk.Align.CENTER)
            del_btn.add_css_class("flat")
            del_btn.add_css_class("destructive-action")

            def make_delete_handler(target_name):
                def on_delete(btn):
                    delete_profile(target_name)
                    self.refresh_profiles_callback()
                    self.refresh_manage_list()
                return on_delete

            del_btn.connect("clicked", make_delete_handler(name))
            row.add_suffix(del_btn)

            group.add(row)

    def present(self):
        self.win.present()
