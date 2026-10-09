import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw

class Design5ProConsole(Gtk.Box):
    """
    Design 5: Pro Media Console / Split Studio
    Information-dense studio console inspired by OBS and broadcast switchers.
    Left panel provides device telemetry and master triggers;
    Right panel provides dual-deck fine-tuning for stream and GPU pipelines.
    """
    def __init__(self, **kwargs):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=16, **kwargs)
        self.set_hexpand(True)
        self.set_vexpand(True)
        self.set_margin_top(16)
        self.set_margin_bottom(16)
        self.set_margin_start(16)
        self.set_margin_end(16)

        self.setup_ui()

    def setup_ui(self):
        # ----------------- LEFT PANEL: MASTER TELEMETRY & CONTROLS (38%) -----------------
        left_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        left_box.set_size_request(320, -1)
        left_box.set_vexpand(True)
        self.append(left_box)

        # Device Telemetry Card
        dev_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        dev_card.add_css_class("card")
        dev_card.set_margin_top(4)
        dev_card.set_margin_bottom(4)

        dev_h = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        dev_h.set_margin_top(14)
        dev_h.set_margin_start(14)
        dev_h.set_margin_end(14)
        ico = Gtk.Image.new_from_icon_name("phone-symbolic")
        ico.set_pixel_size(28)
        ico.add_css_class("accent")
        dev_h.append(ico)

        lbls = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        l_name = Gtk.Label(label="Samsung Galaxy S23", xalign=0)
        l_name.add_css_class("title-3")
        l_ser = Gtk.Label(label="RFCT10ABCDE • USB 3.2", xalign=0)
        l_ser.add_css_class("caption")
        l_ser.add_css_class("dim-label")
        lbls.append(l_name)
        lbls.append(l_ser)
        dev_h.append(lbls)
        dev_card.append(dev_h)

        # Telemetry Metrics Grid
        m_grid = Gtk.Grid()
        m_grid.set_column_spacing(8)
        m_grid.set_row_spacing(8)
        m_grid.set_column_homogeneous(True)
        m_grid.set_margin_start(14)
        m_grid.set_margin_end(14)
        m_grid.set_margin_bottom(14)

        def make_metric(label, val):
            b = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            b.add_css_class("card")
            b.set_margin_top(2)
            b.set_margin_bottom(2)
            b.set_margin_start(2)
            b.set_margin_end(2)
            vl = Gtk.Label(label=val)
            vl.add_css_class("heading")
            lb = Gtk.Label(label=label)
            lb.add_css_class("caption")
            lb.add_css_class("dim-label")
            b.append(vl)
            b.append(lb)
            return b

        m_grid.attach(make_metric("Battery", "88% ⚡"), 0, 0, 1, 1)
        m_grid.attach(make_metric("Panel Res", "1440x3088"), 1, 0, 1, 1)
        m_grid.attach(make_metric("Host GPU", "RTX 3060"), 0, 1, 1, 1)
        m_grid.attach(make_metric("Wayland", "KWin 6.0"), 1, 1, 1, 1)

        dev_card.append(m_grid)
        left_box.append(dev_card)

        # Master Trigger Controls
        ctrl_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        ctrl_card.add_css_class("card")
        ctrl_card.set_margin_top(4)
        ctrl_card.set_margin_bottom(4)

        ctrl_inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        ctrl_inner.set_margin_top(14)
        ctrl_inner.set_margin_bottom(14)
        ctrl_inner.set_margin_start(14)
        ctrl_inner.set_margin_end(14)

        c_lbl = Gtk.Label(label="Master Action Deck", xalign=0)
        c_lbl.add_css_class("heading")
        ctrl_inner.append(c_lbl)

        btn_stream = Gtk.Button(label="🔴  START MIRRORING")
        btn_stream.add_css_class("suggested-action")
        btn_stream.add_css_class("pill")
        btn_stream.set_size_request(-1, 48)
        ctrl_inner.append(btn_stream)

        btn_mk = Gtk.Button(label="⌨️  M/K FOCUS BRIDGE")
        btn_mk.add_css_class("pill")
        btn_mk.set_size_request(-1, 44)
        ctrl_inner.append(btn_mk)

        ctrl_card.append(ctrl_inner)
        left_box.append(ctrl_card)

        # Real-Time Log / Diagnostics View
        diag_group = Adw.PreferencesGroup(title="Active Session Diagnostics")
        left_box.append(diag_group)

        diag_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        diag_box.add_css_class("card")
        diag_box.set_margin_top(4)
        diag_box.set_margin_bottom(4)
        diag_box.set_margin_start(8)
        diag_box.set_margin_end(8)

        diag_txt = Gtk.Label(
            label="[scrcpy] Ready on serial RFCT10ABCDE\n[SDL] Surface: Wayland xdg_toplevel\n[GPU] Active: PRIME Offload (NVIDIA)\n[Jitter] Buffer: 20ms fixed queue",
            xalign=0
        )
        diag_txt.add_css_class("caption")
        diag_txt.add_css_class("dim-label")
        diag_box.append(diag_txt)
        diag_group.add(diag_box)

        # ----------------- RIGHT PANEL: DUAL DECK TUNING (62%) -----------------
        right_scroll = Gtk.ScrolledWindow()
        right_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        right_scroll.set_hexpand(True)
        right_scroll.set_vexpand(True)
        self.append(right_scroll)

        right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        right_scroll.set_child(right_box)

        # Deck 1: Video Pipeline & Display
        d1_group = Adw.PreferencesGroup(title="Deck 1: Video Pipeline &amp; Display")
        right_box.append(d1_group)

        d1_type = Adw.ComboRow(title="Capture Source")
        m_t = Gtk.StringList()
        m_t.append("Display 0 (Android Screen)")
        m_t.append("Camera 0 (Back Sensor 4000x3000)")
        m_t.append("Camera 1 (Front Sensor 1080p)")
        d1_type.set_model(m_t)
        d1_group.add(d1_type)

        d1_res = Adw.ComboRow(title="Streaming Resolution")
        m_r = Gtk.StringList()
        for r in ["Native 1440x3088", "1080p Balanced", "720p Low Latency"]: m_r.append(r)
        d1_res.set_model(m_r)
        d1_group.add(d1_res)

        d1_codec = Adw.ComboRow(title="Encoder / Codec")
        m_c = Gtk.StringList()
        for c in ["H.265 / HEVC (High Efficiency)", "H.264 (Standard AVC)", "AV1"]: m_c.append(c)
        d1_codec.set_model(m_c)
        d1_group.add(d1_codec)

        d1_group.add(Adw.SwitchRow(title="Fullscreen Projection"))
        d1_group.add(Adw.SwitchRow(title="Always Keep Window On Top"))

        # Deck 2: GPU Acceleration & Latency Optimization
        d2_group = Adw.PreferencesGroup(title="Deck 2: GPU Engine &amp; Wayland Latency")
        right_box.append(d2_group)

        d2_gpu = Adw.ComboRow(title="Graphics Adapter")
        m_g = Gtk.StringList()
        for g in ["Discrete NVIDIA (PRIME Offload)", "Integrated AMD Vega (Mesa)", "Automatic"]: m_g.append(g)
        d2_gpu.set_model(m_g)
        d2_group.add(d2_gpu)

        d2_drv = Adw.ComboRow(title="SDL3 Render Backend")
        m_d = Gtk.StringList()
        for d in ["OpenGL", "OpenGL ES 2", "Vulkan", "Software"]: m_d.append(d)
        d2_drv.set_model(m_d)
        d2_group.add(d2_drv)

        d2_buf = Adw.ComboRow(title="Micro-Jitter Buffer")
        m_b = Gtk.StringList()
        for b in ["0 ms (Hard Real-time)", "20 ms (Smooth 60Hz)", "30 ms (Sweetspot)", "50 ms (Wi-Fi)"]: m_b.append(b)
        d2_buf.set_model(m_b)
        d2_buf.set_selected(1)
        d2_group.add(d2_buf)

        d2_group.add(Adw.SwitchRow(title="Hardware UHID Keyboard &amp; Mouse Forwarding"))
        d2_group.add(Adw.SwitchRow(title="Turn Off Device Screen During Mirroring"))
