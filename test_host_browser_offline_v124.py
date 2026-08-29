from pathlib import Path

APP = Path('app.py').read_text(encoding='utf-8')
ACCESS = Path('modules/room_access_routes.py').read_text(encoding='utf-8')


def test_version_and_constants():
    assert 'APP_VERSION = "V1.4.18"' in APP
    assert 'HOST_BROWSER_OFFLINE_GRACE_SECONDS = 20' in APP
    assert 'HOST_BROWSER_OFFLINE_ROOM_STATUSES = {"playing", "friendly_playing"}' in APP


def test_host_offline_flow_is_idempotent_and_guest_safe():
    assert 'def close_room_if_host_browser_offline(room):' in APP
    assert '.eq("status", original_status)' in APP
    assert 'apply_room_abandon_penalty(host_id, ROOM_ABANDON_PENALTY)' in APP
    assert '_award_forfeit_win' not in APP[APP.index('def close_room_if_host_browser_offline'):APP.index('def close_room_with_timeout_penalty')]
    assert 'Bạn không bị cộng hoặc trừ RP' in APP


def test_polling_and_room_views_trigger_cleanup():
    assert 'if close_room_if_host_browser_offline(room):' in APP
    assert ACCESS.count('close_room_if_host_browser_offline(room)') >= 2
