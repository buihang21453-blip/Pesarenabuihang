from pathlib import Path
ROOT = Path(__file__).resolve().parent
APP = (ROOT / 'app.py').read_text(encoding='utf-8')
ROUTES = (ROOT / 'modules' / 'tournament_routes.py').read_text(encoding='utf-8')
TPL = (ROOT / 'templates' / 'tournaments.html').read_text(encoding='utf-8')
ADMIN = (ROOT / 'templates' / 'admin.html').read_text(encoding='utf-8')

def test_version_1424():
    assert 'APP_VERSION = "V1.4.27"' in APP

def test_tournament_is_closed_by_default_and_admin_can_toggle():
    assert 'enabled = False' in ROUTES
    assert "'/admin/tournaments/access'" in ROUTES
    assert 'tournament_area_enabled' in ADMIN

def test_no_tournament_mock_data():
    assert 'PES Arena Champions League' in TPL
    assert 'PES Arena Cup Season 2' not in TPL
    assert 'Super League Season 2' not in TPL

def test_basic_tournament_sections_exist():
    for text in ['Đang diễn ra','Sắp diễn ra','Đã kết thúc','TỔNG QUAN','LỊCH THI ĐẤU','BẢNG XẾP HẠNG','NHÁNH ĐẤU','THỐNG KÊ']:
        assert text in TPL

def test_closed_message_exists():
    assert 'GIẢI ĐẤU TẠM ĐÓNG' in TPL
