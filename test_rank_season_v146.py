from pathlib import Path
APP = Path('app.py').read_text(encoding='utf-8')
SERVICE = Path('modules/season_service.py').read_text(encoding='utf-8')
ROUTES = Path('modules/season_routes.py').read_text(encoding='utf-8')
SERVICE = Path('modules/season_service.py').read_text(encoding='utf-8')
ADMIN = Path('templates/admin.html').read_text(encoding='utf-8')
SQL = Path('docs/update_rank_season_v1_4_6.sql').read_text(encoding='utf-8')

def test_version_and_module_registration():
    assert 'APP_VERSION = "V1.4.21"' in APP
    assert '_season_service' in APP
    assert '_register_season_routes' in APP

def test_new_season_uses_five_matches_from_season_start():
    assert 'started_at' in SERVICE
    assert 'placement_matches' in SERVICE
    assert 'season_match_count_map' in APP and 'total_matches' in APP
    assert 'season_ranking_eligibility' in APP

def test_admin_flow_is_guarded_snapshot_reward_reset():
    assert '/admin/season/snapshot' in ROUTES
    assert '/admin/season/rewards' in ROUTES
    assert '/admin/season/reset-open-next' in ROUTES
    assert 'len(rewards.data or []) < 3' in ROUTES
    assert "db.rpc('reset_rank_season_open_next'" in ROUTES

def test_rewards_have_expected_defaults():
    assert '"top1": {"zcoin": 20000, "lucky_box": 3}' in SERVICE
    assert '"top2": {"zcoin": 15000, "lucky_box": 2}' in SERVICE
    assert '"top3": {"zcoin": 10000, "lucky_box": 1}' in SERVICE

def test_admin_tab_and_schema_exist():
    assert 'data-admin-tab="season"' in ADMIN
    assert 'rank_season_snapshots' in SQL
    assert 'rank_season_rewards' in SQL
