from pathlib import Path
ROOT=Path(__file__).resolve().parent
ROOM=ROOT/'static/css/room'
OWNER=ROOM/'17-center-match-stability.css'
LEGACY=[ROOM/f'{i:02d}-{n}' for i,n in [
(1,'shell-layout.css'),(2,'club-visuals.css'),(3,'mode-selector.css'),(4,'actions-history.css'),(5,'action-states.css'),(6,'responsive-performance.css'),(7,'parsec-history-polish.css'),(8,'action-layout-guard.css'),(9,'series-orchestrator.css'),(10,'prestart-flow.css'),(11,'index-layout-reconnect.css'),(12,'mockup-layout-lock.css')]]
MARKERS=['.room-center-stage-plain','.room-center-vs-image','.room-center-countdown-label','.room-center-countdown','.room-center-status-note','.room-center-score-panel','.room-result-review','.room-score-title','.room-score-fields','.room-score-form','.room-series-hud-slot','.series-room-panel']

def test_center_owner_loaded_between_12_and_13():
    html=(ROOT/'templates/room_detail.html').read_text(encoding='utf-8')
    i12=html.index('12-mockup-layout-lock.css')
    i17=html.index('17-center-match-stability.css')
    i13=html.index('13-mode-stability.css')
    assert i12 < i17 < i13

def test_owner_contains_core_center_rules():
    css=OWNER.read_text(encoding='utf-8')
    for marker in ['.room-center-stage-plain','.room-center-vs-image','.room-center-countdown','.room-center-score-panel']:
        assert marker in css

def test_old_room_01_to_12_no_longer_own_center_markers_except_series_skin():
    for f in LEGACY:
        txt=f.read_text(encoding='utf-8')
        # 09 keeps the series component skin, but the stage HUD slot itself belongs to 17.
        checked=MARKERS
        for marker in checked:
            assert marker not in txt, f'{marker} still in {f.name}'
