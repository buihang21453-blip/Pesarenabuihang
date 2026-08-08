"""Xóa bằng chứng, phòng, trận và tài khoản theo thứ tự an toàn.

Module không khai báo route; dependency được liên kết khi app khởi động.
"""

EXPORTED_NAMES = ['remove_match_dispute_evidence', 'delete_room_safe', 'delete_match_safe', 'delete_player_safe']

def configure(context):
    """Liên kết module với dependency hiện tại của ứng dụng."""
    globals().update(context)


def remove_match_dispute_evidence(match_id):
    if not match_id or db is None:
        return
    try:
        result = execute_query(
            db.table("match_disputes").select("evidence_path").eq("match_id", match_id),
            "list_match_evidence_for_cleanup",
            attempts=2,
        )
        for row in result.data or []:
            remove_dispute_evidence_object(row.get("evidence_path"))
    except Exception as exc:
        print(f"remove_match_dispute_evidence warning: {exc}")


def delete_room_safe(room_id, *, reverse_result=True):
    room = get_room(room_id)
    if not room:
        return

    if room.get("match_id"):
        delete_match_safe(room.get("match_id"), reverse_result=reverse_result)

    db.table("chat_messages").delete().eq("room_id", room_id).execute()
    db.table("match_rooms").delete().eq("id", room_id).execute()


def delete_match_safe(match_id, *, reverse_result=True):
    match = get_match(match_id)
    if match and reverse_result:
        reverse_confirmed_match_result(match)

    remove_match_dispute_evidence(match_id)
    db.table("match_rooms").update({
        "status": "cancelled",
        "match_id": None,
        "note": "Admin đã xóa trận liên kết.",
        "updated_at": now_iso(),
    }).eq("match_id", match_id).execute()

    db.table("matches").delete().eq("id", match_id).execute()


def delete_player_safe(user_id):
    """Vô hiệu hóa tài khoản nhưng giữ nguyên hồ sơ thi đấu và RP lịch sử.

    Người chơi vẫn phải tồn tại trong bảng users để các khóa player1_id/player2_id
    của matches và các phòng đã hoàn tất tiếp tục tra được tên, avatar và dữ liệu cũ.
    Chỉ dữ liệu phiên hoạt động/lời mời chưa hoàn tất được dọn dẹp.
    """
    user = get_user(user_id)
    if not user:
        return False, "Không tìm thấy tài khoản."

    if is_admin_user(user):
        return False, "Không được xóa tài khoản admin chính."

    deleted_at = now_iso()

    # Chỉ giải phóng các phòng CHƯA tạo trận. Phòng/trận đã có match_id phải được
    # giữ nguyên để lịch sử, tỷ số và phép tính RP không thay đổi.
    for room in list_rooms():
        if user_id not in [room.get("host_user_id"), room.get("guest_user_id")]:
            continue
        if room.get("match_id"):
            continue

        if str(room.get("host_user_id")) == str(user_id):
            # Chủ tài khoản bị xóa: đóng phòng chờ, không đụng tới trận lịch sử.
            db.table("chat_messages").delete().eq("room_id", room.get("id")).execute()
            db.table("match_rooms").delete().eq("id", room.get("id")).execute()
        else:
            # Khách bị xóa: trả phòng về trạng thái chờ để chủ có thể mời người khác.
            db.table("match_rooms").update({
                "guest_user_id": None,
                "guest_ready": False,
                "guest_team": None,
                "guest_team_overall": None,
                "guest_team_logo_url": None,
                "guest_team_league": None,
                "invite_id": None,
                "status": "waiting_ready",
                "note": "Tài khoản khách đã bị vô hiệu hóa. Phòng đang chờ đối thủ mới.",
                "state_expires_at": None,
                "updated_at": deleted_at,
            }).eq("id", room.get("id")).execute()

    # Lời mời chưa hoàn tất không còn hiệu lực, nhưng không xóa lịch sử trận.
    for invite in list_invites():
        if user_id in [invite.get("from_user_id"), invite.get("to_user_id")]:
            try:
                db.table("match_invites").update({
                    "status": "cancelled",
                    "updated_at": deleted_at,
                }).eq("id", invite.get("id")).execute()
            except Exception:
                db.table("match_invites").delete().eq("id", invite.get("id")).execute()

    # Xóa dữ liệu đăng nhập/thiết bị đang hoạt động, nhưng giữ users và matches.
    db.table("user_devices").delete().eq("user_id", user_id).execute()
    tombstone_password = hash_password(f"deleted:{user_id}:{deleted_at}")
    execute_query(
        db.table("users").update({
            "account_status": "banned",
            "is_online": False,
            "password_hash": tombstone_password,
            "rejection_reason": "Tài khoản đã được Admin xóa mềm. Lịch sử thi đấu được giữ nguyên.",
            "last_seen_at": deleted_at,
        }).eq("id", user_id),
        "soft_delete_player_keep_history",
        attempts=2,
    )

    cache_delete("_rz_users_all")
    cache_delete("_rz_rooms_all")
    cache_delete("_rz_invites_all")
    cache_delete("_rz_matches_all")
    cache_delete("_rz_current_pending_invites")
    ttl_cache_delete("users_raw")
    ttl_cache_delete("rooms_raw")
    ttl_cache_delete("invites_raw")
    ttl_cache_delete("matches_raw")
    return True, ""
