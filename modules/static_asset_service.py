"""URL tài nguyên tĩnh có thể chuyển sang Supabase Storage.

Biến môi trường hỗ trợ:
- STATIC_ASSET_BASE_URL: URL public cho tài nguyên tĩnh chung.
- SHOP_ASSET_BASE_URL: URL public riêng cho ``static/shop``.
- LUCKYBOX_ASSET_BASE_URL: URL public riêng cho thư mục Lucky Box.
- ROOM_ASSET_BASE_URL: URL public riêng cho asset giao diện phòng đấu.

Từ V1.3.62, ảnh giao diện Production dùng Supabase Storage làm nguồn mặc định.
Các biến môi trường chỉ còn là override khi cần đổi bucket/path; không cần giữ
bản ảnh local trùng lặp trong ZIP triển khai.
"""
from __future__ import annotations

import os
from urllib.parse import quote

from flask import url_for


def _clean_base(value: str | None) -> str:
    return (value or "").strip().rstrip("/")


DEFAULT_STATIC_ASSET_BASE_URL = (
    "https://wlnvdfghatgeygecwrqb.supabase.co/storage/v1/object/public/"
    "pes-assets/v1"
)
DEFAULT_SHOP_ASSET_BASE_URL = (
    "https://wlnvdfghatgeygecwrqb.supabase.co/storage/v1/object/public/"
    "pes-assets/v1.14.41/shop"
)
DEFAULT_LUCKYBOX_ASSET_BASE_URL = (
    "https://wlnvdfghatgeygecwrqb.supabase.co/storage/v1/object/public/"
    "pes-assets/v1.14.41/luckybox"
)


def asset_base_url() -> str:
    return _clean_base(os.getenv("STATIC_ASSET_BASE_URL") or DEFAULT_STATIC_ASSET_BASE_URL)


def shop_asset_base_url() -> str:
    return _clean_base(os.getenv("SHOP_ASSET_BASE_URL") or DEFAULT_SHOP_ASSET_BASE_URL)


def luckybox_asset_base_url() -> str:
    return _clean_base(os.getenv("LUCKYBOX_ASSET_BASE_URL") or DEFAULT_LUCKYBOX_ASSET_BASE_URL)


DEFAULT_ROOM_ASSET_BASE_URL = (
    "https://wlnvdfghatgeygecwrqb.supabase.co/storage/v1/object/public/"
    "pes-assets/room-assets/v1.3.18"
)


def room_asset_base_url() -> str:
    """Return configured room asset URL, defaulting to the project's public bucket."""
    return _clean_base(os.getenv("ROOM_ASSET_BASE_URL") or DEFAULT_ROOM_ASSET_BASE_URL)


def room_asset_url(filename: str) -> str:
    """Return public Supabase URL for room assets.

    V1.3.62 removes the duplicated local room image bundle. The environment
    variable remains an optional override, while the verified public Storage
    path is the safe default.
    """
    clean = str(filename or "").strip().lstrip("/")
    encoded = quote(clean, safe="/")
    return f"{room_asset_base_url()}/{encoded}"


# V1.3.40: 6 logo chế độ được tách riêng khỏi bộ Room asset cũ.
# Người quản trị chỉ cần upload 1.webp -> 6.webp vào đúng thư mục này.
DEFAULT_MODE_ASSET_BASE_URL = (
    "https://wlnvdfghatgeygecwrqb.supabase.co/storage/v1/object/public/"
    "pes-assets/room-assets/v1.3.40/modes"
)

# Người dùng đặt tên file 1 -> 6 theo đúng thứ tự tên hiển thị trên giao diện.
# 1 Rank thường Random | 2 Random 3 chọn 1 | 3 Lượt đi/về | 4 BO3 | 5 Chiến thuật BO3 | 6 Cấm chọn BO3
MODE_LOGO_FILE_BY_CODE = {
    "rank_random": "1.webp",
    "random3_pick1": "2.webp",
    "home_away": "3.webp",
    "bo3": "4.webp",
    "tactical_bo3": "5.webp",
    "ban_pick_bo3": "6.webp",
}


def mode_asset_base_url() -> str:
    """Public base URL dành riêng cho 6 logo chế độ Rank."""
    return _clean_base(os.getenv("MODE_ASSET_BASE_URL") or DEFAULT_MODE_ASSET_BASE_URL)


def mode_asset_url(mode_code: str) -> str:
    """Return URL logo cho một mã chế độ, map sang file 1.webp -> 6.webp."""
    code = str(mode_code or "").strip()
    filename = MODE_LOGO_FILE_BY_CODE.get(code)
    if not filename:
        # Giữ fallback dễ chẩn đoán nếu sau này thêm mode mới mà quên map logo.
        filename = f"{quote(code, safe='')}.webp" if code else "3.webp"
    # V1.3.41: logo mode chỉ sống trên Supabase v1.3.40; không giữ bản local trùng lặp.
    return f"{mode_asset_base_url()}/{filename}"

def asset_url(filename: str) -> str:
    clean = str(filename or "").strip().lstrip("/")
    encoded = quote(clean, safe="/")

    if clean == "luckybox" or clean.startswith("luckybox/"):
        luckybox_base = luckybox_asset_base_url()
        if luckybox_base:
            relative = clean[9:] if clean.startswith("luckybox/") else ""
            return f"{luckybox_base}/{quote(relative, safe='/')}" if relative else luckybox_base
        return url_for("static", filename=clean)

    if clean == "shop" or clean.startswith("shop/"):
        shop_base = shop_asset_base_url()
        if shop_base:
            relative = clean[5:] if clean.startswith("shop/") else ""
            return f"{shop_base}/{quote(relative, safe='/')}" if relative else shop_base
        return url_for("static", filename=clean)

    base = asset_base_url()
    if base:
        return f"{base}/{encoded}"
    return url_for("static", filename=clean)
