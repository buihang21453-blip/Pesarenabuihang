from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVITE = (ROOT / 'modules' / 'invite_routes.py').read_text(encoding='utf-8')
ACTIVITY = (ROOT / 'modules' / 'legacy_room_activity_service.py').read_text(encoding='utf-8')


def test_matchmaking_snapshot_loads_room_kind_fields():
    assert 'invite_id,note,match_mode,team_tier,updated_at' in ACTIVITY
    assert '"c1_room_a": c1_room_for(user_a)' in ACTIVITY
    assert '"normal_room_a": normal_room_for(user_a)' in ACTIVITY


def test_manual_rank_invite_blocks_any_active_c1_room():
    assert 'sender_room_is_c1 = bool(state.get("c1_room_a"))' in INVITE
    assert 'receiver_room_is_c1 = bool(state.get("c1_room_b"))' in INVITE
    assert 'Người chơi này đang ở Phòng đấu C1 nên chưa thể nhận lời mời Rank.' in INVITE


def test_accept_rank_invite_rechecks_both_users_and_c1():
    assert 'invite_state = matchmaking_snapshot(user["id"], inviter_id)' in INVITE
    assert 'if invite_state.get("c1_room_a"):' in INVITE
    assert 'if invite_state.get("c1_room_b"):' in INVITE
    assert 'Lời mời Rank không thể chen vào luồng giải đấu.' in INVITE


def test_quick_match_never_targets_c1_room():
    assert 'Bạn đang ở Phòng đấu C1 nên Tìm Nhanh Rank tạm khóa.' in INVITE
    assert 'if _room_is_c1(opponent_room):' in INVITE


def test_rank_popup_is_suppressed_while_user_is_in_c1():
    assert 'user_in_c1 = _room_is_c1(active_room)' in INVITE
    assert 'if user_in_c1 and not is_c1_invite:' in INVITE
