"""Truy cập dữ liệu Cửa hàng."""


def configure(context):
    globals().update(context)


def _rows(result):
    return [dict(row) for row in (getattr(result, "data", None) or [])]


def list_shop_items(include_unlisted=False, include_inactive=False):
    require_db()
    query = db.table("shop_items").select("*")
    if not include_unlisted:
        query = query.eq("is_listed", True)
    if not include_inactive:
        query = query.eq("is_active", True)
    result = execute_query(
        query.order("sort_order").order("created_at"),
        "shop_list_items",
        attempts=2,
    )
    return _rows(result)



def list_items_by_ids(item_ids):
    ids = sorted({str(item_id) for item_id in (item_ids or []) if item_id})
    if not ids:
        return []
    result = execute_query(
        db.table("shop_items").select("*").in_("id", ids),
        "shop_items_by_ids",
        attempts=2,
    )
    return _rows(result)

def get_shop_item(item_code):
    require_db()
    result = execute_query(
        db.table("shop_items").select("*").eq("code", str(item_code)).limit(1),
        "shop_get_item",
        attempts=2,
    )
    rows = _rows(result)
    return rows[0] if rows else None


def list_user_inventory_rows(user_id):
    require_db()
    result = execute_query(
        db.table("user_inventory")
        .select("*")
        .eq("user_id", str(user_id))
        .gt("quantity", 0)
        .order("updated_at", desc=True),
        "shop_user_inventory",
        attempts=2,
    )
    return _rows(result)


def list_user_equipment_rows(user_id):
    require_db()
    result = execute_query(
        db.table("user_equipment")
        .select("*")
        .eq("user_id", str(user_id)),
        "shop_user_equipment",
        attempts=2,
    )
    return _rows(result)


def purchase_item(user_id, item_code, coupon_inventory_id, request_key):
    require_db()
    result = execute_query(
        db.rpc(
            "purchase_shop_item",
            {
                "p_user_id": str(user_id),
                "p_item_code": str(item_code),
                "p_coupon_inventory_id": str(coupon_inventory_id) if coupon_inventory_id else None,
                "p_request_key": str(request_key),
            },
        ),
        "shop_purchase_item_rpc",
        attempts=2,
    )
    data = getattr(result, "data", None)
    if isinstance(data, list):
        return dict(data[0]) if data else {}
    return dict(data) if isinstance(data, dict) else {}
