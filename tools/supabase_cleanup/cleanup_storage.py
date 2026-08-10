#!/usr/bin/env python3
"""Xoa hang loat asset UI da migrate khoi Supabase Storage.

AN TOAN:
- Mac dinh chi DRY-RUN.
- Chi dung bucket pes-assets theo cleanup_plan.json.
- Chi xoa path nam trong SUPABASE_ASSET_MANIFEST.csv.
- TU CHOI execute neu con thieu bat ky file local nao.
- Execute can dong thoi: --execute + env SUPABASE_CLEANUP_ALLOW_EXECUTE=YES

Vi du:
  python tools/supabase_cleanup/cleanup_storage.py
  set SUPABASE_CLEANUP_ALLOW_EXECUTE=YES
  python tools/supabase_cleanup/cleanup_storage.py --execute
"""
from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PLAN = json.loads((HERE / "cleanup_plan.json").read_text(encoding="utf-8"))
MANIFEST = ROOT / "SUPABASE_ASSET_MANIFEST.csv"


def load_manifest() -> list[str]:
    with MANIFEST.open("r", encoding="utf-8-sig", newline="") as f:
        return [
            (r.get("duong_dan") or "").strip().lstrip("/")
            for r in csv.DictReader(f)
            if (r.get("duong_dan") or "").strip()
        ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true", help="XOA that. Mac dinh chi dry-run")
    parser.add_argument("--prefix", default=PLAN["storage"]["remote_prefix"], help="Prefix trong bucket, mac dinh v1.14.41")
    args = parser.parse_args()

    if not MANIFEST.is_file():
        raise SystemExit("Thieu SUPABASE_ASSET_MANIFEST.csv")
    relative_paths = load_manifest()
    missing = [p for p in relative_paths if not (ROOT / "static" / p).is_file()]
    if missing:
        print(f"TU CHOI: con thieu {len(missing)}/{len(relative_paths)} asset trong /static.")
        print("Hay chay tools/migrate_supabase_assets_to_vercel_static.py truoc.")
        return 3

    prefix = args.prefix.strip().strip("/")
    object_paths = [f"{prefix}/{p}" if prefix else p for p in relative_paths]
    print(f"Bucket: {PLAN['storage']['bucket']}")
    print(f"So object trong manifest: {len(object_paths)}")
    for path in object_paths:
        print(f"  {'DELETE' if args.execute else 'DRY-RUN'} {path}")

    if not args.execute:
        print("\nDRY-RUN: chua xoa gi. Muon xoa that can --execute va SUPABASE_CLEANUP_ALLOW_EXECUTE=YES")
        return 0

    if os.getenv("SUPABASE_CLEANUP_ALLOW_EXECUTE") != "YES":
        print("TU CHOI: chua dat SUPABASE_CLEANUP_ALLOW_EXECUTE=YES")
        return 4
    if (os.getenv("STATIC_ASSET_MODE") or "").strip().lower() != "local":
        print("TU CHOI: STATIC_ASSET_MODE phai la local de dam bao web khong con phu thuoc Storage UI.")
        return 5

    url = (os.getenv("SUPABASE_URL") or "").strip()
    key = (os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY") or "").strip()
    if not url or not key:
        print("TU CHOI: thieu SUPABASE_URL/SUPABASE_SERVICE_ROLE_KEY")
        return 6

    from supabase import create_client
    db = create_client(url, key)
    bucket = db.storage.from_(PLAN["storage"]["bucket"])
    batch_size = 100
    deleted = 0
    for start in range(0, len(object_paths), batch_size):
        batch = object_paths[start:start + batch_size]
        bucket.remove(batch)
        deleted += len(batch)
        print(f"Da gui xoa {deleted}/{len(object_paths)} object")
    print("HOAN TAT lenh xoa asset UI trong manifest. Bucket avatar/evidence khong bi dung vao.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
