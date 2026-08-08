from pathlib import Path
ROOT=Path(__file__).parent

def test_admin_rank_modes_tab_and_save_route():
    html=(ROOT/'templates/admin.html').read_text(encoding='utf-8')
    routes=(ROOT/'modules/admin_dashboard_routes.py').read_text(encoding='utf-8')
    assert 'data-admin-tab="rank-modes"' in html
    assert 'data-admin-panel="rank-modes"' in html
    assert 'admin_save_rank_modes' in html and '/admin/rank-modes' in routes
    for code in ('rank_random','random3_pick1','tactical_bo3','bo3','ban_pick_bo3','home_away'):
        assert code in (ROOT/'modules/rank_modes/catalog.py').read_text(encoding='utf-8')

def test_admin_report_has_series_metrics():
    html=(ROOT/'templates/admin.html').read_text(encoding='utf-8')
    routes=(ROOT/'modules/admin_dashboard_routes.py').read_text(encoding='utf-8')
    for token in ('score_2_0','score_2_1','forfeit','rp_added','rp_removed','comebacks','unlocked_players'):
        assert token in html or token in routes
