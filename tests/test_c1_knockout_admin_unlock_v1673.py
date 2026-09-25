from pathlib import Path
from jinja2 import Environment

ROOT = Path(__file__).resolve().parents[1]


def read(rel):
    return (ROOT / rel).read_text(encoding='utf-8')


def test_v1673_version_and_shared_setting_key():
    assert 'APP_VERSION = "V1.6.75"' in read('app.py')
    comp = read('modules/tournament_competition.py')
    assert 'KNOCKOUT_UNLOCK_KEY = "knockout_match_unlocks_v1"' in comp


def test_admin_can_unlock_or_lock_any_knockout_pair():
    rewards = read('modules/tournament_competition_parts/rewards.py')
    assert "knockout/pair-access" in rewards
    assert 'action not in {"unlock","lock"}' in rewards
    assert 'unlock_order' in rewards
    assert 'ops_ko_pair_access_save' in rewards


def test_new_bracket_pairs_default_to_locked():
    core = read('modules/tournament_competition_parts/core.py')
    assert 'def _knockout_pair_is_unlocked' in core
    assert 'return bool(entry.get("unlocked"))' in core
    rewards = read('modules/tournament_competition_parts/rewards.py')
    assert '"setting_value":{"entries":{},"sequence":0' in rewards


def test_public_ui_disables_room_button_until_admin_unlocks():
    routes = read('modules/tournament_routes.py')
    template = read('templates/tournament/components/knockout_dashboard.html')
    assert '"can_enter": is_unlocked' in routes
    assert '🔒 Chờ BTC mở trận' in routes
    assert '{% if nxt.can_enter %}' in template
    assert '🔒 CHỜ BTC MỞ TRẬN' in template


def test_backend_blocks_locked_knockout_across_entry_paths():
    rooms = read('modules/tournament_competition_parts/rooms.py')
    fixed = read('modules/c1_fixed_match_service.py')
    assert rooms.count('_knockout_pair_is_unlocked') >= 4
    assert 'BTC chưa mở cặp Knockout này' in rooms
    assert 'BTC đã khóa cặp Knockout này' in rooms
    assert 'c1_fixed_start_ko_unlock' in fixed
    assert 'BTC chưa mở cặp Knockout này.' in fixed


def test_admin_template_contains_pair_control_panel_and_templates_parse():
    admin_tpl = read('templates/admin_parts/c1_knockout.html')
    assert '🎛️ Điều hành từng cặp KO' in admin_tpl
    assert '🔓 Mở cặp này' in admin_tpl
    assert '🔒 Khóa lại' in admin_tpl
    env = Environment()
    env.parse(admin_tpl)
    env.parse(read('templates/tournament/components/knockout_dashboard.html'))
