#!/usr/bin/env python3
"""Đóng gói ảnh Shop để upload lên Supabase Storage.

Không sửa ảnh nguồn. Tạo một thư mục versioned, file manifest CSV và ZIP upload.
Chạy từ thư mục gốc dự án:
    python tools/build_supabase_asset_bundle.py
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--version", default="v1.14.41")
    parser.add_argument("--output", default="build/supabase-assets")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    shop_source = root / "static" / "shop"
    if not shop_source.is_dir():
        raise SystemExit(f"Không tìm thấy thư mục: {shop_source}")

    output_root = (root / args.output / args.version).resolve()
    if output_root.exists():
        shutil.rmtree(output_root)
    target = output_root / "shop"
    shutil.copytree(shop_source, target)

    rows = []
    for path in sorted(target.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(output_root).as_posix()
        rows.append({
            "remote_path": f"{args.version}/{relative}",
            "shop_relative_path": path.relative_to(target).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        })

    manifest = output_root / "ASSET_MANIFEST.csv"
    with manifest.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=["remote_path", "shop_relative_path", "bytes", "sha256"])
        writer.writeheader()
        writer.writerows(rows)

    archive = shutil.make_archive(str(output_root), "zip", output_root.parent, output_root.name)
    total = sum(row["bytes"] for row in rows)
    print(f"Đã đóng gói {len(rows)} file, {total:,} bytes")
    print(f"Thư mục: {output_root}")
    print(f"ZIP: {archive}")
    print(f"SHOP_ASSET_BASE_URL phải kết thúc bằng: /{args.version}/shop")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
