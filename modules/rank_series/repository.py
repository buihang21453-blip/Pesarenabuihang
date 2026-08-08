"""Persistence helpers for ranked multi-game series."""

_CONTEXT = {}


def configure(context):
    global _CONTEXT
    _CONTEXT = context


def _g(name):
    return _CONTEXT[name]


def get_active_series(room_id):
    if not room_id:
        return None
    result = _g("execute_query")(
        _g("db").table("match_series")
        .select("*")
        .eq("room_id", room_id)
        .in_("status", ["waiting", "playing", "processing_result"])
        .order("created_at", desc=True)
        .limit(1),
        "rank_series_get_active",
        attempts=2,
    )
    return (result.data or [None])[0]


def get_series(series_id):
    result = _g("execute_query")(
        _g("db").table("match_series").select("*").eq("id", series_id).limit(1),
        "rank_series_get",
        attempts=2,
    )
    return (result.data or [None])[0]


def create_series(room, mode_code):
    result = _g("execute_query")(
        _g("db").table("match_series").insert({
            "room_id": room.get("id"),
            "mode_code": mode_code,
            "player1_id": room.get("host_user_id"),
            "player2_id": room.get("guest_user_id"),
            "status": "playing",
            "metadata": {"phase": "ready", "next_game_no": 1, "used_clubs": []},
            "started_at": _g("now_iso")(),
            "updated_at": _g("now_iso")(),
        }),
        "rank_series_create",
        attempts=2,
    )
    return (result.data or [None])[0]


def update_series(series_id, payload, expected_status=None, expected_updated_at=None):
    query = _g("db").table("match_series").update({**payload, "updated_at": _g("now_iso")()}).eq("id", series_id)
    if expected_status:
        query = query.eq("status", expected_status)
    if expected_updated_at:
        query = query.eq("updated_at", expected_updated_at)
    return _g("execute_query")(query, "rank_series_update", attempts=2)


def list_games(series_id):
    result = _g("execute_query")(
        _g("db").table("match_series_games").select("*").eq("series_id", series_id).order("game_no"),
        "rank_series_games",
        attempts=2,
    )
    return result.data or []


def get_game_by_match(match_id):
    if not match_id:
        return None
    result = _g("execute_query")(
        _g("db").table("match_series_games").select("*").eq("match_id", match_id).limit(1),
        "rank_series_game_by_match",
        attempts=2,
    )
    return (result.data or [None])[0]


def create_game(series_id, game_no, match_id, team1, team2, metadata=None):
    result = _g("execute_query")(
        _g("db").table("match_series_games").insert({
            "series_id": series_id,
            "game_no": int(game_no),
            "match_id": match_id,
            "player1_team": team1,
            "player2_team": team2,
            "status": "playing",
            "metadata": metadata or {},
            "started_at": _g("now_iso")(),
        }),
        "rank_series_create_game",
        attempts=2,
    )
    return (result.data or [None])[0]


def complete_game(game_id, score1, score2, winner_side):
    return _g("execute_query")(
        _g("db").table("match_series_games").update({
            "player1_score": int(score1),
            "player2_score": int(score2),
            "winner_side": winner_side,
            "status": "completed",
            "completed_at": _g("now_iso")(),
        }).eq("id", game_id).eq("status", "playing"),
        "rank_series_complete_game",
        attempts=2,
    )


def add_club_action(series_id, game_no, user_id, action_type, club_code, action_order):
    return _g("execute_query")(
        _g("db").table("match_series_club_actions").insert({
            "series_id": series_id,
            "game_no": game_no,
            "user_id": user_id,
            "action_type": action_type,
            "club_code": club_code,
            "action_order": int(action_order),
        }),
        "rank_series_club_action",
        attempts=2,
    )


def list_club_actions(series_id):
    result = _g("execute_query")(
        _g("db").table("match_series_club_actions").select("*").eq("series_id", series_id).order("action_order"),
        "rank_series_club_actions",
        attempts=2,
    )
    return result.data or []
