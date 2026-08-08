MODE_CODE = "tactical_bo3"


def prepare(service, room, series, games, host, guest):
    game_no = len([g for g in games if g.get("status") == "completed"]) + 1
    pending = service.metadata(series).get("pending_choices")
    if pending and int(pending.get("game_no") or 0) == game_no:
        return {"action": "choose", "game_no": game_no, "state": pending, "label": f"Chiến thuật {game_no}/3"}
    meta = service.metadata(series)
    excluded = service.used_clubs(series, games) + list(meta.get("tactical_seen_clubs") or [])
    state = service.build_three_choices(host, guest, excluded, game_no)
    service.save_pending(series, "choose", state)
    return {"action": "choose", "game_no": game_no, "state": state, "label": f"Chiến thuật {game_no}/3"}
