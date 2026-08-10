from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP = (ROOT / 'app.py').read_text(encoding='utf-8')
MATCH_REPO = (ROOT / 'modules/core/match_repository.py').read_text(encoding='utf-8')
READ = (ROOT / 'modules/read_model_service.py').read_text(encoding='utf-8')
PROFILE = (ROOT / 'modules/profile/service.py').read_text(encoding='utf-8')
ADMIN = (ROOT / 'modules/admin_dashboard_routes.py').read_text(encoding='utf-8')
SQL = (ROOT / 'project_docs/sql/PES_ARENA_READ_MODEL_V1.3.34.sql').read_text(encoding='utf-8')

def test_version():
    assert 'APP_VERSION = "V1.2.25"' in APP

def test_dashboard_only_loads_current_users_matches():
    block = APP[APP.index('def dashboard():'):APP.index('@app.route("/rooms/create"')]
    assert 'load_user_matches(user.get("id"), limit=30)' in block
    assert 'matches = list_matches()' not in block

def test_match_repository_filters_on_supabase():
    block = MATCH_REPO[MATCH_REPO.index('def list_matches'):MATCH_REPO.index('def match_status_label')]
    assert '.eq("status", status)' in block
    assert 'limit = max(1, int(limit))' in block
    assert 'query = query.limit(limit)' in block

def test_profile_does_not_scan_all_matches():
    block = PROFILE[PROFILE.index('def build_profile_context'):]
    assert 'load_user_matches(user_id, limit=50)' in block
    assert 'load_h2h_matches(viewer.get("id"), user_id, limit=10)' in block
    assert 'all_matches = list_matches()' not in block

def test_ranking_prefers_recent_form_read_model():
    block = APP[APP.index('def ranking():'):APP.index('# Hồ sơ cá nhân đã tách')]
    assert 'load_recent_form_map(top_player_ids)' in block

def test_admin_uses_read_model_when_available():
    assert 'load_match_report(report_range)' in ADMIN
    assert 'load_match_report(report_range)' in ADMIN
    assert 'list_matches(limit=500)' in ADMIN
    assert 'list_matches(status="disputed", limit=50)' in ADMIN
    assert 'list_matches(status="playing", limit=50)' in ADMIN

def test_read_model_sql_is_optional_but_complete():
    low = SQL.lower()
    for table in ('player_recent_form_cache','player_profile_stats_cache','player_pair_stats_cache','admin_match_daily_stats'):
        assert f'create table if not exists public.{table}' in low


def test_admin_report_has_short_ttl_cache():
    block = READ[READ.index('def load_match_report'):READ.index('def load_recent_form_map')]
    assert 'read_model:admin_match_report:' in block
    assert '_cache_get(cache_key)' in block
    assert '_cache_set(cache_key, (report, daily_output), 20)' in block
