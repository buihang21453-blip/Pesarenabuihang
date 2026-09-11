import csv
import json
import hashlib
import io
import os
import random
import secrets
import string
import time
import uuid
import threading
import zipfile
from datetime import datetime, timezone, timedelta
from functools import wraps
from pathlib import Path

from dotenv import load_dotenv
from PIL import Image, ImageOps, UnidentifiedImageError
from flask import (
    Flask,
    jsonify,
    flash,
    g,
    has_request_context,
    make_response,
    send_file,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from supabase import create_client

from modules.quick_match.service import build_candidate_sort_key, quick_match_priority_group
from modules.cache_utils import (
    cache_get, cache_set, cache_delete, ttl_cache_get, ttl_cache_set, ttl_cache_delete,
)
from modules.datetime_utils import (
    now_dt, now_iso, future_iso, aware_utc, seconds_until, parse_dt, format_vn_datetime,
)
from modules.rp_formula import (
    BASE_WIN_POINTS, PLACEMENT_MATCHES, PLACEMENT_WIN_MULTIPLIER,
    MIN_RANK_ADJUSTED_WIN_POINTS, MAX_RANK_ADJUSTED_WIN_POINTS,
    MAX_POSITIVE_POINTS_PER_MATCH, WIN_STREAK_BONUSES, HOST_WIN_FACTOR,
    RP_FORMULA_VERSION, RP_RANDOM_SEED_NAMESPACE, formula_summary,
)
from modules.rp_engine import (
    calculate_deltas as calculate_ranked_deltas, validate_deltas as validate_ranked_deltas,
)
from modules.admin_match_service import parse_score, score_changed
from modules.admin_ranking_rebuild import build_replay_plan
from modules.system_feature_service import post_login_endpoint, dashboard_is_enabled
from modules.session_runtime_service import (
    IDLE_TIMEOUT_SECONDS, PROTECTED_ROOM_STATUSES, idle_decision, room_blocks_idle_logout, client_config as session_client_config,
)
from modules.static_asset_service import asset_url, asset_base_url, shop_asset_base_url, luckybox_asset_base_url
from modules.profile import equipment_service as profile_equipment_service
from modules.win_streaks import (
    WIN_STREAK_TITLES, WIN_STREAK_EVENT_PREFIX, get_win_streak_title,
    get_win_streak_badge, build_win_streak_event, encode_win_streak_room_note,
    parse_win_streak_room_note,
)


load_dotenv()

APP_NAME = "PES Arena – Bản Lĩnh Sân Cỏ"
APP_VERSION = "V1.5.60"
# UI release bundle: V1.3
DEFAULT_POINTS = 1000
DEVICE_COOKIE_NAME = "rankzone_device_id"
COOLDOWN_MINUTES = 3
ONLINE_TIMEOUT_SECONDS = 60
CHAT_COOLDOWN_SECONDS = 5
CHAT_MAX_LENGTH = 200

# V1.4.2 — Chat Phòng tạm thời trong RAM, không ghi vào Supabase/database.
# Dữ liệu tự mất khi tiến trình khởi động lại và được dọn theo TTL.
ROOM_CHAT_MEMORY_TTL_SECONDS = 2 * 60 * 60
ROOM_CHAT_MEMORY_LIMIT = 50
_room_chat_memory = {}
_room_chat_last_sent = {}
_room_chat_memory_lock = threading.Lock()
DISPUTE_EVIDENCE_BUCKET = "dispute-evidence"
DISPUTE_EVIDENCE_MAX_BYTES = 4 * 1024 * 1024
DISPUTE_EVIDENCE_MAX_SIDE = 1600
DISPUTE_EVIDENCE_ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}

ACHIEVEMENT_DEFINITIONS = [
    {"code": "first_match", "icon": "⚽", "name": "Bước chân đầu tiên", "description": "Hoàn thành trận đấu đầu tiên.", "metric": "total_matches", "threshold": 1, "priority": 10},
    {"code": "warrior_20", "icon": "🛡️", "name": "Chiến binh sân cỏ", "description": "Hoàn thành 20 trận đấu.", "metric": "total_matches", "threshold": 20, "priority": 20},
    {"code": "winner_10", "icon": "🏅", "name": "Kẻ chinh phục", "description": "Giành 10 chiến thắng.", "metric": "wins", "threshold": 10, "priority": 30},
    {"code": "goals_50", "icon": "🎯", "name": "Sát thủ vòng cấm", "description": "Ghi tổng cộng 50 bàn thắng.", "metric": "goals_for", "threshold": 50, "priority": 40},
    {"code": "hot_streak_5", "icon": "🔥", "name": "Chuỗi lửa", "description": "Thắng liên tiếp 5 trận.", "metric": "streak", "threshold": 5, "priority": 50},
    {"code": "top_one", "icon": "👑", "name": "Đỉnh bảng", "description": "Từng giữ vị trí số 1 BXH sau ít nhất 5 trận.", "metric": "position", "threshold": 1, "priority": 60},
]
ACHIEVEMENT_BY_CODE = {item["code"]: item for item in ACHIEVEMENT_DEFINITIONS}
ADMIN_LEVELS = {"owner", "admin"}
ACCOUNT_STATUSES = {"pending", "approved", "rejected", "banned", "deleted"}
REMATCH_HOST_READY_NOTE = "__rematch_host_ready__"
REMATCH_GUEST_READY_NOTE = "__rematch_guest_ready__"
REMATCH_HOST_DECLINED_NOTE = "__rematch_host_declined__"
REMATCH_GUEST_DECLINED_NOTE = "__rematch_guest_declined__"
REMATCH_EXPIRED_NOTE = "__rematch_expired__"

DISPUTE_REASON_OPTIONS = {
    "wrong_score": "Sai tỷ số",
    "wrong_winner": "Sai người thắng",
    "interrupted": "Trận bị gián đoạn",
    "unilateral_entry": "Kết quả nhập không đúng thỏa thuận",
    "other": "Lý do khác",
    "timeout": "Hết thời gian xác nhận",
    "legacy": "Tranh chấp từ phiên bản cũ",
}
DISPUTE_PENDING_STATUSES = {"pending", "processing"}

# Khóa toàn cục ngắn hạn dùng khi Admin phát lại lịch sử BXH.
# Lưu trong Supabase để có hiệu lực trên nhiều Serverless Function/instance.
RANKING_REBUILD_LOCK_KEY = "admin_ranking_rebuild_lock"
RANKING_REBUILD_LOCK_SECONDS = 5 * 60

INVITE_TIMEOUT_SECONDS = 60
ROOM_READY_TIMEOUT_SECONDS = 30 * 60
RESULT_CONFIRM_TIMEOUT_SECONDS = 60
REMATCH_TIMEOUT_SECONDS = 60
ROOM_EMPTY_INACTIVITY_TIMEOUT_SECONDS = 30 * 60
ROOM_MATCH_INACTIVITY_TIMEOUT_SECONDS = 4 * 60 * 60
ROOM_ABANDON_PENALTY = 20
ROOM_TIMEOUT_PENALTY_RANGE = (22, 25)

RANK_K_FACTOR = 32
RANK_SCALE = 400
TEAM_OVR_BASE = 79
TEAM_OVR_WEIGHT = 20

# Cấu hình công thức: modules/rp_formula.py; logic tính: modules/rp_engine.py

# Rank/Tier difficulty system (V1.8.1)
SMART_RANDOM_CORRECT_WEIGHT = 0.70
SMART_RANDOM_STRONGER_WEIGHT = 0.15
SMART_RANDOM_WEAKER_WEIGHT = 0.15

# Danh hiệu chuỗi thắng đã tách sang modules/win_streaks.py



DEFAULT_RANKS = [
    {"min": 0, "max": 499, "name": "Gà", "short_name": "Gà", "abbr": "G", "code": "CHICKEN", "icon": "🐔", "slug": "ga"},
    {"min": 500, "max": 699, "name": "Non", "short_name": "Non", "abbr": "N", "code": "NOVICE", "icon": "🌱", "slug": "non"},
    {"min": 700, "max": 899, "name": "Báo Thủ", "short_name": "Báo", "abbr": "BT", "code": "LIABILITY", "icon": "⚠️", "slug": "bao-thu"},
    {"min": 900, "max": 1099, "name": "Mới Tập Chơi", "short_name": "Mới Chơi", "abbr": "MTC", "code": "BEGINNER", "icon": "🎮", "slug": "moi-tap-choi"},
    {"min": 1100, "max": 1399, "name": "Bán Chuyên", "short_name": "B.Chuyên", "abbr": "BC", "code": "SEMI_PRO", "icon": "⚔️", "slug": "ban-chuyen"},
    {"min": 1400, "max": 1699, "name": "Chuyên Nghiệp", "short_name": "C.Nghiệp", "abbr": "CN", "code": "PROFESSIONAL", "icon": "🎯", "slug": "chuyen-nghiep"},
    {"min": 1700, "max": 1999, "name": "Đẳng Cấp", "short_name": "Đ.Cấp", "abbr": "ĐC", "code": "CLASS", "icon": "💎", "slug": "dang-cap"},
    {"min": 2000, "max": 2349, "name": "Siêu Sao", "short_name": "S.Sao", "abbr": "SS", "code": "SUPERSTAR", "icon": "🌟", "slug": "sieu-sao"},
    {"min": 2350, "max": 2699, "name": "Huyền Thoại", "short_name": "H.Thoại", "abbr": "HT", "code": "LEGEND", "icon": "🏆", "slug": "huyen-thoai"},
    {"min": 2700, "max": None, "name": "GOAT", "short_name": "GOAT", "abbr": "GOAT", "code": "GOAT", "icon": "👑", "slug": "goat"},
]

MATCH_STATUS_LABELS = {
    "confirmed": "Đã xác nhận",
    "cancelled": "Đã hủy",
    "disputed": "Đang tranh chấp",
    "playing": "Đang thi đấu",
    "waiting_confirm": "Chờ xác nhận",
    "waiting_ready": "Chờ Chủ Phòng Quay",
    "waiting_result_confirm": "Chờ xác nhận kết quả",
}

ACTIVITY_PRIORITY = {
    "ready": 0,
    "in_room": 1,
    "waiting_confirm": 2,
    "playing": 3,
}


APP_ENV = (os.getenv("APP_ENV") or os.getenv("VERCEL_ENV") or "production").strip().lower()

# Production/Preview bắt buộc phải có secret riêng trong biến môi trường.
# Chỉ môi trường test/development mới được tạo secret tạm thời cho phiên chạy cục bộ.
_flask_secret_key = (os.getenv("FLASK_SECRET_KEY") or os.getenv("SECRET_KEY") or "").strip()
if not _flask_secret_key:
    if APP_ENV in {"test", "testing", "development"}:
        _flask_secret_key = secrets.token_hex(32)
    else:
        raise RuntimeError(
            "Thiếu FLASK_SECRET_KEY. Hãy khai báo secret dài, ngẫu nhiên trong biến môi trường Vercel trước khi chạy app."
        )

app = Flask(__name__)
app.secret_key = _flask_secret_key
app.permanent_session_lifetime = timedelta(days=30)
del _flask_secret_key

_STATIC_FINGERPRINT_CACHE = {}

def static_asset(filename):
    """Return a static URL fingerprinted from the file content.

    CSS/JS cache busting no longer depends on manually bumping APP_VERSION.
    A changed file gets a new URL; an unchanged file keeps the same URL.
    """
    clean_name = str(filename or "").lstrip("/")
    file_path = Path(app.static_folder) / clean_name
    try:
        stat = file_path.stat()
        cache_key = (clean_name, stat.st_mtime_ns, stat.st_size)
        fingerprint = _STATIC_FINGERPRINT_CACHE.get(cache_key)
        if fingerprint is None:
            fingerprint = hashlib.sha256(file_path.read_bytes()).hexdigest()[:12]
            _STATIC_FINGERPRINT_CACHE.clear()
            _STATIC_FINGERPRINT_CACHE[cache_key] = fingerprint
    except OSError:
        fingerprint = APP_VERSION
    return f"{url_for('static', filename=clean_name)}?v={fingerprint}"

app.jinja_env.globals["asset_url"] = asset_url
app.jinja_env.globals["static_asset"] = static_asset
app.jinja_env.globals["asset_base_url"] = asset_base_url
app.jinja_env.globals["shop_asset_base_url"] = shop_asset_base_url
app.jinja_env.globals["luckybox_asset_base_url"] = luckybox_asset_base_url

PES_ARENA_TEST_MODE = (os.getenv("PES_ARENA_TEST_MODE") or "false").strip().lower() in {"1", "true", "yes", "on"}
ALLOW_SIMPLE_TEST_PASSWORDS = (os.getenv("ALLOW_SIMPLE_TEST_PASSWORDS") or "false").strip().lower() in {"1", "true", "yes", "on"}
DATABASE_SAFETY_TOKEN = (os.getenv("DATABASE_SAFETY_TOKEN") or "").strip()

def is_test_mode():
    return APP_ENV in {"test", "testing", "development", "preview"} and PES_ARENA_TEST_MODE and DATABASE_SAFETY_TOKEN == "PES_ARENA_TEST_DATABASE"


def simple_test_passwords_enabled():
    """Only allow one-character passwords in an explicitly isolated test environment."""
    return is_test_mode() and ALLOW_SIMPLE_TEST_PASSWORDS


def minimum_password_length():
    return 1 if simple_test_passwords_enabled() else 6


def validate_new_password(password: str):
    minimum = minimum_password_length()
    if len(password or "") < minimum:
        return False, f"Mật khẩu mới phải có ít nhất {minimum} ký tự."
    return True, ""

supabase_url = (os.getenv("SUPABASE_URL") or "").strip().rstrip("/")
supabase_key = (
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    or os.getenv("SUPABASE_KEY")
    or ""
).strip()

db = create_client(supabase_url, supabase_key) if supabase_url and supabase_key else None


# Cache đã tách sang modules/cache_utils.py

def execute_query(query, label="Supabase", attempts=4, delay=0.25):
    """Retry short-lived Vercel/Supabase network failures before returning 500."""
    last_error = None

    for attempt in range(max(1, attempts)):
        try:
            return query.execute()
        except Exception as exc:
            last_error = exc
            message = f"{type(exc).__name__}: {exc}".lower()

            transient = any(token in message for token in (
                "connecterror",
                "connection",
                "server disconnected",
                "remoteprotocolerror",
                "timeout",
                "temporarily",
                "device or resource busy",
                "resource busy",
                "errno 16",
                "eagain",
            ))

            if not transient or attempt >= max(1, attempts) - 1:
                print(f"{label} failed after {attempt + 1} attempt(s): {exc}")
                raise

            # Backoff ngắn: 0.25s, 0.5s, 0.75s...
            time.sleep(delay * (attempt + 1))

    raise last_error



_admin_checked = False


# =========================
# Basic helpers
# =========================
# Tiện ích thời gian đã tách sang modules/datetime_utils.py

def _normalize_storage_public_url(value):
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return value.get("publicUrl") or value.get("public_url") or value.get("signedURL") or value.get("signed_url")
    return str(value or "")


def prepare_dispute_evidence_bytes(file_storage):
    if not file_storage or not getattr(file_storage, "filename", ""):
        return None

    raw = file_storage.read(DISPUTE_EVIDENCE_MAX_BYTES + 1)
    if len(raw) > DISPUTE_EVIDENCE_MAX_BYTES:
        raise ValueError("Ảnh bằng chứng không được vượt quá 4 MB.")
    if not raw:
        raise ValueError("File ảnh bằng chứng đang trống.")

    try:
        with Image.open(io.BytesIO(raw)) as probe:
            image_format = (probe.format or "").upper()
            width, height = probe.size
            probe.verify()
        if image_format not in DISPUTE_EVIDENCE_ALLOWED_FORMATS:
            raise ValueError("Bằng chứng chỉ chấp nhận ảnh JPG, PNG hoặc WEBP.")
        if width < 100 or height < 100:
            raise ValueError("Ảnh bằng chứng quá nhỏ. Vui lòng chọn ảnh từ 100×100 pixel trở lên.")
        if width * height > 30_000_000:
            raise ValueError("Ảnh bằng chứng có độ phân giải quá lớn.")

        with Image.open(io.BytesIO(raw)) as source:
            source = ImageOps.exif_transpose(source).convert("RGB")
            source.thumbnail(
                (DISPUTE_EVIDENCE_MAX_SIDE, DISPUTE_EVIDENCE_MAX_SIDE),
                Image.Resampling.LANCZOS,
            )
            output = io.BytesIO()
            source.save(output, format="WEBP", quality=86, method=6)
            return output.getvalue()
    except ValueError:
        raise
    except (UnidentifiedImageError, OSError, SyntaxError):
        raise ValueError("File bằng chứng không phải ảnh hợp lệ hoặc đã bị lỗi.")


def upload_dispute_evidence(match_id, user_id, evidence_bytes):
    require_db()
    object_path = f"{match_id}/{user_id}/{uuid.uuid4().hex}.webp"
    bucket = db.storage.from_(DISPUTE_EVIDENCE_BUCKET)
    bucket.upload(
        object_path,
        evidence_bytes,
        {
            "content-type": "image/webp",
            "cache-control": "3600",
            "upsert": "false",
        },
    )
    return object_path


def remove_dispute_evidence_object(object_path):
    if not object_path or db is None:
        return
    try:
        db.storage.from_(DISPUTE_EVIDENCE_BUCKET).remove([object_path])
    except Exception as exc:
        print(f"remove_dispute_evidence_object warning: {exc}")


def get_dispute_evidence_signed_url(object_path, expires_in=3600):
    if not object_path or db is None:
        return None
    try:
        response = db.storage.from_(DISPUTE_EVIDENCE_BUCKET).create_signed_url(
            object_path,
            max(60, int(expires_in)),
        )
        return _normalize_storage_public_url(response)
    except Exception as exc:
        print(f"get_dispute_evidence_signed_url warning: {exc}")
        return None


def achievement_progress(player, definition, position=None):
    metric = definition.get("metric")
    threshold = max(1, int(definition.get("threshold", 1) or 1))
    if metric == "position":
        current = 1 if position == 1 and calculated_total_matches(player) >= 5 else 0
    else:
        current = max(0, int(player.get(metric, 0) or 0))
    return current, threshold, min(100, round((current / threshold) * 100))


def eligible_achievement_codes(player, position=None):
    eligible = []
    for definition in ACHIEVEMENT_DEFINITIONS:
        current, threshold, _ = achievement_progress(player, definition, position)
        if current >= threshold:
            eligible.append(definition["code"])
    return eligible


def list_user_achievement_map():
    cached = cache_get("_rz_user_achievement_map")
    if cached is not None:
        return cached
    shared = ttl_cache_get("achievement_map")
    if shared is not None:
        return cache_set("_rz_user_achievement_map", shared)
    mapped = {}
    try:
        result = execute_query(
            db.table("user_achievements").select("user_id,achievement_code,unlocked_at"),
            "list_user_achievements",
            attempts=2,
        )
        for row in result.data or []:
            mapped.setdefault(str(row.get("user_id")), {})[row.get("achievement_code")] = row
    except Exception as exc:
        print(f"list_user_achievement_map warning: {exc}")
    ttl_cache_set("achievement_map", mapped, 30)
    return cache_set("_rz_user_achievement_map", mapped)


def decorate_player_achievements(player, position=None, achievement_map=None):
    if not player:
        return player
    achievement_map = achievement_map if achievement_map is not None else list_user_achievement_map()
    saved = achievement_map.get(str(player.get("id")), {})
    achievements = []
    for definition in ACHIEVEMENT_DEFINITIONS:
        current, threshold, progress = achievement_progress(player, definition, position)
        unlocked = definition["code"] in saved or current >= threshold
        item = dict(definition)
        item.update({
            "unlocked": unlocked,
            "unlocked_at": (saved.get(definition["code"]) or {}).get("unlocked_at"),
            "current": current,
            "progress": progress,
        })
        achievements.append(item)
    unlocked_items = sorted(
        [item for item in achievements if item.get("unlocked")],
        key=lambda item: int(item.get("priority", 0)),
        reverse=True,
    )
    player["achievements"] = achievements
    player["unlocked_achievements"] = unlocked_items
    player["achievement_count"] = len(unlocked_items)
    player["featured_achievement"] = unlocked_items[0] if unlocked_items else None
    return player


def sync_achievements_for_users(user_ids, notify=True):
    user_ids = [str(user_id) for user_id in dict.fromkeys(user_ids or []) if user_id]
    if not user_ids or db is None:
        return []
    try:
        result = execute_query(
            db.table("users").select("*").eq("role", "player"),
            "achievement_fresh_players",
            attempts=2,
        )
        players = [dict(item) for item in (result.data or [])]
        players.sort(key=_player_ranking_sort_key)
        positions = {str(item.get("id")): index for index, item in enumerate(players, 1)}
        by_id = {str(item.get("id")): item for item in players}

        existing_result = execute_query(
            db.table("user_achievements").select("user_id,achievement_code"),
            "achievement_existing",
            attempts=2,
        )
        existing = {(str(row.get("user_id")), row.get("achievement_code")) for row in (existing_result.data or [])}
        newly_unlocked = []
        for user_id in user_ids:
            player = by_id.get(user_id)
            if not player:
                continue
            for code in eligible_achievement_codes(player, positions.get(user_id)):
                if (user_id, code) in existing:
                    continue
                try:
                    execute_query(
                        db.table("user_achievements").insert({
                            "user_id": user_id,
                            "achievement_code": code,
                            "unlocked_at": now_iso(),
                        }),
                        "achievement_unlock",
                        attempts=2,
                    )
                    existing.add((user_id, code))
                    newly_unlocked.append((user_id, code))
                    if notify:
                        definition = ACHIEVEMENT_BY_CODE.get(code, {})
                        create_user_notification(
                            user_id,
                            f"{definition.get('icon', '🏅')} Huy hiệu mới",
                            f"Bạn đã mở khóa huy hiệu {definition.get('name', code)}.",
                            f"/profile/{user_id}",
                            "achievement",
                        )
                except Exception as exc:
                    if "duplicate" not in str(exc).lower():
                        print(f"achievement_unlock warning: {exc}")
        if has_request_context():
            setattr(g, "_rz_user_achievement_map", None)
        return newly_unlocked
    except Exception as exc:
        print(f"sync_achievements_for_users warning: {exc}")
        return []


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def is_admin_user(user) -> bool:
    return bool(
        user and (
            user.get("role") == "admin"
            or user.get("admin_level") in ADMIN_LEVELS
        )
    )


def is_owner_user(user) -> bool:
    return bool(
        user and (
            user.get("admin_level") == "owner"
        )
    )


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
    "matches_view":"Xem trận",
    "matches_confirm":"Xác nhận trận", "matches_cancel":"Hủy trận", "matches_delete":"Xóa trận",
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
    "friendly_enabled": True, "rank_standard_enabled": True, "friendly_random3_enabled": True, "lobby_chat_enabled": True, "room_chat_enabled": True,
    "registration_codes_enabled": True, "announcements_enabled": True, "quick_match_enabled": True,
    "repeat_opponent_rp_enabled": True,
}

def _admin_permissions(user):
    raw = (user or {}).get("admin_permissions") or {}
    if isinstance(raw, str):
        try: raw = json.loads(raw)
        except Exception: raw = {}
    return raw if isinstance(raw, dict) else {}


def has_admin_permission(user, permission_code: str) -> bool:
    if is_owner_user(user): return True
    if not is_admin_user(user): return False
    permissions = _admin_permissions(user)
    if permission_code in permissions: return permissions.get(permission_code) is True
    legacy = LEGACY_ADMIN_PERMISSION_FIELDS.get(permission_code)
    return bool(legacy and user.get(legacy) is True)


def get_system_features():
    request_key = "_system_features_cached"
    cached = cache_get(request_key)
    if isinstance(cached, dict):
        return dict(cached)

    cached = ttl_cache_get("system_features")
    if isinstance(cached, dict):
        return cache_set(request_key, dict(cached))

    features = dict(SYSTEM_FEATURE_DEFAULTS)
    try:
        result = execute_query(
            db.table("system_settings").select("setting_value")
            .eq("setting_key", "admin_system_features").limit(1),
            "get_system_features", attempts=2,
        )
        row = (result.data or [{}])[0]
        raw = row.get("setting_value")
        if isinstance(raw, str):
            raw = json.loads(raw)
        if isinstance(raw, dict):
            features.update({key: bool(value) for key, value in raw.items() if key in features})
    except Exception as exc:
        print(f"get_system_features warning: {exc}")

    # V1.4.122: Rank đơn là chế độ cốt lõi của Phòng đấu thường và luôn được mở.
    # Giữ nguyên giới hạn Rank/ngày và các chặn an toàn khi người chơi đang có
    # một trận C1 hoạt động; chỉ loại bỏ khả năng setting cũ vô tình khóa Rank.
    features["rank_standard_enabled"] = True

    ttl_cache_set("system_features", dict(features), 45)
    return cache_set(request_key, dict(features))


def system_feature_enabled(key: str) -> bool:
    return bool(get_system_features().get(key, SYSTEM_FEATURE_DEFAULTS.get(key, False)))


ROOM_STYLE_SETTING_KEY = "room_visual_style"
ROOM_STYLE_DEFAULT = "default"
ROOM_STYLE_OPTIONS = {
    "default": "Mặc định",
    "champions-night": "Hoàng Gia",
    "frozen-tech": "Cyber Neon",
    "ember-rivalry": "Sân Cỏ Năng Lượng",
    "royal-gold": "Khung Năng Lượng",
    "mono-tactical": "Thiết Giáp",
}


def get_room_visual_style():
    request_key = "_room_visual_style_cached"
    cached = cache_get(request_key)
    if cached in ROOM_STYLE_OPTIONS:
        return cached
    cached = ttl_cache_get("room_visual_style")
    if cached in ROOM_STYLE_OPTIONS:
        return cache_set(request_key, cached)
    style = ROOM_STYLE_DEFAULT
    try:
        result = execute_query(
            db.table("system_settings").select("setting_value")
            .eq("setting_key", ROOM_STYLE_SETTING_KEY).limit(1),
            "get_room_visual_style", attempts=2,
        )
        raw = ((result.data or [{}])[0]).get("setting_value")
        if isinstance(raw, dict):
            raw = raw.get("style")
        if raw in ROOM_STYLE_OPTIONS:
            style = raw
    except Exception as exc:
        print(f"get_room_visual_style warning: {exc}")
    ttl_cache_set("room_visual_style", style, 45)
    return cache_set(request_key, style)


ROOM_MODE_LOGO_SETTING_KEY = "room_mode_logo_config"
ROOM_MODE_LOGO_DEFAULTS = {
    "background_opacity": 0,
    "scale": 100,
    "dock_scale": 135,
}
ROOM_MODE_LOGO_LIMITS = {
    "background_opacity": (0, 100),
    "scale": (50, 200),
    "dock_scale": (70, 220),
}


def _coerce_room_mode_logo_value(value, *, default, lower, upper):
    try:
        if value is None or value == "":
            raise ValueError
        value = int(float(value))
    except Exception:
        value = default
    return max(lower, min(upper, value))


def normalize_room_mode_logo_config(raw):
    config = dict(ROOM_MODE_LOGO_DEFAULTS)
    try:
        if isinstance(raw, str):
            raw = json.loads(raw)
        if isinstance(raw, dict):
            raw_background_opacity = raw.get("background_opacity")
            if raw_background_opacity is None and "opacity" in raw:
                # Tương thích cấu hình V1.2.9.34: opacity cũ là độ rõ logo;
                # chuyển sang nền trong suốt mặc định thay vì làm mờ logo.
                raw_background_opacity = ROOM_MODE_LOGO_DEFAULTS["background_opacity"]
            config["background_opacity"] = _coerce_room_mode_logo_value(
                raw_background_opacity,
                default=ROOM_MODE_LOGO_DEFAULTS["background_opacity"],
                lower=ROOM_MODE_LOGO_LIMITS["background_opacity"][0],
                upper=ROOM_MODE_LOGO_LIMITS["background_opacity"][1],
            )
            config["scale"] = _coerce_room_mode_logo_value(
                raw.get("scale"),
                default=ROOM_MODE_LOGO_DEFAULTS["scale"],
                lower=ROOM_MODE_LOGO_LIMITS["scale"][0],
                upper=ROOM_MODE_LOGO_LIMITS["scale"][1],
            )
            config["dock_scale"] = _coerce_room_mode_logo_value(
                raw.get("dock_scale"),
                default=ROOM_MODE_LOGO_DEFAULTS["dock_scale"],
                lower=ROOM_MODE_LOGO_LIMITS["dock_scale"][0],
                upper=ROOM_MODE_LOGO_LIMITS["dock_scale"][1],
            )
    except Exception as exc:
        print(f"normalize_room_mode_logo_config warning: {exc}")
    return config



def get_room_mode_logo_config(force=False):
    request_key = "_room_mode_logo_config_cached"
    if not force:
        cached = cache_get(request_key)
        if isinstance(cached, dict):
            return dict(cached)
        cached = ttl_cache_get("room_mode_logo_config")
        if isinstance(cached, dict):
            return cache_set(request_key, dict(cached))

    config = dict(ROOM_MODE_LOGO_DEFAULTS)
    try:
        result = execute_query(
            db.table("system_settings").select("setting_value")
            .eq("setting_key", ROOM_MODE_LOGO_SETTING_KEY).limit(1),
            "get_room_mode_logo_config", attempts=2,
        )
        raw = ((result.data or [{}])[0]).get("setting_value")
        config = normalize_room_mode_logo_config(raw)
    except Exception as exc:
        print(f"get_room_mode_logo_config warning: {exc}")

    ttl_cache_set("room_mode_logo_config", dict(config), 45)
    return cache_set(request_key, dict(config))


ROOM_PANEL_LAYOUT_SETTING_KEY = "room_panel_layout_config"
ROOM_PANEL_LAYOUT_DEFAULTS = {
    "center_bars_visible": True,
    "panel_height": 600,
}
ROOM_PANEL_LAYOUT_LIMITS = {
    "panel_height": (480, 900),
}


def normalize_room_panel_layout_config(raw):
    config = dict(ROOM_PANEL_LAYOUT_DEFAULTS)
    try:
        if isinstance(raw, str):
            raw = json.loads(raw)
        if isinstance(raw, dict):
            visible = raw.get("center_bars_visible", ROOM_PANEL_LAYOUT_DEFAULTS["center_bars_visible"])
            if isinstance(visible, str):
                visible = visible.strip().lower() in {"1", "true", "yes", "on", "show", "visible"}
            config["center_bars_visible"] = bool(visible)
            config["panel_height"] = _coerce_room_mode_logo_value(
                raw.get("panel_height"),
                default=ROOM_PANEL_LAYOUT_DEFAULTS["panel_height"],
                lower=ROOM_PANEL_LAYOUT_LIMITS["panel_height"][0],
                upper=ROOM_PANEL_LAYOUT_LIMITS["panel_height"][1],
            )
    except Exception as exc:
        print(f"normalize_room_panel_layout_config warning: {exc}")
    return config


def get_room_panel_layout_config(force=False):
    request_key = "_room_panel_layout_config_cached"
    if not force:
        cached = cache_get(request_key)
        if isinstance(cached, dict):
            return dict(cached)
        cached = ttl_cache_get("room_panel_layout_config")
        if isinstance(cached, dict):
            return cache_set(request_key, dict(cached))

    config = dict(ROOM_PANEL_LAYOUT_DEFAULTS)
    try:
        result = execute_query(
            db.table("system_settings").select("setting_value")
            .eq("setting_key", ROOM_PANEL_LAYOUT_SETTING_KEY).limit(1),
            "get_room_panel_layout_config", attempts=2,
        )
        raw = ((result.data or [{}])[0]).get("setting_value")
        config = normalize_room_panel_layout_config(raw)
    except Exception as exc:
        print(f"get_room_panel_layout_config warning: {exc}")

    ttl_cache_set("room_panel_layout_config", dict(config), 45)
    return cache_set(request_key, dict(config))


ROOM_CENTER_DESIGN_SETTING_KEY = "room_center_design_config"
ROOM_CENTER_DESIGN_DEFAULTS = {
    "stage_padding": 18,
    "stage_gap": 18,
    "mode_width": 320,
    "mode_padding": 13,
    "vs_size": 150,
    "score_width": 340,
    "score_padding": 14,
    "score_input_height": 44,
    "action_height": 46,
    "vertical_layout": "compact",
}
ROOM_CENTER_DESIGN_LIMITS = {
    "stage_padding": (0, 40),
    "stage_gap": (0, 40),
    "mode_width": (180, 420),
    "mode_padding": (4, 28),
    "vs_size": (70, 220),
    "score_width": (220, 440),
    "score_padding": (6, 28),
    "score_input_height": (32, 64),
    "action_height": (34, 64),
}
ROOM_CENTER_VERTICAL_LAYOUTS = {"compact", "spread", "top"}


def normalize_room_center_design_config(raw):
    config = dict(ROOM_CENTER_DESIGN_DEFAULTS)
    try:
        if isinstance(raw, str):
            raw = json.loads(raw)
        if isinstance(raw, dict):
            for key, (lower, upper) in ROOM_CENTER_DESIGN_LIMITS.items():
                config[key] = _coerce_room_mode_logo_value(
                    raw.get(key), default=ROOM_CENTER_DESIGN_DEFAULTS[key], lower=lower, upper=upper,
                )
            layout = str(raw.get("vertical_layout") or "").strip().lower()
            if layout in ROOM_CENTER_VERTICAL_LAYOUTS:
                config["vertical_layout"] = layout
    except Exception as exc:
        print(f"normalize_room_center_design_config warning: {exc}")
    return config


def get_room_center_design_config(force=False):
    request_key = "_room_center_design_config_cached"
    if not force:
        cached = cache_get(request_key)
        if isinstance(cached, dict):
            return dict(cached)
        cached = ttl_cache_get("room_center_design_config")
        if isinstance(cached, dict):
            return cache_set(request_key, dict(cached))

    config = dict(ROOM_CENTER_DESIGN_DEFAULTS)
    try:
        result = execute_query(
            db.table("system_settings").select("setting_value")
            .eq("setting_key", ROOM_CENTER_DESIGN_SETTING_KEY).limit(1),
            "get_room_center_design_config", attempts=2,
        )
        raw = ((result.data or [{}])[0]).get("setting_value")
        config = normalize_room_center_design_config(raw)
    except Exception as exc:
        print(f"get_room_center_design_config warning: {exc}")

    ttl_cache_set("room_center_design_config", dict(config), 45)
    return cache_set(request_key, dict(config))


QUICK_MATCH_SETTING_KEY = "quick_match_config"
QUICK_MATCH_COLOR_DEFAULT = "blue"
QUICK_MATCH_COLOR_VALUES = {"blue", "green"}

def get_quick_match_config():
    request_key = "_quick_match_config_cached"
    cached = cache_get(request_key)
    if isinstance(cached, dict):
        return dict(cached)

    cached = ttl_cache_get("quick_match_config")
    if isinstance(cached, dict):
        return cache_set(request_key, dict(cached))

    config = {"color": QUICK_MATCH_COLOR_DEFAULT}
    try:
        result = execute_query(
            db.table("system_settings").select("setting_value")
            .eq("setting_key", QUICK_MATCH_SETTING_KEY).limit(1),
            "get_quick_match_config", attempts=2,
        )
        raw = ((result.data or [{}])[0]).get("setting_value")
        if isinstance(raw, str):
            raw = json.loads(raw)
        if isinstance(raw, dict) and raw.get("color") in QUICK_MATCH_COLOR_VALUES:
            config["color"] = raw["color"]
    except Exception as exc:
        print(f"get_quick_match_config warning: {exc}")

    ttl_cache_set("quick_match_config", dict(config), 60)
    return cache_set(request_key, dict(config))


DISCORD_ROOM_LINK_SETTING_KEY = "room_discord_link"

def get_room_discord_link():
    request_key = "_room_discord_link_cached"
    cached = cache_get(request_key)
    if isinstance(cached, str):
        return cached
    cached = ttl_cache_get("room_discord_link")
    if isinstance(cached, str):
        return cache_set(request_key, cached)
    value = ""
    try:
        result = execute_query(
            db.table("system_settings").select("setting_value")
            .eq("setting_key", DISCORD_ROOM_LINK_SETTING_KEY).limit(1),
            "get_room_discord_link", attempts=2,
        )
        raw = ((result.data or [{}])[0]).get("setting_value")
        if isinstance(raw, dict):
            value = str(raw.get("url") or "").strip()
        elif isinstance(raw, str):
            value = raw.strip()
    except Exception as exc:
        print(f"get_room_discord_link warning: {exc}")
    ttl_cache_set("room_discord_link", value, 60)
    return cache_set(request_key, value)


REPEAT_OPPONENT_CONFIG_SETTING_KEY = "repeat_opponent_rp_config"
REPEAT_OPPONENT_WINNER_FACTOR_DEFAULTS = [100, 60, 30, 0]
REPEAT_OPPONENT_LOSER_FACTOR_DEFAULTS = [100, 70, 40, 10]

def get_repeat_opponent_rp_config():
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
        result = execute_query(
            db.table("system_settings").select("setting_value").eq(
                "setting_key", REPEAT_OPPONENT_CONFIG_SETTING_KEY
            ).limit(1),
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
        print(f"get_repeat_opponent_rp_config warning: {exc}")

    ttl_cache_set("repeat_opponent_rp_config", {
        "winner_factors": list(config["winner_factors"]),
        "loser_factors": list(config["loser_factors"]),
    }, 60)
    return cache_set(request_key, config)


MAINTENANCE_SETTING_KEY = "server_maintenance_config"
VN_TIMEZONE = timezone(timedelta(hours=7))
_maintenance_cache = {"value": None, "expires_at": 0.0}


def _maintenance_default_config():
    return {
        "manual_closed": False,
        "close_at": "",
        "open_at": "",
        "message": "Hệ thống đang được bảo trì. Vui lòng quay lại sau.",
        "updated_at": "",
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
        result = execute_query(
            db.table("system_settings").select("setting_value")
            .eq("setting_key", MAINTENANCE_SETTING_KEY).limit(1),
            "get_server_maintenance_config",
            attempts=2,
        )
        row = (result.data or [{}])[0]
        raw = row.get("setting_value")
        if isinstance(raw, str):
            raw = json.loads(raw)
        if isinstance(raw, dict):
            for key in config:
                if key in raw:
                    config[key] = raw[key]
    except Exception as exc:
        app.logger.warning("Maintenance config load failed: %s", exc)

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
    # Lịch đóng có thể bật máy chủ tự động, lịch mở có thể mở lại kể cả khi
    # công tắc đóng thủ công đang bật. Mốc thời gian đến sau có quyền ưu tiên.
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
                "kind": next_transition[2],
                "target_iso": next_transition[0].isoformat(),
                "seconds": seconds,
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


def _current_session_is_admin():
    if not session.get("user_id"):
        return False
    try:
        return is_admin_user(current_user())
    except Exception:
        return False


def normalize_invite_code(value: str) -> str:
    return (value or "").strip().upper().replace(" ", "")


def generate_invite_code_value(length: int = 10) -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(length))


RANK_RANGE_SETTING_KEY = "rank_ranges"
_rank_range_cache = {"value": None, "expires_at": 0.0}































TEAM_LOGO_BUCKET = "team-logos"
LEAGUE_LOGO_FOLDER = "league-logos"
LEAGUE_LOGO_FILES = {
    "africa": "africa.png",
    "bundesliga": "bundesliga.png",
    "europe": "europe.png",
    "laliga ea sports": "laliga-ea-sports.png",
    "la liga ea sports": "laliga-ea-sports.png",
    "laliga": "laliga-ea-sports.png",
    "ligue 1": "ligue-1.png",
    "ligue1": "ligue-1.png",
    "premier league": "premier-league.png",
    "serie a": "serie-a.png",
    "serie bkt": "serie-bkt.png",
    "sky bet championship": "sky-bet-championship.png",
    "championship": "sky-bet-championship.png",
    "south america": "south-america.png",
    "super lig": "super-lig.png",
    "süper lig": "super-lig.png",
}


SMART_RANDOM_MODE = "Smart Rank"


CLUB_TIER_RANGES = {
    "S+": (80.50, 81.60),
    "S": (79.50, 80.49),
    "A+": (78.50, 79.49),
    "A": (77.50, 78.49),
    "B": (76.00, 77.49),
    "C": (74.50, 75.99),
    "D": (73.33, 74.49),
}
CLUB_TIER_ORDER = ["S+", "S", "A+", "A", "B", "C", "D"]

# Tỷ lệ Tier CLB theo từng Rank (khóa là level 0..9 trong code).
# Tổng tỷ lệ của mỗi Rank luôn bằng 100.
RANK_CLUB_TIER_WEIGHTS = {
    0: {"S+": 100},
    1: {"S+": 100},
    2: {"S+": 100},
    3: {"S+": 75, "S": 25},
    4: {"S+": 10, "S": 45, "A+": 45},
    5: {"S+": 5, "S": 20, "A+": 50, "A": 25},
    6: {"S": 5, "A+": 15, "A": 45, "B": 35},
    7: {"A+": 5, "A": 10, "B": 50, "C": 35},
    8: {"B": 10, "C": 55, "D": 35},
    9: {"B": 15, "C": 25, "D": 60},
}






_TEAM_CACHE = {"loaded_at": 0.0, "rows": [], "by_name": {}, "pools": {}}
_TEAM_CACHE_TTL_SECONDS = 30
TEAM_COUNT = 0














SMART_RANDOM_MODE = "Smart Tier Random"
RECENT_TEAM_EXCLUSION_COUNT = 5
HOST_XP_FACTOR = 0.95
MATCH_MODE_RANKED = "ranked"
MATCH_MODE_FRIENDLY = "friendly"
FRIENDLY_RANDOM3_MODE = "random3_pick1"
FRIENDLY_RANDOM3_NOTE_PREFIX = "FRIENDLY_RANDOM3:"
RANDOM_SELECTION_MATCH_MODE = "random_selection_match"
RANDOM_SELECTION_MATCH_NOTE_PREFIX = "RANDOM_SELECTION_MATCH:"













RANK_TIER_SETTING_KEY = "rank_club_tier_weights"
_rank_tier_config_cache = {"value": None, "expires_at": 0.0}














def _recent_pair_team_names(user_id, opponent_id, limit=RECENT_TEAM_EXCLUSION_COUNT):
    """CLB người chơi đã dùng trong N trận confirmed gần nhất với đúng đối thủ.

    Lịch sử dùng chung cho Rank thường và Random 3 chọn 1. Khi đổi đối thủ,
    danh sách chống lặp tự tách theo cặp người chơi mới.
    """
    if not user_id or not opponent_id:
        return []
    names = []
    try:
        matches = sorted(
            list_matches(),
            key=lambda item: str(item.get("created_at") or item.get("updated_at") or ""),
            reverse=True,
        )
        for match in matches:
            if str(match.get("status") or "").lower() != "confirmed":
                continue
            p1 = match.get("player1_id")
            p2 = match.get("player2_id")
            if p1 == user_id and p2 == opponent_id:
                name = match.get("team1")
            elif p2 == user_id and p1 == opponent_id:
                name = match.get("team2")
            else:
                continue
            if name:
                names.append(str(name).strip())
            if len(names) >= limit:
                break
    except Exception as exc:
        print(f"recent_pair_team_history warning: {exc}")
    return names

















def apply_host_xp_factor(delta, factor=HOST_XP_FACTOR):
    """Apply the room-host coefficient to the absolute RP change."""
    try:
        safe_factor = float(factor or HOST_XP_FACTOR)
    except (TypeError, ValueError):
        safe_factor = HOST_XP_FACTOR
    value = int(delta or 0)
    if value <= 0:
        return value
    adjusted = round(value * safe_factor)
    return max(1, adjusted)


def require_db():
    if db is None:
        raise RuntimeError("Supabase chưa được cấu hình. Kiểm tra file .env.")


def get_client_ip():
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or ""


def get_device_id():
    device_id = request.cookies.get(DEVICE_COOKIE_NAME)
    if not device_id:
        device_id = getattr(g, "new_device_id", None)
    if not device_id:
        device_id = str(uuid.uuid4())
        g.new_device_id = device_id
    return device_id


@app.after_request
def set_device_cookie(response):
    device_id = getattr(g, "new_device_id", None)
    if device_id:
        response.set_cookie(
            DEVICE_COOKIE_NAME,
            device_id,
            max_age=60 * 60 * 24 * 365,
            httponly=True,
            samesite="Lax",
        )

    # CSS/JS có APP_VERSION trong URL nên có thể cache dài và immutable.
    # Ảnh rank/giao diện giữ 30 ngày để giảm tải nhưng vẫn cho phép thay ảnh
    # cùng tên mà không phải chờ một năm.
    if request.endpoint == "static" or request.path.startswith("/static/"):
        static_path = request.path.lower()
        if static_path.endswith((".css", ".js")):
            cache_control = "public, max-age=31536000, immutable"
        elif static_path.startswith("/static/ranks/") or static_path.endswith(
            (".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif", ".ico")
        ):
            cache_control = "public, max-age=2592000, stale-while-revalidate=604800"
        else:
            cache_control = "public, max-age=604800, stale-while-revalidate=86400"
        response.headers["Cache-Control"] = cache_control
        response.headers.setdefault("Vary", "Accept-Encoding")
    return response


# =========================
# Database helpers
# =========================





# V1.4.1 — tài khoản tàng hình do Admin quản lý.
# Chỉ ảnh hưởng các bề mặt khám phá (BXH, Players, Dashboard, hồ sơ công khai,
# lịch sử toàn hệ thống, Tìm Nhanh). Không sửa RP, lịch sử gốc hoặc Core trận đấu.
INVISIBLE_PLAYERS_SETTING_KEY = "invisible_player_ids"














# V1.4 — điều kiện có thứ hạng chính thức trên BXH.
RANKING_QUALIFY_MATCHES = 5
RANKING_INACTIVE_HIDE_DAYS = 30






















def get_device_link(device_id):
    result = db.table("user_devices").select("*").eq("device_id", device_id).limit(1).execute()
    return result.data[0] if result.data else None


def is_admin_managed_test_account(user):
    """Tài khoản do Admin tạo/import: không bị khóa theo thiết bị hoặc cảnh báo trùng IP."""
    marker = str((user or {}).get("register_ip") or "").strip().upper()
    return marker.startswith("ADMIN_TEST") or marker.startswith("ADMIN_CREATED")


IP_WARNING_SETTING_KEY = "duplicate_ip_warning_config"
_ip_warning_config_cache = {"value": None, "expires_at": 0.0}


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
    """Ghi nhận thiết bị dùng gần nhất, nhưng không dùng thiết bị để chặn tài khoản.

    Từ V1.4.63, quy tắc duyệt tài khoản mới chỉ dựa trên IP đăng ký:
    IP mới -> tự duyệt; IP trùng -> chờ Admin kiểm duyệt. Vì vậy một thiết bị đã
    từng dùng tài khoản khác không được phép trở thành một lớp chặn thứ hai.
    """
    if user.get("role") == "admin" or is_admin_managed_test_account(user):
        return True, ""

    device_id = get_device_id()
    link = get_device_link(device_id)
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
        # Thiết bị chỉ là dữ liệu theo dõi. Khi một tài khoản đã được duyệt hợp lệ,
        # cập nhật liên kết sang tài khoản đang đăng nhập thay vì khóa đăng nhập.
        execute_query(
            db.table("user_devices").update({
                "user_id": user["id"],
                "ip_address": ip,
                "user_agent": user_agent,
                "last_seen_at": now_iso(),
            }).eq("id", link["id"]),
            "link_device_update",
        )

    return True, ""


def device_can_register():
    """Giữ endpoint tương thích; đăng ký không còn bị chặn theo thiết bị/browser."""
    return True, ""


def registration_ip_conflicts(ip):
    """Trả về các tài khoản player đang tồn tại đã đăng ký bằng cùng IP."""
    ip = str(ip or "").strip()
    if not ip:
        return []
    result = execute_query(
        db.table("users")
        .select("id,username,display_name,account_status,register_ip")
        .eq("role", "player")
        .eq("register_ip", ip),
        "registration_ip_conflicts", attempts=2,
    )
    rows = []
    for row in (result.data or []):
        if str(row.get("account_status") or "approved").lower() == "deleted":
            continue
        if is_admin_managed_test_account(row):
            continue
        rows.append(row)
    return rows



def list_all_users():
    require_db()
    result = execute_query(
        db.table("users").select("*").order("created_at", desc=True),
        "list_all_users",
    )
    return result.data or []


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
        users = users_map()
        for row in rows:
            user = users.get(row.get("user_id"), {})
            row["current_username"] = user.get("username") or row.get("username_snapshot") or "-"
            row["current_zalo_name"] = user.get("zalo_name") or row.get("zalo_name_snapshot") or "-"
            row["current_zalo_phone"] = row.get("zalo_phone_snapshot") or "-"
        return rows
    except Exception as exc:
        print(f"list_password_reset_requests warning: {exc}")
        return []


def list_user_devices():
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
            .order("last_seen_at", desc=True),
            "list_user_devices",
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


list_user_devices.last_status = {"ok": None, "row_count": 0, "error": None, "source": "not_loaded"}


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

























# Dịch vụ thông báo cá nhân đã tách sang modules/notification_service.py.






















def apply_room_abandon_penalty(user_id, amount=ROOM_ABANDON_PENALTY):
    """Trừ RP và tính một trận thua do bỏ trận, không cộng thắng cho đối thủ."""
    if not user_id:
        return None
    player = get_user(user_id)
    if not player:
        return None
    penalty = max(0, int(amount or 0))
    old_points = int(player.get("rank_points", 0) or 0)
    new_points = max(0, old_points - penalty)
    execute_query(
        db.table("users").update({
            "rank_points": new_points,
            "losses": int(player.get("losses", 0) or 0) + 1,
            "total_matches": int(player.get("wins", 0) or 0) + int(player.get("draws", 0) or 0) + int(player.get("losses", 0) or 0) + 1,
            "streak": 0,
        }).eq("id", user_id),
        "apply_room_abandon_penalty",
    )
    cache_delete("_rz_users_map")
    cache_delete("_rz_players_all")
    return -(old_points - new_points)


HOST_BROWSER_OFFLINE_GRACE_SECONDS = 20
HOST_BROWSER_OFFLINE_ROOM_STATUSES = {"playing", "friendly_playing"}















GLOBAL_STREAK_EVENT_SETTING_KEY = "global_win_streak_event"
GLOBAL_STREAK_EVENT_TTL_SECONDS = 24 * 60 * 60
GLOBAL_STREAK_EVENT_MAX_ITEMS = 30
































def current_user():
    cached = cache_get("_rz_current_user")
    if cached is not None:
        return cached

    user_id = session.get("user_id")
    if not user_id:
        return None

    try:
        shared_user = ttl_cache_get(f"user:{user_id}")
        user = dict(shared_user) if shared_user is not None else get_user(user_id)
        if user:
            decorate_player_achievements(user)
            ttl_cache_set(f"user:{user_id}", dict(user), 8)
            session["username"] = user.get("username", "")
            session["display_name"] = user.get("display_name", "")
            session["avatar_url"] = user.get("avatar_url")
            session["role"] = user.get("role", "player")
            session["account_status"] = user.get("account_status", "approved")
            session["admin_level"] = user.get("admin_level", "none")
            session["zcoin_balance"] = int(user.get("zcoin_balance") or 0)
            return cache_set("_rz_current_user", user)
    except Exception as exc:
        print(f"current_user warning: {exc}")

    # Fallback để tránh trắng trang khi Supabase ngắt kết nối vài giây.
    fallback_user = {
        "id": user_id,
        "username": session.get("username", "player"),
        "display_name": session.get("display_name", "Player"),
        "avatar_url": session.get("avatar_url"),
        "role": session.get("role", "player"),
        "account_status": session.get("account_status", "approved"),
        "admin_level": session.get("admin_level", "none"),
        "zcoin_balance": int(session.get("zcoin_balance") or 0),
        "rank_points": 0,
        "is_online": True,
        "matchmaking_cooldown_until": None,
    }
    return cache_set("_rz_current_user", fallback_user)













ACTIVE_ROOM_STATUSES = {
    "waiting_ready",
    "playing",
    "friendly_playing",
    "waiting_result_confirm",
    "waiting_confirm",
    "disputed",
}
































def mark_current_user_active():
    user_id = session.get("user_id")
    if not user_id:
        return

    # Admin có thể chủ động ẩn trạng thái Online trong chính phiên đăng nhập.
    # Người chơi thường luôn dùng presence tự động như trước.
    try:
        cached_user = current_user()
    except Exception:
        cached_user = None
    is_admin_account = bool(cached_user and is_admin_user(cached_user))
    forced_offline = is_admin_account and session.get("admin_presence_mode") == "offline"

    try:
        db.table("users").update({
            "is_online": not forced_offline,
            "last_seen_at": now_iso(),
        }).eq("id", user_id).execute()
        # Dữ liệu Players được cache RAM ngắn. Xóa cache sau heartbeat để các
        # instance đang ấm không tiếp tục dùng last_seen_at cũ.
        ttl_cache_delete("players_raw", f"user:{user_id}")
        cache_delete("_rz_players_all")
        cache_delete("_rz_current_user")
    except Exception as exc:
        print(f"Heartbeat warning: {exc}")


def mark_current_user_offline():
    """Đánh dấu offline khi tab/trình duyệt đóng; timeout vẫn là lớp dự phòng."""
    user_id = session.get("user_id")
    if not user_id:
        return
    try:
        db.table("users").update({
            "is_online": False,
            "last_seen_at": now_iso(),
        }).eq("id", user_id).execute()
        ttl_cache_delete("players_raw", f"user:{user_id}")
        cache_delete("_rz_players_all")
        cache_delete("_rz_current_user")
    except Exception as exc:
        print(f"Presence offline warning: {exc}")


def ensure_admin():
    global _admin_checked
    if _admin_checked or db is None:
        return

    admin = get_user_by_username("admin")
    if not admin:
        # Không tự tạo/reset mật khẩu owner trong runtime. Tài khoản sở hữu phải
        # được tạo bằng migration hoặc thao tác thủ công an toàn trong Supabase.
        app.logger.warning("Owner account 'admin' is missing; ensure_admin skipped creation for safety.")
    else:
        # Chỉ chuẩn hóa vai trò; tuyệt đối không ghi đè password_hash.
        execute_query(
            db.table("users").update({
                "display_name": "Admin",
                "role": "admin",
                "admin_level": "owner",
                "account_status": "approved",
            }).eq("username", "admin"),
            "ensure_admin_update_role_only",
        )

    _admin_checked = True


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Bạn cần đăng nhập trước.", "warning")
            return redirect(url_for("login"))

        user = current_user()
        if not user:
            session.clear()
            flash("Phiên đăng nhập không hợp lệ.", "warning")
            return redirect(url_for("login"))

        status = user.get("account_status", "approved")
        if status != "approved":
            session.clear()
            messages = {
                "pending": "Tài khoản đang chờ Admin duyệt.",
                "rejected": "Tài khoản đã bị từ chối.",
                "banned": "Tài khoản đã bị khóa.",
                "deleted": "Tài khoản này đã được xóa khỏi hệ thống.",
            }
            flash(messages.get(status, "Tài khoản chưa được phép sử dụng."), "danger")
            return redirect(url_for("login"))

        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user_id = session.get("user_id")
        user = None
        if user_id:
            try:
                user = get_user(user_id)
                if user:
                    decorate_player_achievements(user)
                    session["username"] = user.get("username", "")
                    session["display_name"] = user.get("display_name", "")
                    session["avatar_url"] = user.get("avatar_url")
                    session["role"] = user.get("role", "player")
                    session["account_status"] = user.get("account_status", "approved")
                    session["admin_level"] = user.get("admin_level", "none")
                    session["zcoin_balance"] = int(user.get("zcoin_balance") or 0)
                    cache_set("_rz_current_user", user)
            except Exception as exc:
                print(f"admin_required warning: {exc}")

        if not user:
            session.clear()
            flash("Phiên đăng nhập admin không hợp lệ. Vui lòng đăng nhập lại.", "warning")
            return redirect(url_for("admin_login"))

        if not is_admin_user(user):
            flash("Bạn không có quyền admin.", "danger")
            return redirect(url_for("dashboard"))
        return view(*args, **kwargs)
    return wrapped


def owner_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()
        if not is_owner_user(user):
            flash("Chỉ chủ hệ thống mới có quyền này.", "danger")
            return redirect(url_for("admin"))
        return view(*args, **kwargs)
    return wrapped


def admin_permission_required(permission_code: str):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            user = current_user()
            if not has_admin_permission(user, permission_code):
                flash("Admin phụ chưa được Chủ hệ thống cấp quyền sử dụng chức năng này.", "danger")
                return redirect_admin("overview")
            return view(*args, **kwargs)
        return wrapped
    return decorator

@app.before_request
def enforce_server_maintenance():
    """Khóa toàn bộ website cho người dùng thường, kể cả /login.

    Admin luôn dùng /admin-login để vào hệ thống khi máy chủ đang bảo trì.
    Static assets và trang đăng nhập Admin được phép để màn hình bảo trì vẫn tải đẹp.
    """
    endpoint = request.endpoint or ""
    allowed_public = {"static", "admin_login"}
    if endpoint in allowed_public:
        return None

    status = get_maintenance_status()
    if not status.get("closed"):
        return None

    if _current_session_is_admin():
        return None

    # Không cho người dùng thường lách qua /login, API, link trực tiếp hoặc phiên cũ.
    if session.get("user_id"):
        session.clear()
    response = make_response(render_template("maintenance.html", maintenance=status), 503)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return response


@app.before_request
def before_request():
    try:
        # Chạy tối đa 1 lần/6 giờ cho toàn hệ thống để tạo cảnh báo 3 ngày
        # và áp dụng RP suy giảm kể cả khi người chơi chưa quay lại đăng nhập.
        if request.endpoint != "static":
            process_inactivity_decay_batch()

        # V4.9: chỉ thao tác thật của người dùng mới gia hạn phiên. Heartbeat/polling không gia hạn.
        if session.get("user_id"):
            now_ts = int(time.time())
            remembered_login = bool(session.get("remember_account"))

            # V1.4.21 — Login Session V2:
            # - Phiên thường: giữ cơ chế timeout 60 phút không hoạt động.
            # - Phiên "Ghi nhớ đăng nhập": cookie tồn tại 30 ngày và KHÔNG bị idle-timeout 60 phút xóa.
            # Flask lưu cờ permanent trong session; gán lại để các phiên remember cũ cũng được chuẩn hóa.
            if remembered_login:
                session.permanent = True
            else:
                last_real = int(session.get("last_real_activity", 0) or 0)

                # V1.14.41.78: người chơi có thể chuyển sang cửa sổ PES/Parsec trong khi
                # trang phòng nằm nền. Mọi request thuộc đúng phòng đấu được xem là
                # hoạt động hợp lệ để không bị đăng xuất giữa trận.
                room_request_active = (
                    request.path.startswith("/room/")
                    or request.path.startswith("/api/room/")
                )
                if room_request_active:
                    session["last_real_activity"] = now_ts
                    session.modified = True
                    last_real = now_ts

                if not last_real:
                    session["last_real_activity"] = now_ts
                elif now_ts - last_real >= IDLE_TIMEOUT_SECONDS and request.endpoint not in {"logout", "static", "api_session_timeout_check", "api_session_activity"}:
                    room = None
                    try:
                        room = active_room_for_user(session.get("user_id"))
                    except Exception as exc:
                        print(f"idle room check warning: {exc}")
                    decision = idle_decision(now_ts=now_ts, last_activity_ts=last_real, room=room)
                    if decision.protected:
                        # Tuyệt đối không đăng xuất khi người chơi đang ở một trận/phòng cần hoàn tất.
                        session["last_real_activity"] = now_ts
                        session.modified = True
                    elif decision.expired:
                        try:
                            execute_query(
                                db.table("users").update({"is_online": False, "last_seen_at": now_iso()}).eq("id", session.get("user_id")),
                                "idle_logout_mark_offline",
                                attempts=1,
                            )
                        except Exception as exc:
                            print(f"idle logout warning: {exc}")
                        session.clear()
                        if request.path.startswith("/api/"):
                            return jsonify({"ok": False, "error": "session_expired", "redirect": url_for("login")}), 401
                        flash("Bạn đã được đăng xuất do không hoạt động trong 60 phút.", "warning")
                        return redirect(url_for("login"))

        # Không gọi ensure_admin() ở mọi request. Trước đây mỗi Vercel instance mới
        # lại đọc + cập nhật bảng users trước khi tải /bxh, tạo thêm kết nối Supabase
        # và có thể gây [Errno 16] Device or resource busy.
        if db is not None and session.get("user_id"):
            # Chỉ cập nhật online tối đa 1 lần/45 giây thay vì ở mọi request
            # (HTML, API, ảnh, heartbeat đều từng tạo một lệnh UPDATE riêng).
            now_ts = int(time.time())
            last_touch = int(session.get("last_activity_touch", 0) or 0)
            if request.endpoint == "heartbeat" or now_ts - last_touch >= 45:
                mark_current_user_active()
                session["last_activity_touch"] = now_ts

            user = current_user()
            allowed = {"change_password", "logout", "static", "heartbeat"}
            if user and user.get("must_change_password") and request.endpoint not in allowed:
                flash("Bạn đang dùng mật khẩu tạm thời. Hãy đổi mật khẩu mới để tiếp tục.", "warning")
                return redirect(url_for("change_password"))
    except Exception as exc:
        # Lỗi cập nhật online không được phép làm hỏng route chính.
        print(f"Before request warning: {exc}")


@app.context_processor

def inject_globals():
    try:
        user = current_user()
    except Exception as exc:
        print(f"inject user warning: {exc}")
        user = None

    if request.endpoint == "change_password":
        return {
            "APP_NAME": APP_NAME,
            "current_user": user,
            "get_rank_name": get_rank_name,
            "get_rank_info": get_rank_info,
            "get_rank_display": get_rank_display,
            "get_team_overall": get_team_overall,
            "get_team_tier": get_team_tier,
        "get_win_streak_title": get_win_streak_title,
        "get_win_streak_badge": get_win_streak_badge,
        "get_league_logo_url": get_league_logo_url,
            "TEAM_COUNT": TEAM_COUNT,
            "APP_VERSION": APP_VERSION,
            "RANKS": load_rank_ranges(),
            "format_vn_datetime": format_vn_datetime,
            "pending_invite_count": 0,
            "incoming_invites": [],
            "active_room": None,
            "cooldown_text": "",
            "active_announcement": None,
            "bell_notifications": [],
            "unread_notification_count": 0,
        }

    # Tối ưu phản hồi HTML: không chặn render để chờ phòng, lời mời và thông báo
    # hệ thống. Các dữ liệu này đã có API nền trong base.html và sẽ xuất hiện ngay
    # sau khi trang hiển thị. Chỉ giữ thông báo cá nhân vì chưa có API riêng.
    pending_count = 0
    incoming = []
    active_room = None
    cooldown = cooldown_text(user) if user else ""
    announcement = None
    try:
        bell_notifications = list_bell_notifications(user.get("id"), 20) if user else []
        unread_notification_count = sum(1 for notice in bell_notifications if not notice.get("is_read"))
    except Exception:
        bell_notifications = []
        unread_notification_count = 0

    return {
        "APP_NAME": APP_NAME,
        "current_user": user,
        "get_rank_name": get_rank_name,
        "get_rank_info": get_rank_info,
        "get_rank_display": get_rank_display,
        "get_team_overall": get_team_overall,
        "get_team_tier": get_team_tier,
        "get_win_streak_title": get_win_streak_title,
        "get_win_streak_badge": get_win_streak_badge,
        "TEAM_COUNT": TEAM_COUNT,
        "APP_VERSION": APP_VERSION,
        "RANKS": load_rank_ranges(),
        "format_vn_datetime": format_vn_datetime,
        "pending_invite_count": pending_count,
        "incoming_invites": incoming,
        "active_room": active_room,
        "cooldown_text": cooldown,
        "active_announcement": announcement,
        "bell_notifications": bell_notifications,
        "unread_notification_count": unread_notification_count,
        "quick_match_config": get_quick_match_config(),
    }




















def build_room_state_key(room):
    """Tạo khóa trạng thái ổn định dùng chung cho HTML và API phòng đấu."""
    return "|".join([
        # Thành viên phòng phải nằm trong state key. Nếu khách vừa tham gia
        # nhưng status vẫn là waiting_ready và guest_ready vẫn False, thiếu
        # guest_user_id sẽ khiến chủ phòng nhận 204 và không làm mới giao diện.
        str(room.get("host_user_id")),
        str(room.get("guest_user_id")),
        str(room.get("updated_at")),
        str(room.get("status")),
        str(room.get("host_team")),
        str(room.get("guest_team")),
        str(room.get("guest_ready")),
        str(room.get("host_score")),
        str(room.get("guest_score")),
        str(room.get("rematch_host_ready")),
        str(room.get("rematch_guest_ready")),
        str(room.get("rematch_host_declined")),
        str(room.get("rematch_guest_declined")),
        str(room.get("rematch_expired")),
        str(room.get("state_expires_at")),
        # C1 chuyển Trận 1 -> Trận 2 có thể giữ nguyên 2 HLV và nhiều trường
        # phòng. Note lại chứa tournament_match_id/leg hiện tại, nên phải đưa
        # dấu vân tay của note vào state key để máy khách luôn nhận ra lần đổi leg.
        hashlib.sha1(str(room.get("note") or "").encode("utf-8")).hexdigest()[:16],
        str((room.get("dispute") or {}).get("status")),
        str((room.get("dispute") or {}).get("updated_at")),
        str(room.get("parsec_link")),
        str(room.get("host_name_style_class")),
        str(room.get("guest_name_style_class")),
        str(((room.get("host_profile_badge") or {}).get("image_url"))),
        str(((room.get("guest_profile_badge") or {}).get("image_url"))),
    ])


def polling_stop_response(reason="stopped"):
    """Kết thúc một poller cũ mà không tạo lỗi 4xx trên trình duyệt."""
    response = app.response_class(status=204)
    response.headers["Cache-Control"] = "no-store, max-age=0"
    response.headers["X-PES-Polling-Stop"] = str(reason or "stopped")[:80]
    return response



# =========================
# Auth
# =========================





def normalize_zalo_phone(value: str) -> str:
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    if digits.startswith("84") and len(digits) in {11, 12}:
        digits = "0" + digits[2:]
    return digits


def generate_temporary_password(length: int = 6) -> str:
    # Bỏ các ký tự dễ nhìn nhầm: I/O/0/1.
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(length))









# =========================
# Chat / Announcements
# =========================


























# =========================
# Hướng dẫn người chơi
# =========================


# =========================
# Dashboard / players
# =========================






def _build_season_stats_map(matches, season):
    """Rebuild W/D/L + recent form for one season from preserved match history.

    This is also the compatibility path for Season 1 snapshots created before
    V1.4.11, which only stored final RP/position/name.
    """
    start = None
    end = None
    try:
        start = parse_dt((season or {}).get("started_at")) if (season or {}).get("started_at") else None
    except Exception:
        start = None
    try:
        end = parse_dt((season or {}).get("ended_at")) if (season or {}).get("ended_at") else None
    except Exception:
        end = None

    stats = {}
    for match in matches or []:
        if str(match.get("status") or "").lower() != "confirmed":
            continue
        try:
            created = parse_dt(match.get("created_at")) if match.get("created_at") else None
        except Exception:
            created = None
        if start and (not created or created < start):
            continue
        if end and (not created or created > end):
            continue

        p1, p2 = match.get("player1_id"), match.get("player2_id")
        s1, s2 = match.get("score1"), match.get("score2")
        if not p1 or not p2 or s1 is None or s2 is None:
            continue
        try:
            s1, s2 = int(s1), int(s2)
        except (TypeError, ValueError):
            continue

        for uid, mine, theirs in ((p1, s1, s2), (p2, s2, s1)):
            key = str(uid)
            row = stats.setdefault(key, {"wins": 0, "draws": 0, "losses": 0, "recent_form": []})
            if mine > theirs:
                row["wins"] += 1; code = {"code": "win", "short": "T", "label": "Thắng"}
            elif mine < theirs:
                row["losses"] += 1; code = {"code": "loss", "short": "B", "label": "Bại"}
            else:
                row["draws"] += 1; code = {"code": "draw", "short": "H", "label": "Hòa"}
            # list_matches() is newest first, so the first five are the final five of the season.
            if len(row["recent_form"]) < 5:
                row["recent_form"].append(code)
    return stats


def _build_recent_form_map(matches, player_ids=None, limit=5):
    """Build recent form pills for leaderboard rows using confirmed matches only."""
    tracked_ids = set(player_ids or []) if player_ids else None
    recent_map = {}

    for match in matches or []:
        if match.get("status") != "confirmed":
            continue

        player1_id = match.get("player1_id")
        player2_id = match.get("player2_id")
        score1 = match.get("score1")
        score2 = match.get("score2")
        if not player1_id or not player2_id or score1 is None or score2 is None:
            continue

        for player_id, my_score, opponent_score in (
            (player1_id, score1, score2),
            (player2_id, score2, score1),
        ):
            if tracked_ids is not None and player_id not in tracked_ids:
                continue

            bucket = recent_map.setdefault(player_id, [])
            if len(bucket) >= limit:
                continue

            if my_score > opponent_score:
                bucket.append({"code": "win", "short": "T", "label": "Thắng"})
            elif my_score < opponent_score:
                bucket.append({"code": "loss", "short": "B", "label": "Bại"})
            else:
                bucket.append({"code": "draw", "short": "H", "label": "Hòa"})

    return recent_map




# Hồ sơ cá nhân đã tách sang modules/profile.


# =========================
# Invites
# =========================




def is_quick_match_invite(invite):
    """Return True only for invites generated by the Quick Match flow."""
    message = str((invite or {}).get("message") or "")
    return message.startswith("QUICK_MATCH|")


QUICK_MATCH_ACTIVE_SECONDS = 30 * 60










# =========================
# Rooms
# =========================


# =========================
# Legacy / history routes
# =========================









# =========================
# Đăng ký module chức năng
# =========================
def redirect_admin(tab="overview"):
    """Điểm điều hướng Admin dùng chung; ưu tiên giữ tab người dùng vừa thao tác."""
    submitted_tab = (request.form.get("_admin_tab") or "").strip() if request.method == "POST" else ""
    if submitted_tab and submitted_tab.replace("-", "").isalnum():
        tab = submitted_tab
    return redirect(url_for("admin") + f"#{tab}")


# Nạp dịch vụ theo thứ tự dependency: thông báo -> khóa -> kết quả -> phát lại -> xóa an toàn.
from modules import legacy_ranking_service as _legacy_ranking_service
from modules import legacy_team_random_service as _legacy_team_random_service
from modules import legacy_player_service as _legacy_player_service
from modules import legacy_match_service as _legacy_match_service
from modules import legacy_room_service as _legacy_room_service
from modules import legacy_chat_service as _legacy_chat_service
from modules import legacy_room_activity_service as _legacy_room_activity_service
from modules import notification_service as _notification_service
from modules import forfeit_history_service as _forfeit_history_service
from modules import ranking_lock_service as _ranking_lock_service
from modules import weekly_rp_rewards_service as _weekly_rp_rewards_service
from modules import match_result_service as _match_result_service
from modules import ranking_rebuild_service as _ranking_rebuild_service
from modules import data_cleanup_service as _data_cleanup_service
from modules import inactivity_rp_service as _inactivity_rp_service
from modules import daily_rank_limit_service as _daily_rank_limit_service
from modules import repeat_opponent_rp_service as _repeat_opponent_rp_service
from modules import zcoin as _zcoin_module
from modules import daily_checkin as _daily_checkin_module
from modules.parsec_room import service as _parsec_room_service
from modules import gift_codes as _gift_codes_module
from modules import season_service as _season_service

for _service_module in (
    _legacy_ranking_service,
    _legacy_team_random_service,
    _legacy_player_service,
    _legacy_match_service,
    _legacy_room_service,
    _legacy_chat_service,
    _legacy_room_activity_service,
    _notification_service,
    _forfeit_history_service,
    _ranking_lock_service,
    _daily_rank_limit_service,
    _repeat_opponent_rp_service,
    _weekly_rp_rewards_service,
    _zcoin_module,
    _daily_checkin_module,
    _gift_codes_module,
    _season_service,
    _parsec_room_service,
    _match_result_service,
    _ranking_rebuild_service,
    _data_cleanup_service,
    _inactivity_rp_service,
):
    _service_module.configure(globals())
    for _service_name in _service_module.EXPORTED_NAMES:
        globals()[_service_name] = getattr(_service_module, _service_name)

# Refresh dependency snapshots after all service exports have been installed.
# This keeps cross-service references identical to the former single-file app.py.
for _service_module in (
    _legacy_ranking_service,
    _legacy_team_random_service,
    _legacy_player_service,
    _legacy_match_service,
    _legacy_room_service,
    _legacy_chat_service,
    _legacy_room_activity_service,
    _notification_service,
    _forfeit_history_service,
    _ranking_lock_service,
    _daily_rank_limit_service,
    _repeat_opponent_rp_service,
    _weekly_rp_rewards_service,
    _zcoin_module,
    _daily_checkin_module,
    _gift_codes_module,
    _season_service,
    _parsec_room_service,
    _match_result_service,
    _ranking_rebuild_service,
    _data_cleanup_service,
    _inactivity_rp_service,
):
    _service_module.configure(globals())


# Route legacy đã tách khỏi app.py để app chỉ còn bootstrap + service chung.
from modules.notification_routes import register_routes as _register_notification_routes
from modules.session_presence_routes import register_routes as _register_session_presence_routes
from modules.room_api_routes import register_routes as _register_room_api_routes
from modules.auth_routes import register_routes as _register_auth_routes
from modules.chat_routes import register_routes as _register_chat_routes
from modules.announcement_routes import register_routes as _register_announcement_routes
from modules.dashboard_routes import register_routes as _register_dashboard_routes
from modules.ranking_routes import register_routes as _register_ranking_routes
from modules.invite_routes import register_routes as _register_invite_routes

# Route phòng đấu.
from modules.room_access_routes import register_routes as _register_room_access_routes
from modules.room_rematch_routes import register_routes as _register_room_rematch_routes
from modules.room_team_routes import register_routes as _register_room_team_routes
from modules.room_result_routes import register_routes as _register_room_result_routes
from modules.match_history_routes import register_routes as _register_match_history_routes
from modules.zcoin import register_routes as _register_zcoin_routes
from modules.profile import register_routes as _register_profile_routes
from modules.parsec_room import register_routes as _register_parsec_room_routes
from modules.shop import register_routes as _register_shop_routes
from modules.inventory import register_routes as _register_inventory_routes
from modules.admin_shop import register_routes as _register_admin_shop_routes
from modules.daily_checkin import register_routes as _register_daily_checkin_routes
from modules.gift_codes import register_routes as _register_gift_code_routes
from modules.admin_economy import register_routes as _register_admin_economy_routes
from modules.luckybox import register_routes as _register_luckybox_routes
from modules.tournament_routes import register_routes as _register_tournament_routes
from modules.tournament_competition import register_routes as _register_tournament_competition_routes
from modules.tournament_test_mode import register_routes as _register_tournament_test_mode_routes

# Route Admin.
from modules.admin_system_routes import register_routes as _register_admin_system_routes
from modules.admin_dashboard_routes import register_routes as _register_admin_dashboard_routes
from modules.admin_account_routes import register_routes as _register_admin_account_routes
from modules.admin_match_routes import register_routes as _register_admin_match_routes
from modules.admin_player_routes import register_routes as _register_admin_player_routes
from modules.admin_data_routes import register_routes as _register_admin_data_routes
from modules.season_routes import register_routes as _register_season_routes

for _route_registrar in (
    _register_notification_routes,
    _register_session_presence_routes,
    _register_room_api_routes,
    _register_auth_routes,
    _register_chat_routes,
    _register_announcement_routes,
    _register_dashboard_routes,
    _register_ranking_routes,
    _register_invite_routes,
    _register_room_access_routes,
    _register_room_rematch_routes,
    _register_room_team_routes,
    _register_room_result_routes,
    _register_match_history_routes,
    _register_zcoin_routes,
    _register_profile_routes,
    _register_parsec_room_routes,
    _register_shop_routes,
    _register_inventory_routes,
    _register_admin_shop_routes,
    _register_daily_checkin_routes,
    _register_gift_code_routes,
    _register_admin_economy_routes,
    _register_luckybox_routes,
    _register_tournament_routes,
    _register_tournament_competition_routes,
    _register_tournament_test_mode_routes,
    _register_season_routes,
    _register_admin_system_routes,
    _register_admin_dashboard_routes,
    _register_admin_account_routes,
    _register_admin_match_routes,
    _register_admin_player_routes,
    _register_admin_data_routes,
):
    _route_registrar(globals())

del _service_module, _service_name, _route_registrar


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
