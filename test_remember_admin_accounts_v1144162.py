from pathlib import Path

APP = Path("app.py").read_text(encoding="utf-8")
LOGIN = Path("templates/login.html").read_text(encoding="utf-8")
ADMIN = Path("templates/admin.html").read_text(encoding="utf-8")
ACCOUNTS = Path("modules/admin_account_routes.py").read_text(encoding="utf-8")


def test_version_and_remember_session():
    assert 'APP_VERSION = "V1.3.13"' in APP
    assert 'app.permanent_session_lifetime = timedelta(days=30)' in APP
    assert 'request.form.get("remember_account") == "1"' in APP
    assert 'session.permanent = remember_account' in APP


def test_browser_password_manager_not_plaintext_storage():
    assert 'name="remember_account"' in LOGIN
    assert 'autocomplete="username"' in LOGIN
    assert 'autocomplete="current-password"' in LOGIN
    assert 'new PasswordCredential(form)' not in LOGIN
    assert 'navigator.credentials.store(credential)' not in LOGIN
    assert "localStorage.setItem(storageKey, usernameInput.value.trim())" in LOGIN
    assert "localStorage.setItem(storageKey, passwordInput.value" not in LOGIN


def test_admin_accounts_simple_password_and_ip_bypass():
    assert 'def is_admin_managed_test_account(user):' in APP
    assert 'is_admin_managed_test_account(user)' in APP
    assert 'minlength="1" value="1"' in ADMIN
    assert 'default_password="1"' in ACCOUNTS
    assert '"register_ip": "ADMIN_TEST_IMPORT"' in ACCOUNTS
