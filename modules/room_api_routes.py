"""Route extracted from app.py without changing endpoint behavior.

Dependencies are injected from the application context at registration time to
avoid circular imports and preserve the existing business logic.
"""

def register_routes(context):
    globals().update(context)

    @app.route("/api/active-room")
    @login_required

    def api_active_room():
        user = current_user()

        if not user or user.get("role") == "admin":
            return jsonify({"ok": True, "has_room": False})

        try:
            room = active_room_for_user(user["id"])
        except Exception:
            return jsonify({"ok": False, "has_room": False, "error": "temporary_db_error"}), 503

        if not room:
            return jsonify({"ok": True, "has_room": False})

        is_host = room.get("host_user_id") == user["id"]
        is_guest = room.get("guest_user_id") == user["id"]
        has_opponent = bool(room.get("guest_user_id"))

        # Chỉ ép quay lại khi trận đã bắt đầu hoặc đang chờ xác nhận.
        # Phòng trống/chờ sẵn sàng vẫn cho phép người dùng xem các trang khác.
        must_finish_statuses = {"playing", "friendly_playing", "waiting_result_confirm"}
        auto_redirect = bool(room.get("status") in must_finish_statuses and has_opponent)

        return jsonify({
            "ok": True,
            "has_room": True,
            "room_id": room["id"],
            "room_url": url_for("room_detail", room_id=room["id"]),
            "status": room.get("status"),
            "is_host": is_host,
            "is_guest": is_guest,
            "has_opponent": has_opponent,
            "auto_redirect": auto_redirect,
        })

    @app.route("/api/room/<room_id>/state")
    @login_required

    def api_room_state(room_id):
        user = current_user()

        try:
            room = get_room(room_id)
        except Exception:
            return jsonify({"ok": False, "error": "temporary_db_error"}), 503

        if not room:
            return polling_stop_response("room_not_found")

        if close_room_if_host_browser_offline(room):
            return polling_stop_response("host_browser_offline")

        if user["id"] not in [room["host_user_id"], room["guest_user_id"]] and not is_admin_user(user):
            return polling_stop_response("room_access_ended")

        state_key = build_room_state_key(room)

        # V4.1: nếu trạng thái chưa đổi, trả response rỗng để giảm dữ liệu truyền.
        # Client vẫn giữ polling nhưng không phải nhận/phân tích JSON lặp lại.
        since_state_key = (request.args.get("since") or "").strip()
        if since_state_key and since_state_key == state_key:
            response = app.response_class(status=204)
            response.headers["Cache-Control"] = "no-store, max-age=0"
            response.headers["X-Room-State-Unchanged"] = "1"
            return response

        rematch_declined_by_me = (
            (user["id"] == room.get("host_user_id") and room.get("rematch_host_declined"))
            or (user["id"] == room.get("guest_user_id") and room.get("rematch_guest_declined"))
        )

        return jsonify({
            "ok": True,
            "state_key": state_key,
            "status": room.get("status"),
            "guest_user_id": str(room.get("guest_user_id") or ""),
            "has_guest": bool(room.get("guest_user_id")),
            "updated_at": str(room.get("updated_at") or ""),
            "rematch_declined": bool(room.get("rematch_declined")),
            "rematch_declined_by_me": bool(rematch_declined_by_me),
            "rematch_expired": bool(room.get("rematch_expired")),
            "timeout_seconds": int(room.get("timeout_seconds") or 0),
            "timeout_label": room.get("timeout_label") or "",
        })

