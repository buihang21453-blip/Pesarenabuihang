#!/usr/bin/env python3
"""Kiểm tra toàn bộ URL ảnh Shop trên Supabase trả HTTP thành công."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("base_url", help="URL kết thúc bằng /v1.14.41/shop")
    parser.add_argument("--manifest", default="build/supabase-assets/v1.14.41/ASSET_MANIFEST.csv")
    parser.add_argument("--project-root", default=str(Path(__file__).resolve().parents[1]))
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    manifest = root / args.manifest
    base = args.base_url.strip().rstrip("/")
    failures = []

    with manifest.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    for index, row in enumerate(rows, 1):
        relative = row["shop_relative_path"].lstrip("/")
        url = f"{base}/{quote(relative, safe='/')}"
        try:
            request = Request(url, method="GET", headers={"Range": "bytes=0-0", "User-Agent": "PES-Arena-Asset-Check/1.0"})
            with urlopen(request, timeout=15) as response:
                if response.status not in (200, 206):
                    raise RuntimeError(f"HTTP {response.status}")
            print(f"[{index}/{len(rows)}] OK {relative}")
        except Exception as exc:
            failures.append((relative, str(exc)))
            print(f"[{index}/{len(rows)}] FAIL {relative}: {exc}")

    if failures:
        print(f"\nCó {len(failures)} URL lỗi. Chưa cấu hình SHOP_ASSET_BASE_URL trên Production.")
        return 1
    print(f"\nPASS: {len(rows)} URL đều truy cập được.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
