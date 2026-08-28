from pathlib import Path
APP=Path('app.py').read_text(encoding='utf-8')
RANK=Path('templates/ranking.html').read_text(encoding='utf-8')
PUBLIC=Path('templates/public_ranking.html').read_text(encoding='utf-8')
SQL=Path('docs/update_rank_season_v1_4_9.sql').read_text(encoding='utf-8')

def test_version(): assert 'APP_VERSION = "V1.4.16"' in APP
def test_historical_snapshot_is_source():
    assert 'ranking_historical_snapshot' in APP
    assert 'rank_season_snapshots' in APP
    assert 'base["rank_points"] = int(row.get("rank_points") or 0)' in APP
def test_season_selector():
    assert 'name="season"' in RANK and 'name="season"' in PUBLIC
    assert 'SEASON {{ season.season_number }}' in RANK and 'SEASON {{ season.season_number }}' in PUBLIC
def test_safe_recovery_sql():
    assert "if v_current < 2 then" in SQL.lower()
    assert "Không tìm thấy Snapshot Season 1" in SQL
    assert "KHÔNG chạm RP" in SQL
