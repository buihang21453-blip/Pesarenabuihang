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
    if not stage or stage.get("status") != "open":
        return False, "Giai đoạn C1 chưa mở.", ()
    if str(match.get("stage_code") or "") == "knockout":
        access_result = execute_query(
            db.table("tournament_settings").select("setting_value").eq("tournament_id", tid)
            .eq("setting_key", "knockout_match_unlocks_v1").limit(1),
            "c1_fixed_start_ko_unlock", attempts=2,
        )
        access_row = (getattr(access_result, "data", None) or [None])[0]
        access_state = (access_row or {}).get("setting_value") or {}
        entries = access_state.get("entries") or {} if isinstance(access_state, dict) else {}
        pair_key = str(match.get("aggregate_group") or match.get("id") or "")
        if not bool((entries.get(pair_key) or {}).get("unlocked")):
            return False, "BTC chưa mở cặp Knockout này.", ()
    match_status = str(match.get("status") or "").lower()
    if match_status not in {"pending", "scheduled", "playing"}:
        return False, "Trận C1 không còn ở trạng thái có thể bắt đầu.", ()
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
        # Có request khác vừa đổi room. Nếu room đã playing thì coi là idempotent,
        # tránh đẩy Host về màn chờ và làm mất form nhập tỷ số.
        fresh_room_result = execute_query(
            db.table("match_rooms").select("*").eq("id", rid).limit(1),
            "c1_fixed_start_recheck_room", attempts=2,
        )
        fresh_room = (getattr(fresh_room_result, "data", None) or [None])[0]
        if fresh_room and str(fresh_room.get("status") or "").lower() == "playing":
            return True, "Trận C1 đã bắt đầu.", (fresh_room.get("host_team"), fresh_room.get("guest_team"))
        return False, "Trạng thái phòng vừa thay đổi. Hãy làm mới phòng.", ()

    # Trường hợp lỗi lệch trạng thái từng gặp: tournament_match đã là `playing`
    # nhưng match_rooms vẫn `waiting_ready`. Khi đó chỉ cần phục hồi room; tuyệt
    # đối không rollback về waiting_ready và không bắt người chơi quay/bắt đầu lại.
    if match_status == "playing":
        return True, "Đã khôi phục Phòng C1 đang thi đấu. Chủ phòng có thể nhập tỷ số.", (host_club, guest_club)

    try:
        changed = execute_query(
            db.table("tournament_matches").update({"status": "playing", "updated_at": started_at})
            .eq("id", mid).eq("tournament_id", tid).eq("status", match["status"]),
            "c1_fixed_start_scheduled_match", attempts=2,
        )
        if not (getattr(changed, "data", None) or []):
            # Có thể request song song đã chuyển fixture sang playing. Đọc lại trước
            # khi rollback, vì rollback trong tình huống này chính là nguyên nhân tạo
            # trạng thái: fixture=playing nhưng room=waiting_ready.
            fresh_match_result = execute_query(
                db.table("tournament_matches").select("*").eq("id", mid).eq("tournament_id", tid).limit(1),
                "c1_fixed_start_recheck_match", attempts=2,
            )
            fresh_match = (getattr(fresh_match_result, "data", None) or [None])[0]
            if fresh_match and str(fresh_match.get("status") or "").lower() == "playing":
                return True, "Đã bắt đầu trận C1 với CLB được gán sẵn.", (host_club, guest_club)
            raise RuntimeError("Scheduled C1 match transition updated no rows")
    except Exception:
        # Room/match are separate updates: restore only when fixture thật sự chưa
        # chuyển sang playing. Không tạo lại state lệch giữa hai bảng.
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
