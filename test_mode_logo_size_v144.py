from pathlib import Path

MODE_OWNER = Path('static/css/room/13-mode-stability.css')


def test_bottom_logo_final_override_is_in_mode_owner():
    css = MODE_OWNER.read_text(encoding='utf-8')
    assert 'transform: scale(2.65)' in css
    assert 'grid-template-columns: 82px minmax(0,1fr)' in css or 'grid-template-columns:82px minmax(0,1fr)' in css


def test_active_mode_logo_is_in_mode_owner_without_layout_growth():
    css = MODE_OWNER.read_text(encoding='utf-8')
    assert 'transform: scale(2.45)' in css
    assert 'overflow: hidden' in css or 'overflow:hidden' in css
