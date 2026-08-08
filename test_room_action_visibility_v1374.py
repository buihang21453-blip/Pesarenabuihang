from pathlib import Path

ROOT = Path(__file__).resolve().parent
CENTER = (ROOT / 'templates/room/_center_stage.html').read_text(encoding='utf-8')
GUEST = (ROOT / 'templates/room/_guest_card.html').read_text(encoding='utf-8')
LIVE = (ROOT / 'templates/_room_live_content.html').read_text(encoding='utf-8')
CSS = (ROOT / 'static/css/room/08-action-layout-guard.css').read_text(encoding='utf-8')


def test_waiting_ready_guest_controls_exist():
    assert 'room_guest_ready' in CENTER
    assert 'Sẵn Sàng' in CENTER
    assert 'room_guest_unready' in CENTER
    assert 'Hủy Sẵn Sàng' in CENTER
    assert 'room_leave' in CENTER


def test_playing_and_post_match_controls_exist():
    assert 'room_guest_forfeit' in CENTER
    assert 'room_submit_result' in CENTER
    assert 'Gửi Kết Quả' in CENTER
    assert 'room_post_result_exit' in CENTER
    assert 'Thoát an toàn' in CENTER
    assert 'room_rematch' in CENTER and 'Đá Tiếp' in CENTER
    assert 'room_rematch_decline' in CENTER and 'Về sảnh' in CENTER


def test_host_kick_exists_before_match_regardless_of_ready_state():
    assert 'room.status == "waiting_ready" and room_room_viewer_is_host' in GUEST
    assert 'room_kick_guest' in GUEST
    assert 'Đưa khỏi phòng' in GUEST


def test_polling_partial_has_same_core_actions():
    for token in (
        'room_guest_ready', 'room_guest_unready', 'room_guest_forfeit',
        'room_submit_result', 'room_post_result_exit', 'room_rematch',
        'room_rematch_decline', 'room_kick_guest'
    ):
        assert token in LIVE


def test_desktop_action_dock_covers_all_action_states():
    for state in ('waiting_ready', 'playing', 'waiting_result_confirm', 'disputed', 'confirmed'):
        assert f'room-state-{state}' in CSS
    assert 'position: absolute !important' in CSS
    assert 'bottom: 10px !important' in CSS
    assert 'padding-bottom: 76px !important' in CSS


def test_score_panel_has_its_own_visible_dock():
    assert ':has(> .room-center-score-panel)' in CSS
    assert 'padding-bottom: 158px !important' in CSS
    assert 'room-state-playing > .room-center-score-panel' in CSS


def test_host_kick_visibility_guard():
    assert '[data-viewer-role="host"] .room-side-card.away .room-guest-card-kick' in CSS
    assert 'visibility: visible' in CSS
