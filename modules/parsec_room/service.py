"""Nghiệp vụ Parsec ID hồ sơ và link tạm thời trong phòng."""
import re
from urllib.parse import urlsplit

EXPORTED_NAMES = ("build_room_parsec_context", "get_admin_discord_link", "validate_discord_link")

PARSEC_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{1,41}(?:#[0-9]{1,20})?$")

DISCORD_LINK_SETTING_KEY = "admin_discord_link"


def validate_discord_link(value):
    value = str(value or "").strip()
    if not value:
        return None
    if len(value) > 500:
        raise ValueError("Link Discord quá dài.")
    try:
        parsed = urlsplit(value)
    except Exception as exc:
        raise ValueError("Link Discord không hợp lệ.") from exc
    if parsed.scheme.lower() != "https":
        raise ValueError("Link Discord bắt buộc dùng HTTPS.")
    host = (parsed.hostname or "").lower()
    valid = False
    if host == "discord.gg":
        valid = bool(parsed.path.strip("/"))
    elif host in {"discord.com", "www.discord.com", "discordapp.com", "www.discordapp.com"}:
        valid = parsed.path.startswith("/invite/") and bool(parsed.path[len("/invite/"):].strip("/"))
    if not valid:
        raise ValueError("Link Discord phải có dạng https://discord.gg/... hoặc https://discord.com/invite/...")
    if parsed.username or parsed.password or parsed.port or parsed.fragment:
        raise ValueError("Link Discord chứa thành phần không hợp lệ.")
    return value


def get_admin_discord_link(force_refresh=False):
    cache_key = "admin_discord_link"
    if not force_refresh:
        try:
            cached = ttl_cache_get(cache_key)
            if cached is not None:
                return str(cached or "") or None
        except Exception:
            pass
    value = None
    try:
        result = execute_query(
            db.table("system_settings").select("setting_value")
            .eq("setting_key", DISCORD_LINK_SETTING_KEY).limit(1),
            "get_admin_discord_link", attempts=2,
        )
        rows = getattr(result, "data", None) or []
        if rows:
            raw = rows[0].get("setting_value")
            if isinstance(raw, dict):
                raw = raw.get("url")
            value = validate_discord_link(raw)
    except Exception:
        value = None
    try:
        ttl_cache_set(cache_key, value or "", 45)
    except Exception:
        pass
    return value


def configure(context):
    globals().update(context)


def validate_parsec_id(value):
    value = " ".join(str(value or "").strip().split())
    if not value:
        return None
    if not PARSEC_ID_RE.fullmatch(value):
        raise ValueError("Parsec ID phải có dạng Tên#MãSố, ví dụ Salem6556#18473949; không được có khoảng trắng.")
    return value


def validate_parsec_link(value):
    value = str(value or "").strip()
    if not value:
        return None
    if len(value) > 500:
        raise ValueError("Link Parsec quá dài.")
    try:
        parsed = urlsplit(value)
    except Exception as exc:
        raise ValueError("Link Parsec không hợp lệ.") from exc
    if parsed.scheme.lower() != "https":
        raise ValueError("Link Parsec bắt buộc dùng HTTPS.")
    if (parsed.hostname or "").lower() != "parsec.gg":
        raise ValueError("Chỉ chấp nhận link chính thức thuộc domain parsec.gg.")
    if parsed.username or parsed.password or parsed.port:
        raise ValueError("Link Parsec chứa thành phần không hợp lệ.")
    if not parsed.path.startswith("/g/") or len([p for p in parsed.path.split("/") if p]) < 3:
        raise ValueError("Link Parsec phải có dạng https://parsec.gg/g/...")
    if parsed.fragment:
        raise ValueError("Link Parsec không được chứa phần #fragment.")
    return value


def _safe_user(user_id):
    if not user_id:
        return {}
    try:
        return dict(get_user(user_id) or {})
    except Exception:
        return {}


def build_room_parsec_context(room, viewer):
    viewer_id = str((viewer or {}).get("id") or "")
    host_id = str(room.get("host_user_id") or "")
    guest_id = str(room.get("guest_user_id") or "")
    is_member = viewer_id in {host_id, guest_id}
    if not is_member:
        return {"visible": False}
    host = _safe_user(host_id)
    guest = _safe_user(guest_id)
    return {
        "visible": True,
        "viewer_is_host": viewer_id == host_id,
        "host_parsec_id": host.get("parsec_id"),
        "guest_parsec_id": guest.get("parsec_id"),
        "room_link": room.get("parsec_link"),
        "discord_link": get_admin_discord_link(),
    }
