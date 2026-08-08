from pathlib import Path

ROOT=Path(__file__).resolve().parent

def test_version():
    assert 'APP_VERSION = "1.3.72"' in (ROOT/'app.py').read_text()

def test_guest_actions_exist_in_waiting_and_playing():
    s=(ROOT/'templates/room/_center_stage.html').read_text()
    assert "room_viewer_is_guest" in s
    assert "room_guest_ready" in s
    assert "room_guest_unready" in s
    assert "room_guest_forfeit" in s
    assert "room_leave" in s

def test_host_and_guest_result_actions_exist():
    s=(ROOT/'templates/room/_center_stage.html').read_text()
    assert "room_confirm_result" in s
    assert "room_dispute_result" in s
    assert "room_submit_result" in s
    assert "room_rematch" in s

def test_layout_guard_reserves_action_lane():
    s=(ROOT/'static/css/room/08-action-layout-guard.css').read_text()
    for state in ['room-state-playing','room-state-waiting_result_confirm','room-state-disputed','room-state-confirmed']:
        assert state in s
    assert 'visibility: visible' in s
    assert '.room-guest-card-kick' in s

def test_viewer_role_debug_marker():
    s=(ROOT/'templates/room_detail.html').read_text()
    assert 'data-viewer-role=' in s
