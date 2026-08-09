from datetime import datetime, timezone, timedelta
from modules.presence.service import evaluate_presence
from modules.invites.service import send_invite_blocker, accept_invite_blocker

def parse(v): return v

def solo(room, uid):
    return bool(room and room.get("status") == "waiting_ready" and room.get("host_user_id") == uid and not room.get("guest_user_id"))

def test_presence_online_and_timeout():
    now=datetime.now(timezone.utc)
    assert evaluate_presence({"is_online":True,"last_seen_at":now-timedelta(seconds=20)}, now=now, parse_datetime=parse, timeout_seconds=60)["online"]
    assert not evaluate_presence({"is_online":True,"last_seen_at":now-timedelta(seconds=61)}, now=now, parse_datetime=parse, timeout_seconds=60)["online"]

def test_invite_sender_solo_room_allowed():
    state={"room_a":{"status":"waiting_ready","host_user_id":"a","guest_user_id":None}}
    assert send_invite_blocker(state,sender_id="a",receiver_id="b",receiver_online=True,is_solo_waiting_room=solo) is None

def test_invite_receiver_busy_blocked():
    state={"room_b":{"status":"playing","host_user_id":"b","guest_user_id":"c"}}
    assert send_invite_blocker(state,sender_id="a",receiver_id="b",receiver_online=True,is_solo_waiting_room=solo)=="receiver_room_busy"

def test_accept_invite_solo_receiver_allowed():
    assert accept_invite_blocker(receiver_match=None,receiver_room={"status":"waiting_ready","host_user_id":"b","guest_user_id":None},receiver_id="b",inviter_match=None,inviter_room=None,inviter_id="a",is_solo_waiting_room=solo) is None
