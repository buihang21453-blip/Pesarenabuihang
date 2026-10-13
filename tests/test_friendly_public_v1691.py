from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def test_v1691_route_is_public_and_static():
    src=(ROOT/'modules/friendly_public_routes.py').read_text(encoding='utf-8')
    assert "@app.route('/friendly')" in src
    assert 'login_required' not in src
    for forbidden in ('db.table(', 'execute_query(', 'create_client(', '.channel('):
        assert forbidden not in src.lower()

def test_v1691_client_random_has_no_network_api():
    src=(ROOT/'static/js/friendly_public.js').read_text(encoding='utf-8')
    for mode in ('premier_league','la_liga','five_star','four_star','club_five_star','nation_five_star'):
        assert mode in src
    for forbidden in ('fetch(', 'XMLHttpRequest', '/api/', '.channel('):
        assert forbidden.lower() not in src.lower()

def test_v1691_links_guest_and_logged_in():
    assert "url_for('friendly_public')" in (ROOT/'templates/public_ranking.html').read_text(encoding='utf-8')
    assert "url_for('friendly_public')" in (ROOT/'templates/login.html').read_text(encoding='utf-8')
    assert "url_for('friendly_public')" in (ROOT/'templates/base.html').read_text(encoding='utf-8')
