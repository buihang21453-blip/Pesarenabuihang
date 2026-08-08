import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def read(path):
    return (ROOT / path).read_text(encoding="utf-8")

def test_version_and_python_parse():
    assert 'APP_VERSION = "V1.2.9"' in read("app.py")
    for path in ("app.py", "modules/profile/equipment_service.py", "modules/room_access_routes.py"):
        ast.parse(read(path), filename=path)

def test_profile_badge_is_loaded_in_public_player_maps():
    equipment = read("modules/profile/equipment_service.py")
    app = read("app.py")
    assert 'PUBLIC_PROFILE_SLOTS = ("avatar_frame", "name_style", "profile_badge")' in equipment
    assert "def build_profile_badge_map" in equipment
    assert "profile_badge_map = profile_equipment_service.build_profile_badge_map(safe)" in app
    assert 'item["profile_badge"] = profile_badge_map.get(user_id)' in app

def test_badge_is_rendered_in_players_and_room():
    players = read("templates/players.html")
    room = read("templates/room_detail.html")
    live = read("templates/_room_live_content.html")
    assert "p.profile_badge.image_url" in players
    for template in (room, live):
        assert "room.host_profile_badge.image_url" in template
        assert "room.guest_profile_badge.image_url" in template

def test_host_kick_route_allows_ready_guest_without_rp_penalty():
    routes = read("modules/room_access_routes.py")
    assert 'endpoint="room_kick_guest"' in routes
    assert 'room.get("status") != "waiting_ready"' in routes
    assert 'Đối thủ đã bấm Sẵn sàng nên không thể bị đưa ra khỏi phòng.' not in routes
    assert '.eq("guest_ready", False)' not in routes
    assert '"guest_user_id": None' in routes
    assert '"guest_ready": False' in routes
    assert '"host_kick_room_guest"' in routes
    assert 'không bị trừ RP' in routes
    assert 'create_user_notification(' in routes

def test_kick_button_is_visible_in_guest_card_for_ready_or_unready_guest():
    for path in ("templates/room_detail.html", "templates/_room_live_content.html"):
        template = read(path)
        assert "url_for('room_kick_guest'" in template
        assert "room-guest-card-kick" in template
        assert "Kể cả khi đã Sẵn sàng" in template
        assert "room.status == \"waiting_ready\" and room_room_viewer_is_host" in template
        assert "Chỉ chủ phòng sử dụng được trước khi đối thủ bấm Sẵn sàng." not in template
