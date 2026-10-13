"""Read-only Vercel Web Analytics helper for PES Arena Admin.

V1.6.99: fetch lifetime /friendly pageviews + visitors from the official
Web Analytics visits/count endpoint. Results are cached in-process for 5 min.
No Supabase table/write is used.
"""
from __future__ import annotations

import json
import os
import time
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


def get_friendly_analytics(path: str = "/friendly") -> dict:
    """Return {ok, visitors, pageviews, error} for one production path.

    Required Vercel environment variables:
      VERCEL_ANALYTICS_TOKEN  - Vercel access token (server-side only)
      VERCEL_PROJECT_ID       - project id (Vercel normally exposes this)
    Optional for team-owned projects:
      VERCEL_TEAM_ID          - team id
    """
    now = time.time()
    cached = _cache.get("value")
    if cached is not None and now < float(_cache.get("expires_at") or 0):
        return dict(cached)

    token = _env("VERCEL_ANALYTICS_TOKEN", "VERCEL_ACCESS_TOKEN")
    project_id = _env("VERCEL_PROJECT_ID", "VERCEL_ANALYTICS_PROJECT_ID")
    team_id = _env("VERCEL_TEAM_ID", "VERCEL_ANALYTICS_TEAM_ID")

    if not token or not project_id:
        result = {
            "ok": False,
            "visitors": None,
            "pageviews": None,
            "error": "Thiếu VERCEL_ANALYTICS_TOKEN hoặc VERCEL_PROJECT_ID",
        }
        _cache.update(expires_at=now + 60, value=result)
        return dict(result)

    params = {
        "projectId": project_id,
        "filter": f"requestPath eq '{path}'",
    }
    if team_id:
        params["teamId"] = team_id

    request = urllib.request.Request(
        _API_URL + "?" + urllib.parse.urlencode(params),
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "User-Agent": "PES-Arena-Admin/1.6.99",
        },
        method="GET",
    )

    try:
        with urllib.request.urlopen(request, timeout=6) as response:
            payload = json.loads(response.read().decode("utf-8"))
        data = payload.get("data") or {}
        result = {
            "ok": True,
            "visitors": int(data.get("visitors") or 0),
            "pageviews": int(data.get("pageviews") or 0),
            "error": "",
        }
        _cache.update(expires_at=now + _CACHE_TTL_SECONDS, value=result)
        return dict(result)
    except Exception as exc:
        # Do not break /admin if Vercel API/token is unavailable.
        result = {
            "ok": False,
            "visitors": None,
            "pageviews": None,
            "error": str(exc)[:180],
        }
        _cache.update(expires_at=now + 60, value=result)
        return dict(result)
