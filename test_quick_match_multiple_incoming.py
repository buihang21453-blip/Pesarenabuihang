from pathlib import Path

APP_SOURCE = Path(__file__).with_name("app.py").read_text(encoding="utf-8")


def test_quick_match_does_not_treat_incoming_invite_as_busy():
    assert "outgoing_inviter_ids" in APP_SOURCE
    assert "oid in busy_match_ids or oid in outgoing_inviter_ids" in APP_SOURCE
    assert "invite_busy_ids" not in APP_SOURCE


def test_quick_match_sender_with_outgoing_invite_is_still_blocked():
    assert 'if str(user["id"]) in outgoing_inviter_ids:' in APP_SOURCE
    assert "Bạn đang chờ một đối thủ phản hồi lời mời đã gửi." in APP_SOURCE


def test_accept_flow_cancels_other_received_pending_invites():
    assert '.eq("to_user_id", user["id"]).eq("status", "pending").neq("id", invite_id)' in APP_SOURCE
