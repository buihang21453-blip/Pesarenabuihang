"""Rank Series orchestrator.

Owns child-game lifecycle for Home/Away, BO3, Tactical BO3 and Ban/Pick BO3.
Child matches are confirmed with delta=0; RP is applied exactly once when the series completes.
"""
import json
import random
from copy import deepcopy

from . import repository
from .modes import home_away, bo3, tactical_bo3, ban_pick_bo3

_CONTEXT = {}
SERIES_MODES = {"home_away", "bo3", "tactical_bo3", "ban_pick_bo3"}
HANDLERS = {
    "home_away": home_away,
    "bo3": bo3,
    "tactical_bo3": tactical_bo3,
    "ban_pick_bo3": ban_pick_bo3,
}
EXPORTED_NAMES = (
    "SERIES_MODES", "get_room_series_context", "prepare_next_series_game",
    "choose_tactical_club", "ban_pick_action", "process_series_timeouts", "confirm_series_child_match",
    "is_series_child_match", "cancel_active_series_for_room", "finalize_series_forfeit",
)


def configure(context):
    global _CONTEXT
    _CONTEXT = context
    repository.configure(context)


def _g(name):
    return _CONTEXT[name]


def _same(a, b):
    return str(a or "") == str(b or "")


def metadata(series):
    raw = (series or {}).get("metadata") or {}
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except Exception:
            raw = {}
    return dict(raw) if isinstance(raw, dict) else {}


def _team_pack(team):
    return {
        "name": team.get("display"), "overall": int(team.get("overall") or 0),
        "total_stats": int(team.get("total_stats") or 0), "tier": team.get("tier") or "",
        "logo": team.get("logo_url") or "", "league": team.get("league") or "",
    }


def _team_by_name(name):
    info = _g("get_team_info")(name)
    if info:
        return _team_pack(info)
    return {"name": name, "overall": 0, "total_stats": 0, "tier": "", "logo": "", "league": ""}


def pack_existing_pair(team_a, team_b):
    a, b = _team_by_name(team_a), _team_by_name(team_b)
    return {"team_a": a["name"], "team_b": b["name"], "overall_a": a["overall"], "overall_b": b["overall"],
            "logo_a": a["logo"], "logo_b": b["logo"], "league_a": a["league"], "league_b": b["league"]}


def used_clubs(series, games=None):
    games = games if games is not None else repository.list_games(series.get("id"))
    names = []
    for game in games:
        names.extend([game.get("player1_team"), game.get("player2_team")])
    return [n for n in names if n]


def smart_random_pair(host, guest, used=None):
    used = {str(x or "").casefold() for x in (used or []) if x}
    # Existing Smart Random already handles rank weights and pair history. Retry to enforce no reuse in Series.
    last = None
    for _ in range(30):
        last = _g("smart_random_team_pair")(host, guest)
        if str(last.get("team_a") or "").casefold() not in used and str(last.get("team_b") or "").casefold() not in used:
            return last
    if last:
        return last
    raise ValueError("Không tìm được CLB phù hợp cho trận tiếp theo.")


def build_three_choices(host, guest, used, game_no):
    used_norm = {str(x or "").casefold() for x in used if x}
    all_teams = list(_g("_all_random_teams")())
    if len(all_teams) < 6:
        raise ValueError("Không đủ CLB cho Đấu chiến thuật BO3.")
    chosen = []
    def pick_for(player):
        options = []
        attempts = 0
        while len(options) < 3 and attempts < 100:
            attempts += 1
            team, _, _, _ = _g("_pick_rank_team")(player, all_teams, extra_excluded=chosen + list(used), include_pair_history=False)
            name = team.get("display")
            if not name or str(name).casefold() in used_norm or str(name).casefold() in {str(x).casefold() for x in chosen}:
                continue
            chosen.append(name)
            options.append(_team_pack(team))
        if len(options) < 3:
            raise ValueError("Không đủ CLB chưa sử dụng để tạo 3 lựa chọn.")
        return options
    return {"game_no": int(game_no), "host_options": pick_for(host), "guest_options": pick_for(guest), "host_choice": None, "guest_choice": None}


def save_pending(series, phase, pending):
    meta = metadata(series); meta["phase"] = phase; meta["pending_choices"] = pending
    if phase == "choose" and pending:
        seen = list(meta.get("tactical_seen_clubs") or [])
        seen_norm = {str(x).casefold() for x in seen if x}
        for key in ("host_options", "guest_options"):
            for team in pending.get(key) or []:
                name = team.get("name")
                if name and name.casefold() not in seen_norm:
                    seen.append(name); seen_norm.add(name.casefold())
        meta["tactical_seen_clubs"] = seen
    repository.update_series(series["id"], {"metadata": meta})
    series["metadata"] = meta


def _ban_pick_turn_seconds(phase):
    cfg = _g("get_rank_mode")("ban_pick_bo3") or {}
    key = "ban_seconds" if phase == "ban" else "pick_seconds"
    return max(5, int(cfg.get(key) or 30))


def _reset_ban_pick_deadline(state):
    phase = state.get("phase") or "ban"
    if phase not in {"ban", "pick"}:
        state.pop("turn_deadline_at", None)
        state.pop("turn_actor", None)
        state.pop("turn_seconds", None)
        return state
    if phase == "ban":
        actor = "host" if int(state.get("ban_count") or 0) % 2 == 0 else "guest"
    else:
        actor = "host" if not state.get("host_pick") else "guest" if not state.get("guest_pick") else None
    if not actor:
        state.pop("turn_deadline_at", None)
        state.pop("turn_actor", None)
        state.pop("turn_seconds", None)
        return state
    seconds = _ban_pick_turn_seconds(phase)
    state["turn_actor"] = actor
    state["turn_seconds"] = seconds
    state["turn_deadline_at"] = _g("future_iso")(seconds)
    return state


def build_ban_pick_pool(host, guest, game_no):
    teams = list(_g("_all_random_teams")())
    cfg = _g("get_rank_mode")("ban_pick_bo3") or {}
    pool_size = max(6, int(cfg.get("pool_size") or 20))
    if len(teams) < pool_size:
        raise ValueError(f"Cần ít nhất {pool_size} CLB hoạt động cho Cấm chọn CLB BO3.")
    sample = random.SystemRandom().sample(teams, pool_size)
    state = {"game_no": int(game_no), "active_game_no": int(game_no), "phase": "ban", "ban_count": 0,
            "pool": [_team_pack(t) for t in sample], "banned": [], "host_pick": None, "guest_pick": None, "action_order": 0}
    return _reset_ban_pick_deadline(state)


def save_ban_pick(series, state, expected_updated_at=None):
    meta = metadata(series); meta["phase"] = "ban_pick"; meta["ban_pick"] = state
    result = repository.update_series(series["id"], {"metadata": meta}, expected_updated_at=expected_updated_at)
    if expected_updated_at and not (result.data or []):
        raise ValueError("Lượt Cấm/Chọn vừa được người chơi khác xử lý. Giao diện sẽ tự cập nhật.")
    series["metadata"] = meta
    return result


def _ensure_series(room, mode_code):
    active = repository.get_active_series(room.get("id"))
    if active:
        if active.get("mode_code") != mode_code or not _same(active.get("player1_id"), room.get("host_user_id")) or not _same(active.get("player2_id"), room.get("guest_user_id")):
            raise ValueError("Phòng đang có một Series khác chưa hoàn tất.")
        return active
    return repository.create_series(room, mode_code)


def _game_counts(series, games):
    p1 = sum(g.get("winner_side") == "player1" and g.get("status") == "completed" for g in games)
    p2 = sum(g.get("winner_side") == "player2" and g.get("status") == "completed" for g in games)
    draws = sum(g.get("winner_side") == "draw" and g.get("status") == "completed" for g in games)
    return int(p1), int(p2), int(draws)


def _start_match(room, series, game_no, pair, mode_code):
    match_result = _g("execute_query")(
        _g("db").table("matches").insert({
            "player1_id": room["host_user_id"], "player2_id": room["guest_user_id"],
            "mode_code": mode_code, "team1": pair["team_a"], "team2": pair["team_b"],
            "team1_overall": pair.get("overall_a") or 0, "team2_overall": pair.get("overall_b") or 0,
            "team1_logo_url": pair.get("logo_a") or None, "team2_logo_url": pair.get("logo_b") or None,
            "team1_league": pair.get("league_a") or None, "team2_league": pair.get("league_b") or None,
            "host_xp_factor": _CONTEXT.get("HOST_XP_FACTOR", 0.95), "status": "playing",
            "note": f"[SERIES:{series['id']}] [GAME:{game_no}] [{mode_code}]", "updated_at": _g("now_iso")(),
        }), "rank_series_create_child_match", attempts=2)
    match = (match_result.data or [None])[0]
    if not match:
        raise ValueError("Không thể tạo trận con của Series.")
    game = repository.create_game(series["id"], game_no, match["id"], pair["team_a"], pair["team_b"], {"mode_code": mode_code})
    if not game:
        _g("execute_query")(_g("db").table("matches").delete().eq("id", match["id"]), "rollback_series_child_match", attempts=1)
        raise ValueError("Không thể liên kết trận con với Series.")
    meta = metadata(series); meta["phase"] = "playing"; meta["active_game_no"] = int(game_no); meta.pop("pending_choices", None)
    if mode_code == "ban_pick_bo3" and meta.get("ban_pick"):
        meta["ban_pick"]["phase"] = "playing"
    repository.update_series(series["id"], {"metadata": meta, "status": "playing"})
    update = {
        "host_team": pair["team_a"], "guest_team": pair["team_b"],
        "host_team_overall": pair.get("overall_a") or 0, "guest_team_overall": pair.get("overall_b") or 0,
        "host_team_logo_url": pair.get("logo_a") or None, "guest_team_logo_url": pair.get("logo_b") or None,
        "host_team_league": pair.get("league_a") or None, "guest_team_league": pair.get("league_b") or None,
        "match_mode": _CONTEXT.get("MATCH_MODE_RANKED", "ranked"), "team_tier": mode_code,
        "status": "playing", "match_id": match["id"], "note": f"__SERIES_ACTIVE__|{series['id']}|{mode_code}|game:{game_no}",
        "state_expires_at": None, "updated_at": _g("now_iso")(),
    }
    changed = _g("execute_query")(_g("db").table("match_rooms").update(update).eq("id", room["id"]).eq("status", "waiting_ready"), "rank_series_start_room_game", attempts=2)
    if not (changed.data or []):
        raise ValueError("Trạng thái phòng vừa thay đổi; chưa bắt đầu trận con.")
    return {"series": series, "game": game, "match": match, "game_no": game_no}


def prepare_next_series_game(room):
    mode_code = _g("normalize_rank_mode_code")(room.get("team_tier"))
    if mode_code not in SERIES_MODES:
        raise ValueError("Chế độ hiện tại không phải Series.")
    if room.get("status") != "waiting_ready" or room.get("match_id"):
        raise ValueError("Phòng chưa sẵn sàng để tạo trận tiếp theo.")
    if not room.get("guest_user_id") or not room.get("guest_ready"):
        raise ValueError("Cần đủ hai người và đối thủ đã Sẵn sàng.")
    host, guest = _g("get_user")(room.get("host_user_id")), _g("get_user")(room.get("guest_user_id"))
    if not host or not guest:
        raise ValueError("Không tải được hai người chơi.")
    series = _ensure_series(room, mode_code)
    games = repository.list_games(series["id"])
    completed = [g for g in games if g.get("status") == "completed"]
    continuation = bool(completed)
    _g("assert_rank_mode_daily_quota")(mode_code, host.get("id"), guest.get("id"), continuation=continuation)
    resolved = _g("resolve_series_result")(mode_code, games)
    if resolved.get("status") == "completed":
        raise ValueError("Series này đã hoàn tất.")
    handler = HANDLERS[mode_code]
    prep = handler.prepare(globals_proxy(), room, series, games, host, guest)
    if prep["action"] == "start_match":
        return {**prep, **_start_match(room, series, prep["game_no"], prep["pair"], mode_code)}
    return {**prep, "series": series}


class _GlobalsProxy:
    smart_random_pair = staticmethod(smart_random_pair)
    pack_existing_pair = staticmethod(pack_existing_pair)
    used_clubs = staticmethod(used_clubs)
    metadata = staticmethod(metadata)
    build_three_choices = staticmethod(build_three_choices)
    save_pending = staticmethod(save_pending)
    build_ban_pick_pool = staticmethod(build_ban_pick_pool)
    save_ban_pick = staticmethod(save_ban_pick)
    reset_ban_pick_deadline = staticmethod(_reset_ban_pick_deadline)
    get_mode_config = staticmethod(lambda: _g("get_rank_mode")("ban_pick_bo3") or {})

def globals_proxy():
    return _GlobalsProxy


def choose_tactical_club(room, user_id, choice_index):
    series = repository.get_active_series(room.get("id"))
    if not series or series.get("mode_code") != "tactical_bo3":
        raise ValueError("Không có lượt Đấu chiến thuật đang chờ chọn CLB.")
    state = metadata(series).get("pending_choices") or {}
    side = "host" if _same(user_id, room.get("host_user_id")) else "guest" if _same(user_id, room.get("guest_user_id")) else None
    if not side:
        raise ValueError("Bạn không thuộc phòng này.")
    options = state.get(f"{side}_options") or []
    idx = int(choice_index)
    if idx < 0 or idx >= len(options):
        raise ValueError("Lựa chọn CLB không hợp lệ.")
    if state.get(f"{side}_choice") is not None:
        raise ValueError("Bạn đã khóa CLB cho trận này.")
    state[f"{side}_choice"] = idx
    save_pending(series, "choose", state)
    repository.add_club_action(series["id"], state.get("game_no"), user_id, "pick", options[idx]["name"], len(repository.list_club_actions(series["id"])) + 1)
    if state.get("host_choice") is None or state.get("guest_choice") is None:
        return {"started": False}
    h = state["host_options"][state["host_choice"]]; g = state["guest_options"][state["guest_choice"]]
    if h["name"] == g["name"]:
        raise ValueError("Hai bên không thể dùng cùng một CLB.")
    pair = {"team_a": h["name"], "team_b": g["name"], "overall_a": h["overall"], "overall_b": g["overall"],
            "logo_a": h.get("logo"), "logo_b": g.get("logo"), "league_a": h.get("league"), "league_b": g.get("league")}
    return {"started": True, **_start_match(room, series, int(state["game_no"]), pair, "tactical_bo3")}


def _available_ban_pick_clubs(series, state):
    banned = set(state.get("banned") or [])
    used = {x.casefold() for x in used_clubs(series) if x}
    taken = {state.get("host_pick"), state.get("guest_pick")}
    return [x.get("name") for x in (state.get("pool") or [])
            if x.get("name") and x.get("name") not in banned and x.get("name") not in taken
            and x.get("name").casefold() not in used]


def ban_pick_action(room, user_id, action, club_name, source="user"):
    series = repository.get_active_series(room.get("id"))
    if not series or series.get("mode_code") != "ban_pick_bo3":
        raise ValueError("Không có lượt Cấm chọn đang hoạt động.")
    meta = metadata(series); state = dict(meta.get("ban_pick") or {})
    if not state:
        raise ValueError("Pool Cấm chọn chưa được tạo.")
    is_host = _same(user_id, room.get("host_user_id")); is_guest = _same(user_id, room.get("guest_user_id"))
    if not (is_host or is_guest): raise ValueError("Bạn không thuộc phòng này.")
    pool_names = [x.get("name") for x in state.get("pool") or []]
    if club_name not in pool_names: raise ValueError("CLB không nằm trong pool hiện tại.")
    action = str(action or "").strip().lower()
    banned = list(state.get("banned") or [])
    action_order = int(state.get("action_order") or 0) + 1
    expected_updated_at = series.get("updated_at")
    if state.get("phase") == "ban":
        if action != "ban": raise ValueError("Hiện tại phải thực hiện lượt cấm CLB.")
        expected_host = (int(state.get("ban_count") or 0) % 2 == 0)
        if expected_host != is_host: raise ValueError("Chưa tới lượt cấm của bạn.")
        if club_name in banned: raise ValueError("CLB này đã bị cấm.")
        banned.append(club_name); state["banned"] = banned; state["ban_count"] = int(state.get("ban_count") or 0) + 1
        state["action_order"] = action_order; state["last_action_source"] = source
        cfg = _g("get_rank_mode")("ban_pick_bo3") or {}
        total_bans = max(0, int(cfg.get("bans_per_player") or 3)) * 2
        if state["ban_count"] >= total_bans: state["phase"] = "pick"
        _reset_ban_pick_deadline(state)
        save_ban_pick(series, state, expected_updated_at=expected_updated_at)
        repository.add_club_action(series["id"], int(state.get("active_game_no") or 1), user_id, "ban_auto" if source == "timeout_random" else "ban", club_name, action_order)
        return {"started": False, "phase": state["phase"], "auto": source == "timeout_random", "club_name": club_name}
    if state.get("phase") != "pick": raise ValueError("Hiện chưa ở bước chọn CLB.")
    if action != "pick": raise ValueError("Hiện tại phải thực hiện lượt chọn CLB.")
    if club_name in banned: raise ValueError("CLB này đã bị cấm.")
    used = {x.casefold() for x in used_clubs(series) if x}
    if club_name.casefold() in used: raise ValueError("CLB này đã được dùng trong Series.")
    if is_host:
        if state.get("host_pick"): raise ValueError("Chủ phòng đã chọn CLB.")
        state["host_pick"] = club_name
    else:
        if not state.get("host_pick"): raise ValueError("Chủ phòng chọn trước trong lượt này.")
        if state.get("guest_pick"): raise ValueError("Đối thủ đã chọn CLB.")
        if club_name == state.get("host_pick"): raise ValueError("Hai bên không thể chọn cùng CLB.")
        state["guest_pick"] = club_name
    state["action_order"] = action_order; state["last_action_source"] = source
    _reset_ban_pick_deadline(state)
    save_ban_pick(series, state, expected_updated_at=expected_updated_at)
    repository.add_club_action(series["id"], int(state.get("active_game_no") or 1), user_id, "pick_auto" if source == "timeout_random" else "pick", club_name, action_order)
    if not state.get("host_pick") or not state.get("guest_pick"):
        return {"started": False, "phase": "pick", "auto": source == "timeout_random", "club_name": club_name}
    a, b = _team_by_name(state["host_pick"]), _team_by_name(state["guest_pick"])
    pair = {"team_a": a["name"], "team_b": b["name"], "overall_a": a["overall"], "overall_b": b["overall"],
            "logo_a": a["logo"], "logo_b": b["logo"], "league_a": a["league"], "league_b": b["league"]}
    return {"started": True, "auto": source == "timeout_random", "club_name": club_name, **_start_match(room, series, int(state.get("active_game_no") or 1), pair, "ban_pick_bo3")}


def process_series_timeouts(room):
    """Resolve expired Ban/Pick turns. Safe to call from room polling.

    One expired turn creates exactly one random action; the next action gets its own
    fresh deadline. Optimistic ``updated_at`` matching prevents two pollers from
    applying the same expired turn twice.
    """
    if not room or room.get("status") != "waiting_ready":
        return {"changed": False}
    if _g("normalize_rank_mode_code")(room.get("team_tier")) != "ban_pick_bo3":
        return {"changed": False}
    series = repository.get_active_series(room.get("id"))
    if not series or series.get("mode_code") != "ban_pick_bo3":
        return {"changed": False}
    state = dict(metadata(series).get("ban_pick") or {})
    if state.get("phase") not in {"ban", "pick"}:
        return {"changed": False}
    deadline = state.get("turn_deadline_at")
    if not deadline or int(_g("seconds_until")(deadline)) > 0:
        return {"changed": False, "remaining": int(_g("seconds_until")(deadline)) if deadline else None}
    actor = state.get("turn_actor")
    if actor not in {"host", "guest"}:
        _reset_ban_pick_deadline(state)
        save_ban_pick(series, state, expected_updated_at=series.get("updated_at"))
        return {"changed": True, "repaired_timer": True}
    user_id = room.get("host_user_id") if actor == "host" else room.get("guest_user_id")
    available = _available_ban_pick_clubs(series, state)
    if not available:
        raise ValueError("Không còn CLB hợp lệ để hệ thống tự động Cấm/Chọn.")
    club_name = random.SystemRandom().choice(available)
    action = "ban" if state.get("phase") == "ban" else "pick"
    result = ban_pick_action(room, user_id, action, club_name, source="timeout_random")
    return {"changed": True, "action": action, "actor": actor, "club_name": club_name, **result}


def is_series_child_match(match):
    if not match:
        return False
    if _g("normalize_rank_mode_code")(match.get("mode_code")) not in SERIES_MODES:
        return False
    return repository.get_game_by_match(match.get("id")) is not None


def _apply_series_rp(series, result):
    p1 = _g("get_user")(series.get("player1_id")); p2 = _g("get_user")(series.get("player2_id"))
    if not p1 or not p2: raise ValueError("Không tải được người chơi để chốt RP Series.")
    rp = _g("calculate_mode_rp")(series.get("mode_code"), result, winner_side=result.get("winner_side"),
        player1_rp=int(p1.get("rank_points") or 0), player2_rp=int(p2.get("rank_points") or 0),
        rng=random.Random(f"PES_ARENA_SERIES|{series.get('id')}"))
    d1, d2 = int(rp.get("player1") or 0), int(rp.get("player2") or 0)
    cap_fn = _CONTEXT.get("apply_daily_positive_rp_cap")
    if callable(cap_fn):
        d1, _ = cap_fn(p1["id"], d1)
        d2, _ = cap_fn(p2["id"], d2)
    _g("execute_query")(_g("db").table("users").update({"rank_points": max(0, int(p1.get("rank_points") or 0) + d1)}).eq("id", p1["id"]), "series_rp_p1", attempts=2)
    _g("execute_query")(_g("db").table("users").update({"rank_points": max(0, int(p2.get("rank_points") or 0) + d2)}).eq("id", p2["id"]), "series_rp_p2", attempts=2)
    return d1, d2, rp


def _reset_room_after_series_confirm(room, series, confirmer_id, *, completed, delta1=0, delta2=0, resolved=None):
    """Reset the room after a confirmed Series child, with idempotent verification.

    A child match may already be confirmed even when the room reset query was lost/failed.
    Retrying confirmation must repair that room instead of leaving it stuck forever in
    waiting_result_confirm.
    """
    if completed:
        resolved = resolved or {}
        room_note = f"Series hoàn tất: {resolved.get('aggregate_score') or resolved.get('score') or 'Hòa'} | RP {int(delta1):+d}/{int(delta2):+d}"
        guest_ready = False
    else:
        meta = metadata(series)
        next_game_no = int(meta.get("next_game_no") or 1)
        room_note = f"__SERIES_ACTIVE__|{series['id']}|{series.get('mode_code')}|next:{next_game_no}"
        guest_ready = True

    room_update = {
        "status": "waiting_ready", "guest_ready": guest_ready, "host_team": None, "guest_team": None,
        "host_team_overall": None, "guest_team_overall": None, "host_team_logo_url": None, "guest_team_logo_url": None,
        "host_team_league": None, "guest_team_league": None, "host_score": None, "guest_score": None, "match_id": None,
        "submitted_by_id": None, "confirmed_by_id": confirmer_id, "team_tier": series.get("mode_code"),
        "match_mode": _CONTEXT.get("MATCH_MODE_RANKED", "ranked"), "note": room_note,
        "state_expires_at": None, "updated_at": _g("now_iso")(),
    }
    result = _g("execute_query")(
        _g("db").table("match_rooms").update(room_update).eq("id", room["id"]).eq("status", "waiting_result_confirm"),
        "series_reset_room", attempts=2,
    )
    if result.data or []:
        return True

    # Idempotent success: another request may already have repaired the room.
    fresh_room = _g("get_room")(room["id"])
    if fresh_room and fresh_room.get("status") == "waiting_ready" and not fresh_room.get("match_id"):
        return True
    raise ValueError("Kết quả Series đã được ghi nhận nhưng phòng chưa thể làm mới; hãy thử xác nhận lại.")


def confirm_series_child_match(room, match, confirmer_id):
    game = repository.get_game_by_match(match.get("id"))
    if not game:
        raise ValueError("Không tìm thấy trận con trong Series.")
    series = repository.get_series(game.get("series_id"))
    if not series or series.get("status") not in {"playing", "processing_result"}:
        raise ValueError("Series không còn ở trạng thái thi đấu.")
    score1, score2 = int(match.get("score1") or 0), int(match.get("score2") or 0)
    winner_side = "player1" if score1 > score2 else "player2" if score2 > score1 else "draw"
    # Claim child match so repeated confirmation cannot update stats twice.
    claim = _g("execute_query")(_g("db").table("matches").update({"status": "processing_result", "updated_at": _g("now_iso")()}).eq("id", match["id"]).eq("status", "waiting_confirm"), "claim_series_child", attempts=2)
    if not (claim.data or []):
        fresh = _g("get_match")(match["id"])
        if fresh and fresh.get("status") == "confirmed":
            latest = repository.get_series(series["id"]) or series
            completed = latest.get("status") == "completed"
            resolved = metadata(latest).get("resolved") or {}
            d1 = int(latest.get("rp_player1") or 0)
            d2 = int(latest.get("rp_player2") or 0)
            _reset_room_after_series_confirm(
                room, latest, confirmer_id, completed=completed, delta1=d1, delta2=d2, resolved=resolved
            )
            return {"series_completed": completed, "delta1": d1, "delta2": d2, "resolved": resolved}
        raise ValueError("Trận con đã được xử lý bởi yêu cầu khác.")
    p1, p2 = _g("get_user")(match.get("player1_id")), _g("get_user")(match.get("player2_id"))
    if not p1 or not p2: raise ValueError("Không tải được người chơi.")
    # Child games count toward W/D/L, goals and daily match quota, but never grant per-game RP/streak.
    _g("update_player_after_match")(p1, 0, score1, score2, affect_streak=False)
    _g("update_player_after_match")(p2, 0, score2, score1, affect_streak=False)
    _g("execute_query")(_g("db").table("matches").update({
        "delta1": 0, "delta2": 0, "rp_formula_version": "series_child_v1",
        "rp_details": {"source": "modules/rank_series/service.py", "mode_code": series.get("mode_code"), "series_id": series.get("id"), "game_no": game.get("game_no"), "series_rp_applied": False},
        "status": "confirmed", "confirmed_by_id": confirmer_id,
        "note": f"Đã xác nhận trận {game.get('game_no')} của Series {series.get('mode_code')}; RP chốt ở cuối Series.", "updated_at": _g("now_iso")(),
    }).eq("id", match["id"]).eq("status", "processing_result"), "finalize_series_child", attempts=2)
    repository.complete_game(game["id"], score1, score2, winner_side)
    games = repository.list_games(series["id"])
    resolved = _g("resolve_series_result")(series.get("mode_code"), games)
    p1wins, p2wins, draws = _game_counts(series, games)
    agg1 = sum(int(g.get("player1_score") or 0) for g in games if g.get("status") == "completed")
    agg2 = sum(int(g.get("player2_score") or 0) for g in games if g.get("status") == "completed")
    base_update = {"player1_wins": p1wins, "player2_wins": p2wins, "draw_games": draws, "aggregate_player1": agg1, "aggregate_player2": agg2}
    if resolved.get("status") == "completed":
        claim_series = repository.update_series(series["id"], {**base_update, "status": "processing_result"}, expected_status="playing")
        if not (claim_series.data or []):
            latest = repository.get_series(series["id"])
            if latest and latest.get("status") == "completed":
                return {"series_completed": True, "delta1": int(latest.get("rp_player1") or 0), "delta2": int(latest.get("rp_player2") or 0)}
            raise ValueError("Series đang được yêu cầu khác chốt kết quả.")
        d1, d2, rp = _apply_series_rp(series, resolved)
        # Store the one-time Series RP on the final child match as well. This keeps
        # daily +150 RP accounting, match history and admin rollback compatible
        # with the existing match-based accounting without granting RP per child.
        _g("execute_query")(_g("db").table("matches").update({
            "delta1": int(d1), "delta2": int(d2), "rp_formula_version": "series_rp_v2",
            "rp_details": {"source": "modules/rank_series/service.py", "mode_code": series.get("mode_code"),
                           "series_id": series.get("id"), "game_no": game.get("game_no"),
                           "series_rp_applied": True, "series_result": resolved, "series_rp": rp},
            "note": f"Trận cuối Series {series.get('mode_code')}; RP Series đã chốt: {int(d1):+d}/{int(d2):+d}.",
            "updated_at": _g("now_iso")(),
        }).eq("id", match["id"]).eq("status", "confirmed"), "store_series_rp_on_final_match", attempts=2)
        winner_user_id = series.get("player1_id") if resolved.get("winner_side") == "player1" else series.get("player2_id") if resolved.get("winner_side") == "player2" else None
        audit = _g("mode_series_rp_audit_payload")(rp)
        repository.update_series(series["id"], {**base_update, **audit, "status": "completed", "winner_user_id": winner_user_id,
            "result_code": resolved.get("score") or resolved.get("aggregate_score") or "draw", "rp_applied": True,
            "rp_player1": d1, "rp_player2": d2, "completed_at": _g("now_iso")(), "metadata": {**metadata(series), "phase": "completed", "resolved": resolved}}, expected_status="processing_result")
        room_note = f"Series hoàn tất: {resolved.get('aggregate_score') or resolved.get('score') or 'Hòa'} | RP {d1:+d}/{d2:+d}"
        guest_ready = False
        completed = True
    else:
        meta = metadata(series); meta["phase"] = "ready"; meta["next_game_no"] = len([g for g in games if g.get("status") == "completed"]) + 1; meta.pop("pending_choices", None)
        if meta.get("ban_pick"):
            meta["ban_pick"]["phase"] = "pick"; meta["ban_pick"]["host_pick"] = None; meta["ban_pick"]["guest_pick"] = None
        repository.update_series(series["id"], {**base_update, "metadata": meta})
        room_note = f"__SERIES_ACTIVE__|{series['id']}|{series.get('mode_code')}|next:{meta['next_game_no']}"
        d1 = d2 = 0; guest_ready = True; completed = False
    _reset_room_after_series_confirm(
        room, series, confirmer_id, completed=completed, delta1=d1, delta2=d2, resolved=resolved
    )
    for key in ("_rz_users_map", "_rz_players_all", "_rz_rooms_all"):
        try: _g("cache_delete")(key)
        except Exception: pass
    try: _g("ttl_cache_delete")("players_raw", "rooms_raw")
    except Exception: pass
    return {"series_completed": completed, "delta1": d1, "delta2": d2, "resolved": resolved}


def get_room_series_context(room):
    mode_code = _g("normalize_rank_mode_code")((room or {}).get("team_tier"))
    if mode_code not in SERIES_MODES:
        return None
    series = repository.get_active_series(room.get("id"))
    if not series:
        # Show pre-start state without creating DB rows during GET/polling.
        return {"mode_code": mode_code, "active": False, "phase": "ready", "game_no": 1, "games": [], "score": "0 - 0", "can_start": bool(room.get("guest_ready"))}
    games = repository.list_games(series["id"]); p1, p2, draws = _game_counts(series, games); meta = metadata(series)
    game_no = len([g for g in games if g.get("status") == "completed"]) + (0 if series.get("status") == "completed" else 1)
    ctx = {"mode_code": mode_code, "active": True, "series_id": series.get("id"), "status": series.get("status"), "phase": meta.get("phase") or "ready",
           "updated_at": series.get("updated_at"), "game_no": game_no, "games": games, "p1_wins": p1, "p2_wins": p2, "draws": draws, "score": f"{p1} - {p2}", "metadata": meta, "can_start": bool(room.get("guest_ready"))}
    if mode_code == "home_away": ctx["score"] = f"{int(series.get('aggregate_player1') or 0)} - {int(series.get('aggregate_player2') or 0)}"
    if meta.get("pending_choices"): ctx["choices"] = meta["pending_choices"]
    if meta.get("ban_pick"):
        bp = dict(meta["ban_pick"])
        bp["turn_remaining_seconds"] = int(_g("seconds_until")(bp.get("turn_deadline_at"))) if bp.get("turn_deadline_at") else 0
        ctx["ban_pick"] = bp
    return ctx


def cancel_active_series_for_room(room_id, reason="cancelled"):
    series = repository.get_active_series(room_id)
    if not series: return False
    # Close any unfinished child-game row as well, otherwise a new Series can
    # inherit an orphaned "playing" child after a dispute/cancel.
    try:
        _g("execute_query")(
            _g("db").table("match_series_games").update({
                "status": "cancelled",
                "completed_at": _g("now_iso")(),
            }).eq("series_id", series["id"]).eq("status", "playing"),
            "rank_series_cancel_open_games", attempts=2,
        )
    except Exception:
        pass
    repository.update_series(series["id"], {"status": "cancelled", "result_code": reason, "completed_at": _g("now_iso")(),
        "metadata": {**metadata(series), "phase": "cancelled", "cancel_reason": reason}})
    return True


def finalize_series_forfeit(room, offender_id, penalty_delta=0, winner_delta=0):
    """Close an active Series after a manual/timeout/browser-offline forfeit.

    RP is already applied by the room forfeit flow; this function only makes the
    Series tables reflect that same final outcome so reports and future games do
    not see an orphaned active Series.
    """
    if not room or not room.get("id"):
        return False
    series = repository.get_active_series(room.get("id"))
    if not series:
        return False
    offender_side = "player1" if _same(offender_id, series.get("player1_id")) else "player2" if _same(offender_id, series.get("player2_id")) else None
    if not offender_side:
        return False
    winner_id = series.get("player2_id") if offender_side == "player1" else series.get("player1_id")
    # If a child match was already running, close its Series-game row with the
    # canonical 0-2/2-0 forfeit score. The room-level match history remains the
    # source for the public forfeit record.
    game = repository.get_game_by_match(room.get("match_id")) if room.get("match_id") else None
    if game and game.get("status") == "playing":
        if offender_side == "player1":
            repository.complete_game(game["id"], 0, 2, "player2")
        else:
            repository.complete_game(game["id"], 2, 0, "player1")
    games = repository.list_games(series["id"]); p1wins, p2wins, draws = _game_counts(series, games)
    agg1 = sum(int(g.get("player1_score") or 0) for g in games if g.get("status") == "completed")
    agg2 = sum(int(g.get("player2_score") or 0) for g in games if g.get("status") == "completed")
    p1_delta = int(penalty_delta or 0) if offender_side == "player1" else int(winner_delta or 0)
    p2_delta = int(penalty_delta or 0) if offender_side == "player2" else int(winner_delta or 0)
    payload = {
        "status": "completed", "forfeit_user_id": offender_id, "winner_user_id": winner_id,
        "result_code": "forfeit", "rp_applied": True, "rp_player1": p1_delta, "rp_player2": p2_delta,
        "player1_wins": p1wins, "player2_wins": p2wins, "draw_games": draws,
        "aggregate_player1": agg1, "aggregate_player2": agg2, "completed_at": _g("now_iso")(),
        "metadata": {**metadata(series), "phase": "completed", "resolved": {"status":"completed","reason":"forfeit","forfeiting_side":offender_side}},
    }
    repository.update_series(series["id"], payload)
    return True
