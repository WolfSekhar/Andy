import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw

class Design2TabbedDeck(Gtk.Box):
    """
    Design 2: Tabbed Deck with Pinned Footer Dock
    Features a centered Adw.ViewSwitcher with zero-scroll tabbed categories,
    and a floating bottom action dock keeping the Stream trigger always accessible.
    """
    def __init__(self, **kwargs):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, **kwargs)
        self.set_hexpand(True)
        self.set_vexpand(True)

        self.setup_ui()

    def setup_ui(self):
        # Top Tab Bar using ViewSwitcher
        tab_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        tab_header.set_halign(Gtk.Align.CENTER)
        tab_header.set_margin_top(12)
        tab_header.set_margin_bottom(12)
        self.append(tab_header)

        self.stack = Adw.ViewStack()
        self.stack.set_hexpand(True)
        self.stack.set_vexpand(True)

        switcher = Adw.ViewSwitcher()
        switcher.set_stack(self.stack)
        switcher.set_policy(Adw.ViewSwitcherPolicy.WIDE)
        tab_header.append(switcher)

        # Tab 1: Screen Mirroring
        t1_clamp = Adw.Clamp(maximum_size=700)
        t1_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        t1_box.set_margin_top(12)
        t1_clamp.set_child(t1_box)

        grp1 = Adw.PreferencesGroup(title="Display &amp; Stream Configuration")
        t1_box.append(grp1)

        disp_row = Adw.ComboRow(title="Target Display")
        m_disp = Gtk.StringList()
        m_disp.append("Display 0 (Default Screen)")
        m_disp.append("Display 1 (Secondary Screen)")
        disp_row.set_model(m_disp)
        grp1.add(disp_row)

        res_row = Adw.ComboRow(title="Resolution Quality")
        m_res = Gtk.StringList()
        for r in ["1080x2340 (Native)", "864x1872 (Balanced)", "648x1404 (Smooth)", "432x936 (Lite)"]:
            m_res.append(r)
        res_row.set_model(m_res)
        grp1.add(res_row)

        codec_row = Adw.ComboRow(title="Video Codec")
        m_codec = Gtk.StringList()
        for c in ["H.264 (Universally Compatible)", "H.265 / HEVC (Recommended for Low Bandwidth)", "AV1 (Next-Gen Efficiency)"]:
            m_codec.append(c)
        codec_row.set_model(m_codec)
        codec_row.set_selected(1)
        grp1.add(codec_row)

        fps_row = Adw.ComboRow(title="Max FPS")
        m_fps = Gtk.StringList()
        for f in ["60 FPS", "30 FPS", "15 FPS"]:
            m_fps.append(f)
        fps_row.set_model(m_fps)
        grp1.add(fps_row)

        sw_full = Adw.SwitchRow(title="Launch Fullscreen")
        sw_border = Adw.SwitchRow(title="Borderless Window")
        sw_top = Adw.SwitchRow(title="Always On Top")
        grp1.add(sw_full)
        grp1.add(sw_border)
        grp1.add(sw_top)

        page1 = self.stack.add_titled_with_icon(t1_clamp, "screen", "Screen", "video-display-symbolic")

        # Tab 2: Camera Studio
        t2_clamp = Adw.Clamp(maximum_size=700)
        t2_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        t2_box.set_margin_top(12)
        t2_clamp.set_child(t2_box)

        grp2 = Adw.PreferencesGroup(title="Camera Input &amp; Hardware Settings")
        t2_box.append(grp2)

        cam_row = Adw.ComboRow(title="Camera Sensor")
        m_cam = Gtk.StringList()
        m_cam.append("Back Camera 0 (4000x3000, 30fps)")
        m_cam.append("Front Camera 1 (1920x1080, 30fps)")
        m_cam.append("Ultra-Wide Camera 2 (4000x3000)")
        cam_row.set_model(m_cam)
        grp2.add(cam_row)

        cam_res = Adw.ComboRow(title="Camera Output Size")
        m_cres = Gtk.StringList()
        for s in ["1920x1080 (FHD)", "1280x720 (HD)", "3840x2160 (4K)"]:
            m_cres.append(s)
        cam_res.set_model(m_cres)
        grp2.add(cam_res)

        cam_fps = Adw.ComboRow(title="Camera Framerate")
        m_cfps = Gtk.StringList()
        for f in ["60 FPS", "30 FPS"]:
            m_cfps.append(f)
        cam_fps.set_model(m_cfps)
        grp2.add(cam_fps)

        page2 = self.stack.add_titled_with_icon(t2_clamp, "camera", "Camera", "camera-web-symbolic")

        # Tab 3: Controls & Audio
        t3_clamp = Adw.Clamp(maximum_size=700)
        t3_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        t3_box.set_margin_top(12)
        t3_clamp.set_child(t3_box)

        grp3 = Adw.PreferencesGroup(title="Input &amp; Audio Forwarding")
        t3_box.append(grp3)

        aud_codec = Adw.ComboRow(title="Audio Forwarding Codec")
        m_aud = Gtk.StringList()
        for a in ["Opus (Ultra Low Latency)", "AAC (High Fidelity)", "RAW PCM", "Disabled (No Audio)"]:
            m_aud.append(a)
        aud_codec.set_model(m_aud)
        grp3.add(aud_codec)

        grp3.add(Adw.SwitchRow(title="Hardware Keyboard (UHID/OTG Forwarding)"))
        grp3.add(Adw.SwitchRow(title="Hardware Mouse (UHID/OTG Forwarding)"))
        grp3.add(Adw.SwitchRow(title="Turn Screen Off while Connected"))
        grp3.add(Adw.SwitchRow(title="Prevent Device Sleep (Stay Awake)"))

        page3 = self.stack.add_titled_with_icon(t3_clamp, "controls", "Controls & Audio", "input-gaming-symbolic")

        # Tab 4: GPU & Performance
        t4_clamp = Adw.Clamp(maximum_size=700)
        t4_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        t4_box.set_margin_top(12)
        t4_clamp.set_child(t4_box)

        grp4 = Adw.PreferencesGroup(title="GPU Acceleration &amp; Wayland Engine")
        t4_box.append(grp4)

        gpu_row = Adw.ComboRow(title="GPU Renderer Engine")
        m_gpu = Gtk.StringList()
        for g in ["Auto-Detect (Mesa Direct)", "NVIDIA PRIME Offload (__NV_PRIME_RENDER_OFFLOAD=1)", "Integrated AMD Vega"]:
            m_gpu.append(g)
        gpu_row.set_model(m_gpu)
        grp4.add(gpu_row)

        backend_row = Adw.ComboRow(title="Compositor Window Protocol")
        m_back = Gtk.StringList()
        for b in ["Wayland (Native XDG Shell)", "XWayland (X11 Fallback)", "Automatic"]:
            m_back.append(b)
        backend_row.set_model(m_back)
        grp4.add(backend_row)

        buffer_row = Adw.ComboRow(title="Jitter Smoothing Buffer")
        m_buf = Gtk.StringList()
        for bf in ["0 ms (Instant)", "20 ms (Smooth 60Hz)", "30 ms (Sweetspot)", "50 ms (Wi-Fi)"]:
            m_buf.append(bf)
        buffer_row.set_model(m_buf)
        buffer_row.set_selected(1)
        grp4.add(buffer_row)

        grp4.add(Adw.SwitchRow(title="Real-Time FPS Performance Counter"))

        page4 = self.stack.add_titled_with_icon(t4_clamp, "performance", "GPU & Wayland", "applications-system-symbolic")

        # Content area scroll
        content_scroll = Gtk.ScrolledWindow()
        content_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        content_scroll.set_hexpand(True)
        content_scroll.set_vexpand(True)
        content_scroll.set_child(self.stack)
        self.append(content_scroll)

        # ----------------- PERSISTENT BOTTOM ACTION DOCK -----------------
        dock = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        dock.add_css_class("toolbar")
        dock.set_margin_top(8)
        dock.set_margin_bottom(12)
        dock.set_margin_start(16)
        dock.set_margin_end(16)

        # Device selection inside dock
        dev_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        dev_drop = Gtk.DropDown()
        m_d = Gtk.StringList()
        m_d.append("Galaxy S23 (RFCT10ABCDE)")
        m_d.append("Pixel 8 Pro (9A29384723)")
        dev_drop.set_model(m_d)
        dev_drop.set_valign(Gtk.Align.CENTER)
        dev_box.append(dev_drop)

        refresh_btn = Gtk.Button(icon_name="view-refresh-symbolic")
        refresh_btn.set_valign(Gtk.Align.CENTER)
        dev_box.append(refresh_btn)
        dock.append(dev_box)

        # Status badge
        dock.append(Gtk.Box(hexpand=True)) # Spacer

        status_label = Gtk.Label(label="🔋 85% • 1080x2340 • USB 3.0")
        status_label.add_css_class("dim-label")
        status_label.add_css_class("caption")
        dock.append(status_label)

        dock.append(Gtk.Box(hexpand=True)) # Spacer

        # Action Buttons
        actions_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        btn_stream = Gtk.Button(label="STREAM")
        btn_stream.add_css_class("suggested-action")
        btn_stream.add_css_class("pill")
        btn_stream.set_size_request(130, 42)

        btn_mk = Gtk.Button(label="Connect M/K")
        btn_mk.add_css_class("pill")
        btn_mk.set_size_request(130, 42)

        actions_box.append(btn_mk)
        actions_box.append(btn_stream)
        dock.append(actions_box)

        self.append(dock)
