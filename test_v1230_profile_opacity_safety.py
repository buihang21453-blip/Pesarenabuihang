from pathlib import Path
import ast
ROOT=Path(__file__).parent

def read(rel): return (ROOT/rel).read_text(encoding="utf-8")

def test_profile_route_has_safe_fallback():
    routes=read("modules/profile/routes.py")
    service=read("modules/profile/service.py")
    assert "build_profile_context_fallback" in routes
    assert "PROFILE-" in routes
    assert "def build_profile_context_fallback" in service
    ast.parse(service); ast.parse(routes)

def test_room_ui_has_component_opacity_controls():
    svc=read("modules/admin_room_ui/service.py")
    tpl=read("templates/admin/tabs/room-ui.html")
    room=read("templates/room_detail.html")
    css=read("static/css/room_v2.css")
    for key in ["background_opacity","header_opacity","host_panel_opacity","center_panel_opacity","opponent_panel_opacity","sidebar_panel_opacity","mode_card_opacity","action_zone_opacity"]:
        assert key in svc and key in tpl
    for var in ["--rui-background-opacity","--rui-header-opacity","--rui-host-panel-opacity","--rui-center-panel-opacity","--rui-away-panel-opacity","--rui-sidebar-panel-opacity","--rui-mode-card-opacity","--rui-action-zone-opacity"]:
        assert var in room and var in css

def test_version_1230():
    assert 'APP_VERSION = "V1.2.30"' in read("app.py")
