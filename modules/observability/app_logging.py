"""Structured request/error logging for PES Arena.

Production/serverless: logs to stdout so Vercel captures them.
Local/dev: optionally also rotates a local log file (PES_LOG_FILE or logs/pes_arena.log).
"""
from __future__ import annotations

import json
import logging
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from flask import g, has_request_context, request
from flask.signals import got_request_exception

LOGGER_NAME = "pes_arena"
_DEFAULT_LOCAL_LOG = "logs/pes_arena.log"


def _json_line(level: str, event: str, **fields: Any) -> str:
    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "event": event,
        **{k: v for k, v in fields.items() if v is not None},
    }
    return json.dumps(payload, ensure_ascii=False, default=str, separators=(",", ":"))


def _request_fields() -> dict[str, Any]:
    if not has_request_context():
        return {}
    return {
        "request_id": getattr(g, "request_id", None),
        "method": request.method,
        "path": request.path,
        "endpoint": request.endpoint,
        "user_id": (getattr(g, "current_user", None) or {}).get("id") if isinstance(getattr(g, "current_user", None), dict) else None,
    }


def log_system_event(event: str, level: int = logging.INFO, **fields: Any) -> None:
    logger = logging.getLogger(LOGGER_NAME)
    level_name = logging.getLevelName(level) if isinstance(level, int) else str(level)
    logger.log(level, _json_line(str(level_name), event, **_request_fields(), **fields))


def configure_app_logging(app, app_version: str, slow_request_ms: int | None = None):
    """Attach request timing + uncaught exception logging exactly once."""
    if app.extensions.get("pes_arena_logging"):
        return logging.getLogger(LOGGER_NAME)

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(getattr(logging, (os.getenv("PES_LOG_LEVEL") or "INFO").upper(), logging.INFO))
    logger.propagate = False

    if not logger.handlers:
        stream = logging.StreamHandler(sys.stdout)
        stream.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(stream)

        app_env = (os.getenv("APP_ENV") or os.getenv("VERCEL_ENV") or "production").lower()
        file_logging = (os.getenv("PES_LOG_TO_FILE") or ("1" if app_env in {"development", "test", "testing"} else "0")).lower() in {"1", "true", "yes", "on"}
        if file_logging:
            log_path = Path(os.getenv("PES_LOG_FILE") or _DEFAULT_LOCAL_LOG)
            try:
                log_path.parent.mkdir(parents=True, exist_ok=True)
                file_handler = RotatingFileHandler(log_path, maxBytes=2 * 1024 * 1024, backupCount=5, encoding="utf-8")
                file_handler.setFormatter(logging.Formatter("%(message)s"))
                logger.addHandler(file_handler)
            except OSError:
                logger.warning(_json_line("WARNING", "log_file_unavailable", path=str(log_path)))

    slow_ms = int(slow_request_ms or os.getenv("PES_SLOW_REQUEST_MS") or 1500)

    @app.before_request
    def _pes_log_request_start():
        g.request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:16]
        g.request_started_perf = time.perf_counter()

    @app.after_request
    def _pes_log_request_end(response):
        started = getattr(g, "request_started_perf", None)
        duration_ms = round((time.perf_counter() - started) * 1000, 2) if started else None
        response.headers.setdefault("X-Request-ID", getattr(g, "request_id", ""))
        event = "slow_request" if duration_ms is not None and duration_ms >= slow_ms else "request_complete"
        level = logging.WARNING if event == "slow_request" or response.status_code >= 500 else logging.INFO
        log_system_event(event, level=level, status=response.status_code, duration_ms=duration_ms)
        return response

    def _on_exception(sender, exception, **extra):
        logger.exception(_json_line("ERROR", "uncaught_exception", **_request_fields(), error_type=type(exception).__name__, error=str(exception)))

    got_request_exception.connect(_on_exception, app, weak=False)
    app.extensions["pes_arena_logging"] = {"version": app_version, "slow_request_ms": slow_ms}
    logger.info(_json_line("INFO", "application_logging_ready", app_version=app_version, slow_request_ms=slow_ms))
    return logger
