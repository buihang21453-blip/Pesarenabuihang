"""Read-only Vercel Web Analytics helper for PES Arena Admin.

V1.6.101: scope-aware /friendly analytics reader.
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


def _error_result(code: str, message: str, http_status=None, detail="") -> dict:
    return {"ok": False, "visitors": None, "pageviews": None,
            "error_code": code, "error": message, "http_status": http_status,
            "detail": detail[:300] if detail else ""}


def _extract_error(body: str) -> str:
    try:
        payload = json.loads(body or "{}")
        err = payload.get("error") or {}
        if isinstance(err, dict):
            return str(err.get("message") or err.get("code") or "").strip()
        return str(err or "").strip()
    except Exception:
        return ""


def _friendly_http_error(status: int, body: str) -> dict:
    detail = _extract_error(body)
    if status == 401:
        msg, code = "Token Vercel không hợp lệ hoặc đã hết hạn (401).", "unauthorized"
    elif status == 403:
        msg, code = "Vercel từ chối scope của token/project/team (403).", "forbidden"
    elif status == 404:
        msg, code = "Không tìm thấy project hoặc Web Analytics API cho Project/Team đã cấu hình (404).", "not_found"
    elif status == 429:
        msg, code = "Vercel Analytics API đang giới hạn tần suất truy vấn (429).", "rate_limited"
    else:
        msg, code = f"Vercel Analytics API trả lỗi HTTP {status}.", "http_error"
    if detail:
        msg += f" {detail[:180]}"
    return _error_result(code, msg, status, detail)


def _scope_candidates(team_value: str, team_slug: str):
    """Try the configured ownership scope first, then safe alternatives.

    Vercel requires teamId/slug for team-owned projects and requires those to be
    omitted for personal projects. This also tolerates a slug pasted into
    VERCEL_TEAM_ID without hiding a real authorization error.
    """
    candidates = []
    if team_slug:
        candidates.append(("slug", {"slug": team_slug}))
    if team_value:
        if team_value.startswith("team_"):
            candidates.append(("teamId", {"teamId": team_value}))
        else:
            candidates.append(("slug", {"slug": team_value}))
    # Personal-account projects must omit teamId/slug.
    candidates.append(("personal", {}))
    out, seen = [], set()
    for label, scope in candidates:
        key = tuple(sorted(scope.items()))
        if key not in seen:
            seen.add(key)
            out.append((label, scope))
    return out


def _query(token: str, project_id: str, path: str, scope: dict):
    params = {"projectId": project_id, "filter": f"requestPath eq '{path}'", **scope}
    request = urllib.request.Request(
        _API_URL + "?" + urllib.parse.urlencode(params),
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json",
                 "User-Agent": "PES-Arena-Admin/1.6.101"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=6) as response:
            payload = json.loads(response.read().decode("utf-8"))
        data = payload.get("data")
        if not isinstance(data, dict):
            return None, _error_result("bad_response", "Vercel Analytics API trả dữ liệu không đúng định dạng.")
        return {"ok": True, "visitors": int(data.get("visitors") or 0),
                "pageviews": int(data.get("pageviews") or 0), "error_code": "",
                "error": "", "http_status": 200}, None
    except urllib.error.HTTPError as exc:
        try:
            body = exc.read().decode("utf-8", errors="replace")
        except Exception:
            body = ""
        return None, _friendly_http_error(int(exc.code), body)
    except urllib.error.URLError as exc:
        return None, _error_result("network", f"Không kết nối được Vercel Analytics API: {str(exc.reason)[:120]}")
    except json.JSONDecodeError:
        return None, _error_result("bad_json", "Vercel Analytics API trả response không phải JSON hợp lệ.")
    except Exception as exc:
        return None, _error_result("unexpected", f"Lỗi đọc Vercel Analytics: {type(exc).__name__}: {str(exc)[:120]}")


def get_friendly_analytics(path: str = "/friendly") -> dict:
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
        _cache.update(expires_at=now + 60, value=result); return dict(result)
    if not project_id:
        result = _error_result("missing_project", "Thiếu VERCEL_PROJECT_ID trên deployment Production.")
        _cache.update(expires_at=now + 60, value=result); return dict(result)

    attempts = []
    last_error = None
    for label, scope in _scope_candidates(team_value, team_slug):
        result, error = _query(token, project_id, path, scope)
        if result:
            result["scope_used"] = label
            _cache.update(expires_at=now + _CACHE_TTL_SECONDS, value=result)
            return dict(result)
        last_error = error
        attempts.append(f"{label}:{(error or {}).get('http_status') or (error or {}).get('error_code')}")
        # Only a 403 can plausibly be fixed by changing ownership scope.
        if not error or error.get("http_status") != 403:
            break

    result = dict(last_error or _error_result("unknown", "Không đọc được Vercel Web Analytics."))
    if result.get("http_status") == 403:
        result["error"] = (
            "Vercel trả 403 Not authorized sau khi đã thử scope Team ID/slug và personal. "
            "Hãy tạo Access Token với Scope đúng team đang sở hữu project pesonline."
        )
    result["scope_attempts"] = ", ".join(attempts)
    _cache.update(expires_at=now + 60, value=result)
    return dict(result)
