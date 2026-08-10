#!/usr/bin/env python3
"""Audit an toan cho PES Arena/Supabase.

Mac dinh KHONG sua/xoa Supabase. Script:
- quet ten bang duoc Python runtime tham chieu;
- quet dependency SQL trong docs/;
- kiem tra asset manifest da co day du trong /static hay chua;
- tuy chon doc row-count cua cac bang da biet neu co SUPABASE_URL + SERVICE ROLE KEY.

Usage:
    python tools/supabase_cleanup/audit_supabase.py
    python tools/supabase_cleanup/audit_supabase.py --live
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
PLAN_PATH = Path(__file__).with_name("cleanup_plan.json")
MANIFEST = ROOT / "SUPABASE_ASSET_MANIFEST.csv"

TABLE_CALL = re.compile(r"\.table\(\s*['\"]([^'\"]+)['\"]\s*\)")
SQL_TABLE = re.compile(
    r"\b(?:from|join|update|into|delete\s+from|truncate\s+table)\s+(?:public\.)?([a-z_][a-z0-9_]*)",
    re.IGNORECASE,
)
SQL_IGNORE = {
    "cfg", "distinct_pairs", "generate_series", "if", "information_schema", "jsonb_each_text",
    "latest", "of", "old", "old_day", "or", "owner_counts", "pg_constraint", "public", "s",
    "sday", "selected_id",
}


def load_plan() -> dict:
    return json.loads(PLAN_PATH.read_text(encoding="utf-8"))


def source_files() -> Iterable[Path]:
    if (ROOT / "app.py").is_file():
        yield ROOT / "app.py"
    modules = ROOT / "modules"
    if modules.is_dir():
        yield from modules.rglob("*.py")


def scan_runtime_tables() -> dict[str, list[str]]:
    refs: dict[str, set[str]] = {}
    for path in source_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        for table in TABLE_CALL.findall(text):
            refs.setdefault(table, set()).add(path.relative_to(ROOT).as_posix())
    return {k: sorted(v) for k, v in sorted(refs.items())}


def scan_sql_tables() -> dict[str, list[str]]:
    refs: dict[str, set[str]] = {}
    for path in (ROOT / "docs").rglob("*.sql") if (ROOT / "docs").is_dir() else []:
        text = path.read_text(encoding="utf-8", errors="ignore")
        for table in SQL_TABLE.findall(text):
            name = table.lower()
            if name in SQL_IGNORE or name.startswith("v_"):
                continue
            refs.setdefault(name, set()).add(path.relative_to(ROOT).as_posix())
    return {k: sorted(v) for k, v in sorted(refs.items())}


def asset_status() -> tuple[int, int, list[str]]:
    if not MANIFEST.is_file():
        return 0, 0, ["SUPABASE_ASSET_MANIFEST.csv khong ton tai"]
    with MANIFEST.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    missing = []
    for row in rows:
        rel = (row.get("duong_dan") or "").strip().lstrip("/")
        if rel and not (ROOT / "static" / rel).is_file():
            missing.append(rel)
    return len(rows), len(rows) - len(missing), missing


def live_counts(tables: list[str]) -> dict[str, object]:
    try:
        from supabase import create_client
    except Exception as exc:  # pragma: no cover
        return {"_error": f"Khong import duoc supabase: {exc}"}
    url = (os.getenv("SUPABASE_URL") or "").strip()
    key = (os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY") or "").strip()
    if not url or not key:
        return {"_error": "Thieu SUPABASE_URL/SUPABASE_SERVICE_ROLE_KEY trong environment"}
    db = create_client(url, key)
    out: dict[str, object] = {}
    for table in tables:
        try:
            result = db.table(table).select("*", count="exact").limit(1).execute()
            out[table] = getattr(result, "count", None)
        except Exception as exc:
            out[table] = {"error": str(exc)}
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="Chi DOC row-count tu Supabase; khong xoa/sua")
    parser.add_argument("--json", dest="json_path", help="Ghi bao cao JSON ra file")
    args = parser.parse_args()

    plan = load_plan()
    runtime = scan_runtime_tables()
    sql_refs = scan_sql_tables()
    manifest_total, local_total, missing_assets = asset_status()

    known = sorted(set(runtime) | set(sql_refs))
    report = {
        "runtime_table_count": len(runtime),
        "runtime_tables": runtime,
        "sql_dependency_tables": sql_refs,
        "known_table_count": len(known),
        "cleanup_plan": plan,
        "assets": {
            "manifest_total": manifest_total,
            "local_total": local_total,
            "missing_total": len(missing_assets),
            "missing": missing_assets,
            "storage_delete_ready": bool(manifest_total and not missing_assets),
        },
    }
    if args.live:
        report["live_row_counts"] = live_counts(sorted(set(known) | set(plan["cache_tables_clear"]) | set(plan["log_retention"])))

    print("=== PES ARENA - SUPABASE AUDIT (READ ONLY) ===")
    print(f"Runtime tables: {len(runtime)}")
    print(f"SQL dependency refs: {len(sql_refs)}")
    print(f"Known tables total: {len(known)}")
    print(f"Asset local: {local_total}/{manifest_total}")
    if missing_assets:
        print(f"[KHOA XOA STORAGE] Con thieu {len(missing_assets)} asset local. KHONG duoc xoa pes-assets.")
        for item in missing_assets[:15]:
            print(f"  - {item}")
        if len(missing_assets) > 15:
            print(f"  ... va {len(missing_assets) - 15} file khac")
    else:
        print("[OK] Asset manifest da co day du trong /static. Co the chay preview Storage.")

    print("\nBang chi REVIEW, khong tu dong drop:")
    for name in plan["candidate_unused_tables_review_only"]:
        print(f"  - {name}")

    if args.json_path:
        target = Path(args.json_path)
        if not target.is_absolute():
            target = ROOT / target
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nDa ghi: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
