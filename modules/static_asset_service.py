"""Local-first static asset URLs with Supabase Storage fallback.

V1.6.86 policy:
- System assets are requested from GitHub/Vercel first under ``/static/assets``.
- If an image is not present there, browser-side fallback switches to Supabase Storage.
- Existing absolute http(s) URLs from DB are preserved unchanged.
- Shop/LuckyBox keep their dedicated Supabase fallback namespaces.

Environment variables (fallback destinations):
- STATIC_ASSET_BASE_URL: general Supabase/public asset base.
- SHOP_ASSET_BASE_URL: optional Shop fallback base.
- LUCKYBOX_ASSET_BASE_URL: optional Lucky Box fallback base.
"""
from __future__ import annotations

import os
from urllib.parse import quote

from flask import url_for


def _clean_base(value: str | None) -> str:
    return (value or "").strip().rstrip("/")


DEFAULT_PES_ASSET_V11441_BASE_URL = "https://wlnvdfghatgeygecwrqb.supabase.co/storage/v1/object/public/pes-assets/v1.14.41"
DEFAULT_SHOP_ASSET_BASE_URL = f"{DEFAULT_PES_ASSET_V11441_BASE_URL}/shop"
DEFAULT_LUCKYBOX_ASSET_BASE_URL = f"{DEFAULT_PES_ASSET_V11441_BASE_URL}/luckybox"


def asset_base_url() -> str:
    """Primary browser base. V1.6.86 always prefers Vercel static assets."""
    return "/static/assets"


def asset_fallback_base_url() -> str:
    """General remote fallback, normally Supabase Storage."""
    return _clean_base(os.getenv("STATIC_ASSET_BASE_URL")) or DEFAULT_PES_ASSET_V11441_BASE_URL


def shop_asset_base_url() -> str:
    return _clean_base(os.getenv("SHOP_ASSET_BASE_URL")) or DEFAULT_SHOP_ASSET_BASE_URL


def luckybox_asset_base_url() -> str:
    return _clean_base(os.getenv("LUCKYBOX_ASSET_BASE_URL")) or DEFAULT_LUCKYBOX_ASSET_BASE_URL


def asset_url(filename: str) -> str:
    """Return the preferred local Vercel URL for a logical system asset."""
    raw = str(filename or "").strip()
    if raw.startswith(("https://", "http://")):
        return raw

    clean = raw.lstrip("/")
    return url_for("static", filename=f"assets/{clean}")


def asset_fallback_url(filename: str) -> str:
    """Return the Supabase/public fallback URL for a logical system asset."""
    raw = str(filename or "").strip()
    if raw.startswith(("https://", "http://")):
        return raw

    clean = raw.lstrip("/")
    if clean == "luckybox" or clean.startswith("luckybox/"):
        base = luckybox_asset_base_url()
        relative = clean[9:] if clean.startswith("luckybox/") else ""
        return f"{base}/{quote(relative, safe='/')}" if relative else base

    if clean == "shop" or clean.startswith("shop/"):
        base = shop_asset_base_url()
        relative = clean[5:] if clean.startswith("shop/") else ""
        return f"{base}/{quote(relative, safe='/')}" if relative else base

    return f"{asset_fallback_base_url()}/{quote(clean, safe='/')}"
