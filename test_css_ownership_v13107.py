from pathlib import Path
ROOT=Path(__file__).resolve().parent
ROOM=ROOT/'static/css/room'
OWNER=ROOM/'18-active-mode-status-stability.css'
OLD=[ROOM/n for n in ['01-shell-layout.css','03-mode-selector.css','05-action-states.css','06-responsive-performance.css','10-prestart-flow.css','11-index-layout-reconnect.css','12-mockup-layout-lock.css','17-center-match-stability.css']]
MARKERS=['room-master-active-mode','room-master-mode-number','room-master-mode-heading','room-master-unlock-pill','room-master-room-ready','room-ready-status']

def test_owner_loaded_after_17_and_before_13():
    html=(ROOT/'templates/room_detail.html').read_text(encoding='utf-8')
    assert html.index('17-center-match-stability.css') < html.index('18-active-mode-status-stability.css') < html.index('13-mode-stability.css')

def test_owner_contains_all_target_markers():
    css=OWNER.read_text(encoding='utf-8')
    for marker in MARKERS:
        assert marker in css

def test_old_modules_no_longer_own_target_markers():
    for f in OLD:
        txt=f.read_text(encoding='utf-8')
        for marker in MARKERS:
            assert marker not in txt, f'{marker} still in {f.name}'
