"""Pure invite availability decisions.

Routes keep database writes/redirects; this module owns the business decision so
Frontend visibility and Backend validation can be checked against one contract.
"""


def send_invite_blocker(state, *, sender_id, receiver_id, receiver_online, is_solo_waiting_room):
    state = state or {}
    sender_room = state.get("room_a")
    receiver_room = state.get("room_b")

    if state.get("match_a"):
        return "sender_active_match"
    if sender_room and not is_solo_waiting_room(sender_room, sender_id):
        return "sender_room_busy"
    if state.get("match_b"):
        return "receiver_active_match"
    if receiver_room and not is_solo_waiting_room(receiver_room, receiver_id):
        return "receiver_room_busy"
    if not receiver_online:
        return "receiver_offline"
    if state.get("pair_pending"):
        return "pair_pending"
    return None


SEND_INVITE_MESSAGES = {
    "sender_active_match": ("Bạn đang có trận chưa hoàn tất nên chưa thể gửi lời mời.", "warning", "dashboard"),
    "sender_room_busy": ("Phòng của bạn đã có đủ 2 người hoặc đã bắt đầu. Bạn không thể gửi thêm lời mời.", "warning", "dashboard"),
    "receiver_active_match": ("Người chơi này đang thi đấu hoặc còn trận chưa hoàn tất.", "warning", "players"),
    "receiver_room_busy": ("Phòng của người chơi này đã có đủ 2 người hoặc đã bắt đầu.", "warning", "players"),
    "receiver_offline": ("Người chơi này vừa offline. Bạn hãy chọn một đối thủ đang online khác nhé.", "danger", "players"),
    "pair_pending": ("Hai người đang có lời mời chờ xử lý.", "warning", "players"),
}


def accept_invite_blocker(*, receiver_match, receiver_room, receiver_id, inviter_match, inviter_room, inviter_id, is_solo_waiting_room):
    if receiver_match:
        return "receiver_active_match"
    if receiver_room and not is_solo_waiting_room(receiver_room, receiver_id):
        return "receiver_room_busy"
    if inviter_match or (inviter_room and not is_solo_waiting_room(inviter_room, inviter_id)):
        return "inviter_unavailable"
    return None
