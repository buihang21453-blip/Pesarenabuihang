from pathlib import Path

ROOT = Path(__file__).parent
APP = (ROOT / "app.py").read_text(encoding="utf-8")
ADMIN_ROUTES = (ROOT / "modules/admin_system_routes.py").read_text(encoding="utf-8")
ROOM_ROUTES = (ROOT / "modules/room_access_routes.py").read_text(encoding="utf-8")
ADMIN = (ROOT / "templates/admin.html").read_text(encoding="utf-8")
ROOM = (ROOT / "templates/room_detail.html").read_text(encoding="utf-8")
PARTIAL = (ROOT / "templates/partials/room_dynamic_state.html").read_text(encoding="utf-8")
CSS = (ROOT / "static/css/rank_mode_toggle.css").read_text(encoding="utf-8")


def test_version_and_room_panel_config_exist():
    assert 'APP_VERSION = "V1.4.2"' in APP
    assert 'ROOM_PANEL_LAYOUT_SETTING_KEY = "room_panel_layout_config"' in APP
    assert '"center_bars_visible": True' in APP
    assert '"panel_height": 600' in APP
    assert 'admin_update_room_panel_layout_config' in ADMIN_ROUTES
    assert '"room_panel_layout_config": get_room_panel_layout_config()' in ROOM_ROUTES


def test_admin_has_one_toggle_for_both_bars_and_height_control():
    assert 'Hiện 2 thanh trang trí ở khung trung tâm' in ADMIN
    assert 'name="center_bars_visible"' in ADMIN
    assert 'name="panel_height"' in ADMIN
    assert 'Lưu bố cục phòng đấu' in ADMIN


def test_room_exposes_bar_state_and_equal_height_variable():
    for source in (ROOM, PARTIAL):
        assert 'data-center-bars=' in source
        assert '--room-panel-height:' in source
    assert '[data-center-bars="hidden"] .room-center-stage-plain::before' in CSS
    assert '[data-center-bars="hidden"] .room-center-stage-plain::after' in CSS
    assert 'min-height: var(--room-panel-height, 600px) !important' in CSS
    assert '.room-team-card.home' in CSS
    assert '.room-team-card.away' in CSS

if __name__ == "__main__":
    test_version_and_room_panel_config_exist()
    test_admin_has_one_toggle_for_both_bars_and_height_control()
    test_room_exposes_bar_state_and_equal_height_variable()
