"""Quản lý URL tài nguyên tĩnh theo mô hình Vercel-first.

V1.2.20:
- STATIC_ASSET_MODE=auto (mặc định): nếu file có trong ``/static`` thì dùng Vercel
  Static/CDN; nếu chưa có file local thì mới fallback sang URL Storage cũ.
- STATIC_ASSET_MODE=local: luôn dùng ``/static``.
- STATIC_ASSET_MODE=remote: luôn ưu tiên các *_ASSET_BASE_URL như trước.

Biến môi trường tương thích:
- STATIC_ASSET_BASE_URL: URL public tài nguyên chung (fallback/remote).
- SHOP_ASSET_BASE_URL: URL public riêng ``shop``.
- LUCKYBOX_ASSET_BASE_URL: URL public riêng ``luckybox``.

Mục tiêu là cho phép chuyển dần ảnh từ Supabase Storage về Vercel Static mà
không làm mất ảnh trong lúc migration.
"""
from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import quote

from flask import current_app, url_for


def _clean_base(value: str | None) -> str:
    return (value or "").strip().rstrip("/")


def asset_mode() -> str:
    mode = (os.getenv("STATIC_ASSET_MODE") or "auto").strip().lower()
    return mode if mode in {"auto", "local", "remote"} else "auto"


def asset_base_url() -> str:
    return _clean_base(os.getenv("STATIC_ASSET_BASE_URL"))


def shop_asset_base_url() -> str:
    return _clean_base(os.getenv("SHOP_ASSET_BASE_URL"))


def luckybox_asset_base_url() -> str:
    return _clean_base(os.getenv("LUCKYBOX_ASSET_BASE_URL"))


def _local_asset_exists(filename: str) -> bool:
    try:
        static_folder = current_app.static_folder
    except RuntimeError:
        static_folder = None
    if not static_folder:
        return False
    try:
        root = Path(static_folder).resolve()
        candidate = (root / filename).resolve()
        candidate.relative_to(root)
        return candidate.is_file()
    except (OSError, ValueError):
        return False


def supabase_asset_root() -> str:
    """Public root của bucket pes-assets, suy ra trực tiếp từ SUPABASE_URL.

    Đây là fallback an toàn khi Production chưa khai báo các *_ASSET_BASE_URL.
    Không chứa service-role key và chỉ trỏ tới bucket public.
    """
    supabase_url = _clean_base(os.getenv("SUPABASE_URL"))
    if not supabase_url:
        return ""
    return f"{supabase_url}/storage/v1/object/public/pes-assets"


def _derived_version_base() -> str:
    root = supabase_asset_root()
    return f"{root}/v1.14.41" if root else ""


def _join_public(base: str, relative: str) -> str | None:
    base = _clean_base(base)
    relative = str(relative or "").strip().lstrip("/")
    if not base:
        return None
    return f"{base}/{quote(relative, safe='/')}" if relative else base


def _remote_url(clean: str) -> str | None:
    # Logo 6 chế độ đã tồn tại ở nhánh riêng v1.3.40 của bucket.
    # Không ghép chúng vào STATIC_ASSET_BASE_URL=/v1.14.41 vì sẽ tạo URL sai
    # .../v1.14.41/v1.3.40/modes/*.webp.
    if clean == "v1.3.40" or clean.startswith("v1.3.40/"):
        root = supabase_asset_root()
        direct = _join_public(root, clean)
        if direct:
            return direct

    if clean == "luckybox" or clean.startswith("luckybox/"):
        relative = clean[9:] if clean.startswith("luckybox/") else ""
        # Ưu tiên biến cấu hình cũ; nếu Vercel chưa khai báo thì tự suy ra
        # từ SUPABASE_URL để ảnh Lucky Box không rơi về /static và bị 404.
        base = luckybox_asset_base_url() or (f"{_derived_version_base()}/luckybox" if _derived_version_base() else "")
        return _join_public(base, relative)

    if clean == "shop" or clean.startswith("shop/"):
        relative = clean[5:] if clean.startswith("shop/") else ""
        base = shop_asset_base_url() or (f"{_derived_version_base()}/shop" if _derived_version_base() else "")
        return _join_public(base, relative)

    # Tài nguyên chung: vẫn ưu tiên STATIC_ASSET_BASE_URL nếu có. Nếu chưa có
    # thì suy ra nhánh asset hiện hành từ SUPABASE_URL.
    base = asset_base_url() or _derived_version_base()
    return _join_public(base, clean)


def asset_url(filename: str) -> str:
    clean = str(filename or "").strip().lstrip("/")
    mode = asset_mode()

    # Vercel-first: file đã nằm trong project thì để Vercel CDN phục vụ trực tiếp.
    if mode == "local" or (mode == "auto" and _local_asset_exists(clean)):
        return url_for("static", filename=clean)

    remote = _remote_url(clean)
    if remote:
        return remote

    # Khi chưa cấu hình remote hoặc migration đã hoàn tất, quay về local.
    return url_for("static", filename=clean)
