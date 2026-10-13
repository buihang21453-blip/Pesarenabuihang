import io
import json
import os
import urllib.error
from unittest import mock

import modules.vercel_analytics_service as svc


class Resp:
    def __init__(self, payload): self.payload = payload
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self): return json.dumps(self.payload).encode()


def reset_cache():
    svc._cache.update(expires_at=0.0, value=None)


def test_success_reads_both_metrics():
    reset_cache()
    env = {"VERCEL_ANALYTICS_TOKEN":"tok", "VERCEL_PROJECT_ID":"prj_123", "VERCEL_TEAM_ID":"team_123"}
    with mock.patch.dict(os.environ, env, clear=True), mock.patch.object(svc.urllib.request, "urlopen", return_value=Resp({"data":{"pageviews":6,"visitors":4}})):
        got = svc.get_friendly_analytics()
    assert got["ok"] and got["visitors"] == 4 and got["pageviews"] == 6


def test_team_slug_mistakenly_in_team_id_is_supported():
    reset_cache()
    env = {"VERCEL_ANALYTICS_TOKEN":"tok", "VERCEL_PROJECT_ID":"prj_123", "VERCEL_TEAM_ID":"pesarenabuihang"}
    captured = {}
    def fake(req, timeout=6):
        captured["url"] = req.full_url
        return Resp({"data":{"pageviews":6,"visitors":4}})
    with mock.patch.dict(os.environ, env, clear=True), mock.patch.object(svc.urllib.request, "urlopen", side_effect=fake):
        svc.get_friendly_analytics()
    assert "slug=pesarenabuihang" in captured["url"]
    assert "teamId=" not in captured["url"]


def test_403_is_specific_and_safe():
    reset_cache()
    env = {"VERCEL_ANALYTICS_TOKEN":"super-secret", "VERCEL_PROJECT_ID":"prj_123", "VERCEL_TEAM_ID":"team_123"}
    err = urllib.error.HTTPError("x", 403, "Forbidden", {}, io.BytesIO(b'{"error":{"message":"Forbidden"}}'))
    with mock.patch.dict(os.environ, env, clear=True), mock.patch.object(svc.urllib.request, "urlopen", side_effect=err):
        got = svc.get_friendly_analytics()
    assert not got["ok"] and got["http_status"] == 403 and got["error_code"] == "forbidden"
    assert "super-secret" not in got["error"]
