from pathlib import Path

APP = Path('app.py').read_text(encoding='utf-8')
BASE = Path('templates/base.html').read_text(encoding='utf-8')


def test_version_v128():
    assert 'APP_VERSION = "V1.4.27"' in APP


def test_snapshot_filters_orphan_matches():
    assert 'active_match_ids = {str(r.get("match_id"))' in APP
    assert 'if str(x.get("id")) in active_match_ids' in APP


def test_snapshot_expires_stale_pending_invites():
    assert 'matchmaking_expire_stale_invite' in APP
    assert '.select("id,from_user_id,to_user_id,status,expires_at,created_at")' in APP


def test_invites_not_blocked_by_daily_limit_or_global_cooldown():
    send = APP[APP.index('def send_invite():'):APP.index('def is_quick_match_invite')]
    quick = APP[APP.index('def quick_match_invite():'):APP.index('@app.route("/api/invites/quick-match/')]
    respond = APP[APP.index('def respond_invite(invite_id):'):APP.index('@app.route', APP.index('def respond_invite(invite_id):') + 50)]
    assert 'daily_rank_block_message' not in send
    assert 'is_player_in_cooldown' not in send
    assert 'daily_rank_block_message' not in quick
    assert 'is_player_in_cooldown' not in quick
    assert 'cancel_invite_daily_limit' not in respond
    assert 'is_player_in_cooldown' not in respond


def test_invite_poll_watchdog_exists():
    assert 'lastPendingInvitePollAt' in BASE
    assert 'Date.now() - lastPendingInvitePollAt >= 15000' in BASE
