from pathlib import Path
ROOT=Path(__file__).resolve().parent
APP=(ROOT/'app.py').read_text(encoding='utf-8')
CLEAN=(ROOT/'modules/data_cleanup_service.py').read_text(encoding='utf-8')
ADMIN=(ROOT/'templates/admin.html').read_text(encoding='utf-8')
PROFILE=(ROOT/'modules/profile/routes.py').read_text(encoding='utf-8')

def test_v1416_version_and_status():
    assert 'APP_VERSION = "V1.4.27"' in APP
    assert '"deleted"' in APP.split('ACCOUNT_STATUSES',1)[1].split('\n',1)[0]

def test_delete_is_history_preserving_hard_delete():
    body=CLEAN.split('def delete_player_safe',1)[1]
    assert 'hard_delete_player_keep_match_history' in body
    assert '"account_status": "deleted"' not in body
    assert 'db.table("matches").delete()' not in body
    assert 'reverse_confirmed_match_result' not in body

def test_deleted_hidden_from_live_surfaces_but_kept_in_old_season():
    assert 'preserve_deleted=False' in APP
    assert 'preserve_deleted=True' in APP
    assert 'account_status") or "approved").lower() == "deleted"' in APP

def test_admin_has_ban_and_hard_delete_actions():
    assert 'Banned' in ADMIN
    assert 'Xóa tài khoản' in ADMIN

def test_deleted_profile_hidden_from_players():
    assert 'account_status") or "approved").lower() == "deleted"' in PROFILE
