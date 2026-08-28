"""PES Arena Season core: snapshot, rewards, reset and season placement."""
from datetime import datetime

EXPORTED_NAMES = [
    "get_current_season", "get_season_history", "count_season_matches",
    "build_season_match_count_map", "season_ranking_eligibility",
]

SEASON_SETTING_KEY = "rank_season_current"
DEFAULT_SEASON = {
    "season_number": 1,
    "name": "Season 1",
    "started_at": None,
    "status": "active",
    "placement_matches": 5,
}

def configure(context):
    globals().update(context)

def _parse(value):
    if not value:
        return None
    try:
        return parse_dt(value)
    except Exception:
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except Exception:
            return None

def get_current_season(force=False):
    require_db()
    try:
        result = execute_query(
            db.table("system_settings").select("setting_value").eq("setting_key", SEASON_SETTING_KEY).limit(1),
            "get_current_rank_season", attempts=2,
        )
        if result.data:
            value = dict(result.data[0].get("setting_value") or {})
            merged = dict(DEFAULT_SEASON)
            merged.update(value)
            return merged
    except Exception:
        pass
    return dict(DEFAULT_SEASON)

def get_season_history(limit=20):
    require_db()
    try:
        result = execute_query(
            db.table("rank_seasons").select("*").order("season_number", desc=True).limit(max(1, min(int(limit), 100))),
            "get_rank_season_history", attempts=2,
        )
        return [dict(x) for x in (result.data or [])]
    except Exception:
        return []

def build_season_match_count_map(matches, season=None):
    season = season or get_current_season()
    start = _parse(season.get("started_at"))
    counts = {}
    for match in matches or []:
        if not _ranking_activity_match(match):
            continue
        created = _parse(match.get("created_at"))
        if start and (not created or created < start):
            continue
        for uid in (match.get("player1_id"), match.get("player2_id")):
            if uid:
                key = str(uid)
                counts[key] = counts.get(key, 0) + 1
    return counts

def count_season_matches(user_id, matches, season=None):
    return build_season_match_count_map(matches, season).get(str(user_id), 0)

def season_ranking_eligibility(player, season_matches, latest_activity_at=None, now=None, season=None):
    season = season or get_current_season()
    required = max(1, int(season.get("placement_matches") or 5))
    matches = max(0, int(season_matches or 0))
    if matches < required:
        return {"visible": False, "reason": "placement", "matches": matches,
                "matches_needed": required - matches, "inactive_days": 0}
    if latest_activity_at:
        now = now or now_dt()
        inactive_days = max(0, int((now - latest_activity_at).total_seconds() // 86400))
        if inactive_days >= RANKING_INACTIVE_HIDE_DAYS:
            return {"visible": False, "reason": "inactive", "matches": matches,
                    "matches_needed": 0, "inactive_days": inactive_days}
    return {"visible": True, "reason": "ranked", "matches": matches,
            "matches_needed": 0, "inactive_days": 0}
