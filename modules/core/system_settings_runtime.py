"""Runtime system settings/configuration helpers for PES Arena.

Owns feature toggles, Quick Match UI config, repeat-opponent RP factors and
maintenance schedule parsing/loading. Extracted from app.py in V1.3.61.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone, timedelta

_ctx = {}

ADMIN_PERMISSION_GROUPS = {
    "users": ["users_view", "users_approve", "users_edit", "users_delete", "password_reset", "accounts_import"],
    "matches": ["matches_view", "matches_confirm", "matches_cancel", "matches_delete"],
    "operations": ["rooms_manage", "invites_manage", "announcements_manage"],
    "system": ["system_features_manage", "chat_manage", "friendly_manage", "registration_codes_manage", "admin_logs_view"],
    "rp": ["rp_view", "rp_simulate", "rp_backup_restore", "daily_rank_limits_manage"],
    "economy": ["zcoin_view", "zcoin_manage"],
    "permissions": ["permissions_manage"],
}
ADMIN_PERMISSION_LABELS = {
    "users_view":"Xem người dùng", "users_approve":"Duyệt tài khoản", "users_edit":"Sửa tài khoản",
    "users_delete":"Xóa tài khoản", "password_reset":"Xử lý quên mật khẩu", "accounts_import":"Import CSV",
    "matches_view":"Xem trận", "matches_confirm":"Xác nhận trận", "matches_cancel":"Hủy trận", "matches_delete":"Xóa trận",
    "rooms_manage":"Quản lý phòng", "invites_manage":"Quản lý lời mời",
    "announcements_manage":"Quản lý thông báo", "system_features_manage":"Bật/tắt tính năng hệ thống", "chat_manage":"Quản lý Chat", "friendly_manage":"Quản lý Giao hữu",
    "registration_codes_manage":"Quản lý mã đăng ký", "admin_logs_view":"Xem nhật ký Admin",
    "rp_view":"Xem công thức RP", "rp_simulate":"Tính thử RP",
    "rp_backup_restore":"Backup/Khôi phục RP", "daily_rank_limits_manage":"Bật/tắt giới hạn Rank ngày",
    "zcoin_view":"Xem ví và giao dịch Zcoin", "zcoin_manage":"Cộng/trừ Zcoin",
    "permissions_manage":"Cấp/thu hồi quyền Admin",
}
LEGACY_ADMIN_PERMISSION_FIELDS = {
    "create_test_account": "admin_can_create_test_account",
    "import_accounts_csv": "admin_can_import_accounts_csv",
    "accounts_import": "admin_can_import_accounts_csv",
}
SYSTEM_FEATURE_DEFAULTS = {
    "dashboard_enabled": False,
    "public_ranking_enabled": True,
    "friendly_enabled": True, "rank_standard_enabled": True, "friendly_random3_enabled": True,
    "lobby_chat_enabled": True, "room_chat_enabled": True,
    "registration_codes_enabled": True, "announcements_enabled": True, "quick_match_enabled": True,
    "repeat_opponent_rp_enabled": True,
    "rank_tactical_bo3_enabled": True, "rank_bo3_enabled": True,
    "rank_ban_pick_bo3_enabled": True, "rank_home_away_enabled": True,
}
QUICK_MATCH_SETTING_KEY = "quick_match_config"
QUICK_MATCH_COLOR_DEFAULT = "green"
QUICK_MATCH_COLOR_VALUES = {"blue", "green"}

BUTTON_THEME_SETTING_KEY = "gaming_neon_button_theme"
BUTTON_COLOR_VALUES = {"blue", "green", "gold", "red", "gray", "purple"}
BUTTON_THEME_DEFAULTS = {
    "invite": "gold",
    "quick": "green",
    "success": "green",
    "danger": "red",
    "primary": "gold",
    "secondary": "gray",
    "default": "blue",
    "special": "purple",
}
REPEAT_OPPONENT_CONFIG_SETTING_KEY = "repeat_opponent_rp_config"
REPEAT_OPPONENT_WINNER_FACTOR_DEFAULTS = [100, 60, 30, 0]
REPEAT_OPPONENT_LOSER_FACTOR_DEFAULTS = [100, 70, 40, 10]
MAINTENANCE_SETTING_KEY = "server_maintenance_config"
VN_TIMEZONE = timezone(timedelta(hours=7))
_maintenance_cache = {"value": None, "expires_at": 0.0}

EXPORTED_NAMES = (
    "ADMIN_PERMISSION_GROUPS", "ADMIN_PERMISSION_LABELS", "LEGACY_ADMIN_PERMISSION_FIELDS",
    "SYSTEM_FEATURE_DEFAULTS", "QUICK_MATCH_SETTING_KEY", "QUICK_MATCH_COLOR_DEFAULT",
    "QUICK_MATCH_COLOR_VALUES", "BUTTON_THEME_SETTING_KEY", "BUTTON_COLOR_VALUES", "BUTTON_THEME_DEFAULTS", "REPEAT_OPPONENT_CONFIG_SETTING_KEY",
    "REPEAT_OPPONENT_WINNER_FACTOR_DEFAULTS", "REPEAT_OPPONENT_LOSER_FACTOR_DEFAULTS", "MAINTENANCE_SETTING_KEY", "VN_TIMEZONE",
    "_admin_permissions", "has_admin_permission", "get_system_features", "system_feature_enabled", "get_quick_match_config", "get_button_theme_config",
    "get_repeat_opponent_rp_config", "_maintenance_default_config", "_parse_maintenance_time",
    "_normalize_maintenance_input", "get_maintenance_config", "get_maintenance_status",
)

# `_admin_permissions` is intentionally exported because extracted Admin/User modules
# receive dependencies through app.py globals() and call this helper directly.


def configure(context):
    global _ctx
    _ctx = context


def _get(name):
    return _ctx[name]


def _admin_permissions(user):
    raw = (user or {}).get("admin_permissions") or {}
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except Exception:
            raw = {}
    return raw if isinstance(raw, dict) else {}


def has_admin_permission(user, permission_code: str) -> bool:
    if _get("is_owner_user")(user):
        return True
    if not _get("is_admin_user")(user):
        return False
    permissions = _admin_permissions(user)
    if permission_code in permissions:
        return permissions.get(permission_code) is True
    legacy = LEGACY_ADMIN_PERMISSION_FIELDS.get(permission_code)
    return bool(legacy and user.get(legacy) is True)


def get_system_features():
    cache_get, cache_set = _get("cache_get"), _get("cache_set")
    ttl_cache_get, ttl_cache_set = _get("ttl_cache_get"), _get("ttl_cache_set")
    request_key = "_system_features_cached"
    cached = cache_get(request_key)
    if isinstance(cached, dict):
        return dict(cached)
    cached = ttl_cache_get("system_features")
    if isinstance(cached, dict):
        return cache_set(request_key, dict(cached))

    features = dict(SYSTEM_FEATURE_DEFAULTS)
    try:
        result = _get("execute_query")(
            _get("db").table("system_settings").select("setting_value").eq("setting_key", "admin_system_features").limit(1),
            "get_system_features", attempts=2,
        )
        raw = ((result.data or [{}])[0]).get("setting_value")
        if isinstance(raw, str):
            raw = json.loads(raw)
        if isinstance(raw, dict):
            features.update({key: bool(value) for key, value in raw.items() if key in features})
    except Exception as exc:
        _get("log_system_event")("system_features_load_failed", level=30, error_type=type(exc).__name__, error=str(exc))
    ttl_cache_set("system_features", dict(features), 45)
    return cache_set(request_key, dict(features))


def system_feature_enabled(key: str) -> bool:
    return bool(get_system_features().get(key, SYSTEM_FEATURE_DEFAULTS.get(key, False)))


def get_quick_match_config():
    cache_get, cache_set = _get("cache_get"), _get("cache_set")
    ttl_cache_get, ttl_cache_set = _get("ttl_cache_get"), _get("ttl_cache_set")
    request_key = "_quick_match_config_cached"
    cached = cache_get(request_key)
    if isinstance(cached, dict):
        return dict(cached)
    cached = ttl_cache_get("quick_match_config")
    if isinstance(cached, dict):
        return cache_set(request_key, dict(cached))

    config = {"color": QUICK_MATCH_COLOR_DEFAULT}
    try:
        result = _get("execute_query")(
            _get("db").table("system_settings").select("setting_value").eq("setting_key", QUICK_MATCH_SETTING_KEY).limit(1),
            "get_quick_match_config", attempts=2,
        )
        raw = ((result.data or [{}])[0]).get("setting_value")
        if isinstance(raw, str):
            raw = json.loads(raw)
        if isinstance(raw, dict) and raw.get("color") in QUICK_MATCH_COLOR_VALUES:
            config["color"] = raw["color"]
    except Exception as exc:
        _get("log_system_event")("quick_match_config_load_failed", level=30, error_type=type(exc).__name__, error=str(exc))
    ttl_cache_set("quick_match_config", dict(config), 60)
    return cache_set(request_key, dict(config))


def get_button_theme_config():
    """Return the Gaming Neon semantic color map used by player-side action buttons.

    The setting is stored as one JSON object in system_settings so Admin can change
    colors without touching CSS. Unknown/missing values safely fall back to defaults.
    """
    cache_get, cache_set = _get("cache_get"), _get("cache_set")
    ttl_cache_get, ttl_cache_set = _get("ttl_cache_get"), _get("ttl_cache_set")
    request_key = "_button_theme_config_cached"
    cached = cache_get(request_key)
    if isinstance(cached, dict):
        return dict(cached)
    cached = ttl_cache_get("button_theme_config")
    if isinstance(cached, dict):
        return cache_set(request_key, dict(cached))

    config = dict(BUTTON_THEME_DEFAULTS)
    try:
        result = _get("execute_query")(
            _get("db").table("system_settings").select("setting_value").eq("setting_key", BUTTON_THEME_SETTING_KEY).limit(1),
            "get_button_theme_config", attempts=2,
        )
        raw = ((result.data or [{}])[0]).get("setting_value")
        if isinstance(raw, str):
            raw = json.loads(raw)
        if isinstance(raw, dict):
            for key in config:
                value = str(raw.get(key) or "").strip().lower()
                if value in BUTTON_COLOR_VALUES:
                    config[key] = value
    except Exception as exc:
        _get("log_system_event")("button_theme_config_load_failed", level=30, error_type=type(exc).__name__, error=str(exc))
    ttl_cache_set("button_theme_config", dict(config), 60)
    return cache_set(request_key, dict(config))


def get_repeat_opponent_rp_config():
    cache_get, cache_set = _get("cache_get"), _get("cache_set")
    ttl_cache_get, ttl_cache_set = _get("ttl_cache_get"), _get("ttl_cache_set")
    request_key = "_repeat_opponent_rp_config_cached"
    cached = cache_get(request_key)
    if isinstance(cached, dict):
        return {key: list(value) if isinstance(value, list) else value for key, value in cached.items()}
    cached = ttl_cache_get("repeat_opponent_rp_config")
    if isinstance(cached, dict):
        copied = {key: list(value) if isinstance(value, list) else value for key, value in cached.items()}
        return cache_set(request_key, copied)

    config = {
        "winner_factors": list(REPEAT_OPPONENT_WINNER_FACTOR_DEFAULTS),
        "loser_factors": list(REPEAT_OPPONENT_LOSER_FACTOR_DEFAULTS),
    }
    try:
        result = _get("execute_query")(
            _get("db").table("system_settings").select("setting_value").eq("setting_key", REPEAT_OPPONENT_CONFIG_SETTING_KEY).limit(1),
            "get_repeat_opponent_rp_config", attempts=2,
        )
        raw = ((result.data or [{}])[0]).get("setting_value")
        if isinstance(raw, str):
            raw = json.loads(raw)
        if isinstance(raw, dict):
            for key in ("winner_factors", "loser_factors"):
                values = raw.get(key)
                if isinstance(values, list) and len(values) == 4:
                    normalized = [max(0, min(100, int(value))) for value in values]
                    if all(normalized[index] >= normalized[index + 1] for index in range(3)):
                        config[key] = normalized
    except Exception as exc:
        _get("log_system_event")("repeat_opponent_config_load_failed", level=30, error_type=type(exc).__name__, error=str(exc))
    ttl_cache_set("repeat_opponent_rp_config", {
        "winner_factors": list(config["winner_factors"]),
        "loser_factors": list(config["loser_factors"]),
    }, 60)
    return cache_set(request_key, config)


def _maintenance_default_config():
    return {
        "manual_closed": False, "close_at": "", "open_at": "",
        "message": "Hệ thống đang được bảo trì. Vui lòng quay lại sau.", "updated_at": "",
    }


def _parse_maintenance_time(value):
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=VN_TIMEZONE)
        return parsed.astimezone(VN_TIMEZONE)
    except (TypeError, ValueError):
        return None


def _normalize_maintenance_input(value):
    parsed = _parse_maintenance_time(value)
    return parsed.isoformat(timespec="minutes") if parsed else ""


def get_maintenance_config(force=False):
    now_ts = time.time()
    if not force and _maintenance_cache.get("value") is not None and now_ts < _maintenance_cache.get("expires_at", 0):
        return dict(_maintenance_cache["value"])
    config = _maintenance_default_config()
    try:
        result = _get("execute_query")(
            _get("db").table("system_settings").select("setting_value").eq("setting_key", MAINTENANCE_SETTING_KEY).limit(1),
            "get_server_maintenance_config", attempts=2,
        )
        raw = ((result.data or [{}])[0]).get("setting_value")
        if isinstance(raw, str):
            raw = json.loads(raw)
        if isinstance(raw, dict):
            for key in config:
                if key in raw:
                    config[key] = raw[key]
    except Exception as exc:
        _get("log_system_event")("maintenance_config_load_failed", level=30, error_type=type(exc).__name__, error=str(exc))
    config["manual_closed"] = bool(config.get("manual_closed"))
    _maintenance_cache["value"] = dict(config)
    _maintenance_cache["expires_at"] = now_ts + 15
    return config


def get_maintenance_status(config=None):
    config = dict(config or get_maintenance_config())
    now = datetime.now(VN_TIMEZONE)
    close_at = _parse_maintenance_time(config.get("close_at"))
    open_at = _parse_maintenance_time(config.get("open_at"))
    closed = bool(config.get("manual_closed"))
    transitions = []
    if close_at:
        transitions.append((close_at, True, "close"))
    if open_at:
        transitions.append((open_at, False, "open"))
    for when, state, _kind in sorted(transitions, key=lambda item: item[0]):
        if now >= when:
            closed = state
    future = [(when, state, kind) for when, state, kind in transitions if when > now]
    next_transition = min(future, key=lambda item: item[0]) if future else None
    countdown = None
    if next_transition:
        seconds = max(0, int((next_transition[0] - now).total_seconds()))
        if seconds <= 30 * 60:
            countdown = {
                "kind": next_transition[2], "target_iso": next_transition[0].isoformat(), "seconds": seconds,
                "label": "Máy chủ sẽ đóng để bảo trì" if next_transition[2] == "close" else "Máy chủ sẽ mở trở lại",
            }
    return {
        "closed": closed,
        "message": str(config.get("message") or _maintenance_default_config()["message"]),
        "close_at": close_at.isoformat() if close_at else "",
        "open_at": open_at.isoformat() if open_at else "",
        "close_at_input": close_at.strftime("%Y-%m-%dT%H:%M") if close_at else "",
        "open_at_input": open_at.strftime("%Y-%m-%dT%H:%M") if open_at else "",
        "countdown": countdown,
    }
