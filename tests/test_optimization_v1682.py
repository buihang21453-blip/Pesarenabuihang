from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def read(p): return (ROOT/p).read_text(encoding='utf-8')

def test_version_1682():
    assert 'APP_VERSION = "V1.6.82"' in read('app.py')

def test_history_has_db_side_pagination():
    s=read('modules/legacy_match_service.py')
    assert 'def list_history_matches_page' in s
    assert 'count="exact"' in s
    assert '.range(start, start+per_page-1)' in s
    assert 'MATCH_READ_COLUMNS' in s

def test_history_route_uses_safe_db_page_and_fallback():
    s=read('modules/match_history_routes.py')
    assert 'db_paged = history_view == "mine" and not query and status_filter != "cancelled"' in s
    assert 'list_history_matches_page' in s
    assert 'rows = list_matches()' in s

def test_ranking_activity_is_narrow():
    svc=read('modules/legacy_match_service.py')
    route=read('modules/ranking_routes.py')
    assert 'def list_ranking_activity_matches' in svc
    assert '.in_("status", ["confirmed", "cancelled"])' in svc
    assert 'ranking_activity_matches = list_ranking_activity_matches()' in route

def test_index_sql_present():
    s=read('SQL_CU/SQL_V1.6.82_DB_READ_INDEXES.sql')
    assert 'idx_matches_player1_created_at' in s
    assert 'idx_matches_player2_created_at' in s
    assert 'idx_season_player_stats_season_rank' in s
