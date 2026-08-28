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
    """Xóa thật tài khoản, chỉ giữ danh tính tối thiểu + lịch sử matches/BXH mùa cũ.

    V1.4.17 dùng RPC database để thao tác nguyên tử. RPC sẽ:
    1) chép danh tính cần thiết sang archived_player_identities;
    2) xóa dữ liệu phụ thuộc tài khoản và phòng/lời mời;
    3) giữ nguyên public.matches và rank_season_snapshots;
    4) xóa hẳn hàng public.users.
    """
    user = get_user(user_id)
    if not user:
        return False, "Không tìm thấy tài khoản."
    if is_admin_user(user):
        return False, "Không được xóa tài khoản Admin."

    # Hủy trạng thái tàng hình trước khi user biến mất để setting không giữ UUID rác.
    try:
        invisible_ids = get_invisible_player_ids(force=True)
        if str(user_id) in {str(x) for x in invisible_ids}:
            invisible_ids = {str(x) for x in invisible_ids if str(x) != str(user_id)}
            execute_query(
                db.table("system_settings").upsert({
                    "setting_key": INVISIBLE_PLAYERS_SETTING_KEY,
                    "setting_value": {"user_ids": sorted(invisible_ids)},
                    "updated_at": now_iso(),
                }, on_conflict="setting_key"),
                "hard_delete_remove_invisible_id", attempts=2,
            )
    except Exception as exc:
        print(f"hard delete invisible cleanup warning: {exc}")

    try:
        result = execute_query(
            db.rpc("hard_delete_player_keep_match_history", {"p_user_id": user_id}),
            "hard_delete_player_keep_match_history", attempts=1,
        )
        payload = (result.data or {}) if not isinstance(result.data, list) else ((result.data or [{}])[0])
        if isinstance(payload, dict) and payload.get("ok") is False:
            return False, str(payload.get("error") or "Không thể xóa tài khoản.")
    except Exception as exc:
        print(f"hard_delete_player_keep_match_history error: {type(exc).__name__}: {exc}")
        return False, "Không thể xóa tài khoản. Hãy chạy docs/update_hard_delete_account_v1_4_17.sql trong Supabase rồi thử lại."

    for key in ("_rz_users_all", "_rz_users_map", "_rz_archived_users_map", "_rz_players_all",
                "_rz_rooms_all", "_rz_invites_all", "_rz_matches_all", "_rz_current_pending_invites"):
        cache_delete(key)
    for key in ("users_raw", "players_raw", "rooms_raw", "invites_raw", "matches_raw", "invisible_player_ids"):
        ttl_cache_delete(key)
    return True, ""

