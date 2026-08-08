from pathlib import Path
from modules.blackbox import service
from modules.blackbox.safety import source_isolation_audit

ROOT = Path(__file__).parent


def test_v1354_version_and_safety_lab_files():
    app = (ROOT / 'app.py').read_text(encoding='utf-8')
    assert 'APP_VERSION = "1.3.54"' in app
    assert (ROOT / 'modules/blackbox/safety.py').exists()
    assert (ROOT / 'static/js/blackbox_safety_lab.js').exists()
    tab = (ROOT / 'templates/admin/tabs/blackbox.html').read_text(encoding='utf-8')
    assert 'Black Box Safety Lab' in tab
    assert 'Chạy kiểm tra tự động' in tab


def test_kill_switch_does_not_load_client_when_disabled():
    base = (ROOT / 'templates/base.html').read_text(encoding='utf-8')
    assert 'bb_cfg.enabled and bb_cfg.client_enabled' in base
    assert 'blackbox_runtime_config' in base


def test_critical_gameplay_sources_unchanged_from_v1352():
    results = source_isolation_audit()
    assert results
    assert all(x['status'] == 'PASS' for x in results), results


def test_fail_open_forced_storage_exception():
    service.configure({'APP_VERSION': '1.3.54'})
    def explode(_rows, _incidents):
        raise RuntimeError('forced')
    result = service.blackbox_store_batch(
        user_id=None,
        session_id='test',
        page='/',
        events=[{'type': 'test_event'}],
        client={},
        _storage_override=explode,
    )
    assert result['ok'] is False
    assert result['reason'] == 'storage_failed'


def test_safety_endpoint_is_admin_only():
    routes = (ROOT / 'modules/blackbox/routes.py').read_text(encoding='utf-8')
    assert '/api/admin/blackbox/safety' in routes
    frag = routes.split('/api/admin/blackbox/safety', 1)[1][:300]
    assert '@login_required' in frag
    assert '@admin_required' in frag
