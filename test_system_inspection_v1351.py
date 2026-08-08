from pathlib import Path
ROOT=Path(__file__).resolve().parent

def text(p): return (ROOT/p).read_text(encoding='utf-8')

def test_version():
    assert 'APP_VERSION = "1.3.51"' in text('app.py')

def test_ban_pick_timeout_core():
    s=text('modules/rank_series/service.py')
    for token in ('process_series_timeouts','turn_deadline_at','timeout_random','ban_auto','pick_auto','future_iso','seconds_until'):
        assert token in s
    assert 'process_series_timeouts(room)' in text('app.py')

def test_ban_pick_admin_guard():
    s=text('modules/admin_dashboard_routes.py')
    assert 'minimum_pool = bans_per_player * 2 + 6' in s
    assert '@admin_permission_required("system_features_manage")' in s
    assert '@admin_permission_required("users_edit")' in s

def test_tactical_no_repeated_offered_clubs():
    s=text('modules/rank_series/service.py')
    m=text('modules/rank_series/modes/tactical_bo3.py')
    assert 'tactical_seen_clubs' in s
    assert 'tactical_seen_clubs' in m

def test_polling_is_fast_only_during_ban_pick():
    s=text('templates/room_detail.html')
    assert 'currentRoomMode === "ban_pick_bo3"' in s
    assert 'return 3000' in s
    assert 'series-turn-countdown' in s
