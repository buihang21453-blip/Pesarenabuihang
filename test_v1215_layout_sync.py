from pathlib import Path

ROOT = Path(__file__).resolve().parent
ROOM = (ROOT / 'templates/room_detail.html').read_text(encoding='utf-8')
LIVE = (ROOT / 'templates/_room_live_content.html').read_text(encoding='utf-8')
CSS = (ROOT / 'static/css/room_detail.css').read_text(encoding='utf-8')
APP = (ROOT / 'app.py').read_text(encoding='utf-8')


def test_version_1215():
    assert 'APP_VERSION = "V1.2.15"' in APP


def test_shell_has_layout_state_class_and_badge():
    assert 'room-layout-v1215 room-state-{{ room_layout_state }}' in ROOM
    assert 'room-stage-state-badge' in ROOM
    for state in ('waiting-opponent','waiting-ready','playing','waiting-confirm','confirmed','disputed'):
        assert state in ROOM


def test_confirmed_uses_same_result_review_layout():
    marker = "room.status in ['waiting_result_confirm', 'confirmed']"
    assert marker in ROOM and marker in LIVE
    assert 'room-result-confirmed-badge' in ROOM and 'room-result-confirmed-badge' in LIVE
    assert ROOM.count("url_for('room_rematch'") == 1
    assert LIVE.count("url_for('room_rematch'") == 1


def test_layout_css_has_stable_geometry():
    required = (
        '.room-layout-v1215',
        '--room-layout-card-min-h',
        '.room-layout-v1215 .room-center-stage-plain',
        '.room-layout-v1215 .room-result-review',
        '.room-layout-v1215 .room-result-confirmed-badge',
        '.room-layout-v1215.room-state-confirmed .room-finished-summary{display:none}',
    )
    for token in required:
        assert token in CSS
