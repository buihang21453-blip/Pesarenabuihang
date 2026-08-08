"""Nghiệp vụ quản trị Cửa hàng."""

from . import repository
from modules.shop.catalog import ITEM_TYPE_LABELS, RARITY_LABELS


def configure(context):
    globals().update(context)
    repository.configure(context)


def _safe_int(value, default=0):
    try:
        return int(value or 0)
    except (TypeError, ValueError, OverflowError):
        return default


def _safe_dict(value):
    return dict(value) if isinstance(value, dict) else {}


def _safe_load(label, loader, default):
    try:
        value = loader()
        return default if value is None else value
    except Exception as exc:
        app.logger.warning("Admin Shop load failed [%s]: %s", label, exc)
        return default


def build_page_context():
    items = _safe_load("items", repository.list_all_items, [])
    players = _safe_load("players", repository.list_players, [])
    purchases = _safe_load("purchases", lambda: repository.list_recent_purchases(100), [])
    setup_required = not items

    for item in items:
        item["metadata"] = _safe_dict(item.get("metadata"))
        item["rarity_label"] = RARITY_LABELS.get(item.get("rarity"), str(item.get("rarity") or "").title())
        item["item_type_label"] = ITEM_TYPE_LABELS.get(item.get("item_type"), "Vật phẩm")
        item["image_url"] = asset_url(item.get("image_path") or "zcoin-logo.webp")
        item["price_zcoin"] = max(0, _safe_int(item.get("price_zcoin")))

    item_names = {str(row.get("id")): row.get("name") for row in items}
    user_names = {
        str(row.get("id")): row.get("display_name") or row.get("username")
        for row in players
    }
    for row in purchases:
        row["item_name"] = item_names.get(str(row.get("item_id"))) or "Vật phẩm"
        row["user_name"] = user_names.get(str(row.get("user_id"))) or "Người chơi"

    stats = {
        "item_count": len(items),
        "listed_count": sum(1 for row in items if row.get("is_listed")),
        "reward_only_count": sum(1 for row in items if not row.get("is_listed") and row.get("is_active")),
        "purchase_count": len(purchases),
        "zcoin_spent": sum(max(0, _safe_int(row.get("final_price"))) for row in purchases),
    }
    return {
        "admin_shop_items": items,
        "admin_shop_players": players,
        "admin_shop_purchases": purchases,
        "admin_shop_stats": stats,
        "admin_shop_setup_required": setup_required,
    }


def parse_item_update(form):
    try:
        price = int(form.get("price_zcoin") or 0)
        sort_order = int(form.get("sort_order") or 0)
    except (TypeError, ValueError):
        raise ValueError("Giá và thứ tự phải là số nguyên.")
    if price < 0 or price > 10_000_000:
        raise ValueError("Giá vật phẩm phải từ 0 đến 10.000.000 Zcoin.")
    if sort_order < 0 or sort_order > 100_000:
        raise ValueError("Thứ tự hiển thị không hợp lệ.")
    return {
        "price_zcoin": price,
        "sort_order": sort_order,
        "is_active": form.get("is_active") == "1",
        "is_listed": form.get("is_listed") == "1",
        "is_featured": form.get("is_featured") == "1",
    }


def parse_grant(form):
    item_code = str(form.get("item_code") or "").strip()
    target_mode = str(form.get("target_mode") or "single").strip()
    target_user_id = str(form.get("target_user_id") or "").strip() or None
    note = str(form.get("note") or "").strip()
    try:
        quantity = int(form.get("quantity") or 1)
    except (TypeError, ValueError):
        quantity = 0
    if not item_code:
        raise ValueError("Hãy chọn vật phẩm cần tặng.")
    if quantity < 1 or quantity > 100:
        raise ValueError("Số lượng tặng phải từ 1 đến 100.")
    grant_all = target_mode == "all"
    if not grant_all and not target_user_id:
        raise ValueError("Hãy chọn người chơi nhận vật phẩm.")
    if len(note) > 300:
        raise ValueError("Ghi chú không được vượt quá 300 ký tự.")
    return {
        "item_code": item_code,
        "quantity": quantity,
        "target_user_id": target_user_id,
        "grant_all": grant_all,
        "note": note,
    }


def admin_error_message(exc):
    text = str(exc or "").lower()
    mappings = (
        ("shop_admin_permission_denied", "Bạn không có quyền quản trị Cửa hàng."),
        ("shop_item_not_found", "Không tìm thấy vật phẩm."),
        ("shop_target_not_found", "Không tìm thấy người chơi nhận vật phẩm."),
        ("pgrst202", "Supabase chưa nhận RPC Cửa hàng. Hãy chạy SQL Giai đoạn 3."),
    )
    for needle, message in mappings:
        if needle in text:
            return message
    return "Không thể thực hiện thao tác Cửa hàng."
