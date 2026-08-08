"""PES Arena Black Box: fail-open incident/event storage and admin read helpers."""
from __future__ import annotations

import hashlib
import json
import os
import re
import uuid
from datetime import datetime, timezone

_CONTEXT = {}

EXPORTED_NAMES = (
    "blackbox_config",
    "blackbox_store_batch",
    "blackbox_list_incidents",
    "blackbox_get_incident",
    "blackbox_summary",
)

_SENSITIVE_KEY = re.compile(r"password|passwd|secret|token|authorization|cookie|session|service.?key|apikey|api_key|parsec", re.I)
_MAX_TEXT = 1200
_MAX_EVENTS_PER_BATCH = 80


def configure(context):
    global _CONTEXT
    _CONTEXT = context or {}


def _db():
    return _CONTEXT.get("db")


def _execute(query, label):
    fn = _CONTEXT.get("execute_query")
    return fn(query, label, attempts=1) if callable(fn) else query.execute()


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _bool_env(name, default):
    raw = os.getenv(name)
    if raw is None:
        return bool(default)
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _int_env(name, default, minimum=None, maximum=None):
    """Parse optional numeric env safely; malformed values must never crash Flask."""
    try:
        value = int(str(os.getenv(name, default)).strip())
    except (TypeError, ValueError):
        value = int(default)
    if minimum is not None:
        value = max(int(minimum), value)
    if maximum is not None:
        value = min(int(maximum), value)
    return value


def blackbox_config():
    # This function is called from page-render context. It must be exception-free.
    return {
        "enabled": _bool_env("BLACKBOX_ENABLED", True),
        "client_enabled": _bool_env("BLACKBOX_CLIENT_ENABLED", True),
        "capture_clicks": _bool_env("BLACKBOX_CAPTURE_CLICKS", True),
        "capture_network": _bool_env("BLACKBOX_CAPTURE_NETWORK", True),
        "capture_console": _bool_env("BLACKBOX_CAPTURE_CONSOLE", True),
        "batch_size": _int_env("BLACKBOX_BATCH_SIZE", 20, 5, 50),
        "flush_ms": _int_env("BLACKBOX_FLUSH_MS", 10000, 3000, 60000),
        "slow_api_ms": _int_env("BLACKBOX_SLOW_API_MS", 2500, 500, None),
        "max_buffer": _int_env("BLACKBOX_MAX_BUFFER", 200, 50, 500),
        "app_version": str(_CONTEXT.get("APP_VERSION") or "unknown"),
    }


def _sanitize(value, depth=0):
    if depth > 5:
        return "[max-depth]"
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        text = value.replace("\x00", "")
        return text[:_MAX_TEXT] + ("…" if len(text) > _MAX_TEXT else "")
    if isinstance(value, (list, tuple)):
        return [_sanitize(v, depth + 1) for v in list(value)[:50]]
    if isinstance(value, dict):
        out = {}
        for k, v in list(value.items())[:80]:
            key = str(k)[:100]
            out[key] = "[redacted]" if _SENSITIVE_KEY.search(key) else _sanitize(v, depth + 1)
        return out
    return _sanitize(str(value), depth + 1)


def _severity(event):
    explicit = str(event.get("level") or "").upper()
    if explicit in {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"}:
        return explicit
    kind = str(event.get("type") or event.get("event") or "").lower()
    if "error" in kind or "exception" in kind or "unhandled" in kind:
        return "ERROR"
    if "timeout" in kind or "slow" in kind or "warning" in kind:
        return "WARNING"
    return "INFO"


def _fingerprint(event):
    basis = "|".join([
        str(event.get("type") or event.get("event") or "event"),
        str(event.get("message") or "")[:300],
        str(event.get("source") or "")[:200],
        str(event.get("status") or ""),
    ])
    return hashlib.sha256(basis.encode("utf-8", "ignore")).hexdigest()[:20]


def blackbox_store_batch(*, user_id, session_id, page, events, client=None, request_id=None, _storage_override=None):
    """Persist a small client batch. Fail-open: returns ok=False instead of raising."""
    cfg = blackbox_config()
    if not cfg["enabled"]:
        return {"ok": True, "disabled": True, "stored": 0}
    db = _db()
    safe_events = [_sanitize(e) for e in list(events or [])[:_MAX_EVENTS_PER_BATCH] if isinstance(e, dict)]
    if not safe_events:
        return {"ok": True, "stored": 0}

    session_id = str(session_id or uuid.uuid4().hex)[:80]
    page = str(page or "")[:300]
    client = _sanitize(client or {})
    rows = []
    incident_rows = []
    created = _now_iso()
    for event in safe_events:
        level = _severity(event)
        row_id = str(uuid.uuid4())
        row = {
            "id": row_id,
            "session_id": session_id,
            "user_id": str(user_id) if user_id else None,
            "request_id": str(request_id or "")[:80] or None,
            "page": page,
            "event_type": str(event.get("type") or event.get("event") or "client_event")[:100],
            "level": level,
            "message": str(event.get("message") or "")[:800] or None,
            "payload": event,
            "client": client,
            "created_at": str(event.get("ts") or created)[:80],
        }
        rows.append(row)
        if level in {"ERROR", "CRITICAL"} or str(event.get("type") or "").lower() in {"api_slow", "api_timeout"}:
            incident_rows.append({
                "id": str(uuid.uuid4()),
                "incident_code": "BB-" + datetime.now().strftime("%Y%m%d") + "-" + uuid.uuid4().hex[:6].upper(),
                "fingerprint": _fingerprint(event),
                "session_id": session_id,
                "user_id": str(user_id) if user_id else None,
                "page": page,
                "severity": level if level != "INFO" else "WARNING",
                "status": "open",
                "title": str(event.get("message") or event.get("type") or "Black Box incident")[:240],
                "event_id": row_id,
                "app_version": cfg["app_version"],
                "created_at": created,
            })
    try:
        if callable(_storage_override):
            _storage_override(rows, incident_rows)
        else:
            if db is None:
                logger = _CONTEXT.get("log_system_event")
                if callable(logger):
                    logger("blackbox_batch_no_db", level=30, session_id=session_id, count=len(rows))
                return {"ok": False, "stored": 0, "reason": "database_unavailable"}
            _execute(db.table("blackbox_events").insert(rows), "blackbox_insert_events")
            if incident_rows:
                _execute(db.table("blackbox_incidents").insert(incident_rows), "blackbox_insert_incidents")
        return {"ok": True, "stored": len(rows), "incidents": len(incident_rows)}
    except Exception as exc:
        logger = _CONTEXT.get("log_system_event")
        if callable(logger):
            logger("blackbox_storage_failed", level=30, error_type=type(exc).__name__, error=str(exc)[:500], count=len(rows))
        return {"ok": False, "stored": 0, "reason": "storage_failed"}


def blackbox_list_incidents(limit=100):
    db = _db()
    if db is None:
        return []
    try:
        res = _execute(
            db.table("blackbox_incidents")
              .select("id,incident_code,fingerprint,session_id,user_id,page,severity,status,title,event_id,app_version,created_at")
              .order("created_at", desc=True).limit(max(1, min(int(limit), 300))),
            "blackbox_list_incidents",
        )
        return res.data or []
    except Exception:
        return []


def blackbox_get_incident(incident_id):
    db = _db()
    if db is None:
        return None
    try:
        inc_res = _execute(db.table("blackbox_incidents").select("*").eq("id", incident_id).limit(1), "blackbox_get_incident")
        incident = (inc_res.data or [None])[0]
        if not incident:
            return None
        sid = incident.get("session_id")
        ev_res = _execute(
            db.table("blackbox_events").select("*").eq("session_id", sid).order("created_at", desc=False).limit(250),
            "blackbox_get_incident_events",
        )
        incident["events"] = ev_res.data or []
        return incident
    except Exception:
        return None


def blackbox_summary(incidents=None):
    incidents = incidents if incidents is not None else blackbox_list_incidents(200)
    return {
        "total": len(incidents),
        "open": sum(1 for i in incidents if i.get("status") == "open"),
        "critical": sum(1 for i in incidents if i.get("severity") == "CRITICAL"),
        "error": sum(1 for i in incidents if i.get("severity") == "ERROR"),
        "warning": sum(1 for i in incidents if i.get("severity") == "WARNING"),
    }
