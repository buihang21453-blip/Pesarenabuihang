from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parent


def test_blackbox_migration_is_server_only_and_grants_service_role():
    sql = (ROOT / 'project_docs/sql/20260808_blackbox.sql').read_text(encoding='utf-8').lower()
    assert 'create table if not exists public.blackbox_events' in sql
    assert 'create table if not exists public.blackbox_incidents' in sql
    assert 'enable row level security' in sql
    assert 'revoke all on table public.blackbox_events from anon, authenticated' in sql
    assert 'revoke all on table public.blackbox_incidents from anon, authenticated' in sql
    assert 'grant select, insert on table public.blackbox_events to service_role' in sql
    assert 'grant select, insert on table public.blackbox_incidents to service_role' in sql


def test_blackbox_safety_reports_missing_schema_helpfully():
    src = (ROOT / 'modules/blackbox/safety.py').read_text(encoding='utf-8')
    ast.parse(src)
    assert 'project_docs/sql/20260808_blackbox.sql' in src
    assert 'blackbox_incidents' in src


def test_admin_sticky_tabs_are_below_topbar():
    css = (ROOT / 'static/css/admin_dashboard.css').read_text(encoding='utf-8')
    assert 'body[data-page="admin"] .admin-tabs{top:102px}' in css
    assert '@media(max-width:520px){body[data-page="admin"] .admin-tabs{top:84px}' in css


def test_overlap_scanner_ignores_offscreen_controls():
    js = (ROOT / 'static/js/blackbox_safety_lab.js').read_text(encoding='utf-8')
    assert 'r.bottom <= 0' in js
    assert 'r.top >= innerHeight' in js
    assert 'r.right <= 0' in js
    assert 'r.left >= innerWidth' in js


def test_room_result_routes_receive_series_helper_before_registration():
    app = (ROOT / 'app.py').read_text(encoding='utf-8')
    export_pos = app.find('for _service_name in _service_module.EXPORTED_NAMES')
    register_pos = app.find('_register_room_result_routes,')
    assert export_pos != -1 and register_pos != -1 and export_pos < register_pos
    assert '"is_series_child_match"' in (ROOT / 'modules/rank_series/service.py').read_text(encoding='utf-8')
