from datetime import datetime, timedelta, timezone
from pathlib import Path

APP = Path('app.py').read_text(encoding='utf-8')
DAILY = Path('modules/daily_rank_limit_service.py').read_text(encoding='utf-8')
ADMIN = Path('modules/admin_dashboard_routes.py').read_text(encoding='utf-8')


def test_version_67():
    assert 'APP_VERSION = "V1.4.11"' in APP


def test_active_room_reads_match_rooms_and_waiting_ready():
    assert 'db.table("match_rooms")' in APP
    assert '"waiting_ready"' in APP
    assert 'ACTIVE_ROOM_STATUSES' in APP


def test_duplicate_waiting_room_cleanup_is_safe():
    assert 'def cleanup_duplicate_waiting_rooms' in APP
    assert '.eq("status", "waiting_ready")' in APP
    assert '.is_("match_id", "null")' in APP
    assert 'cleanup_duplicate_waiting_rooms' in ADMIN


def test_weekend_limit_is_15_vietnam_time():
    namespace = {}
    exec(compile(DAILY, 'daily_rank_limit_service.py', 'exec'), namespace)
    vn = timezone(timedelta(hours=7))
    saturday = datetime(2026, 8, 1, 12, 0, tzinfo=vn)
    sunday = datetime(2026, 8, 2, 23, 59, tzinfo=vn)
    monday = datetime(2026, 8, 3, 0, 0, tzinfo=vn)
    assert namespace['current_daily_game_limit'](saturday) == 15
    assert namespace['current_daily_game_limit'](sunday) == 15
    assert namespace['current_daily_game_limit'](monday) == 10
