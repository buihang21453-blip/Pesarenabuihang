"""V1.6.40 regression checks: GĐ2 assigned clubs, readiness, result UI."""
import unittest
from types import SimpleNamespace
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from modules.c1_fixed_match_service import start_assigned_club_match


class Query:
    def __init__(self, db, name):
        self.db, self.name, self.filters, self.action, self.patch = db, name, [], 'select', {}

    def select(self, *_): return self
    def eq(self, k, v): self.filters.append((k, v)); return self
    def in_(self, k, vals): self.filters.append((k, tuple(vals))); return self
    def limit(self, *_): return self
    def update(self, values): self.action = 'update'; self.patch = values; return self

    def result(self):
        rows = [r for r in self.db.rows[self.name] if all(
            (r.get(k) in v if isinstance(v, tuple) else r.get(k) == v)
            for k, v in self.filters)]
        if self.action == 'update':
            if self.name == 'tournament_matches' and self.db.fail_match:
                return SimpleNamespace(data=[])
            for row in rows: row.update(self.patch)
        return SimpleNamespace(data=[dict(x) for x in rows])


class DB:
    def __init__(self):
        import json
        self.fail_match = False
        self.rows = {
            'match_rooms': [dict(id='room', status='waiting_ready', guest_ready=True,
                                 host_user_id='h', guest_user_id='g',
                                 host_team='OLD', guest_team=None,
                                 note='TOURNAMENT_ROOM|' + json.dumps(dict(
                                     tournament_id='tour', tournament_match_id='fixture',
                                     stage_code='league')))],
            'tournament_matches': [dict(id='fixture', tournament_id='tour', status='pending',
                                        stage_code='league', home_user_id='h', away_user_id='g')],
            'tournament_stages': [dict(tournament_id='tour', stage_code='league', status='open')],
            'tournament_members': [dict(tournament_id='tour', user_id='h', status='active', fixed_club_name='Porto'),
                                   dict(tournament_id='tour', user_id='g', status='active', fixed_club_name='Napoli')],
        }

    def table(self, name): return Query(self, name)


def execute(query, *_args, **_kwargs): return query.result()


class FixedMatchTests(unittest.TestCase):
    def setUp(self): self.db = DB()

    def start(self):
        return start_assigned_club_match(self.db, execute, 'tour', 'room', lambda: '2026-09-19T10:00:00Z')

    def test_ready_assigns_both_clubs_and_starts_linked_fixture(self):
        ok, message, clubs = self.start()
        self.assertTrue(ok, message)
        self.assertEqual(clubs, ('Porto', 'Napoli'))
        self.assertEqual(self.db.rows['match_rooms'][0]['status'], 'playing')
        self.assertEqual(self.db.rows['tournament_matches'][0]['status'], 'playing')
        self.assertEqual(self.db.rows['match_rooms'][0]['host_team'], 'Porto')

    def test_not_ready_does_not_start(self):
        self.db.rows['match_rooms'][0]['guest_ready'] = False
        ok, _, _ = self.start()
        self.assertFalse(ok)
        self.assertEqual(self.db.rows['tournament_matches'][0]['status'], 'pending')

    def test_wrong_opponent_does_not_start(self):
        self.db.rows['match_rooms'][0]['guest_user_id'] = 'outsider'
        ok, _, _ = self.start()
        self.assertFalse(ok)
        self.assertEqual(self.db.rows['tournament_matches'][0]['status'], 'pending')

    def test_room_rolls_back_when_fixture_transition_fails(self):
        self.db.fail_match = True
        with self.assertRaises(RuntimeError): self.start()
        self.assertEqual(self.db.rows['match_rooms'][0]['status'], 'waiting_ready')
        self.assertEqual(self.db.rows['tournament_matches'][0]['status'], 'pending')

    def test_already_playing_is_idempotent(self):
        self.start()
        ok, _, _ = self.start()
        self.assertTrue(ok)
        self.assertEqual(self.db.rows['tournament_matches'][0]['status'], 'playing')


class UIContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        cls.env = Environment(loader=FileSystemLoader(str(root / 'templates')))
        cls.env.globals['url_for'] = lambda endpoint, **kw: '/' + endpoint

    def test_guest_ready_without_draw(self):
        tpl = self.env.get_template('partials/c1_fixed_waiting_controls.html')
        html = tpl.render(room=dict(id='room', has_guest=True, guest_ready=False,
                                    host_team='Porto', guest_team='Napoli'),
                          room_viewer_is_guest=True, room_room_viewer_is_host=False,
                          tournament_fixed_clubs_ready=True,
                          tournament_meta=dict(tournament_id='tour'))
        self.assertIn('SẴN SÀNG THI ĐẤU', html)
        self.assertNotIn('🎲', html)
        self.assertIn('room_guest_ready', html)

    def test_same_result_ui_for_league_host_and_guest(self):
        tpl = self.env.get_template('partials/tournament_room_result.html')
        common = dict(is_tournament_room=True,
                      tournament_meta=dict(stage_code='league', tournament_id='tour'),
                      tournament_match=dict(id='fixture', status='playing'),
                      tournament_fixed_club_mode=True,
                      tournament_result_proposal={},
                      current_user=dict(role='player'),
                      room=dict(id='room', status='playing', host_name='A', guest_name='B',
                                host_team='Porto', guest_team='Napoli'))
        html = tpl.render(**common, room_room_viewer_is_host=True, room_viewer_is_guest=False)
        self.assertIn('tournament_room_submit_result', html)
        self.assertIn('name="host_score"', html)
        self.assertIn('name="guest_score"', html)
        common['room']['status'] = 'waiting_result_confirm'
        html = tpl.render(**common, room_room_viewer_is_host=False, room_viewer_is_guest=True)
        self.assertIn('tournament_room_confirm_result', html)
        self.assertIn('tournament_room_dispute_result', html)

    def test_missing_linked_fixture_is_explicit(self):
        tpl = self.env.get_template('partials/tournament_room_result.html')
        html = tpl.render(is_tournament_room=True,
                          tournament_meta=dict(stage_code='league', tournament_id='tour'),
                          tournament_match=None, tournament_fixed_club_mode=True)
        self.assertIn('Không tải được trận C1 GĐ2', html)
        self.assertNotIn('tournament_room_submit_result', html)


if __name__ == '__main__': unittest.main()
