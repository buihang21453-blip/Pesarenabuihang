"""V1.6.33: pure regression tests for C1 lobby layout and 3-day opponent times."""
import ast
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).resolve().parents[1]


class LobbyVisibilityTests(unittest.TestCase):
    def test_lobby_four_opponents_have_three_days_and_overlaps(self):
        env = Environment(loader=FileSystemLoader(str(ROOT / 'templates')))
        today = [
            {'label': 'Hôm nay', 'weekday': 'Thứ Sáu', 'slots': [{'iso': '2026-09-18T19:00:00+07:00', 'label': '19:00 – 20:00'}]},
            {'label': 'Ngày mai', 'weekday': 'Thứ Bảy', 'slots': []},
            {'label': 'Ngày kia', 'weekday': 'Chủ nhật', 'slots': []},
        ]
        rivals = []
        for number in range(4):
            rivals.append({
                'name': f'Đối thủ {number}', 'tier': number % 3 + 1,
                'club': f'CLB {number}', 'club_pot': number % 3 + 1,
                'club_logo': '', 'zalo': '',
                'availability_days': [{
                    'label': d['label'], 'weekday': d['weekday'],
                    'opponent_slots': [{'iso': '2026-09-18T19:00:00+07:00', 'label': '19:00', 'is_overlap': True}] if i == 0 else [],
                } for i, d in enumerate(today)],
            })
        hub = {
            'days': today, 'mine_set': {'2026-09-18T19:00:00+07:00'},
            'mine_availability_days': [
                {'label':'Hôm nay','weekday':'Thứ Sáu','opponent_slots':[
                    {'iso':'2026-09-18T19:00:00+07:00','label':'19:00','is_overlap':True},
                    {'iso':'2026-09-18T19:30:00+07:00','label':'19:30','is_overlap':True},
                ]},
                {'label':'Ngày mai','weekday':'Thứ Bảy','opponent_slots':[]},
                {'label':'Ngày kia','weekday':'Chủ nhật','opponent_slots':[]},
            ],
            'league_opponents': rivals, 'is_test': False,
            'admin_preview': False, 'host_ready': [{'display_name':'Không được thấy', 'region': 'HN'}],
            'availability_error': False,
        }
        html = env.get_template('tournament/tabs/lobby.html').render(tournaments=[{
            'id': 'tour', 'name': 'CHAMPION LEAGUE ARENA',
            'landing_hub': hub, 'needs_availability_gate': False,
        }])
        self.assertEqual(html.count('class="c1-lobby-rival"'), 4)
        self.assertEqual(html.count('class="c1-lobby-day"'), 12)
        self.assertEqual(html.count('is-overlap'), 6)
        self.assertIn('c1-lobby-my-time is-overlap', html)
        self.assertLess(html.index('01 · LỊCH CỦA TÔI'), html.index('02 · LỊCH RẢNH CỦA ĐỐI THỦ'))
        self.assertIn('19:30', html)
        self.assertNotIn('Host đang rảnh', html)
        for rival in rivals:
            self.assertIn(rival['name'], html)
            self.assertIn(rival['club'], html)

    def test_lobby_availability_helpers_and_css_structure(self):
        source = (ROOT / 'modules/tournament_routes.py').read_text()
        tree = ast.parse(source)
        routes = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'register_routes')
        fn = next(n for n in routes.body if isinstance(n, ast.FunctionDef) and n.name == '_landing_group_slots')
        module = ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[]))
        days = [{'date': '2026-09-18', 'label': 'Hôm nay'},
                {'date': '2026-09-19', 'label': 'Ngày mai'},
                {'date': '2026-09-20', 'label': 'Ngày kia'}]
        namespace = {'_landing_availability_days': lambda: days, 'datetime': datetime}
        exec(compile(module, '<lobby helper>', 'exec'), namespace)
        iso = '2026-09-18T19:30:00+07:00'
        output = namespace['_landing_group_slots']([iso], {iso})
        self.assertEqual(len(output), 3)
        self.assertEqual(output[0]['opponent_slots'][0]['label'], '19:30')
        self.assertTrue(output[0]['opponent_slots'][0]['is_overlap'])
        css = (ROOT / 'templates/tournament/styles.html').read_text()
        self.assertEqual(css.count('<style>'), 1)
        self.assertEqual(css.count('</style>'), 1)
        self.assertLess(css.index('.c1-lobby-mine'), css.index('</style>'))
        self.assertIn('tournament_lobby_four_league_fixtures', source)
        self.assertIn('tournament_lobby_all_opponent_availability', source)
        self.assertIn('admin_c1_lobby_full_availability', source)


if __name__ == '__main__':
    unittest.main()
