from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parent
APP = (ROOT / "app.py").read_text(encoding="utf-8")
SESSION_JS = (ROOT / "static" / "js" / "session-timeout.js").read_text(encoding="utf-8")
RUNTIME = (ROOT / "modules" / "session_runtime_service.py").read_text(encoding="utf-8")


def test_version_and_python_parse():
    assert 'APP_VERSION = "V1.4.8"' in APP
    ast.parse(APP)


def test_playing_room_timeout_is_longer_than_session_idle_window():
    assert 'ROOM_MATCH_INACTIVITY_TIMEOUT_SECONDS = 4 * 60 * 60' in APP
    assert 'IDLE_TIMEOUT_SECONDS = 60 * 60' in RUNTIME


def test_room_requests_refresh_server_activity_before_idle_logout():
    assert 'request.path.startswith("/room/")' in APP
    assert 'request.path.startswith("/api/room/")' in APP
    assert 'session["last_real_activity"] = now_ts' in APP
    assert 'room_request_active' in APP


def test_room_tab_keeps_session_alive_when_browser_is_hidden():
    assert 'const isRoomPage = global.location.pathname.startsWith("/room/");' in SESSION_JS
    assert '(document.hidden && !isRoomPage)' in SESSION_JS
    assert '(!document.hidden || isRoomPage)' in SESSION_JS


def test_playing_statuses_are_still_protected_from_idle_logout():
    assert '"playing"' in RUNTIME
    assert '"friendly_playing"' in RUNTIME
    assert '"waiting_result_confirm"' in RUNTIME
