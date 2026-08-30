from pathlib import Path
ROOT=Path(__file__).resolve().parent
APP=(ROOT/'app.py').read_text(encoding='utf-8')
SQL=(ROOT/'docs/update_season_isolated_stats_v1_4_18.sql').read_text(encoding='utf-8')

def test_version():
    assert 'APP_VERSION = "V1.4.26"' in APP

def test_current_ranking_uses_season_stats():
    assert 'season_player_stats' in APP
    assert 'season_stats_by_id' in APP

def test_sql_backfills_current_season_only():
    assert "m.created_at >= v_started_at" in SQL
    assert "SET wins = 0" in SQL
    assert "rank_points = 1000" in SQL
    assert "total_matches = 0" in SQL

def test_sql_does_not_delete_matches_or_snapshots():
    low=SQL.lower()
    assert 'delete from public.matches' not in low
    assert 'truncate public.matches' not in low
    assert 'delete from public.rank_season_snapshots' not in low
