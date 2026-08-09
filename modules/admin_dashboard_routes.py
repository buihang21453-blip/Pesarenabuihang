# HOTFIX V1.14.39.1: legacy Zcoin context removed from /admin
"""Route trang tổng quan Admin và tải dữ liệu quản trị an toàn.

Module đăng ký route theo dependency của app.py để giữ nguyên endpoint và tránh import vòng.
"""

def register_routes(context):
    """Đăng ký nhóm route vào Flask app hiện tại."""
    globals().update(context)

    @app.route("/admin/rank-modes", methods=["POST"])
    @login_required
    @admin_required
    @admin_permission_required("system_features_manage")
    def admin_save_rank_modes():
        configs = get_rank_mode_configs()
        int_fields = ("min_rp", "min_matches", "max_rp_gap", "pool_size", "bans_per_player", "ban_seconds", "pick_seconds")
        rp_fields = ("win_2_0", "lose_0_2", "win_2_1", "lose_1_2", "forfeit_win", "forfeit_loss", "draw_1_1", "draw_all", "one_win_one_draw_win", "one_win_one_draw_loss", "win_both", "lose_both", "draw")
        for code, mode in configs.items():
            enabled_key = f"{code}__enabled"
            if enabled_key in request.form:
                mode["enabled"] = request.form.get(enabled_key) == "1"
            for field in int_fields:
                key = f"{code}__{field}"
                if key in request.form:
                    try: mode[field] = max(0, int(request.form.get(key) or 0))
                    except (TypeError, ValueError): pass
            rp = dict(mode.get("rp") or {})
            for field in rp_fields:
                key = f"{code}__rp__{field}"
                if key in request.form:
                    try: rp[field] = int(request.form.get(key) or 0)
                    except (TypeError, ValueError): pass
            mode["rp"] = rp
        # Guard cấu hình Cấm/Chọn: pool phải đủ cho toàn bộ lượt cấm + tối đa 3 trận,
        # mỗi trận cần 2 CLB mới vì CLB đã dùng không được dùng lại.
        ban_pick = configs.get("ban_pick_bo3") or {}
        bans_per_player = max(0, int(ban_pick.get("bans_per_player") or 3))
        minimum_pool = bans_per_player * 2 + 6
        ban_pick["pool_size"] = max(minimum_pool, int(ban_pick.get("pool_size") or minimum_pool))
        ban_pick["ban_seconds"] = max(5, int(ban_pick.get("ban_seconds") or 30))
        ban_pick["pick_seconds"] = max(5, int(ban_pick.get("pick_seconds") or 30))
        configs["ban_pick_bo3"] = ban_pick
        save_rank_mode_configs(configs)
        flash("Đã lưu cấu hình 6 chế độ Rank.", "success")
        return redirect(url_for("admin", tab="rank-modes") + "#rank-modes")

    @app.route("/admin/rank-modes/user-unlocks/<user_id>", methods=["POST"])
    @login_required
    @admin_required
    @admin_permission_required("users_edit")
    def admin_save_user_rank_mode_unlocks(user_id):
        user = get_user(user_id)
        if not user:
            flash("Không tìm thấy tài khoản.", "error")
            return redirect(url_for("admin", tab="rank-modes") + "#rank-modes")
        selected = [code for code in MODE_ORDER if request.form.get(f"mode__{code}") == "1"]
        actor = current_user() or {}
        save_user_rank_mode_unlocks(user_id, selected, actor.get("id"))
        display_name = user.get("display_name") or user.get("username") or user_id
        flash(f"Đã cập nhật quyền chế độ Rank cho {display_name}.", "success")
        return redirect(url_for("admin", tab="users") + "#users")

    @app.route("/admin")
    @login_required
    @admin_required
    def admin():
        admin_started_at = time.perf_counter()
        allowed_admin_tabs = {"overview", "users", "passwords", "rooms", "matches", "match-report", "rank-modes", "test-data", "system", "economy", "rp-tools", "logs", "blackbox", "room-ui"}
        active_admin_tab = str(request.args.get("tab") or "overview").strip().lower()
        if active_admin_tab not in allowed_admin_tabs:
            active_admin_tab = "overview"

        needs_rooms = active_admin_tab == "rooms"
        needs_matches = active_admin_tab == "matches"
        needs_users = active_admin_tab in {"overview", "users", "system"}
        needs_passwords = active_admin_tab in {"overview", "passwords"}
        needs_rank_modes = active_admin_tab in {"users", "rank-modes", "system"}

        # Trang Admin chứa nhiều khối dữ liệu độc lập. Một truy vấn phụ lỗi không được
        # làm sập toàn bộ trang; khối lỗi sẽ tạm trả danh sách rỗng và ghi log Vercel.
        def admin_safe_load(label, loader, default):
            try:
                value = loader()
                return default if value is None else value
            except Exception as exc:
                app.logger.exception("Admin load failed [%s]: %s", label, exc)
                return default

        all_rooms = admin_safe_load("rooms", list_rooms, []) if needs_rooms else []

        # Không thực hiện thao tác ghi/xóa dữ liệu trong request mở tab Admin.
        # Bản cũ quét từng người chơi rồi gọi cleanup_duplicate_waiting_rooms(),
        # tạo N+1 truy vấn Supabase và là nguyên nhân lớn khiến tab phản hồi rất chậm.

        all_matches = admin_safe_load("matches", list_matches, []) if needs_matches else []

        if active_admin_tab == "overview":
            # Tổng quan chỉ cần số lượng/trạng thái. Không enrich toàn bộ phòng,
            # không auto-confirm từng trận và không tải các cột lớn như rp_details.
            all_rooms = admin_safe_load(
                "overview_rooms",
                lambda: execute_query(
                    db.table("match_rooms").select("id,status,note").order("created_at", desc=True).limit(2000),
                    "admin_overview_rooms",
                    attempts=1,
                ).data or [],
                [],
            )
            all_matches = admin_safe_load(
                "overview_matches",
                lambda: execute_query(
                    db.table("matches").select("id,status").order("created_at", desc=True).limit(5000),
                    "admin_overview_matches",
                    attempts=1,
                ).data or [],
                [],
            )

        # V1.3.34: Báo cáo là READ MODEL. Khi click chỉ SELECT các bảng đã tổng hợp
        # trong Supabase; không đọc matches/rooms/series, không parse note/rp_details,
        # không for qua user x mode trong request giao diện.
        report_range = str(request.args.get("match_report_range") or "today").strip().lower()
        match_report = {
            "range": report_range,
            "range_label": "Hôm nay",
            "range_labels": {
                "today": "Hôm nay", "yesterday": "Hôm qua", "3days": "3 ngày gần đây",
                "7days": "1 tuần", "30days": "1 tháng", "all": "Toàn thời gian",
            },
            "total": 0, "confirmed": 0, "playing": 0, "waiting": 0,
            "disputed": 0, "cancelled": 0, "unique_players": 0,
            "confirmed_goals": 0, "positive_rp": 0, "mode_rows": [],
            "popular_mode": "Chưa có dữ liệu", "source": "empty",
        }
        match_report_daily = []
        report_matches = []
        if active_admin_tab == "match-report":
            cached_report = admin_safe_load(
                "match_report_read_model",
                lambda: load_match_report(report_range),
                None,
            )
            if cached_report:
                match_report, match_report_daily = cached_report
            else:
                # Không âm thầm quay lại cách cũ vì chính fallback đó làm tab treo hàng chục giây.
                # Admin sẽ thấy hướng dẫn chạy migration thay vì request quét toàn lịch sử.
                match_report["range"] = report_range if report_range in match_report["range_labels"] else "today"
                match_report["range_label"] = match_report["range_labels"].get(match_report["range"], "Hôm nay")
                match_report["source"] = "migration_required"
                app.logger.warning("ADMIN_READ_MODEL migration_required tab=match-report")

        raw_users = admin_safe_load("users", list_all_users, []) if needs_users else []
        admin_users = admin_safe_load(
            "decorate_users", lambda: decorate_admin_users(raw_users), []
        )

        # Ưu tiên nhóm IP trùng lên đầu và đặt các tài khoản cùng IP cạnh nhau.
        admin_users.sort(key=lambda item: (
            0 if item.get("duplicate_ips") else 1,
            (item.get("duplicate_ips") or [item.get("latest_ip") or "~"])[0],
            (item.get("username") or "").lower(),
        ))
        players = [u for u in admin_users if u.get("role") == "player"]
        admins = [u for u in admin_users if is_admin_user(u)]
        pending_users = [u for u in players if u.get("account_status") == "pending"]

        password_reset_requests = admin_safe_load(
            "password_resets", lambda: list_password_reset_requests("pending"), []
        ) if needs_passwords else []
        raw_disputes = admin_safe_load(
            "match_disputes", lambda: list_match_disputes("pending"), []
        ) if active_admin_tab in {"overview", "matches"} else []
        pending_disputes = []
        for item in raw_disputes:
            try:
                pending_disputes.append(decorate_match_dispute(item, all_matches))
            except Exception as exc:
                app.logger.exception("Admin dispute decoration failed: %s", exc)

        audit_logs = (
            admin_safe_load("audit_logs", list_admin_activity_logs, [])
            if active_admin_tab == "logs" and is_owner_user(current_user()) else []
        )
        blackbox_incidents = admin_safe_load("blackbox_incidents", lambda: blackbox_list_incidents(120), []) if active_admin_tab == "blackbox" else []
        blackbox_stats = blackbox_summary(blackbox_incidents) if active_admin_tab == "blackbox" else {"total": 0, "open": 0, "critical": 0, "error": 0, "warning": 0}
        blackbox_cfg = blackbox_config() if active_admin_tab == "blackbox" else {"enabled": False}
        duplicate_ip_groups = admin_safe_load(
            "duplicate_ips", lambda: build_duplicate_ip_groups(admin_users), []
        ) if active_admin_tab in {"overview", "users"} else []
        duplicate_ip_user_count = len({
            str(account.get("id"))
            for group in duplicate_ip_groups
            for account in group.get("accounts", [])
            if account.get("id")
        })
        ip_device_status = dict(getattr(list_user_devices, "last_status", {}) or {})
        ip_device_status.setdefault("ok", None)
        ip_device_status.setdefault("row_count", 0)
        ip_device_status["account_ip_count"] = sum(1 for user in admin_users if user.get("known_ips"))
        ip_device_status["duplicate_group_count"] = len(duplicate_ip_groups)

        rendered_admin = render_template(
            "admin.html",
            admin_users=admin_users,
            players=players,
            admins=admins,
            pending_users=pending_users,
            all_matches=all_matches[:80],
            disputed=[m for m in all_matches if m.get("status") == "disputed"],
            playing=[m for m in all_matches if m.get("status") == "playing"],
            rooms=[r for r in all_rooms if r.get("status") in ["waiting_ready", "playing", "friendly_playing", "waiting_result_confirm", "waiting_confirm", "disputed"]],
            recent_closed_rooms=[
                r for r in all_rooms
                if r.get("status") == "cancelled"
                and (
                    "đóng trình duyệt" in str(r.get("note") or "").casefold()
                    or "host_browser_offline" in str(r.get("note") or "").casefold()
                    or "chủ phòng" in str(r.get("note") or "").casefold()
                )
            ][:30],
            all_rooms=all_rooms[:80],
            invites=admin_safe_load("invites", lambda: list_invites("pending"), []) if active_admin_tab in {"overview", "rooms"} else [],
            active_announcement=admin_safe_load("announcement", get_active_announcement, None) if active_admin_tab in {"overview", "system"} else None,
            password_reset_requests=password_reset_requests,
            audit_logs=audit_logs,
            blackbox_incidents=blackbox_incidents,
            blackbox_summary=blackbox_stats,
            blackbox_config=blackbox_cfg,
            duplicate_ip_groups=duplicate_ip_groups,
            duplicate_ip_user_count=duplicate_ip_user_count,
            ip_device_status=ip_device_status,
            pending_disputes=pending_disputes,
            can_create_test_account=has_admin_permission(current_user(), "users_edit"),
            can_import_accounts_csv=has_admin_permission(current_user(), "accounts_import"),
            admin_permission_groups=ADMIN_PERMISSION_GROUPS,
            admin_permission_labels=ADMIN_PERMISSION_LABELS,
            current_admin_permissions=_admin_permissions(current_user()),
            system_features=admin_safe_load("system_features", get_system_features, dict(SYSTEM_FEATURE_DEFAULTS)) if active_admin_tab == "system" else dict(SYSTEM_FEATURE_DEFAULTS),
            maintenance_config=admin_safe_load("maintenance_config", get_maintenance_config, _maintenance_default_config()) if active_admin_tab == "system" else _maintenance_default_config(),
            maintenance_status=admin_safe_load("maintenance_status", get_maintenance_status, {"closed": False, "countdown": None}) if active_admin_tab == "system" else {"closed": False, "countdown": None},
            match_report=match_report,
            match_report_daily=match_report_daily,
            rank_mode_configs=admin_safe_load("rank_mode_configs", get_rank_mode_configs, {}) if needs_rank_modes else {},
            rank_mode_order=MODE_ORDER,
            rank_mode_user_unlocks=admin_safe_load("rank_mode_user_unlocks", list_rank_mode_user_unlocks, {}) if active_admin_tab == "users" else {},
            room_ui_config=admin_safe_load("room_ui_config", get_room_ui_config, dict(ROOM_UI_DEFAULTS)) if active_admin_tab == "room-ui" else dict(ROOM_UI_DEFAULTS),
            room_ui_defaults=dict(ROOM_UI_DEFAULTS),
            room_ui_field_specs=ROOM_UI_FIELD_SPECS,
            active_admin_tab=active_admin_tab,
        )
        app.logger.info(
            "ADMIN_PERF tab=%s range=%s duration_ms=%d rooms=%d matches=%d users=%d report_matches=%d",
            active_admin_tab,
            report_range,
            int((time.perf_counter() - admin_started_at) * 1000),
            len(all_rooms),
            len(all_matches),
            len(raw_users),
            len(report_matches),
        )
        return rendered_admin

