from pathlib import Path

ROOT = Path(__file__).parent
ADMIN = (ROOT / "templates/admin.html").read_text(encoding="utf-8")
JS = (ROOT / "static/js/admin_dashboard.js").read_text(encoding="utf-8")
APP = (ROOT / "app.py").read_text(encoding="utf-8")


def test_room_settings_are_grouped_in_dedicated_tab():
    assert 'data-admin-tab="room-design"' in ADMIN
    assert 'data-admin-panel="room-design"' in ADMIN
    room_section = ADMIN.split('data-admin-panel="room-design"', 1)[1].split('data-admin-panel="economy"', 1)[0]
    for marker in (
        'Phong cách phòng đấu',
        'Tuỳ chỉnh logo chế độ thi đấu',
        'Bố cục 3 khung phòng đấu',
        'Link Discord phòng đấu',
        'Giao diện nút Tìm Nhanh',
    ):
        assert marker in room_section


def test_admin_forms_keep_current_tab_after_save():
    assert "input.name = '_admin_tab'" in JS
    assert 'panel.dataset.adminPanel' in JS
    assert 'request.form.get("_admin_tab")' in APP
    assert 'APP_VERSION = "V1.4.7"' in APP
