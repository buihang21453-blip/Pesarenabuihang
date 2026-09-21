"""Legacy service extracted from app.py with behavior preserved.

The application injects its runtime dependencies through configure(context).
"""

EXPORTED_NAMES = ['get_user_by_username', 'calculated_total_matches', 'get_invisible_player_ids', 'is_player_invisible', 'can_view_player_identity', 'filter_players_for_viewer', 'invite_visible_players', 'match_visible_to_viewer', '_ranking_activity_match', '_latest_ranking_activity_map', 'ranking_eligibility', 'normalize_player_match_totals', 'get_user', 'is_user_online_now', '_player_ranking_sort_key', 'list_players', 'archived_users_map', 'users_map']

def configure(context):
    globals().update(context)

def get_user_by_username(username):
    """Find a user by username without creating extra Supabase clients."""
    require_db()
    normalized = str(username or "").strip()
    if not normalized:
        return None

    result = execute_query(
        db.table("users").select("*").ilike("username", normalized).limit(20),
        "get_user_by_username",
    )
    target = normalized.casefold()
    return next(
        (
            row for row in (result.data or [])
            if str(row.get("username") or "").strip().casefold() == target
        ),
        None,
    )


def calculated_total_matches(player):
    """Nguồn chuẩn duy nhất: tổng trận = thắng + hòa + thua."""
    player = player or {}
    return max(0, int(player.get("wins", 0) or 0)) + max(0, int(player.get("draws", 0) or 0)) + max(0, int(player.get("losses", 0) or 0))


def get_invisible_player_ids(force=False):
    request_key = "_invisible_player_ids_cached"
    if not force:
        cached = cache_get(request_key)
        if isinstance(cached, (set, list, tuple)):
            return {str(item) for item in cached if item}
        cached = ttl_cache_get("invisible_player_ids")
        if isinstance(cached, (set, list, tuple)):
            values = {str(item) for item in cached if item}
            cache_set(request_key, values)
            return values

    values = set()
    try:
        result = execute_query(
            db.table("system_settings").select("setting_value")
            .eq("setting_key", INVISIBLE_PLAYERS_SETTING_KEY).limit(1),
            "get_invisible_player_ids", attempts=2,
        )
        raw = ((result.data or [{}])[0]).get("setting_value")
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except Exception:
                raw = []
        if isinstance(raw, dict):
            raw = raw.get("user_ids") or []
        if isinstance(raw, (list, tuple, set)):
            values = {str(item) for item in raw if item}
    except Exception as exc:
        print(f"get_invisible_player_ids warning: {exc}")

    ttl_cache_set("invisible_player_ids", sorted(values), 45)
    cache_set(request_key, values)
    return values


def is_player_invisible(user_id, invisible_ids=None):
    if not user_id:
        return False
    ids = invisible_ids if invisible_ids is not None else get_invisible_player_ids()
    return str(user_id) in {str(item) for item in ids}


def can_view_player_identity(target_user_id, viewer=None, invisible_ids=None):
    """Admin và tài khoản tàng hình thấy đầy đủ; tài khoản thường không thấy tài khoản tàng hình."""
    if not target_user_id:
        return True
    viewer = viewer if viewer is not None else current_user()
    if is_admin_user(viewer):
        return True
    ids = invisible_ids if invisible_ids is not None else get_invisible_player_ids()
    ids = {str(item) for item in ids}
    viewer_id = str((viewer or {}).get("id") or "")
    # Các tài khoản tàng hình tạo thành một nhóm nhìn thấy nhau, đồng thời vẫn
    # nhìn thấy toàn bộ tài khoản thường như người dùng bình thường.
    if viewer_id and viewer_id in ids:
        return True
    target_id = str(target_user_id)
    return target_id not in ids


def filter_players_for_viewer(players, viewer=None, invisible_ids=None, *, preserve_deleted=False):
    viewer = viewer if viewer is not None else current_user()
    ids = invisible_ids if invisible_ids is not None else get_invisible_player_ids()
    ids = {str(item) for item in ids}
    rows = list(players or [])

    # deleted chỉ còn là hồ sơ lưu lịch sử. Không xuất hiện ở Players, tìm kiếm,
    # mời đấu hoặc BXH mùa hiện tại. Riêng BXH mùa đã đóng có thể bật
    # preserve_deleted=True để giữ nguyên thứ hạng lịch sử.
    if not preserve_deleted:
        rows = [p for p in rows if str(p.get("account_status") or "approved").lower() != "deleted"]

    if is_admin_user(viewer):
        return rows

    viewer_id = str((viewer or {}).get("id") or "")
    if viewer_id and viewer_id in ids:
        return rows

    return [player for player in rows if str(player.get("id") or "") not in ids]


def invite_visible_players(viewer=None, *, include_admin=False, force_invisible_refresh=True):
    """Danh sách dùng cho các bề mặt Mời đấu.

    - Invisible viewer: thấy mọi player khác, kể cả Invisible.
    - Normal viewer: không thấy Invisible.
    - Có thể ép đọc lại setting từ DB để tránh cache cũ trên serverless instance.
    """
    viewer = viewer if viewer is not None else current_user()
    invisible_ids = get_invisible_player_ids(force=force_invisible_refresh)
    rows = list_players(include_admin=include_admin)
    return filter_players_for_viewer(rows, viewer, invisible_ids)


def match_visible_to_viewer(match, viewer=None, invisible_ids=None):
    viewer = viewer if viewer is not None else current_user()
    ids = invisible_ids if invisible_ids is not None else get_invisible_player_ids()
    if is_admin_user(viewer):
        return True
    return all(
        can_view_player_identity(user_id, viewer, ids)
        for user_id in (match.get("player1_id"), match.get("player2_id"))
        if user_id
    )


def _ranking_activity_match(match):
    """Một trận được xem là hoạt động Rank để duy trì trạng thái trên BXH."""
    status = str((match or {}).get("status") or "").strip().lower()
    if status == "confirmed":
        return True
    if status == "cancelled":
        try:
            return bool(is_forfeit_match(match))
        except Exception:
            note = str((match or {}).get("note") or "").casefold()
            return "[forfeit:" in note or "bỏ cuộc" in note
    return False


def _latest_ranking_activity_map(matches):
    latest = {}
    for match in matches or []:
        if not _ranking_activity_match(match):
            continue
        created = parse_dt((match or {}).get("created_at"))
        if not created:
            continue
        for user_id in ((match or {}).get("player1_id"), (match or {}).get("player2_id")):
            key = str(user_id or "")
            if not key:
                continue
            old = latest.get(key)
            if old is None or created > old:
                latest[key] = created
    return latest


def ranking_eligibility(player, latest_activity_at=None, now=None):
    """Trạng thái BXH: đủ 5 trận và chưa vắng Rank 30 ngày."""
    matches = calculated_total_matches(player or {})
    if matches < RANKING_QUALIFY_MATCHES:
        return {
            "visible": False,
            "reason": "placement",
            "matches": matches,
            "matches_needed": RANKING_QUALIFY_MATCHES - matches,
            "inactive_days": 0,
        }

    if latest_activity_at:
        now = now or now_dt()
        inactive_days = max(0, int((now - latest_activity_at).total_seconds() // 86400))
        if inactive_days >= RANKING_INACTIVE_HIDE_DAYS:
            return {
                "visible": False,
                "reason": "inactive",
                "matches": matches,
                "matches_needed": 0,
                "inactive_days": inactive_days,
            }
    else:
        inactive_days = 0

    return {
        "visible": True,
        "reason": "ranked",
        "matches": matches,
        "matches_needed": 0,
        "inactive_days": inactive_days,
    }


def normalize_player_match_totals(player):
    item = dict(player or {})
    item["total_matches"] = calculated_total_matches(item)
    return item


def get_user(user_id):
    require_db()
    result = execute_query(
        db.table("users").select("*").eq("id", user_id).limit(1),
        "get_user",
    )
    return normalize_player_match_totals(result.data[0]) if result.data else None


def is_user_online_now(user):
    seen = parse_dt((user or {}).get("last_seen_at"))
    cutoff = now_dt() - timedelta(seconds=ONLINE_TIMEOUT_SECONDS)
    return bool((user or {}).get("is_online")) and bool(seen) and seen >= cutoff


def _player_ranking_sort_key(player):
    points = int(player.get("rank_points", 0) or 0)
    wins = int(player.get("wins", 0) or 0)
    goals_for = int(player.get("goals_for", 0) or 0)
    goals_against = int(player.get("goals_against", 0) or 0)
    total_matches = calculated_total_matches(player)
    name = str(player.get("display_name") or player.get("username") or "").casefold()
    return (-points, -wins, -(goals_for - goals_against), -goals_for, -total_matches, name)


def list_players(include_admin=False):
    require_db()
    cached = cache_get("_rz_players_all")
    if cached is None:
        shared = ttl_cache_get("players_raw")
        if shared is None:
            result = execute_query(
                db.table("users").select("*").order("rank_points", desc=True),
                "list_players",
            )
            shared = result.data or []
            ttl_cache_set("players_raw", shared, 8)
        cached = [dict(row) for row in shared]
        cache_set("_rz_players_all", cached)

    players = cached if include_admin else [p for p in cached if p.get("role") == "player"]
    safe = []
    for player in players:
        item = normalize_player_match_totals(player)
        item["is_online"] = is_user_online_now(item)
        safe.append(item)

    # Xếp hạng ổn định khi nhiều người bằng điểm: thắng, hiệu số, bàn thắng, số trận.
    achievement_map = list_user_achievement_map()
    if not include_admin:
        safe.sort(key=_player_ranking_sort_key)
        official_position = 0
        for item in safe:
            if calculated_total_matches(item) >= RANKING_QUALIFY_MATCHES:
                official_position += 1
                item["position"] = official_position
                item["ranking_status"] = "official"
                item["matches_to_official_rank"] = 0
                item["rank_info"] = get_player_rank_info(item, official_position)
                decorate_player_achievements(item, official_position, achievement_map)
            else:
                item["position"] = None
                item["ranking_status"] = "placement"
                item["matches_to_official_rank"] = max(0, RANKING_QUALIFY_MATCHES - calculated_total_matches(item))
                item["rank_info"] = get_player_rank_info(item, None)
                decorate_player_achievements(item, None, achievement_map)
    else:
        for item in safe:
            item["rank_info"] = get_rank_info(item.get("rank_points", 0))
            decorate_player_achievements(item, None, achievement_map)

    # Gắn mỹ phẩm hồ sơ theo lô để Players/BXH/Dashboard dùng chung,
    # tránh truy vấn N+1 cho từng người chơi.
    try:
        avatar_frame_map = profile_equipment_service.build_avatar_frame_map(safe)
        name_style_map = profile_equipment_service.build_name_style_map(safe)
        profile_badge_map = profile_equipment_service.build_profile_badge_map(safe)
    except Exception as exc:
        app.logger.debug("Player cosmetic map fallback: %s", exc)
        avatar_frame_map = {}
        name_style_map = {}
        profile_badge_map = {}
    for item in safe:
        user_id = str(item.get("id"))
        item["avatar_frame"] = avatar_frame_map.get(user_id)
        item["name_style"] = name_style_map.get(user_id)
        item["profile_badge"] = profile_badge_map.get(user_id)
        metadata = (item.get("name_style") or {}).get("metadata") if isinstance(item.get("name_style"), dict) else {}
        item["name_style_class"] = str((metadata or {}).get("css_class") or "").strip()

    return safe


def archived_users_map():
    """Danh tính tối thiểu của tài khoản đã xóa thật, chỉ dùng để đọc lịch sử trận."""
    cached = cache_get("_rz_archived_users_map")
    if cached is not None:
        return cached
    rows = []
    try:
        result = execute_query(
            db.table("archived_player_identities").select("user_id,username,display_name,avatar_url"),
            "archived_users_map", attempts=2,
        )
        rows = list(result.data or [])
    except Exception as exc:
        # Tương thích trước khi chạy SQL V1.4.17: lịch sử vẫn mở được, chỉ thiếu tên archive.
        print(f"archived_users_map warning: {exc}")
    mapped = {str(row.get("user_id")): dict(row) for row in rows if row.get("user_id")}
    return cache_set("_rz_archived_users_map", mapped)


def users_map():
    cached = cache_get("_rz_users_map")
    if cached is not None:
        return cached

    mapped = {user["id"]: user for user in list_players(include_admin=True)}
    return cache_set("_rz_users_map", mapped)

