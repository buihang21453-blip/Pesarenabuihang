from pathlib import Path

ROOT = Path(__file__).resolve().parent

def test_admin_receives_recent_closed_host_offline_rooms():
    source = (ROOT / "modules" / "admin_dashboard_routes.py").read_text(encoding="utf-8")
    assert "recent_closed_rooms=" in source
    assert 'r.get("status") == "cancelled"' in source
    assert "đóng trình duyệt" in source

def test_admin_template_displays_closed_rooms_panel():
    template = (ROOT / "templates" / "admin.html").read_text(encoding="utf-8")
    assert "Phòng đã đóng do chủ Offline" in template
    assert "recent_closed_rooms" in template
    assert "Xem phòng" in template
