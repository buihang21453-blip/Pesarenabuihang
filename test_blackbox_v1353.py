from pathlib import Path

ROOT = Path(__file__).parent


def test_blackbox_module_is_registered():
    app = (ROOT / 'app.py').read_text(encoding='utf-8')
    assert 'from modules import blackbox as _blackbox_module' in app
    assert '_register_blackbox_routes' in app
    assert 'APP_VERSION = "1.3.54"' in app


def test_blackbox_client_is_loaded_for_logged_in_users():
    base = (ROOT / 'templates/base.html').read_text(encoding='utf-8')
    assert 'PES_BLACKBOX_CONFIG' in base
    assert "js/blackbox.js" in base
    assert "api_blackbox_events" in base


def test_blackbox_has_fail_open_ingest():
    routes = (ROOT / 'modules/blackbox/routes.py').read_text(encoding='utf-8')
    service = (ROOT / 'modules/blackbox/service.py').read_text(encoding='utf-8')
    assert 'return jsonify({"ok": True' in routes
    assert 'storage_failed' in service
    assert 'blackbox_storage_failed' in service


def test_blackbox_admin_tab_exists():
    admin = (ROOT / 'templates/admin.html').read_text(encoding='utf-8')
    dashboard = (ROOT / 'modules/admin_dashboard_routes.py').read_text(encoding='utf-8')
    assert '🛡 Black Box' in admin
    assert '"blackbox"' in dashboard
    assert (ROOT / 'templates/admin/tabs/blackbox.html').exists()


def test_extension_files_exist():
    ext = ROOT / 'chrome_extension/pes_arena_blackbox'
    for name in ['manifest.json','content.js','page-hook.js','service-worker.js','popup.html','popup.js','README.txt']:
        assert (ext / name).exists(), name


def test_blackbox_migration_is_isolated():
    sql = (ROOT / 'project_docs/sql/20260808_blackbox.sql').read_text(encoding='utf-8')
    assert 'blackbox_events' in sql
    assert 'blackbox_incidents' in sql
    assert 'match_rooms' not in sql
    assert 'alter table public.blackbox_events enable row level security' in sql
