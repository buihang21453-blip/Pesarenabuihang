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


def _remote_url(clean: str) -> str | None:
    if clean == "luckybox" or clean.startswith("luckybox/"):
        base = luckybox_asset_base_url()
        if base:
            relative = clean[9:] if clean.startswith("luckybox/") else ""
            return f"{base}/{quote(relative, safe='/')}" if relative else base
        return None

    if clean == "shop" or clean.startswith("shop/"):
        base = shop_asset_base_url()
        if base:
            relative = clean[5:] if clean.startswith("shop/") else ""
            return f"{base}/{quote(relative, safe='/')}" if relative else base
        return None

    base = asset_base_url()
    if base:
        return f"{base}/{quote(clean, safe='/')}"
    return None


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
