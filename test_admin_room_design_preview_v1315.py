from pathlib import Path

ROOT=Path(__file__).parent
ADMIN=(ROOT/"templates/admin.html").read_text(encoding="utf-8")
CSS=(ROOT/"static/style.css").read_text(encoding="utf-8")
JS=(ROOT/"static/js/admin_dashboard.js").read_text(encoding="utf-8")
APP=(ROOT/"app.py").read_text(encoding="utf-8")

def test_room_design_tab_has_live_preview():
    assert 'id="adminRoomPreview"' in ADMIN
    assert 'Preview phòng đấu' in ADMIN
    assert 'admin-room-preview-stage' in ADMIN
    assert 'admin-room-preview-mode-dock' in ADMIN

def test_preview_reflects_room_design_controls_live():
    for name in ('panel_height','stage_padding','stage_gap','mode_width','mode_padding','vs_size','score_width','score_padding','score_input_height','action_height','room_mode_logo_background_opacity','room_mode_logo_scale','room_mode_dock_logo_scale','center_bars_visible','vertical_layout','room_visual_style'):
        assert name in JS
    assert 'syncPreview' in JS
    assert '--preview-panel-height' in CSS
    assert '[data-center-bars="hidden"]' in CSS

def test_version_1315():
    assert 'APP_VERSION = "V1.4.14"' in APP
