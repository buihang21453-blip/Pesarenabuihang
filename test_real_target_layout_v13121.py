from pathlib import Path
ROOT = Path(__file__).resolve().parent

def test_version_and_css_loaded_last():
    assert 'APP_VERSION = "1.3.121"' in (ROOT/'app.py').read_text(encoding='utf-8')
    html=(ROOT/'templates/room_detail.html').read_text(encoding='utf-8')
    assert '24-real-layout-v121.css' in html
    assert html.index('24-real-layout-v121.css') > html.index('23-target-action-states-bridge.css')

def test_real_four_column_ratio():
    css=(ROOT/'static/css/room/24-real-layout-v121.css').read_text(encoding='utf-8')
    assert 'minmax(300px,1.03fr) minmax(360px,.90fr) minmax(300px,1.03fr) minmax(280px,.70fr)' in css
    assert 'height:590px!important' in css

def test_assets_and_function_templates_untouched_by_new_layer():
    css=(ROOT/'static/css/room/24-real-layout-v121.css').read_text(encoding='utf-8')
    assert 'url(' not in css
    assert 'action=' not in css.lower()
