"""Admin routes for Room UI Designer."""
from . import service


def register_routes(context):
    globals().update(context)
    service.configure(context)

    # Make the reader available to later-registered modules (notably the Admin dashboard).
    context["get_room_ui_config"] = service.get_room_ui_config
    context["ROOM_UI_DEFAULTS"] = service.DEFAULTS
    context["ROOM_UI_FIELD_SPECS"] = service.FIELD_SPECS

    @app.context_processor
    def inject_room_ui_designer_context():
        # Room UI settings are presentation-only. Do not hit Supabase for every
        # gameplay POST/API/template render because that can interfere with the
        # result/confirm/rematch/mode-switch hot paths.
        if request.endpoint == "room_detail":
            return {"room_ui_config": service.get_room_ui_config()}
        return {}

    @app.route("/admin/room-ui/save", methods=["POST"])
    @login_required
    @admin_required
    @admin_permission_required("system_features_manage")
    def admin_room_ui_save():
        config = service.parse_form_config(request.form)
        service.save_room_ui_config(config)
        log_admin_action("Cập nhật Room UI Designer", "system", details=config)
        flash("Đã lưu cấu hình thiết kế phòng đấu.", "success")
        return redirect(url_for("admin", tab="room-ui") + "#room-ui")

    @app.route("/admin/room-ui/reset", methods=["POST"])
    @login_required
    @admin_required
    @admin_permission_required("system_features_manage")
    def admin_room_ui_reset():
        config = service.reset_room_ui_config()
        log_admin_action("Khôi phục Room UI Designer mặc định", "system", details=config)
        flash("Đã khôi phục cấu hình thiết kế phòng đấu mặc định.", "success")
        return redirect(url_for("admin", tab="room-ui") + "#room-ui")
