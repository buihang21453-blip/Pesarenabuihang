from pathlib import Path

ROOT = Path(__file__).resolve().parent

def test_version():
    assert 'APP_VERSION = "1.3.120"' in (ROOT/'app.py').read_text(encoding='utf-8')

def test_final_bridge_load_order():
    html=(ROOT/'templates/room_detail.html').read_text(encoding='utf-8')
    a=html.index('21-target-side-rail-bridge.css')
    b=html.index('22-target-mode-strip-bridge.css')
    c=html.index('23-target-action-states-bridge.css')
    assert a < b < c

def test_mode_bridge_keeps_six_column_desktop_and_selected_logo_priority():
    css=(ROOT/'static/css/room/22-target-mode-strip-bridge.css').read_text(encoding='utf-8')
    assert 'grid-template-columns:repeat(6,minmax(0,1fr))' in css
    assert '.room-master-mode-card.is-selected .room-master-card-icon img' in css

def test_action_bridge_covers_result_and_confirm_without_html_rewrite():
    css=(ROOT/'static/css/room/23-target-action-states-bridge.css').read_text(encoding='utf-8')
    assert '.room-center-score-panel' in css
    assert '.room-result-review' in css
    assert '.room-result-dispute-form' in css

def test_real_mode_assets_are_still_template_driven():
    t=(ROOT/'templates/room/_bottom_modes_history.html').read_text(encoding='utf-8')
    assert 'mode_asset(mode.code)' in t
    assert 'assets/modes/' not in t
