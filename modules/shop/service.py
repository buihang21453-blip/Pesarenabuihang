"""Nghiệp vụ hiển thị và mua vật phẩm trong Cửa hàng."""

from datetime import datetime, timezone
import uuid

from . import repository
from .catalog import (
    CATEGORY_DEFINITIONS,
    CATEGORY_LABELS,
    CONSUMABLE_TYPES,
    EQUIPMENT_SLOT_BY_TYPE,
    ITEM_TYPE_LABELS,
    RARITY_LABELS,
    RARITY_ORDER,
    category_for_item,
)


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


def _parse_time(value):
    if not value:
        return None
    text = str(value).replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except (TypeError, ValueError):
        return None


def _decorate_item(item, inventory_by_item_id, equipment_by_item_id, current_balance):
    row = dict(item or {})
    metadata = _safe_dict(row.get("metadata"))
    row["metadata"] = metadata
    row["price_zcoin"] = max(0, _safe_int(row.get("price_zcoin")))
    row["rarity"] = str(row.get("rarity") or "common")
    row["rarity_label"] = RARITY_LABELS.get(row["rarity"], row["rarity"].title())
    row["rarity_order"] = RARITY_ORDER.get(row["rarity"], 0)
    row["item_type_label"] = ITEM_TYPE_LABELS.get(row.get("item_type"), "Vật phẩm")
    row["category"] = category_for_item(row)
    row["category_label"] = CATEGORY_LABELS.get(row["category"], "Vật phẩm")
    row["image_url"] = asset_url(row.get("image_path") or "zcoin-logo.webp")
    row["preview_url"] = asset_url(row.get("preview_path") or row.get("image_path") or "zcoin-logo.webp")
    inventory = inventory_by_item_id.get(str(row.get("id")))
    row["inventory"] = inventory
    row["owned"] = bool(inventory and _safe_int(inventory.get("quantity")) > 0)
    row["quantity_owned"] = _safe_int((inventory or {}).get("quantity"))
    row["is_equipped"] = str(row.get("id")) in equipment_by_item_id
    row["is_consumable"] = bool(row.get("is_consumable")) or row.get("item_type") in CONSUMABLE_TYPES
    row["is_unique"] = bool(row.get("is_unique"))
    row["can_afford"] = current_balance >= row["price_zcoin"]
    row["can_buy"] = bool(
        row.get("is_active")
        and row.get("is_listed")
        and row["price_zcoin"] >= 0
        and (not row["is_unique"] or not row["owned"])
        and row["can_afford"]
    )
    row["equipment_slot"] = EQUIPMENT_SLOT_BY_TYPE.get(row.get("item_type"))
    row["discount_percent"] = max(0, _safe_int(metadata.get("discount_percent")))
    row["max_discount"] = max(0, _safe_int(metadata.get("max_discount")))
    row["minimum_subtotal"] = max(0, _safe_int(metadata.get("minimum_subtotal")))
    return row


def _safe_catalog_load(user_id):
    try:
        listed_items = repository.list_shop_items()
        inventory = repository.list_user_inventory_rows(user_id)
        equipment = repository.list_user_equipment_rows(user_id)
        listed_ids = {str(item.get("id")) for item in listed_items if item.get("id")}
        extra_ids = [
            row.get("item_id") for row in inventory
            if row.get("item_id") and str(row.get("item_id")) not in listed_ids
        ]
        owned_unlisted_items = repository.list_items_by_ids(extra_ids)
        return listed_items, owned_unlisted_items, inventory, equipment, False
    except Exception as exc:
        app.logger.warning("Shop schema unavailable: %s", exc)
        return [], [], [], [], True


def build_shop_context(user, active_category="featured"):
    active_category = str(active_category or "featured").strip().lower()
    allowed_categories = {item["code"] for item in CATEGORY_DEFINITIONS}
    if active_category not in allowed_categories:
        active_category = "featured"

    items, owned_unlisted_items, inventory_rows, equipment_rows, setup_required = _safe_catalog_load(user.get("id"))
    inventory_by_item_id = {
        str(row.get("item_id")): dict(row)
        for row in inventory_rows
        if row.get("item_id")
    }
    equipment_by_item_id = {
        str(row.get("item_id")): dict(row)
        for row in equipment_rows
        if row.get("item_id")
    }
    balance = max(0, _safe_int(user.get("zcoin_balance")))
    decorated = [
        _decorate_item(row, inventory_by_item_id, equipment_by_item_id, balance)
        for row in items
    ]
    owned_unlisted_decorated = [
        _decorate_item(row, inventory_by_item_id, equipment_by_item_id, balance)
        for row in owned_unlisted_items
    ]

    featured = [row for row in decorated if row.get("is_featured")]
    if not featured:
        featured = sorted(
            decorated,
            key=lambda row: (-row.get("rarity_order", 0), row.get("sort_order", 9999)),
        )[:6]

    if active_category == "featured":
        visible_items = featured
    else:
        visible_items = [row for row in decorated if row.get("category") == active_category]

    coupons = [
        row for row in (decorated + owned_unlisted_decorated)
        if row.get("item_type") == "discount_coupon" and row.get("owned")
    ]
    for row in decorated:
        if row.get("item_type") == "discount_coupon":
            row["eligible_coupons"] = []
        else:
            row["eligible_coupons"] = [
                coupon for coupon in coupons
                if row.get("price_zcoin", 0) >= coupon.get("minimum_subtotal", 0)
            ]

    category_counts = {item["code"]: 0 for item in CATEGORY_DEFINITIONS}
    category_counts["featured"] = len(featured)
    for row in decorated:
        category_counts[row.get("category")] = category_counts.get(row.get("category"), 0) + 1

    return {
        "shop_items": visible_items,
        "all_shop_items": decorated,
        "shop_featured_items": featured,
        "shop_categories": CATEGORY_DEFINITIONS,
        "shop_category_counts": category_counts,
        "active_shop_category": active_category,
        "available_coupons": coupons,
        "shop_setup_required": setup_required,
        "shop_purchase_token": uuid.uuid4().hex,
    }


def purchase_for_user(user, item_code, coupon_inventory_id, request_key):
    clean_code = str(item_code or "").strip()
    clean_key = str(request_key or "").strip()
    if not clean_code or len(clean_code) > 100:
        raise ValueError("Mã vật phẩm không hợp lệ.")
    if not clean_key or len(clean_key) > 120:
        raise ValueError("Phiên mua hàng không hợp lệ. Hãy tải lại trang.")

    result = repository.purchase_item(
        user.get("id"),
        clean_code,
        coupon_inventory_id,
        clean_key,
    )
    if not result:
        raise RuntimeError("Cửa hàng không trả về kết quả giao dịch.")
    return result


def purchase_error_message(exc):
    text = str(exc or "").lower()
    mappings = (
        ("shop_item_not_found", "Không tìm thấy vật phẩm trong Cửa hàng."),
        ("shop_item_not_for_sale", "Vật phẩm này hiện không được bày bán."),
        ("shop_item_unavailable", "Vật phẩm này hiện không khả dụng."),
        ("shop_item_already_owned", "Bạn đã sở hữu vật phẩm này."),
        ("insufficient_zcoin", "Số dư Zcoin của bạn không đủ."),
        ("invalid_shop_coupon", "Phiếu giảm giá không hợp lệ hoặc đã hết."),
        ("coupon_not_eligible", "Phiếu giảm giá không áp dụng cho vật phẩm này."),
        ("coupon_minimum_not_met", "Giá vật phẩm chưa đạt mức tối thiểu của phiếu giảm giá."),
        ("shop_schema", "Cửa hàng chưa được cài đặt trên Supabase."),
        ("purchase_shop_item", "Cửa hàng chưa được cài đặt trên Supabase."),
        ("pgrst202", "Supabase chưa nhận RPC mua vật phẩm. Hãy chạy SQL Giai đoạn 3."),
    )
    for needle, message in mappings:
        if needle in text:
            return message
    return "Không thể hoàn tất giao dịch. Hãy kiểm tra Vercel Logs rồi thử lại."
