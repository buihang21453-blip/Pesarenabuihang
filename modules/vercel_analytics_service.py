"""Read-only Vercel Web Analytics helper for PES Arena Admin.

V1.6.100: robust /friendly analytics reader with safe diagnostics.
No Supabase table/write is used. Results are cached in-process for 5 min.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

_API_URL = "https://api.vercel.com/v1/query/web-analytics/visits/count"
_CACHE_TTL_SECONDS = 300
_cache = {"expires_at": 0.0, "value": None}


def _env(*names: str) -> str:
    for name in names:
        value = str(os.getenv(name) or "").strip()
        if value:
            return value
    return ""


def _error_result(code: str, message: str, http_status=None) -> dict:
    return {
        "ok": False,
        "visitors": None,
        "pageviews": None,
        "error_code": code,
        "error": message,
        "http_status": http_status,
    }


def _friendly_http_error(status: int, body: str) -> dict:
    detail = ""
    try:
        payload = json.loads(body or "{}")
        err = payload.get("error") or {}
        if isinstance(err, dict):
            detail = str(err.get("message") or err.get("code") or "").strip()
        elif err:
            detail = str(err).strip()
    except Exception:
        detail = ""

    if status == 401:
        msg = "Token Vercel không hợp lệ hoặc đã hết hạn (401)."
        code = "unauthorized"
    elif status == 403:
        msg = "Token chưa có quyền đọc Web Analytics của project/team (403)."
        code = "forbidden"
    elif status == 404:
        msg = "Không tìm thấy project hoặc Web Analytics API cho Project/Team ID đã cấu hình (404)."
        code = "not_found"
    elif status == 429:
        msg = "Vercel Analytics API đang giới hạn tần suất truy vấn (429)."
        code = "rate_limited"
    else:
        msg = f"Vercel Analytics API trả lỗi HTTP {status}."
        code = "http_error"
    if detail:
        msg += f" {detail[:140]}"
    return _error_result(code, msg, status)


def get_friendly_analytics(path: str = "/friendly") -> dict:
    """Return lifetime production visitors/pageviews for one requestPath.

    Required:
      VERCEL_ANALYTICS_TOKEN
      VERCEL_PROJECT_ID (normally starts with ``prj_``)

    Team-owned project: set either VERCEL_TEAM_ID (``team_...``) or
    VERCEL_TEAM_SLUG. For backwards compatibility, if VERCEL_TEAM_ID contains
    a slug instead of a ``team_`` id, it is automatically sent as ``slug``.
    """
    now = time.time()
    cached = _cache.get("value")
    if cached is not None and now < float(_cache.get("expires_at") or 0):
        return dict(cached)

    token = _env("VERCEL_ANALYTICS_TOKEN", "VERCEL_ACCESS_TOKEN")
    project_id = _env("VERCEL_PROJECT_ID", "VERCEL_ANALYTICS_PROJECT_ID")
    team_value = _env("VERCEL_TEAM_ID", "VERCEL_ANALYTICS_TEAM_ID")
    team_slug = _env("VERCEL_TEAM_SLUG", "VERCEL_ANALYTICS_TEAM_SLUG")

    if not token:
        result = _error_result("missing_token", "Thiếu VERCEL_ANALYTICS_TOKEN trên deployment Production.")
        _cache.update(expires_at=now + 60, value=result)
        return dict(result)
    if not project_id:
        result = _error_result("missing_project", "Thiếu VERCEL_PROJECT_ID trên deployment Production.")
        _cache.update(expires_at=now + 60, value=result)
        return dict(result)

    params = {
        "projectId": project_id,
        "filter": f"requestPath eq '{path}'",
    }
    if team_slug:
        params["slug"] = team_slug
    elif team_value:
        # A common setup mistake is pasting the team slug (e.g. pesarenabuihang)
        # into VERCEL_TEAM_ID. Accept both forms safely.
        if team_value.startswith("team_"):
            params["teamId"] = team_value
        else:
            params["slug"] = team_value

    request = urllib.request.Request(
        _API_URL + "?" + urllib.parse.urlencode(params),
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "User-Agent": "PES-Arena-Admin/1.6.100",
        },
        method="GET",
    )

    try:
        with urllib.request.urlopen(request, timeout=6) as response:
            payload = json.loads(response.read().decode("utf-8"))
        data = payload.get("data")
        if not isinstance(data, dict):
            result = _error_result("bad_response", "Vercel Analytics API trả dữ liệu không đúng định dạng.")
            _cache.update(expires_at=now + 60, value=result)
            return dict(result)
        result = {
            "ok": True,
            "visitors": int(data.get("visitors") or 0),
            "pageviews": int(data.get("pageviews") or 0),
            "error_code": "",
            "error": "",
            "http_status": 200,
        }
        _cache.update(expires_at=now + _CACHE_TTL_SECONDS, value=result)
        return dict(result)
    except urllib.error.HTTPError as exc:
        try:
            body = exc.read().decode("utf-8", errors="replace")
        except Exception:
            body = ""
        result = _friendly_http_error(int(exc.code), body)
    except urllib.error.URLError as exc:
        result = _error_result("network", f"Không kết nối được Vercel Analytics API: {str(exc.reason)[:120]}")
    except json.JSONDecodeError:
        result = _error_result("bad_json", "Vercel Analytics API trả response không phải JSON hợp lệ.")
    except Exception as exc:
        result = _error_result("unexpected", f"Lỗi đọc Vercel Analytics: {type(exc).__name__}: {str(exc)[:120]}")

    _cache.update(expires_at=now + 60, value=result)
    return dict(result)
