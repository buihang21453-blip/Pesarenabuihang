"""V1.2.23 - regression tests for Admin login/session on mobile/Vercel."""
import os
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("FLASK_SECRET_KEY", "v1223-test-secret-0123456789abcdef0123456789abcdef")

import app as app_module

ADMIN = {
    "id": "admin-1",
    "username": "admin",
    "display_name": "Admin",
    "password_hash": app_module.hash_password("secret123"),
    "role": "admin",
    "admin_level": "owner",
    "account_status": "approved",
    "zcoin_balance": 0,
}
MOBILE_UA = "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 Chrome/151 Mobile Safari/537.36"


def _client():
    app_module.app.config.update(TESTING=True)
    return app_module.app.test_client()


def test_admin_route_without_session_goes_to_admin_login():
    client = _client()
    response = client.get("/admin", headers={"User-Agent": MOBILE_UA}, follow_redirects=False)
    assert response.status_code in (301, 302, 303, 307, 308)
    assert response.headers["Location"].endswith("/admin-login")


def test_admin_required_keeps_signed_admin_session_when_db_temporarily_fails(monkeypatch):
    client = _client()
    monkeypatch.setattr(app_module, "get_user", lambda _uid: (_ for _ in ()).throw(RuntimeError("temporary network")))
    monkeypatch.setattr(app_module, "decorate_player_achievements", lambda user: user)
    with client.session_transaction() as sess:
        sess["user_id"] = ADMIN["id"]
        sess["username"] = ADMIN["username"]
        sess["display_name"] = ADMIN["display_name"]
        sess["role"] = "admin"
        sess["admin_level"] = "owner"
        sess["account_status"] = "approved"
        sess["zcoin_balance"] = 0
    # A lightweight protected endpoint whose body is irrelevant; auth must not bounce to login.
    response = client.get("/admin", headers={"User-Agent": MOBILE_UA}, follow_redirects=False)
    assert response.status_code != 302 or not response.headers.get("Location", "").endswith("/admin-login")


def test_admin_login_presence_failure_does_not_cancel_login(monkeypatch):
    client = _client()
    monkeypatch.setattr(app_module, "get_user_by_username", lambda username: dict(ADMIN) if username == "admin" else None)
    monkeypatch.setattr(app_module, "execute_query", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("presence update failed")))
    response = client.post(
        "/admin-login",
        data={"username": "admin", "password": "secret123"},
        headers={"User-Agent": MOBILE_UA},
        follow_redirects=False,
    )
    assert response.status_code in (301, 302, 303, 307, 308)
    assert response.headers["Location"].endswith("/admin")
    with client.session_transaction() as sess:
        assert sess.get("user_id") == ADMIN["id"]
        assert sess.get("admin_level") == "owner"


def test_admin_required_denies_real_non_admin(monkeypatch):
    client = _client()
    player = dict(ADMIN, role="player", admin_level="none")
    monkeypatch.setattr(app_module, "get_user", lambda _uid: player)
    monkeypatch.setattr(app_module, "decorate_player_achievements", lambda user: user)
    app_module.ttl_cache_delete(f"user:{ADMIN['id']}")
    with client.session_transaction() as sess:
        sess["user_id"] = ADMIN["id"]
        sess["username"] = ADMIN["username"]
        sess["display_name"] = ADMIN["display_name"]
        sess["role"] = "admin"
        sess["admin_level"] = "owner"
        sess["account_status"] = "approved"
    response = client.get("/admin", headers={"User-Agent": MOBILE_UA}, follow_redirects=False)
    assert response.status_code in (301, 302, 303, 307, 308)
    assert not response.headers["Location"].endswith("/admin-login")
