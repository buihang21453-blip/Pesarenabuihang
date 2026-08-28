from pathlib import Path

ROOT = Path(__file__).parent
APP = (ROOT / 'app.py').read_text(encoding='utf-8')
BASE = (ROOT / 'templates' / 'base.html').read_text(encoding='utf-8')


def test_version_v127():
    assert 'APP_VERSION = "V1.4.6"' in APP


def test_pending_api_reads_multiple_rows():
    section = APP[APP.index('def api_pending_invites'):APP.index('def api_active_room')]
    assert '.limit(20)' in section
    assert '.limit(1)' not in section


def test_pending_api_does_not_hide_invites_on_db_error():
    section = APP[APP.index('def api_pending_invites'):APP.index('def api_active_room')]
    assert 'status_code = 503' in section
    assert 'invite_poll_failed' in section


def test_invites_poll_on_history_and_guide_pages():
    assert 'pendingInvitePoller = PESNet.createPoller' in BASE
    assert 'if (!isPassivePage) {' not in BASE[BASE.index('let pendingInvitePoller'):BASE.index('// Active room')]


def test_invites_continue_checking_in_background():
    section = BASE[BASE.index('key: "pending-invites"'):BASE.index('// Active room')]
    assert 'hiddenInterval: 10000' in section
    assert 'runWhenHidden: true' in section


def test_http_errors_do_not_become_empty_invite_list():
    section = BASE[BASE.index('function checkPendingInvites'):BASE.index('function escapeHtml')]
    assert 'if (!res.ok)' in section
    assert 'throw new Error' in section
