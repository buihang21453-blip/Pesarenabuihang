from pathlib import Path

ROOT = Path(__file__).resolve().parent

def read(path):
    return (ROOT / path).read_text(encoding='utf-8')

def test_v1254_version_and_button_owner():
    assert 'APP_VERSION = "V1.2.54"' in read('app.py')
    html = read('templates/room_detail.html')
    live = read('templates/_room_live_content.html')
    assert "css/room/buttons.css" in html
    for src in (html, live):
        assert 'room-neon-green' in src
        assert 'room-neon-gold' in src
        assert 'room-neon-red' in src

def test_reference_skin_contract():
    css = read('static/css/room/buttons.css')
    import re
    code = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    assert '!important' not in code
    assert 'border-radius:8px' in css
    assert 'background-color:rgba(3,7,10,.94)' in css
    assert 'box-shadow:' in css
    assert '--room-neon-color:#d59a17' in css
    assert '--room-neon-color:#17d85a' in css
    assert '--room-neon-color:#e52d24' in css
    assert 'transform:none' in css

def test_legacy_size_rules_do_not_take_neon_skin():
    css = read('static/css/room_detail.css')
    assert '.room-center-action-btn:not(.room-neon-btn)' in css
    quick = read('static/css/quick_match.css')
    assert ':not(.room-neon-btn)' in quick

def test_quick_match_is_single_button_width():
    css = read('static/css/room_v2.css')
    assert 'width:clamp(132px,44%,145px)' in css
    assert 'max-width:145px' in css
