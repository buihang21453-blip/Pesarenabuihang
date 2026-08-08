"""Giảm RP khi người chơi lâu không thi đấu Rank.

Mốc không hoạt động được tính từ trận Rank gần nhất, không tính từ lần mở web,
đăng nhập hoặc heartbeat. Người chưa từng đá Rank dùng ngày tạo tài khoản làm
mốc ban đầu. Trạng thái xử lý được lưu trong system_settings để không trừ lặp.
"""
from __future__ import annotations

from datetime import datetime, timezone
import time
from threading import Lock

EXPORTED_NAMES = [
    "process_inactivity_for_user",
    "process_inactivity_decay_batch",
]

DECAY_START_DAY = 10
SECOND_TIER_START_DAY = 20
DECAY_END_DAY = 30
FIRST_DAILY_PENALTY = 10
SECOND_DAILY_PENALTY = 20
RP_FLOOR = 500
WARNING_DAYS = {7: 3, 8: 2, 9: 1}
BATCH_SETTING_KEY = "rp_inactivity_decay_batch"
USER_SETTING_PREFIX = "rp_inactivity_decay_user_"
BATCH_INTERVAL_SECONDS = 6 * 60 * 60
RANK_ACTIVITY_STATUSES = {"playing", "waiting_confirm", "disputed", "confirmed"}

# Gate RAM theo warm instance. Nếu batch chưa đến hạn, các request tiếp theo trên
# cùng instance không cần đọc system_settings thêm lần nữa. Database vẫn là khóa
# nguồn sự thật giữa nhiều instance Vercel.
_batch_gate_lock = Lock()
_batch_gate_until = 0.0


def configure(context):
    globals().update(context)


def _aware_dt(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _is_rank_activity_match(match):
    status = str((match or {}).get("status") or "").strip().lower()
    if status in RANK_ACTIVITY_STATUSES:
        return True
    if status == "cancelled":
        checker = globals().get("is_forfeit_match")
        if callable(checker):
            try:
                return bool(checker(match))
            except Exception:
                pass
        note = str((match or {}).get("note") or "").casefold()
        return "[forfeit:" in note or "bỏ cuộc" in note
    return False


def _latest_rank_match_at(user_id):
    if not user_id:
        return None
    try:
        result = execute_query(
            db.table("matches")
            .select("id,status,note,loser_id,created_at")
            .or_(f"player1_id.eq.{user_id},player2_id.eq.{user_id}")
            .order("created_at", desc=True)
            .limit(20),
            "latest_rank_match_for_inactivity",
            attempts=2,
        )
        for match in result.data or []:
            if _is_rank_activity_match(match):
                return _aware_dt(match.get("created_at"))
    except Exception as exc:
        print(f"latest rank match warning user={user_id}: {exc}")
    return None


def _rank_activity_anchor(user):
    supplied = _aware_dt(user.get("last_rank_match_at"))
    if supplied:
        return supplied
    latest = _latest_rank_match_at(user.get("id"))
    if latest:
        return latest
    return _aware_dt(user.get("created_at"))


def _inactive_days(user, now=None):
    now = now or datetime.now(timezone.utc)
    last_rank_activity = _rank_activity_anchor(user)
    if not last_rank_activity:
        return 0, None
    return max(0, int((now - last_rank_activity).total_seconds() // 86400)), last_rank_activity


def _target_penalty(inactive_days):
    days = max(0, min(int(inactive_days or 0), DECAY_END_DAY))
    if days < DECAY_START_DAY:
        return 0
    first_days = min(days, SECOND_TIER_START_DAY - 1) - DECAY_START_DAY + 1
    second_days = max(0, days - SECOND_TIER_START_DAY + 1)
    return first_days * FIRST_DAILY_PENALTY + second_days * SECOND_DAILY_PENALTY


def _setting_key(user_id):
    return f"{USER_SETTING_PREFIX}{user_id}"


def _load_state(user_id):
    try:
        result = execute_query(
            db.table("system_settings").select("setting_value")
            .eq("setting_key", _setting_key(user_id)).limit(1),
            "load_inactivity_decay_state", attempts=2,
        )
        value = (result.data or [{}])[0].get("setting_value") if result.data else {}
        return dict(value or {}) if isinstance(value, dict) else {}
    except Exception as exc:
        print(f"load inactivity state warning: {exc}")
        return {}


def _save_state(user_id, state):
    execute_query(
        db.table("system_settings").upsert({
            "setting_key": _setting_key(user_id),
            "setting_value": state,
            "updated_at": now_iso(),
        }, on_conflict="setting_key"),
        "save_inactivity_decay_state", attempts=2,
    )


def process_inactivity_for_user(user, now=None):
    if not user or not user.get("id") or user.get("role") == "admin" or is_admin_user(user):
        return {"ok": True, "deducted": 0, "inactive_days": 0}

    inactive_days, last_rank_activity = _inactive_days(user, now=now)
    if not last_rank_activity:
        return {"ok": True, "deducted": 0, "inactive_days": 0}

    user_id = user.get("id")
    anchor = last_rank_activity.isoformat()
    state = _load_state(user_id)

    # Một trận Rank mới tạo ra anchor mới và bắt đầu lại chu kỳ suy giảm RP.
    if state.get("rank_activity_anchor") != anchor:
        state = {
            "rank_activity_anchor": anchor,
            "applied_penalty": 0,
            "warning_remaining": [],
        }

    warning_remaining = {int(item) for item in (state.get("warning_remaining") or []) if str(item).isdigit()}
    remaining = WARNING_DAYS.get(inactive_days)
    if remaining and remaining not in warning_remaining:
        create_user_notification(
            user_id,
            "Cảnh báo RP do không thi đấu Rank",
            f"Còn {remaining} ngày trước khi bắt đầu bị trừ RP. Hãy hoàn thành một trận Rank để đặt lại thời gian không hoạt động.",
            "/rooms",
            "rp_inactivity_warning",
        )
        warning_remaining.add(remaining)

    target = _target_penalty(inactive_days)
    already_applied = max(0, int(state.get("applied_penalty") or 0))
    pending = max(0, target - already_applied)
    current_rp = max(0, int(user.get("rank_points") or 0))
    actual = min(pending, max(0, current_rp - RP_FLOOR))

    if actual > 0:
        new_rp = max(RP_FLOOR, current_rp - actual)
        execute_query(
            db.table("users").update({"rank_points": new_rp}).eq("id", user_id),
            "apply_inactivity_rp_decay", attempts=2,
        )
        create_user_notification(
            user_id,
            "RP bị trừ do không thi đấu Rank",
            f"Bạn đã {inactive_days} ngày không thi đấu Rank và bị trừ {actual} RP. RP hiện tại: {new_rp}. Mức sàn bảo vệ là {RP_FLOOR} RP.",
            "/ranking",
            "rp_inactivity_decay",
        )

    state.update({
        "rank_activity_anchor": anchor,
        "applied_penalty": target,
        "warning_remaining": sorted(warning_remaining),
        "last_inactive_days": inactive_days,
        "last_processed_at": now_iso(),
    })
    _save_state(user_id, state)
    return {"ok": True, "deducted": actual, "inactive_days": inactive_days}


def _batch_due():
    global _batch_gate_until

    mono_now = time.monotonic()
    if mono_now < _batch_gate_until:
        return False

    with _batch_gate_lock:
        mono_now = time.monotonic()
        if mono_now < _batch_gate_until:
            return False

        now_ts = int(time.time())
        try:
            result = execute_query(
                db.table("system_settings").select("setting_value")
                .eq("setting_key", BATCH_SETTING_KEY).limit(1),
                "load_inactivity_batch_state", attempts=1,
            )
            value = (result.data or [{}])[0].get("setting_value") if result.data else {}
            last_run = int((value or {}).get("last_run_ts") or 0) if isinstance(value, dict) else 0
            elapsed = max(0, now_ts - last_run)
            if elapsed < BATCH_INTERVAL_SECONDS:
                _batch_gate_until = mono_now + max(30, BATCH_INTERVAL_SECONDS - elapsed)
                return False

            execute_query(
                db.table("system_settings").upsert({
                    "setting_key": BATCH_SETTING_KEY,
                    "setting_value": {"last_run_ts": now_ts},
                    "updated_at": now_iso(),
                }, on_conflict="setting_key"),
                "claim_inactivity_batch", attempts=1,
            )
            _batch_gate_until = mono_now + BATCH_INTERVAL_SECONDS
            return True
        except Exception as exc:
            # Tránh tạo bão retry khi Supabase tạm thời lỗi.
            _batch_gate_until = mono_now + 60
            print(f"inactivity batch lock warning: {exc}")
            return False


def _latest_rank_activity_map():
    """Nạp một lần lịch sử gần đây để batch không tạo một query cho mỗi user."""
    latest = {}
    try:
        result = execute_query(
            db.table("matches")
            .select("player1_id,player2_id,status,note,loser_id,created_at")
            .order("created_at", desc=True)
            .limit(20000),
            "list_rank_matches_for_inactivity_batch", attempts=2,
        )
        for match in result.data or []:
            if not _is_rank_activity_match(match):
                continue
            created = match.get("created_at")
            for user_id in (match.get("player1_id"), match.get("player2_id")):
                key = str(user_id or "")
                if key and key not in latest:
                    latest[key] = created
    except Exception as exc:
        print(f"load rank activity map warning: {exc}")
    return latest


def process_inactivity_decay_batch(force=False):
    if db is None or (not force and not _batch_due()):
        return {"ok": True, "processed": 0, "deducted": 0}
    processed = 0
    deducted = 0
    try:
        result = execute_query(
            db.table("users")
            .select("id,role,admin_level,rank_points,created_at")
            .eq("account_status", "approved")
            .order("created_at", desc=False)
            .limit(2000),
            "list_users_for_inactivity_decay", attempts=2,
        )
        latest_map = _latest_rank_activity_map()
        now = datetime.now(timezone.utc)
        for row in result.data or []:
            try:
                user = dict(row)
                user["last_rank_match_at"] = latest_map.get(str(user.get("id")))
                outcome = process_inactivity_for_user(user, now=now)
                processed += 1
                deducted += int(outcome.get("deducted") or 0)
            except Exception as exc:
                print(f"process inactivity user warning: {exc}")
    except Exception as exc:
        print(f"process inactivity batch warning: {exc}")
    return {"ok": True, "processed": processed, "deducted": deducted}
