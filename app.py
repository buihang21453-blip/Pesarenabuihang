import csv
import json
import hashlib
import os
import random
import secrets
import string
import time
import uuid
import zipfile
from datetime import datetime, timezone, timedelta
from functools import wraps
from pathlib import Path

from dotenv import load_dotenv
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
from modules.presence.service import is_online as presence_is_online
from modules.invites.service import send_invite_blocker, SEND_INVITE_MESSAGES, accept_invite_blocker
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
from modules.static_asset_service import (
    asset_url, asset_base_url, shop_asset_base_url, luckybox_asset_base_url,
    room_asset_url, room_asset_base_url, mode_asset_url, mode_asset_base_url,
)
from modules.profile import equipment_service as profile_equipment_service
from modules.observability import configure_app_logging, log_system_event
from modules.win_streaks import (
    WIN_STREAK_TITLES, WIN_STREAK_EVENT_PREFIX, get_win_streak_title,
    get_win_streak_badge, build_win_streak_event, encode_win_streak_room_note,
    parse_win_streak_room_note,
)


load_dotenv()

APP_NAME = "PES Arena – Bản Lĩnh Sân Cỏ"
APP_VERSION = "1.3.125"
DEFAULT_POINTS = 1000
DEVICE_COOKIE_NAME = "rankzone_device_id"
COOLDOWN_MINUTES = 3
ONLINE_TIMEOUT_SECONDS = 120
CHAT_COOLDOWN_SECONDS = 5
CHAT_MAX_LENGTH = 200
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
ACCOUNT_STATUSES = {"pending", "approved", "rejected", "banned"}
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

configure_app_logging(app, APP_VERSION)

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
app.jinja_env.globals["room_asset"] = room_asset_url
app.jinja_env.globals["room_asset_base_url"] = room_asset_base_url
app.jinja_env.globals["mode_asset"] = mode_asset_url
app.jinja_env.globals["mode_asset_base_url"] = mode_asset_base_url

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
                log_system_event(
                    "database_query_failed",
                    level=40,
                    label=label,
                    attempts=attempt + 1,
                    transient=transient,
                    error_type=type(exc).__name__,
                    error=str(exc),
                )
                raise

            log_system_event(
                "database_query_retry",
                level=30,
                label=label,
                attempt=attempt + 1,
                max_attempts=max(1, attempts),
                error_type=type(exc).__name__,
            )
            # Backoff ngắn: 0.25s, 0.5s, 0.75s...
            time.sleep(delay * (attempt + 1))

    raise last_error



_admin_checked = False


# =========================
# Basic helpers
# =========================
# Tiện ích thời gian đã tách sang modules/datetime_utils.py

# Dispute evidence helpers moved to modules/core/dispute_evidence.py (V1.3.61).
from modules.core import dispute_evidence as _core_dispute_evidence
_core_dispute_evidence.configure(globals())
for _evidence_name in _core_dispute_evidence.EXPORTED_NAMES:
    globals()[_evidence_name] = getattr(_core_dispute_evidence, _evidence_name)


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


# Compatibility source marker for legacy static regression checks: "rank_standard_enabled": True
# System settings / maintenance / permission helpers moved to
# modules/core/system_settings_runtime.py (V1.3.61). Public names stay bound in
# app.py for compatibility with existing route modules and tests.
from modules.core import system_settings_runtime as _core_system_settings_runtime
_core_system_settings_runtime.configure(globals())
for _settings_name in _core_system_settings_runtime.EXPORTED_NAMES:
    globals()[_settings_name] = getattr(_core_system_settings_runtime, _settings_name)


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







RANK_TIER_SETTING_KEY = "rank_club_tier_weights"
_rank_tier_config_cache = {"value": None, "expires_at": 0.0}

































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





















IP_WARNING_SETTING_KEY = "duplicate_ip_warning_config"
_ip_warning_config_cache = {"value": None, "expires_at": 0.0}































































# Dịch vụ thông báo cá nhân đã tách sang modules/notification_service.py.
























SERIES_FORFEIT_RP = 20




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
            ttl_cache_set(f"user:{user_id}", dict(user), 30)
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
            # Presence V1.3.36: route /heartbeat tự cập nhật presence, không UPDATE
            # thêm một lần trong before_request. Các request thường chỉ là lớp
            # dự phòng nếu heartbeat phía trình duyệt bị trì hoãn.
            now_ts = int(time.time())
            last_touch = int(session.get("last_activity_touch", 0) or 0)
            if request.endpoint != "heartbeat" and now_ts - last_touch >= 60:
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


def _safe_blackbox_runtime_config():
    """Black Box must never make a normal page render fail.

    Returns a fully disabled config if the module is unavailable or any environment
    value is malformed. This is intentionally fail-open for PES Arena gameplay.
    """
    fallback = {
        "enabled": False,
        "client_enabled": False,
        "capture_clicks": False,
        "capture_network": False,
        "capture_console": False,
        "batch_size": 20,
        "flush_ms": 10000,
        "slow_api_ms": 2500,
        "max_buffer": 200,
        "app_version": APP_VERSION,
    }
    try:
        fn = globals().get("blackbox_config")
        if not callable(fn):
            return fallback
        cfg = fn() or {}
        if not isinstance(cfg, dict):
            return fallback
        return {**fallback, **cfg}
    except Exception as exc:
        try:
            app.logger.warning("Black Box config disabled after error: %s", exc)
        except Exception:
            pass
        return fallback


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
            "blackbox_runtime_config": _safe_blackbox_runtime_config(),
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
        "button_theme_config": get_button_theme_config(),
        "blackbox_runtime_config": _safe_blackbox_runtime_config(),
    }


@app.route("/notifications")
@login_required
def notifications():
    user = current_user()
    unread_only = (request.args.get("filter") or "all") == "unread"
    notices, _ = list_user_notifications(
        user.get("id"), page=1, per_page=20, unread_only=unread_only
    )
    return render_template(
        "notifications.html",
        notifications=notices,
        page=1,
        has_next=False,
        notification_filter="unread" if unread_only else "all",
        notification_retention_days=7,
        notification_max_items=20,
    )


@app.route("/notifications/read-all", methods=["POST"])
@login_required
def mark_all_notifications_read():
    user = current_user()
    execute_query(
        db.table("user_notifications").update({
            "is_read": True,
            "read_at": now_iso(),
        }).eq("user_id", user.get("id")).eq("is_read", False),
        "mark_all_notifications_read",
    )
    ttl_cache_delete(f"bell_notifications:{user.get('id')}")
    flash("Đã đánh dấu tất cả thông báo là đã đọc.", "success")
    return redirect(url_for("notifications"))


@app.route("/notification/<notification_id>/read", methods=["POST"])
@login_required
def mark_notification_read(notification_id):
    user = current_user()
    execute_query(
        db.table("user_notifications").update({
            "is_read": True,
            "read_at": now_iso(),
        }).eq("id", notification_id).eq("user_id", user.get("id")),
        "mark_notification_read",
    )
    ttl_cache_delete(f"bell_notifications:{user.get('id')}")
    next_url = request.form.get("next_url", "").strip()
    if next_url.startswith("/") and not next_url.startswith("//"):
        return redirect(next_url)
    return redirect(request.referrer or url_for("dashboard"))


@app.route("/api/session/activity", methods=["POST"])
@login_required
def api_session_activity():
    """Gia hạn phiên chỉ khi trình duyệt báo có thao tác thật của người dùng."""
    now_ts = int(time.time())
    session["last_real_activity"] = now_ts
    session["last_activity_touch"] = now_ts
    session.modified = True
    return jsonify({"ok": True, "last_activity": now_ts})


@app.route("/api/session/timeout-check")
@login_required
def api_session_timeout_check():
    """Chỉ gọi một lần khi bộ đếm 60 phút hết; không phải polling."""
    user = current_user()
    room = None
    try:
        if user:
            room = active_room_for_user(user.get("id"))
    except Exception as exc:
        print(f"timeout check room warning: {exc}")
    protected = room_blocks_idle_logout(room)
    return jsonify({
        "ok": True,
        "protected": protected,
        "room_url": url_for("room_detail", room_id=room.get("id")) if protected and room else None,
    })


@app.route("/heartbeat", methods=["POST"])
@login_required
def heartbeat():
    mark_current_user_active()
    session["last_activity_touch"] = int(time.time())
    return jsonify({"ok": True})


@app.route("/presence/offline", methods=["POST"])
@login_required
def presence_offline():
    # V1.3.36: endpoint tương thích cho tab/client cũ. Không đánh dấu offline từ
    # pagehide/sendBeacon vì refresh, back-forward cache và điều hướng có thể đến
    # muộn hơn request của trang mới, làm user đang hoạt động bị Offline giả.
    # Logout thật vẫn đánh dấu offline tại route logout; còn mất kết nối được xác
    # định bằng ONLINE_TIMEOUT_SECONDS.
    return ("", 204)


@app.route("/api/invites/pending")
@login_required
def api_pending_invites():
    """Truy vấn trực tiếp lời mời của người hiện tại để giảm độ trễ popup."""
    user = current_user()
    if not user:
        return jsonify({"invites": []})

    try:
        # Lấy nhiều bản ghi thay vì chỉ 1 bản ghi mới nhất. Nếu lời mời mới nhất
        # vừa hết hạn trong lúc xử lý, lời mời hợp lệ cũ hơn vẫn phải được trả về.
        result = execute_query(
            db.table("match_invites")
              .select("id,from_user_id,to_user_id,tier,status,expires_at,created_at")
              .eq("to_user_id", user["id"])
              .eq("status", "pending")
              .order("created_at", desc=True)
              .limit(20),
            "api_pending_invites_direct",
            attempts=2,
        )
        rows = result.data or []
        data = []
        for row in rows:
            invite = expire_invite_if_needed(dict(row))
            if invite.get("status") != "pending":
                continue
            sender = get_user(invite.get("from_user_id")) or {}
            decorate_player_achievements(sender)
            data.append({
                "id": invite["id"],
                "from_name": sender.get("display_name", "Unknown"),
                "from_avatar_url": sender.get("avatar_url"),
                "from_avatar_frame": sender.get("avatar_frame"),
                "from_achievement": sender.get("featured_achievement"),
                "from_rank": get_rank_display(sender.get("rank_points", 0)),
                "from_points": sender.get("rank_points", 0),
                "tier": invite.get("tier") or SMART_RANDOM_MODE,
                "expires_in_seconds": int(invite.get("expires_in_seconds") or 0),
                "accept_url": url_for("respond_invite", invite_id=invite["id"]),
                "reject_url": url_for("respond_invite", invite_id=invite["id"]),
            })
        response = jsonify({"invites": data})
        response.headers["Cache-Control"] = "no-store, max-age=0"
        response.headers["X-Invite-Poll"] = "fast-active"
        return response
    except Exception as exc:
        # Không trả danh sách rỗng khi DB lỗi vì phía trình duyệt sẽ hiểu nhầm là
        # không còn lời mời và tự ẩn popup đang hiển thị.
        print(f"api_pending_invites ERROR user={user.get('id')}: {type(exc).__name__}: {exc}")
        response = jsonify({"ok": False, "error": "invite_poll_failed"})
        response.status_code = 503
        response.headers["Cache-Control"] = "no-store, max-age=0"
        return response



@app.route("/api/active-room")
@login_required

def api_active_room():
    user = current_user()

    if not user or user.get("role") == "admin":
        return jsonify({"ok": True, "has_room": False})

    try:
        room = active_room_for_user(user["id"])
    except Exception:
        return jsonify({"ok": False, "has_room": False, "error": "temporary_db_error"}), 503

    if not room:
        return jsonify({"ok": True, "has_room": False})

    is_host = room.get("host_user_id") == user["id"]
    is_guest = room.get("guest_user_id") == user["id"]
    has_opponent = bool(room.get("guest_user_id"))

    # Chỉ ép quay lại khi trận đã bắt đầu hoặc đang chờ xác nhận.
    # Phòng trống/chờ sẵn sàng vẫn cho phép người dùng xem các trang khác.
    must_finish_statuses = {"playing", "friendly_playing", "waiting_result_confirm"}
    auto_redirect = bool(room.get("status") in must_finish_statuses and has_opponent)

    return jsonify({
        "ok": True,
        "has_room": True,
        "room_id": room["id"],
        "room_url": url_for("room_detail", room_id=room["id"]),
        "status": room.get("status"),
        "is_host": is_host,
        "is_guest": is_guest,
        "has_opponent": has_opponent,
        "auto_redirect": auto_redirect,
    })

def build_room_state_key(room, series_version=None):
    """Tạo khóa trạng thái nhẹ dùng chung cho HTML và API phòng đấu.

    team_tier + updated_at fix the stale-mode bug. ``series_version`` lets the
    opponent see Tactical/Ban-Pick actions even when the match_rooms row itself
    did not change.
    """
    return "|".join([
        # Thành viên phòng phải nằm trong state key. Nếu khách vừa tham gia
        # nhưng status vẫn là waiting_ready và guest_ready vẫn False, thiếu
        # guest_user_id sẽ khiến chủ phòng nhận 204 và không làm mới giao diện.
        str(room.get("host_user_id")),
        str(room.get("guest_user_id")),
        str(room.get("status")),
        str(room.get("match_mode")),
        str(room.get("team_tier")),
        str(room.get("updated_at")),
        str(series_version or ""),
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


@app.route("/api/room/<room_id>/state")
@login_required

def api_room_state(room_id):
    user = current_user()

    try:
        room = get_room_poll_snapshot(room_id)
    except Exception:
        return jsonify({"ok": False, "error": "temporary_db_error"}), 503

    if not room:
        return polling_stop_response("room_not_found")

    if close_room_if_host_browser_offline(room):
        return polling_stop_response("host_browser_offline")

    if user["id"] not in [room["host_user_id"], room["guest_user_id"]] and not is_admin_user(user):
        return polling_stop_response("room_access_ended")

    # Cấm/Chọn BO3: polling cũng là nhịp watchdog. Khi hết thời gian, server
    # tự random đúng 1 CLB cho lượt hiện tại rồi cấp deadline mới cho lượt sau.
    try:
        timeout_result = process_series_timeouts(room)
        if timeout_result.get("changed"):
            room = get_room_poll_snapshot(room_id) or room
    except ValueError:
        pass

    series_version = get_series_poll_version(room)
    state_key = build_room_state_key(room, series_version)

    # V4.1: nếu trạng thái chưa đổi, trả response rỗng để giảm dữ liệu truyền.
    # Client vẫn giữ polling nhưng không phải nhận/phân tích JSON lặp lại.
    since_state_key = (request.args.get("since") or "").strip()
    if since_state_key and since_state_key == state_key:
        response = app.response_class(status=204)
        response.headers["Cache-Control"] = "no-store, max-age=0"
        response.headers["X-Room-State-Unchanged"] = "1"
        return response

    rematch_declined_by_me = (
        (user["id"] == room.get("host_user_id") and room.get("rematch_host_declined"))
        or (user["id"] == room.get("guest_user_id") and room.get("rematch_guest_declined"))
    )

    return jsonify({
        "ok": True,
        "state_key": state_key,
        "status": room.get("status"),
        "rematch_declined": bool(room.get("rematch_declined")),
        "rematch_declined_by_me": bool(rematch_declined_by_me),
        "rematch_expired": bool(room.get("rematch_expired")),
        "timeout_seconds": int(room.get("timeout_seconds") or 0),
        "timeout_label": room.get("timeout_label") or "",
    })

# =========================
# Auth
# =========================
@app.route("/")
def index():
    # Trang chủ công khai luôn mở thẳng Bảng xếp hạng.
    # Người dùng chỉ được chuyển tới màn hình đăng nhập khi chủ động bấm Đăng nhập.
    return redirect(url_for("ranking"))


@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    get_device_id()

    existing = current_user() if session.get("user_id") else None
    if existing and is_admin_user(existing):
        return redirect(url_for("admin"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        try:
            user = get_user_by_username(username)
        except Exception as exc:
            app.logger.warning("Admin login database warning: %s", exc)
            flash("Máy chủ dữ liệu đang bận. Vui lòng thử lại sau vài giây.", "warning")
            return redirect(url_for("admin_login"))

        if not user or user.get("password_hash") != hash_password(password):
            flash("Sai tài khoản hoặc mật khẩu Admin.", "danger")
            return redirect(url_for("admin_login"))
        if user.get("account_status", "approved") != "approved" or not is_admin_user(user):
            flash("Tài khoản này không có quyền truy cập trang quản trị.", "danger")
            return redirect(url_for("admin_login"))

        session.clear()
        session["user_id"] = user["id"]
        session["username"] = user.get("username", "")
        session["display_name"] = user.get("display_name", "")
        session["avatar_url"] = user.get("avatar_url")
        session["role"] = user.get("role", "player")
        session["account_status"] = user.get("account_status", "approved")
        session["admin_level"] = user.get("admin_level", "none")
        session["zcoin_balance"] = int(user.get("zcoin_balance") or 0)
        session["last_real_activity"] = int(time.time())
        session["last_activity_touch"] = int(time.time())
        execute_query(
            db.table("users").update({"is_online": True, "last_seen_at": now_iso()}).eq("id", user["id"]),
            "admin_login_mark_online",
            attempts=2,
        )
        return redirect(url_for("admin"))

    return render_template("admin_login.html", auth_only=True)


@app.route("/login", methods=["GET", "POST"])
def login():
    get_device_id()

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        try:
            user = get_user_by_username(username)
        except Exception as exc:
            # A temporary Supabase/Vercel socket failure must not become a raw 500.
            print(f"Login database warning: {exc}")
            flash("Máy chủ dữ liệu đang bận. Vui lòng đăng nhập lại sau vài giây.", "warning")
            return redirect(url_for("login"))

        if not user or user["password_hash"] != hash_password(password):
            flash("Sai tên tài khoản hoặc mật khẩu.", "danger")
            return redirect(url_for("login"))

        status = user.get("account_status", "approved")
        if status != "approved":
            messages = {
                "pending": "Tài khoản của bạn đang chờ Admin duyệt.",
                "rejected": "Tài khoản của bạn đã bị từ chối.",
                "banned": "Tài khoản của bạn đã bị khóa. Hãy liên hệ Admin.",
            }
            flash(messages.get(status, "Tài khoản chưa được phép đăng nhập."), "danger")
            return redirect(url_for("login"))

        ok, msg = link_device_to_user(user)
        if not ok:
            flash(msg, "danger")
            return redirect(url_for("login"))

        remember_account = request.form.get("remember_account") == "1"
        session.permanent = remember_account
        session["remember_account"] = remember_account
        session["user_id"] = user["id"]
        session["username"] = user.get("username", "")
        session["display_name"] = user.get("display_name", "")
        session["avatar_url"] = user.get("avatar_url")
        session["role"] = user.get("role", "player")
        session["account_status"] = status
        session["admin_level"] = user.get("admin_level", "none")
        session["zcoin_balance"] = int(user.get("zcoin_balance") or 0)
        session["last_real_activity"] = int(time.time())
        session["last_activity_touch"] = int(time.time())
        # Tính RP không hoạt động trước khi cập nhật last_seen_at của lần đăng nhập mới.
        try:
            process_inactivity_for_user(user)
        except Exception as exc:
            print(f"Login inactivity decay warning: {exc}")
        execute_query(
            db.table("users").update({"is_online": True, "last_seen_at": now_iso()}).eq("id", user["id"]),
            "login_mark_online",
        )

        if user.get("must_change_password"):
            flash("Đăng nhập bằng mật khẩu tạm thành công. Hãy tạo mật khẩu mới.", "warning")
            return redirect(url_for("change_password"))

        # Người mở link chia sẻ khi chưa đăng nhập sẽ được đưa trở lại đúng
        # phòng sau khi đăng nhập, thay vì bị rơi về Dashboard/BXH.
        pending_room_join_id = session.pop("pending_room_join_id", None)
        if pending_room_join_id:
            return redirect(url_for("room_join_shared", room_id=pending_room_join_id))

        return redirect(url_for(post_login_endpoint(get_system_features(), is_admin=is_admin_user(user))))

    return render_template("login.html")

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        zalo_name = request.form.get("zalo_name", "").strip()
        user = get_user_by_username(username) if username else None

        matches_identity = bool(
            user
            and zalo_name
            and (user.get("zalo_name") or "").strip().casefold() == zalo_name.casefold()
        )

        if matches_identity:
            existing = execute_query(
                db.table("password_reset_requests")
                .select("id")
                .eq("user_id", user["id"])
                .eq("status", "pending")
                .limit(1),
                "find_pending_password_reset",
            )
            if not existing.data:
                execute_query(
                    db.table("password_reset_requests").insert({
                        "user_id": user["id"],
                        "username_snapshot": user.get("username"),
                        "zalo_name_snapshot": user.get("zalo_name"),
                        "status": "pending",
                        "requested_ip": get_client_ip(),
                    }),
                    "create_password_reset_request",
                )

        flash("Nếu tài khoản và tên Zalo khớp, yêu cầu đã được gửi đến Admin. Hãy liên hệ Admin qua Zalo để nhận mật khẩu tạm.", "success")
        return redirect(url_for("login"))

    return render_template("forgot_password.html")


@app.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    user = current_user()
    if request.method == "POST":
        current_password = request.form.get("current_password", "").strip()
        new_password = request.form.get("new_password", "").strip()
        if user.get("password_hash") != hash_password(current_password):
            flash("Mật khẩu tạm hoặc mật khẩu hiện tại không đúng.", "danger")
            return redirect(url_for("change_password"))
        valid_password, password_error = validate_new_password(new_password)
        if not valid_password:
            flash(password_error, "danger")
            return redirect(url_for("change_password"))
        if hash_password(new_password) == user.get("password_hash"):
            flash("Mật khẩu mới phải khác mật khẩu tạm hoặc mật khẩu hiện tại.", "warning")
            return redirect(url_for("change_password"))

        changed_at = now_iso()
        execute_query(
            db.table("users").update({
                "password_hash": hash_password(new_password),
                "must_change_password": False,
                "password_changed_at": changed_at,
            }).eq("id", user["id"]),
            "user_change_password",
        )
        try:
            execute_query(
                db.table("password_reset_requests").update({
                    "status": "resolved",
                    "admin_note": "User đã tự đổi mật khẩu.",
                    "resolved_at": changed_at,
                }).eq("user_id", user["id"]).eq("status", "pending"),
                "close_password_reset_after_user_change",
            )
        except Exception as exc:
            print(f"close password reset warning: {exc}")
        flash("Đã đổi mật khẩu thành công.", "success")
        pending_room_join_id = session.pop("pending_room_join_id", None)
        if pending_room_join_id:
            return redirect(url_for("room_join_shared", room_id=pending_room_join_id))
        return redirect(url_for("profile", user_id=user["id"]) + "#account-controls")

    if not user.get("must_change_password"):
        return redirect(url_for("profile", user_id=user["id"]) + "#account-controls")
    return render_template("change_password.html", force_change=True, auth_only=True, minimum_password_length=minimum_password_length())


@app.route("/register", methods=["GET", "POST"])
def register():
    if not system_feature_enabled("registration_codes_enabled"):
        flash("Tính năng đăng ký tài khoản đang tạm tắt.", "warning")
        return redirect(url_for("login"))
    get_device_id()

    if request.method == "POST":
        can_register, msg = device_can_register()
        if not can_register:
            flash(msg, "danger")
            return redirect(url_for("register"))

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        zalo_name = request.form.get("zalo_name", "").strip()

        if not username or not password or not zalo_name:
            flash("Vui lòng nhập đủ Tên tài khoản, Mật khẩu và Tên Zalo.", "danger")
            return redirect(url_for("register"))

        if len(username) < 3 or len(username) > 30:
            flash("Tên tài khoản phải từ 3 đến 30 ký tự.", "danger")
            return redirect(url_for("register"))

        if len(password) < minimum_password_length():
            flash(f"Mật khẩu phải có ít nhất {minimum_password_length()} ký tự.", "danger")
            return redirect(url_for("register"))

        if len(zalo_name) < 2 or len(zalo_name) > 80:
            flash("Tên Zalo không hợp lệ.", "danger")
            return redirect(url_for("register"))

        if get_user_by_username(username):
            flash("Tên tài khoản đã tồn tại.", "danger")
            return redirect(url_for("register"))

        ip = get_client_ip()
        ua = request.headers.get("User-Agent", "")

        created = execute_query(
            db.table("users").insert({
                "username": username,
                "password_hash": hash_password(password),
                "display_name": username,
                "zalo_name": zalo_name,
                "role": "player",
                "account_status": "pending",
                "invite_code_used": None,
                "rank_points": DEFAULT_POINTS,
                "register_ip": ip,
                "register_user_agent": ua,
            }),
            "register_user",
        )

        user = created.data[0]
        link_device_to_user(user)

        flash("Đăng ký thành công. Tài khoản đang chờ Admin duyệt.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/logout")
@login_required
def logout():
    user_id = session.get("user_id")
    if user_id:
        try:
            execute_query(
                db.table("users").update({"is_online": False, "last_seen_at": now_iso()}).eq("id", user_id),
                "logout_mark_offline",
            )
        except Exception as exc:
            print(f"logout warning: {exc}")
    session.clear()
    if request.args.get("reason") == "inactive":
        flash("Bạn đã được đăng xuất do không hoạt động trong 60 phút.", "warning")
    else:
        flash("Đã đăng xuất.", "success")
    return redirect(url_for("login"))


# =========================
# Chat / Announcements
# =========================
@app.route("/chat")
@login_required
def lobby_chat():
    if not system_feature_enabled("lobby_chat_enabled"):
        return redirect(url_for("dashboard"))
    return render_template("chat.html", messages=list_chat_messages("global", limit=20))


@app.route("/chat/send", methods=["POST"])
@login_required
def send_global_chat():
    user = current_user()
    message = request.form.get("message", "")

    ok, error = create_chat_message(user["id"], message, scope="global")
    if not ok:
        flash(error, "warning")
    else:
        flash("Đã gửi tin nhắn.", "success")

    return redirect(url_for("lobby_chat"))


@app.route("/api/chat/global")
@login_required
def api_global_chat():
    if not system_feature_enabled("lobby_chat_enabled"):
        return polling_stop_response("lobby_chat_disabled")
    messages = list_chat_messages("global", limit=20)
    return jsonify({"ok": True, "messages": messages})


@app.route("/api/chat/global/status")
@login_required
def api_global_chat_status():
    if not system_feature_enabled("lobby_chat_enabled"):
        return polling_stop_response("lobby_chat_disabled")
    """Dữ liệu nhẹ để hiển thị số tin chat sảnh chưa đọc khi khung chat đang đóng."""
    user = current_user()
    limit = 100
    query = (
        db.table("chat_messages")
        .select("id,user_id,created_at")
        .eq("scope", "global")
        .is_("room_id", "null")
        .order("created_at", desc=True)
        .limit(limit)
    )
    result = execute_query(query, "api_global_chat_status")
    rows = list(reversed(result.data or []))

    messages = [
        {
            "id": row.get("id"),
            "created_at": row.get("created_at"),
            "is_own": row.get("user_id") == user.get("id"),
        }
        for row in rows
    ]

    return jsonify({
        "ok": True,
        "messages": messages,
        "latest_created_at": messages[-1]["created_at"] if messages else None,
        "limit_reached": len(messages) >= limit,
    })


@app.route("/api/room/<room_id>/chat")
@login_required
def api_room_chat(room_id):
    if not system_feature_enabled("room_chat_enabled"):
        return polling_stop_response("room_chat_disabled")
    user = current_user()
    room = get_room(room_id)

    if not room:
        return polling_stop_response("room_not_found")

    if user["id"] not in [room["host_user_id"], room["guest_user_id"]] and not is_admin_user(user):
        return polling_stop_response("room_access_ended")

    messages = list_chat_messages("room", room_id=room_id, limit=20)
    return jsonify({"ok": True, "messages": messages})


@app.route("/room/<room_id>/chat/send", methods=["POST"])
@login_required
def send_room_chat(room_id):
    if not system_feature_enabled("room_chat_enabled"):
        flash("Chat phòng đang bị tắt.", "warning")
        return redirect(url_for("room_detail", room_id=room_id))
    user = current_user()
    room = get_room(room_id)

    if not room:
        flash("Không tìm thấy phòng.", "danger")
        return redirect(url_for("rooms"))

    if user["id"] not in [room["host_user_id"], room["guest_user_id"]] and not is_admin_user(user):
        flash("Bạn không thuộc phòng này.", "danger")
        return redirect(url_for("rooms"))

    message = request.form.get("message", "")
    ok, error = create_chat_message(user["id"], message, scope="room", room_id=room_id)

    if not ok:
        flash(error, "warning")

    return redirect(url_for("room_detail", room_id=room_id))


@app.route("/api/room/<room_id>/chat/send", methods=["POST"])
@login_required
def api_send_room_chat(room_id):
    """Gửi chat phòng bằng AJAX, không redirect và không tải lại khung phòng."""
    if not system_feature_enabled("room_chat_enabled"):
        return jsonify({"ok": False, "disabled": True, "error": "Chat phòng đang bị tắt."})

    user = current_user()
    room = get_room(room_id)
    if not room:
        return polling_stop_response("room_not_found")
    if user["id"] not in [room["host_user_id"], room["guest_user_id"]] and not is_admin_user(user):
        return polling_stop_response("room_access_ended")

    payload = request.get_json(silent=True) or request.form
    message = payload.get("message", "")
    ok, error = create_chat_message(user["id"], message, scope="room", room_id=room_id)
    if not ok:
        return jsonify({"ok": False, "error": error}), 400
    return jsonify({"ok": True})


@app.route("/admin/announcement", methods=["POST"])
@login_required
@admin_required
@admin_permission_required("announcements_manage")
def admin_create_announcement():
    user = current_user()
    title = request.form.get("title", "THÔNG BÁO").strip() or "THÔNG BÁO"
    message = request.form.get("message", "").strip()

    if not message:
        flash("Nội dung thông báo không được để trống.", "danger")
        return redirect_admin("system")

    created = create_admin_announcement(
        title=title[:40],
        message=message[:220],
        admin_user_id=user.get("id"),
    )
    announcement_id = created.data[0].get("id") if created.data else None
    log_admin_action("Đăng thông báo", "announcement", announcement_id, title[:40], message[:220])

    flash("Đã đăng thông báo admin.", "success")
    return redirect_admin("system")


@app.route("/admin/announcement/clear", methods=["POST"])
@login_required
@admin_required
@admin_permission_required("announcements_manage")
def admin_clear_announcement():
    db.table("admin_announcements").update({"is_active": False}).eq("is_active", True).execute()
    log_admin_action("Tắt thông báo", "announcement", details="Đã tắt toàn bộ thông báo đang hoạt động.")
    flash("Đã tắt thông báo admin.", "success")
    return redirect_admin("system")


@app.route("/api/announcement/current")
@login_required
def api_current_announcement():
    events = get_active_global_streak_events()
    if events:
        announcements = []
        for event in events:
            kind = str(event.get("kind") or "milestone")
            announcements.append({
                "id": f"streak:{event.get('id', 'event')}",
                "title": event.get("title") or "DANH HIỆU CHUỖI THẮNG",
                "message": event.get("subtitle") or "Một danh hiệu mới vừa được thiết lập!",
                "created_at": event.get("published_at"),
                "expires_at": event.get("expires_at"),
                "announcement_type": "shutdown" if kind == "shutdown" else "win_streak",
                "icon": "⚡" if kind == "shutdown" else "🏆",
            })
        return jsonify({"ok": True, "announcements": announcements, "announcement": announcements[0]})

    announcement = get_active_announcement()
    if not announcement:
        return jsonify({"ok": True, "announcements": [], "announcement": None})
    admin_item = {
        "id": announcement["id"],
        "title": announcement["title"],
        "message": announcement["message"],
        "created_at": announcement["created_at"],
        "announcement_type": "admin",
        "icon": "📢",
    }
    return jsonify({"ok": True, "announcements": [admin_item], "announcement": admin_item})


@app.route("/api/chat/global/send", methods=["POST"])
@login_required
def api_send_global_chat():
    if not system_feature_enabled("lobby_chat_enabled"):
        return jsonify({"ok": False, "disabled": True, "error": "Chat Sảnh đang bị tắt."})
    user = current_user()
    payload = request.get_json(silent=True) or {}
    message = payload.get("message", "")

    ok, error = create_chat_message(user["id"], message, scope="global")
    if not ok:
        return jsonify({"ok": False, "error": error}), 400

    return jsonify({"ok": True})


@app.route("/api/admin/announcement/send", methods=["POST"])
@login_required
@admin_required
@admin_permission_required("announcements_manage")
def api_admin_send_announcement():
    if not system_feature_enabled("announcements_enabled"):
        return jsonify({"ok": False, "error": "Thông báo hệ thống đang bị tắt."}), 403
    user = current_user()
    payload = request.get_json(silent=True) or {}
    title = (payload.get("title") or "THÔNG BÁO").strip()[:40] or "THÔNG BÁO"
    message = (payload.get("message") or "").strip()[:220]

    if not message:
        return jsonify({"ok": False, "error": "Nội dung thông báo không được để trống."}), 400

    created = create_admin_announcement(
        title=title,
        message=message,
        admin_user_id=user.get("id"),
    )
    announcement_id = created.data[0].get("id") if created.data else None
    log_admin_action("Đăng thông báo", "announcement", announcement_id, title, message)

    return jsonify({"ok": True})


@app.route("/api/online-count")
@login_required
def api_online_count():
    players = list_players(include_admin=True)
    online_count = sum(1 for player in players if player.get("is_online"))
    return jsonify({"ok": True, "online_count": online_count})


# =========================
# Hướng dẫn người chơi
# =========================
@app.route("/huong-dan")
@login_required
def guide():
    return render_template("guide.html")


# =========================
# Dashboard / players
# =========================
@app.route("/dashboard")
@login_required
def dashboard():
    if not dashboard_is_enabled(get_system_features()):
        return redirect(url_for("ranking"))
    user = current_user()
    try:
        player_rows = list_players()
        presence_rows = list_players(include_admin=True)
        # V1.3.34: Dashboard chỉ lấy trận của chính user, không list_matches() toàn hệ thống.
        matches = load_user_matches(user.get("id"), limit=30)
        rooms = list_rooms()
        invite_count = current_pending_invite_count()
    except Exception:
        player_rows, presence_rows, matches, rooms = [], [], [], []
        invite_count = 0
        flash("Dữ liệu đang tải chậm, vui lòng thử lại sau vài giây.", "warning")

    me = next((player for player in player_rows if player.get("id") == user.get("id")), dict(user))
    my_position = next((index for index, player in enumerate(player_rows, 1) if player.get("id") == user.get("id")), None)
    my_rank_info = get_player_rank_info(me, my_position)
    total = calculated_total_matches(me)
    wins = int(me.get("wins", 0) or 0)
    me["winrate"] = round((wins / total) * 100, 1) if total else 0

    my_matches = [
        decorate_match_for_view(match, user.get("id"))
        for match in matches
        if user.get("id") in {match.get("player1_id"), match.get("player2_id")}
    ]
    recent_matches = my_matches[:5]

    active_room = active_room_for_user(user.get("id"))
    attention = {
        "invites": invite_count,
        "has_room": bool(active_room),
        "waiting_confirm": len([m for m in matches if m.get("status") == "waiting_confirm" and user.get("id") in {m.get("player1_id"), m.get("player2_id")}]),
        "disputed": len([m for m in matches if m.get("status") == "disputed" and user.get("id") in {m.get("player1_id"), m.get("player2_id")}]),
    }

    activity_map = build_player_activity_map(rooms, [])
    online_players = [p for p in presence_rows if p.get("is_online") and p.get("id") != user.get("id")]
    solo_room_user_ids = {
        str(room.get("host_user_id"))
        for room in rooms
        if is_solo_waiting_room(room, room.get("host_user_id"))
    }
    for player in online_players:
        status = activity_map.get(player.get("id"), {"code": "ready", "label": "Sẵn sàng"})
        player["activity_code"] = status["code"]
        player["activity_label"] = status["label"]
        player["can_receive_invite"] = bool(
            status["code"] == "ready" or str(player.get("id")) in solo_room_user_ids
        )
        player["is_busy"] = not player["can_receive_invite"]

    online_players.sort(key=lambda p: (p.get("is_busy", False), _player_ranking_sort_key(p)))

    return render_template(
        "dashboard.html",
        me=me,
        my_position=my_position,
        my_rank_info=my_rank_info,
        attention=attention,
        online_players=online_players,
        recent_matches=recent_matches,
    )


@app.route("/rooms/create", methods=["POST"])
@login_required
def create_open_room():
    user = current_user()
    limit_message = daily_rank_block_message(user.get("id"))
    if limit_message:
        flash(limit_message, "warning")
        return redirect(url_for("dashboard"))
    cleanup_duplicate_waiting_rooms(user["id"])
    existing = active_room_for_user(user["id"])
    if existing:
        return redirect(url_for("room_detail", room_id=existing["id"]))
    if active_match_for_user(user["id"]):
        flash("Bạn đang có trận chưa hoàn tất.", "warning")
        return redirect(url_for("dashboard"))

    room = execute_query(
        db.table("match_rooms").insert({
            "invite_id": None,
            "host_user_id": user["id"],
            "guest_user_id": None,
            "team_tier": default_rank_room_team_tier(),
            "match_mode": MATCH_MODE_RANKED,
            "friendly_tier": "A",
            "status": "waiting_ready",
            "guest_ready": False,
            "note": "Phòng mở đang chờ chủ phòng mời đối thủ.",
            "state_expires_at": None,
            "updated_at": now_iso(),
        }),
        "create_open_room",
    ).data[0]
    # Chống double-click / hai request chạy đồng thời trên nhiều Vercel instance.
    cleanup_duplicate_waiting_rooms(user["id"])
    canonical_room = active_room_for_user(user["id"])
    if canonical_room:
        room = canonical_room
    flash("Đã tạo phòng đấu. Bạn có thể mời đối thủ từ danh sách Players.", "success")
    return redirect(url_for("room_detail", room_id=room["id"]))


@app.route("/players")
@login_required
def players():
    player_rows = list_players(include_admin=True)
    rooms = list_rooms()
    activity_map = build_player_activity_map(rooms=rooms)
    solo_room_user_ids = {
        str(room.get("host_user_id"))
        for room in rooms
        if is_solo_waiting_room(room, room.get("host_user_id"))
    }
    viewer = current_user()
    viewer_room = active_room_for_user(viewer.get("id")) if viewer else None
    viewer_can_invite = bool(
        viewer
        and not active_match_for_user(viewer.get("id"))
        and (not viewer_room or is_solo_waiting_room(viewer_room, viewer.get("id")))
    )
    query = (request.args.get("q") or "").strip().casefold()
    status_filter = (request.args.get("status") or "all").strip()

    for player in player_rows:
        if not player.get("is_online"):
            status = {"code": "offline", "label": "Offline"}
        else:
            status = activity_map.get(player.get("id"), {"code": "ready", "label": "Sẵn sàng"})
        player["activity_code"] = status["code"]
        player["activity_label"] = status["label"]
        player["is_busy"] = status["code"] not in {"ready", "offline"}
        player["can_receive_invite"] = bool(
            player.get("is_online")
            and (status["code"] == "ready" or str(player.get("id")) in solo_room_user_ids)
        )
        total = calculated_total_matches(player)
        player["winrate"] = round((int(player.get("wins", 0) or 0) / total) * 100, 1) if total else 0
        player["last_seen_display"] = format_vn_datetime(player.get("last_seen_at"))

    if query:
        player_rows = [
            player for player in player_rows
            if query in str(player.get("display_name") or "").casefold()
            or query in str(player.get("username") or "").casefold()
        ]
    if status_filter != "all":
        player_rows = [player for player in player_rows if player.get("activity_code") == status_filter]

    status_order = {"ready": 0, "in_room": 1, "waiting_confirm": 2, "playing": 3, "offline": 4}
    player_rows.sort(key=lambda p: (status_order.get(p.get("activity_code"), 9), _player_ranking_sort_key(p)))
    return render_template(
        "players.html",
        players=player_rows,
        q=request.args.get("q", ""),
        status_filter=status_filter,
        viewer_can_invite=viewer_can_invite,
    )


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


@app.route("/ranking")
@app.route("/bxh")
def ranking():
    user = current_user()

    # Admin có thể khóa BXH công khai. Người đã đăng nhập vẫn được xem BXH,
    # chỉ khách chưa đăng nhập mới được chuyển về trang đăng nhập.
    if not user and not system_feature_enabled("public_ranking_enabled"):
        flash("Bảng xếp hạng công khai đang được Admin tạm khóa. Vui lòng đăng nhập để tiếp tục.", "warning")
        return redirect(url_for("login"))

    try:
        player_rows = list_players()
    except Exception as exc:
        # BXH là trang công khai; nếu Supabase chập chờn thì vẫn trả trang thay vì HTTP 500.
        print(f"ranking list_players warning: {exc}")
        player_rows = []

    query = (request.args.get("q") or "").strip().casefold()
    rank_filter = (request.args.get("rank") or "all").strip()

    current_player = None
    current_position = None
    if user:
        current_player = next((player for player in player_rows if player.get("id") == user.get("id")), None)
        current_position = current_player.get("position") if current_player else None

    filtered = player_rows
    if query:
        filtered = [
            player for player in filtered
            if query in str(player.get("display_name") or "").casefold()
            or query in str(player.get("username") or "").casefold()
        ]
    if rank_filter != "all":
        filtered = [player for player in filtered if player.get("rank_info", {}).get("slug") == rank_filter]

    top_players = filtered[:100]
    # V1.3.34: phong độ 5 trận đã được trigger Supabase lưu sẵn. BXH chỉ SELECT cache.
    recent_form_map = load_recent_form_map({player.get("id") for player in top_players})

    for player in top_players:
        total_matches = calculated_total_matches(player)
        wins = int(player.get("wins") or 0)
        draws = int(player.get("draws") or 0)
        losses = int(player.get("losses") or 0)
        player["winrate"] = round((wins / total_matches) * 100, 1) if total_matches else 0
        player["record_text"] = f"{wins}T • {draws}H • {losses}B"
        player["recent_form"] = recent_form_map.get(player.get("id"), [])

    template_name = "ranking.html" if user else "public_ranking.html"
    return render_template(
        template_name,
        players=filtered,
        current_player=current_player,
        current_position=current_position,
        q=request.args.get("q", ""),
        rank_filter=rank_filter,
    )


# Hồ sơ cá nhân đã tách sang modules/profile.


# =========================
# Invites
# =========================
@app.route("/invites")
@login_required
def invites():
    user = current_user()

    # Nếu người chơi đã có phòng active, không để mắc kẹt ở trang mời đấu.
    try:
        active_room = active_room_for_user(user["id"])
        if active_room:
            return redirect(url_for("room_detail", room_id=active_room["id"]))
    except Exception:
        flash("Đang kiểm tra phòng hiện tại hơi chậm, vui lòng thử lại sau vài giây.", "warning")

    all_players = list_players()
    available_players = [
        player for player in all_players
        if player["id"] != user["id"] and player.get("is_online")
    ]

    all_invites = list_invites()
    received = [i for i in all_invites if i["to_user_id"] == user["id"] and i["status"] == "pending"]
    sent = [i for i in all_invites if i["from_user_id"] == user["id"] and i["status"] == "pending"]
    history = [i for i in all_invites if i["from_user_id"] == user["id"] or i["to_user_id"] == user["id"]][:20]

    return render_template(
        "invites.html",
        players=available_players,
        received=received,
        sent=sent,
        history=history,
    )


@app.route("/invites/send", methods=["POST"])
@login_required
def send_invite():
    user = current_user()

    to_user_id = request.form.get("to_user_id")
    tier = SMART_RANDOM_MODE

    if not to_user_id or to_user_id == user["id"]:
        flash("Đối thủ không hợp lệ.", "danger")
        return redirect(url_for("players"))

    opponent = get_user(to_user_id)
    if not opponent:
        flash("Không tìm thấy đối thủ.", "danger")
        return redirect(url_for("players"))

    try:
        state = matchmaking_snapshot(user["id"], to_user_id)
    except Exception as exc:
        print(f"send_invite state ERROR from={user.get('id')} to={to_user_id}: {type(exc).__name__}: {exc}")
        flash("Không thể kiểm tra trạng thái phòng lúc này. Vui lòng thử lại sau vài giây.", "danger")
        return redirect(url_for("players"))

    sender_room = state.get("room_a")
    receiver_room = state.get("room_b")
    blocker = send_invite_blocker(
        state,
        sender_id=user["id"],
        receiver_id=to_user_id,
        receiver_online=is_user_online_now(opponent),
        is_solo_waiting_room=is_solo_waiting_room,
    )
    if blocker:
        message, category, endpoint = SEND_INVITE_MESSAGES[blocker]
        flash(message, category)
        return redirect(url_for(endpoint))

    invite_result = execute_query(
        db.table("match_invites").insert({
            "from_user_id": user["id"],
            "to_user_id": to_user_id,
            "tier": tier,
            "status": "pending",
            "message": f'{user["display_name"]} mời {opponent["display_name"]} thi đấu hạng.',
            "expires_at": future_iso(INVITE_TIMEOUT_SECONDS),
            "updated_at": now_iso(),
        }),
        "send_match_invite",
    )
    invite = invite_result.data[0] if invite_result.data else None
    ttl_cache_delete("invites_raw")
    cache_delete("_rz_invites_all")
    cache_delete("_rz_current_pending_invites")
    if not invite:
        flash("Không thể gửi lời mời lúc này. Vui lòng thử lại.", "danger")
        return redirect(url_for("players"))

    # Chủ phòng phải được đưa vào phòng ngay sau khi bấm Mời đấu.
    # Nếu đã có phòng trống thì gắn lời mời vào phòng đó; nếu chưa có thì tạo phòng mới.
    if sender_room:
        room_result = execute_query(
            db.table("match_rooms").update({
                "invite_id": invite["id"],
                "note": f'Đã mời {opponent["display_name"]}. Đang chờ đối thủ chấp nhận.',
                "updated_at": now_iso(),
            }).eq("id", sender_room["id"]).eq("status", "waiting_ready"),
            "attach_invite_to_open_room",
        )
        room = room_result.data[0] if room_result.data else sender_room
    else:
        room_result = execute_query(
            db.table("match_rooms").insert({
                "invite_id": invite["id"],
                "host_user_id": user["id"],
                "guest_user_id": None,
                "team_tier": default_rank_room_team_tier(),
                "match_mode": MATCH_MODE_RANKED,
                "friendly_tier": "A",
                "status": "waiting_ready",
                "guest_ready": False,
                "note": f'Đã mời {opponent["display_name"]}. Đang chờ đối thủ chấp nhận.',
                "state_expires_at": None,
                "updated_at": now_iso(),
            }),
            "create_room_for_invite",
        )
        room = room_result.data[0] if room_result.data else None

    if not room:
        # Tránh để lại lời mời treo nếu tạo phòng thất bại.
        execute_query(
            db.table("match_invites").update({
                "status": "cancelled",
                "updated_at": now_iso(),
            }).eq("id", invite["id"]).eq("status", "pending"),
            "cancel_invite_after_room_error",
        )
        flash("Đã gửi lời mời nhưng không thể tạo phòng. Vui lòng thử lại.", "danger")
        return redirect(url_for("players"))

    flash(f'Đã mời {opponent["display_name"]}. Bạn đang ở trong phòng và chờ đối thủ chấp nhận.', "success")
    return redirect(url_for("room_detail", room_id=room["id"]))


def is_quick_match_invite(invite):
    """Return True only for invites generated by the Quick Match flow."""
    message = str((invite or {}).get("message") or "")
    return message.startswith("QUICK_MATCH|")


@app.route("/invites/quick-match", methods=["POST"])
@login_required
def quick_match_invite():
    user = current_user()
    payload = request.get_json(silent=True) or request.form or {}
    raw_excluded = payload.get("excluded_user_ids", [])
    if isinstance(raw_excluded, str):
        raw_excluded = [item for item in raw_excluded.split(",") if item]
    excluded_user_ids = {str(item).strip() for item in (raw_excluded or []) if str(item).strip()}
    if not system_feature_enabled("quick_match_enabled"):
        return jsonify({"ok": False, "message": "Tính năng Tìm Nhanh đang được Admin tắt."}), 403
    try:
        state = matchmaking_snapshot(user["id"])
    except Exception as exc:
        print(f"quick_match state ERROR user={user.get('id')}: {type(exc).__name__}: {exc}")
        return jsonify({"ok": False, "message": "Không thể kiểm tra trạng thái phòng lúc này."}), 503

    sender_room = state.get("room_a")
    if state.get("match_a") or not is_solo_waiting_room(sender_room, user["id"]):
        return jsonify({"ok": False, "message": "Tìm Nhanh chỉ dùng khi bạn đang ở phòng một mình."}), 409

    rooms = state.get("rooms") or []
    matches = state.get("matches") or []
    invites = state.get("invites") or []
    room_by_user = {}
    for room in rooms:
        for uid in (room.get("host_user_id"), room.get("guest_user_id")):
            if uid:
                room_by_user[str(uid)] = room
    busy_match_ids = {str(uid) for m in matches for uid in (m.get("player1_id"), m.get("player2_id")) if uid}
    # Chỉ người đang CHỦ ĐỘNG gửi một lời mời khác mới được xem là bận.
    # Người chỉ đang NHẬN một hay nhiều lời mời vẫn có thể tiếp tục nhận thêm
    # lời mời thủ công hoặc Tìm Nhanh. Khi họ chấp nhận một lời mời, luồng
    # respond_invite sẽ tự hủy các lời mời chờ còn lại để tránh vào hai phòng.
    outgoing_inviter_ids = {
        str(i.get("from_user_id"))
        for i in invites
        if i.get("from_user_id")
    }
    if str(user["id"]) in outgoing_inviter_ids:
        return jsonify({"ok": False, "message": "Bạn đang chờ một đối thủ phản hồi lời mời đã gửi."}), 409

    my_points = int(user.get("rank_points", 0) or 0)
    my_rank_level = get_rank_level(my_points)
    candidates = []
    online_total = 0
    busy_total = 0
    cooldown_total = 0

    # Tìm Nhanh phải đọc presence trực tiếp từ Supabase thay vì dùng danh sách
    # người chơi đã cache. Cache ngắn vẫn có thể làm một tài khoản vừa heartbeat
    # bị coi là offline trên instance Vercel khác. last_seen_at là nguồn xác thực
    # chính; is_online chỉ là cờ hiển thị nhanh.
    try:
        online_result = execute_query(
            db.table("users")
            .select("id,username,display_name,role,admin_level,account_status,rank_points,is_online,last_seen_at,matchmaking_cooldown_until"),
            "quick_match_live_players",
            attempts=3,
        )
        quick_players = [dict(row) for row in (online_result.data or [])]
    except Exception as exc:
        print(f"quick_match players ERROR user={user.get('id')}: {type(exc).__name__}: {exc}")
        return jsonify({"ok": False, "message": "Không thể đọc danh sách người chơi online lúc này."}), 503

    presence_cutoff = now_dt() - timedelta(seconds=ONLINE_TIMEOUT_SECONDS)
    for opponent in quick_players:
        oid = str(opponent.get("id") or "")
        if not oid or oid == str(user["id"]) or oid in excluded_user_ids:
            continue
        role = str(opponent.get("role") or "").strip().lower()
        admin_level = str(opponent.get("admin_level") or "").strip().lower()
        if role not in {"player", "admin"} and admin_level not in {"owner", "admin"}:
            continue
        if opponent.get("account_status", "approved") != "approved":
            continue
        seen = parse_dt(opponent.get("last_seen_at"))
        # Admin chọn Offline vẫn có last_seen_at mới vì thao tác đổi trạng thái
        # và heartbeat ẩn tiếp tục cập nhật thời gian. Vì vậy Tìm Nhanh phải
        # kiểm tra đồng thời cờ is_online; chỉ dựa last_seen_at sẽ gửi lời mời
        # giả tới Admin đang ẩn trạng thái, trong khi phía nhận không nhận popup.
        if opponent.get("is_online") is not True or not seen or seen < presence_cutoff:
            continue
        online_total += 1
        # Có lời mời ĐẾN không làm người chơi bị loại khỏi danh sách.
        # Chỉ loại khi chính họ đang có lời mời ĐI chờ phản hồi.
        if oid in busy_match_ids or oid in outgoing_inviter_ids:
            busy_total += 1
            continue
        opponent_room = room_by_user.get(oid)
        if opponent_room and not is_solo_waiting_room(opponent_room, oid):
            busy_total += 1
            continue
        opponent_points = int(opponent.get("rank_points", 0) or 0)
        gap = abs(opponent_points - my_points)
        same_rank = get_rank_level(opponent_points) == my_rank_level

        # Thứ tự ưu tiên Tìm Nhanh:
        # 0. Cùng bậc Rank (luôn ưu tiên trước)
        # 1. Khác Rank, chênh tối đa 300 RP
        # 2. Khác Rank, chênh 301-500 RP
        # 3. Khác Rank, chênh 501-1.000 RP
        # 4. Khác Rank, chênh 1.001-2.000 RP
        # Người khác Rank chênh quá 2.000 RP không được chọn.
        priority_group = quick_match_priority_group(same_rank=same_rank, points_gap=gap)
        if priority_group is None:
            continue

        # Trong cùng nhóm: ưu tiên RP gần nhất, sau đó người hoạt động
        # gần đây hơn, cuối cùng mới dùng tên để kết quả ổn định.
        sort_key = build_candidate_sort_key(
            priority_group=priority_group,
            points_gap=gap,
            last_seen=seen,
            display_name=opponent.get("display_name") or opponent.get("username") or "",
        )
        candidates.append((*sort_key, opponent))

    if not candidates:
        if online_total == 0:
            message = "Hiện không có người chơi nào khác đang online."
        elif busy_total:
            message = "Người chơi đang online hiện đều bận, phòng đã đủ người hoặc đang chờ đối thủ phản hồi lời mời đã gửi."
        elif cooldown_total:
            message = "Người chơi đang online hiện đều trong thời gian chờ ghép trận."
        else:
            message = "Hiện chưa có đối thủ phù hợp đang online."
        return jsonify({"ok": False, "message": message}), 404

    candidates.sort(key=lambda item: (item[0], item[1], item[2], item[3]))
    opponent = candidates[0][4]
    invite_result = execute_query(
        db.table("match_invites").insert({
            "from_user_id": user["id"], "to_user_id": opponent["id"],
            "tier": SMART_RANDOM_MODE, "status": "pending",
            "message": f'QUICK_MATCH|{user["display_name"]} tìm nhanh và mời {opponent["display_name"]} thi đấu hạng.',
            "expires_at": future_iso(INVITE_TIMEOUT_SECONDS), "updated_at": now_iso(),
        }), "quick_match_create_invite",
    )
    invite = invite_result.data[0] if invite_result.data else None
    if not invite:
        return jsonify({"ok": False, "message": "Không thể gửi lời mời lúc này."}), 500
    attach_result = execute_query(
        db.table("match_rooms").update({
            "invite_id": invite["id"],
            "note": "Đã tìm thấy đối thủ phù hợp. Đang chờ phản hồi.",
            "updated_at": now_iso(),
        }).eq("id", sender_room["id"]).eq("status", "waiting_ready").is_("guest_user_id", "null"),
        "quick_match_attach_invite",
    )
    if not attach_result.data:
        execute_query(
            db.table("match_invites").update({
                "status": "cancelled",
                "updated_at": now_iso(),
            }).eq("id", invite["id"]).eq("status", "pending"),
            "quick_match_cancel_unattached_invite",
            attempts=2,
        )
        ttl_cache_delete("invites_raw")
        cache_delete("_rz_invites_all")
        return jsonify({
            "ok": False,
            "message": "Phòng vừa thay đổi nên lời mời chưa được gửi. Vui lòng bấm Tìm Nhanh lại.",
        }), 409
    ttl_cache_delete("invites_raw")
    cache_delete("_rz_invites_all")
    return jsonify({
        "ok": True,
        "invite_id": invite.get("id"),
        "opponent_id": opponent.get("id"),
        "message": "Đã tìm thấy đối thủ. Đang chờ phản hồi...",
    })


@app.route("/api/invites/quick-match/<invite_id>/status")
@login_required
def quick_match_invite_status(invite_id):
    """Return the live state of a Quick Match invitation.

    This endpoint also reconciles stale pending rows. A Quick Match chain must
    stop when the sender's room is already filled, and must move on when the
    selected opponent goes offline or becomes unavailable.
    """
    user = current_user()
    invite = get_invite(invite_id)
    if not invite or str(invite.get("from_user_id")) != str(user.get("id")) or not is_quick_match_invite(invite):
        return jsonify({
            "ok": False,
            "status": "missing",
            "continue_search": False,
            "message": "Không tìm thấy lượt Tìm Nhanh.",
        }), 404

    status = str(invite.get("status") or "")
    continue_search = status in {"rejected", "expired", "cancelled"}
    reason = status

    if status == "pending":
        sender_id = invite.get("from_user_id")
        opponent_id = invite.get("to_user_id")
        now = now_dt()

        room_result = execute_query(
            db.table("match_rooms")
              .select("id,host_user_id,guest_user_id,status,invite_id")
              .eq("host_user_id", sender_id)
              .in_("status", ["waiting_ready", "playing", "friendly_playing", "waiting_result_confirm"])
              .order("updated_at", desc=True)
              .limit(1),
            "quick_match_status_sender_room",
            attempts=2,
        )
        sender_room = dict(room_result.data[0]) if room_result.data else None

        # A different player has already entered the sender's room. The search
        # is complete and must not continue to invite more people.
        if sender_room and sender_room.get("guest_user_id"):
            guest_id = str(sender_room.get("guest_user_id"))
            next_status = "accepted" if guest_id == str(opponent_id) else "cancelled"
            execute_query(
                db.table("match_invites").update({
                    "status": next_status,
                    "updated_at": now_iso(),
                }).eq("id", invite_id).eq("status", "pending"),
                "quick_match_close_when_room_filled",
                attempts=2,
            )
            status = "room_filled"
            reason = "room_filled"
            continue_search = False
        elif not sender_room or not is_solo_waiting_room(sender_room, sender_id):
            execute_query(
                db.table("match_invites").update({
                    "status": "cancelled",
                    "updated_at": now_iso(),
                }).eq("id", invite_id).eq("status", "pending"),
                "quick_match_cancel_sender_unavailable",
                attempts=2,
            )
            status = "sender_unavailable"
            reason = "sender_unavailable"
            continue_search = False
        else:
            opponent_result = execute_query(
                db.table("users")
                  .select("id,is_online,last_seen_at,role,admin_level,account_status")
                  .eq("id", opponent_id)
                  .limit(1),
                "quick_match_status_opponent_presence",
                attempts=2,
            )
            opponent = dict(opponent_result.data[0]) if opponent_result.data else None
            seen = parse_dt((opponent or {}).get("last_seen_at"))
            presence_cutoff = now - timedelta(seconds=ONLINE_TIMEOUT_SECONDS)
            opponent_online = bool(
                opponent
                and (opponent.get("account_status", "approved") == "approved")
                and seen
                and seen >= presence_cutoff
                and opponent.get("is_online") is not False
            )

            if not opponent_online:
                execute_query(
                    db.table("match_invites").update({
                        "status": "cancelled",
                        "updated_at": now_iso(),
                    }).eq("id", invite_id).eq("status", "pending"),
                    "quick_match_cancel_offline_opponent",
                    attempts=2,
                )
                status = "opponent_offline"
                reason = "opponent_offline"
                continue_search = True
            else:
                availability = matchmaking_snapshot(opponent_id)
                opponent_room = availability.get("room_a")
                opponent_busy = bool(
                    availability.get("match_a")
                    or (opponent_room and not is_solo_waiting_room(opponent_room, opponent_id))
                )
                other_pending = any(
                    str(row.get("id")) != str(invite_id)
                    and str(opponent_id) in {str(row.get("from_user_id")), str(row.get("to_user_id"))}
                    for row in (availability.get("invites") or [])
                )
                if opponent_busy or other_pending:
                    execute_query(
                        db.table("match_invites").update({
                            "status": "cancelled",
                            "updated_at": now_iso(),
                        }).eq("id", invite_id).eq("status", "pending"),
                        "quick_match_cancel_unavailable_opponent",
                        attempts=2,
                    )
                    status = "opponent_unavailable"
                    reason = "opponent_unavailable"
                    continue_search = True

    if status != "pending":
        ttl_cache_delete("invites_raw")
        cache_delete("_rz_invites_all")
        cache_delete("_rz_current_pending_invites")

    return jsonify({
        "ok": True,
        "status": status,
        "reason": reason,
        "continue_search": bool(continue_search),
        "opponent_id": invite.get("to_user_id"),
        "expires_in_seconds": int(invite.get("expires_in_seconds") or 0),
    })


@app.route("/invites/respond/<invite_id>", methods=["POST"])
@login_required
def respond_invite(invite_id):
    user = current_user()
    action = request.form.get("action")
    invite = get_invite(invite_id)

    if not invite:
        flash("Không tìm thấy lời mời.", "danger")
        return redirect(url_for("invites"))

    if invite["to_user_id"] != user["id"]:
        flash("Bạn không có quyền xử lý lời mời này.", "danger")
        return redirect(url_for("invites"))

    if invite["status"] == "expired":
        flash("Lời mời đã hết hạn sau 60 giây. Hãy nhờ đối thủ gửi lời mời mới.", "warning")
        return redirect(url_for("dashboard"))

    if invite["status"] != "pending":
        flash("Lời mời này đã được xử lý.", "warning")
        return redirect(url_for("invites"))

    if action == "reject":
        db.table("match_invites").update({"status": "rejected", "updated_at": now_iso()}).eq("id", invite_id).execute()
        ttl_cache_delete("invites_raw")
        cache_delete("_rz_invites_all")
        if is_quick_match_invite(invite):
            flash("Đã từ chối lời mời Tìm Nhanh.", "success")
        else:
            flash("Đã từ chối lời mời.", "success")
        return redirect(url_for("invites"))

    if action != "accept":
        flash("Hành động không hợp lệ.", "danger")
        return redirect(url_for("invites"))

    receiver_match = active_match_for_user(user["id"])
    receiver_room = active_room_for_user(user["id"])
    inviter_id = invite.get("from_user_id")
    inviter_match = active_match_for_user(inviter_id)
    inviter_room = active_room_for_user(inviter_id)
    accept_blocker = accept_invite_blocker(
        receiver_match=receiver_match,
        receiver_room=receiver_room,
        receiver_id=user["id"],
        inviter_match=inviter_match,
        inviter_room=inviter_room,
        inviter_id=inviter_id,
        is_solo_waiting_room=is_solo_waiting_room,
    )
    if accept_blocker == "receiver_active_match":
        flash("Bạn đang có trận chưa hoàn tất nên không thể nhận lời mời.", "warning")
        return redirect(url_for("dashboard"))
    if accept_blocker == "receiver_room_busy":
        flash("Phòng của bạn đã có đủ 2 người hoặc đã bắt đầu nên không thể nhận lời mời khác.", "warning")
        return redirect(url_for("dashboard"))
    if accept_blocker == "inviter_unavailable":
        execute_query(
            db.table("match_invites").update({
                "status": "cancelled",
                "updated_at": now_iso(),
            }).eq("id", invite_id),
            "cancel_stale_invite_busy_sender",
        )
        flash("Người mời đang ở phòng hoặc trận khác. Lời mời này đã hết hiệu lực.", "warning")
        return redirect(url_for("dashboard"))

    room = None
    target_room_created = False
    try:
        if inviter_room:
            attach_result = execute_query(
                db.table("match_rooms").update({
                    "invite_id": invite_id,
                    "guest_user_id": invite["to_user_id"],
                    "guest_ready": False,
                    "note": "Đối thủ đã vào phòng. Khách chưa sẵn sàng.",
                    "state_expires_at": None,
                    "updated_at": now_iso(),
                })
                .eq("id", inviter_room["id"])
                .eq("status", "waiting_ready")
                .is_("guest_user_id", "null"),
                "attach_guest_to_open_room",
            )
            room = attach_result.data[0] if attach_result.data else None
        else:
            create_result = execute_query(
                db.table("match_rooms").insert({
                    "invite_id": invite_id,
                    "host_user_id": invite["from_user_id"],
                    "guest_user_id": invite["to_user_id"],
                    "team_tier": default_rank_room_team_tier(),
                    "match_mode": MATCH_MODE_RANKED,
                    "friendly_tier": "A",
                    "status": "waiting_ready",
                    "guest_ready": False,
                    "note": "Đối thủ đã vào phòng. Khách chưa sẵn sàng.",
                    "state_expires_at": None,
                    "updated_at": now_iso(),
                }),
                "create_room_when_accepting_invite",
            )
            room = create_result.data[0] if create_result.data else None
            target_room_created = bool(room)

        if not room:
            flash("Phòng của người mời vừa có người khác tham gia. Lời mời không còn hiệu lực.", "warning")
            return redirect(url_for("dashboard"))

        # Người nhận có thể đang làm chủ một phòng trống. Khi nhận lời, đóng phòng cũ
        # trước khi hoàn tất lời mời để mỗi tài khoản chỉ còn đúng một phòng active.
        if receiver_room and str(receiver_room.get("id")) != str(room.get("id")):
            old_invite_id = receiver_room.get("invite_id")
            delete_result = execute_query(
                db.table("match_rooms").delete()
                .eq("id", receiver_room["id"])
                .eq("host_user_id", user["id"])
                .eq("status", "waiting_ready")
                .is_("guest_user_id", "null"),
                "close_receiver_solo_room_on_accept",
            )
            if not delete_result.data:
                raise RuntimeError("Không thể đóng phòng cũ của người nhận")
            if old_invite_id and str(old_invite_id) != str(invite_id):
                execute_query(
                    db.table("match_invites").update({
                        "status": "cancelled",
                        "updated_at": now_iso(),
                    }).eq("id", old_invite_id).eq("status", "pending"),
                    "cancel_receiver_old_room_invite",
                )

        execute_query(
            db.table("match_invites").update({
                "status": "accepted",
                "updated_at": now_iso(),
            }).eq("id", invite_id).eq("status", "pending"),
            "accept_match_invite",
        )
        # Hủy các lời mời chờ khác của người nhận để popup cũ không xuất hiện lại.
        execute_query(
            db.table("match_invites").update({
                "status": "cancelled",
                "updated_at": now_iso(),
            }).eq("to_user_id", user["id"]).eq("status", "pending").neq("id", invite_id),
            "cancel_other_incoming_invites_after_accept",
            attempts=1,
        )
        execute_query(
            db.table("match_invites").update({
                "status": "cancelled",
                "updated_at": now_iso(),
            }).eq("from_user_id", user["id"]).eq("status", "pending").neq("id", invite_id),
            "cancel_receiver_outgoing_invites_after_accept",
            attempts=1,
        )
        # Khi phòng của người mời đã có khách, mọi lời mời khác do người
        # mời gửi (bao gồm Tìm Nhanh) phải kết thúc để không còn trạng thái treo.
        execute_query(
            db.table("match_invites").update({
                "status": "cancelled",
                "updated_at": now_iso(),
            }).eq("from_user_id", inviter_id).eq("status", "pending").neq("id", invite_id),
            "cancel_inviter_other_outgoing_after_accept",
            attempts=1,
        )
    except Exception as exc:
        print(f"respond_invite accept ERROR invite={invite_id}: {type(exc).__name__}: {exc}")
        # Hoàn tác việc gắn khách nếu đóng phòng cũ thất bại.
        try:
            if room:
                if target_room_created:
                    execute_query(
                        db.table("match_rooms").delete().eq("id", room["id"]),
                        "rollback_created_invite_room",
                        attempts=1,
                    )
                else:
                    execute_query(
                        db.table("match_rooms").update({
                            "guest_user_id": None,
                            "guest_ready": False,
                            "invite_id": invite_id,
                            "note": "Đang chờ đối thủ chấp nhận lời mời.",
                            "updated_at": now_iso(),
                        }).eq("id", room["id"]).eq("guest_user_id", user["id"]),
                        "rollback_attached_invite_guest",
                        attempts=1,
                    )
        except Exception as rollback_exc:
            print(f"respond_invite rollback warning: {rollback_exc}")
        flash("Không thể chuyển phòng an toàn lúc này. Phòng cũ của bạn vẫn được giữ nguyên; vui lòng thử lại.", "danger")
        return redirect(url_for("dashboard"))

    ttl_cache_delete("rooms_raw")
    ttl_cache_delete("invites_raw")
    cache_delete("_rz_rooms_all")
    cache_delete("_rz_invites_all")
    cache_delete("_rz_current_pending_invites")
    flash("Đã nhận lời mời. Phòng cũ một người của bạn đã được đóng và bạn đã vào phòng của đối thủ. Hãy bấm Sẵn sàng khi đã chuẩn bị xong.", "success")
    return redirect(url_for("room_detail", room_id=room["id"]))


@app.route("/invites/cancel/<invite_id>", methods=["POST"])
@login_required
def cancel_invite(invite_id):
    user = current_user()
    invite = get_invite(invite_id)

    if not invite:
        flash("Không tìm thấy lời mời.", "danger")
        return redirect(url_for("invites"))

    if invite["from_user_id"] != user["id"]:
        flash("Bạn không có quyền hủy lời mời này.", "danger")
        return redirect(url_for("invites"))

    if invite["status"] != "pending":
        flash("Lời mời này đã được xử lý.", "warning")
        return redirect(url_for("invites"))

    db.table("match_invites").update({"status": "cancelled", "updated_at": now_iso()}).eq("id", invite_id).execute()
    flash("Đã hủy lời mời.", "success")
    return redirect(url_for("invites"))


# =========================
# Rooms
# =========================


# =========================
# Legacy / history routes
# =========================









# =========================
# Core modules extracted from legacy app.py (V1.3.52)
# =========================
from modules.core import achievements as _core_achievements
from modules.core import rank_team_service as _core_rank_team_service
from modules.core import room_runtime as _core_room_runtime
from modules.core import user_repository as _core_user_repository
from modules.core import match_repository as _core_match_repository
from modules.core import social_runtime as _core_social_runtime
from modules.core import matchmaking_runtime as _core_matchmaking_runtime

_CORE_MODULES = (
    _core_achievements, _core_rank_team_service, _core_room_runtime,
    _core_user_repository, _core_match_repository, _core_social_runtime,
    _core_matchmaking_runtime,
)
for _core_module in _CORE_MODULES:
    _core_module.configure(globals())
    for _core_name in _core_module.EXPORTED_NAMES:
        globals()[_core_name] = getattr(_core_module, _core_name)
# Second pass refreshes cross-module dependencies after every exported name exists.
for _core_module in _CORE_MODULES:
    _core_module.configure(globals())


# =========================
# Đăng ký module chức năng
# =========================
def redirect_admin(tab="overview"):
    """Điểm điều hướng Admin dùng chung cho mọi module quản trị."""
    return redirect(url_for("admin") + f"#{tab}")


# Nạp dịch vụ theo thứ tự dependency: thông báo -> khóa -> kết quả -> phát lại -> xóa an toàn.
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
from modules import rank_modes as _rank_modes_module
from modules import rank_series as _rank_series_module
from modules import read_model_service as _read_model_service
from modules import blackbox as _blackbox_module

for _service_module in (
    _notification_service,
    _forfeit_history_service,
    _ranking_lock_service,
    _daily_rank_limit_service,
    _repeat_opponent_rp_service,
    _weekly_rp_rewards_service,
    _zcoin_module,
    _daily_checkin_module,
    _gift_codes_module,
    _rank_modes_module,
    _rank_series_module,
    _parsec_room_service,
    _match_result_service,
    _ranking_rebuild_service,
    _data_cleanup_service,
    _inactivity_rp_service,
    _blackbox_module,
):
    _service_module.configure(globals())
    for _service_name in _service_module.EXPORTED_NAMES:
        globals()[_service_name] = getattr(_service_module, _service_name)

# Core modules that depend on later service exports must be refreshed once
# those helpers exist in app globals. Room needs Rank Mode helpers; Match
# Repository needs forfeit/series helpers used by History and Profile decorators.
_core_room_runtime.configure(globals())
_core_match_repository.configure(globals())

# Read-model V1.3.34 không export route; chỉ cung cấp các SELECT nhanh.
_read_model_service.configure(globals())
for _read_model_name in (
    "load_match_report", "load_recent_form_map", "load_player_profile_summary",
    "load_user_matches", "load_h2h_matches", "load_pair_stats", "load_user_ip_cache",
):
    globals()[_read_model_name] = getattr(_read_model_service, _read_model_name)


# Route phòng đấu.
from modules.room_access_routes import register_routes as _register_room_access_routes
from modules.room_rematch_routes import register_routes as _register_room_rematch_routes
from modules.room_team_routes import register_routes as _register_room_team_routes
from modules.room_result_routes import register_routes as _register_room_result_routes
from modules.rank_series import register_routes as _register_rank_series_routes
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
from modules.blackbox import register_routes as _register_blackbox_routes

# Route Admin.
from modules.admin_system_routes import register_routes as _register_admin_system_routes
from modules.admin_dashboard_routes import register_routes as _register_admin_dashboard_routes
from modules.admin_account_routes import register_routes as _register_admin_account_routes
from modules.admin_match_routes import register_routes as _register_admin_match_routes
from modules.admin_player_routes import register_routes as _register_admin_player_routes
from modules.admin_data_routes import register_routes as _register_admin_data_routes

for _route_registrar in (
    _register_room_access_routes,
    _register_room_rematch_routes,
    _register_room_team_routes,
    _register_room_result_routes,
    _register_rank_series_routes,
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
    _register_blackbox_routes,
    _register_admin_system_routes,
    _register_admin_dashboard_routes,
    _register_admin_account_routes,
    _register_admin_match_routes,
    _register_admin_player_routes,
    _register_admin_data_routes,
):
    _route_registrar(globals())

del _service_module, _service_name, _route_registrar, _read_model_name, _evidence_name, _settings_name


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
