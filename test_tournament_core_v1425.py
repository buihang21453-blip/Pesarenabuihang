from pathlib import Path

def test_version_and_sql_exist():
    assert 'APP_VERSION = "V1.4.26"' in Path('app.py').read_text()
    sql = Path('docs/update_tournament_core_v1_4_25.sql').read_text().lower()
    assert 'create table if not exists public.tournaments' in sql
    assert 'create table if not exists public.tournament_registrations' in sql
    assert 'create table if not exists public.tournament_members' in sql
    assert 'champion-league-arena' in sql

def test_tournament_routes_are_independent():
    src = Path('modules/tournament_routes.py').read_text()
    assert "'/tournaments/<tournament_id>/register'" in src
    assert "'/admin/tournaments/registrations/<registration_id>/approve'" in src
    assert "'/admin/tournaments/registrations/<registration_id>/reject'" in src
    assert "'/admin/tournaments/<tournament_id>/members/add'" in src
    assert 'season_player_stats' not in src
    assert 'rank_points' not in src

def test_tournament_ui_has_registration_and_admin_review():
    public = Path('templates/tournaments.html').read_text()
    admin = Path('templates/admin.html').read_text()
    assert 'Đăng ký tham gia' in public
    assert 'Đang chờ Admin duyệt' in public
    assert 'Chờ duyệt' in admin
    assert 'Thêm HLV trực tiếp' in admin
