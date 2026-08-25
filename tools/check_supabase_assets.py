#!/usr/bin/env python3
"""Kiểm tra toàn bộ tài nguyên trong SUPABASE_ASSET_MANIFEST.csv.

Cách dùng:
  set STATIC_ASSET_BASE_URL=https://PROJECT.supabase.co/storage/v1/object/public/pes-assets/v1
  set SHOP_ASSET_BASE_URL=https://PROJECT.supabase.co/storage/v1/object/public/pes-assets/v1.14.41/shop
  set LUCKYBOX_ASSET_BASE_URL=https://PROJECT.supabase.co/storage/v1/object/public/pes-assets/v1.14.41/luckybox
  python tools/check_supabase_assets.py

Script chỉ gửi HEAD/GET nhẹ, không sửa dữ liệu Supabase.
"""
from __future__ import annotations

import csv
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "SUPABASE_ASSET_MANIFEST.csv"


def clean_base(value: str | None) -> str:
    return (value or "").strip().rstrip("/")


def build_url(path: str, static_base: str, shop_base: str) -> str:
    clean = path.strip().lstrip("/")
    if clean.startswith("shop/") and shop_base:
        return f"{shop_base}/{quote(clean[5:], safe='/')}"
    return f"{static_base}/{quote(clean, safe='/')}"


def check_url(url: str) -> tuple[bool, int | None, str]:
    headers = {"User-Agent": "PES-Arena-Asset-Checker/1.0"}
    for method in ("HEAD", "GET"):
        req = Request(url, headers=headers, method=method)
        if method == "GET":
            req.add_header("Range", "bytes=0-0")
        try:
            with urlopen(req, timeout=15) as response:
                status = int(getattr(response, "status", 200))
                content_type = response.headers.get("Content-Type", "")
                return 200 <= status < 400, status, content_type
        except HTTPError as exc:
            if method == "HEAD" and exc.code in {403, 405, 501}:
                continue
            return False, exc.code, str(exc)
        except URLError as exc:
            return False, None, str(exc.reason)
    return False, None, "Không thể kiểm tra"


def main() -> int:
    static_base = clean_base(os.getenv("STATIC_ASSET_BASE_URL"))
    shop_base = clean_base(os.getenv("SHOP_ASSET_BASE_URL"))
    if not static_base:
        print("LỖI: STATIC_ASSET_BASE_URL đang trống. Website sẽ dùng /static thay vì Supabase.")
        return 2

    with MANIFEST.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    failed = []
    print(f"Kiểm tra {len(rows)} tài nguyên...")
    for row in rows:
        path = (row.get("duong_dan") or "").strip()
        if not path:
            continue
        url = build_url(path, static_base, shop_base)
        ok, status, detail = check_url(url)
        label = "OK" if ok else "LỖI"
        print(f"[{label}] {status or '-'} {path} -> {url}")
        if not ok:
            failed.append((path, url, status, detail))

    print(f"\nKết quả: {len(rows) - len(failed)}/{len(rows)} tài nguyên truy cập được.")
    if failed:
        print("Các tài nguyên lỗi:")
        for path, url, status, detail in failed:
            print(f"- {path}: HTTP {status or '-'} — {detail}\n  {url}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
