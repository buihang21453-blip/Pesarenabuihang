"""Module hóa từ V1.2.9.

Giữ nguyên logic gốc; dependency được truyền từ app.py bằng configure() để tránh import vòng.
"""

_CONTEXT = {}

def configure(context):
    _CONTEXT.clear()
    _CONTEXT.update(context)
    globals().update(context)

EXPORTED_NAMES = ['auto_confirm_expired_match_if_needed', 'list_matches', 'match_status_label', '_normalize_match_score', '_same_user_id', '_normalize_match_delta', 'decorate_match_for_view', 'build_player_activity_map', 'get_match', 'get_match_dispute', 'get_match_dispute_by_match', 'list_match_disputes', 'dispute_reason_label', 'create_or_update_match_dispute', 'decorate_match_dispute', 'invite_expiry_dt', 'expire_invite_if_needed', 'get_invite', 'list_invites']

def auto_confirm_expired_match_if_needed(match):
    """Tự xác nhận trận chờ quá 1 phút, độc lập với trạng thái phòng.

    Hủy/đóng phòng chỉ giải phóng người chơi. Kết quả đã nhập vẫn tiếp tục
    chờ xác nhận và được tính RP sau thời hạn nếu không có tranh chấp.
    """
    if not match or match.get("status") != "waiting_confirm":
        return match
    submitted_at = aware_utc(parse_dt(match.get("updated_at"))) or aware_utc(parse_dt(match.get("created_at")))
    if not submitted_at or submitted_at + timedelta(seconds=RESULT_CONFIRM_TIMEOUT_SECONDS) > now_dt():
        return match
    try:
        # Lưu trạng thái người chơi/phòng trước khi cộng RP để tạo đúng sự kiện
        # chuỗi thắng hoặc SHUTDOWN cho cả luồng tự xác nhận sau 1 phút.
        users_before_streak_event = users_map()
        room_before_result = None
        try:
            room_before_result_query = execute_query(
                db.table("match_rooms").select("*").eq("match_id", match.get("id")).limit(1),
                "load_room_before_auto_confirm_streak_event",
                attempts=2,
            )
            room_before_result = (room_before_result_query.data or [None])[0]
        except Exception as room_exc:
            print(
                f"load_room_before_auto_confirm_streak_event warning match={match.get('id')}: "
                f"{type(room_exc).__name__}: {room_exc}"
            )

        apply_match_result(dict(match))
        streak_event = build_win_streak_event(
            match, room_before_result, users_before_streak_event
        )
        if streak_event:
            publish_global_streak_event(streak_event)

        fresh_result = execute_query(
            db.table("matches").select("*").eq("id", match.get("id")).limit(1),
            "reload_auto_confirmed_match",
            attempts=2,
        )
        fresh = dict(fresh_result.data[0]) if fresh_result.data else dict(match)

        # Auto-confirm chỉ chốt trận thành confirmed. Không xóa tỷ số/CLB/match_id
        # để hai người còn nhìn thấy kết quả và quyết định Đá tiếp / Rời phòng.
        room_result = execute_query(
            db.table("match_rooms").select("id,status").eq("match_id", match.get("id")).limit(1),
            "load_room_for_auto_confirm",
            attempts=2,
        )
        linked_room = (room_result.data or [None])[0]
        if linked_room and linked_room.get("status") == "waiting_result_confirm":
            finish_result = execute_query(
                db.table("match_rooms").update({
                    "status": "confirmed",
                    "guest_ready": False,
                    "note": "Kết quả đã tự xác nhận sau thời gian chờ. Chọn Đá tiếp hoặc Rời phòng.",
                    "state_expires_at": future_iso(REMATCH_TIMEOUT_SECONDS),
                    "updated_at": now_iso(),
                }).eq("id", linked_room.get("id")).eq("status", "waiting_result_confirm"),
                "finish_room_after_auto_confirm",
                attempts=2,
            )
            if not (finish_result.data or []):
                print(f"auto_confirm room state changed match={match.get('id')} room={linked_room.get('id')}")
        cache_delete("_rz_matches_all", "_rz_rooms_all")
        ttl_cache_delete("matches_raw")
        ttl_cache_delete("rooms_raw")
        return fresh
    except Exception as exc:
        print(f"auto_confirm_expired_match warning match={match.get('id')}: {type(exc).__name__}: {exc}")
        return match


def list_matches(status=None, limit=None, offset=0):
    """Đọc trận đấu có lọc tại Supabase thay vì luôn tải toàn bộ bảng.

    - Không truyền status/limit: giữ hành vi cũ và request-cache toàn bộ.
    - Có status hoặc limit: SELECT đúng tập cần thiết, giảm dữ liệu truyền và CPU Python.
    """
    require_db()

    cache_key = f"_rz_matches_{status or 'all'}_{int(limit) if limit else 'all'}_{int(offset or 0)}"
    cached = cache_get(cache_key)
    if cached is None:
        query = db.table("matches").select("*")
        if status:
            query = query.eq("status", status)
        query = query.order("created_at", desc=True)
        if limit:
            limit = max(1, int(limit))
            offset = max(0, int(offset or 0))
            if offset:
                query = query.range(offset, offset + limit - 1)
            else:
                query = query.limit(limit)
        result = execute_query(query, f"list_matches:{status or 'all'}:{limit or 'all'}:{offset or 0}")
        cached = result.data or []
        cache_set(cache_key, cached)

    processed_matches = [auto_confirm_expired_match_if_needed(dict(m)) for m in cached]
    matches = [m for m in processed_matches if not status or m.get("status") == status]
    users = users_map()

    for match in matches:
        player1 = users.get(match.get("player1_id"), {})
        player2 = users.get(match.get("player2_id"), {})
        match["player1_name"] = player1.get("display_name", "Unknown")
        match["player2_name"] = player2.get("display_name", "Unknown")
        match["player1_avatar_url"] = player1.get("avatar_url")
        match["player2_avatar_url"] = player2.get("avatar_url")
        match["player1_avatar_frame"] = player1.get("avatar_frame")
        match["player2_avatar_frame"] = player2.get("avatar_frame")
        match["player1_achievement"] = player1.get("featured_achievement")
        match["player2_achievement"] = player2.get("featured_achievement")
        match["submitted_by_name"] = users.get(match.get("submitted_by_id"), {}).get("display_name", "")
        match["winner_name"] = users.get(match.get("winner_id"), {}).get("display_name", "")
        match["loser_name"] = users.get(match.get("loser_id"), {}).get("display_name", "")

    return matches

def match_status_label(status):
    return MATCH_STATUS_LABELS.get(status, str(status or "-").replace("_", " ").title())


def _normalize_match_score(value):
    """Return an integer score while preserving a missing score as None."""
    if value is None or value == "":
        return None
    try:
        return int(round(float(value)))
    except (TypeError, ValueError, OverflowError):
        return None


def _same_user_id(left, right):
    """Compare Supabase/user IDs safely even when one side is not a string."""
    if left is None or right is None:
        return False
    return str(left) == str(right)


def _normalize_match_delta(value):
    """Normalize RP deltas returned as int, float or numeric string."""
    try:
        return int(round(float(value or 0)))
    except (TypeError, ValueError, OverflowError):
        return 0


def decorate_match_for_view(match, viewer_id=None):
    """Prepare one match with a single, consistent left/right display order.

    Personal history and Profile always put the viewed player on the left.
    System-wide history keeps the original player1/player2 order. Winner/loser
    display data is derived from the confirmed score, so stale winner_id fields
    cannot make the UI show the wrong side.
    """
    item = dict(match or {})
    item["is_forfeit"] = is_forfeit_match(item)
    item["forfeit_loser_id"] = forfeit_loser_id(item) if item["is_forfeit"] else None
    if item["is_forfeit"]:
        item["note"] = forfeit_display_note(item)
    item["status_label"] = "Bỏ cuộc" if item["is_forfeit"] else match_status_label(item.get("status"))
    item["created_at_display"] = format_vn_datetime(item.get("created_at"))
    item["is_cancelled"] = item.get("status") == "cancelled"
    rp_details = item.get("rp_details") or {}
    repeat_details = rp_details.get("repeat_opponent") if isinstance(rp_details, dict) else {}
    repeat_details = repeat_details if isinstance(repeat_details, dict) else {}
    item["repeat_opponent_details"] = repeat_details
    item["is_no_rp_pair_match"] = repeat_details.get("counted_for_rp") is False
    item["repeat_encounter_number"] = repeat_details.get("encounter_number")

    score1 = _normalize_match_score(item.get("score1"))
    score2 = _normalize_match_score(item.get("score2"))
    item["score1_normalized"] = score1
    item["score2_normalized"] = score2

    player1_id = item.get("player1_id")
    player2_id = item.get("player2_id")
    viewer_is_player1 = _same_user_id(viewer_id, player1_id)
    viewer_is_player2 = _same_user_id(viewer_id, player2_id)
    item["is_mine"] = bool(viewer_is_player1 or viewer_is_player2)

    computed_winner_id = None
    computed_loser_id = None
    is_confirmed_result = (
        item.get("status") == "confirmed"
        and score1 is not None
        and score2 is not None
    )
    if is_confirmed_result:
        if score1 > score2:
            computed_winner_id, computed_loser_id = player1_id, player2_id
        elif score2 > score1:
            computed_winner_id, computed_loser_id = player2_id, player1_id

    # Display-only winner/loser fields use the score as source of truth.
    item["display_winner_id"] = computed_winner_id
    item["display_loser_id"] = computed_loser_id
    if computed_winner_id is not None:
        item["winner_name"] = (
            item.get("player1_name")
            if _same_user_id(computed_winner_id, player1_id)
            else item.get("player2_name")
        )
        item["loser_name"] = (
            item.get("player2_name")
            if _same_user_id(computed_loser_id, player2_id)
            else item.get("player1_name")
        )
    elif is_confirmed_result:
        item["winner_name"] = ""
        item["loser_name"] = ""

    # Personal views always put the relevant player on the left.
    left_is_player1 = not viewer_is_player2
    if left_is_player1:
        left_prefix, right_prefix = "player1", "player2"
        left_score, right_score = score1, score2
        left_delta, right_delta = item.get("delta1"), item.get("delta2")
        left_team, right_team = item.get("team1"), item.get("team2")
    else:
        left_prefix, right_prefix = "player2", "player1"
        left_score, right_score = score2, score1
        left_delta, right_delta = item.get("delta2"), item.get("delta1")
        left_team, right_team = item.get("team2"), item.get("team1")

    def side_value(prefix, suffix):
        return item.get(f"{prefix}_{suffix}")

    item["left_player_id"] = side_value(left_prefix, "id")
    item["left_player_name"] = side_value(left_prefix, "name")
    item["left_avatar_url"] = side_value(left_prefix, "avatar_url")
    item["left_avatar_frame"] = side_value(left_prefix, "avatar_frame")
    item["left_achievement"] = side_value(left_prefix, "achievement")
    item["left_team"] = left_team
    item["left_score"] = left_score
    item["left_delta"] = _normalize_match_delta(left_delta)

    item["right_player_id"] = side_value(right_prefix, "id")
    item["right_player_name"] = side_value(right_prefix, "name")
    item["right_avatar_url"] = side_value(right_prefix, "avatar_url")
    item["right_avatar_frame"] = side_value(right_prefix, "avatar_frame")
    item["right_achievement"] = side_value(right_prefix, "achievement")
    item["right_team"] = right_team
    item["right_score"] = right_score
    item["right_delta"] = _normalize_match_delta(right_delta)

    if item["is_forfeit"]:
        item["score_display"] = "Bỏ cuộc"
    elif item["is_cancelled"]:
        item["score_display"] = "Không tính"
    else:
        left_score_display = left_score if left_score is not None else "-"
        right_score_display = right_score if right_score is not None else "-"
        item["score_display"] = f"{left_score_display} - {right_score_display}"

    item["left_result_code"] = "neutral"
    item["left_result_label"] = item["status_label"]
    item["right_result_code"] = "neutral"
    item["right_result_label"] = item["status_label"]

    if item["is_forfeit"]:
        left_is_loser = _same_user_id(item.get("forfeit_loser_id"), item.get("left_player_id"))
        right_is_loser = _same_user_id(item.get("forfeit_loser_id"), item.get("right_player_id"))
        if left_is_loser:
            item["left_result_code"], item["left_result_label"] = "loss", "THUA BỎ CUỘC"
            item["right_result_code"], item["right_result_label"] = "neutral", "ĐỐI THỦ BỎ CUỘC"
        elif right_is_loser:
            item["left_result_code"], item["left_result_label"] = "neutral", "ĐỐI THỦ BỎ CUỘC"
            item["right_result_code"], item["right_result_label"] = "loss", "THUA BỎ CUỘC"
        else:
            item["left_result_code"] = item["right_result_code"] = "cancelled"
            item["left_result_label"] = item["right_result_label"] = "BỎ CUỘC"
    elif is_confirmed_result:
        if left_score > right_score:
            item["left_result_code"], item["left_result_label"] = "win", "THẮNG"
            item["right_result_code"], item["right_result_label"] = "loss", "THUA"
        elif left_score < right_score:
            item["left_result_code"], item["left_result_label"] = "loss", "THUA"
            item["right_result_code"], item["right_result_label"] = "win", "THẮNG"
        else:
            item["left_result_code"] = item["right_result_code"] = "draw"
            item["left_result_label"] = item["right_result_label"] = "HÒA"
    elif item.get("status") == "cancelled":
        item["left_result_code"] = item["right_result_code"] = "cancelled"
        item["left_result_label"] = item["right_result_label"] = "ĐÃ HỦY"
    elif item.get("status") == "disputed":
        item["left_result_code"] = item["right_result_code"] = "disputed"
        item["left_result_label"] = item["right_result_label"] = "TRANH CHẤP"
    else:
        item["left_result_code"] = item["right_result_code"] = "pending"

    item["result_code"] = "neutral"
    item["result_label"] = item["status_label"]
    item["my_delta"] = None
    item["opponent_id"] = None
    item["opponent_name"] = None
    item["my_avatar_url"] = None
    item["opponent_avatar_url"] = None
    item["my_avatar_frame"] = None
    item["opponent_avatar_frame"] = None
    item["my_achievement"] = None
    item["opponent_achievement"] = None
    item["my_team"] = None
    item["opponent_team"] = None

    if item["is_mine"]:
        # The viewed/current player is always the left side in personal views.
        item["result_code"] = item["left_result_code"]
        item["result_label"] = item["left_result_label"]
        item["my_delta"] = item["left_delta"]
        item["opponent_id"] = item["right_player_id"]
        item["opponent_name"] = item["right_player_name"]
        item["my_avatar_url"] = item["left_avatar_url"]
        item["opponent_avatar_url"] = item["right_avatar_url"]
        item["my_avatar_frame"] = item["left_avatar_frame"]
        item["opponent_avatar_frame"] = item["right_avatar_frame"]
        item["my_achievement"] = item["left_achievement"]
        item["opponent_achievement"] = item["right_achievement"]
        item["my_team"] = item["left_team"]
        item["opponent_team"] = item["right_team"]

    return item


def build_player_activity_map(rooms=None, matches=None):
    rooms = list_rooms() if rooms is None else rooms
    matches = list_matches() if matches is None else matches
    activity = {}

    def set_status(user_id, code, label):
        if not user_id:
            return
        current = activity.get(user_id)
        if not current or ACTIVITY_PRIORITY.get(code, 0) > ACTIVITY_PRIORITY.get(current.get("code"), 0):
            activity[user_id] = {"code": code, "label": label}

    for room in rooms:
        if not room_is_active(room):
            continue
        if room.get("status") == "waiting_ready":
            code, label = "in_room", "Đang trong phòng"
        elif room.get("status") == "waiting_result_confirm":
            code, label = "waiting_confirm", "Chờ xác nhận"
        else:
            code, label = "playing", "Đang thi đấu"
        set_status(room.get("host_user_id"), code, label)
        set_status(room.get("guest_user_id"), code, label)

    for match in matches:
        if match.get("status") == "waiting_confirm":
            code, label = "waiting_confirm", "Chờ xác nhận"
        elif match.get("status") == "playing":
            code, label = "playing", "Đang thi đấu"
        else:
            continue
        set_status(match.get("player1_id"), code, label)
        set_status(match.get("player2_id"), code, label)

    return activity


def get_match(match_id):
    result = execute_query(
        db.table("matches").select("*").eq("id", match_id).limit(1),
        "get_match",
    )
    match = dict(result.data[0]) if result.data else None
    return auto_confirm_expired_match_if_needed(match) if match else None


def get_match_dispute(dispute_id):
    result = execute_query(
        db.table("match_disputes").select("*").eq("id", dispute_id).limit(1),
        "get_match_dispute",
    )
    return dict(result.data[0]) if result.data else None


def get_match_dispute_by_match(match_id, statuses=None):
    query = db.table("match_disputes").select("*").eq("match_id", match_id).order("created_at", desc=True).limit(1)
    if statuses:
        status_list = list(statuses) if not isinstance(statuses, str) else [statuses]
        query = query.in_("status", status_list)
    result = execute_query(query, "get_match_dispute_by_match")
    return dict(result.data[0]) if result.data else None


def list_match_disputes(status=None):
    query = db.table("match_disputes").select("*").order("created_at", desc=True)
    if status:
        query = query.eq("status", status)
    result = execute_query(query, "list_match_disputes")
    return [dict(item) for item in (result.data or [])]


def dispute_reason_label(reason_code):
    return DISPUTE_REASON_OPTIONS.get(reason_code, DISPUTE_REASON_OPTIONS["other"])


def create_or_update_match_dispute(
    room,
    raised_by_id,
    reason_code,
    details="",
    source="player",
    evidence_path=None,
):
    if not room or not room.get("match_id"):
        return None

    reason_code = reason_code if reason_code in DISPUTE_REASON_OPTIONS else "other"
    details = (details or "").strip()[:500]
    existing = get_match_dispute_by_match(room.get("match_id"), DISPUTE_PENDING_STATUSES)
    payload = {
        "room_id": room.get("id"),
        "raised_by_id": raised_by_id,
        "reason_code": reason_code,
        "reason_label": dispute_reason_label(reason_code),
        "details": details or None,
        "source": source,
        "submitted_score1": room.get("host_score"),
        "submitted_score2": room.get("guest_score"),
        "status": "pending",
        "updated_at": now_iso(),
    }
    if evidence_path:
        payload.update({
            "evidence_path": evidence_path,
            "evidence_uploaded_at": now_iso(),
        })

    if existing:
        result = execute_query(
            db.table("match_disputes").update(payload).eq("id", existing.get("id")),
            "update_match_dispute",
        )
    else:
        payload["match_id"] = room.get("match_id")
        result = execute_query(
            db.table("match_disputes").insert(payload),
            "create_match_dispute",
        )
    return dict(result.data[0]) if result.data else existing


def decorate_match_dispute(dispute, all_matches=None):
    item = dict(dispute or {})
    match = None
    if item.get("match_id") and all_matches is not None:
        match = next((m for m in all_matches if str(m.get("id")) == str(item.get("match_id"))), None)
    if item.get("match_id") and match is None:
        match = get_match(item.get("match_id"))
    users = users_map()
    player1 = users.get((match or {}).get("player1_id"), {})
    player2 = users.get((match or {}).get("player2_id"), {})
    raised_by = users.get(item.get("raised_by_id"), {})
    resolved_by = users.get(item.get("resolved_by_id"), {})

    item["match"] = match or {}
    item["player1_name"] = player1.get("display_name", "Unknown")
    item["player2_name"] = player2.get("display_name", "Unknown")
    item["player1_username"] = player1.get("username", "-")
    item["player2_username"] = player2.get("username", "-")
    item["player1_points"] = int(player1.get("rank_points", 0) or 0)
    item["player2_points"] = int(player2.get("rank_points", 0) or 0)
    item["raised_by_name"] = raised_by.get("display_name") or ("Hệ thống" if item.get("source") == "timeout" else "Không xác định")
    item["resolved_by_name"] = resolved_by.get("display_name", "")
    item["reason_label"] = item.get("reason_label") or dispute_reason_label(item.get("reason_code"))
    item["evidence_url"] = get_dispute_evidence_signed_url(item.get("evidence_path"))
    if item.get("submitted_score1") is None:
        item["submitted_score1"] = (match or {}).get("score1")
    if item.get("submitted_score2") is None:
        item["submitted_score2"] = (match or {}).get("score2")

    candidates = all_matches if all_matches is not None else list_matches()
    pair = {(match or {}).get("player1_id"), (match or {}).get("player2_id")}
    item["head_to_head"] = [
        other for other in candidates
        if other.get("status") == "confirmed"
        and str(other.get("id")) != str(item.get("match_id"))
        and {other.get("player1_id"), other.get("player2_id")} == pair
    ][:5]
    return item


def invite_expiry_dt(invite):
    explicit = aware_utc(parse_dt(invite.get("expires_at")))
    if explicit:
        return explicit
    created = aware_utc(parse_dt(invite.get("created_at")))
    return created + timedelta(seconds=INVITE_TIMEOUT_SECONDS) if created else None


def expire_invite_if_needed(invite):
    if not invite or invite.get("status") != "pending":
        return invite

    expires_at = invite_expiry_dt(invite)
    invite["expires_at"] = expires_at.isoformat() if expires_at else None
    invite["expires_in_seconds"] = max(0, int((expires_at - now_dt()).total_seconds())) if expires_at else 0

    if expires_at and expires_at <= now_dt():
        try:
            execute_query(
                db.table("match_invites").update({
                    "status": "expired",
                    "updated_at": now_iso(),
                }).eq("id", invite.get("id")).eq("status", "pending"),
                "expire_match_invite",
            )
            invite["status"] = "expired"
            invite["expires_in_seconds"] = 0
        except Exception as exc:
            print(f"expire_invite_if_needed warning: {exc}")
    return invite


def get_invite(invite_id):
    result = execute_query(
        db.table("match_invites").select("*").eq("id", invite_id).limit(1),
        "get_invite",
    )
    invite = dict(result.data[0]) if result.data else None
    return expire_invite_if_needed(invite) if invite else None


def list_invites(status=None, limit=None, enrich=True):
    cache_key = f"_rz_invites_{status or 'all'}_{int(limit) if limit else 'all'}"
    cached = cache_get(cache_key)
    if cached is None:
        query = db.table("match_invites").select("*")
        if status:
            query = query.eq("status", status)
        query = query.order("created_at", desc=True)
        if limit:
            query = query.limit(max(1, int(limit)))
        result = execute_query(query, f"list_invites:{status or 'all'}:{limit or 'all'}")
        cached = [dict(row) for row in (result.data or [])]
        cache_set(cache_key, cached)

    processed = []
    for raw in cached:
        invite = expire_invite_if_needed(dict(raw))
        if status and invite.get("status") != status:
            continue
        processed.append(invite)

    if enrich:
        users = users_map()
        for invite in processed:
            from_user = users.get(invite.get("from_user_id"), {})
            to_user = users.get(invite.get("to_user_id"), {})
            invite["from_name"] = from_user.get("display_name", "Unknown")
            invite["from_avatar_url"] = from_user.get("avatar_url")
            invite["from_avatar_frame"] = from_user.get("avatar_frame")
            invite["from_achievement"] = from_user.get("featured_achievement")
            invite["from_points"] = from_user.get("rank_points", 0)
            invite["from_rank"] = get_rank_display(from_user.get("rank_points", 0))
            invite["to_name"] = to_user.get("display_name", "Unknown")
            invite["to_avatar_url"] = to_user.get("avatar_url")
            invite["to_avatar_frame"] = to_user.get("avatar_frame")
            invite["to_achievement"] = to_user.get("featured_achievement")
            invite["to_points"] = to_user.get("rank_points", 0)
            invite["to_rank"] = get_rank_display(to_user.get("rank_points", 0))

    return processed

