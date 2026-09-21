"""V1.6.47 room header layout regression checks (no external services required)."""
import unittest
from pathlib import Path
from jinja2 import Environment

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "room_detail.html"

class RoomModeHeaderV1647Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = TEMPLATE.read_text(encoding="utf-8")
        cls.topbar = cls.source.split('<div class="room-stage-topbar panel">', 1)[1].split('<div class="room-match-shell room-arena-frame">', 1)[0]

    def test_jinja_compiles(self):
        Environment().parse(self.source)

    def test_logo_removed_only_from_header(self):
        self.assertNotIn('room-stage-arena-logo', self.topbar)
        self.assertNotIn('pes-arena-room-logo.webp', self.topbar)

    def test_header_order_and_mode_labels(self):
        self.assertLess(self.topbar.index('room-stage-title-wrap'), self.topbar.index('room-mode-switch-strip'))
        self.assertLess(self.topbar.index('room-mode-switch-strip'), self.topbar.index('room-stage-share-wrap'))
        for label in ('RANK', 'Xếp hạng', 'C1', 'Giải đấu', 'MINI CUP'):
            self.assertIn(label, self.topbar)
        self.assertIn('quickCreateC1RoomForm', self.topbar)
        self.assertIn('data-room-layout-tab="mini_cup"', self.topbar)

    def test_center_grid_with_symmetric_outer_tracks(self):
        self.assertIn('grid-template-columns:minmax(205px,1fr) minmax(315px,520px) minmax(205px,1fr)', self.source)
        self.assertIn('grid-column:1;grid-row:1;min-width:0;justify-self:start;', self.source)
        self.assertIn('grid-column:2;grid-row:1;justify-self:center;', self.source)
        self.assertIn('grid-column:3;grid-row:1;min-width:0;justify-self:end;', self.source)

    def test_responsive_and_share_conditional(self):
        self.assertIn('@media(max-width:1120px)', self.source)
        self.assertIn('@media(max-width:620px)', self.source)
        self.assertIn('grid-column:1/-1;grid-row:2;justify-self:center;', self.source)
        self.assertIn("{% if room.status == 'waiting_ready' and not room.has_guest", self.topbar)

if __name__ == '__main__':
    unittest.main()
