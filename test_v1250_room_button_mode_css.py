from pathlib import Path
ROOT=Path(__file__).resolve().parent

def read(p): return (ROOT/p).read_text(encoding='utf-8')

def test_version_and_imports():
    assert 'APP_VERSION = "V1.2.50"' in read('app.py')
    t=read('templates/room_detail.html')
    assert "css/room/buttons.css" in t
    assert "css/room/mode_cards.css" in t

def test_quick_match_does_not_restyle_neon():
    q=read('static/css/quick_match.css')
    assert '.room-quick-match-btn:not(.room-neon-btn)' in q
    assert '.room-quick-match-btn.room-quick-match-green' not in q

def test_mode_logos_single_fixed_owner():
    r=read('static/css/room_v2.css')
    m=read('static/css/room/mode_cards.css')
    assert '.room-v2-mode-card.mode-7 img' not in r
    assert 'transform:scale(.72)' not in r and 'transform:scale(.78)' not in r
    assert '--room-mode-logo-fixed-size:64px' in m
    assert 'width:var(--room-mode-logo-fixed-size)' in m
    assert 'height:var(--room-mode-logo-fixed-size)' in m
