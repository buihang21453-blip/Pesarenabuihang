"""HTTP actions for ranked Series orchestration."""

def register_routes(context):
    globals().update(context)

    @app.route("/room/<room_id>/series/start-next-game", methods=["POST"])
    @login_required
    def room_series_start_next_game(room_id):
        user = current_user(); room = get_room(room_id)
        if not room:
            flash("Không tìm thấy phòng.", "danger"); return redirect(url_for("rooms"))
        if str(user.get("id")) != str(room.get("host_user_id")) and not is_admin_user(user):
            flash("Chỉ chủ phòng mới được bắt đầu trận con.", "danger"); return redirect(url_for("room_detail", room_id=room_id))
        try:
            result = prepare_next_series_game(room)
            if result.get("action") == "start_match": flash(f"Đã bắt đầu {result.get('label') or 'trận tiếp theo'}.", "success")
            elif result.get("action") == "choose": flash("Đã tạo 3 CLB cho mỗi bên. Hai người hãy khóa lựa chọn.", "success")
            else: flash("Đã mở bước Cấm/Chọn CLB.", "success")
        except ValueError as exc: flash(str(exc), "warning")
        return redirect(url_for("room_detail", room_id=room_id))

    @app.route("/room/<room_id>/series/tactical-pick", methods=["POST"])
    @login_required
    def room_series_tactical_pick(room_id):
        user = current_user(); room = get_room(room_id)
        if not room: flash("Không tìm thấy phòng.", "danger"); return redirect(url_for("rooms"))
        try:
            result = choose_tactical_club(room, user.get("id"), request.form.get("choice_index", -1))
            flash("Cả hai đã chọn xong. Trận con bắt đầu!" if result.get("started") else "Đã khóa CLB. Chờ đối thủ chọn.", "success")
        except (ValueError, TypeError) as exc: flash(str(exc), "warning")
        return redirect(url_for("room_detail", room_id=room_id))

    @app.route("/room/<room_id>/series/ban-pick", methods=["POST"])
    @login_required
    def room_series_ban_pick(room_id):
        user = current_user(); room = get_room(room_id)
        if not room: flash("Không tìm thấy phòng.", "danger"); return redirect(url_for("rooms"))
        try:
            result = ban_pick_action(room, user.get("id"), request.form.get("action"), request.form.get("club_name"))
            flash("Cả hai đã chọn xong. Trận con bắt đầu!" if result.get("started") else "Đã ghi nhận lựa chọn.", "success")
        except ValueError as exc: flash(str(exc), "warning")
        return redirect(url_for("room_detail", room_id=room_id))
