from pathlib import Path
ROOT = Path(__file__).resolve().parent

def read(path):
    return (ROOT / path).read_text(encoding='utf-8')

def test_version_is_13118():
    assert 'APP_VERSION = "1.3.118"' in read('app.py')

def test_part3_css_is_loaded_after_part1_bridge():
    room = read('templates/room_detail.html')
    assert 'css/room/20-target-center-bridge.css' in room
    assert room.index('19-target-layout-bridge.css') < room.index('20-target-center-bridge.css')

def test_part3_is_css_ratio_only_and_keeps_existing_template_assets():
    center = read('templates/room/_center_stage.html')
    live = read('templates/_room_live_content.html')
    assert 'mode_asset(selected_rank_mode)' in center
    assert 'mode_asset(selected_rank_mode)' in live
    assert "room_asset('vs-gold-emblem.webp')" in center
    assert "asset_url('vs.webp')" in live
    css = read('static/css/room/20-target-center-bridge.css')
    assert 'room-state-waiting_ready' in css
    assert 'width:175px!important' in css
    assert 'height:105px!important' in css
    assert 'min-height:318px!important' in css

def test_part3_does_not_touch_result_or_backend_sources():
    css = read('static/css/room/20-target-center-bridge.css')
    assert '.room-center-score-panel' not in css
    assert '.room-result-review' not in css
    assert 'url_for(' not in css

def test_project_map_declares_part3_owner():
    m = read('PROJECT_MAP.md')
    assert '20-target-center-bridge.css' in m
    assert 'PHẦN 3' in m
