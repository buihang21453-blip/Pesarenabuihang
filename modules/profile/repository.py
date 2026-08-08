"""Truy cập dữ liệu dành riêng cho Hồ sơ cá nhân."""


def configure(context):
    globals().update(context)


def update_avatar_record(user_id, avatar_url, avatar_path):
    return execute_query(
        db.table("users").update({
            "avatar_url": avatar_url,
            "avatar_path": avatar_path,
            "avatar_updated_at": now_iso(),
        }).eq("id", user_id),
        "profile_update_avatar",
    )


def clear_avatar_record(user_id):
    return execute_query(
        db.table("users").update({
            "avatar_url": None,
            "avatar_path": None,
            "avatar_updated_at": now_iso(),
        }).eq("id", user_id),
        "profile_delete_avatar",
    )


def find_display_name_duplicates(display_name):
    try:
        result = execute_query(
            db.table("users").select("id,display_name").ilike("display_name", display_name).limit(5),
            "profile_check_display_name_duplicate",
        )
        return result.data or []
    except Exception:
        return []


def update_display_name_record(user_id, display_name, change_count):
    return execute_query(
        db.table("users").update({
            "display_name": display_name,
            "display_name_change_count": change_count,
            "display_name_changed_at": now_iso(),
        }).eq("id", user_id),
        "profile_update_display_name",
    )


def update_display_name_with_entitlement(user_id, display_name):
    """Đổi tên nguyên tử và bắt buộc tiêu thụ 1 Vé đổi tên trong Kho đồ."""
    result = execute_query(
        db.rpc(
            "change_display_name_with_ticket",
            {
                "p_user_id": str(user_id),
                "p_new_display_name": str(display_name),
            },
        ),
        "profile_change_display_name_ticket",
        attempts=2,
    )
    data = getattr(result, "data", None)
    if isinstance(data, list):
        return dict(data[0]) if data else {}
    return dict(data) if isinstance(data, dict) else {}


def get_display_name_ticket_count(user_id):
    """Đếm vé đổi tên còn trong Kho đồ; thiếu schema trả về 0."""
    try:
        item_result = execute_query(
            db.table("shop_items")
            .select("id")
            .eq("code", "display_name_change_ticket")
            .limit(1),
            "profile_name_ticket_item",
            attempts=1,
        )
        if not item_result.data:
            return 0
        item_id = item_result.data[0].get("id")
        inventory_result = execute_query(
            db.table("user_inventory")
            .select("quantity")
            .eq("user_id", str(user_id))
            .eq("item_id", str(item_id))
            .limit(1),
            "profile_name_ticket_inventory",
            attempts=1,
        )
        return int((inventory_result.data[0].get("quantity") if inventory_result.data else 0) or 0)
    except Exception:
        return 0
