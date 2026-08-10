from pathlib import Path
ROOT = Path(__file__).resolve().parent

def test_version_and_admin_tab_loading_contract():
    app = (ROOT / 'app.py').read_text(encoding='utf-8')
    route = (ROOT / 'modules/admin_dashboard_routes.py').read_text(encoding='utf-8')
    js = (ROOT / 'static/js/admin_dashboard.js').read_text(encoding='utf-8')
    assert 'APP_VERSION = "V1.2.18"' in app
    assert 'active_tab = str(request.args.get("tab")' in route
    assert 'list_admin_overview_users(limit=300)' in route
    assert 'elif active_tab == "users"' in route
    assert 'elif active_tab == "matches"' in route
    assert "serverTabs = new Set" in js
    assert "?tab=" in js

def test_admin_heavy_sources_are_not_loaded_unconditionally():
    route = (ROOT / 'modules/admin_dashboard_routes.py').read_text(encoding='utf-8')
    prefix = route.split('if active_tab == "overview":', 1)[0]
    assert 'list_all_users(' not in prefix
    assert 'list_user_devices(' not in prefix
    assert 'list_admin_activity_logs(' not in prefix
    assert 'list_matches()' not in prefix

def test_repository_supports_limits_and_pages():
    users = (ROOT / 'modules/core/user_repository.py').read_text(encoding='utf-8')
    matches = (ROOT / 'modules/core/match_repository.py').read_text(encoding='utf-8')
    rooms = (ROOT / 'modules/core/room_runtime.py').read_text(encoding='utf-8')
    assert 'def list_all_users(limit=None, offset=0):' in users
    assert '.range(offset, offset + limit - 1)' in users
    assert 'def list_matches(status=None, limit=None, offset=0):' in matches
    assert 'def list_invites(status=None, limit=None, enrich=True):' in matches
    assert 'def list_rooms(status=None, limit=None, enrich=True):' in rooms
