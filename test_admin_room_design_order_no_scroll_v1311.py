from pathlib import Path

ROOT = Path(__file__).parent
APP = (ROOT / "app.py").read_text(encoding="utf-8")
ADMIN = (ROOT / "templates/admin.html").read_text(encoding="utf-8")
CSS = (ROOT / "static/css/rank_mode_toggle.css").read_text(encoding="utf-8")

def test_version_and_room_style_is_last_room_design_panel():
    assert 'APP_VERSION = "V1.4"' in APP
    room_design = ADMIN.split('data-admin-panel="room-design"', 1)[1].split('</section>', 1)[0]
    assert room_design.rfind('🎨 Phong cách phòng đấu') > room_design.rfind('⚡ Giao diện nút Tìm Nhanh')

def test_three_room_panels_do_not_use_internal_scrollbars():
    marker = 'PES Arena V1.3.11 — Admin đặt chiều cao cơ sở'
    block = CSS.split(marker, 1)[1]
    assert 'height: auto !important;' in block
    assert 'min-height: var(--room-panel-height, 600px) !important;' in block
    assert 'max-height: none !important;' in block
    assert 'overflow-y: visible !important;' in block
    assert 'overflow-y: auto !important;' not in block

