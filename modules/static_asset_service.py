"""PES Arena V1.6.87 asset routing helpers.

Policy: GitHub/Vercel static first, Supabase Storage fallback.
The local tree mirrors Supabase namespaces under /static/assets.
"""
from __future__ import annotations

import os
from urllib.parse import quote
from flask import url_for

SUPABASE_PROJECT_URL = "https://wlnvdfghatgeygecwrqb.supabase.co"
DEFAULT_PES_ASSET_ROOT = f"{SUPABASE_PROJECT_URL}/storage/v1/object/public/pes-assets"
DEFAULT_TEAM_LOGO_ROOT = f"{SUPABASE_PROJECT_URL}/storage/v1/object/public/team-logos"
KNOWN_PES_ROOTS = ("Giaidau/", "v1/", "v1.3.40/", "v1.14.41/", "LeBocThamGD2/")

def _clean_base(value):
    return (value or "").strip().rstrip("/")

def _mapped_path(filename):
    raw=str(filename or "").strip()
    if raw.startswith(("https://", "http://")):
        return raw
    clean=raw.lstrip("/")
    if clean.startswith("team-logos/") or clean.startswith(KNOWN_PES_ROOTS):
        return clean
    # Legacy logical assets (shop/, luckybox/, ranks/, logo...) live in v1.14.41.
    return f"v1.14.41/{clean}"

def asset_base_url():
    return "/static/assets"

def pes_asset_root_url():
    # New root-level override. Do not reuse legacy STATIC_ASSET_BASE_URL here because
    # older deployments point it directly at .../v1.14.41.
    return _clean_base(os.getenv("PES_ASSET_ROOT_URL")) or DEFAULT_PES_ASSET_ROOT

def team_logo_root_url():
    return _clean_base(os.getenv("TEAM_LOGO_BASE_URL")) or DEFAULT_TEAM_LOGO_ROOT

def asset_fallback_base_url():
    # Compatibility: general legacy logical assets are v1.14.41.
    return f"{pes_asset_root_url()}/v1.14.41"

def shop_asset_base_url():
    return _clean_base(os.getenv("SHOP_ASSET_BASE_URL")) or f"{pes_asset_root_url()}/v1.14.41/shop"

def luckybox_asset_base_url():
    return _clean_base(os.getenv("LUCKYBOX_ASSET_BASE_URL")) or f"{pes_asset_root_url()}/v1.14.41/luckybox"

def asset_url(filename):
    raw=str(filename or "").strip()
    if raw.startswith(("https://", "http://")):
        return raw
    mapped=_mapped_path(raw)
    return url_for("static", filename=f"assets/{mapped}")

def asset_fallback_url(filename):
    raw=str(filename or "").strip()
    if raw.startswith(("https://", "http://")):
        return raw
    mapped=_mapped_path(raw)
    if mapped.startswith("team-logos/"):
        rel=mapped[len("team-logos/"):]
        return f"{team_logo_root_url()}/{quote(rel, safe='/')}"
    return f"{pes_asset_root_url()}/{quote(mapped, safe='/')}"
