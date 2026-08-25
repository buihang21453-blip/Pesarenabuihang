"""Route Hồ sơ cá nhân, giữ nguyên endpoint để tương thích toàn app."""

from . import repository
from . import service


def register_routes(context):
    globals().update(context)
    repository.configure(context)
    service.configure(context)

    @app.context_processor
    def inject_current_profile_equipment():
        user = current_user()
        if not user:
            return {"current_profile_equipment": {}}
        try:
            return {"current_profile_equipment": service.build_equipment_state(user)}
        except Exception as exc:
            app.logger.debug("Topbar equipment fallback user=%s: %s", user.get("id"), exc)
            return {"current_profile_equipment": {}}

    @app.route("/profile")
    @login_required
    def my_profile():
        return redirect(url_for("profile", user_id=current_user().get("id")))

    @app.route("/profile/avatar", methods=["POST"])
    @login_required
    def update_profile_avatar():
        user = current_user()
        avatar_file = request.files.get("avatar")
        new_path = None
        try:
            avatar_bytes = service.prepare_avatar_bytes(avatar_file)
            new_path, new_url = service.upload_avatar_to_storage(user.get("id"), avatar_bytes)
            old_path = user.get("avatar_path")
            repository.update_avatar_record(user.get("id"), new_url, new_path)
            session["avatar_url"] = new_url
            if old_path and old_path != new_path:
                service.remove_avatar_object(old_path)
            flash("Ảnh đại diện đã được cập nhật và sẽ hiển thị trên toàn app.", "success")
        except ValueError as exc:
            flash(str(exc), "danger")
        except Exception as exc:
            if new_path:
                service.remove_avatar_object(new_path)
            app.logger.exception("update_profile_avatar error: %s", exc)
            flash("Không thể cập nhật ảnh đại diện lúc này. Hãy kiểm tra đã chạy SQL V1.6.1 rồi thử lại.", "danger")
        return redirect(url_for("profile", user_id=user.get("id")))

    @app.route("/profile/avatar/delete", methods=["POST"])
    @login_required
    def delete_profile_avatar():
        user = current_user()
        old_path = user.get("avatar_path")
        try:
            repository.clear_avatar_record(user.get("id"))
            session["avatar_url"] = None
            service.remove_avatar_object(old_path)
            flash("Đã xóa ảnh đại diện. App sẽ dùng chữ cái mặc định.", "success")
        except Exception as exc:
            app.logger.exception("delete_profile_avatar error: %s", exc)
            flash("Không thể xóa ảnh đại diện lúc này.", "danger")
        return redirect(url_for("profile", user_id=user.get("id")))

    @app.route("/profile/display-name", methods=["POST"])
    @login_required
    def update_display_name():
        user = current_user()
        if not user:
            return redirect(url_for("login"))

        new_name = " ".join(request.form.get("display_name", "").strip().split())
        current_name = str(user.get("display_name") or "").strip()
        if len(new_name) < 2 or len(new_name) > 40:
            flash("Tên hiển thị phải có từ 2 đến 40 ký tự.", "danger")
            return redirect(url_for("profile", user_id=user.get("id")))
        if new_name.casefold() == current_name.casefold():
            flash("Tên hiển thị mới không khác tên hiện tại.", "warning")
            return redirect(url_for("profile", user_id=user.get("id")))

        duplicate = repository.find_display_name_duplicates(new_name)
        if any(row.get("id") != user.get("id") and str(row.get("display_name") or "").casefold() == new_name.casefold() for row in duplicate):
            flash("Tên hiển thị này đã được người khác sử dụng.", "danger")
            return redirect(url_for("profile", user_id=user.get("id")))

        # Từ V1.14.41.1, mọi lần đổi tên đều bắt buộc dùng 1 Vé đổi tên.
        ticket_count = repository.get_display_name_ticket_count(user.get("id"))
        if ticket_count <= 0:
            flash("Bạn cần có Vé đổi tên trong Kho đồ để đổi tên hiển thị.", "danger")
            return redirect(url_for("profile", user_id=user.get("id")))

        try:
            result = repository.update_display_name_with_entitlement(user.get("id"), new_name)
            if not result or not result.get("used_ticket"):
                raise RuntimeError("DISPLAY_NAME_TICKET_NOT_CONSUMED")
            session["display_name"] = new_name
            ttl_cache_delete(f"user:{user.get('id')}")
            cache_delete("_rz_current_user")
            cache_delete("_rz_players_all")
            cache_delete("_rz_users_map")
            flash("Đã đổi tên hiển thị và sử dụng 1 Vé đổi tên trong Kho đồ.", "success")
        except Exception as exc:
            lowered = str(exc).lower()
            app.logger.exception("update_display_name error: %s", exc)
            if "display_name_change_ticket_required" in lowered or "display_name_change_limit_reached" in lowered:
                flash("Bạn không còn Vé đổi tên trong Kho đồ.", "danger")
            elif "display_name_duplicate" in lowered:
                flash("Tên hiển thị này đã được người khác sử dụng.", "danger")
            elif "pgrst202" in lowered or "change_display_name_with_ticket" in lowered:
                flash("Hãy chạy SQL V1.14.41.1 để bật chế độ đổi tên chỉ bằng Vé.", "danger")
            else:
                flash("Không thể đổi tên lúc này. Hãy kiểm tra Vercel Logs.", "danger")
        return redirect(url_for("profile", user_id=user.get("id")))

    @app.route("/profile/<user_id>")
    @login_required
    def profile(user_id):
        viewer = current_user()
        if not can_view_player_identity(user_id, viewer):
            flash("Không tìm thấy player.", "danger")
            return redirect(url_for("players"))
        context_data = service.build_profile_context(user_id, viewer)
        if context_data is None:
            flash("Không tìm thấy player.", "danger")
            return redirect(url_for("players"))
        return render_template("profile.html", **context_data)
