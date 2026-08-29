from pathlib import Path

ROOT = Path(__file__).parent
APP = (ROOT / "app.py").read_text(encoding="utf-8")
CSS = (ROOT / "static/css/rank_mode_toggle.css").read_text(encoding="utf-8")
ADMIN = (ROOT / "templates/admin.html").read_text(encoding="utf-8")
ROOMS = [
    (ROOT / "templates/room_detail.html").read_text(encoding="utf-8"),
    (ROOT / "templates/_room_live_content.html").read_text(encoding="utf-8"),
    (ROOT / "templates/partials/room_dynamic_state.html").read_text(encoding="utf-8"),
]


def test_version_v1310():
    assert 'APP_VERSION = "V1.4.20"' in APP


def test_real_three_room_elements_are_targeted_exactly():
    assert '.room-arena-frame > section.room-side-card.room-team-card.home' in CSS
    assert '.room-arena-frame > section.room-center-stage-plain' in CSS
    assert '.room-arena-frame > section.room-side-card.room-team-card.away' in CSS
    assert 'min-height: var(--room-panel-height, 600px) !important;' in CSS
    assert 'height: auto !important;' in CSS
    assert 'max-height: none !important;' in CSS
    assert 'overflow-y: visible !important;' in CSS
    assert 'scrollbar-width: none !important;' in CSS


def test_room_templates_contain_the_three_target_elements_and_variable():
    for source in ROOMS:
        assert 'room-side-card room-team-card home' in source
        assert 'room-center-stage-plain' in source
        assert 'room-side-card room-team-card away' in source
    assert '--room-panel-height:' in ROOMS[0]
    assert '--room-panel-height:' in ROOMS[2]


def test_admin_explains_direct_height_behavior():
    assert 'Cả 3 khung luôn bằng nhau' in ADMIN
    assert 'không xuất hiện thanh cuộn trong khung' in ADMIN
    assert 'nếu nội dung nhiều hơn, cả hàng tự giãn thêm' in ADMIN
