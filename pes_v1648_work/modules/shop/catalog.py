"""Hằng số catalog Shop Giai đoạn 3.

Database là nguồn dữ liệu chính. Các hằng số này chỉ chuẩn hóa cách hiển thị,
slot trang bị và thông báo của ứng dụng.
"""

CATEGORY_DEFINITIONS = (
    {"code": "featured", "label": "Nổi bật", "icon": "✦"},
    {"code": "avatar_frame", "label": "Khung Avatar", "icon": "◉"},
    {"code": "profile_banner", "label": "Banner Hồ sơ", "icon": "▰"},
    {"code": "name_style", "label": "Màu Tên", "icon": "A"},
    {"code": "profile_badge", "label": "Huy hiệu", "icon": "◆"},
    {"code": "utility", "label": "Tiện ích", "icon": "✦"},
)

CATEGORY_LABELS = {item["code"]: item["label"] for item in CATEGORY_DEFINITIONS}

RARITY_LABELS = {
    "common": "Phổ thông",
    "rare": "Hiếm",
    "epic": "Sử thi",
    "elite": "Tinh anh",
    "legendary": "Huyền thoại",
}

RARITY_ORDER = {
    "common": 1,
    "rare": 2,
    "epic": 3,
    "elite": 4,
    "legendary": 5,
}

ITEM_TYPE_LABELS = {
    "avatar_frame": "Khung Avatar",
    "profile_banner": "Banner Hồ sơ",
    "name_style": "Màu Tên",
    "profile_badge": "Huy hiệu cạnh tên",
    "display_name_ticket": "Vé đổi tên hiển thị",
    "discount_coupon": "Phiếu giảm giá",
}

EQUIPMENT_SLOT_BY_TYPE = {
    "avatar_frame": "avatar_frame",
    "profile_banner": "profile_banner",
    "name_style": "name_style",
    "profile_badge": "profile_badge",
}

EQUIPMENT_SLOT_LABELS = {
    "avatar_frame": "Khung Avatar",
    "profile_banner": "Banner Hồ sơ",
    "name_style": "Màu Tên",
    "profile_badge": "Huy hiệu",
}

CONSUMABLE_TYPES = {"display_name_ticket", "discount_coupon"}


def category_for_item(item):
    item_type = str((item or {}).get("item_type") or "")
    return item_type if item_type in EQUIPMENT_SLOT_BY_TYPE else "utility"
