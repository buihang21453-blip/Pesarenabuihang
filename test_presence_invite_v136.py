from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP = (ROOT / "app.py").read_text(encoding="utf-8")
BASE = (ROOT / "templates" / "base.html").read_text(encoding="utf-8")
PRESENCE_JS = (ROOT / "static" / "js" / "presence.js").read_text(encoding="utf-8")


def test_presence_timeout_has_safe_margin():
    assert 'ONLINE_TIMEOUT_SECONDS = 120' in APP


def test_heartbeat_runs_immediately_and_in_background():
    assert 'visibleInterval: 30000' in BASE
    assert 'hiddenInterval: 60000' in BASE
    assert 'runWhenHidden: true' in PRESENCE_JS
    assert 'immediate: true' in PRESENCE_JS
    assert 'jitter: 3000' in BASE


def test_presence_refreshes_when_returning_to_browser():
    assert "document.addEventListener('visibilitychange'" in PRESENCE_JS
    assert "window.addEventListener('focus', heartbeatOnResume)" in PRESENCE_JS
    assert 'postHeartbeat();' in PRESENCE_JS


def test_pagehide_no_longer_forces_offline():
    assert "window.addEventListener('pagehide', sendOffline" not in BASE
    route = APP[APP.index('@app.route("/presence/offline"'):APP.index('@app.route("/api/invites/pending")')]
    assert 'mark_current_user_offline()' not in route


def test_heartbeat_is_not_double_written_in_before_request():
    assert 'if request.endpoint != "heartbeat" and now_ts - last_touch >= 60:' in APP
    heartbeat_route = APP[APP.index('@app.route("/heartbeat"'):APP.index('@app.route("/presence/offline"')]
    assert 'mark_current_user_active()' in heartbeat_route
    assert 'session["last_activity_touch"] = int(time.time())' in heartbeat_route


def test_quick_match_uses_same_presence_timeout():
    assert 'max(ONLINE_TIMEOUT_SECONDS, 90)' not in APP
    assert APP.count('timedelta(seconds=ONLINE_TIMEOUT_SECONDS)') >= 2
