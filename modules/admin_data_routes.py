"""Route Admin xóa trận, hủy/xóa phòng và xóa lời mời.

Module đăng ký route theo dependency của app.py để giữ nguyên endpoint và tránh import vòng.
"""

def register_routes(context):
    """Đăng ký nhóm route vào Flask app hiện tại."""
    globals().update(context)

    @app.route("/admin/match/<match_id>/delete", methods=["POST"])
    @login_required
    @admin_required
    @admin_permission_required("matches_delete")
    def admin_delete_match(match_id):
        """Giữ endpoint cũ nhưng khóa xóa trực tiếp để tránh làm lệch lịch sử."""
        flash(
            "Collap_V1.13.3a đã tắt xóa trực tiếp trận đấu. Admin chỉ được chuyển trạng thái sang Đã hủy.",
            "warning",
        )
        return redirect_admin("matches")


    @app.route("/admin/room/<room_id>/cancel", methods=["POST"])
    @login_required
    @admin_required
    @admin_permission_required("rooms_manage")
    def admin_cancel_room(room_id):
        """Giải phóng phòng an toàn; lỗi phụ không được trả Internal Server Error."""
        try:
            room = get_room(room_id)
            if not room:
                flash("Không tìm thấy phòng.", "danger")
                return redirect_admin("rooms")

            if room.get("status") == "cancelled":
                flash("Phòng này đã được hủy trước đó.", "warning")
                return redirect_admin("rooms")

            linked_match = None
            if room.get("match_id"):
                try:
                    linked_match = get_match(room.get("match_id"))
                except Exception as exc:
                    app.logger.warning("admin_cancel_room get_match failed room=%s: %s", room_id, exc)
            old_match_status = linked_match.get("status") if linked_match else None
            updated_at = now_iso()

            # Dùng execute_query để có retry ngắn và log đúng nhãn. Điều kiện status
            # giúp thao tác idempotent khi người dùng double-click hoặc Vercel retry.
            update_query = (
                db.table("match_rooms")
                .update({
                    "status": "cancelled",
                    "note": "Admin đã hủy phòng để giải phóng người chơi. Kết quả trận được xử lý độc lập.",
                    "state_expires_at": None,
                    "updated_at": updated_at,
                })
                .eq("id", room_id)
                .neq("status", "cancelled")
            )
            execute_query(update_query, "admin_cancel_room", attempts=2)

            # Lời mời là dữ liệu phụ. Nếu bảng/column lời mời lỗi, phòng vẫn phải
            # được giải phóng và Admin nhận thông báo cảnh báo thay vì trang 500.
            invite_warning = False
            if room.get("invite_id"):
                try:
                    execute_query(
                        db.table("match_invites").update({
                            "status": "cancelled",
                            "updated_at": updated_at,
                        }).eq("id", room.get("invite_id")),
                        "admin_cancel_room_invite",
                        attempts=2,
                    )
                except Exception as exc:
                    invite_warning = True
                    app.logger.exception("Cancel linked invite failed room=%s invite=%s: %s", room_id, room.get("invite_id"), exc)

            cache_delete("_rz_rooms_all")
            cache_delete("_rz_invites_all")
            cache_delete("_rz_current_pending_invites")
            ttl_cache_delete("rooms_raw")
            ttl_cache_delete("invites_raw")

            log_admin_action(
                "Hủy phòng", "room", room_id,
                details=(
                    f"Phòng cũ: {room.get('status')}; trận: {old_match_status or 'không có'}; "
                    "chỉ giải phóng phòng, không sửa trạng thái trận và không đổi RP"
                ),
            )
            if invite_warning:
                flash("Đã hủy phòng. Lời mời liên kết chưa cập nhật được nhưng người chơi đã được giải phóng.", "warning")
            else:
                flash("Đã hủy phòng. Kết quả trận vẫn được xử lý riêng và RP không bị mất.", "success")
            return redirect_admin("rooms")
        except Exception as exc:
            app.logger.exception("admin_cancel_room failed room=%s: %s", room_id, exc)
            flash("Không thể hủy phòng lúc này. Hệ thống đã ghi log lỗi; vui lòng thử lại sau vài giây.", "danger")
            return redirect_admin("rooms")


    @app.route("/admin/invite/<invite_id>/delete", methods=["POST"])
    @login_required
    @admin_required
    @admin_permission_required("invites_manage")
    def admin_delete_invite(invite_id):
        invite = get_invite(invite_id)
        if not invite:
            flash("Không tìm thấy lời mời.", "danger")
            return redirect_admin("rooms")

        db.table("match_invites").delete().eq("id", invite_id).execute()
        log_admin_action("Xóa lời mời", "invite", invite_id, details=f"{invite.get('from_name', '-')} → {invite.get('to_name', '-')}")
        flash("Đã xóa lời mời.", "success")
        return redirect_admin("rooms")

