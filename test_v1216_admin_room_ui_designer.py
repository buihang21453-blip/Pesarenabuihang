from pathlib import Path

ROOT = Path(__file__).resolve().parent


def test_module_files_exist():
    required = [
        ROOT / 'modules/admin_room_ui/service.py',
        ROOT / 'modules/admin_room_ui/routes.py',
        ROOT / 'templates/admin/tabs/room-ui.html',
        ROOT / 'static/js/admin/room-ui-designer.js',
        ROOT / 'static/css/admin/room-ui-designer.css',
    ]
    assert all(p.exists() for p in required)


def test_admin_tab_and_routes_are_connected():
    app = (ROOT / 'app.py').read_text(encoding='utf-8')
    admin = (ROOT / 'templates/admin.html').read_text(encoding='utf-8')
    routes = (ROOT / 'modules/admin_room_ui/routes.py').read_text(encoding='utf-8')
    assert '_register_admin_room_ui_routes' in app
    assert 'data-admin-tab="room-ui"' in admin
    assert 'data-admin-panel="room-ui"' in admin
    assert '/admin/room-ui/save' in routes
    assert '/admin/room-ui/reset' in routes


def test_room_layout_uses_designer_config_for_all_states():
    room = (ROOT / 'templates/room_detail.html').read_text(encoding='utf-8')
    css = (ROOT / 'static/css/room_detail.css').read_text(encoding='utf-8')
    assert 'room-ui-configurable' in room
    assert '--rui-host:{{ room_ui_config.host_width }}fr' in room
    assert '--rui-center:{{ room_ui_config.center_width }}fr' in room
    assert '--rui-away:{{ room_ui_config.opponent_width }}fr' in room
    assert '--rui-side:{{ room_ui_config.sidebar_width }}fr' in room
    assert '.room-ui-configurable .room-team-card.home' in css
    assert '.room-ui-configurable .room-center-stage-plain' in css
    assert '.room-ui-configurable .room-team-card.away' in css
    assert '.room-ui-configurable .room-arena-right-rail' in css


def test_six_modes_share_one_scale_setting():
    service = (ROOT / 'modules/admin_room_ui/service.py').read_text(encoding='utf-8')
    template = (ROOT / 'templates/admin/tabs/room-ui.html').read_text(encoding='utf-8')
    assert '"mode_logo_scale"' in service
    assert 'mode_1_logo_scale' not in service.split('FIELD_SPECS =',1)[1]
    assert 'Tỷ lệ chung' in template


def test_no_new_supabase_table_required():
    service = (ROOT / 'modules/admin_room_ui/service.py').read_text(encoding='utf-8')
    assert 'table("system_settings")' in service
    assert 'room_ui_designer_config' in service


def test_version_1216_and_state_preview():
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    tpl = (ROOT / "templates/admin/tabs/room-ui.html").read_text(encoding="utf-8")
    assert 'APP_VERSION = "V1.2.16"' in app
    for key in ["waiting","ready","playing","confirm","confirmed","rematch"]:
        assert f'data-room-ui-preview-state="{{{{ key }}}}"' in tpl or key in tpl
