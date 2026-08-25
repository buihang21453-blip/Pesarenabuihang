from pathlib import Path

ROOT = Path(__file__).parent
APP = (ROOT / "app.py").read_text(encoding="utf-8")
ADMIN_ROUTES = (ROOT / "modules/admin_system_routes.py").read_text(encoding="utf-8")
ROOM_ROUTES = (ROOT / "modules/room_access_routes.py").read_text(encoding="utf-8")
ADMIN = (ROOT / "templates/admin.html").read_text(encoding="utf-8")
ROOM = (ROOT / "templates/room_detail.html").read_text(encoding="utf-8")
ROOM_PARTIAL = (ROOT / "templates/partials/room_dynamic_state.html").read_text(encoding="utf-8")
CSS = (ROOT / "static/css/rank_mode_toggle.css").read_text(encoding="utf-8")


def test_room_mode_logo_config_is_defined_and_routed():
    assert "ROOM_MODE_LOGO_SETTING_KEY" in APP
    assert "ROOM_MODE_LOGO_DEFAULTS" in APP
    assert "ROOM_MODE_LOGO_LIMITS" in APP
    assert "normalize_room_mode_logo_config" in APP
    assert "get_room_mode_logo_config" in APP
    assert "admin_update_room_mode_logo_config" in ADMIN_ROUTES
    assert 'room_mode_logo_config' in ROOM_ROUTES


def test_admin_has_controls_for_logo_opacity_and_scale():
    assert "Tuỳ chỉnh logo chế độ thi đấu" in ADMIN
    assert "room_mode_logo_opacity" in ADMIN
    assert "room_mode_logo_scale" in ADMIN
    assert "Độ trong suốt logo (%)" in ADMIN
    assert "Kích thước logo (%)" in ADMIN


def test_room_views_receive_css_variables_and_transparent_mode_blocks():
    assert "--room-mode-logo-opacity" in ROOM
    assert "--room-mode-logo-scale" in ROOM
    assert "--room-mode-logo-opacity" in ROOM_PARTIAL
    assert "background: transparent !important;" in CSS
    assert "grid-template-columns: repeat(3, minmax(0, 1fr))" in CSS

if __name__ == "__main__":
    test_room_mode_logo_config_is_defined_and_routed()
    test_admin_has_controls_for_logo_opacity_and_scale()
    test_room_views_receive_css_variables_and_transparent_mode_blocks()
