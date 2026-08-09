from pathlib import Path

ROOT = Path(__file__).resolve().parent
STYLE = (ROOT / 'static/style.css').read_text(encoding='utf-8')
ROOM = (ROOT / 'static/css/room_detail.css').read_text(encoding='utf-8')
BASE = (ROOT / 'templates/base.html').read_text(encoding='utf-8')
APP = (ROOT / 'app.py').read_text(encoding='utf-8')

def test_version():
    assert 'APP_VERSION = "V1.2.14"' in APP

def test_room_css_is_conditional():
    assert "request.endpoint == 'room_detail'" in BASE
    assert "css/room_detail.css" in BASE

def test_major_room_blocks_moved_out_of_global_style():
    assert 'Room redesign v1.10.0' not in STYLE
    assert 'Collap_V1.13.7' not in STYLE
    assert 'Room redesign v1.10.0' in ROOM
    assert 'Collap_V1.13.7' in ROOM

def test_room_module_css_still_separate():
    for name in ['quick_match.css','parsec_room.css','rank_mode_toggle.css']:
        assert (ROOT / 'static/css' / name).exists()

def test_global_css_reduced():
    assert len(STYLE.encode('utf-8')) < 220_000
    assert STYLE.count('.room') < 200
