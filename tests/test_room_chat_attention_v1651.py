from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROOM = (ROOT / "templates" / "room_detail.html").read_text(encoding="utf-8")
STYLE = (ROOT / "static" / "style.css").read_text(encoding="utf-8")


def test_room_chat_is_open_by_default():
    assert 'id="bottomRoomChat" class="bottom-lobby-chat bottom-room-chat" data-room-chat-panel' in ROOM
    assert 'id="bottomRoomChat" class="bottom-lobby-chat bottom-room-chat chat-collapsed" hidden' not in ROOM
    assert 'aria-expanded="true"' in ROOM


def test_room_chat_unread_badge_and_incoming_signal_exist():
    assert 'id="roomChatUnreadBadge"' in ROOM
    assert 'roomChatUnreadCount' in ROOM
    assert 'signalIncomingRoomChat' in ROOM
    assert 'String(msg.user_id || "") !== String(currentRoomChatUserId || "")' in ROOM
    assert 'room-chat-message-new' in ROOM
    assert 'room-chat-new-chip' in ROOM


def test_room_chat_attention_styles_exist():
    assert '.room-chat-unread-badge' in STYLE
    assert '.room-chat-floating-toggle.has-unread' in STYLE
    assert '.bottom-chat-message.room-chat-message-new' in STYLE
    assert '@keyframes roomChatTogglePulse' in STYLE
