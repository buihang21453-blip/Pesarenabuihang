"""Truy cập dữ liệu Kho đồ và trang bị."""


def configure(context):
    globals().update(context)


def _rows(result):
    return [dict(row) for row in (getattr(result, "data", None) or [])]


def list_inventory(user_id):
    require_db()
    result = execute_query(
        db.table("user_inventory")
        .select("*")
        .eq("user_id", str(user_id))
        .gt("quantity", 0)
        .order("updated_at", desc=True),
        "inventory_list",
        attempts=2,
    )
    return _rows(result)


def list_items_by_ids(item_ids):
    ids = sorted({str(item_id) for item_id in item_ids if item_id})
    if not ids:
        return []
    result = execute_query(
        db.table("shop_items").select("*").in_("id", ids),
        "inventory_items",
        attempts=2,
    )
    return _rows(result)


def list_equipment(user_id):
    require_db()
    result = execute_query(
        db.table("user_equipment")
        .select("*")
        .eq("user_id", str(user_id)),
        "inventory_equipment",
        attempts=2,
    )
    return _rows(result)


def equip_inventory_item(user_id, inventory_id):
    result = execute_query(
        db.rpc(
            "equip_shop_item",
            {
                "p_user_id": str(user_id),
                "p_inventory_id": str(inventory_id),
            },
        ),
        "inventory_equip_rpc",
        attempts=2,
    )
    data = getattr(result, "data", None)
    if isinstance(data, list):
        return dict(data[0]) if data else {}
    return dict(data) if isinstance(data, dict) else {}


def unequip_slot(user_id, slot):
    result = execute_query(
        db.rpc(
            "unequip_shop_slot",
            {
                "p_user_id": str(user_id),
                "p_slot": str(slot),
            },
        ),
        "inventory_unequip_rpc",
        attempts=2,
    )
    data = getattr(result, "data", None)
    if isinstance(data, list):
        return dict(data[0]) if data else {}
    return dict(data) if isinstance(data, dict) else {}
