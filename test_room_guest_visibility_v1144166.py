from pathlib import Path

APP = Path("app.py").read_text(encoding="utf-8")
ROOM_TEMPLATE = Path("templates/room_detail.html").read_text(encoding="utf-8")


def test_version_is_66():
    assert 'APP_VERSION = "V1.4.12"' in APP


def test_room_state_key_tracks_participants():
    block = APP.split("def build_room_state_key(room):", 1)[1].split("def polling_stop_response", 1)[0]
    assert 'str(room.get("host_user_id"))' in block
    assert 'str(room.get("guest_user_id"))' in block


def test_room_client_refreshes_when_state_key_changes():
    assert 'if (data.state_key !== currentRoomStateKey)' in ROOM_TEMPLATE
    assert 'await refreshRoomView();' in ROOM_TEMPLATE
