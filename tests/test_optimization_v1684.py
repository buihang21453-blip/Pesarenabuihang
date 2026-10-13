from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p): return (ROOT/p).read_text(encoding='utf-8')
def test_version_1684(): assert 'APP_VERSION = "V1.6.84"' in read('app.py')
def test_admin_db_limits_and_no_get_cleanup():
    s=read('modules/admin_dashboard_routes.py')
    assert 'list_matches(limit=80)' in s
    assert 'list_rooms(limit=80)' in s
    assert 'cleanup_duplicate_waiting_rooms(uid)' not in s
    assert 'admin_match_report' in s
    assert 'admin_migration_checks_v1684' in s
def test_tournament_hot_reads_explicit():
    s=read('modules/tournament_routes.py')
    assert 'TOURNAMENT_MATCH_COLUMNS' in s
    assert 'TOURNAMENT_REG_COLUMNS' in s
    assert 'tournament_admin_data_v1684' in s
    assert "db.table('match_rooms').select('*').order('updated_at'" not in s
