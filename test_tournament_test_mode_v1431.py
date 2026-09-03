from pathlib import Path
ROOT=Path(__file__).parent

def test_module_registered():
    app=(ROOT/'app.py').read_text(encoding='utf-8')
    assert 'tournament_test_mode' in app
    assert '_register_tournament_test_mode_routes' in app

def test_routes_and_isolation():
    src=(ROOT/'modules/tournament_test_mode.py').read_text(encoding='utf-8')
    assert '/admin/tournament-test-mode' in src
    assert 'tournament_test_sandboxes' in src
    assert 'db.table("matches")' not in src
    assert 'db.table("zcoin' not in src.lower()
    assert 'db.table("lucky' not in src.lower()

def test_sql_is_sandbox_only():
    sql=(ROOT/'docs/update_tournament_test_mode_v1_4_31.sql').read_text(encoding='utf-8').lower()
    assert 'tournament_test_sandboxes' in sql
    assert 'public.matches' not in sql
    assert 'tournament_matches' not in sql

def test_admin_link_and_role_switch():
    admin=(ROOT/'templates/admin.html').read_text(encoding='utf-8')
    tpl=(ROOT/'templates/tournament_test_mode.html').read_text(encoding='utf-8')
    assert 'admin_tournament_test_mode' in admin
    assert 'Xem với tư cách' in tpl
    assert 'spectator' in tpl
