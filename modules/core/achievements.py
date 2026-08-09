"""Module hóa từ V1.2.9.

Giữ nguyên logic gốc; dependency được truyền từ app.py bằng configure() để tránh import vòng.
"""

_CONTEXT = {}

def configure(context):
    _CONTEXT.clear()
    _CONTEXT.update(context)
    globals().update(context)

EXPORTED_NAMES = ['achievement_progress', 'eligible_achievement_codes', 'list_user_achievement_map', 'decorate_player_achievements', 'sync_achievements_for_users']

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

