from pathlib import Path

APP = Path('app.py').read_text(encoding='utf-8')
BASE = Path('templates/base.html').read_text(encoding='utf-8')
ROUTES = Path('modules/tournament_routes.py').read_text(encoding='utf-8')
TPL = Path('templates/tournaments.html').read_text(encoding='utf-8')


def test_version_v1422():
    assert 'APP_VERSION = "V1.4.23"' in APP


def test_tournament_is_registered_as_separate_module():
    assert 'modules.tournament_routes' in APP
    assert '_register_tournament_routes' in APP
    assert "@app.get('/tournaments')" in ROUTES


def test_sidebar_has_tournament_tab():
    assert "url_for('tournaments')" in BASE
    assert '> Giải đấu</a>' in BASE


def test_shell_has_no_mock_tournament_data():
    assert 'TỔNG QUAN' in TPL
    assert 'LỊCH THI ĐẤU' in TPL
    assert 'BẢNG XẾP HẠNG' in TPL
    assert 'NHÁNH ĐẤU' in TPL
    assert 'THỐNG KÊ' in TPL
    assert 'Chưa có giải đấu được mở' in TPL
