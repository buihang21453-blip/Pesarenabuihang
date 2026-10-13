"""V1.6.83 backend-only RPC readers for DB-side pagination.

Each helper returns None when the SQL migration has not been installed so routes
can fall back to the preserved V1.6.82 behavior without breaking deployment.
"""


def configure(context):
    globals().update(context)


def _rpc_payload(name, params):
    try:
        result = execute_query(db.rpc(name, params), name, attempts=2)
        data = result.data
        if isinstance(data, list) and len(data) == 1 and isinstance(data[0], dict) and len(data[0]) == 1:
            data = next(iter(data[0].values()))
        if isinstance(data, dict):
            return data
    except Exception as exc:
        app.logger.warning("%s unavailable; using legacy fallback: %s", name, exc)
    return None


def players_page(*, page, page_size, query, status, viewer, invisible_ids, online_timeout_seconds):
    return _rpc_payload("pes_players_page", {
        "p_page": int(page), "p_page_size": int(page_size), "p_query": query or "",
        "p_status": status or "all", "p_viewer_is_admin": bool(is_admin_user(viewer)),
        "p_viewer_is_invisible": bool(viewer and str(viewer.get("id")) in {str(x) for x in invisible_ids}),
        "p_invisible_ids": list(str(x) for x in invisible_ids),
        "p_online_timeout_seconds": int(online_timeout_seconds),
    })


def leaderboard_page(*, season_number, page, page_size, query, rank_filter, viewer,
                     invisible_ids, placement_matches, inactive_days):
    min_points = max_points = None
    if rank_filter and rank_filter != "all":
        rank = next((r for r in get_rank_ranges() if str(r.get("slug")) == str(rank_filter)), None)
        if rank:
            min_points = rank.get("min")
            max_points = rank.get("max")
    return _rpc_payload("pes_leaderboard_page", {
        "p_season_number": int(season_number), "p_page": int(page), "p_page_size": int(page_size),
        "p_query": query or "", "p_min_points": min_points, "p_max_points": max_points,
        "p_placement_matches": int(placement_matches), "p_inactive_days": int(inactive_days),
        "p_viewer_is_admin": bool(is_admin_user(viewer)),
        "p_viewer_is_invisible": bool(viewer and str(viewer.get("id")) in {str(x) for x in invisible_ids}),
        "p_invisible_ids": list(str(x) for x in invisible_ids),
        "p_current_user_id": (viewer or {}).get("id"),
    })
