from modules.rank_modes import service as svc


def setup_status(remaining_by_user, enabled=True):
    def rank_daily_status(user_id):
        remaining = remaining_by_user[str(user_id)]
        return {"enabled": enabled, "games_remaining": remaining, "games": 10-remaining, "game_limit": 10}
    svc.configure({"rank_daily_status": rank_daily_status})


def test_required_slots_by_mode():
    assert svc.required_daily_games_for_mode("rank_random") == 1
    assert svc.required_daily_games_for_mode("random3_pick1") == 1
    assert svc.required_daily_games_for_mode("home_away") == 2
    assert svc.required_daily_games_for_mode("bo3") == 3
    assert svc.required_daily_games_for_mode("tactical_bo3") == 3
    assert svc.required_daily_games_for_mode("ban_pick_bo3") == 3


def test_nine_played_only_single_allowed():
    setup_status({"a":1,"b":1})
    assert svc.rank_mode_daily_quota_status("rank_random","a","b")["eligible"]
    assert not svc.rank_mode_daily_quota_status("home_away","a","b")["eligible"]
    assert not svc.rank_mode_daily_quota_status("bo3","a","b")["eligible"]


def test_eight_played_home_away_yes_bo3_no():
    setup_status({"a":2,"b":2})
    assert svc.rank_mode_daily_quota_status("home_away","a","b")["eligible"]
    assert not svc.rank_mode_daily_quota_status("bo3","a","b")["eligible"]


def test_seven_played_all_series_allowed():
    setup_status({"a":3,"b":3})
    for code in ("home_away","bo3","tactical_bo3","ban_pick_bo3"):
        assert svc.rank_mode_daily_quota_status(code,"a","b")["eligible"]


def test_series_continuation_requires_only_one_real_slot():
    setup_status({"a":1,"b":1})
    assert svc.rank_mode_daily_quota_status("bo3","a","b",continuation=True)["eligible"]
    setup_status({"a":0,"b":1})
    assert not svc.rank_mode_daily_quota_status("bo3","a","b",continuation=True)["eligible"]
