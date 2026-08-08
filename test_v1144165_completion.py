from pathlib import Path

APP = Path("app.py").read_text(encoding="utf-8")
SESSION = Path("modules/session_runtime_service.py").read_text(encoding="utf-8")
ADMIN = Path("templates/admin.html").read_text(encoding="utf-8")
LOGIN = Path("templates/login.html").read_text(encoding="utf-8")

def test_direct_room_session_protection():
    assert 'active_room_for_user_direct' in APP
    assert 'PROTECTED_ROOM_STATUSES' in APP
    assert '.or_(f"host_user_id.eq.{user_id},guest_user_id.eq.{user_id}")' in APP
    assert 'has_participant' in SESSION

def test_ip_loading_diagnostics_visible():
    assert 'list_user_devices.last_status' in APP
    assert 'Không tải được lịch sử IP thiết bị' in ADMIN
    assert 'Tải lại IP' in ADMIN

def test_remember_wording_is_accurate():
    assert 'Ghi nhớ đăng nhập trên thiết bị này' in LOGIN
    assert 'Mật khẩu do trình quản lý mật khẩu của trình duyệt lưu' in LOGIN
    assert 'passwordInput.value' not in LOGIN.split('localStorage.setItem')[-1]
