"""Pure Rank daily policy shared by live results and chronological Admin replay.

Daily cap applies ONLY to normal match RP; streak and weekly activity bonuses
are separate. Once normal RP reaches the cap, further match losses cost 0 RP.
The game quota takes precedence and excludes *all* RP/bonuses and streak changes.
"""
from datetime import datetime, timedelta, timezone

VN_TZ = timezone(timedelta(hours=7))
WEEKDAY_GAMES = 10
WEEKEND_GAMES = 20
WEEKDAY_BASE_RP = 180
WEEKEND_BASE_RP = 250


def day_limits(moment=None):
    moment = moment or datetime.now(VN_TZ)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=VN_TZ)
    weekend = moment.astimezone(VN_TZ).weekday() >= 5
    return (WEEKEND_GAMES, WEEKEND_BASE_RP) if weekend else (WEEKDAY_GAMES, WEEKDAY_BASE_RP)


def apply_match_cap(delta, earned_base, limit, streak_bonus=0):
    """Return (final delta, detail), retaining only an eligible win-streak bonus.

    Call only for a match within the daily game quota. ``earned_base`` is the
    sum of positive *base* contributions, never total RP including bonuses.
    """
    delta, earned_base, limit = int(delta or 0), max(0, int(earned_base or 0)), int(limit)
    streak_bonus = max(0, min(int(streak_bonus or 0), max(0, delta)))
    base_delta = max(0, delta - streak_bonus)
    remaining = max(0, limit - earned_base)
    applied_base = min(base_delta, remaining)
    reached = earned_base >= limit
    if delta > 0:
        applied = applied_base + streak_bonus
    elif delta < 0 and reached:
        applied = 0
    else:
        applied = delta
    return applied, {
        "enabled": True, "earned_before": earned_base,
        "formula_delta": delta, "applied_delta": applied,
        "base_formula_delta": base_delta, "base_applied": applied_base,
        "streak_bonus": streak_bonus, "remaining_before": remaining,
        "limit": limit, "capped": applied != delta,
        "loss_protected": delta < 0 and reached,
        "bonus_exempt": True,
    }
