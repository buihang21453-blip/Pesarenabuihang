"""Route extracted from app.py without changing endpoint behavior.

Dependencies are injected from the application context at registration time to
avoid circular imports and preserve the existing business logic.
"""

def register_routes(context):
    globals().update(context)

    @app.route("/api/session/activity", methods=["POST"])
    @login_required
    def api_session_activity():
        """Gia hạn phiên chỉ khi trình duyệt báo có thao tác thật của người dùng."""
        now_ts = int(time.time())
        session["last_real_activity"] = now_ts
        session["last_activity_touch"] = now_ts
        session.modified = True
        return jsonify({"ok": True, "last_activity": now_ts})

    @app.route("/api/session/timeout-check")
    @login_required
    def api_session_timeout_check():
        """Kiểm tra timeout cho phiên thường; phiên remember 30 ngày không dùng idle-timeout."""
        if session.get("remember_account"):
            return jsonify({"ok": True, "protected": True, "remembered": True, "room_url": None})
        user = current_user()
        room = None
        try:
            if user:
                room = active_room_for_user(user.get("id"))
        except Exception as exc:
            print(f"timeout check room warning: {exc}")
        protected = room_blocks_idle_logout(room)
        return jsonify({
            "ok": True,
            "protected": protected,
            "room_url": url_for("room_detail", room_id=room.get("id")) if protected and room else None,
        })

    @app.route("/heartbeat", methods=["POST"])
    @login_required
    def heartbeat():
        mark_current_user_active()
        return jsonify({"ok": True})

    @app.route("/presence/offline", methods=["POST"])
    @login_required
    def presence_offline():
        # sendBeacon không cần phản hồi JSON lớn. Khi chỉ chuyển trang nội bộ,
        # before_request/heartbeat của trang mới sẽ đánh dấu online lại ngay.
        mark_current_user_offline()
        return ("", 204)

    @app.route("/api/online-count")
    @login_required
    def api_online_count():
        viewer = current_user()
        players = filter_players_for_viewer(list_players(include_admin=True), viewer)
        online_count = sum(1 for player in players if player.get("is_online"))
        return jsonify({"ok": True, "online_count": online_count})

