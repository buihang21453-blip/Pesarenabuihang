"""Route extracted from app.py without changing endpoint behavior.

Dependencies are injected from the application context at registration time to
avoid circular imports and preserve the existing business logic.
"""

def register_routes(context):
    globals().update(context)

    @app.route("/chat")
    @login_required
    def lobby_chat():
        if not system_feature_enabled("lobby_chat_enabled"):
            return redirect(url_for("dashboard"))
        return render_template("chat.html", messages=list_chat_messages("global", limit=20))

    @app.route("/chat/send", methods=["POST"])
    @login_required
    def send_global_chat():
        user = current_user()
        message = request.form.get("message", "")

        ok, error = create_chat_message(user["id"], message, scope="global")
        if not ok:
            flash(error, "warning")
        else:
            flash("Đã gửi tin nhắn.", "success")

        return redirect(url_for("lobby_chat"))

    @app.route("/api/chat/global")
    @login_required
    def api_global_chat():
        if not system_feature_enabled("lobby_chat_enabled"):
            return polling_stop_response("lobby_chat_disabled")
        messages = list_chat_messages("global", limit=20)
        return jsonify({"ok": True, "messages": messages})

    @app.route("/api/chat/global/status")
    @login_required
    def api_global_chat_status():
        if not system_feature_enabled("lobby_chat_enabled"):
            return polling_stop_response("lobby_chat_disabled")
        """Dữ liệu nhẹ để hiển thị số tin chat sảnh chưa đọc khi khung chat đang đóng."""
        user = current_user()
        limit = 100
        query = (
            db.table("chat_messages")
            .select("id,user_id,created_at")
            .eq("scope", "global")
            .is_("room_id", "null")
            .order("created_at", desc=True)
            .limit(limit)
        )
        result = execute_query(query, "api_global_chat_status")
        rows = list(reversed(result.data or []))

        messages = [
            {
                "id": row.get("id"),
                "created_at": row.get("created_at"),
                "is_own": row.get("user_id") == user.get("id"),
            }
            for row in rows
        ]

        return jsonify({
            "ok": True,
            "messages": messages,
            "latest_created_at": messages[-1]["created_at"] if messages else None,
            "limit_reached": len(messages) >= limit,
        })

    @app.route("/api/room/<room_id>/chat")
    @login_required
    def api_room_chat(room_id):
        if not system_feature_enabled("room_chat_enabled"):
            return polling_stop_response("room_chat_disabled")
        user = current_user()
        room = get_room(room_id)

        if not room:
            return polling_stop_response("room_not_found")

        if user["id"] not in [room["host_user_id"], room["guest_user_id"]] and not is_admin_user(user):
            return polling_stop_response("room_access_ended")

        messages = list_chat_messages("room", room_id=room_id, limit=30)
        return jsonify({"ok": True, "messages": messages, "persistent": True})

    @app.route("/room/<room_id>/chat/send", methods=["POST"])
    @login_required
    def send_room_chat(room_id):
        if not system_feature_enabled("room_chat_enabled"):
            flash("Chat phòng đang bị tắt.", "warning")
            return redirect(url_for("room_detail", room_id=room_id))
        user = current_user()
        room = get_room(room_id)

        if not room:
            flash("Không tìm thấy phòng.", "danger")
            return redirect(url_for("rooms"))

        if user["id"] not in [room["host_user_id"], room["guest_user_id"]] and not is_admin_user(user):
            flash("Bạn không thuộc phòng này.", "danger")
            return redirect(url_for("rooms"))

        message = request.form.get("message", "")
        ok, error = create_chat_message(user["id"], message, scope="room", room_id=room_id)

        if not ok:
            flash(error, "warning")

        return redirect(url_for("room_detail", room_id=room_id))

    @app.route("/api/room/<room_id>/chat/send", methods=["POST"])
    @login_required
    def api_send_room_chat(room_id):
        """Gửi chat phòng bằng AJAX, không redirect và không tải lại khung phòng."""
        if not system_feature_enabled("room_chat_enabled"):
            return jsonify({"ok": False, "disabled": True, "error": "Chat phòng đang bị tắt."})

        user = current_user()
        room = get_room(room_id)
        if not room:
            return polling_stop_response("room_not_found")
        if user["id"] not in [room["host_user_id"], room["guest_user_id"]] and not is_admin_user(user):
            return polling_stop_response("room_access_ended")

        payload = request.get_json(silent=True) or request.form
        message = payload.get("message", "")
        ok, error = create_chat_message(user["id"], message, scope="room", room_id=room_id)
        if not ok:
            return jsonify({"ok": False, "error": error}), 400
        # Trả luôn snapshot mới nhất để máy gửi render tức thì, không phải chờ poll kế tiếp.
        messages = list_chat_messages("room", room_id=room_id, limit=30)
        return jsonify({"ok": True, "messages": messages, "persistent": True})

    @app.route("/api/chat/global/send", methods=["POST"])
    @login_required
    def api_send_global_chat():
        if not system_feature_enabled("lobby_chat_enabled"):
            return jsonify({"ok": False, "disabled": True, "error": "Chat Sảnh đang bị tắt."})
        user = current_user()
        payload = request.get_json(silent=True) or {}
        message = payload.get("message", "")

        ok, error = create_chat_message(user["id"], message, scope="global")
        if not ok:
            return jsonify({"ok": False, "error": error}), 400

        return jsonify({"ok": True})

