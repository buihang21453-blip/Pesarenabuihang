"""URL tài nguyên tĩnh có thể chuyển sang Supabase Storage.

Biến môi trường hỗ trợ:
- STATIC_ASSET_BASE_URL: URL public cho tài nguyên tĩnh chung.
- SHOP_ASSET_BASE_URL: URL public riêng cho ``static/shop``.
- LUCKYBOX_ASSET_BASE_URL: URL public riêng cho thư mục Lucky Box.

Khi biến tương ứng để trống, hệ thống tự dùng file trong ``/static``. Việc tách
Shop ra thành URL riêng cho phép chuyển dần ảnh nặng lên Storage mà không ảnh
hưởng logo hoặc tài nguyên giao diện thiết yếu.
"""
from __future__ import annotations

import os
from urllib.parse import quote

from flask import url_for


def _clean_base(value: str | None) -> str:
    return (value or "").strip().rstrip("/")


def asset_base_url() -> str:
    return _clean_base(os.getenv("STATIC_ASSET_BASE_URL"))


DEFAULT_PES_ASSET_V11441_BASE_URL = "https://wlnvdfghatgeygecwrqb.supabase.co/storage/v1/object/public/pes-assets/v1.14.41"
DEFAULT_SHOP_ASSET_BASE_URL = "https://wlnvdfghatgeygecwrqb.supabase.co/storage/v1/object/public/pes-assets/v1.14.41/shop"
DEFAULT_LUCKYBOX_ASSET_BASE_URL = "https://wlnvdfghatgeygecwrqb.supabase.co/storage/v1/object/public/pes-assets/v1.14.41/luckybox"


def shop_asset_base_url() -> str:
    explicit = _clean_base(os.getenv("SHOP_ASSET_BASE_URL"))
    if explicit:
        return explicit
    # Shop là namespace asset riêng. Không kế thừa STATIC_ASSET_BASE_URL vì
    # asset chung của site có thể đang ở /v1, trong khi Shop nằm ở /v1.14.41/shop.
    return DEFAULT_SHOP_ASSET_BASE_URL


def luckybox_asset_base_url() -> str:
    explicit = _clean_base(os.getenv("LUCKYBOX_ASSET_BASE_URL"))
    if explicit:
        return explicit
    # Lucky Box dùng cùng bộ vật phẩm/trang bị version v1.14.41 và phải tách
    # khỏi STATIC_ASSET_BASE_URL chung của website.
    return DEFAULT_LUCKYBOX_ASSET_BASE_URL


def asset_url(filename: str) -> str:
    raw = str(filename or "").strip()
    # Cho phép Supabase/DB lưu URL public đầy đủ mà không bị quote thành đường local sai.
    if raw.startswith(("https://", "http://")):
        return raw

    clean = raw.lstrip("/")
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
