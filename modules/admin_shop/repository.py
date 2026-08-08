"""Repository quản trị catalog và cấp vật phẩm."""


def configure(context):
    globals().update(context)


def _rows(result):
    return [dict(row) for row in (getattr(result, "data", None) or [])]


def list_all_items():
    result = execute_query(
        db.table("shop_items").select("*").order("sort_order").order("created_at"),
        "admin_shop_items",
        attempts=2,
    )
    return _rows(result)


def list_players():
    rows = list_all_users()
    result = [dict(row) for row in (rows or []) if row.get("role") == "player"]
    result.sort(key=lambda row: str(row.get("display_name") or row.get("username") or "").casefold())
    return result


def list_recent_purchases(limit=100):
    result = execute_query(
        db.table("shop_purchases")
        .select("*")
        .order("created_at", desc=True)
        .limit(max(1, min(int(limit or 100), 300))),
        "admin_shop_purchases",
        attempts=2,
    )
    return _rows(result)


def update_item(item_id, payload):
    result = execute_query(
        db.table("shop_items")
        .update(dict(payload, updated_at=now_iso()))
        .eq("id", str(item_id)),
        "admin_shop_update_item",
        attempts=2,
    )
    rows = _rows(result)
    return rows[0] if rows else None


def grant_item(actor_user_id, item_code, quantity, target_user_id=None, grant_all=False, note=""):
    result = execute_query(
        db.rpc(
            "admin_grant_shop_item",
            {
                "p_actor_user_id": str(actor_user_id),
                "p_item_code": str(item_code),
                "p_quantity": int(quantity),
                "p_target_user_id": str(target_user_id) if target_user_id else None,
                "p_all_players": bool(grant_all),
                "p_note": str(note or ""),
            },
        ),
        "admin_shop_grant_item_rpc",
        attempts=2,
    )
    data = getattr(result, "data", None)
    if isinstance(data, list):
        return dict(data[0]) if data else {}
    return dict(data) if isinstance(data, dict) else {}
