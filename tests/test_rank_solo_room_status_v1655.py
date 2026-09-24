from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACTIVITY = (ROOT / "modules" / "legacy_room_activity_service.py").read_text(encoding="utf-8")
MATCH = (ROOT / "modules" / "legacy_match_service.py").read_text(encoding="utf-8")
INVITE = (ROOT / "modules" / "invite_routes.py").read_text(encoding="utf-8")


def test_solo_room_does_not_require_waiting_ready_only():
    assert 'and not room.get("guest_user_id")' in ACTIVITY
    assert 'and not room.get("match_id")' in ACTIVITY
    assert '"playing", "friendly_playing"' in ACTIVITY


def test_snapshot_repairs_stale_solo_rank_room():
    assert 'repair_stale_solo_rank_room_status' in ACTIVITY
    assert 'room["status"] = "waiting_ready"' in ACTIVITY
    assert 'not _is_c1_room(room)' in ACTIVITY


def test_activity_label_treats_solo_without_match_as_in_room():
    assert 'is_solo_without_match' in MATCH
    assert 'code, label = "in_room", "Đang trong phòng"' in MATCH


def test_invite_still_uses_solo_room_helper():
    assert 'not is_solo_waiting_room(receiver_room, user["id"])' in INVITE
    assert 'not is_solo_waiting_room(inviter_room, inviter_id)' in INVITE
