from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
def read(p): return (ROOT/p).read_text(encoding="utf-8")

def test_version_1690():
    assert 'APP_VERSION = "V1.6.90"' in read('app.py')

def test_admin_deep_data_is_tab_scoped():
    src=read('modules/admin_dashboard_routes.py')
    assert 'active_admin_tab == "match-report"' in src
    assert 'active_admin_tab == "rooms"' in src
    assert 'active_admin_tab == "logs"' in src
    assert 'active_admin_tab == "database"' in src

def test_admin_tab_navigation_requests_server_dataset():
    js=read('static/js/admin_dashboard.js')
    assert "url.searchParams.set('tab', tabName)" in js
    html=read('templates/admin.html')
    assert "tab='match-report'" in html
