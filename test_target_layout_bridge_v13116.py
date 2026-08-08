from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP = (ROOT / 'app.py').read_text(encoding='utf-8')
ROOM = (ROOT / 'templates/room_detail.html').read_text(encoding='utf-8')
CSS = (ROOT / 'static/css/room/19-target-layout-bridge.css').read_text(encoding='utf-8')


def test_version_116():
    assert 'APP_VERSION = "1.3.116"' in APP


def test_bridge_loaded_last():
    assert '19-target-layout-bridge.css' in ROOM
    assert ROOM.index('16-side-rail-history-stability.css') < ROOM.index('19-target-layout-bridge.css')


def test_target_desktop_ratio_only():
    assert 'minmax(300px,1.03fr)' in CSS
    assert 'minmax(360px,.90fr)' in CSS
    assert 'minmax(280px,.70fr)' in CSS
    assert 'grid-template-areas:"home center away rail"' in CSS
    assert 'gap:10px' in CSS
    assert 'height:590px' in CSS


def test_topbar_ratio():
    assert 'min-height:96px' in CSS
    assert 'minmax(360px,1.2fr)' in CSS
    assert 'width:min(520px,82%)' in CSS


def test_bridge_does_not_replace_assets_or_logic():
    lowered = CSS.lower()
    for token in ('url(', 'background-image', 'room_asset(', 'asset_url(', 'fetch(', '/api/', 'form action'):
        assert token not in lowered
