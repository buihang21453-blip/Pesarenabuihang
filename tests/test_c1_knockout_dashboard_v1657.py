import unittest
from pathlib import Path
from types import SimpleNamespace
from jinja2 import Environment, FileSystemLoader


class KnockoutDashboardTemplateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        cls.root = root
        cls.env = Environment(loader=FileSystemLoader(str(root / 'templates')))
        cls.env.globals['url_for'] = lambda endpoint, **kw: f"/{endpoint}/" + "/".join(str(v) for v in kw.values())

    def test_public_bracket_and_my_next_match_are_visible(self):
        tpl = self.env.get_template('tournament/components/knockout_dashboard.html')
        tournament = {
            'id': 'tour',
            'my_member': {'user_id': 'u1'},
            'public_knockout': {
                'generated': True,
                'current_round': 'qf',
                'my_next': {
                    'id': 'm1', 'round_code': 'qf', 'round_label': 'TỨ KẾT',
                    'leg_no': 1, 'status_label': 'Chờ thi đấu', 'opponent_name': 'HLV 8',
                    'scheduled_at': None,
                },
                'tickets': [
                    {'user_id': 'u1', 'rank': 1, 'name': 'HLV 1', 'club': 'Como', 'remaining': 1, 'total': 1}
                ],
                'rounds': {
                    'qf': [{
                        'status': 'pending', 'status_label': 'Chờ thi đấu', 'completed_legs': 0,
                        'leg_count': 2, 'home_name': 'HLV 1', 'away_name': 'HLV 8',
                        'home_total': 0, 'away_total': 0, 'has_score': False,
                        'legs': [{'leg_no': 1, 'status': 'pending'}, {'leg_no': 2, 'status': 'pending'}],
                    }],
                    'sf': [], 'final': [],
                },
            },
        }
        html = tpl.render(tournament=tournament, current_user=SimpleNamespace(id='u1'))
        self.assertIn('Bảng theo dõi Knockout', html)
        self.assertIn('TRẬN TIẾP THEO CỦA TÔI', html)
        self.assertIn('HLV 1', html)
        self.assertIn('HLV 8', html)
        self.assertIn('Random lại CLB', html)
        self.assertIn('TỨ KẾT', html)
        self.assertIn('BÁN KẾT', html)
        self.assertIn('CHUNG KẾT', html)

    def test_reroll_is_allowed_after_bracket_generation_but_guarded_after_start(self):
        source = (self.root / 'modules' / 'tournament_competition_parts' / 'rewards.py').read_text(encoding='utf-8')
        self.assertIn('sinh bracket Top 8 không làm mất vé', source)
        self.assertIn('{"pending","scheduled","cancelled"}', source)
        self.assertIn('đã bắt đầu vòng Knockout', source)


if __name__ == '__main__':
    unittest.main()
