"""Module hóa từ V1.2.9.

Giữ nguyên logic gốc; dependency được truyền từ app.py bằng configure() để tránh import vòng.
"""

_CONTEXT = {}

def configure(context):
    _CONTEXT.clear()
    _CONTEXT.update(context)
    globals().update(context)

EXPORTED_NAMES = ['room_state_expiry_dt', 'room_inactivity_expiry_dt', 'room_expiry_dt', 'close_room_if_host_browser_offline', 'close_room_with_timeout_penalty', 'expire_room_if_needed', 'get_room', 'enrich_room', 'list_rooms']

def room_state_expiry_dt(room):
    """Short state-specific deadline such as ready/result/rematch timeout."""
    explicit = aware_utc(parse_dt(room.get("state_expires_at")))
    if explicit:
        return explicit

    updated = aware_utc(parse_dt(room.get("updated_at"))) or aware_utc(parse_dt(room.get("created_at")))
    if not updated:
        return None

    status = room.get("status")
    note = room.get("note") or ""
    if status == "waiting_ready":
        # Phòng chưa bắt đầu được xử lý bằng bộ đếm không hoạt động 30 phút.
        return None
    if status == "waiting_result_confirm":
        return updated + timedelta(seconds=RESULT_CONFIRM_TIMEOUT_SECONDS)
    if status == "confirmed" and note in {REMATCH_HOST_READY_NOTE, REMATCH_GUEST_READY_NOTE}:
        return updated + timedelta(seconds=REMATCH_TIMEOUT_SECONDS)
    return None


def room_inactivity_expiry_dt(room):
    """Đóng phòng chờ sau 30 phút, phòng đã bắt đầu sau 60 phút không hoạt động."""
    active_statuses = {"waiting_ready", "playing", "friendly_playing", "waiting_result_confirm"}
    status = room.get("status")
    note = room.get("note") or ""
    if status == "confirmed" and note in {REMATCH_HOST_READY_NOTE, REMATCH_GUEST_READY_NOTE}:
        active = True
    else:
        active = status in active_statuses
    if not active:
        return None

    last_activity = aware_utc(parse_dt(room.get("updated_at"))) or aware_utc(parse_dt(room.get("created_at")))
    if not last_activity:
        return None
    timeout_seconds = (
        ROOM_EMPTY_INACTIVITY_TIMEOUT_SECONDS
        if status == "waiting_ready"
        else ROOM_MATCH_INACTIVITY_TIMEOUT_SECONDS
    )
    return last_activity + timedelta(seconds=timeout_seconds)


def room_expiry_dt(room):
    state_expiry = room_state_expiry_dt(room)
    inactivity_expiry = room_inactivity_expiry_dt(room)
    candidates = [dt for dt in (state_expiry, inactivity_expiry) if dt]
    return min(candidates) if candidates else None


def close_room_if_host_browser_offline(room):
    """Đóng phòng khi chủ đã đóng tab/trình duyệt và presence chuyển Offline.

    Chỉ áp dụng sau khi trận đã bắt đầu. Khách không được cộng/trừ RP, không
    thay đổi thắng/hòa/thua hoặc chuỗi. Điều kiện update theo status giúp chống
    xử lý lặp trên nhiều instance Vercel.
    """
    if not room or room.get("status") not in HOST_BROWSER_OFFLINE_ROOM_STATUSES:
        return False

    host_id = room.get("host_user_id")
    guest_id = room.get("guest_user_id")
    if not host_id or not guest_id:
        return False

    try:
        host = get_user(host_id)
    except Exception as exc:
        print(f"Host offline check warning: {exc}")
        return False
    if not host or host.get("is_online") is not False:
        return False

    last_seen = aware_utc(parse_dt(host.get("last_seen_at")))
    if not last_seen:
        return False
    if now_dt() < last_seen + timedelta(seconds=HOST_BROWSER_OFFLINE_GRACE_SECONDS):
        return False

    original_status = room.get("status")
    reason = (
        f"{host.get('display_name') or host.get('username') or 'Chủ phòng'} "
        f"đã đóng trình duyệt khi trận đang diễn ra và bị trừ {ROOM_ABANDON_PENALTY} RP."
    )
    update_data = {
        "status": "cancelled",
        "guest_ready": False,
        "note": reason,
        "state_expires_at": None,
        "updated_at": now_iso(),
    }
    result = execute_query(
        db.table("match_rooms").update(update_data)
        .eq("id", room.get("id"))
        .eq("status", original_status),
        "host_browser_offline_close_room",
    )
    if not (result.data or []):
        return False

    room.update(update_data)
    penalty_delta = apply_room_abandon_penalty(host_id, ROOM_ABANDON_PENALTY)
    record_room_forfeit_match(
        room,
        offender_role="host",
        penalty_delta=penalty_delta if penalty_delta is not None else -ROOM_ABANDON_PENALTY,
        reason=reason,
        event_type="host_browser_offline_forfeit",
    )

    create_user_notification(
        host_id,
        "⚠️ Bạn đã thoát trận",
        f"Phòng đã đóng vì trình duyệt của bạn Offline. Bạn bị trừ {ROOM_ABANDON_PENALTY} RP và mất chuỗi thắng.",
        "/matches",
        "host_browser_offline_penalty",
    )
    create_user_notification(
        guest_id,
        "🚪 Chủ phòng đã Offline",
        "Phòng đã tự đóng. Bạn không bị cộng hoặc trừ RP và có thể tạo phòng mới ngay.",
        "/rooms",
        "host_browser_offline_room_closed",
    )
    cache_delete("_rz_rooms_all")
    ttl_cache_delete("rooms_raw")
    return True


def close_room_with_timeout_penalty(room, offender_role, reason):
    """Đóng phòng và phạt ngẫu nhiên 22–25 RP đúng một lần."""
    room_id = room.get("id")
    original_status = room.get("status")
    offender_id = room.get("host_user_id") if offender_role == "host" else room.get("guest_user_id")
    update_data = {
        "status": "cancelled",
        "note": reason,
        "state_expires_at": None,
        "updated_at": now_iso(),
    }
    result = execute_query(
        db.table("match_rooms").update(update_data).eq("id", room_id).eq("status", original_status),
        "close_room_timeout_penalty",
    )
    # Nếu request khác đã đóng phòng trước, không trừ điểm lần thứ hai.
    if not (result.data or []):
        return False

    room.update(update_data)
    penalty_amount = random.SystemRandom().randint(*ROOM_TIMEOUT_PENALTY_RANGE)
    penalty_delta = apply_room_abandon_penalty(offender_id, penalty_amount)
    record_room_forfeit_match(
        room,
        offender_role=offender_role,
        penalty_delta=penalty_delta if penalty_delta is not None else -penalty_amount,
        reason=reason,
        event_type="timeout_forfeit",
    )

    offender_name = room.get("host_name") if offender_role == "host" else room.get("guest_name")
    other_id = room.get("guest_user_id") if offender_role == "host" else room.get("host_user_id")
    create_user_notification(
        offender_id,
        "⏱️ Trận bị tính là bỏ trận",
        f"Bạn bị trừ {abs(int(penalty_delta or -penalty_amount))} RP vì {reason.lower()}",
        "/matches",
        "room_timeout_penalty",
    )
    create_user_notification(
        other_id,
        "⏱️ Phòng đấu đã tự đóng",
        f"{offender_name or 'Đối thủ'} bị tính là bỏ trận. Bạn không bị cộng hoặc trừ RP.",
        "/matches",
        "room_timeout",
    )
    return True


def expire_room_if_needed(room):
    if not room:
        return room

    expires_at = room_expiry_dt(room)
    room["state_expires_at"] = expires_at.isoformat() if expires_at else None
    room["timeout_seconds"] = max(0, int((expires_at - now_dt()).total_seconds())) if expires_at else 0
    if not expires_at or expires_at > now_dt():
        return room

    status = room.get("status")
    note = room.get("note") or ""
    mode = room.get("match_mode") or MATCH_MODE_RANKED
    state_expiry = room_state_expiry_dt(room)
    inactivity_expiry = room_inactivity_expiry_dt(room)
    inactivity_expired = bool(
        inactivity_expiry
        and inactivity_expiry <= now_dt()
        and (not state_expiry or inactivity_expiry <= state_expiry)
    )

    try:
        # Trận Xếp hạng đã quay đội nhưng chủ không nhập kết quả trong 60 phút.
        if status == "playing" and mode == MATCH_MODE_RANKED and inactivity_expired:
            close_room_with_timeout_penalty(
                room,
                "host",
                "Chủ phòng không nhập kết quả sau 60 phút và bị tính là thoát trận.",
            )
            room["timeout_seconds"] = 0
            return room

        # Đã nhập tỷ số nhưng chưa xác nhận: sau 1 phút tự xác nhận kết quả.
        # Không phạt người quên xác nhận và không phụ thuộc phòng còn hoạt động hay đã hủy.
        if status == "waiting_result_confirm" and mode == MATCH_MODE_RANKED:
            pending_match = get_match(room.get("match_id")) if room.get("match_id") else None
            if pending_match and pending_match.get("status") == "confirmed":
                # Match đã chốt nhưng Room chưa kịp chuyển trạng thái (race/network/DB retry).
                # Tuyệt đối không reset về waiting_ready ở đây: nếu reset, UI mất tỷ số,
                # match_id và bước Đá tiếp trở nên không thể truy cập.
                update_data = {
                    "status": "confirmed",
                    "guest_ready": False,
                    "confirmed_by_id": room.get("guest_user_id") or room.get("host_user_id"),
                    "note": "Kết quả đã được xác nhận. Chọn Đá tiếp hoặc Rời phòng.",
                    "state_expires_at": future_iso(REMATCH_TIMEOUT_SECONDS),
                    "updated_at": now_iso(),
                }
                repair = execute_query(
                    db.table("match_rooms").update(update_data)
                    .eq("id", room.get("id")).in_("status", ["waiting_result_confirm", "confirmed"]),
                    "repair_room_after_confirmed_match_timeout",
                    attempts=2,
                )
                if repair.data or []:
                    room.update(update_data)
            room["timeout_seconds"] = seconds_until(room.get("state_expires_at"))
            return room

        # Giao hữu hoặc phòng chưa bắt đầu: chỉ đóng, không trừ điểm.
        if inactivity_expired or status == "waiting_ready":
            update_data = {
                "status": "cancelled",
                "note": (
                    "Phòng tự đóng sau 30 phút không hoạt động."
                    if status == "waiting_ready"
                    else "Phòng tự đóng sau 60 phút không hoạt động."
                ),
                "state_expires_at": None,
                "updated_at": now_iso(),
            }
            result = execute_query(
                db.table("match_rooms").update(update_data).eq("id", room.get("id")).eq("status", status),
                "expire_room_inactivity",
            )
            if result.data or []:
                room.update(update_data)
                if room.get("match_id"):
                    execute_query(
                        db.table("matches").update({
                            "status": "cancelled",
                            "note": (
                                "Phòng tự đóng sau 30 phút không hoạt động; không áp dụng phạt RP."
                                if status == "waiting_ready"
                                else "Phòng tự đóng sau 60 phút không hoạt động; không áp dụng phạt RP."
                            ),
                            "updated_at": now_iso(),
                        }).eq("id", room.get("match_id")),
                        "cancel_inactive_room_match",
                    )
            room["timeout_seconds"] = 0
            return room

        if status == "confirmed" and note not in {REMATCH_HOST_DECLINED_NOTE, REMATCH_GUEST_DECLINED_NOTE, REMATCH_EXPIRED_NOTE}:
            # Giai đoạn Confirmed có timeout riêng kể từ lúc xác nhận kết quả.
            # Hết hạn chỉ kết thúc quyền Đá tiếp; không reset đội/tỷ số/match_id
            # và tuyệt đối không tự bắt đầu một trận mới.
            update_data = {
                "note": REMATCH_EXPIRED_NOTE,
                "state_expires_at": None,
                "updated_at": now_iso(),
            }
            execute_query(
                db.table("match_rooms").update(update_data).eq("id", room.get("id")).eq("status", "confirmed"),
                "expire_rematch_request",
            )
            room.update(update_data)
            room["timeout_seconds"] = 0
    except Exception as exc:
        print(f"expire_room_if_needed warning: {exc}")

    return room


def get_room(room_id):
    result = execute_query(
        db.table("match_rooms").select("*").eq("id", room_id).limit(1),
        "get_room",
    )
    room = dict(result.data[0]) if result.data else None
    if room:
        expire_room_if_needed(room)
        enrich_room(room)
    return room


def enrich_room(room):
    users = users_map()
    host = users.get(room.get("host_user_id"), {})
    guest = users.get(room.get("guest_user_id"), {})

    raw_room_id = str(room.get("id") or "")
    compact_room_id = "".join(ch for ch in raw_room_id.upper() if ch.isalnum())
    room["room_code"] = (compact_room_id[:6] or "ROOM00")

    room["host_name"] = host.get("display_name", "Unknown")
    room["host_name_style_class"] = str(host.get("name_style_class") or "").strip()
    room["host_profile_badge"] = host.get("profile_badge")
    room["host_avatar_url"] = host.get("avatar_url")
    room["host_avatar_frame"] = host.get("avatar_frame")
    room["host_achievement"] = host.get("featured_achievement")
    room["host_points"] = host.get("rank_points", 0)
    room["host_rank_info"] = get_rank_info(host.get("rank_points", 0))
    room["host_rank"] = get_rank_display(host.get("rank_points", 0))
    room["host_streak"] = int(host.get("streak", 0) or 0)
    room["host_streak_badge"] = get_win_streak_badge(room["host_streak"])
    room["has_guest"] = bool(room.get("guest_user_id"))
    room["guest_name"] = guest.get("display_name", "Đang chờ đối thủ") if room["has_guest"] else "Đang chờ đối thủ"
    room["guest_name_style_class"] = str(guest.get("name_style_class") or "").strip() if room["has_guest"] else ""
    room["guest_profile_badge"] = guest.get("profile_badge") if room["has_guest"] else None
    room["guest_avatar_url"] = guest.get("avatar_url") if room["has_guest"] else None
    room["guest_avatar_frame"] = guest.get("avatar_frame") if room["has_guest"] else None
    room["guest_achievement"] = guest.get("featured_achievement") if room["has_guest"] else None
    room["guest_points"] = guest.get("rank_points", 0) if room["has_guest"] else 0
    room["guest_rank_info"] = get_rank_info(guest.get("rank_points", 0)) if room["has_guest"] else None
    room["guest_rank"] = get_rank_display(guest.get("rank_points", 0)) if room["has_guest"] else "Chưa có người chơi"
    room["guest_streak"] = int(guest.get("streak", 0) or 0) if room["has_guest"] else 0
    room["guest_streak_badge"] = get_win_streak_badge(room["guest_streak"]) if room["has_guest"] else None
    room["streak_event"] = parse_win_streak_room_note(room.get("note"))
    if room.get("host_team"):
        info = get_db_team_info(room.get("host_team")) or {}
        room["host_team_overall"] = room.get("host_team_overall") or info.get("overall") or get_team_overall(room.get("host_team"))
        room["host_team_logo_url"] = room.get("host_team_logo_url") or info.get("logo_url")
        room["host_team_league"] = room.get("host_team_league") or info.get("league") or ""
        room["host_team_league_logo_url"] = get_league_logo_url(room["host_team_league"])
        room["host_team_tier"] = info.get("tier") or get_team_tier(room.get("host_team"))
        room["host_team_total_stats"] = int(info.get("total_stats") or 0)
    else:
        room["host_team_total_stats"] = 0
    if room.get("guest_team"):
        info = get_db_team_info(room.get("guest_team")) or {}
        room["guest_team_overall"] = room.get("guest_team_overall") or info.get("overall") or get_team_overall(room.get("guest_team"))
        room["guest_team_logo_url"] = room.get("guest_team_logo_url") or info.get("logo_url")
        room["guest_team_league"] = room.get("guest_team_league") or info.get("league") or ""
        room["guest_team_league_logo_url"] = get_league_logo_url(room["guest_team_league"])
        room["guest_team_tier"] = info.get("tier") or get_team_tier(room.get("guest_team"))
        room["guest_team_total_stats"] = int(info.get("total_stats") or 0)
    else:
        room["guest_team_total_stats"] = 0
    room["smart_random_rule"] = get_smart_random_rule(host, guest)
    room["rematch_host_ready"] = room.get("note") == REMATCH_HOST_READY_NOTE
    room["rematch_guest_ready"] = room.get("note") == REMATCH_GUEST_READY_NOTE
    room["rematch_host_declined"] = room.get("note") == REMATCH_HOST_DECLINED_NOTE
    room["rematch_guest_declined"] = room.get("note") == REMATCH_GUEST_DECLINED_NOTE
    room["rematch_declined"] = room["rematch_host_declined"] or room["rematch_guest_declined"]
    room["match_mode"] = room.get("match_mode") or MATCH_MODE_RANKED
    if (not system_feature_enabled("rank_standard_enabled") and room.get("status") == "waiting_ready"
            and room.get("match_mode") == MATCH_MODE_RANKED and not decode_friendly_random3_state(room.get("note"))):
        room["team_tier"] = FRIENDLY_RANDOM3_MODE
    room["friendly_tier"] = room.get("friendly_tier") or "A"
    random3_state = decode_friendly_random3_state(room.get("note"))
    room["friendly_random3"] = random3_state
    room["friendly_random3_active"] = bool(random3_state)
    room["friendly_random3_host_chosen"] = bool(random3_state and random3_state.get("host_choice") is not None)
    room["friendly_random3_guest_chosen"] = bool(random3_state and random3_state.get("guest_choice") is not None)
    room["host_team_league"] = room.get("host_team_league") or ""
    room["guest_team_league"] = room.get("guest_team_league") or ""
    room["host_team_league_logo_url"] = room.get("host_team_league_logo_url") or get_league_logo_url(room["host_team_league"])
    room["guest_team_league_logo_url"] = room.get("guest_team_league_logo_url") or get_league_logo_url(room["guest_team_league"])
    room["rematch_expired"] = room.get("note") == REMATCH_EXPIRED_NOTE
    room["dispute"] = None
    if room.get("status") == "disputed" and room.get("match_id"):
        try:
            dispute = get_match_dispute_by_match(room.get("match_id"), DISPUTE_PENDING_STATUSES)
            if dispute:
                room["dispute"] = decorate_match_dispute(dispute)
        except Exception as exc:
            print(f"enrich_room dispute warning: {exc}")
    room["timeout_seconds"] = seconds_until(room.get("state_expires_at"))
    state_expiry = room_state_expiry_dt(room)
    inactivity_expiry = room_inactivity_expiry_dt(room)
    inactivity_is_next = bool(
        inactivity_expiry
        and (not state_expiry or inactivity_expiry <= state_expiry)
    )
    if inactivity_is_next and room.get("timeout_seconds", 0) > 0:
        room["timeout_label"] = "Phòng sẽ tự đóng nếu không có hoạt động trong"
    elif room.get("status") == "waiting_ready" and room.get("guest_user_id") and not room.get("guest_ready"):
        room["timeout_label"] = "Phòng sẽ tự đóng nếu không có hoạt động trong"
    elif room.get("status") == "waiting_result_confirm":
        room["timeout_label"] = "Khách cần xác nhận hoặc tranh chấp trong"
    elif room.get("status") == "confirmed" and (room.get("rematch_host_ready") or room.get("rematch_guest_ready")):
        room["timeout_label"] = "Yêu cầu đá tiếp sẽ hết hạn trong"
    else:
        room["timeout_label"] = ""

    room["match_mode_label"] = ("Random 3 chọn 1" if room.get("team_tier") == FRIENDLY_RANDOM3_MODE else ("Xếp hạng (Rank)" if room.get("match_mode") != MATCH_MODE_FRIENDLY else f"Giao hữu Tier {room.get('friendly_tier') or ''}".strip()))
    room["battle_label"] = "Trận đấu xếp hạng" if room.get("match_mode") != MATCH_MODE_FRIENDLY else "Trận đấu giao hữu"
    room["start_countdown_seconds"] = 0
    room["match_elapsed_seconds"] = 0
    if room.get("guest_user_id"):
        time_source = room.get("updated_at") or room.get("created_at")
        event_dt = parse_dt(time_source) if time_source else None
        if event_dt:
            elapsed = max(0, int((now_dt() - event_dt).total_seconds()))
            if room.get("status") == "waiting_ready":
                room["start_countdown_seconds"] = max(0, 300 - elapsed)
            elif room.get("status") in {"playing", "friendly_playing", "waiting_result_confirm"}:
                room["match_elapsed_seconds"] = elapsed
    room["guest_ready_label"] = "Đã sẵn sàng" if room.get("guest_ready") else "Chưa sẵn sàng"
    return room


def list_rooms(status=None):
    cached = cache_get("_rz_rooms_all")
    if cached is None:
        shared = ttl_cache_get("rooms_raw")
        if shared is None:
            query = db.table("match_rooms").select("*").order("created_at", desc=True)
            result = execute_query(query, "list_rooms")
            shared = result.data or []
            ttl_cache_set("rooms_raw", shared, 3)
        cached = [dict(row) for row in shared]
        cache_set("_rz_rooms_all", cached)

    rooms = []
    for raw in cached:
        room = expire_room_if_needed(dict(raw))
        if status and room.get("status") != status:
            continue
        enrich_room(room)
        rooms.append(room)
    return rooms

