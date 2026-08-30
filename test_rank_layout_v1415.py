from pathlib import Path

ROOT = Path(__file__).parent
APP = (ROOT/'app.py').read_text(encoding='utf-8')
SERVICE = (ROOT/'modules'/'season_service.py').read_text(encoding='utf-8')
ROUTES = (ROOT/'modules'/'season_routes.py').read_text(encoding='utf-8')
RANKING = (ROOT/'templates'/'ranking.html').read_text(encoding='utf-8')
ADMIN = (ROOT/'templates'/'admin.html').read_text(encoding='utf-8')
CSS = (ROOT/'static'/'style.css').read_text(encoding='utf-8')

def test_version_1415():
    assert 'APP_VERSION = "V1.4.26"' in APP

def test_layout_setting_core():
    assert 'RANKING_LAYOUT_SETTING_KEY = "ranking_layout_style"' in SERVICE
    assert 'def get_ranking_layout()' in SERVICE
    assert 'value in {"horizontal", "vertical"}' in SERVICE

def test_admin_can_switch_layout():
    assert "'/admin/season/ranking-layout'" in ROUTES
    assert 'name="ranking_layout" value="horizontal"' in ADMIN
    assert 'name="ranking_layout" value="vertical"' in ADMIN
    assert 'Lưu bố cục BXH' in ADMIN

def test_vertical_order_and_tagline():
    assert 'ranking-layout-{{ ranking_layout_style' in RANKING
    assert 'THE NEW SEASON BEGINS' in RANKING
    assert 'ranking-title-after-podium' in RANKING
    assert RANKING.index('podium-stage podium-stage-cups') < RANKING.index('ranking-title-after-podium') < RANKING.index('ranking-board-panel')

def test_vertical_css():
    assert '.ranking-layout-vertical .ranking-showcase' in CSS
    assert 'flex-direction:column' in CSS


def test_public_ranking_uses_same_layout_and_keeps_empty_podium():
    public = (ROOT/'templates'/'public_ranking.html').read_text(encoding='utf-8')
    assert 'ranking-layout-{{ ranking_layout_style' in public
    assert 'THE NEW SEASON BEGINS' in public
    assert "players[0].display_name if players|length > 0 else '---'" in public
