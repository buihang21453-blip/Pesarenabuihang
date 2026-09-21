"""No-DB regression: clubs used in each player's last five Rank matches cannot recur."""
import ast
import random
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from modules import legacy_team_random_service as random_service

ROOT = Path(__file__).resolve().parents[1]


class _Query:
    def __init__(self, rows):
        self.rows = rows
        self.column = None
        self.user_id = None
        self.size = 100

    def select(self, *_args): return self
    def eq(self, column, value):
        self.column, self.user_id = column, value
        return self
    def order(self, *_args, **_kwargs): return self
    def limit(self, count):
        self.size = count
        return self
    def execute(self):
        rows = [r for r in self.rows if str(r.get(self.column)) == str(self.user_id)]
        rows.sort(key=lambda r: r.get('created_at') or '', reverse=True)
        return SimpleNamespace(data=rows[:self.size])


class _DB:
    def __init__(self, rows): self.rows = rows
    def table(self, name):
        if name != 'matches': raise AssertionError(name)
        return _Query(self.rows)


def load_history(rows, fail=False):
    """Test production function in isolation without bootstrapping Flask/Supabase."""
    src = (ROOT / 'app.py').read_text(encoding='utf-8')
    node = next(n for n in ast.parse(src).body
                if isinstance(n, ast.FunctionDef) and n.name == '_recent_rank_team_names')
    mod = ast.Module(body=[node], type_ignores=[])
    namespace = {
        'RECENT_TEAM_EXCLUSION_COUNT': 5,
        'db': _DB(rows),
        'execute_query': (lambda query, *_args, **_kwargs: query.execute()) if not fail else
                         (lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError('connection lost'))),
        'app': SimpleNamespace(logger=SimpleNamespace(warning=lambda *_args: None)),
    }
    exec(compile(mod, '<history>', 'exec'), namespace)
    return namespace['_recent_rank_team_names']


def match(mid, player, team, opponent, date, status='confirmed', note=''):
    return dict(id=mid, player1_id=player, player2_id=opponent, team1=team,
                team2='Opponent Club', status=status, note=note, created_at=date)


class HistoryTests(unittest.TestCase):
    def test_last_five_across_different_opponents_and_both_sides(self):
        rows = [match(f'm{i}', 'me', f'Club{i}', f'opponent{i}', f'2026-09-{i:02d}T12:00:00')
                for i in range(1, 7)]
        rows[4]['player1_id'], rows[4]['player2_id'] = rows[4]['player2_id'], rows[4]['player1_id']
        rows[4]['team1'], rows[4]['team2'] = rows[4]['team2'], rows[4]['team1']
        self.assertEqual(load_history(rows)('me'), ['Club6', 'Club5', 'Club4', 'Club3', 'Club2'])

    def test_cancelled_before_team_does_not_consume_match_slot(self):
        rows = [match('no_team', 'me', 'Chưa quay đội', 'x', '2026-09-20T00:00:00', status='cancelled')]
        rows += [match(f'm{i}', 'me', f'Club{i}', 'x', f'2026-09-{i:02d}T00:00:00') for i in range(1, 7)]
        self.assertEqual(load_history(rows)('me'), ['Club6', 'Club5', 'Club4', 'Club3', 'Club2'])

    def test_random_selection_all_three_teams_and_five_matches_not_five_names(self):
        rows = [match(f'm{i}', 'me', f'Club{i}', 'x', f'2026-09-{i:02d}T00:00:00') for i in range(1, 6)]
        rows[-1]['team1'] = 'Alpha + Beta + Gamma'
        rows[-1]['note'] = '[MODE:random_selection_match]'
        self.assertEqual(load_history(rows)('me'), ['Alpha', 'Beta', 'Gamma', 'Club4', 'Club3', 'Club2', 'Club1'])

    def test_in_progress_already_allocated_and_forfeit(self):
        rows = [match('m1', 'me', 'Already Assigned', 'x', '2026-09-21T01:00:00', 'playing'),
                match('m2', 'me', 'Forfeit Club', 'y', '2026-09-20T01:00:00', 'cancelled', '[FORFEIT:host]')]
        self.assertEqual(load_history(rows)('me'), ['Already Assigned', 'Forfeit Club'])

    def test_failure_fails_closed(self):
        with self.assertRaisesRegex(ValueError, 'Không đọc được lịch sử'):
            load_history([], fail=True)('me')


class RandomTests(unittest.TestCase):
    @staticmethod
    def teams(count=16):
        return [dict(display=f'Club{i}', team=f'Club{i}', tier='A', overall=80,
                     total_stats=1000, power_score=80, logo_url='', league='League', id=i)
                for i in range(count)]

    def setup_patches(self, teams, history):
        patches = [
            patch.object(random_service, '_all_random_teams', return_value=teams),
            patch.object(random_service, '_recent_rank_team_names', side_effect=lambda uid: history[uid], create=True),
            patch.object(random_service, 'get_rank_level', return_value=0, create=True),
            patch.object(random_service, 'get_rank_tier_weights', return_value={'A': 100.0}, create=True),
            patch.object(random_service, 'load_rank_ranges', return_value=[{'name': 'Test'}], create=True),
            patch.object(random_service, 'power_score_to_tier', return_value='A', create=True),
            patch.object(random_service, 'CLUB_TIER_ORDER', ['A'], create=True),
            patch.object(random_service, 'SMART_RANDOM_MODE', 'Smart Tier Random', create=True),
            patch.object(random_service, 'random', random, create=True),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def test_single_random_no_repeats_for_either_player_or_within_match(self):
        self.setup_patches(self.teams(), {'a': [f'Club{i}' for i in range(5)],
                                          'b': [f'Club{i}' for i in range(5, 10)]})
        for _ in range(40):
            result = random_service.smart_random_team_pair({'id': 'a'}, {'id': 'b'})
            self.assertNotIn(result['team_a'], [f'Club{i}' for i in range(5)])
            self.assertNotIn(result['team_b'], [f'Club{i}' for i in range(5, 10)])
            self.assertNotEqual(result['team_a'], result['team_b'])

    def test_random3_six_distinct_options_and_no_repeat(self):
        self.setup_patches(self.teams(), {'a': [f'Club{i}' for i in range(5)],
                                          'b': [f'Club{i}' for i in range(5, 10)]})
        with patch.object(random_service, 'FRIENDLY_RANDOM3_MODE', 'random3_pick1', create=True):
            result = random_service.build_friendly_random3_state({'id': 'a'}, {'id': 'b'})
        host = [t['name'] for t in result['host_options']]
        guest = [t['name'] for t in result['guest_options']]
        self.assertEqual(len(set(host + guest)), 6)
        self.assertFalse(set(host).intersection(f'Club{i}' for i in range(5)))
        self.assertFalse(set(guest).intersection(f'Club{i}' for i in range(5, 10)))

    def test_exhausted_pool_rejects_repeat_instead_of_relaxing_history(self):
        self.setup_patches(self.teams(5), {'a': [f'Club{i}' for i in range(5)], 'b': []})
        with self.assertRaisesRegex(ValueError, 'Không còn đủ CLB hợp lệ'):
            random_service.smart_random_team_pair({'id': 'a'}, {'id': 'b'})
        with patch.object(random_service, '_all_random_teams', return_value=self.teams(6)), \
             patch.object(random_service, 'FRIENDLY_RANDOM3_MODE', 'random3_pick1', create=True):
            with self.assertRaisesRegex(ValueError, 'Không còn đủ CLB hợp lệ'):
                random_service.build_friendly_random3_state({'id': 'a'}, {'id': 'b'})


if __name__ == '__main__':
    unittest.main()
