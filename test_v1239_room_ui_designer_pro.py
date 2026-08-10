from pathlib import Path
from jinja2 import Environment
ROOT = Path(__file__).resolve().parent

def read(path):
    return (ROOT / path).read_text(encoding='utf-8')

def test_v1239_version_and_templates_parse():
    assert 'APP_VERSION = "V1.2.39"' in read('app.py')
    env = Environment()
    env.parse(read('templates/room_detail.html'))
    env.parse(read('templates/admin/tabs/room-ui.html'))

def test_symmetric_player_columns_and_no_x_controls():
    tpl = read('templates/admin/tabs/room-ui.html')
    room = read('templates/room_detail.html')
    assert 'player_width' in tpl
    assert '--rui-host:{{ room_ui_config.player_width }}fr' in room
    assert '--rui-away:{{ room_ui_config.player_width }}fr' in room
    assert 'name="host_x"' not in tpl and 'name="opponent_x"' not in tpl
    assert 'name="avatar_x"' not in tpl and 'name="vs_x"' not in tpl

def test_center_actions_and_mode_logo_advanced_controls():
    tpl = read('templates/admin/tabs/room-ui.html')
    css = read('static/css/room_v2.css')
    for key in ('center_button_height','center_action_width','center_action_gap','mode_logo_size'):
        assert key in tpl
    assert '--rui-center-button-height' in css
    assert '--rui-mode-logo-size' in css
    assert 'width:100%!important' in css

def test_right_rail_advanced_controls():
    tpl = read('templates/admin/tabs/room-ui.html')
    for key in ('rail_parsec_ratio','rail_room_history_ratio','rail_h2h_ratio','rail_gap'):
        assert key in tpl
