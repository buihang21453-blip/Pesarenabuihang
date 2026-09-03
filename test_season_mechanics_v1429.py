from pathlib import Path

APP = Path('app.py').read_text(encoding='utf-8')
WEEKLY = Path('modules/weekly_rp_rewards_service.py').read_text(encoding='utf-8')
REPEAT = Path('modules/repeat_opponent_rp_service.py').read_text(encoding='utf-8')
INACTIVE = Path('modules/inactivity_rp_service.py').read_text(encoding='utf-8')
RESULT = Path('modules/match_result_service.py').read_text(encoding='utf-8')
ADMIN = Path('templates/admin.html').read_text(encoding='utf-8')
SQL = Path('docs/update_season_mechanics_v1_4_29.sql').read_text(encoding='utf-8')


def test_version_v1429():
    assert 'APP_VERSION = "V1.4.29"' in APP


def test_win_loss_streak_queries_are_season_bounded():
    assert '_current_season_mechanics_start_iso' in APP
    assert 'query = query.gte("created_at", season_start)' in APP
    assert 'new_loss_streak = current_loss_streak + 1' in RESULT
    assert '"loss_streak": new_loss_streak' in RESULT


def test_weekly_rewards_are_season_scoped():
    assert 'season_number' in WEEKLY
    assert '_bounded_week_window' in WEEKLY
    assert 'activity_start' in WEEKLY
    assert 'season_number integer not null default 1' in SQL
    assert 'uq_weekly_rp_rewards_season_user_week_code' in SQL


def test_repeat_opponent_and_inactivity_are_season_bounded():
    assert '_current_season_started_at' in REPEAT
    assert 'start_iso = season_start.isoformat()' in REPEAT
    assert '_current_season_context' in INACTIVE
    assert 'query = query.gte("created_at", season_start.isoformat())' in INACTIVE
    assert 'USER_SETTING_PREFIX}s{season_number}_' in INACTIVE


def test_season_stats_store_streaks_and_new_season_resets_them():
    assert 'add column if not exists streak' in SQL
    assert 'add column if not exists loss_streak' in SQL
    assert 'streak=0,loss_streak=0' in SQL.replace(' ', '').replace('\n','')


def test_admin_recent_match_names_link_to_profiles():
    assert 'm.player1_profile_available' in ADMIN
    assert "url_for('profile', user_id=m.player1_id)" in ADMIN
    assert 'm.player2_profile_available' in ADMIN
    assert "url_for('profile', user_id=m.player2_id)" in ADMIN
