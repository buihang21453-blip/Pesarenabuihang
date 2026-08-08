from pathlib import Path

ROOT = Path(__file__).parent
APP = (ROOT / 'app.py').read_text(encoding='utf-8')
BASE = (ROOT / 'templates/base.html').read_text(encoding='utf-8')
PRESENCE_JS = (ROOT / 'static/js/presence.js').read_text(encoding='utf-8')
PRESENCE_SERVICE = (ROOT / 'modules/presence/service.py').read_text(encoding='utf-8')
INVITE_SERVICE = (ROOT / 'modules/invites/service.py').read_text(encoding='utf-8')
INVITE_JS = (ROOT / 'static/js/invite_center.js').read_text(encoding='utf-8')


def test_v137_presence_is_physically_modularized():
    assert 'APP_VERSION = "1.3.38"' in APP
    assert "static_asset('js/presence.js')" in BASE
    assert 'def is_online(' in PRESENCE_SERVICE
    assert 'function postHeartbeat()' in PRESENCE_JS
    assert 'function postHeartbeat()' not in BASE


def test_presence_background_contract_is_in_frontend_module():
    assert "visibleInterval: Number(cfg.visibleInterval || 30000)" in PRESENCE_JS
    assert "hiddenInterval: Number(cfg.hiddenInterval || 60000)" in PRESENCE_JS
    assert 'runWhenHidden: true' in PRESENCE_JS
    assert 'immediate: true' in PRESENCE_JS
    assert "window.addEventListener('focus', heartbeatOnResume)" in PRESENCE_JS


def test_invite_business_rules_are_in_service():
    assert 'send_invite_blocker(' in APP
    assert 'SEND_INVITE_MESSAGES' in APP
    assert 'accept_invite_blocker(' in APP
    assert 'receiver_offline' in INVITE_SERVICE
    assert 'pair_pending' in INVITE_SERVICE


def test_pagehide_does_not_force_offline():
    assert 'sendBeacon' not in PRESENCE_JS
    route = APP[APP.index('def presence_offline():'):APP.index('@app.route("/api/invites/pending")')]
    assert 'mark_current_user_offline()' not in route


def test_invite_frontend_is_physically_modularized():
    assert "static_asset('js/invite_center.js')" in BASE
    assert 'function checkPendingInvites()' in INVITE_JS
    assert 'function renderInvitePopup(invite)' in INVITE_JS
    assert 'let pendingInvitesRequestPromise' not in BASE
