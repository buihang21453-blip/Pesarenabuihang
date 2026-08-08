from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP = (ROOT / 'app.py').read_text(encoding='utf-8')
ADMIN = (ROOT / 'modules/admin_dashboard_routes.py').read_text(encoding='utf-8')
READ = (ROOT / 'modules/read_model_service.py').read_text(encoding='utf-8')
PROFILE = (ROOT / 'modules/profile/service.py').read_text(encoding='utf-8')
SQL = (ROOT / 'project_docs/sql/PES_ARENA_READ_MODEL_V1.3.34.sql').read_text(encoding='utf-8')


def test_version_and_read_model_wired():
    assert 'APP_VERSION = "1.3.34"' in APP
    assert 'load_match_report' in APP
    assert 'load_recent_form_map' in APP


def test_admin_match_report_does_not_scan_history():
    start = ADMIN.index('# V1.3.34: Báo cáo là READ MODEL')
    end = ADMIN.index('raw_users =', start)
    block = ADMIN[start:end]
    assert 'load_match_report(report_range)' in block
    assert 'db.table("matches")' not in block
    assert 'db.table("match_rooms")' not in block
    assert 'db.table("match_series")' not in block
    assert 'for match in report_matches' not in block


def test_ranking_no_longer_loads_all_confirmed_matches():
    ranking = APP[APP.index('def ranking():'):APP.index('# Hồ sơ cá nhân đã tách')]
    assert 'load_recent_form_map' in ranking
    assert 'list_matches(status="confirmed")' not in ranking


def test_dashboard_only_loads_user_matches():
    dashboard = APP[APP.index('def dashboard():'):APP.index('@app.route("/rooms/create"')]
    assert 'load_user_matches(user.get("id"), limit=30)' in dashboard
    assert 'matches = list_matches()' not in dashboard


def test_profile_uses_cache_and_targeted_queries():
    block = PROFILE[PROFILE.index('def build_profile_context'):]
    assert 'load_user_matches(user_id, limit=50)' in block
    assert 'load_player_profile_summary(user_id)' in block
    assert 'load_pair_stats(viewer_id, user_id)' in block
    assert 'all_matches = list_matches()' not in block


def test_sql_has_precomputed_tables_and_triggers():
    for table in (
        'admin_match_daily_stats', 'admin_match_mode_daily_stats',
        'admin_match_player_daily_stats', 'admin_series_daily_stats',
        'player_recent_form_cache', 'player_profile_stats_cache',
        'player_pair_stats_cache', 'admin_rank_mode_unlock_stats',
        'admin_user_ip_summary_cache',
    ):
        assert f'create table if not exists public.{table}' in SQL.lower()
    assert 'trg_pes_matches_read_model' in SQL
    assert 'pes_refresh_match_stats_day' in SQL
