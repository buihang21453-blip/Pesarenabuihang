#!/usr/bin/env python3
"""Tải asset public từ Supabase Storage về ``static/`` để Vercel CDN phục vụ.

Ví dụ Windows PowerShell:
  python tools/migrate_supabase_assets_to_vercel_static.py ^
    --static-base "https://PROJECT.supabase.co/storage/v1/object/public/pes-assets/v1.14.41" ^
    --shop-base "https://PROJECT.supabase.co/storage/v1/object/public/pes-assets/v1.14.41/shop" ^
    --luckybox-base "https://PROJECT.supabase.co/storage/v1/object/public/pes-assets/v1.14.41/luckybox"

Script không cần service_role key vì chỉ tải từ public bucket. Nó không xóa dữ
liệu trên Supabase. Sau khi kiểm tra đủ file, deploy project lên Vercel và đặt
STATIC_ASSET_MODE=auto hoặc local.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "static"
MANIFEST = ROOT / "SUPABASE_ASSET_MANIFEST.csv"
LUCKYBOX_MAPPING = ROOT / "docs" / "LUCKYBOX_ASSET_MAPPING_V1.14.41.42.csv"


def clean_base(value: str | None) -> str:
    return (value or "").strip().rstrip("/")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_assets() -> list[dict]:
    assets: dict[str, dict] = {}
    with MANIFEST.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            path = (row.get("duong_dan") or "").strip().lstrip("/")
            if path:
                assets[path] = {
                    "path": path,
                    "bytes": int(row.get("dung_luong_bytes") or 0),
                    "sha256": "",
                }

    if LUCKYBOX_MAPPING.exists():
        with LUCKYBOX_MAPPING.open("r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                path = (row.get("asset_path") or row.get("remote_path") or row.get("path") or "").strip().lstrip("/")
                if not path:
                    values = list(row.values())
                    path = str(values[0] if values else "").strip().lstrip("/")
                if path:
                    expected_bytes = int(str(row.get("bytes") or "0").strip() or 0)
                    expected_sha = str(row.get("sha256") or "").strip().lower()
                    assets[path] = {
                        "path": path,
                        "bytes": expected_bytes,
                        "sha256": expected_sha,
                    }
    return list(assets.values())


def build_url(path: str, static_base: str, shop_base: str, luckybox_base: str) -> str:
    if path.startswith("luckybox/") and luckybox_base:
        return f"{luckybox_base}/{quote(path[9:], safe='/')}"
    if path.startswith("shop/") and shop_base:
        return f"{shop_base}/{quote(path[5:], safe='/')}"
    if not static_base:
        raise ValueError(f"Thiếu --static-base để tải {path}")
    return f"{static_base}/{quote(path, safe='/')}"


def download(url: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".part")
    req = Request(url, headers={"User-Agent": "PES-Arena-Asset-Migrator/1.2.20"})
    with urlopen(req, timeout=60) as response, tmp.open("wb") as out:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)
    tmp.replace(target)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--static-base", required=True)
    parser.add_argument("--shop-base", default="")
    parser.add_argument("--luckybox-base", default="")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    static_base = clean_base(args.static_base)
    shop_base = clean_base(args.shop_base)
    luckybox_base = clean_base(args.luckybox_base)
    assets = load_assets()
    ok = 0
    failed = []

    print(f"Chuẩn bị tải {len(assets)} asset về {STATIC}")
    for item in assets:
        path = item["path"]
        target = STATIC / path
        try:
            if target.exists() and not args.overwrite:
                valid_size = not item["bytes"] or target.stat().st_size == item["bytes"]
                valid_hash = not item["sha256"] or sha256(target) == item["sha256"]
                if valid_size and valid_hash:
                    print(f"[SKIP] {path}")
                    ok += 1
                    continue
            url = build_url(path, static_base, shop_base, luckybox_base)
            download(url, target)
            if item["bytes"] and target.stat().st_size != item["bytes"]:
                raise ValueError(f"sai dung lượng: {target.stat().st_size} != {item['bytes']}")
            if item["sha256"] and sha256(target) != item["sha256"]:
                raise ValueError("SHA256 không khớp")
            print(f"[OK] {path}")
            ok += 1
        except (HTTPError, URLError, OSError, ValueError) as exc:
            print(f"[LỖI] {path}: {exc}")
            failed.append((path, str(exc)))

    print(f"\nKết quả: {ok}/{len(assets)} asset hợp lệ.")
    if failed:
        print("Không xóa Supabase Storage. Khắc phục các file lỗi rồi chạy lại script.")
        return 1
    print("Hoàn tất. Deploy lên Vercel và đặt STATIC_ASSET_MODE=auto (hoặc local).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
