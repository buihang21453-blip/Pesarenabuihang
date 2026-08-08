"""Fast read-model helpers for pages that should only SELECT precomputed data.

V1.3.34 moves expensive report/profile/ranking aggregation to Supabase write-time
triggers. These helpers intentionally avoid loading full history tables.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

_CONTEXT = {}


def configure(context):
    global _CONTEXT
    _CONTEXT = context or {}


def _db():
    return _CONTEXT.get("db")


def _execute(query, label, attempts=1):
    fn = _CONTEXT.get("execute_query")
    if not fn:
        return query.execute()
    return fn(query, label, attempts=attempts)


def _mode_order():
    return tuple(_CONTEXT.get("MODE_ORDER") or ())


def _mode_configs():
    getter = _CONTEXT.get("get_rank_mode_configs")
    return getter() if callable(getter) else {}


def _query_rows(table_name, columns="*", start_date=None, end_date=None, order=None, desc=False):
    db = _db()
    if db is None:
        return []
    query = db.table(table_name).select(columns)
    if start_date is not None:
        query = query.gte("stat_date", str(start_date))
    if end_date is not None:
        query = query.lte("stat_date", str(end_date))
    if order:
        query = query.order(order, desc=desc)
    return _execute(query, f"read_model_{table_name}", attempts=1).data or []


def resolve_report_range(range_key, today=None):
    vn_tz = timezone(timedelta(hours=7))
    today = today or datetime.now(vn_tz).date()
    labels = {
        "today": "Hôm nay",
        "yesterday": "Hôm qua",
        "3days": "3 ngày gần đây",
        "7days": "1 tuần",
        "30days": "1 tháng",
        "all": "Toàn thời gian",
    }
    if range_key not in labels:
        range_key = "today"
    if range_key == "today":
        start = end = today
    elif range_key == "yesterday":
        start = end = today - timedelta(days=1)
    elif range_key == "3days":
        start, end = today - timedelta(days=2), today
    elif range_key == "7days":
        start, end = today - timedelta(days=6), today
    elif range_key == "30days":
        start, end = today - timedelta(days=29), today
    else:
        start = end = None
    return range_key, labels, start, end


def load_match_report(range_key="today"):
    """Load admin match report from tiny precomputed Supabase tables.

    Returns ``None`` when the V1.3.34 SQL migration has not been applied, so the
    caller may temporarily fall back to legacy logic instead of returning HTTP 500.
    """
    range_key, labels, start, end = resolve_report_range(range_key)
    try:
        daily_rows = _query_rows(
            "admin_match_daily_stats",
            "stat_date,total,confirmed,playing,waiting,disputed,cancelled,confirmed_goals,positive_rp,updated_at",
            start, end, order="stat_date", desc=True,
        )
        mode_rows_raw = _query_rows(
            "admin_match_mode_daily_stats",
            "stat_date,mode_code,match_count",
            start, end,
        )
        series_rows = _query_rows(
            "admin_series_daily_stats",
            "stat_date,mode_code,series,completed,score_2_0,score_2_1,draw,forfeit,disputed,rp_added,rp_removed,games,comebacks",
            start, end,
        )
        player_rows = _query_rows(
            "admin_match_player_daily_stats",
            "stat_date,user_id",
            start, end,
        )
        unlock_rows = _query_rows(
            "admin_rank_mode_unlock_stats",
            "mode_code,unlocked_players,updated_at",
        )
    except Exception:
        return None

    totals = {
        "total": 0,
        "confirmed": 0,
        "playing": 0,
        "waiting": 0,
        "disputed": 0,
        "cancelled": 0,
        "confirmed_goals": 0,
        "positive_rp": 0,
    }
    for row in daily_rows:
        for key in totals:
            totals[key] += int(row.get(key) or 0)

    unique_players = len({str(row.get("user_id")) for row in player_rows if row.get("user_id")})
    mode_counts = {code: 0 for code in _mode_order()}
    for row in mode_rows_raw:
        code = str(row.get("mode_code") or "")
        if code in mode_counts:
            mode_counts[code] += int(row.get("match_count") or 0)

    series_totals = {
        code: {
            "series": 0, "completed": 0, "score_2_0": 0, "score_2_1": 0,
            "draw": 0, "forfeit": 0, "disputed": 0, "rp_added": 0,
            "rp_removed": 0, "games": 0, "comebacks": 0,
        }
        for code in _mode_order()
    }
    for row in series_rows:
        code = str(row.get("mode_code") or "")
        if code not in series_totals:
            continue
        bucket = series_totals[code]
        for key in bucket:
            bucket[key] += int(row.get(key) or 0)

    unlocked = {str(row.get("mode_code") or ""): int(row.get("unlocked_players") or 0) for row in unlock_rows}
    configs = _mode_configs()
    output_modes = []
    total_matches = totals["total"]
    for code in _mode_order():
        cfg = dict(configs.get(code) or {"code": code, "label": code})
        stat = series_totals[code]
        stat["completion_rate"] = round(stat["completed"] * 100 / stat["series"], 1) if stat["series"] else 0
        stat["avg_rp"] = round(stat["rp_added"] / stat["completed"], 1) if stat["completed"] else 0
        output_modes.append({
            **cfg,
            "match_count": mode_counts.get(code, 0),
            "percent": round(mode_counts.get(code, 0) * 100 / total_matches, 1) if total_matches else 0,
            "unlocked_players": unlocked.get(code, 0),
            **stat,
        })

    popular_code = max(mode_counts, key=mode_counts.get) if total_matches and mode_counts else None
    report = {
        "range": range_key,
        "range_label": labels[range_key],
        "range_labels": labels,
        **totals,
        "unique_players": unique_players,
        "mode_counts": mode_counts,
        "mode_rows": output_modes,
        "popular_mode": (configs.get(popular_code) or {}).get("label", popular_code) if popular_code else "Chưa có dữ liệu",
        "source": "read_model",
    }

    daily_mode = {}
    for row in mode_rows_raw:
        day = str(row.get("stat_date") or "")
        if not day:
            continue
        daily_mode.setdefault(day, {})[str(row.get("mode_code") or "")] = int(row.get("match_count") or 0)
    player_by_day = {}
    for row in player_rows:
        day = str(row.get("stat_date") or "")
        uid = str(row.get("user_id") or "")
        if day and uid:
            player_by_day.setdefault(day, set()).add(uid)

    daily_output = []
    for row in daily_rows:
        day = str(row.get("stat_date") or "")
        try:
            label = date.fromisoformat(day).strftime("%d/%m/%Y")
        except Exception:
            label = day
        item = {
            "date": day,
            "date_label": label,
            "total": int(row.get("total") or 0),
            "confirmed": int(row.get("confirmed") or 0),
            "playing": int(row.get("playing") or 0),
            "waiting": int(row.get("waiting") or 0),
            "disputed": int(row.get("disputed") or 0),
            "cancelled": int(row.get("cancelled") or 0),
            "player_count": len(player_by_day.get(day, set())),
        }
        for code in _mode_order():
            item[code] = daily_mode.get(day, {}).get(code, 0)
        daily_output.append(item)
    return report, daily_output


def load_recent_form_map(player_ids):
    ids = [str(x) for x in (player_ids or []) if x]
    if not ids:
        return {}
    db = _db()
    if db is None:
        return {}
    try:
        query = db.table("player_recent_form_cache").select("user_id,recent_form").in_("user_id", ids)
        rows = _execute(query, "read_model_recent_form", attempts=1).data or []
    except Exception:
        return {}
    out = {}
    for row in rows:
        form = row.get("recent_form") or []
        if isinstance(form, list):
            out[str(row.get("user_id"))] = form[:5]
    return out


def load_player_profile_summary(user_id):
    if not user_id or _db() is None:
        return None
    try:
        rows = _execute(
            _db().table("player_profile_stats_cache")
            .select("user_id,favorite_team,frequent_opponent_id,updated_at")
            .eq("user_id", user_id).limit(1),
            "read_model_profile_summary",
            attempts=1,
        ).data or []
        return rows[0] if rows else None
    except Exception:
        return None


def load_user_matches(user_id, limit=10, status=None):
    if not user_id or _db() is None:
        return []
    try:
        query = _db().table("matches").select("*").or_(f"player1_id.eq.{user_id},player2_id.eq.{user_id}")
        if status:
            query = query.eq("status", status)
        query = query.order("created_at", desc=True).limit(int(limit))
        return _execute(query, "read_model_user_matches", attempts=1).data or []
    except Exception:
        return []


def load_h2h_matches(user_a, user_b, limit=10):
    if not user_a or not user_b or _db() is None:
        return []
    try:
        # PostgREST AND groups avoid scanning unrelated users.
        expr = (
            f"and(player1_id.eq.{user_a},player2_id.eq.{user_b}),"
            f"and(player1_id.eq.{user_b},player2_id.eq.{user_a})"
        )
        query = (_db().table("matches").select("*").eq("status", "confirmed")
                 .or_(expr).order("created_at", desc=True).limit(int(limit)))
        return _execute(query, "read_model_h2h_matches", attempts=1).data or []
    except Exception:
        return []


def load_pair_stats(user_a, user_b):
    if not user_a or not user_b or str(user_a) == str(user_b) or _db() is None:
        return None
    a, b = sorted([str(user_a), str(user_b)])
    try:
        rows = _execute(
            _db().table("player_pair_stats_cache")
            .select("user_low_id,user_high_id,total,user_low_wins,user_high_wins,draws,updated_at")
            .eq("user_low_id", a).eq("user_high_id", b).limit(1),
            "read_model_pair_stats",
            attempts=1,
        ).data or []
        return rows[0] if rows else None
    except Exception:
        return None


def load_user_ip_cache():
    if _db() is None:
        return None
    try:
        rows = _execute(
            _db().table("admin_user_ip_summary_cache")
            .select("user_id,latest_ip,known_ips,duplicate_ips,duplicate_ip_count,updated_at"),
            "read_model_user_ip_cache",
            attempts=1,
        ).data or []
        return {str(row.get("user_id")): row for row in rows if row.get("user_id")}
    except Exception:
        return None
