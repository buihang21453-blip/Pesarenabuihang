from pathlib import Path
ROOT=Path(__file__).resolve().parent
APP=(ROOT/'app.py').read_text(encoding='utf-8')
SQL=(ROOT/'docs/update_season_player_stats_v1_4_19.sql').read_text(encoding='utf-8')
ROUTES=(ROOT/'modules/season_routes.py').read_text(encoding='utf-8')

def test_version_1419():
    assert 'APP_VERSION = "V1.4.25"' in APP

def test_ranking_reads_season_table():
    assert 'db.table("season_player_stats").select("*").eq("season_number", requested_sn)' in APP
    assert 'season_stats_by_id' in APP

def test_schema_isolated_by_composite_key():
    assert 'primary key (season_number, user_id)' in SQL
    assert 'rank_points integer not null default 1000' in SQL
    assert 'recent_form jsonb' in SQL

def test_migration_preserves_history():
    low=SQL.lower()
    assert 'delete from public.matches' not in low
    assert 'truncate public.matches' not in low
    assert 'delete from public.rank_season_snapshots' not in low

def test_current_user_changes_are_mirrored():
    assert 'sync_user_current_season_stats' in SQL
    assert 'trg_sync_user_current_season_stats' in SQL

def test_new_season_is_seeded():
    assert 'reset_rank_season_open_next' in ROUTES and 'season_player_stats' in SQL
