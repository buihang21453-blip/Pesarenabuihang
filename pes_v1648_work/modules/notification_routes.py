"""Route extracted from app.py without changing endpoint behavior.

Dependencies are injected from the application context at registration time to
avoid circular imports and preserve the existing business logic.
"""

def register_routes(context):
    globals().update(context)

    @app.route("/notifications")
    @login_required
    def notifications():
        user = current_user()
        unread_only = (request.args.get("filter") or "all") == "unread"
        notices, _ = list_user_notifications(
            user.get("id"), page=1, per_page=20, unread_only=unread_only
        )
        return render_template(
            "notifications.html",
            notifications=notices,
            page=1,
            has_next=False,
            notification_filter="unread" if unread_only else "all",
            notification_retention_days=7,
            notification_max_items=20,
        )

    @app.route("/notifications/read-all", methods=["POST"])
    @login_required
    def mark_all_notifications_read():
        user = current_user()
        execute_query(
            db.table("user_notifications").update({
                "is_read": True,
                "read_at": now_iso(),
            }).eq("user_id", user.get("id")).eq("is_read", False),
            "mark_all_notifications_read",
        )
        ttl_cache_delete(f"bell_notifications:{user.get('id')}")
        flash("Đã đánh dấu tất cả thông báo là đã đọc.", "success")
        return redirect(url_for("notifications"))

    @app.route("/notification/<notification_id>/read", methods=["POST"])
    @login_required
    def mark_notification_read(notification_id):
        user = current_user()
        execute_query(
            db.table("user_notifications").update({
                "is_read": True,
                "read_at": now_iso(),
            }).eq("id", notification_id).eq("user_id", user.get("id")),
            "mark_notification_read",
        )
        ttl_cache_delete(f"bell_notifications:{user.get('id')}")
        next_url = request.form.get("next_url", "").strip()
        if next_url.startswith("/") and not next_url.startswith("//"):
            return redirect(next_url)
        return redirect(request.referrer or url_for("dashboard"))

