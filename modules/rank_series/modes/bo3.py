MODE_CODE = "bo3"


def prepare(service, room, series, games, host, guest):
    game_no = len([g for g in games if g.get("status") == "completed"]) + 1
    used = service.used_clubs(series, games)
    pair = service.smart_random_pair(host, guest, used=used)
    return {"action": "start_match", "game_no": game_no, "pair": pair, "label": f"Trận {game_no}/3"}
