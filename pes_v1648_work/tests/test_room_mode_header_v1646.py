"""Regression checks for V1.6.46 room mode tabs inside the room header."""
import re
import unittest
from pathlib import Path

from jinja2 import Environment

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "room_detail.html"


class RoomModeHeaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = TEMPLATE.read_text(encoding="utf-8")

    def test_jinja_syntax(self):
        Environment().parse(self.source)

    def test_mode_nav_nested_in_topbar_not_separate_strip(self):
        start = self.source.index('<div class="room-stage-topbar panel">')
        nav = self.source.index('<div class="room-mode-switch-strip">', start)
        share = self.source.index('<div class="room-stage-share-wrap">', nav)
        end_topbar = self.source.index('<div class="room-match-shell room-arena-frame">', share)
        # Jinja branch markup is unrendered, but top-level balance of div elements
        # must place the navigation and sharing UI in the same header.
        before = self.source[start:nav]
        self.assertEqual(before.count('<div'), before.count('</div>') + 1)
        self.assertEqual(self.source[start:end_topbar].count('room-mode-switch-strip'), 1)
        self.assertLess(nav, share)
        self.assertNotIn('<div class="room-mode-switch-strip panel">', self.source)

    def test_three_modes_and_existing_actions_preserved(self):
        strip = self.source.split('<div class="room-mode-switch-strip">', 1)[1].split('</div>\n\n        {% if room.status', 1)[0]
        self.assertLess(strip.index('RANK'), strip.index('C1'))
        self.assertLess(strip.index('C1'), strip.index('MINI CUP'))
        self.assertIn('quickCreateRoomForm', strip)
        self.assertIn('quickCreateC1RoomForm', strip)
        self.assertIn('data-room-layout-tab="mini_cup"', strip)
        self.assertIn('id="copyRoomShareLink"', self.source)
        self.assertIn('function bindRoomModeTabs()', self.source)

    def test_responsive_header_layout(self):
        self.assertIn('three mode buttons centered', self.source)
        self.assertIn('grid-column:2;grid-row:1;justify-self:center;', self.source)
        self.assertIn('@media(max-width:1120px)', self.source)
        self.assertIn('@media(max-width:620px)', self.source)
        self.assertNotIn('room-stage-arena-logo', self.source.split('<div class="room-stage-topbar panel">',1)[1].split('<div class="room-match-shell room-arena-frame">',1)[0])


if __name__ == '__main__':
    unittest.main()
