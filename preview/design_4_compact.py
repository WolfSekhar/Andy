import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw

class Design4CompactCompanion(Gtk.Box):
    """
    Design 4: Compact Companion / Floating Widget
    A focused, 460px companion window tailored for Wayland tiling WMs,
    laptop screens, and quick flyout sessions without desktop clutter.
    """
    def __init__(self, **kwargs):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, **kwargs)
        self.set_hexpand(True)
        self.set_vexpand(True)

        self.setup_ui()

    def setup_ui(self):
        clamp = Adw.Clamp(maximum_size=460)
        clamp.set_margin_top(16)
        clamp.set_margin_bottom(16)
        clamp.set_margin_start(16)
        clamp.set_margin_end(16)
        self.append(clamp)

        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        clamp.set_child(card)

        # Device Header Bar
        dev_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        dev_avatar = Gtk.Image.new_from_icon_name("phone-symbolic")
        dev_avatar.set_pixel_size(24)
        dev_avatar.add_css_class("accent")
        dev_row.append(dev_avatar)

        dev_title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        dev_title_box.set_hexpand(True)
        lbl_dev = Gtk.Label(label="Galaxy S23 Ultra", xalign=0)
        lbl_dev.add_css_class("title-3")
        lbl_status = Gtk.Label(label="🟢 Connected via USB • 🔋 85%", xalign=0)
        lbl_status.add_css_class("caption")
        lbl_status.add_css_class("dim-label")
        dev_title_box.append(lbl_dev)
        dev_title_box.append(lbl_status)
        dev_row.append(dev_title_box)

        btn_ref = Gtk.Button(icon_name="view-refresh-symbolic")
        btn_ref.set_valign(Gtk.Align.CENTER)
        dev_row.append(btn_ref)
        card.append(dev_row)

        # Segmented Mode Switcher
        mode_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        mode_box.add_css_class("linked")
        mode_box.set_homogeneous(True)

        btn_m_screen = Gtk.ToggleButton(label="📱 Screen")
        btn_m_screen.set_active(True)
        btn_m_cam = Gtk.ToggleButton(label="📷 Camera", group=btn_m_screen)
        btn_m_mk = Gtk.ToggleButton(label="⌨️ M/K Bridge", group=btn_m_screen)

        mode_box.append(btn_m_screen)
        mode_box.append(btn_m_cam)
        mode_box.append(btn_m_mk)
        card.append(mode_box)

        # Quick-Tiles Grid (4 Key Parameters)
        grid = Gtk.Grid()
        grid.set_column_spacing(10)
        grid.set_row_spacing(10)
        grid.set_column_homogeneous(True)
        card.append(grid)

        def make_tile(title, dropdown_items, selected=0):
            tile = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            tile.add_css_class("card")
            tile.set_margin_top(4)
            tile.set_margin_bottom(4)
            tile.set_margin_start(4)
            tile.set_margin_end(4)

            t_lbl = Gtk.Label(label=title, xalign=0)
            t_lbl.add_css_class("caption")
            t_lbl.add_css_class("dim-label")
            tile.append(t_lbl)

            drop = Gtk.DropDown()
            m = Gtk.StringList()
            for item in dropdown_items: m.append(item)
            drop.set_model(m)
            drop.set_selected(selected)
            tile.append(drop)
            return tile

        t_res = make_tile("Resolution", ["Native 1080p", "Balanced 80%", "Smooth 60%", "Lite 40%"])
        t_fps = make_tile("Framerate", ["60 FPS", "30 FPS", "15 FPS"])
        t_gpu = make_tile("GPU Engine", ["Auto Mesa", "NVIDIA PRIME", "AMD Vega"])
        t_codec = make_tile("Codec", ["H.265 HEVC", "H.264", "AV1"])

        grid.attach(t_res, 0, 0, 1, 1)
        grid.attach(t_fps, 1, 0, 1, 1)
        grid.attach(t_gpu, 0, 1, 1, 1)
        grid.attach(t_codec, 1, 1, 1, 1)

        # Quick Switch Toggles
        toggles_group = Adw.PreferencesGroup()
        card.append(toggles_group)

        sw_screen_off = Adw.SwitchRow(title="Turn Screen Off (Save Battery)")
        sw_uhid = Adw.SwitchRow(title="Hardware Keyboard/Mouse (UHID)")
        sw_full = Adw.SwitchRow(title="Launch in Fullscreen")
        toggles_group.add(sw_screen_off)
        toggles_group.add(sw_uhid)
        toggles_group.add(sw_full)

        # Primary Launch Button (Full Width Hero Pill)
        btn_launch = Gtk.Button(label="LAUNCH SESSION")
        btn_launch.add_css_class("suggested-action")
        btn_launch.add_css_class("pill")
        btn_launch.set_size_request(-1, 52)
        card.append(btn_launch)

        # Bottom subtle link for advanced dialog
        adv_link = Gtk.Button(label="Advanced Performance & Profile Settings →")
        adv_link.add_css_class("flat")
        adv_link.set_halign(Gtk.Align.CENTER)
        card.append(adv_link)
