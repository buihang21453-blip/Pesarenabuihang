MODE_CODE = "ban_pick_bo3"


def prepare(service, room, series, games, host, guest):
    game_no = len([g for g in games if g.get("status") == "completed"]) + 1
    state = service.metadata(series).get("ban_pick")
    if not state:
        state = service.build_ban_pick_pool(host, guest, game_no)
        service.save_ban_pick(series, state)
    else:
        state = dict(state)
        state["game_no"] = game_no
        state.setdefault("host_pick", None)
        state.setdefault("guest_pick", None)
        if int(state.get("active_game_no") or 0) != game_no:
            state["active_game_no"] = game_no
            state["host_pick"] = None
            state["guest_pick"] = None
            cfg = service.get_mode_config()
            total_bans = max(0, int(cfg.get("bans_per_player") or 3)) * 2
            state["phase"] = "pick" if int(state.get("ban_count") or 0) >= total_bans else "ban"
            service.reset_ban_pick_deadline(state)
            service.save_ban_pick(series, state)
    return {"action": "ban_pick", "game_no": game_no, "state": state, "label": f"Cấm chọn {game_no}/3"}
