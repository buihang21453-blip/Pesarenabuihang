from pathlib import Path

ROOT = Path(__file__).parent
APP = (ROOT / "app.py").read_text(encoding="utf-8")
ADMIN_ROUTES = (ROOT / "modules/admin_player_routes.py").read_text(encoding="utf-8")
ADMIN_DASH = (ROOT / "modules/admin_dashboard_routes.py").read_text(encoding="utf-8")
ADMIN = (ROOT / "templates/admin.html").read_text(encoding="utf-8")
PROFILE_ROUTES = (ROOT / "modules/profile/routes.py").read_text(encoding="utf-8")
HISTORY = (ROOT / "modules/match_history_routes.py").read_text(encoding="utf-8")


def test_version_and_invisible_setting_exist():
    assert 'APP_VERSION = "V1.4.29"' in APP
    assert 'INVISIBLE_PLAYERS_SETTING_KEY = "invisible_player_ids"' in APP
    assert "get_invisible_player_ids" in APP
    assert "can_view_player_identity" in APP
    assert "filter_players_for_viewer" in APP


def test_ranking_removes_hidden_slots_for_normal_viewers_but_preserves_self_admin_position():
    assert "global_position_map" in APP
    assert "preserve_global_positions" in APP
    assert "viewer_is_invisible" in APP
    assert "player_rows = filter_players_for_viewer(eligible_player_rows, user, invisible_ids)" in APP


def test_hidden_accounts_are_filtered_from_discovery_surfaces():
    assert "presence_rows = filter_players_for_viewer(presence_rows, user, invisible_ids)" in APP
    assert "player_rows = invite_visible_players(current_user(), include_admin=True, force_invisible_refresh=True)" in APP
    assert "if not can_view_player_identity(oid, user, invisible_ids):" in APP
    assert "players = filter_players_for_viewer(list_players(include_admin=True), viewer)" in APP
    assert "if not can_view_player_identity(user_id, viewer):" in PROFILE_ROUTES
    assert "match_visible_to_viewer(match, user, invisible_ids)" in HISTORY


def test_admin_can_toggle_invisibility_per_player():
    assert "admin_toggle_player_invisibility" in ADMIN_ROUTES
    assert "update_player_invisibility" in ADMIN_ROUTES
    assert '"is_invisible"' in ADMIN_DASH
    assert "👻 Tàng hình" in ADMIN
    assert "👻 Bật tàng hình" in ADMIN
    assert "Hiện tài khoản" in ADMIN

