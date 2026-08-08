"""Automated Black Box safety checks.

These checks intentionally avoid mutating gameplay data. They verify source isolation,
fail-open behavior, configuration, and basic storage availability. Browser-only checks
live in static/js/blackbox_safety_lab.js.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASELINE_FILE = Path(__file__).with_name("baseline_v1369.json")

CRITICAL_PATHS = [
    "modules/rp_engine.py",
    "modules/rp_formula.py",
    "modules/match_result_service.py",
    "modules/room_result_routes.py",
    "modules/room_access_routes.py",
    "modules/room_rematch_routes.py",
    "modules/core/room_runtime.py",
    "modules/core/matchmaking_runtime.py",
    "modules/core/match_repository.py",
    "modules/quick_match/service.py",
    "modules/invites/service.py",
    "modules/presence/service.py",
    "modules/rank_modes/service.py",
    "modules/daily_rank_limit_service.py",
]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _result(name, status, detail, **extra):
    return {"name": name, "status": status, "detail": detail, **extra}


def source_isolation_audit():
    try:
        baseline = json.loads(BASELINE_FILE.read_text(encoding="utf-8"))
    except Exception as exc:
        return [_result("Black Box source baseline", "NOT_TESTED", f"Không đọc được baseline: {type(exc).__name__}")]

    baseline_version = str(baseline.get("baseline_version") or "unknown")
    out = []
    for rel in CRITICAL_PATHS:
        current = ROOT / rel
        expected = baseline.get("files", {}).get(rel)
        if not current.exists() or not expected:
            out.append(_result(rel, "NOT_TESTED", "Thiếu file hiện tại hoặc hash baseline."))
            continue
        actual = _sha256(current)
        if actual == expected:
            out.append(_result(rel, "PASS", f"Khớp baseline an toàn V{baseline_version}.", hash=actual[:12], baseline_version=baseline_version))
        else:
            out.append(_result(rel, "WARNING", f"Có thay đổi so với baseline an toàn V{baseline_version}; cần regression review.", baseline=expected[:12], current=actual[:12], baseline_version=baseline_version))
    return out


def config_audit(cfg):
    checks = []
    checks.append(_result(
        "Kill Switch server",
        "PASS" if isinstance(cfg.get("enabled"), bool) else "FAIL",
        f"BLACKBOX_ENABLED={cfg.get('enabled')}",
    ))
    checks.append(_result(
        "Kill Switch client",
        "PASS" if isinstance(cfg.get("client_enabled"), bool) else "FAIL",
        f"BLACKBOX_CLIENT_ENABLED={cfg.get('client_enabled')}",
    ))
    max_buffer = int(cfg.get("max_buffer") or 0)
    checks.append(_result(
        "Buffer bounded",
        "PASS" if 50 <= max_buffer <= 500 else "WARNING",
        f"max_buffer={max_buffer}",
    ))
    flush_ms = int(cfg.get("flush_ms") or 0)
    checks.append(_result(
        "Batch flush cadence",
        "PASS" if flush_ms >= 3000 else "WARNING",
        f"flush_ms={flush_ms}",
    ))
    return checks


def storage_probe(context):
    """Read-only storage probe; never writes gameplay or Black Box rows."""
    db = context.get("db")
    execute_query = context.get("execute_query")
    if db is None:
        return _result("Black Box storage", "WARNING", "Database context unavailable.")
    try:
        query = db.table("blackbox_incidents").select("id").limit(1)
        res = execute_query(query, "blackbox_safety_storage_probe", attempts=1) if callable(execute_query) else query.execute()
        _ = getattr(res, "data", None)
        return _result("Black Box storage", "PASS", "Bảng blackbox_incidents truy cập được (read-only).")
    except Exception as exc:
        message = str(exc or "")
        lowered = message.lower()
        if "blackbox_incidents" in lowered and ("does not exist" in lowered or "schema cache" in lowered or "pgrst205" in lowered):
            detail = "Thiếu bảng blackbox_incidents; hãy chạy project_docs/sql/20260808_blackbox.sql trên Supabase."
        else:
            detail = f"Không truy cập được bảng Black Box: {type(exc).__name__}"
        return _result("Black Box storage", "WARNING", detail)


def fail_open_probe(store_batch):
    """Force the isolated Black Box storage layer to fail; no database write occurs."""
    def explode(_rows, _incidents):
        raise RuntimeError("intentional_blackbox_safety_failure")

    try:
        res = store_batch(
            user_id=None,
            session_id="safety-crash-probe",
            page="/admin",
            events=[{"type": "safety_probe", "message": "synthetic in-memory crash"}],
            client={"safety": True},
            _storage_override=explode,
        )
        ok = isinstance(res, dict) and res.get("ok") is False and res.get("reason") == "storage_failed"
        return _result(
            "Crash test: storage exception",
            "PASS" if ok else "FAIL",
            "Exception lưu Black Box đã được cô lập, không bubble ra gameplay." if ok else f"Kết quả bất thường: {res}",
        )
    except Exception as exc:
        return _result("Crash test: storage exception", "FAIL", f"Exception bị bubble: {type(exc).__name__}: {exc}")


def run_server_safety_audit(context, cfg, store_batch):
    checks = []
    checks.extend(config_audit(cfg))
    checks.extend(source_isolation_audit())
    checks.append(storage_probe(context))
    checks.append(fail_open_probe(store_batch))
    counts = {k: sum(1 for x in checks if x["status"] == k) for k in ("PASS", "WARNING", "FAIL", "NOT_TESTED")}
    overall = "FAIL" if counts["FAIL"] else ("WARNING" if counts["WARNING"] or counts["NOT_TESTED"] else "PASS")
    return {"overall": overall, "counts": counts, "checks": checks}
