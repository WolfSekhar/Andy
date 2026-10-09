import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw

class Design3HeroStudio(Gtk.Box):
    """
    Design 3: Quick-Launch Hero Studio
    Features an expressive Hero status card, 1-click Quick Presets for instant launch,
    and collapsible drawers (Adw.ExpanderRow) for detailed tuning.
    """
    def __init__(self, **kwargs):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, **kwargs)
        self.set_hexpand(True)
        self.set_vexpand(True)

        self.setup_ui()

    def setup_ui(self):
        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroller.set_hexpand(True)
        scroller.set_vexpand(True)
        self.append(scroller)

        clamp = Adw.Clamp(maximum_size=820)
        clamp.set_margin_top(20)
        clamp.set_margin_bottom(24)
        clamp.set_margin_start(20)
        clamp.set_margin_end(20)
        scroller.set_child(clamp)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        clamp.set_child(main_box)

        # ----------------- HERO CARD -----------------
        hero_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        hero_card.add_css_class("card")
        hero_card.set_margin_bottom(6)
        hero_card.set_margin_top(4)

        # Top row: Device Info + Dropdown selector
        hero_top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        hero_top.set_margin_top(16)
        hero_top.set_margin_start(18)
        hero_top.set_margin_end(18)

        dev_icon = Gtk.Image.new_from_icon_name("phone-symbolic")
        dev_icon.set_pixel_size(36)
        dev_icon.add_css_class("accent")
        hero_top.append(dev_icon)

        dev_meta = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        dev_meta.set_hexpand(True)
        d_name = Gtk.Label(label="Samsung Galaxy S23 Ultra", xalign=0)
        d_name.add_css_class("title-2")
        d_sub = Gtk.Label(label="Android 14 (OneUI 6.1) • Serial: RFCT10ABCDE • USB 3.2 High-Speed", xalign=0)
        d_sub.add_css_class("caption")
        d_sub.add_css_class("dim-label")
        dev_meta.append(d_name)
        dev_meta.append(d_sub)
        hero_top.append(dev_meta)

        # Quick device switcher
        dev_combo = Gtk.DropDown()
        m_d = Gtk.StringList()
        m_d.append("Galaxy S23")
        m_d.append("Pixel Tablet")
        dev_combo.set_model(m_d)
        dev_combo.set_valign(Gtk.Align.CENTER)
        hero_top.append(dev_combo)
        hero_card.append(hero_top)

        # Hero Telemetry Badges
        telemetry_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        telemetry_box.set_margin_start(18)
        telemetry_box.set_margin_end(18)

        def make_pill(text, icon):
            b = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            b.add_css_class("card")
            b.set_margin_top(2)
            b.set_margin_bottom(2)
            img = Gtk.Image.new_from_icon_name(icon)
            img.set_pixel_size(14)
            lbl = Gtk.Label(label=text)
            lbl.add_css_class("caption")
            b.append(img)
            b.append(lbl)
            return b

        telemetry_box.append(make_pill("Battery 88%", "battery-good-symbolic"))
        telemetry_box.append(make_pill("Display 1440x3088 (120Hz)", "video-display-symbolic"))
        telemetry_box.append(make_pill("Active GPU: NVIDIA RTX 3060", "applications-system-symbolic"))
        telemetry_box.append(make_pill("Wayland Native", "network-wireless-symbolic"))
        hero_card.append(telemetry_box)

        # Hero Big Action Row
        action_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        action_row.set_margin_top(6)
        action_row.set_margin_bottom(16)
        action_row.set_margin_start(18)
        action_row.set_margin_end(18)

        btn_stream = Gtk.Button(label="  LAUNCH MIRRORING  ")
        btn_stream.add_css_class("suggested-action")
        btn_stream.add_css_class("pill")
        btn_stream.set_hexpand(True)
        btn_stream.set_size_request(-1, 50)

        btn_mk = Gtk.Button(label="CONNECT M/K BRIDGE")
        btn_mk.add_css_class("pill")
        btn_mk.set_size_request(200, 50)

        action_row.append(btn_stream)
        action_row.append(btn_mk)
        hero_card.append(action_row)

        main_box.append(hero_card)

        # ----------------- 1-CLICK QUICK PRESETS GRID -----------------
        preset_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        p_title = Gtk.Label(label="1-Click Performance Presets", xalign=0)
        p_title.add_css_class("heading")
        preset_header.append(p_title)
        main_box.append(preset_header)

        preset_grid = Gtk.Grid()
        preset_grid.set_column_spacing(12)
        preset_grid.set_row_spacing(12)
        preset_grid.set_column_homogeneous(True)
        main_box.append(preset_grid)

        presets = [
            ("🎮 Gaming Pro", "60 FPS • 20ms Jitter Buffer • Vulkan/OpenGL • Low Latency", 0, 0),
            ("💼 Office & Reading", "Native 1440p • 30 FPS • Ultra-Crisp Text • Power Efficient", 1, 0),
            ("🎬 Smooth Media", "60 FPS • H.265 HEVC • 50ms Smooth Buffer • Hi-Fi Audio", 0, 1),
            ("🔋 Battery Saver", "40% Lite Res • Screen Turned Off • Integrated GPU", 1, 1),
        ]

        for title, desc, col, row in presets:
            btn = Gtk.Button()
            btn.add_css_class("card")
            card_b = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            card_b.set_margin_top(12)
            card_b.set_margin_bottom(12)
            card_b.set_margin_start(14)
            card_b.set_margin_end(14)

            t_lbl = Gtk.Label(label=title, xalign=0)
            t_lbl.add_css_class("heading")
            d_lbl = Gtk.Label(label=desc, xalign=0)
            d_lbl.add_css_class("caption")
            d_lbl.add_css_class("dim-label")
            d_lbl.set_wrap(True)

            card_b.append(t_lbl)
            card_b.append(d_lbl)
            btn.set_child(card_b)
            preset_grid.attach(btn, col, row, 1, 1)

        # ----------------- ACCORDION DRAWERS (Adw.ExpanderRow) -----------------
        deep_tune_title = Gtk.Label(label="Detailed Customization", xalign=0)
        deep_tune_title.add_css_class("heading")
        deep_tune_title.set_margin_top(8)
        main_box.append(deep_tune_title)

        drawers_group = Adw.PreferencesGroup()
        main_box.append(drawers_group)

        # Drawer 1: Display & Stream
        exp_disp = Adw.ExpanderRow(title="Display &amp; Stream Pipeline", subtitle="Resolution, Bitrate, FPS, Window mode")
        drawers_group.add(exp_disp)

        r_res = Adw.ComboRow(title="Max Resolution Preset")
        m_r = Gtk.StringList()
        for r in ["Native 100% (1440x3088)", "Balanced 80% (1152x2470)", "Smooth 60% (864x1852)", "Lite 40% (576x1235)"]:
            m_r.append(r)
        r_res.set_model(m_r)
        exp_disp.add_row(r_res)

        r_codec = Adw.ComboRow(title="Video Codec")
        m_c = Gtk.StringList()
        for c in ["H.264", "H.265 / HEVC", "AV1"]: m_c.append(c)
        r_codec.set_model(m_c)
        exp_disp.add_row(r_codec)

        exp_disp.add_row(Adw.SwitchRow(title="Fullscreen Mirroring"))
        exp_disp.add_row(Adw.SwitchRow(title="Borderless Window Mode"))

        # Drawer 2: GPU Acceleration & Wayland
        exp_gpu = Adw.ExpanderRow(title="GPU Acceleration &amp; Wayland Engine", subtitle="PRIME offloading, SDL render driver, Wayland sync")
        drawers_group.add(exp_gpu)

        gpu_choice = Adw.ComboRow(title="Graphics Adapter")
        m_g = Gtk.StringList()
        for g in ["Auto (Mesa Native)", "Dedicated NVIDIA PRIME (__NV_PRIME_RENDER_OFFLOAD=1)", "Integrated AMD Vega"]:
            m_g.append(g)
        gpu_choice.set_model(m_g)
        exp_gpu.add_row(gpu_choice)

        r_drv = Adw.ComboRow(title="SDL Render Driver")
        m_dr = Gtk.StringList()
        for d in ["OpenGL", "OpenGL ES 2", "Vulkan", "Software"]: m_dr.append(d)
        r_drv.set_model(m_dr)
        exp_gpu.add_row(r_drv)

        exp_gpu.add_row(Adw.SwitchRow(title="Display Real-Time FPS Overlay in Console"))

        # Drawer 3: Peripherals & Controls
        exp_ctrl = Adw.ExpanderRow(title="Audio &amp; Peripheral Controls", subtitle="UHID Keyboard/Mouse, Screen power, Audio codec")
        drawers_group.add(exp_ctrl)
        exp_ctrl.add_row(Adw.SwitchRow(title="Hardware Keyboard Forwarding (UHID/OTG)"))
        exp_ctrl.add_row(Adw.SwitchRow(title="Hardware Mouse Forwarding (UHID/OTG)"))
        exp_ctrl.add_row(Adw.SwitchRow(title="Turn Off Device Screen During Mirroring"))
        exp_ctrl.add_row(Adw.SwitchRow(title="Keep Device Screen Awake"))
