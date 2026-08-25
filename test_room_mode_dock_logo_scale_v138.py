from pathlib import Path

ROOT = Path(__file__).parent
APP = (ROOT / "app.py").read_text(encoding="utf-8")
ADMIN = (ROOT / "templates/admin.html").read_text(encoding="utf-8")
ROUTES = (ROOT / "modules/admin_system_routes.py").read_text(encoding="utf-8")
ROOM = (ROOT / "templates/room_detail.html").read_text(encoding="utf-8")
CSS = (ROOT / "static/css/rank_mode_toggle.css").read_text(encoding="utf-8")

def test_v138_dock_logo_has_independent_admin_scale():
    assert 'APP_VERSION = "V1.4"' in APP
    assert '"dock_scale": 135' in APP
    assert '"dock_scale": (70, 220)' in APP
    assert 'room_mode_dock_logo_scale' in ADMIN
    assert 'Kích thước logo CÁC CHẾ ĐỘ THI ĐẤU (%)' in ADMIN
    assert 'room_mode_dock_logo_scale' in ROUTES
    assert '--room-mode-dock-logo-scale' in ROOM
    assert 'scale(var(--room-mode-dock-logo-scale, 1.35))' in CSS
    assert 'min-height: 122px' in CSS
