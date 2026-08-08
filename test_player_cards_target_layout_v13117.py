from pathlib import Path

ROOT = Path(__file__).resolve().parent


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_version_is_13117():
    assert 'APP_VERSION = "1.3.117"' in read("app.py")


def test_host_and_guest_keep_real_dynamic_bindings():
    host = read("templates/room/_host_card.html")
    guest = read("templates/room/_guest_card.html")
    for token in (
        "room.host_name", "room.host_avatar_url", "room.host_rank_info",
        "room.host_team_logo_url", "room.host_team_total_stats",
    ):
        assert token in host
    for token in (
        "room.guest_name", "room.guest_avatar_url", "room.guest_rank_info",
        "room.guest_team_logo_url", "room.guest_team_total_stats",
        "room.guest_ready_label",
    ):
        assert token in guest


def test_part2_styles_are_in_shell_player_owner():
    css = read("static/css/room/14-shell-player-stability.css")
    assert "V1.3.117" in css
    assert "PHẦN 2" in css
    assert ".room-player-heading-plain .player-avatar" in css
    assert "width:94px!important" in css
    assert ".room-club-logo-large" in css
    assert "width:118px!important" in css
    assert ".room-team-points-value" in css


def test_part2_does_not_replace_project_assets_in_templates():
    host = read("templates/room/_host_card.html")
    guest = read("templates/room/_guest_card.html")
    combined = host + guest
    assert "assets/player-host.webp" not in combined
    assert "assets/player-guest.webp" not in combined
    assert "assets/clubs/" not in combined
    assert "room.host_team_logo_url" in combined
    assert "room.guest_team_logo_url" in combined


def test_layout_bridge_part1_remains_loaded_last():
    room = read("templates/room_detail.html")
    assert "css/room/19-target-layout-bridge.css" in room
    assert room.index("css/room/14-shell-player-stability.css") < room.index("css/room/19-target-layout-bridge.css")
