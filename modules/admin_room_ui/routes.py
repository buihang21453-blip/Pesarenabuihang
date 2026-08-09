"""Route Admin cho trình thiết kế giao diện phòng đấu."""
from . import service


def register_routes(context):
    globals().update(context)
    service.configure(context)

    # Xuất reader để các route/template đăng ký sau có thể dùng chung.
    context["get_room_ui_config"] = service.get_room_ui_config
    context["ROOM_UI_DEFAULTS"] = service.DEFAULTS
    context["ROOM_UI_FIELD_SPECS"] = service.FIELD_SPECS

    @app.context_processor
    def inject_room_ui_designer_context():
        endpoint = request.endpoint or ""
        if endpoint == "room_detail":
            return {"room_ui_config": service.get_room_ui_config()}
        if endpoint == "admin":
            return {
                "room_ui_config": service.get_room_ui_config(),
                "room_ui_field_specs": service.FIELD_SPECS,
            }
        return {}

    @app.route("/admin/room-ui/save", methods=["POST"])
    @login_required
    @admin_required
    @admin_permission_required("system_features_manage")
    def admin_room_ui_save():
        config = service.parse_form_config(request.form)
        service.save_room_ui_config(config)
        log_admin_action("Cập nhật thiết kế giao diện phòng", "system", details=config)
        flash("Đã lưu thiết kế giao diện phòng đấu.", "success")
        return redirect(url_for("admin") + "#room-ui")

    @app.route("/admin/room-ui/reset", methods=["POST"])
    @login_required
    @admin_required
    @admin_permission_required("system_features_manage")
    def admin_room_ui_reset():
        config = service.reset_room_ui_config()
        log_admin_action("Khôi phục thiết kế phòng mặc định", "system", details=config)
        flash("Đã khôi phục giao diện phòng đấu mặc định.", "success")
        return redirect(url_for("admin") + "#room-ui")
