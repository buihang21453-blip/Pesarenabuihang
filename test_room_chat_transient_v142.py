from pathlib import Path

ROOT = Path(__file__).parent
APP = (ROOT / 'app.py').read_text(encoding='utf-8')
ROOM = (ROOT / 'templates/room_detail.html').read_text(encoding='utf-8')
CSS = (ROOT / 'static/style.css').read_text(encoding='utf-8')


def test_version_and_transient_room_chat_store():
    assert 'APP_VERSION = "V1.4.25"' in APP
    assert 'ROOM_CHAT_MEMORY_TTL_SECONDS' in APP
    assert '_room_chat_memory = {}' in APP
    assert 'list_transient_room_chat_messages' in APP
    assert 'create_transient_room_chat_message' in APP


def test_room_chat_does_not_use_database_message_writer():
    route_block = APP[APP.index('def api_room_chat(room_id):'):APP.index('@app.route("/admin/announcement"')]
    assert 'list_chat_messages("room"' not in route_block
    assert 'create_chat_message(user["id"], message, scope="room"' not in route_block
    assert 'create_transient_room_chat_message' in route_block


def test_room_chat_uses_lobby_style_floating_panel():
    assert 'id="roomChatToggleButton"' in ROOM
    assert 'id="bottomRoomChat"' in ROOM
    assert 'bottom-lobby-chat bottom-room-chat' in ROOM
    assert 'Không lưu lịch sử' in ROOM
    assert 'function toggleRoomChat()' in ROOM
    assert '.room-chat-floating-toggle' in CSS
