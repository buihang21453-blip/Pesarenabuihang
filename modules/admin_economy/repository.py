"""Repository dữ liệu cho trang quản trị kinh tế."""


def configure(context):
    globals().update(context)


def list_players_for_economy():
    rows = list_all_users()
    players = [dict(row) for row in (rows or []) if row.get("role") == "player"]
    players.sort(
        key=lambda item: (
            (item.get("display_name") or item.get("username") or "").lower(),
            (item.get("username") or "").lower(),
        )
    )
    return players


def list_recent_transactions(limit=100):
    return list_zcoin_transactions(limit=limit)


def list_codes(limit=150):
    return list_gift_codes(limit=limit)
