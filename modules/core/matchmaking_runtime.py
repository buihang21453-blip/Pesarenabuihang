"""Module hóa từ V1.2.9.

Giữ nguyên logic gốc; dependency được truyền từ app.py bằng configure() để tránh import vòng.
"""

_CONTEXT = {}

def configure(context):
    _CONTEXT.clear()
    _CONTEXT.update(context)
    globals().update(context)

EXPORTED_NAMES = ['is_player_in_cooldown', 'cooldown_text', 'current_pending_invites', 'current_pending_invite_count', 'room_is_active', '_direct_active_rooms_for_user', 'cleanup_duplicate_waiting_rooms', 'active_room_for_user', 'build_room_head_to_head', '_room_by_match_id', 'match_blocks_new_room', 'active_match_for_user', 'busy_user_ids', 'has_active_room_between', 'has_active_match_between', 'has_pending_invite_between', 'is_solo_waiting_room', 'matchmaking_snapshot']

def is_player_in_cooldown(user):
    cooldown = parse_dt(user.get("matchmaking_cooldown_until"))
    return bool(cooldown and cooldown > now_dt())


def cooldown_text(user):
    cooldown = parse_dt(user.get("matchmaking_cooldown_until"))
    if not cooldown or cooldown <= now_dt():
        return ""
    seconds = int((cooldown - now_dt()).total_seconds())
    minutes = max(1, seconds // 60 + (1 if seconds % 60 else 0))
    return f"{minutes} phút"


def current_pending_invites():
    cached = cache_get("_rz_current_pending_invites")
    if cached is not None:
        return cached
    try:
        user = current_user()
        if not user:
            return cache_set("_rz_current_pending_invites", [])
        invites = list_invites("pending")
        return cache_set("_rz_current_pending_invites", [invite for invite in invites if invite["to_user_id"] == user["id"]])
    except Exception as exc:
        print(f"current_pending_invites warning: {exc}")
        return []


def current_pending_invite_count():
    try:
        return len(current_pending_invites())
    except Exception:
        return 0


def room_is_active(room):
    if room.get("status") in {"waiting_ready", "playing", "friendly_playing", "waiting_result_confirm"}:
        return True
    return (
        room.get("status") == "confirmed"
        and (room.get("note") or "") in {REMATCH_HOST_READY_NOTE, REMATCH_GUEST_READY_NOTE}
    )


def _direct_active_rooms_for_user(user_id, limit=20):
    """Đọc phòng active trực tiếp từ bảng match_rooms, không dùng cache Vercel."""
    if not user_id:
        return []
    result = execute_query(
        db.table("match_rooms")
        .select("*")
        .or_(f"host_user_id.eq.{user_id},guest_user_id.eq.{user_id}")
        .in_("status", sorted(ACTIVE_ROOM_STATUSES))
        .order("updated_at", desc=True)
        .limit(limit),
        "active_room_for_user_direct",
        attempts=2,
    )
    return list(result.data or [])


def cleanup_duplicate_waiting_rooms(user_id):
    """Xóa an toàn các phòng waiting_ready bị nhân đôi của một người chơi.

    Chỉ đụng tới phòng chưa có match_id. Phòng có đối thủ được ưu tiên giữ lại;
    nếu nhiều phòng cùng loại thì giữ phòng cập nhật mới nhất. Lời mời gắn với
    phòng bị xóa cũng được đóng để không còn trạng thái treo.
    """
    try:
        rooms = [
            room for room in _direct_active_rooms_for_user(user_id)
            if str(room.get("status") or "") == "waiting_ready" and not room.get("match_id")
        ]
    except Exception as exc:
        print(f"cleanup_duplicate_waiting_rooms load warning: {exc}")
        return 0
    if len(rooms) <= 1:
        return 0

    rooms.sort(
        key=lambda room: (
            1 if room.get("guest_user_id") else 0,
            1 if room.get("invite_id") else 0,
            str(room.get("updated_at") or room.get("created_at") or ""),
            str(room.get("id") or ""),
        ),
        reverse=True,
    )
    keep_id = str(rooms[0].get("id"))
    removed = 0
    for room in rooms[1:]:
        room_id = room.get("id")
        if not room_id or str(room_id) == keep_id:
            continue
        try:
            deleted = execute_query(
                db.table("match_rooms").delete()
                .eq("id", room_id)
                .eq("status", "waiting_ready")
                .is_("match_id", "null"),
                "cleanup_duplicate_waiting_room",
                attempts=2,
            )
            if deleted.data:
                removed += 1
                invite_id = room.get("invite_id")
                if invite_id:
                    execute_query(
                        db.table("match_invites").update({
                            "status": "cancelled",
                            "updated_at": now_iso(),
                        }).eq("id", invite_id).eq("status", "pending"),
                        "cleanup_duplicate_waiting_room_invite",
                        attempts=2,
                    )
        except Exception as exc:
            print(f"cleanup duplicate room warning room={room_id}: {exc}")
    if removed:
        cache_delete("_rz_rooms_all")
        cache_delete("_rz_invites_all")
        cache_delete("_rz_current_pending_invites")
        ttl_cache_delete("rooms_raw")
        ttl_cache_delete("invites_raw")
    return removed


def active_room_for_user(user_id, exclude_room_id=None):
    """Tìm trực tiếp mọi phòng active của người chơi từ match_rooms."""
    if not user_id:
        return None
    try:
        rooms = _direct_active_rooms_for_user(user_id)
        for room in rooms:
            if exclude_room_id and str(room.get("id")) == str(exclude_room_id):
                continue
            return room
    except Exception as exc:
        print(f"active_room_for_user direct warning: {exc}")

    try:
        for room in list_rooms():
            if exclude_room_id and str(room.get("id")) == str(exclude_room_id):
                continue
            if str(room.get("status") or "").lower() in ACTIVE_ROOM_STATUSES and user_id in [room.get("host_user_id"), room.get("guest_user_id")]:
                return room
    except Exception as exc:
        print(f"active_room_for_user fallback warning: {exc}")
    return None


def build_room_head_to_head(room):
    """Thống kê đối đầu trong phòng bằng truy vấn nhỏ, có fallback an toàn.

    Trước đây mỗi lần khách nhận thay đổi trạng thái và tải lại phòng, hàm này
    gọi ``list_matches("confirmed")`` nên phải lấy và làm giàu toàn bộ lịch sử
    trận của hệ thống. Phòng chơi nhiều ván liên tiếp vì thế có thể tải chậm hơn,
    đặc biệt ở phía khách vốn đồng bộ bằng polling. Bản này chỉ đọc các cột cần
    thiết của đúng hai người chơi kể từ thời điểm mở phòng.
    """
    host_id = room.get("host_user_id")
    guest_id = room.get("guest_user_id")
    room_created_at = room.get("created_at")
    room_opened_at = parse_dt(room_created_at)

    empty = {
        "available": bool(host_id and guest_id),
        "total": 0,
        "host_wins": 0,
        "guest_wins": 0,
        "draws": 0,
        "host_goals": 0,
        "guest_goals": 0,
        "matches": [],
        "since": format_vn_datetime(room_created_at),
    }
    if not host_id or not guest_id:
        return empty

    raw_matches = None
    try:
        pair_filter = (
            f"and(player1_id.eq.{host_id},player2_id.eq.{guest_id}),"
            f"and(player1_id.eq.{guest_id},player2_id.eq.{host_id})"
        )
        query = (
            db.table("matches")
            .select("id,player1_id,player2_id,score1,score2,delta1,delta2,created_at,status")
            .eq("status", "confirmed")
            .or_(pair_filter)
        )
        if room_created_at:
            query = query.gte("created_at", room_created_at)
        query = query.order("created_at", desc=True).limit(100)
        result = execute_query(query, "room_head_to_head_pair", attempts=2)
        raw_matches = result.data or []
    except Exception as exc:
        # Không để phần lịch sử phụ làm hỏng toàn bộ phòng nếu Supabase/PostgREST
        # tạm thời không nhận bộ lọc OR. Fallback giữ nguyên hành vi bản cũ.
        app.logger.warning("Room head-to-head optimized query failed; using cache fallback: %s", exc)

    pair = {str(host_id), str(guest_id)}
    if raw_matches is None:
        raw_matches = []
        for match in list_matches("confirmed"):
            if {str(match.get("player1_id")), str(match.get("player2_id"))} != pair:
                continue
            match_time = parse_dt(match.get("created_at"))
            if room_opened_at and match_time and match_time < room_opened_at:
                continue
            raw_matches.append(match)

    selected = []
    for match in raw_matches:
        if {str(match.get("player1_id")), str(match.get("player2_id"))} != pair:
            continue
        match_time = parse_dt(match.get("created_at"))
        if room_opened_at and match_time and match_time < room_opened_at:
            continue

        try:
            score1 = int(match.get("score1") or 0)
            score2 = int(match.get("score2") or 0)
        except (TypeError, ValueError):
            continue

        host_is_player1 = str(match.get("player1_id")) == str(host_id)
        host_score = score1 if host_is_player1 else score2
        guest_score = score2 if host_is_player1 else score1
        item = {
            "id": match.get("id"),
            "created_at_display": format_vn_datetime(match.get("created_at")),
            "host_score": host_score,
            "guest_score": guest_score,
            "host_delta": _normalize_match_delta(
                match.get("delta1") if host_is_player1 else match.get("delta2")
            ),
            "guest_delta": _normalize_match_delta(
                match.get("delta2") if host_is_player1 else match.get("delta1")
            ),
        }
        selected.append(item)

        empty["host_goals"] += host_score
        empty["guest_goals"] += guest_score
        if host_score > guest_score:
            empty["host_wins"] += 1
        elif guest_score > host_score:
            empty["guest_wins"] += 1
        else:
            empty["draws"] += 1

    empty["total"] = len(selected)
    # Cột phải chỉ cần các trận mới nhất; tổng W-D-L vẫn tính trên toàn phiên.
    empty["matches"] = selected[:8]
    return empty


def _room_by_match_id(rooms):
    return {
        str(room.get("match_id")): room
        for room in (rooms or [])
        if room.get("match_id") not in (None, "")
    }


def match_blocks_new_room(match, linked_room=None):
    """Chỉ khóa người chơi khi trận còn gắn với một phòng đang hoạt động.

    Một bản ghi ``matches`` còn ``playing``/``waiting_confirm`` nhưng phòng đã
    ``cancelled`` hoặc không còn tồn tại là dữ liệu mồ côi. Nó không được tiếp
    tục chặn người chơi tạo phòng mới.
    """
    if not match or match.get("status") not in {"playing", "waiting_confirm"}:
        return False
    return bool(linked_room and room_is_active(linked_room))


def active_match_for_user(user_id):
    """Trả về trận thật sự đang khóa người chơi, bỏ qua match mồ côi."""
    user_key = str(user_id)
    rooms = list_rooms()
    rooms_by_match = _room_by_match_id(rooms)
    for match in list_matches():
        if user_key not in {str(match.get("player1_id")), str(match.get("player2_id"))}:
            continue
        linked_room = rooms_by_match.get(str(match.get("id")))
        if match_blocks_new_room(match, linked_room):
            return match
    return None


def busy_user_ids(rooms=None, matches=None):
    """Trả về tập user đang có phòng hoặc trận thật sự chưa hoàn tất."""
    rooms = list_rooms() if rooms is None else rooms
    matches = list_matches() if matches is None else matches
    busy = set()

    for room in rooms:
        if room_is_active(room):
            busy.add(room.get("host_user_id"))
            busy.add(room.get("guest_user_id"))

    rooms_by_match = _room_by_match_id(rooms)
    for match in matches:
        linked_room = rooms_by_match.get(str(match.get("id")))
        if match_blocks_new_room(match, linked_room):
            busy.add(match.get("player1_id"))
            busy.add(match.get("player2_id"))

    busy.discard(None)
    return busy


def has_active_room_between(user_a, user_b):
    active_statuses = {"waiting_ready", "playing", "waiting_result_confirm"}
    for room in list_rooms():
        same_pair = {room.get("host_user_id"), room.get("guest_user_id")} == {user_a, user_b}
        if same_pair and room.get("status") in active_statuses:
            return True
    return False


def has_active_match_between(user_a, user_b):
    active_statuses = {"playing", "waiting_confirm"}
    for match in list_matches():
        same_pair = {match.get("player1_id"), match.get("player2_id")} == {user_a, user_b}
        if same_pair and match.get("status") in active_statuses:
            return True
    return False


def has_pending_invite_between(user_a, user_b):
    for invite in list_invites("pending"):
        same_pair = {invite.get("from_user_id"), invite.get("to_user_id")} == {user_a, user_b}
        if same_pair:
            return True
    return False


def is_solo_waiting_room(room, user_id):
    """True only when user is the host of an empty room that has not started."""
    if not room or not user_id:
        return False
    return bool(
        str(room.get("host_user_id")) == str(user_id)
        and room.get("status") == "waiting_ready"
        and not room.get("guest_user_id")
    )


def matchmaking_snapshot(user_a, user_b=None):
    """Fetch only the small raw state needed by invite actions.

    This avoids loading/enriching every room, match, achievement and team merely
    to decide whether two users are available.
    """
    ids = {str(user_a)}
    if user_b:
        ids.add(str(user_b))
    rooms_result = execute_query(
        db.table("match_rooms")
        .select("id,match_id,host_user_id,guest_user_id,status,invite_id")
        .in_("status", ["waiting_ready", "playing", "friendly_playing", "waiting_result_confirm", "waiting_confirm", "disputed"]),
        "matchmaking_active_rooms",
        attempts=3,
    )
    matches_result = execute_query(
        db.table("matches")
        .select("id,player1_id,player2_id,status")
        .in_("status", ["playing", "waiting_confirm", "processing_result", "disputed"]),
        "matchmaking_active_matches",
        attempts=3,
    )
    invites_result = execute_query(
        db.table("match_invites")
        .select("id,from_user_id,to_user_id,status,expires_at,created_at")
        .eq("status", "pending"),
        "matchmaking_pending_invites",
        attempts=3,
    )
    rooms = [dict(x) for x in (rooms_result.data or [])]
    active_match_ids = {str(r.get("match_id")) for r in rooms if r.get("match_id")}
    # Trận mồ côi không còn phòng hoạt động không được chặn ghép trận/lời mời.
    matches = [dict(x) for x in (matches_result.data or []) if str(x.get("id")) in active_match_ids]

    invites = []
    now = now_dt()
    for raw in (invites_result.data or []):
        invite = dict(raw)
        expires_at = parse_dt(invite.get("expires_at"))
        if expires_at and expires_at <= now:
            try:
                execute_query(
                    db.table("match_invites").update({
                        "status": "expired",
                        "updated_at": now_iso(),
                    }).eq("id", invite.get("id")).eq("status", "pending"),
                    "matchmaking_expire_stale_invite",
                    attempts=1,
                )
            except Exception as exc:
                print(f"matchmaking stale invite warning id={invite.get('id')}: {exc}")
            continue
        invites.append(invite)

    def room_for(uid):
        uid = str(uid)
        return next((r for r in rooms if uid in {str(r.get("host_user_id")), str(r.get("guest_user_id"))}), None)

    def match_for(uid):
        uid = str(uid)
        return next((m for m in matches if uid in {str(m.get("player1_id")), str(m.get("player2_id"))}), None)

    pair_pending = False
    if user_b:
        target = {str(user_a), str(user_b)}
        pair_pending = any({str(i.get("from_user_id")), str(i.get("to_user_id"))} == target for i in invites)
    return {
        "rooms": rooms,
        "matches": matches,
        "invites": invites,
        "room_a": room_for(user_a),
        "room_b": room_for(user_b) if user_b else None,
        "match_a": match_for(user_a),
        "match_b": match_for(user_b) if user_b else None,
        "pair_pending": pair_pending,
    }

