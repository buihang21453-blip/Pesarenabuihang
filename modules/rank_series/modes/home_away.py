MODE_CODE = "home_away"


def prepare(service, room, series, games, host, guest):
    game_no = len([g for g in games if g.get("status") == "completed"]) + 1
    if game_no == 1:
        pair = service.smart_random_pair(host, guest, used=[])
    else:
        first = games[0] if games else None
        if not first:
            raise ValueError("Không tìm thấy dữ liệu lượt đi để tạo lượt về.")
        # Lượt về giữ đúng hai CLB và đổi sân/đổi phía cho công bằng.
        pair = service.pack_existing_pair(first.get("player1_team"), first.get("player2_team"))
    return {"action": "start_match", "game_no": game_no, "pair": pair, "label": f"Lượt {game_no}/2"}
