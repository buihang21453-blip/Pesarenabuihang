from pathlib import Path
ROOT=Path(__file__).parent

def read(p): return (ROOT/p).read_text(encoding='utf-8')

def test_v122_single_visual_authority():
    room=read('templates/room_detail.html')
    assert 'APP_VERSION = "1.3.122"' in read('app.py')
    assert '25-full-mockup-v122.css' in room
    for old in ('12-mockup-layout-lock.css','19-target-layout-bridge.css','20-target-center-bridge.css','21-target-side-rail-bridge.css','22-target-mode-strip-bridge.css','23-target-action-states-bridge.css','24-real-layout-v121.css'):
        assert old not in room

def test_v122_real_four_column_layout():
    css=read('static/css/room/25-full-mockup-v122.css')
    assert 'grid-template-areas:"host center guest rail"' in css
    assert 'grid-template-columns:minmax(300px,1.03fr) minmax(360px,.90fr) minmax(300px,1.03fr) minmax(280px,.70fr)' in css
    assert 'grid-template-columns:repeat(6,minmax(0,1fr))' in css
    assert '.room-master-mode-card.is-selected .room-master-card-icon img' in css

def test_v122_history_moved_to_right_rail_in_both_render_paths():
    side=read('templates/room/_side_rail.html')
    bottom=read('templates/room/_bottom_modes_history.html')
    live=read('templates/_room_live_content.html')
    assert 'room-side-history-slot' in side and 'partials/room_history_panel.html' in side
    assert 'room-bottom-side' not in bottom
    assert 'room-side-history-slot' in live
    assert 'room-bottom-side' not in live
