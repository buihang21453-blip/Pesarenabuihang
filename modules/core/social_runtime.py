"""Module hóa từ V1.2.9.

Giữ nguyên logic gốc; dependency được truyền từ app.py bằng configure() để tránh import vòng.
"""

_CONTEXT = {}

def configure(context):
    _CONTEXT.clear()
    _CONTEXT.update(context)
    globals().update(context)

EXPORTED_NAMES = ['_normalize_global_streak_events', 'publish_global_streak_event', 'get_active_global_streak_events', 'get_active_global_streak_event', 'get_active_announcement', 'enrich_chat_message', 'list_chat_messages', 'user_can_chat', 'touch_room_activity', 'create_chat_message']

def _normalize_global_streak_events(raw):
    """Chuẩn hóa dữ liệu cũ (1 dict) và dữ liệu mới (danh sách sự kiện)."""
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except Exception:
            return []
    if isinstance(raw, dict):
        raw = [raw]
    if not isinstance(raw, list):
        return []

    now = now_dt()
    active = []
    seen = set()
    for item in raw:
        if not isinstance(item, dict):
            continue
        event_id = str(item.get("id") or "").strip()
        if not event_id or event_id in seen:
            continue
        expires_at = aware_utc(parse_dt(item.get("expires_at")))
        if not expires_at or expires_at <= now:
            continue
        seen.add(event_id)
        active.append(dict(item))

    # SHUTDOWN ưu tiên trước; trong cùng loại, sự kiện mới hơn đứng trước.
    active.sort(
        key=lambda item: (
            0 if str(item.get("kind")) == "shutdown" else 1,
            str(item.get("published_at") or ""),
        )
    )
    shutdowns = [item for item in active if str(item.get("kind")) == "shutdown"]
    milestones = [item for item in active if str(item.get("kind")) != "shutdown"]
    shutdowns.sort(key=lambda item: str(item.get("published_at") or ""), reverse=True)
    milestones.sort(key=lambda item: str(item.get("published_at") or ""), reverse=True)
    return (shutdowns + milestones)[:GLOBAL_STREAK_EVENT_MAX_ITEMS]


def publish_global_streak_event(event):
    if not isinstance(event, dict) or event.get("kind") not in {"milestone", "shutdown"}:
        return False
    payload = dict(event)
    payload["published_at"] = now_iso()
    payload["expires_at"] = future_iso(GLOBAL_STREAK_EVENT_TTL_SECONDS)
    payload["source"] = "win_streak"
    try:
        result = execute_query(
            db.table("system_settings").select("setting_value")
            .eq("setting_key", GLOBAL_STREAK_EVENT_SETTING_KEY).limit(1),
            "read_global_streak_events", attempts=2,
        )
        raw = ((result.data or [{}])[0]).get("setting_value")
        events = _normalize_global_streak_events(raw)
        events = [item for item in events if str(item.get("id")) != str(payload.get("id"))]
        events.append(payload)
        events = _normalize_global_streak_events(events)
        execute_query(
            db.table("system_settings").upsert({
                "setting_key": GLOBAL_STREAK_EVENT_SETTING_KEY,
                "setting_value": json.dumps(events, ensure_ascii=False),
                "updated_at": now_iso(),
            }, on_conflict="setting_key"),
            "publish_global_streak_event", attempts=2,
        )
        ttl_cache_delete("global_win_streak_events")
        ttl_cache_delete("global_win_streak_event")
        return True
    except Exception as exc:
        print(f"publish_global_streak_event warning: {exc}")
        return False


def get_active_global_streak_events():
    cached = ttl_cache_get("global_win_streak_events")
    if cached is not None:
        return [] if cached is False else cached
    try:
        result = execute_query(
            db.table("system_settings").select("setting_value")
            .eq("setting_key", GLOBAL_STREAK_EVENT_SETTING_KEY).limit(1),
            "get_active_global_streak_events", attempts=2,
        )
        raw = ((result.data or [{}])[0]).get("setting_value")
        events = _normalize_global_streak_events(raw)
        ttl_cache_set("global_win_streak_events", events if events else False, 15)
        return events
    except Exception as exc:
        print(f"get_active_global_streak_events warning: {exc}")
        return []


def get_active_global_streak_event():
    """Tương thích với code cũ: trả sự kiện ưu tiên đầu tiên."""
    events = get_active_global_streak_events()
    return events[0] if events else None


def get_active_announcement():
    try:
        cached = cache_get("_rz_active_announcement")
        if cached is not None:
            return cached

        shared = ttl_cache_get("active_announcement")
        if shared is not None:
            return cache_set("_rz_active_announcement", None if shared is False else shared)
        result = execute_query(
            db.table("admin_announcements")
            .select("*")
            .eq("is_active", True)
            .order("created_at", desc=True)
            .limit(1),
            "get_active_announcement",
        )
        announcement = result.data[0] if result.data else None
        ttl_cache_set("active_announcement", announcement if announcement is not None else False, 15)
        return cache_set("_rz_active_announcement", announcement)
    except Exception:
        return None


def enrich_chat_message(message, users=None):
    if users is None:
        users = users_map()
    user = users.get(message.get("user_id"), {})
    message["user_name"] = user.get("display_name", "Unknown")
    message["user_avatar_url"] = user.get("avatar_url")
    message["user_avatar_frame"] = user.get("avatar_frame")
    message["user_avatar_frame_url"] = (user.get("avatar_frame") or {}).get("image_url") if isinstance(user.get("avatar_frame"), dict) else None
    message["user_achievement"] = user.get("featured_achievement")
    message["user_role"] = "admin" if is_admin_user(user) else user.get("role", "player")
    # Giữ timestamp gốc cho logic chưa đọc, đồng thời gửi chuỗi giờ Việt Nam dễ đọc.
    message["created_at_display"] = format_vn_datetime(message.get("created_at"))
    return message


def list_chat_messages(scope="global", room_id=None, limit=20):
    query = db.table("chat_messages").select("*").eq("scope", scope)

    if room_id:
        query = query.eq("room_id", room_id)
    else:
        query = query.is_("room_id", "null")

    result = execute_query(query.order("created_at", desc=True).limit(limit), "list_chat_messages")
    messages = list(reversed(result.data or []))
    users = users_map()
    return [enrich_chat_message(message, users) for message in messages]


def user_can_chat(user_id, scope="global", room_id=None):
    query = db.table("chat_messages").select("*").eq("user_id", user_id).eq("scope", scope)

    if room_id:
        query = query.eq("room_id", room_id)
    else:
        query = query.is_("room_id", "null")

    result = execute_query(query.order("created_at", desc=True).limit(1), "user_can_chat")
    if not result.data:
        return True, ""

    last_time = parse_dt(result.data[0].get("created_at"))
    if not last_time:
        return True, ""

    diff = (now_dt() - last_time).total_seconds()
    if diff < CHAT_COOLDOWN_SECONDS:
        wait = max(1, int(CHAT_COOLDOWN_SECONDS - diff))
        return False, f"Bạn gửi quá nhanh. Chờ {wait} giây."

    return True, ""


def touch_room_activity(room_id):
    """Reset the 60-minute inactivity timer after a meaningful room action."""
    if not room_id:
        return
    try:
        execute_query(
            db.table("match_rooms").update({"updated_at": now_iso()}).eq("id", room_id),
            "touch_room_activity",
            attempts=1,
        )
        cache_delete("_rz_rooms_all")
    except Exception as exc:
        print(f"touch_room_activity warning: {exc}")


def create_chat_message(user_id, message, scope="global", room_id=None):
    message = (message or "").strip()

    if not message:
        return False, "Tin nhắn không được để trống."

    if len(message) > CHAT_MAX_LENGTH:
        return False, f"Tin nhắn tối đa {CHAT_MAX_LENGTH} ký tự."

    ok, error = user_can_chat(user_id, scope, room_id)
    if not ok:
        return False, error

    db.table("chat_messages").insert({
        "user_id": user_id,
        "room_id": room_id,
        "scope": scope,
        "message": message,
    }).execute()

    if scope == "room" and room_id:
        touch_room_activity(room_id)

    return True, ""

