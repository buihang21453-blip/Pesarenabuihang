"""No-DB regression checks for weekday/weekend caps and exempt RP rewards."""
import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from modules.rank_daily_policy import day_limits, apply_match_cap
from modules import daily_rank_limit_service as service

VN = timezone(timedelta(hours=7))


class DailyPolicyTests(unittest.TestCase):
    def test_limits(self):
        self.assertEqual(day_limits(datetime(2026, 9, 21, tzinfo=VN)), (10, 180))
        self.assertEqual(day_limits(datetime(2026, 9, 19, tzinfo=VN)), (20, 250))
        self.assertEqual(day_limits(datetime(2026, 9, 20, tzinfo=VN)), (20, 250))

    def test_partial_base_plus_full_bonus(self):
        delta, detail = apply_match_cap(25, 179, 180, 5)
        self.assertEqual((delta, detail['base_applied'], detail['streak_bonus']), (6, 1, 5))

    def test_loss_protected_only_after_cap(self):
        self.assertEqual(apply_match_cap(-22, 180, 180)[0], 0)
        self.assertEqual(apply_match_cap(-22, 179, 180)[0], -22)
        self.assertEqual(apply_match_cap(-22, 250, 250)[0], 0)

    def test_bonus_unlimited_outside_base_cap(self):
        self.assertEqual(apply_match_cap(15, 180, 180, 15)[0], 15)
        self.assertEqual(apply_match_cap(15, 250, 250, 15)[0], 15)
        self.assertEqual(apply_match_cap(25, 249, 250, 15)[0], 16)

    def test_excess_game_must_be_zero_before_cap(self):
        # Result service suppresses all delta/bonus before running this cap.
        self.assertEqual(apply_match_cap(0, 180, 180, 0)[0], 0)

    def test_positive_counter_uses_only_base_applied(self):
        rows = [
            dict(id='a', player1_id='me', player2_id='other', status='confirmed', delta1=37, delta2=-18,
                 rp_details={'daily_rank_limits': {'positive_rp_cap': {'player1': {'base_applied': 22, 'streak_bonus': 15}}}}),
            dict(id='b', player1_id='other', player2_id='me', status='confirmed', delta1=-17, delta2=12,
                 rp_details={'daily_rank_limits': {'positive_rp_cap': {'player2': {'base_applied': 2, 'streak_bonus': 10}}}}),
            dict(id='c', player1_id='me', player2_id='other', status='confirmed', delta1=20, delta2=-20,
                 rp_details={}),
        ]
        original = service._matches_today
        try:
            service._matches_today = lambda uid: rows
            self.assertEqual(service.positive_rp_today('me'), 44)
            self.assertEqual(service.positive_rp_today('me', exclude_match_id='a'), 22)
        finally:
            service._matches_today = original

    def test_weekly_bonus_is_separate_from_match_counter(self):
        from modules.weekly_rp_rewards_service import _reward_rules, DEFAULT_WEEKLY_RP_REWARD_CONFIG
        self.assertEqual(sum(x[2] for x in _reward_rules(DEFAULT_WEEKLY_RP_REWARD_CONFIG)), 120)


if __name__ == '__main__':
    unittest.main()

class ReplayConsistencyTests(unittest.TestCase):
    def test_replay_weekend_20_game_limit_and_bonus(self):
        from modules.admin_ranking_rebuild import build_replay_plan
        users = [dict(id=uid, rank_points=1000, total_matches=0, wins=0, draws=0, losses=0,
                      goals_for=0, goals_against=0, streak=0, loss_streak=0) for uid in ('a', 'b')]
        matches = [dict(id=f'm{i:02}', player1_id='a', player2_id='b', score1=2, score2=1,
                        status='confirmed', delta1=0, delta2=0, created_at=f'2026-09-20T{(i-1):02}:00:00+07:00')
                   for i in range(1, 22)]
        _, updates = build_replay_plan(
            users=users, matches=matches, overrides={},
            calculate_deltas=lambda *args, **kw: (25, -20),
            get_rank_level=lambda rp: 0,
            apply_host_factor=lambda base, factor: base,
            host_by_match={}, default_points=1000, placement_matches=0,
            host_win_factor=1.0, formula_version='test', formula_summary=lambda: {},
            seed_namespace='test', daily_positive_rp_limit=180,
            repeat_opponent_rules_enabled=False,
        )
        self.assertEqual(updates['m20']['rp_details']['daily_rank_limits']['game_limit']['game_limit'], 20)
        self.assertEqual(updates['m21']['delta1'], 0)
        self.assertEqual(updates['m21']['delta2'], 0)
        self.assertFalse(updates['m21']['rp_details']['daily_rank_limits']['game_limit']['rp_eligible'])
        self.assertEqual(updates['m21']['rp_details']['daily_rank_limits']['counted_user_ids'], [])
        base = sum(updates[f'm{i:02}']['rp_details']['daily_rank_limits']['positive_rp_cap']['player1']['base_applied']
                   for i in range(1, 21))
        self.assertLessEqual(base, 250)
        bonus = sum(updates[f'm{i:02}']['rp_details']['daily_rank_limits']['positive_rp_cap']['player1']['streak_bonus']
                    for i in range(1, 21))
        self.assertGreater(bonus, 0)

    def test_live_11th_game_excluded(self):
        original_enabled, original_games, original_now, original_game_limit = service.daily_rank_limits_enabled, service.ranked_games_today, service._now_vn, service.current_daily_game_limit
        try:
            service.daily_rank_limits_enabled = lambda: True
            service._now_vn = lambda: datetime(2026, 9, 21, tzinfo=VN)
            service.current_daily_game_limit = lambda: 10
            service.ranked_games_today = lambda uid: 10
            self.assertTrue(service.daily_rank_match_rp_status('a', 'b')['rp_eligible'])
            service.ranked_games_today = lambda uid: 11 if uid == 'a' else 10
            self.assertFalse(service.daily_rank_match_rp_status('a', 'b')['rp_eligible'])
        finally:
            service.daily_rank_limits_enabled, service.ranked_games_today, service._now_vn, service.current_daily_game_limit = original_enabled, original_games, original_now, original_game_limit


class WeeklyEligibilityTests(unittest.TestCase):
    def test_weekly_matches_exclude_daily_over_quota(self):
        from modules import weekly_rp_rewards_service as weekly
        class FakeTable:
            def select(self, *args): return self
            def eq(self, *args): return self
            def gte(self, *args): return self
            def lt(self, *args): return self
            def or_(self, *args): return self
        class FakeDB:
            def table(self, name):
                self_name = name
                assert self_name == 'matches'
                return FakeTable()
        records = [
            dict(id='ok',player1_id='me',player2_id='first', rp_details={'daily_rank_limits':{'game_limit':{'rp_eligible':True}}}),
            dict(id='exceeded',player1_id='me',player2_id='second', rp_details={'daily_rank_limits':{'game_limit':{'rp_eligible':False}}}),
            dict(id='legacy',player1_id='me',player2_id='third', rp_details={}),
        ]
        old_db, old_exec = weekly.__dict__.get('db'), weekly.__dict__.get('execute_query')
        try:
            weekly.db = FakeDB()
            weekly.execute_query = lambda *a, **k: SimpleNamespace(data=records)
            start = datetime(2026, 9, 14, tzinfo=VN)
            self.assertEqual(weekly._load_week_activity('me',start,start+timedelta(days=7)), (2, 2))
        finally:
            if old_db is None: weekly.__dict__.pop('db', None)
            else: weekly.db = old_db
            if old_exec is None: weekly.__dict__.pop('execute_query',None)
            else: weekly.execute_query = old_exec
