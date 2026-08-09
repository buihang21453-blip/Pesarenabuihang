from pathlib import Path

ROOT = Path(__file__).resolve().parent

def text(path):
    return (ROOT / path).read_text(encoding='utf-8')


def test_v143_version():
    assert 'APP_VERSION = "1.4.3"' in text('app.py')


def test_invite_accept_claims_invite_before_deleting_receiver_room():
    src = text('app.py')
    claim = src.index('"accept_match_invite"')
    close = src.index('"close_receiver_solo_room_on_accept"')
    assert claim < close
    assert 'rollback_accepted_invite_after_join_error' in src
    assert 'Secondary invite cleanup must never undo a successfully joined room' in src


def test_ready_routes_verify_database_write():
    src = text('modules/room_team_routes.py')
    assert 'Sẵn sàng chưa được ghi nhận' in src
    assert 'chưa thể hủy Sẵn sàng' in src
    assert 'if not (ready_result.data or [])' in src


def test_standard_random_rolls_back_orphan_match():
    src = text('modules/room_team_routes.py')
    assert 'rollback_room_random_orphan_match' in src
    assert 'db.table("matches").delete().eq("id", match["id"]).eq("status", "playing")' in src


def test_submit_result_connects_match_and_room_states():
    src = text('modules/room_result_routes.py')
    assert '"status": "waiting_confirm"' in src
    assert '"status": "waiting_result_confirm"' in src
    assert 'rollback_submit_room_match_result' in src


def test_manual_confirm_stops_at_confirmed_for_post_match_choice():
    src = text('modules/room_result_routes.py')
    assert '"confirm_result_finish_room"' in src
    block = src[src.index('# V1.4.3: confirmation must finish'):src.index('room_update_result = execute_query')]
    assert '"status": "confirmed"' in block
    assert '"state_expires_at": future_iso(REMATCH_TIMEOUT_SECONDS)' in block
    assert '"match_id": None' not in block
    assert '"host_score": None' not in block
    assert '"guest_score": None' not in block


def test_auto_confirm_uses_same_confirmed_state():
    src = text('modules/core/match_repository.py')
    assert '"finish_room_after_auto_confirm"' in src
    pos = src.index('"finish_room_after_auto_confirm"')
    block = src[max(0, pos-900):pos+200]
    assert '"status": "confirmed"' in block
    assert 'future_iso(REMATCH_TIMEOUT_SECONDS)' in block


def test_rematch_requires_two_players_regardless_of_click_order():
    src = text('modules/room_rematch_routes.py')
    assert 'if current_note != opponent_ready_note:' in src
    assert 'room_rematch_first_ready' in src
    assert 'room_rematch_reset_same_room' in src
    assert 'Khách bấm Đá tiếp: khách được tính là sẵn sàng ngay' not in src
    first = src.index('room_rematch_first_ready')
    reset = src.index('room_rematch_reset_same_room')
    assert first < reset


def test_completed_series_reaches_post_match_choice_but_intermediate_game_continues():
    src = text('modules/rank_series/service.py')
    fn = src[src.index('def _reset_room_after_series_confirm'):src.index('def confirm_series_child_match')]
    assert 'if completed:' in fn
    assert '"status": "confirmed"' in fn
    assert '"status": "waiting_ready"' in fn
    assert 'series_finish_room' in fn


def test_confirmed_room_remains_busy_until_exit_or_timeout():
    app = text('app.py')
    runtime = text('modules/core/matchmaking_runtime.py')
    assert '"confirmed",' in app[app.index('ACTIVE_ROOM_STATUSES'):app.index('ACTIVE_ROOM_STATUSES')+300]
    assert 'REMATCH_HOST_DECLINED_NOTE' in runtime
    assert 'REMATCH_GUEST_DECLINED_NOTE' in runtime
    assert 'REMATCH_EXPIRED_NOTE' in runtime


def test_ui_has_every_primary_match_flow_endpoint():
    ui = '\n'.join([
        text('templates/base.html'),
        text('templates/invites.html'),
        text('templates/_room_live_content.html'),
        text('templates/room/_center_stage.html'),
        text('templates/partials/room_confirmed_actions.html'),
        text('templates/room/_extra_controls.html'),
    ])
    for endpoint in (
        'respond_invite', 'room_guest_ready', 'room_random_teams',
        'room_submit_result', 'room_confirm_result', 'room_rematch',
        'room_rematch_decline', 'room_leave', 'room_guest_forfeit', 'room_host_forfeit',
    ):
        assert endpoint in ui, endpoint
