"""Route extracted from app.py without changing endpoint behavior.

Dependencies are injected from the application context at registration time to
avoid circular imports and preserve the existing business logic.
"""

def register_routes(context):
    globals().update(context)

    @app.route("/admin/announcement", methods=["POST"])
    @login_required
    @admin_required
    @admin_permission_required("announcements_manage")
    def admin_create_announcement():
        user = current_user()
        title = request.form.get("title", "THÔNG BÁO").strip() or "THÔNG BÁO"
        message = request.form.get("message", "").strip()

        if not message:
            flash("Nội dung thông báo không được để trống.", "danger")
            return redirect_admin("system")

        created = create_admin_announcement(
            title=title[:40],
            message=message[:220],
            admin_user_id=user.get("id"),
        )
        announcement_id = created.data[0].get("id") if created.data else None
        log_admin_action("Đăng thông báo", "announcement", announcement_id, title[:40], message[:220])

        flash("Đã đăng thông báo admin.", "success")
        return redirect_admin("system")

    @app.route("/admin/announcement/clear", methods=["POST"])
    @login_required
    @admin_required
    @admin_permission_required("announcements_manage")
    def admin_clear_announcement():
        db.table("admin_announcements").update({"is_active": False}).eq("is_active", True).execute()
        log_admin_action("Tắt thông báo", "announcement", details="Đã tắt toàn bộ thông báo đang hoạt động.")
        flash("Đã tắt thông báo admin.", "success")
        return redirect_admin("system")

    @app.route("/api/announcement/current")
    @login_required
    def api_current_announcement():
        events = get_active_global_streak_events()
        if events:
            announcements = []
            for event in events:
                kind = str(event.get("kind") or "milestone")
                announcements.append({
                    "id": f"streak:{event.get('id', 'event')}",
                    "title": event.get("title") or "DANH HIỆU CHUỖI THẮNG",
                    "message": event.get("subtitle") or "Một danh hiệu mới vừa được thiết lập!",
                    "created_at": event.get("published_at"),
                    "expires_at": event.get("expires_at"),
                    "announcement_type": "shutdown" if kind == "shutdown" else "win_streak",
                    "icon": "⚡" if kind == "shutdown" else "🏆",
                })
            return jsonify({"ok": True, "announcements": announcements, "announcement": announcements[0]})

        announcement = get_active_announcement()
        if not announcement:
            return jsonify({"ok": True, "announcements": [], "announcement": None})
        admin_item = {
            "id": announcement["id"],
            "title": announcement["title"],
            "message": announcement["message"],
            "created_at": announcement["created_at"],
            "announcement_type": "admin",
            "icon": "📢",
        }
        return jsonify({"ok": True, "announcements": [admin_item], "announcement": admin_item})

    @app.route("/api/admin/announcement/send", methods=["POST"])
    @login_required
    @admin_required
    @admin_permission_required("announcements_manage")
    def api_admin_send_announcement():
        if not system_feature_enabled("announcements_enabled"):
            return jsonify({"ok": False, "error": "Thông báo hệ thống đang bị tắt."}), 403
        user = current_user()
        payload = request.get_json(silent=True) or {}
        title = (payload.get("title") or "THÔNG BÁO").strip()[:40] or "THÔNG BÁO"
        message = (payload.get("message") or "").strip()[:220]

        if not message:
            return jsonify({"ok": False, "error": "Nội dung thông báo không được để trống."}), 400

        created = create_admin_announcement(
            title=title,
            message=message,
            admin_user_id=user.get("id"),
        )
        announcement_id = created.data[0].get("id") if created.data else None
        log_admin_action("Đăng thông báo", "announcement", announcement_id, title, message)

        return jsonify({"ok": True})

