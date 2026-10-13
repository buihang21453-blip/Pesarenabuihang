"""PES Arena realtime signalling over Supabase Broadcast.

Security model: browsers receive only the publishable/anon key plus opaque HMAC
channel names. Business data is never broadcast. A realtime event only tells an
authorized page to refresh its existing Flask API. If Realtime is unavailable,
existing HTTP polling remains as a sparse fallback.
"""
import hashlib
import hmac
import json
import os
import urllib.request


def _public_key():
    return (os.getenv("SUPABASE_PUBLISHABLE_KEY") or os.getenv("SUPABASE_ANON_KEY") or "").strip()


def realtime_enabled():
    return bool((os.getenv("SUPABASE_URL") or "").strip() and _public_key())


def public_config():
    return {
        "enabled": realtime_enabled(),
        "url": (os.getenv("SUPABASE_URL") or "").strip().rstrip("/"),
        "key": _public_key(),
    }


def topic(secret, kind, identifier):
    raw = f"pes:{kind}:{identifier}".encode("utf-8")
    digest = hmac.new(str(secret).encode("utf-8"), raw, hashlib.sha256).hexdigest()[:40]
    return f"pes-{kind}-{digest}"


def publish(secret, kind, identifier, event, payload=None):
    """Best-effort signal. Never let Realtime failure break gameplay."""
    cfg = public_config()
    service_key = (os.getenv("SUPABASE_SECRET_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY") or "").strip()
    if not cfg["url"] or not service_key or not identifier:
        return False
    channel = topic(secret, kind, identifier)
    url = f'{cfg["url"]}/realtime/v1/api/broadcast/{channel}/events/{event}'
    body = json.dumps(payload or {"changed": True}, separators=(",", ":")).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST", headers={
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=1.25) as resp:
            return 200 <= int(resp.status) < 300
    except Exception as exc:
        print(f"realtime broadcast warning [{kind}/{event}]: {exc}")
        return False
