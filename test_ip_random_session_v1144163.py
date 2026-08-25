from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parent
APP = (ROOT / "app.py").read_text(encoding="utf-8")
ADMIN = (ROOT / "templates" / "admin.html").read_text(encoding="utf-8")
SESSION_JS = (ROOT / "static" / "js" / "session-timeout.js").read_text(encoding="utf-8")
SYSTEM_ROUTES = (ROOT / "modules" / "admin_system_routes.py").read_text(encoding="utf-8")
PLAYER_ROUTES = (ROOT / "modules" / "admin_player_routes.py").read_text(encoding="utf-8")


def test_version_and_python_parse():
    assert 'APP_VERSION = "V1.4.5"' in APP
    ast.parse(APP)
    ast.parse(SYSTEM_ROUTES)
    ast.parse(PLAYER_ROUTES)


def test_duplicate_ip_controls_present():
    assert 'duplicate_ip_warning_config' in APP
    assert 'admin_update_duplicate_ip_warning' in ADMIN
    assert 'admin_toggle_duplicate_ip_trust' in ADMIN
    assert 'user_ignored_for_duplicate_ip' in APP


def test_random3_uses_each_players_rank_config():
    assert 'host_tier_weights": get_rank_tier_weights(host_level)' in APP
    assert 'guest_tier_weights": get_rank_tier_weights(guest_level)' in APP
    assert '_pick_rank_team(' in APP
    assert 'player.get("rank_points", 0)' in APP


def test_visible_tab_and_real_activity_keep_session_alive():
    assert '"pointermove"' in SESSION_JS
    assert '"wheel"' in SESSION_JS
    assert '"scroll"' in SESSION_JS
    assert 'startVisibleKeepalive()' in SESSION_JS
    assert '"api_session_activity"' in APP
    assert 'session["last_real_activity"] = int(time.time())' in APP
