from pathlib import Path
APP=Path('app.py').read_text()
CLEAN=Path('modules/data_cleanup_service.py').read_text()
ADMIN=Path('modules/admin_dashboard_routes.py').read_text()
SQL=Path('docs/update_hard_delete_account_v1_4_17.sql').read_text()

def test_version():
    assert 'APP_VERSION = "V1.4.29"' in APP

def test_delete_uses_atomic_rpc_not_soft_status():
    body=CLEAN.split('def delete_player_safe',1)[1]
    assert 'hard_delete_player_keep_match_history' in body
    assert '"account_status": "deleted"' not in body

def test_archive_identity_and_keep_matches():
    assert 'archived_player_identities' in SQL
    assert "c.relname not in ('matches'" in SQL
    assert 'delete from public.users where id = p_user_id' in SQL

def test_match_names_fallback_to_archive():
    assert 'archived_users_map()' in APP
    assert 'archived_users.get(player1_id' in APP
    assert 'archived_users.get(player2_id' in APP

def test_admin_hides_legacy_soft_deleted_rows():
    assert 'account_status") or "approved").lower() != "deleted"' in ADMIN
