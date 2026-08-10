"""Module hóa từ V1.2.9.

Giữ nguyên logic gốc; dependency được truyền từ app.py bằng configure() để tránh import vòng.
"""

from modules.presence.service import is_online as presence_is_online

_CONTEXT = {}

def configure(context):
    _CONTEXT.clear()
    _CONTEXT.update(context)
    globals().update(context)

EXPORTED_NAMES = ['list_admin_overview_users', 'get_user_by_username', 'calculated_total_matches', 'normalize_player_match_totals', 'get_user', 'is_user_online_now', '_player_ranking_sort_key', 'list_players', 'users_map', 'get_device_link', 'is_admin_managed_test_account', 'get_duplicate_ip_warning_config', 'user_ignored_for_duplicate_ip', 'link_device_to_user', 'device_can_register', 'list_all_users', 'log_admin_action', 'existing_user_id', 'create_admin_announcement', 'list_admin_activity_logs', 'get_password_reset_request', 'list_password_reset_requests', 'list_user_devices', 'decorate_admin_users', 'build_duplicate_ip_groups', 'get_invite_code_record', 'list_registration_invite_codes']

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
    """Một nguồn quyết định Online dùng chung cho Players / Invite / Quick Match."""
    return presence_is_online(
        user,
        now=now_dt(),
        parse_datetime=parse_dt,
        timeout_seconds=ONLINE_TIMEOUT_SECONDS,
    )


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
            ttl_cache_set("players_raw", shared, 20)
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
        for position, item in enumerate(safe, 1):
            item["position"] = position
            item["rank_info"] = get_player_rank_info(item, position)
            decorate_player_achievements(item, position, achievement_map)
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


def users_map():
    cached = cache_get("_rz_users_map")
    if cached is not None:
        return cached

    mapped = {user["id"]: user for user in list_players(include_admin=True)}
    return cache_set("_rz_users_map", mapped)


def get_device_link(device_id):
    result = db.table("user_devices").select("*").eq("device_id", device_id).limit(1).execute()
    return result.data[0] if result.data else None


def is_admin_managed_test_account(user):
    """Tài khoản do Admin tạo/import: không bị khóa theo thiết bị hoặc cảnh báo trùng IP."""
    marker = str((user or {}).get("register_ip") or "").strip().upper()
    return marker.startswith("ADMIN_TEST") or marker.startswith("ADMIN_CREATED")


def get_duplicate_ip_warning_config(force=False):
    """Cấu hình cảnh báo IP: bật/tắt toàn cục và danh sách tài khoản tin cậy."""
    now = time.time()
    if not force and _ip_warning_config_cache["value"] is not None and now < _ip_warning_config_cache["expires_at"]:
        return dict(_ip_warning_config_cache["value"])

    config = {"enabled": True, "ignore_admin_managed": True, "trusted_user_ids": []}
    if db is not None:
        try:
            result = execute_query(
                db.table("system_settings").select("setting_value")
                .eq("setting_key", IP_WARNING_SETTING_KEY).limit(1),
                "load_duplicate_ip_warning_config", attempts=2,
            )
            stored = (result.data or [{}])[0].get("setting_value") if result.data else {}
            if isinstance(stored, dict):
                config["enabled"] = bool(stored.get("enabled", True))
                config["ignore_admin_managed"] = bool(stored.get("ignore_admin_managed", True))
                config["trusted_user_ids"] = sorted({str(x) for x in (stored.get("trusted_user_ids") or []) if x})
        except Exception as exc:
            print(f"duplicate ip config warning: {exc}")

    _ip_warning_config_cache.update({"value": dict(config), "expires_at": now + 30})
    return config


def user_ignored_for_duplicate_ip(user, config=None):
    config = config or get_duplicate_ip_warning_config()
    if not user:
        return False
    user_id = str(user.get("id") or "")
    if user_id and user_id in set(config.get("trusted_user_ids") or []):
        return True
    if config.get("ignore_admin_managed", True):
        return user.get("role") == "admin" or is_admin_user(user) or is_admin_managed_test_account(user)
    return False


def link_device_to_user(user):
    # Admin chính và tài khoản do Admin tạo/import không bị giới hạn thiết bị/IP.
    # Đây chỉ là ngoại lệ xác thực; mọi trận Rank vẫn tính W/H/B và RP bình thường.
    if user.get("role") == "admin" or is_admin_managed_test_account(user):
        return True, ""

    device_id = get_device_id()
    link = get_device_link(device_id)

    if link and link["user_id"] != user["id"]:
        return False, "Thiết bị này đã được liên kết với một tài khoản player khác."

    ip = get_client_ip()
    user_agent = request.headers.get("User-Agent", "")

    if not link:
        execute_query(
            db.table("user_devices").insert({
                "user_id": user["id"],
                "device_id": device_id,
                "ip_address": ip,
                "user_agent": user_agent,
                "last_seen_at": now_iso(),
            }),
            "link_device_create",
        )
    else:
        execute_query(
            db.table("user_devices").update({
                "ip_address": ip,
                "user_agent": user_agent,
                "last_seen_at": now_iso(),
            }).eq("id", link["id"]),
            "link_device_update",
        )

    return True, ""


def device_can_register():
    device_id = get_device_id()
    link = get_device_link(device_id)
    if link:
        return False, "Thiết bị này đã có tài khoản player. Mỗi thiết bị chỉ được tạo 1 tài khoản."

    ip = get_client_ip()
    ua = request.headers.get("User-Agent", "")

    # Chặn mềm: cùng IP + cùng User Agent đã từng đăng ký.
    result = (
        db.table("users")
        .select("id")
        .eq("role", "player")
        .eq("register_ip", ip)
        .eq("register_user_agent", ua)
        .limit(1)
        .execute()
    )

    if result.data:
        return False, "Thiết bị/trình duyệt này có dấu hiệu đã đăng ký tài khoản player."

    return True, ""


def list_all_users(limit=None, offset=0):
    """Danh sách user cho Admin; hỗ trợ limit để tab không phải tải toàn bộ bảng."""
    require_db()
    query = db.table("users").select("*").order("created_at", desc=True)
    if limit:
        limit = max(1, int(limit))
        offset = max(0, int(offset or 0))
        if offset:
            query = query.range(offset, offset + limit - 1)
        else:
            query = query.limit(limit)
    result = execute_query(query, f"list_all_users:{limit or 'all'}:{offset or 0}")
    return result.data or []


def list_admin_overview_users(limit=120):
    """Payload nhẹ cho trang /admin mặc định, không kéo IP thiết bị/cosmetic."""
    require_db()
    fields = "id,username,display_name,zalo_name,role,admin_level,account_status,register_ip,created_at,rank_points,wins,draws,losses"
    result = execute_query(
        db.table("users").select(fields).order("created_at", desc=True).limit(max(1, int(limit))),
        f"list_admin_overview_users:{limit}",
    )
    rows = [normalize_player_match_totals(dict(row)) for row in (result.data or [])]
    for row in rows:
        row["admin_permissions"] = _admin_permissions(row)
    return rows


def log_admin_action(action, target_type="system", target_id=None, target_label="", details=""):
    """Ghi nhật ký quản trị; lỗi ghi log không được làm hỏng thao tác chính."""
    try:
        actor = current_user()
        if not actor or not is_admin_user(actor):
            return
        execute_query(
            db.table("admin_activity_logs").insert({
                "admin_user_id": actor.get("id"),
                "admin_name": actor.get("username") or actor.get("display_name") or "Admin",
                "action": str(action)[:80],
                "target_type": str(target_type)[:50],
                "target_id": str(target_id)[:120] if target_id else None,
                "target_label": str(target_label)[:160] if target_label else None,
                "details": str(details)[:1000] if details else None,
                "ip_address": get_client_ip(),
            }),
            "log_admin_action",
            attempts=2,
        )
    except Exception as exc:
        print(f"Admin audit log warning: {exc}")


def existing_user_id(user_id):
    """Trả về UUID chỉ khi người dùng thực sự còn tồn tại trong public.users."""
    if not user_id:
        return None
    try:
        result = execute_query(
            db.table("users").select("id").eq("id", user_id).limit(1),
            "existing_user_id",
            attempts=1,
        )
        rows = result.data or []
        return rows[0].get("id") if rows else None
    except Exception as exc:
        print(f"existing_user_id warning: {exc}")
        return None


def create_admin_announcement(title, message, admin_user_id=None):
    """Tạo thông báo và tự phục hồi khi khóa ngoại admin cũ bị lệch.

    Một số dự án nâng cấp từ phiên bản cũ còn giữ session/admin UUID không còn
    tồn tại trong public.users. Khi đó Postgres trả mã 23503. Thông báo không
    bắt buộc phải có admin_user_id nên ta thử lại với NULL thay vì gây lỗi 500.
    """
    payload = {
        "admin_user_id": existing_user_id(admin_user_id),
        "title": title,
        "message": message,
        "is_active": True,
    }
    try:
        return db.table("admin_announcements").insert(payload).execute()
    except Exception as exc:
        error_code = str(getattr(exc, "code", "") or "")
        error_text = str(exc)
        if payload["admin_user_id"] and (error_code == "23503" or "23503" in error_text):
            payload["admin_user_id"] = None
            return db.table("admin_announcements").insert(payload).execute()
        raise


def list_admin_activity_logs(limit=150):
    try:
        result = execute_query(
            db.table("admin_activity_logs")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit),
            "list_admin_activity_logs",
        )
        return result.data or []
    except Exception as exc:
        print(f"list_admin_activity_logs warning: {exc}")
        return []


def get_password_reset_request(request_id):
    result = execute_query(
        db.table("password_reset_requests").select("*").eq("id", request_id).limit(1),
        "get_password_reset_request",
    )
    return result.data[0] if result.data else None


def list_password_reset_requests(status=None, limit=100):
    try:
        query = (
            db.table("password_reset_requests")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
        )
        if status:
            query = query.eq("status", status)
        result = execute_query(query, "list_password_reset_requests")
        rows = [dict(row) for row in (result.data or [])]
        # Không gọi users_map() ở Admin: hàm đó kéo toàn bộ player + cosmetic/achievement.
        # Chỉ đọc đúng các user có yêu cầu quên mật khẩu.
        user_ids = sorted({str(row.get("user_id")) for row in rows if row.get("user_id")})
        users = {}
        if user_ids:
            try:
                user_result = execute_query(
                    db.table("users").select("id,username,zalo_name").in_("id", user_ids),
                    "password_reset_users", attempts=2,
                )
                users = {str(item.get("id")): item for item in (user_result.data or [])}
            except Exception as exc:
                print(f"password_reset_users warning: {exc}")
        for row in rows:
            user = users.get(str(row.get("user_id")), {})
            row["current_username"] = user.get("username") or row.get("username_snapshot") or "-"
            row["current_zalo_name"] = user.get("zalo_name") or row.get("zalo_name_snapshot") or "-"
        return rows
    except Exception as exc:
        print(f"list_password_reset_requests warning: {exc}")
        return []


def list_user_devices(limit=500):
    """Lấy IP thiết bị và lưu trạng thái tải để Admin không hiểu nhầm dữ liệu rỗng."""
    require_db()
    list_user_devices.last_status = {
        "ok": False,
        "row_count": 0,
        "error": None,
        "source": "user_devices",
    }
    try:
        result = execute_query(
            db.table("user_devices")
            .select("user_id,ip_address,last_seen_at,created_at")
            .order("last_seen_at", desc=True).limit(max(1, int(limit))),
            f"list_user_devices:{limit}",
        )
        rows = result.data or []
        list_user_devices.last_status = {
            "ok": True,
            "row_count": len(rows),
            "error": None,
            "source": "user_devices",
        }
        return rows
    except Exception as exc:
        # Không làm sập trang Admin, nhưng phải đưa trạng thái lỗi ra giao diện.
        message = str(exc).strip() or exc.__class__.__name__
        list_user_devices.last_status = {
            "ok": False,
            "row_count": 0,
            "error": message[:240],
            "source": "register_ip_only",
        }
        print(f"list_user_devices warning: {exc}")
        return []


def decorate_admin_users(users):
    """Bổ sung toàn bộ IP và trạng thái trùng IP cho danh sách Admin.

    Tài khoản tin cậy/cấu hình tắt cảnh báo chỉ ảnh hưởng màu cảnh báo, không được
    loại khỏi dữ liệu đối chiếu. Nhờ vậy bộ lọc "Chỉ hiện IP trùng" luôn thấy đủ.
    """
    rows = [dict(user) for user in users]
    for row in rows:
        row["admin_permissions"] = _admin_permissions(row)

    devices = list_user_devices()
    config = get_duplicate_ip_warning_config()
    warnings_enabled = bool(config.get("enabled", True))
    known_ips_by_user = {str(user.get("id")): set() for user in rows}
    latest_ip_by_user = {}
    row_by_id = {str(user.get("id")): user for user in rows}

    # Luôn thu thập IP đăng ký, kể cả tài khoản được tin cậy/được Admin tạo.
    for user in rows:
        user_id = str(user.get("id") or "")
        register_ip = str(user.get("register_ip") or "").strip()
        if user_id and register_ip and not register_ip.upper().startswith(("ADMIN_TEST", "ADMIN_CREATED")):
            known_ips_by_user.setdefault(user_id, set()).add(register_ip)

    # Luôn thu thập IP thiết bị. Dòng đầu tiên là IP mới nhất do truy vấn đã sort desc.
    for device in devices:
        user_id = str(device.get("user_id") or "")
        ip = str(device.get("ip_address") or "").strip()
        if not user_id or not ip or user_id not in row_by_id:
            continue
        known_ips_by_user.setdefault(user_id, set()).add(ip)
        latest_ip_by_user.setdefault(user_id, ip)

    ip_owners = {}
    for user_id, ip_values in known_ips_by_user.items():
        for ip in ip_values:
            ip_owners.setdefault(ip, set()).add(user_id)

    username_by_id = {str(user.get("id")): user.get("username", "-") for user in rows}
    for user in rows:
        user_id = str(user.get("id") or "")
        known_ips = sorted(known_ips_by_user.get(user_id, set()))
        duplicate_ips = [ip for ip in known_ips if len(ip_owners.get(ip, set())) > 1]
        duplicate_accounts = sorted({
            username_by_id.get(owner_id, "-")
            for ip in duplicate_ips
            for owner_id in ip_owners.get(ip, set())
            if owner_id != user_id
        })
        trusted = user_ignored_for_duplicate_ip(user, config)
        detected = bool(duplicate_accounts)

        user["latest_ip"] = latest_ip_by_user.get(user_id) or user.get("register_ip") or "-"
        user["known_ips"] = known_ips
        user["duplicate_ips"] = duplicate_ips
        user["duplicate_ip_count"] = max([len(ip_owners.get(ip, set())) for ip in duplicate_ips] or [0])
        user["duplicate_ip_accounts"] = duplicate_accounts
        user["duplicate_ip_detected"] = detected
        user["duplicate_ip_trusted"] = trusted
        user["duplicate_ip_warning_visible"] = detected and warnings_enabled and not trusted

    return rows


def build_duplicate_ip_groups(users):
    """Gom các IP đang được từ 2 tài khoản trở lên sử dụng để Admin dễ kiểm tra clone."""
    ip_users = {}

    for user in users:
        user_id = str(user.get("id") or "")
        if not user_id:
            continue
        for ip in user.get("known_ips") or []:
            normalized_ip = (ip or "").strip()
            if not normalized_ip:
                continue
            ip_users.setdefault(normalized_ip, {})[user_id] = user

    groups = []
    for ip, owners in ip_users.items():
        if len(owners) < 2:
            continue

        accounts = sorted(
            [
                {
                    "id": owner.get("id"),
                    "username": owner.get("username") or "-",
                    "display_name": owner.get("display_name") or owner.get("username") or "-",
                    "account_status": owner.get("account_status") or "approved",
                    "role": owner.get("role") or "player",
                    "admin_level": owner.get("admin_level") or "none",
                }
                for owner in owners.values()
            ],
            key=lambda item: item["username"].lower(),
        )
        groups.append({
            "ip": ip,
            "account_count": len(accounts),
            "accounts": accounts,
            "usernames": [item["username"] for item in accounts],
        })

    groups.sort(key=lambda item: (-item["account_count"], item["ip"]))
    return groups


def get_invite_code_record(code_value):
    code_value = normalize_invite_code(code_value)
    if not code_value:
        return None
    result = execute_query(
        db.table("registration_invite_codes")
        .select("*")
        .eq("code", code_value)
        .limit(1),
        "get_invite_code_record",
    )
    return result.data[0] if result.data else None


def list_registration_invite_codes(limit=100):
    result = execute_query(
        db.table("registration_invite_codes")
        .select("*")
        .order("created_at", desc=True)
        .limit(limit),
        "list_registration_invite_codes",
    )
    records = result.data or []
    users = {u["id"]: u for u in list_all_users()}
    for record in records:
        record["created_by_name"] = users.get(record.get("created_by"), {}).get("display_name", "-")
        record["used_by_name"] = users.get(record.get("used_by"), {}).get("display_name", "-")
    return records

