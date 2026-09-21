"""Start a scheduled C1 GĐ2/KO match with the players' assigned clubs.

Shared by guest-ready automatic start and the host's legacy/retry endpoint.
No draw, ticket usage, ranking writes or random team selection happens here.
"""


def start_assigned_club_match(db, execute_query, tournament_id, room_id, now_iso):
    """Return (started, message, clubs); status writes are checked and rolled back.

    A guest must have confirmed readiness. Reads are fresh, not the cached UI
    room, so the fixed teams are captured at the moment the game begins.
    """
    tid = str(tournament_id or "")
    rid = str(room_id or "")
    rows = execute_query(
        db.table("match_rooms").select("*").eq("id", rid).limit(1),
        "c1_fixed_start_fresh_room", attempts=2,
    )
    room = (getattr(rows, "data", None) or [None])[0]
    if not room:
        return False, "Không tìm thấy phòng C1.", ()
    if room.get("status") == "playing":
        return True, "Trận đã bắt đầu.", (room.get("host_team"), room.get("guest_team"))
    if room.get("status") != "waiting_ready" or not room.get("guest_user_id") or not room.get("guest_ready"):
        return False, "Cần đủ hai HLV và đội khách bấm Sẵn sàng trước khi bắt đầu.", ()

    import json
    note = str(room.get("note") or "")
    if not note.startswith("TOURNAMENT_ROOM|"):
        return False, "Phòng không có thông tin trận C1.", ()
    try:
        meta = json.loads(note[len("TOURNAMENT_ROOM|"):])
    except (ValueError, TypeError):
        return False, "Thông tin trận C1 không hợp lệ.", ()
    if str(meta.get("tournament_id") or "") != tid or meta.get("test_sandbox_room"):
        return False, "Không đúng giải đấu hoặc đây là phòng kiểm thử.", ()
    mid = str(meta.get("tournament_match_id") or "")
    if not mid:
        return False, "Phòng chưa liên kết với trận C1.", ()
    mr = execute_query(
        db.table("tournament_matches").select("*").eq("id", mid).eq("tournament_id", tid).limit(1),
        "c1_fixed_start_match", attempts=2,
    )
    match = (getattr(mr, "data", None) or [None])[0]
    if not match or match.get("stage_code") not in {"league", "knockout"}:
        return False, "Phòng chưa gắn với trận GĐ2/Knockout hợp lệ.", ()
    stage_result = execute_query(
        db.table("tournament_stages").select("status").eq("tournament_id", tid)
        .eq("stage_code", match["stage_code"]).limit(1),
        "c1_fixed_start_stage", attempts=2,
    )
    stage = (getattr(stage_result, "data", None) or [None])[0]
    if not stage or stage.get("status") != "open" or match.get("status") not in {"pending", "scheduled"}:
        return False, "Giai đoạn chưa mở hoặc trận không còn ở trạng thái chờ.", ()
    host_id, guest_id = str(room.get("host_user_id") or ""), str(room.get("guest_user_id") or "")
    expected = {str(match.get("home_user_id") or ""), str(match.get("away_user_id") or "")}
    if not host_id or not guest_id or host_id == guest_id or {host_id, guest_id} != expected:
        return False, "Hai HLV trong phòng không khớp lịch GĐ2.", ()
    members_result = execute_query(
        db.table("tournament_members").select("user_id,fixed_club_name,status")
        .eq("tournament_id", tid).in_("user_id", [host_id, guest_id]),
        "c1_fixed_start_members", attempts=2,
    )
    clubs = {
        str(m.get("user_id") or ""): str(m.get("fixed_club_name") or "").strip()
        for m in (getattr(members_result, "data", None) or []) if m.get("status") == "active"
    }
    host_club, guest_club = clubs.get(host_id), clubs.get(guest_id)
    if not host_club or not guest_club or host_club == guest_club:
        return False, "Hai HLV chưa có hai CLB hợp lệ khác nhau.", ()

    started_at = now_iso()
    patch = {
        "host_team": host_club, "guest_team": guest_club,
        "host_team_overall": None, "guest_team_overall": None,
        "host_team_logo_url": None, "guest_team_logo_url": None,
        "host_team_league": None, "guest_team_league": None,
        "team_tier": "TOURNAMENT", "match_mode": "tournament",
        "status": "playing", "guest_ready": True, "updated_at": started_at,
    }
    updated = execute_query(
        db.table("match_rooms").update(patch).eq("id", rid)
        .eq("status", "waiting_ready").eq("guest_ready", True)
        .eq("host_user_id", host_id).eq("guest_user_id", guest_id),
        "c1_fixed_start_room", attempts=2,
    )
    if not (getattr(updated, "data", None) or []):
        return False, "Trạng thái phòng vừa thay đổi. Hãy làm mới phòng.", ()
    try:
        changed = execute_query(
            db.table("tournament_matches").update({"status": "playing", "updated_at": started_at})
            .eq("id", mid).eq("tournament_id", tid).eq("status", match["status"]),
            "c1_fixed_start_scheduled_match", attempts=2,
        )
        if not (getattr(changed, "data", None) or []):
            raise RuntimeError("Scheduled C1 match transition updated no rows")
    except Exception:
        # Room/match are separate updates: restore only if this room is still playing.
        execute_query(
            db.table("match_rooms").update({
                "status": "waiting_ready", "guest_ready": True,
                "host_team": room.get("host_team"), "guest_team": room.get("guest_team"),
                "updated_at": now_iso(),
            }).eq("id", rid).eq("status", "playing"),
            "c1_fixed_start_rollback", attempts=2,
        )
        raise
    return True, "Đã bắt đầu trận C1 với CLB được gán sẵn.", (host_club, guest_club)
