from pathlib import Path

ROOT = Path(__file__).parent
APP = (ROOT / "app.py").read_text(encoding="utf-8")
ROUTES = (ROOT / "modules/admin_system_routes.py").read_text(encoding="utf-8")
ROOM_ROUTES = (ROOT / "modules/room_access_routes.py").read_text(encoding="utf-8")
ADMIN = (ROOT / "templates/admin.html").read_text(encoding="utf-8")
ROOM = (ROOT / "templates/room_detail.html").read_text(encoding="utf-8")
PARTIAL = (ROOT / "templates/partials/room_dynamic_state.html").read_text(encoding="utf-8")
CSS = (ROOT / "static/css/rank_mode_toggle.css").read_text(encoding="utf-8")

def test_center_design_config_and_reset_exist():
    assert 'ROOM_CENTER_DESIGN_SETTING_KEY = "room_center_design_config"' in APP
    assert 'ROOM_CENTER_DESIGN_DEFAULTS' in APP
    assert 'normalize_room_center_design_config' in APP
    assert 'get_room_center_design_config' in APP
    assert 'admin_update_room_center_design_config' in ROUTES
    assert 'request.form.get("config_action") == "reset"' in ROUTES

def test_admin_exposes_major_center_element_sizes():
    for name in ('stage_padding','stage_gap','mode_width','mode_padding','vs_size','score_width','score_padding','score_input_height','action_height','vertical_layout'):
        assert f'name="{name}"' in ADMIN
    assert 'Trở về mặc định' in ADMIN

def test_room_receives_center_design_variables():
    assert 'room_center_design_config' in ROOM_ROUTES
    for source in (ROOM, PARTIAL):
        assert '--room-center-stage-gap:' in source
        assert '--room-center-vs-size:' in source
        assert 'data-center-layout=' in source

def test_css_uses_real_dimensions_not_transform_for_center_blocks():
    for marker in ('--room-center-stage-padding','--room-center-mode-width','--room-center-vs-size','--room-center-score-width','--room-center-action-height'):
        assert marker in CSS
    assert 'justify-content: space-evenly' in CSS

def test_version_is_v1312():
    assert 'APP_VERSION = "V1.3.16"' in APP
