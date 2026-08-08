from pathlib import Path

ROOT = Path(__file__).resolve().parent

def test_version_bumped():
    assert 'APP_VERSION = "1.3.119"' in (ROOT/'app.py').read_text(encoding='utf-8')

def test_bridge_is_loaded_last():
    text=(ROOT/'templates/room_detail.html').read_text(encoding='utf-8')
    assert "css/room/21-target-side-rail-bridge.css" in text
    assert text.index('20-target-center-bridge.css') < text.index('21-target-side-rail-bridge.css')

def test_bridge_scoped_to_room():
    css=(ROOT/'static/css/room/21-target-side-rail-bridge.css').read_text(encoding='utf-8')
    assert '.arena-room-v2 .room-side-info-panel' in css
    assert '.arena-room-v2 .parsec-room-panel' in css
    assert '.arena-room-v2 .room-bottom-side .room-history-full' in css

def test_side_rail_template_untouched_core_bindings():
    text=(ROOT/'templates/room/_side_rail.html').read_text(encoding='utf-8')
    assert '#{{ room.room_code }}' in text
    assert '{{ room.match_mode_label }}' in text
    assert '{% include "partials/parsec_room_panel.html" %}' in text

def test_no_demo_assets_in_bridge():
    css=(ROOT/'static/css/room/21-target-side-rail-bridge.css').read_text(encoding='utf-8')
    for name in ('player-host.webp','player-guest.webp','assets/modes/','vs-gold-emblem.webp'):
        assert name not in css
