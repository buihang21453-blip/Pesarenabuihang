from pathlib import Path
ROOT = Path(__file__).resolve().parent
APP = (ROOT/'app.py').read_text(encoding='utf-8')
ROUTES = (ROOT/'modules'/'season_routes.py').read_text(encoding='utf-8')
ADMIN = (ROOT/'templates'/'admin.html').read_text(encoding='utf-8')
RANK = (ROOT/'templates'/'ranking.html').read_text(encoding='utf-8')
PUBLIC = (ROOT/'templates'/'public_ranking.html').read_text(encoding='utf-8')

def test_version_v1413():
    assert 'APP_VERSION = "V1.4.25"' in APP

def test_season_dropdown_simple_labels():
    assert 'SEASON {{ season.season_number }}' in RANK
    assert 'SEASON {{ season.season_number }}' in PUBLIC
    assert 'Đã kết thúc' not in RANK.split('id="season-select"',1)[1].split('</select>',1)[0]

def test_top3_personal_notification_routes():
    assert "'/admin/season/notify-top3'" in ROUTES
    assert 'create_user_notification(' in ROUTES
    assert 'Gửi thông báo thưởng Top 3' in ADMIN

def test_three_system_notification_buttons():
    assert "season_closed" in ROUTES
    assert "season_started_detail" in ROUTES
    assert "season_welcome" in ROUTES
    assert 'Gửi thông báo #1' in ADMIN
    assert 'Gửi thông báo #2' in ADMIN
    assert 'Gửi thông báo #3' in ADMIN
