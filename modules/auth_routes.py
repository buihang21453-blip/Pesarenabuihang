"""Route extracted from app.py without changing endpoint behavior.

Dependencies are injected from the application context at registration time to
avoid circular imports and preserve the existing business logic.
"""

def register_routes(context):
    globals().update(context)

    @app.route("/")
    def index():
        # Trang chủ công khai luôn mở thẳng Bảng xếp hạng.
        # Người dùng chỉ được chuyển tới màn hình đăng nhập khi chủ động bấm Đăng nhập.
        return redirect(url_for("ranking"))

    @app.route("/admin-login", methods=["GET", "POST"])
    def admin_login():
        get_device_id()

        existing = current_user() if session.get("user_id") else None
        if existing and is_admin_user(existing):
            return redirect(url_for("admin"))

        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "").strip()
            try:
                user = get_user_by_username(username)
            except Exception as exc:
                app.logger.warning("Admin login database warning: %s", exc)
                flash("Máy chủ dữ liệu đang bận. Vui lòng thử lại sau vài giây.", "warning")
                return redirect(url_for("admin_login"))

            if not user or user.get("password_hash") != hash_password(password):
                flash("Sai tài khoản hoặc mật khẩu Admin.", "danger")
                return redirect(url_for("admin_login"))
            if user.get("account_status", "approved") != "approved" or not is_admin_user(user):
                flash("Tài khoản này không có quyền truy cập trang quản trị.", "danger")
                return redirect(url_for("admin_login"))

            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user.get("username", "")
            session["display_name"] = user.get("display_name", "")
            session["avatar_url"] = user.get("avatar_url")
            session["role"] = user.get("role", "player")
            session["account_status"] = user.get("account_status", "approved")
            session["admin_level"] = user.get("admin_level", "none")
            session["zcoin_balance"] = int(user.get("zcoin_balance") or 0)
            session["last_real_activity"] = int(time.time())
            session["last_activity_touch"] = int(time.time())
            execute_query(
                db.table("users").update({"is_online": True, "last_seen_at": now_iso()}).eq("id", user["id"]),
                "admin_login_mark_online",
                attempts=2,
            )
            return redirect(url_for("admin"))

        return render_template("admin_login.html", auth_only=True)

    @app.route("/login", methods=["GET", "POST"])
    def login():
        get_device_id()

        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "").strip()

            try:
                user = get_user_by_username(username)
            except Exception as exc:
                # A temporary Supabase/Vercel socket failure must not become a raw 500.
                print(f"Login database warning: {exc}")
                flash("Máy chủ dữ liệu đang bận. Vui lòng đăng nhập lại sau vài giây.", "warning")
                return redirect(url_for("login"))

            if not user or user["password_hash"] != hash_password(password):
                flash("Sai tên tài khoản hoặc mật khẩu.", "danger")
                return redirect(url_for("login"))

            status = user.get("account_status", "approved")
            if status != "approved":
                messages = {
                    "pending": (
                        "Tài khoản chưa thể duyệt tự động vì IP đăng ký bị trùng. Admin có thể kiểm duyệt tài khoản này."
                        if "Trùng IP" in str(user.get("rejection_reason") or "")
                        else "Tài khoản của bạn đang chờ Admin duyệt."
                    ),
                    "rejected": "Tài khoản của bạn đã bị từ chối.",
                    "banned": "Tài khoản của bạn đã bị khóa. Hãy liên hệ Admin.",
                    "deleted": "Tài khoản này đã được Admin xóa khỏi hệ thống.",
                }
                flash(messages.get(status, "Tài khoản chưa được phép đăng nhập."), "danger")
                return redirect(url_for("login"))

            ok, msg = link_device_to_user(user)
            if not ok:
                flash(msg, "danger")
                return redirect(url_for("login"))

            remember_account = request.form.get("remember_account") == "1"
            session.permanent = remember_account
            session["remember_account"] = remember_account
            session["user_id"] = user["id"]
            session["username"] = user.get("username", "")
            session["display_name"] = user.get("display_name", "")
            session["avatar_url"] = user.get("avatar_url")
            session["role"] = user.get("role", "player")
            session["account_status"] = status
            session["admin_level"] = user.get("admin_level", "none")
            session["zcoin_balance"] = int(user.get("zcoin_balance") or 0)
            session["last_real_activity"] = int(time.time())
            session["last_activity_touch"] = int(time.time())
            # Tính RP không hoạt động trước khi cập nhật last_seen_at của lần đăng nhập mới.
            try:
                process_inactivity_for_user(user)
            except Exception as exc:
                print(f"Login inactivity decay warning: {exc}")
            execute_query(
                db.table("users").update({"is_online": True, "last_seen_at": now_iso()}).eq("id", user["id"]),
                "login_mark_online",
            )

            if user.get("must_change_password"):
                flash("Đăng nhập bằng mật khẩu tạm thành công. Hãy tạo mật khẩu mới.", "warning")
                return redirect(url_for("change_password"))

            # Người mở link chia sẻ khi chưa đăng nhập sẽ được đưa trở lại đúng
            # phòng sau khi đăng nhập, thay vì bị rơi về Dashboard/BXH.
            pending_room_join_id = session.pop("pending_room_join_id", None)
            if pending_room_join_id:
                return redirect(url_for("room_join_shared", room_id=pending_room_join_id))

            return redirect(url_for(post_login_endpoint(get_system_features(), is_admin=is_admin_user(user))))

        return render_template("login.html")

    @app.route("/forgot-password", methods=["GET", "POST"])
    def forgot_password():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            zalo_phone = normalize_zalo_phone(request.form.get("zalo_phone", ""))
            user = get_user_by_username(username) if username else None

            if not username or not zalo_phone:
                flash("Vui lòng nhập đủ Tên tài khoản và SĐT Zalo đang dùng.", "danger")
                return redirect(url_for("forgot_password"))

            # SĐT Zalo chỉ được lưu làm thông tin liên hệ/lịch sử yêu cầu, KHÔNG dùng để xác minh.
            # Hệ thống hiện chưa có dữ liệu SĐT đã đăng ký đáng tin cậy cho các tài khoản cũ.
            if not user:
                flash("Không tìm thấy tài khoản này.", "danger")
                return redirect(url_for("forgot_password"))

            # Chống bấm liên tục: mỗi tài khoản tối đa 1 lần/phút.
            recent = execute_query(
                db.table("password_reset_requests")
                .select("id,created_at")
                .eq("user_id", user["id"])
                .order("created_at", desc=True)
                .limit(1),
                "forgot_password_recent_request",
            )
            if recent.data:
                last_at = parse_dt(recent.data[0].get("created_at"))
                if last_at and (now_dt() - last_at).total_seconds() < 60:
                    flash("Bạn vừa yêu cầu cấp lại mật khẩu. Vui lòng thử lại sau 1 phút.", "warning")
                    return redirect(url_for("forgot_password"))

            temporary_password = generate_temporary_password(6)
            requested_at = now_iso()
            request_row = execute_query(
                db.table("password_reset_requests").insert({
                    "user_id": user["id"],
                    "username_snapshot": user.get("username"),
                    "zalo_name_snapshot": user.get("zalo_name"),
                    "zalo_phone_snapshot": zalo_phone,
                    "status": "resolved",
                    "requested_ip": get_client_ip(),
                    "admin_note": "Hệ thống tự cấp mật khẩu tạm 6 ký tự.",
                    "resolved_at": requested_at,
                }),
                "forgot_password_log_request",
            )
            execute_query(
                db.table("users").update({
                    "password_hash": hash_password(temporary_password),
                    "must_change_password": True,
                    "password_changed_at": requested_at,
                }).eq("id", user["id"]),
                "forgot_password_issue_temporary_password",
            )

            response = make_response(render_template(
                "forgot_password.html",
                temporary_password=temporary_password,
                reset_username=user.get("username"),
                request_logged=bool(request_row.data),
            ))
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            return response

        return render_template("forgot_password.html")

    @app.route("/change-password", methods=["GET", "POST"])
    @login_required
    def change_password():
        user = current_user()
        if request.method == "POST":
            current_password = request.form.get("current_password", "").strip()
            new_password = request.form.get("new_password", "").strip()
            if user.get("password_hash") != hash_password(current_password):
                flash("Mật khẩu tạm hoặc mật khẩu hiện tại không đúng.", "danger")
                return redirect(url_for("change_password"))
            valid_password, password_error = validate_new_password(new_password)
            if not valid_password:
                flash(password_error, "danger")
                return redirect(url_for("change_password"))
            if hash_password(new_password) == user.get("password_hash"):
                flash("Mật khẩu mới phải khác mật khẩu tạm hoặc mật khẩu hiện tại.", "warning")
                return redirect(url_for("change_password"))

            changed_at = now_iso()
            execute_query(
                db.table("users").update({
                    "password_hash": hash_password(new_password),
                    "must_change_password": False,
                    "password_changed_at": changed_at,
                }).eq("id", user["id"]),
                "user_change_password",
            )
            try:
                execute_query(
                    db.table("password_reset_requests").update({
                        "status": "resolved",
                        "admin_note": "User đã tự đổi mật khẩu.",
                        "resolved_at": changed_at,
                    }).eq("user_id", user["id"]).eq("status", "pending"),
                    "close_password_reset_after_user_change",
                )
            except Exception as exc:
                print(f"close password reset warning: {exc}")
            flash("Đã đổi mật khẩu thành công.", "success")
            pending_room_join_id = session.pop("pending_room_join_id", None)
            if pending_room_join_id:
                return redirect(url_for("room_join_shared", room_id=pending_room_join_id))
            return redirect(url_for("profile", user_id=user["id"]) + "#account-controls")

        if not user.get("must_change_password"):
            return redirect(url_for("profile", user_id=user["id"]) + "#account-controls")
        return render_template("change_password.html", force_change=True, auth_only=True, minimum_password_length=minimum_password_length())

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if not system_feature_enabled("registration_codes_enabled"):
            flash("Tính năng đăng ký tài khoản đang tạm tắt.", "warning")
            return redirect(url_for("login"))
        get_device_id()

        if request.method == "POST":
            can_register, msg = device_can_register()
            if not can_register:
                flash(msg, "danger")
                return redirect(url_for("register"))

            username = request.form.get("username", "").strip()
            password = request.form.get("password", "").strip()
            zalo_name = request.form.get("zalo_name", "").strip()
            if not username or not password or not zalo_name:
                flash("Vui lòng nhập đủ Tên tài khoản, Mật khẩu và Tên Zalo.", "danger")
                return redirect(url_for("register"))

            if len(username) < 3 or len(username) > 30:
                flash("Tên tài khoản phải từ 3 đến 30 ký tự.", "danger")
                return redirect(url_for("register"))

            if len(password) < minimum_password_length():
                flash(f"Mật khẩu phải có ít nhất {minimum_password_length()} ký tự.", "danger")
                return redirect(url_for("register"))

            if len(zalo_name) < 2 or len(zalo_name) > 80:
                flash("Tên Zalo không hợp lệ.", "danger")
                return redirect(url_for("register"))
            if get_user_by_username(username):
                flash("Tên tài khoản đã tồn tại.", "danger")
                return redirect(url_for("register"))

            ip = get_client_ip()
            ua = request.headers.get("User-Agent", "")

            ip_conflicts = registration_ip_conflicts(ip)
            if ip_conflicts:
                # Không tiết lộ cơ chế kiểm tra IP ra giao diện công khai.
                flash("⚠️ PES Arena phát hiện bạn đã có tài khoản trên web rồi. Vui lòng không lập thêm tài khoản khác. Nếu quên mật khẩu hoặc tài khoản, vui lòng liên hệ Admin.", "warning")
                return redirect(url_for("register"))

            auto_approved = True
            account_status = "approved"

            payload = {
                "username": username,
                "password_hash": hash_password(password),
                "display_name": username,
                "zalo_name": zalo_name,
                "role": "player",
                "account_status": account_status,
                "invite_code_used": None,
                "rank_points": DEFAULT_POINTS,
                "register_ip": ip,
                "register_user_agent": ua,
                "rejection_reason": None,
            }
            if auto_approved:
                payload["approved_at"] = now_iso()

            created = execute_query(
                db.table("users").insert(payload),
                "register_user",
            )

            user = created.data[0]

            if auto_approved:
                # Chỉ ghi nhận thiết bị; không dùng thiết bị làm điều kiện duyệt.
                try:
                    link_device_to_user(user)
                except Exception as exc:
                    print(f"register device tracking warning: {exc}")
                flash("Đăng ký thành công. Tài khoản đã được duyệt tự động, bạn có thể đăng nhập ngay.", "success")
            else:
                flash("Không thể duyệt tự động vì IP đăng ký đã được sử dụng. Tài khoản đã chuyển sang chờ Admin kiểm duyệt.", "warning")
            return redirect(url_for("login"))

        return render_template("register.html")

    @app.route("/logout")
    @login_required
    def logout():
        user_id = session.get("user_id")
        if user_id:
            try:
                execute_query(
                    db.table("users").update({"is_online": False, "last_seen_at": now_iso()}).eq("id", user_id),
                    "logout_mark_offline",
                )
            except Exception as exc:
                print(f"logout warning: {exc}")
        session.clear()
        if request.args.get("reason") == "inactive":
            flash("Bạn đã được đăng xuất do không hoạt động trong 60 phút.", "warning")
        else:
            flash("Đã đăng xuất.", "success")
        return redirect(url_for("login"))

