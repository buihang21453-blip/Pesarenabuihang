"""Nghiệp vụ Kho đồ và trang bị hồ sơ."""

from . import repository
from modules.shop.catalog import (
    CATEGORY_DEFINITIONS,
    EQUIPMENT_SLOT_BY_TYPE,
    EQUIPMENT_SLOT_LABELS,
    ITEM_TYPE_LABELS,
    RARITY_LABELS,
    category_for_item,
)

INVENTORY_TABS = (
    {"code": "all", "label": "Tất cả"},
    {"code": "equipped", "label": "Đang sử dụng"},
    {"code": "avatar_frame", "label": "Khung Avatar"},
    {"code": "profile_banner", "label": "Banner"},
    {"code": "name_style", "label": "Màu Tên"},
    {"code": "profile_badge", "label": "Huy hiệu"},
    {"code": "utility", "label": "Vật phẩm tiêu hao"},
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


def _decorate_inventory(row, item, equipped_by_inventory):
    inventory = dict(row or {})
    item = dict(item or {})
    metadata = _safe_dict(item.get("metadata"))
    inventory["item"] = item
    inventory["metadata"] = metadata
    inventory["item_name"] = item.get("name") or item.get("code") or "Vật phẩm"
    inventory["item_code"] = item.get("code")
    inventory["item_type"] = item.get("item_type")
    inventory["item_type_label"] = ITEM_TYPE_LABELS.get(item.get("item_type"), "Vật phẩm")
    inventory["category"] = category_for_item(item)
    inventory["rarity"] = item.get("rarity") or "common"
    inventory["rarity_label"] = RARITY_LABELS.get(inventory["rarity"], inventory["rarity"].title())
    inventory["image_url"] = asset_url(item.get("image_path") or "zcoin-logo.webp")
    inventory["quantity"] = max(0, _safe_int(inventory.get("quantity")))
    equipment = equipped_by_inventory.get(str(inventory.get("id")))
    inventory["equipment"] = equipment
    inventory["is_equipped"] = bool(equipment)
    inventory["equipment_slot"] = EQUIPMENT_SLOT_BY_TYPE.get(item.get("item_type"))
    inventory["can_equip"] = bool(inventory["equipment_slot"] and not item.get("is_consumable"))
    inventory["is_consumable"] = bool(item.get("is_consumable"))
    inventory["acquired_from_label"] = {
        "shop": "Mua từ Shop",
        "admin_grant": "Admin tặng",
        "gift_code": "Gift Code",
        "event": "Sự kiện",
    }.get(str(inventory.get("acquired_from") or ""), "Phần thưởng")
    return inventory


def build_inventory_context(user, active_tab="all", focus_item_code=""):
    active_tab = str(active_tab or "all").strip().lower()
    allowed_tabs = {tab["code"] for tab in INVENTORY_TABS}
    if active_tab not in allowed_tabs:
        active_tab = "all"

    setup_required = False
    try:
        rows = repository.list_inventory(user.get("id"))
        equipment_rows = repository.list_equipment(user.get("id"))
        items = repository.list_items_by_ids([row.get("item_id") for row in rows])
    except Exception as exc:
        app.logger.warning("Inventory schema unavailable: %s", exc)
        rows, equipment_rows, items = [], [], []
        setup_required = True

    items_by_id = {str(item.get("id")): item for item in items}
    equipped_by_inventory = {
        str(row.get("inventory_id")): dict(row)
        for row in equipment_rows
        if row.get("inventory_id")
    }
    decorated = [
        _decorate_inventory(row, items_by_id.get(str(row.get("item_id")), {}), equipped_by_inventory)
        for row in rows
    ]
    decorated = [row for row in decorated if row.get("item_code")]

    if active_tab == "all":
        visible = decorated
    elif active_tab == "equipped":
        visible = [row for row in decorated if row.get("is_equipped")]
    else:
        visible = [row for row in decorated if row.get("category") == active_tab]

    equipment_slots = []
    equipment_by_slot = {str(row.get("slot")): row for row in equipment_rows}
    inventory_by_id = {str(row.get("id")): row for row in decorated}
    for slot, label in EQUIPMENT_SLOT_LABELS.items():
        equipment = equipment_by_slot.get(slot)
        inventory_item = inventory_by_id.get(str((equipment or {}).get("inventory_id")))
        equipment_slots.append({
            "slot": slot,
            "label": label,
            "equipment": equipment,
            "inventory_item": inventory_item,
        })

    tab_counts = {tab["code"]: 0 for tab in INVENTORY_TABS}
    tab_counts["all"] = len(decorated)
    tab_counts["equipped"] = sum(1 for row in decorated if row.get("is_equipped"))
    for row in decorated:
        tab_counts[row.get("category")] = tab_counts.get(row.get("category"), 0) + 1

    display_name_tickets = sum(
        row.get("quantity", 0)
        for row in decorated
        if row.get("item_type") == "display_name_ticket"
    )

    return {
        "inventory_items": visible,
        "all_inventory_items": decorated,
        "inventory_tabs": INVENTORY_TABS,
        "inventory_tab_counts": tab_counts,
        "active_inventory_tab": active_tab,
        "equipment_slots": equipment_slots,
        "inventory_setup_required": setup_required,
        "display_name_ticket_count": display_name_tickets,
        "focus_item_code": str(focus_item_code or "").strip(),
    }


def equipment_error_message(exc):
    text = str(exc or "").lower()
    mappings = (
        ("inventory_item_not_found", "Không tìm thấy vật phẩm trong Kho đồ."),
        ("item_not_equippable", "Vật phẩm này không thể trang bị."),
        ("invalid_equipment_slot", "Vị trí trang bị không hợp lệ."),
        ("pgrst202", "Supabase chưa nhận RPC trang bị. Hãy chạy SQL Giai đoạn 3."),
    )
    for needle, message in mappings:
        if needle in text:
            return message
    return "Không thể thay đổi trang bị lúc này."
