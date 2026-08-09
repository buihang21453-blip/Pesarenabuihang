from pathlib import Path
import ast
ROOT=Path(__file__).resolve().parent
APP=(ROOT/'app.py').read_text(encoding='utf-8')

def test_version_and_core_modules():
    assert 'APP_VERSION = "V1.2.10"' in APP
    for name in ['achievements','rank_team_service','room_runtime','user_repository','match_repository','social_runtime','matchmaking_runtime']:
        p=ROOT/'modules'/'core'/f'{name}.py'
        assert p.exists()
        ast.parse(p.read_text(encoding='utf-8'))

def test_flow_service_is_registered():
    assert 'from modules import room_flow_service as _room_flow_service' in APP
    text=(ROOT/'modules'/'room_flow_service.py').read_text(encoding='utf-8')
    for state in ['waiting_ready','playing','waiting_result_confirm','confirmed']:
        assert state in text

def test_key_routes_use_shared_flow_guard():
    team=(ROOT/'modules'/'room_team_routes.py').read_text(encoding='utf-8')
    result=(ROOT/'modules'/'room_result_routes.py').read_text(encoding='utf-8')
    rematch=(ROOT/'modules'/'room_rematch_routes.py').read_text(encoding='utf-8')
    assert 'require_room_action(room, "ready")' in team
    assert 'require_room_action(room, "random_team")' in team
    assert 'require_room_action(room, "submit_result")' in result
    assert 'require_room_action(room, "confirm_result")' in result
    assert 'require_room_action(room, "rematch")' in rematch

def test_app_reduced_monolith_helpers():
    tree=ast.parse(APP)
    names={n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
    assert 'get_user' not in names
    assert 'get_room' not in names
    assert 'list_matches' not in names
    assert 'active_room_for_user' not in names
