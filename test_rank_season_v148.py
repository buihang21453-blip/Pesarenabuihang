from pathlib import Path
APP=Path("app.py").read_text(encoding="utf-8")
ROUTES=Path("modules/season_routes.py").read_text(encoding="utf-8")
SQL=Path("docs/update_rank_season_v1_4_8.sql").read_text(encoding="utf-8")

def test_v148_version():
    assert 'APP_VERSION = "V1.4.13"' in APP

def test_reset_is_atomic_rpc():
    assert "db.rpc('reset_rank_season_open_next'" in ROUTES
    assert "update public.users" in SQL
    assert "insert into public.rank_seasons" in SQL
    assert "rank_season_current" in SQL

def test_reset_failure_is_caught_and_visible():
    assert "season reset failed" in ROUTES
    assert "Database đã tự hoàn tác" in ROUTES

def test_rpc_guards_snapshot_rewards_and_repeat():
    assert "Season snapshot missing" in SQL
    assert "Top 3 reward logs missing" in SQL
    assert "already_done" in SQL
