"""State machine dùng chung cho toàn bộ luồng phòng đấu V1.2.10.

Mục tiêu: một nguồn quy tắc duy nhất cho Front-end/route/backend.
Không thay schema DB; chỉ chuẩn hóa điều kiện hành động và chuyển trạng thái.
"""

_CONTEXT = {}

def configure(context):
    _CONTEXT.clear()
    _CONTEXT.update(context)
    globals().update(context)

EXPORTED_NAMES = [
    "ROOM_FLOW_TRANSITIONS", "ROOM_ACTION_STATES", "room_flow_stage",
    "room_action_allowed", "room_action_block_message", "require_room_action",
    "room_transition_allowed", "describe_room_flow",
]

ROOM_FLOW_TRANSITIONS = {
    "waiting_ready": {"playing", "friendly_playing", "cancelled"},
    "playing": {"waiting_result_confirm", "cancelled"},
    "friendly_playing": {"waiting_ready", "cancelled"},
    "waiting_result_confirm": {"confirmed", "cancelled"},
    "confirmed": {"waiting_ready", "cancelled"},
    "cancelled": set(),
}

ROOM_ACTION_STATES = {
    "join": {"waiting_ready"},
    "ready": {"waiting_ready"},
    "unready": {"waiting_ready"},
    "select_mode": {"waiting_ready"},
    "random_team": {"waiting_ready"},
    "start": {"waiting_ready"},
    "submit_result": {"playing"},
    "confirm_result": {"waiting_result_confirm"},
    "dispute_result": {"waiting_result_confirm"},
    "rematch": {"confirmed"},
    "rematch_decline": {"confirmed"},
    "finish_friendly": {"friendly_playing"},
}

def room_flow_stage(room):
    status = (room or {}).get("status") or "unknown"
    return {
        "waiting_ready": "CHUAN_BI",
        "playing": "DANG_THI_DAU",
        "friendly_playing": "GIAO_HUU_DANG_THI_DAU",
        "waiting_result_confirm": "CHO_XAC_NHAN_KET_QUA",
        "confirmed": "DA_XAC_NHAN_CHO_QUYET_DINH",
        "cancelled": "DA_DONG",
    }.get(status, "KHONG_XAC_DINH")

def room_action_allowed(room, action):
    allowed = ROOM_ACTION_STATES.get(action)
    return True if allowed is None else (room or {}).get("status") in allowed

def room_action_block_message(room, action):
    status = (room or {}).get("status") or "không xác định"
    labels = {
        "join":"tham gia phòng", "ready":"Sẵn sàng", "unready":"Hủy sẵn sàng",
        "select_mode":"đổi chế độ", "random_team":"quay/chọn CLB", "start":"bắt đầu trận",
        "submit_result":"gửi kết quả", "confirm_result":"xác nhận kết quả",
        "dispute_result":"báo tranh chấp", "rematch":"Đá tiếp",
        "rematch_decline":"từ chối Đá tiếp", "finish_friendly":"kết thúc giao hữu",
    }
    return f"Không thể {labels.get(action, action)} khi phòng đang ở trạng thái {status}."

def require_room_action(room, action):
    if room_action_allowed(room, action):
        return True, ""
    return False, room_action_block_message(room, action)

def room_transition_allowed(current_status, target_status):
    if current_status == target_status:
        return True
    return target_status in ROOM_FLOW_TRANSITIONS.get(current_status, set())

def describe_room_flow():
    return [
        "waiting_ready", "playing", "waiting_result_confirm",
        "confirmed", "waiting_ready(rematch)",
    ]
