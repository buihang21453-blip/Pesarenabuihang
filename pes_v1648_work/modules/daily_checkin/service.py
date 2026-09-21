"""Nghiệp vụ điểm danh 7 ngày và dữ liệu hiển thị cho member."""

from datetime import datetime, timedelta, timezone

from . import repository

REWARD_SCHEDULE = (100, 120, 150, 180, 220, 280, 450)
EXPORTED_NAMES = (
    "DAILY_CHECKIN_REWARDS",
    "build_daily_checkin_status",
    "claim_daily_reward",
)
DAILY_CHECKIN_REWARDS = REWARD_SCHEDULE


def configure(context):
    globals().update(context)


def _safe_int(value, default=0):
    try:
        return int(value or 0)
    except (TypeError, ValueError, OverflowError):
        return default


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value)[:10]).date()
    except Exception:
        return None


def _today_vn():
    return datetime.now(timezone(timedelta(hours=7))).date()


def build_daily_checkin_status(user_id):
    """Tính trạng thái hiển thị; RPC vẫn là nơi quyết định cuối cùng."""
    rows = repository.list_recent_checkins(user_id, limit=14)
    today = _today_vn()
    latest = rows[0] if rows else None
    latest_date = _parse_date((latest or {}).get("checkin_date"))
    latest_streak = max(0, _safe_int((latest or {}).get("streak_day")))
    claimed_today = latest_date == today

    if claimed_today:
        current_day = min(max(latest_streak, 1), 7)
        next_day = 1 if current_day >= 7 else current_day + 1
    elif latest_date == today - timedelta(days=1):
        current_day = min(max(latest_streak, 0), 7)
        next_day = 1 if current_day >= 7 else current_day + 1
    else:
        current_day = 0
        next_day = 1

    days = []
    for index, reward in enumerate(REWARD_SCHEDULE, start=1):
        days.append({
            "day": index,
            "reward": reward,
            "claimed": claimed_today and index <= current_day,
            "completed": (not claimed_today) and current_day > 0 and index <= current_day,
            "next": (not claimed_today) and index == next_day,
            "today": claimed_today and index == current_day,
        })

    return {
        "ready": True,
        "claimed_today": claimed_today,
        "current_day": current_day,
        "next_day": next_day,
        "next_reward": REWARD_SCHEDULE[next_day - 1],
        "days": days,
        "recent": rows[:7],
    }


def claim_daily_reward(user_id, request_key):
    payload = repository.claim_daily_checkin(user_id, request_key)
    if not payload:
        raise RuntimeError("Supabase không trả về kết quả điểm danh.")
    payload["reward_amount"] = max(0, _safe_int(payload.get("reward_amount")))
    payload["streak_day"] = min(max(1, _safe_int(payload.get("streak_day"), 1)), 7)
    payload["balance_after"] = max(0, _safe_int(payload.get("balance_after")))
    payload["duplicate"] = bool(payload.get("duplicate"))
    return payload
