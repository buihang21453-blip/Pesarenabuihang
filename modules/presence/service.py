"""Pure presence rules shared by Players, Invite and Quick Match.

This module deliberately has no Flask/Supabase dependency so the online decision
can be tested independently from routes and rendering.
"""
from datetime import timedelta

DEFAULT_ONLINE_TIMEOUT_SECONDS = 120


def evaluate_presence(user, *, now, parse_datetime, timeout_seconds=DEFAULT_ONLINE_TIMEOUT_SECONDS):
    """Return a normalized presence decision with a reason code."""
    user = user or {}
    if not bool(user.get("is_online")):
        return {"online": False, "reason": "flag_offline", "age_seconds": None}

    seen = parse_datetime(user.get("last_seen_at"))
    if not seen:
        return {"online": False, "reason": "missing_last_seen", "age_seconds": None}

    age = max(0.0, (now - seen).total_seconds())
    cutoff = now - timedelta(seconds=int(timeout_seconds))
    if seen < cutoff:
        return {"online": False, "reason": "heartbeat_timeout", "age_seconds": int(age)}

    return {"online": True, "reason": "online", "age_seconds": int(age)}


def is_online(user, *, now, parse_datetime, timeout_seconds=DEFAULT_ONLINE_TIMEOUT_SECONDS):
    return bool(evaluate_presence(
        user,
        now=now,
        parse_datetime=parse_datetime,
        timeout_seconds=timeout_seconds,
    )["online"])
