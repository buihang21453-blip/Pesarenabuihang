from pathlib import Path

BASE = Path("templates/base.html").read_text(encoding="utf-8")
APP = Path("app.py").read_text(encoding="utf-8")

def test_version_v129():
    assert 'APP_VERSION = "V1.3.9"' in APP

def test_pending_invite_poller_runs_on_room_pages():
    section = BASE[BASE.index('let pendingInvitePoller'):BASE.index('// Active room')]
    assert 'if (!isRoomPage) {' not in section
    assert 'pendingInvitePoller = PESNet.createPoller' in section
    assert 'checkPendingInvites();' in section
