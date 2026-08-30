from pathlib import Path
ROOT=Path(__file__).resolve().parent
APP=(ROOT/'app.py').read_text(encoding='utf-8')
SQL=(ROOT/'docs/update_season_player_stats_v1_4_20.sql').read_text(encoding='utf-8')
SQL19=(ROOT/'docs/update_season_player_stats_v1_4_19.sql').read_text(encoding='utf-8')

def test_version():
    assert 'APP_VERSION = "V1.4.27"' in APP

def test_repair_uses_current_season_started_at():
    assert "rank_season_current" in SQL
    assert "m.created_at >= v_started_at" in SQL
    assert "rank_seasons" in SQL

def test_repair_does_not_touch_rp_or_history():
    low=SQL.lower()
    assert "set rank_points =" not in low
    assert "delete from public.matches" not in low
    assert "truncate public.matches" not in low
    assert "delete from public.rank_season_snapshots" not in low

def test_repair_rebuilds_all_current_stats():
    assert "SET wins = 0" in SQL
    assert "recent_form='[]'::jsonb" in SQL
    assert "ROW_NUMBER() OVER(PARTITION BY user_id" in SQL
    assert "season_number=v_current_season" in SQL

def test_known_v1419_bug_is_detected():
    assert "RP/WDL hiện đang đúng trên users" in SQL19
    assert "coalesce(u.wins,0)" in SQL19
