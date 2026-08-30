from pathlib import Path

APP = Path("app.py").read_text(encoding="utf-8")
BASE = Path("templates/base.html").read_text(encoding="utf-8")
LOGIN = Path("templates/login.html").read_text(encoding="utf-8")


def test_release_version_and_short_public_ranking_notice():
    assert 'APP_VERSION = "V1.4.24"' in APP
    assert 'flash("Đăng ký để tham gia Championship Ranking", "warning")' in APP
    assert 'Bảng xếp hạng công khai đang được Admin tạm khóa' not in APP


def test_remember_session_uses_30_day_permanent_cookie_without_idle_logout():
    assert 'app.permanent_session_lifetime = timedelta(days=30)' in APP
    assert 'remembered_login = bool(session.get("remember_account"))' in APP
    assert 'if remembered_login:' in APP
    assert 'session.permanent = True' in APP
    assert 'else:\n                last_real = int(session.get("last_real_activity", 0) or 0)' in APP
    assert "and not session.get('remember_account')" in BASE
    assert 'if session.get("remember_account"):' in APP
    assert '"remembered": True' in APP


def test_normal_session_keeps_idle_timeout_and_password_is_not_stored():
    assert 'IDLE_TIMEOUT_SECONDS' in APP
    assert 'Bạn đã được đăng xuất do không hoạt động trong 60 phút.' in APP
    assert 'name="remember_account"' in LOGIN
    assert 'localStorage.setItem(storageKey, usernameInput.value.trim())' in LOGIN
    assert 'localStorage.setItem(storageKey, passwordInput.value' not in LOGIN
