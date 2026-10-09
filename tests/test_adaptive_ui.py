import sys
import os
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src/ui')))

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio

from window import AndyWindow

class TestAdaptiveUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            Adw.init()
        except Exception:
            pass

    def setUp(self):
        import uuid
        app_id = f'com.wolfsekhar.test_adaptive_{uuid.uuid4().hex[:8]}'
        self.app = Adw.Application(application_id=app_id, flags=Gio.ApplicationFlags.NON_UNIQUE)
        with patch('gi.repository.Gdk.Display.get_default', return_value=MagicMock()):
            with patch('scrcpy_manager.get_device_displays', return_value=[]):
                with patch('scrcpy_manager.get_device_cameras', return_value=[]):
                    self.win = AndyWindow(application=self.app)

    def test_backward_compatibility_references(self):
        """Ensure all card references and legacy split_hbox alias remain valid."""
        self.assertIsNotNone(self.win.stream_card)
        self.assertIsNotNone(self.win.advanced_card)
        self.assertIsNotNone(self.win.details_card)
        self.assertIsNotNone(self.win.split_hbox)
        self.assertIs(self.win.split_hbox, self.win.card_flow)

    def test_cards_flow_reflow_geometry(self):
        """
        Verify that FlowBox reflows cards from 1 line (desktop) to 2 lines (tablet)
        to 3 lines (mobile single-column stack), with height increasing accordingly.
        """
        flow = self.win.card_flow
        
        # 1. Desktop width (1200px): All 3 cards fit side-by-side on 1 line
        _, desktop_h, _, _ = flow.measure(Gtk.Orientation.VERTICAL, 1200)
        
        # 2. Tablet width (750px): 2 cards on line 1, 1 card on line 2
        _, tablet_h, _, _ = flow.measure(Gtk.Orientation.VERTICAL, 750)
        
        # 3. Mobile width (380px): 3 lines stacked vertically (1 column)
        _, mobile_h, _, _ = flow.measure(Gtk.Orientation.VERTICAL, 380)

        print(f"\nMeasured Heights: Desktop(1200px)={desktop_h}px, Tablet(750px)={tablet_h}px, Mobile(380px)={mobile_h}px")

        # Desktop height should be the height of 1 row of cards
        self.assertGreater(desktop_h, 0)
        
        # Tablet height should be approximately 2 rows of cards (> desktop)
        self.assertGreater(tablet_h, desktop_h, "Tablet height must be taller than desktop due to 2nd row wrapping")
        
        # Mobile height should be approximately 3 rows of cards (> tablet)
        self.assertGreater(mobile_h, tablet_h, "Mobile height must be taller than tablet due to single-column vertical stacking")

    def test_window_mobile_minimum_width(self):
        """
        Verify that the window's minimum width request is <= 360px,
        allowing it to easily fit on mobile phone screens (PinePhone, Librem 5, Phosh, Plasma Mobile).
        """
        flow = self.win.card_flow
        min_card_flow_w, _, _, _ = flow.measure(Gtk.Orientation.HORIZONTAL, -1)
        self.assertLessEqual(min_card_flow_w, 360, f"Card flow min width {min_card_flow_w}px must be <= 360px for mobile")

        top_bin = self.win.top_breakpoint_bin
        min_top_w, _, _, _ = top_bin.measure(Gtk.Orientation.HORIZONTAL, -1)
        self.assertLessEqual(min_top_w, 360, f"Top bar min width {min_top_w}px must be <= 360px for mobile")

    def test_top_action_bar_breakpoint_configuration(self):
        """Verify that the top bar has an active BreakpointBin with max-width condition."""
        self.assertIsInstance(self.win.top_breakpoint_bin, Adw.BreakpointBin)
        self.assertIsInstance(self.win.top_hbox, Gtk.Box)
        self.assertIsInstance(self.win.top_buttons_box, Gtk.Box)
        self.assertTrue(self.win.stream_button.get_hexpand())
        self.assertTrue(self.win.connect_mk_button.get_hexpand())

if __name__ == '__main__':
    unittest.main()
