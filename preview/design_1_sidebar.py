import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gdk

class Design1Sidebar(Gtk.Box):
    """
    Design 1: Modern GNOME NavigationSplitView
    Features a clean left sidebar for device telemetry & mode navigation,
    and a wide, well-categorized settings canvas on the right.
    """
    def __init__(self, **kwargs):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, **kwargs)
        self.set_hexpand(True)
        self.set_vexpand(True)

        self.setup_ui()

    def setup_ui(self):
        # Navigation Split View
        self.split_view = Adw.NavigationSplitView()
        self.split_view.set_hexpand(True)
        self.split_view.set_vexpand(True)
        self.split_view.set_min_sidebar_width(280)
        self.split_view.set_max_sidebar_width(340)
        self.append(self.split_view)

        # ----------------- SIDEBAR -----------------
        sidebar_page = Adw.NavigationPage(title="Devices &amp; Modes")
        sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        sidebar_box.set_margin_top(16)
        sidebar_box.set_margin_bottom(16)
        sidebar_box.set_margin_start(16)
        sidebar_box.set_margin_end(16)
        sidebar_page.set_child(sidebar_box)
        self.split_view.set_sidebar(sidebar_page)

        # Device Card (Hero Badge)
        device_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        device_card.add_css_class("card")
        device_card.set_margin_bottom(8)

        dev_title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        dev_title_box.set_margin_top(12)
        dev_title_box.set_margin_start(12)
        dev_title_box.set_margin_end(12)

        phone_icon = Gtk.Image.new_from_icon_name("phone-symbolic")
        phone_icon.set_pixel_size(24)
        dev_title_box.append(phone_icon)

        dev_lbl_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        dev_name = Gtk.Label(label="Samsung Galaxy S23", xalign=0)
        dev_name.add_css_class("heading")
        dev_serial = Gtk.Label(label="RFCT10ABCDE • Android 14", xalign=0)
        dev_serial.add_css_class("caption")
        dev_serial.add_css_class("dim-label")
        dev_lbl_box.append(dev_name)
        dev_lbl_box.append(dev_serial)
        dev_title_box.append(dev_lbl_box)
        device_card.append(dev_title_box)

        # Quick stats badges
        badge_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        badge_box.set_margin_start(12)
        badge_box.set_margin_end(12)
        badge_box.set_margin_bottom(12)

        batt_pill = Gtk.Label(label="⚡ 85% Battery")
        batt_pill.add_css_class("caption")
        batt_pill.add_css_class("pill")
        batt_pill.add_css_class("accent")

        res_pill = Gtk.Label(label="📺 1080x2340")
        res_pill.add_css_class("caption")
        res_pill.add_css_class("pill")

        badge_box.append(batt_pill)
        badge_box.append(res_pill)
        device_card.append(badge_box)
        sidebar_box.append(device_card)

        # Navigation Mode List
        mode_group = Adw.PreferencesGroup(title="Active Mode")
        sidebar_box.append(mode_group)

        self.mode_list = Gtk.ListBox()
        self.mode_list.add_css_class("boxed-list")
        self.mode_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        mode_group.add(self.mode_list)

        modes = [
            ("Screen Mirroring", "display-symbolic", "Stream full Android screen"),
            ("Camera Stream", "camera-photo-symbolic", "Use phone as high-res webcam"),
            ("Mouse &amp; Keyboard", "input-keyboard-symbolic", "Low-resource input bridge")
        ]

        for title, icon, desc in modes:
            row = Adw.ActionRow(title=title, subtitle=desc)
            img = Gtk.Image.new_from_icon_name(icon)
            row.add_prefix(img)
            self.mode_list.append(row)
        self.mode_list.select_row(self.mode_list.get_row_at_index(0))

        # Bottom Launch Actions in Sidebar
        sidebar_box.append(Gtk.Box(vexpand=True)) # Spacer

        btn_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        start_btn = Gtk.Button(label="Start Mirroring")
        start_btn.add_css_class("suggested-action")
        start_btn.add_css_class("pill")
        start_btn.set_size_request(-1, 46)

        mk_btn = Gtk.Button(label="Connect M/K Only")
        mk_btn.add_css_class("flat")
        mk_btn.add_css_class("pill")

        btn_box.append(start_btn)
        btn_box.append(mk_btn)
        sidebar_box.append(btn_box)

        # ----------------- CONTENT CANVAS -----------------
        content_page = Adw.NavigationPage(title="Configuration")
        content_scroll = Gtk.ScrolledWindow()
        content_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        content_page.set_child(content_scroll)
        self.split_view.set_content(content_page)

        clamp = Adw.Clamp(maximum_size=800)
        clamp.set_margin_top(24)
        clamp.set_margin_bottom(24)
        clamp.set_margin_start(24)
        clamp.set_margin_end(24)
        content_scroll.set_child(clamp)

        canvas_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        clamp.set_child(canvas_box)

        # Display & Resolution Group
        disp_group = Adw.PreferencesGroup(title="Display &amp; Quality Presets")
        canvas_box.append(disp_group)

        res_row = Adw.ComboRow(title="Resolution Quality")
        res_model = Gtk.StringList()
        for r in ["1080x2340 (100% Native)", "864x1872 (80% Balanced)", "648x1404 (60% Smooth)", "432x936 (40% Lite)"]:
            res_model.append(r)
        res_row.set_model(res_model)
        disp_group.add(res_row)

        fps_row = Adw.ComboRow(title="Frame Rate Limit")
        fps_model = Gtk.StringList()
        for f in ["60 FPS (Ultra Smooth)", "30 FPS (Standard)", "15 FPS (Power Saver)"]:
            fps_model.append(f)
        fps_row.set_model(fps_model)
        disp_group.add(fps_row)

        bitrate_row = Adw.EntryRow(title="Bitrate (Mbps)")
        bitrate_row.set_text("8")
        disp_group.add(bitrate_row)

        # Hardware & GPU Tuning Group
        gpu_group = Adw.PreferencesGroup(title="Hardware &amp; GPU Acceleration (Wayland)")
        canvas_box.append(gpu_group)

        gpu_adapter = Adw.ComboRow(title="GPU Adapter")
        gpu_m = Gtk.StringList()
        for g in ["Default (Auto)", "Discrete (NVIDIA PRIME Offload)", "Integrated (AMD Vega / Intel)"]:
            gpu_m.append(g)
        gpu_adapter.set_model(gpu_m)
        gpu_group.add(gpu_adapter)

        render_drv = Adw.ComboRow(title="Render Driver (SDL3)")
        drv_m = Gtk.StringList()
        for d in ["OpenGL (Standard)", "OpenGL ES 2 (Low Overhead)", "Vulkan (Experimental)", "Software (CPU Fallback)"]:
            drv_m.append(d)
        render_drv.set_model(drv_m)
        gpu_group.add(render_drv)

        buffer_row = Adw.ComboRow(title="Micro-Jitter Buffer")
        buf_m = Gtk.StringList()
        for b in ["0 ms (Lowest Latency)", "20 ms (Smooth 60Hz)", "30 ms (Recommended)", "50 ms (Wi-Fi Stability)"]:
            buf_m.append(b)
        buffer_row.set_model(buf_m)
        buffer_row.set_selected(1)
        gpu_group.add(buffer_row)

        fps_log_switch = Adw.SwitchRow(title="Real-Time FPS Performance Overlay")
        gpu_group.add(fps_log_switch)

        # Peripheral & Power Group
        periph_group = Adw.PreferencesGroup(title="Device Peripherals &amp; Controls")
        canvas_box.append(periph_group)

        sw_screen_off = Adw.SwitchRow(title="Turn Off Device Screen During Mirroring")
        sw_stay_awake = Adw.SwitchRow(title="Keep Device Awake")
        sw_uhid_kb = Adw.SwitchRow(title="Hardware Keyboard Forwarding (UHID/OTG)")
        sw_uhid_mouse = Adw.SwitchRow(title="Hardware Mouse Forwarding (UHID/OTG)")

        periph_group.add(sw_screen_off)
        periph_group.add(sw_stay_awake)
        periph_group.add(sw_uhid_kb)
        periph_group.add(sw_uhid_mouse)
