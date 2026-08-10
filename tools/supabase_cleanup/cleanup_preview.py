#!/usr/bin/env python3
"""Preview ke hoach don Supabase. KHONG co lenh delete/drop."""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PLAN = json.loads((HERE / "cleanup_plan.json").read_text(encoding="utf-8"))
MANIFEST = ROOT / "SUPABASE_ASSET_MANIFEST.csv"


def main() -> int:
    print("=== PREVIEW DON SUPABASE - KHONG XOA DU LIEU ===\n")
    print("1) CACHE/THONG KE: se clear DU LIEU, GIU NGUYEN BANG")
    for table in PLAN["cache_tables_clear"]:
        print(f"   TRUNCATE (neu bang ton tai): {table}")

    print("\n2) LOG: chi xoa ban ghi cu hon moc giu lai")
    for table, days in PLAN["log_retention"].items():
        print(f"   {table}: giu {days} ngay gan nhat")

    print("\n3) BANG NGHI THUA: CHI BAO CAO, KHONG DROP TU DONG")
    for table in PLAN["candidate_unused_tables_review_only"]:
        print(f"   REVIEW ONLY: {table}")

    print("\n4) STORAGE pes-assets")
    rows = []
    if MANIFEST.is_file():
        with MANIFEST.open("r", encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
    missing = []
    for row in rows:
        rel = (row.get("duong_dan") or "").strip().lstrip("/")
        if rel and not (ROOT / "static" / rel).is_file():
            missing.append(rel)
    print(f"   Manifest: {len(rows)} file; local: {len(rows)-len(missing)}; missing: {len(missing)}")
    if missing:
        print("   => KHOA XOA STORAGE dang BAT. Phai migrate asset ve /static truoc.")
    else:
        print("   => Co the chay cleanup_storage.py o che do dry-run.")

    print("\n5) BUCKET KHONG BAO GIO TU DONG DUNG VAO")
    for bucket in PLAN["storage"]["never_touch_buckets"]:
        print(f"   - {bucket}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
