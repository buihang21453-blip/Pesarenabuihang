from pathlib import Path

ROOT = Path(__file__).resolve().parent
cleanup = (ROOT / 'modules/data_cleanup_service.py').read_text(encoding='utf-8')
kick = (ROOT / 'modules/room_access_routes.py').read_text(encoding='utf-8')
admin = (ROOT / 'templates/admin.html').read_text(encoding='utf-8')


def test_hard_delete_keeps_matches_and_removes_user_via_rpc():
    body = cleanup.split('def delete_player_safe', 1)[1]
    assert 'db.table("matches").delete()' not in body
    assert 'reverse_confirmed_match_result' not in body
    assert 'hard_delete_player_keep_match_history' in body
    assert 'account_status": "deleted"' not in body


def test_kick_is_pre_match_only_and_cancels_invite():
    body = kick.split('def room_kick_guest', 1)[1].split('@app.route("/room/<room_id>/leave"', 1)[0]
    assert 'room.get("status") != "waiting_ready"' in body
    assert 'if room.get("match_id")' in body
    assert 'cancel_invite_after_host_kick' in body
    assert 'reverse_confirmed_match_result' not in body


def test_admin_copy_explains_history_preserving_delete():
    assert 'Xóa tài khoản' in admin
    assert 'Lịch sử trận và BXH các mùa cũ' in admin
