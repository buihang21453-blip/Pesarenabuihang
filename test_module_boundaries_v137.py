from datetime import datetime, timezone, timedelta

from modules.presence.service import evaluate_presence
from modules.invites.service import send_invite_blocker, accept_invite_blocker


def parse_dt(value):
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value) if value else None


def solo(room, uid):
    return bool(room and str(room.get('host_user_id')) == str(uid) and room.get('status') == 'waiting_ready' and not room.get('guest_user_id'))


def test_presence_contract_online_and_timeout():
    now = datetime(2026, 8, 7, 6, 0, tzinfo=timezone.utc)
    live = {'is_online': True, 'last_seen_at': (now - timedelta(seconds=90)).isoformat()}
    stale = {'is_online': True, 'last_seen_at': (now - timedelta(seconds=121)).isoformat()}
    assert evaluate_presence(live, now=now, parse_datetime=parse_dt, timeout_seconds=120)['online'] is True
    state = evaluate_presence(stale, now=now, parse_datetime=parse_dt, timeout_seconds=120)
    assert state['online'] is False
    assert state['reason'] == 'heartbeat_timeout'


def test_invite_send_contract():
    state = {'match_a': None, 'match_b': None, 'room_a': None, 'room_b': None, 'pair_pending': False}
    assert send_invite_blocker(state, sender_id='a', receiver_id='b', receiver_online=True, is_solo_waiting_room=solo) is None
    assert send_invite_blocker(state, sender_id='a', receiver_id='b', receiver_online=False, is_solo_waiting_room=solo) == 'receiver_offline'
    state['pair_pending'] = True
    assert send_invite_blocker(state, sender_id='a', receiver_id='b', receiver_online=True, is_solo_waiting_room=solo) == 'pair_pending'


def test_invite_accept_contract():
    assert accept_invite_blocker(receiver_match=None, receiver_room=None, receiver_id='b', inviter_match=None, inviter_room=None, inviter_id='a', is_solo_waiting_room=solo) is None
    busy = {'host_user_id': 'b', 'guest_user_id': 'c', 'status': 'waiting_ready'}
    assert accept_invite_blocker(receiver_match=None, receiver_room=busy, receiver_id='b', inviter_match=None, inviter_room=None, inviter_id='a', is_solo_waiting_room=solo) == 'receiver_room_busy'
