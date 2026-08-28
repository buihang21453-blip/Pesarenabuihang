from pathlib import Path
APP=Path('app.py').read_text(encoding='utf-8')
ROUTES=Path('modules/season_routes.py').read_text(encoding='utf-8')
SERVICE=Path('modules/season_service.py').read_text(encoding='utf-8')
ADMIN=Path('templates/admin.html').read_text(encoding='utf-8')
SQL=Path('docs/update_rank_season_v1_4_7.sql').read_text(encoding='utf-8')

def test_v147_version(): assert 'APP_VERSION = "V1.4.7"' in APP
def test_reward_config_setting():
    assert 'SEASON_REWARD_SETTING_KEY = "rank_season_reward_config"' in SERVICE
    assert 'get_season_reward_config' in SERVICE
def test_admin_reward_inputs():
    assert 'name="top{{ pos }}_zcoin"' in ADMIN
    assert 'name="top{{ pos }}_lucky_box"' in ADMIN
    assert 'admin_season_reward_config' in ADMIN
def test_reward_route_uses_saved_config():
    assert "@app.post('/admin/season/reward-config')" in ROUTES
    assert 'reward_config = get_season_reward_config()' in ROUTES
    assert "reward_config.get(f'top{pos}'" in ROUTES
def test_sql_seeds_defaults():
    assert 'rank_season_reward_config' in SQL
    assert "'zcoin',20000" in SQL and "'lucky_box',3" in SQL
