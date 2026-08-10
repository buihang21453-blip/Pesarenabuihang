# V1.2.18: Admin lazy-by-tab / Supabase payload reduction
"""Trang Admin tối ưu: chỉ tải dữ liệu nặng khi mở đúng tab."""


def register_routes(context):
    globals().update(context)

    @app.route("/admin")
    @login_required
    @admin_required
    def admin():
        def safe(label, loader, default):
            try:
                value = loader()
                return default if value is None else value
            except Exception as exc:
                app.logger.exception("Admin load failed [%s]: %s", label, exc)
                return default

        allowed_tabs = {
            "overview", "users", "passwords", "rooms", "matches", "match-report",
            "test-data", "system", "room-ui", "rp-tools", "economy", "logs",
        }
        active_tab = str(request.args.get("tab") or "overview").strip().lower()
        if active_tab not in allowed_tabs:
            active_tab = "overview"
        try:
            admin_page = max(1, int(request.args.get("page") or 1))
        except (TypeError, ValueError):
            admin_page = 1
        admin_page_size = 50

        # Mặc định nhẹ để template luôn render được dù tab chưa tải dữ liệu.
        admin_users = []
        players = []
        admins = []
        pending_users = []
        all_matches = []
        disputed_matches = []
        playing_matches = []
        all_rooms = []
        invites = []
        password_reset_requests = []
        pending_disputes = []
        audit_logs = []
        duplicate_ip_groups = []
        duplicate_ip_user_count = 0
        ip_device_status = {"ok": None, "row_count": 0, "error": None, "source": "not_loaded", "account_ip_count": 0, "duplicate_group_count": 0}
        active_announcement = None

        report_range_labels = {
            "today": "Hôm nay", "yesterday": "Hôm qua", "3days": "3 ngày gần đây",
            "7days": "1 tuần", "30days": "1 tháng", "all": "Toàn thời gian",
        }
        report_range = str(request.args.get("match_report_range") or "today").strip().lower()
        if report_range not in report_range_labels:
            report_range = "today"
        match_report = {
            "range": report_range, "range_label": report_range_labels[report_range],
            "range_labels": report_range_labels, "total": 0, "confirmed": 0,
            "playing": 0, "waiting": 0, "disputed": 0, "cancelled": 0,
            "unique_players": 0, "confirmed_goals": 0, "positive_rp": 0,
            "rank_random": 0, "random3_pick1": 0, "rank_random_percent": 0,
            "random3_pick1_percent": 0, "popular_mode": "Chưa tải dữ liệu",
        }
        match_report_daily = []

        # OVERVIEW: payload nhẹ, không đọc user_devices, audit log hay toàn bộ matches.
        if active_tab == "overview":
            overview_users = safe("overview_users", lambda: list_admin_overview_users(limit=300), [])
            players = [u for u in overview_users if u.get("role") == "player"]
            admins = [u for u in overview_users if is_admin_user(u)]
            pending_users = [u for u in players if u.get("account_status") == "pending"]
            all_rooms = safe("overview_rooms", lambda: list_rooms(limit=50, enrich=False), [])
            playing_matches = [r for r in all_rooms if r.get("status") in {"playing", "friendly_playing"}]
            invites = safe("overview_invites", lambda: list_invites("pending", limit=30, enrich=False), [])
            password_reset_requests = safe("overview_passwords", lambda: list_password_reset_requests("pending", limit=20), [])
            active_announcement = safe("overview_announcement", get_active_announcement, None)

        # USERS: chỉ lúc bấm tab mới đọc user_devices và dựng nhóm IP trùng.
        elif active_tab == "users":
            raw_users = safe("users", lambda: list_all_users(limit=admin_page_size, offset=(admin_page - 1) * admin_page_size), [])
            admin_users = safe("decorate_users", lambda: decorate_admin_users(raw_users), [])
            admin_users.sort(key=lambda item: (
                0 if item.get("duplicate_ips") else 1,
                (item.get("duplicate_ips") or [item.get("latest_ip") or "~"])[0],
                (item.get("username") or "").lower(),
            ))
            players = [u for u in admin_users if u.get("role") == "player"]
            admins = [u for u in admin_users if is_admin_user(u)]
            pending_users = [u for u in players if u.get("account_status") == "pending"]
            duplicate_ip_groups = safe("duplicate_ips", lambda: build_duplicate_ip_groups(admin_users), [])
            duplicate_ip_user_count = len({
                str(account.get("id"))
                for group in duplicate_ip_groups
                for account in group.get("accounts", []) if account.get("id")
            })
            ip_device_status = dict(getattr(list_user_devices, "last_status", {}) or {})
            ip_device_status.setdefault("ok", None)
            ip_device_status.setdefault("row_count", 0)
            ip_device_status["account_ip_count"] = sum(1 for user in admin_users if user.get("known_ips"))
            ip_device_status["duplicate_group_count"] = len(duplicate_ip_groups)

        elif active_tab == "passwords":
            password_reset_requests = safe("password_resets", lambda: list_password_reset_requests("pending", limit=80), [])

        elif active_tab == "rooms":
            all_rooms = safe("rooms", lambda: list_rooms(limit=80), [])
            # Dọn duplicate chỉ ở tab Phòng; không bắt /admin mặc định phải làm việc bảo trì dữ liệu.
            participant_ids = {
                str(value) for room in all_rooms
                for value in (room.get("host_user_id"), room.get("guest_user_id")) if value
            }
            cleanup_count = 0
            for participant_id in participant_ids:
                cleanup_count += safe(
                    f"cleanup_duplicate_rooms:{participant_id}",
                    lambda uid=participant_id: cleanup_duplicate_waiting_rooms(uid), 0,
                )
            if cleanup_count:
                all_rooms = safe("rooms_after_cleanup", lambda: list_rooms(limit=80), [])
            invites = safe("invites", lambda: list_invites("pending", limit=80), [])

        elif active_tab == "matches":
            all_matches = safe("matches", lambda: list_matches(limit=admin_page_size, offset=(admin_page - 1) * admin_page_size), [])
            disputed_matches = safe("matches_disputed", lambda: list_matches(status="disputed", limit=50), [])
            playing_matches = safe("matches_playing", lambda: list_matches(status="playing", limit=50), [])
            raw_disputes = safe("match_disputes", lambda: list_match_disputes("pending"), [])
            for item in raw_disputes:
                try:
                    pending_disputes.append(decorate_match_dispute(item, all_matches))
                except Exception as exc:
                    app.logger.exception("Admin dispute decoration failed: %s", exc)

        elif active_tab == "match-report":
            payload = safe("match_report_read_model", lambda: load_match_report(report_range), None)
            if payload:
                match_report, match_report_daily = payload
            else:
                # Fallback chỉ chạy khi người dùng thực sự mở Báo cáo.
                from datetime import datetime, timedelta, timezone
                report_matches = safe("report_matches_fallback", lambda: list_matches(limit=500), [])
                vn_tz = timezone(timedelta(hours=7))
                today_vn = datetime.now(vn_tz).date()
                ranges = {
                    "today": (today_vn, today_vn),
                    "yesterday": (today_vn - timedelta(days=1), today_vn - timedelta(days=1)),
                    "3days": (today_vn - timedelta(days=2), today_vn),
                    "7days": (today_vn - timedelta(days=6), today_vn),
                    "30days": (today_vn - timedelta(days=29), today_vn),
                    "all": (None, None),
                }
                start_date, end_date = ranges[report_range]
                filtered = []
                for m in report_matches:
                    try:
                        raw = str(m.get("created_at") or "").replace("Z", "+00:00")
                        dt = datetime.fromisoformat(raw)
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=timezone.utc)
                        day = dt.astimezone(vn_tz).date()
                    except Exception:
                        continue
                    if start_date and not (start_date <= day <= end_date):
                        continue
                    row = dict(m); row["_day"] = day; filtered.append(row)
                status_counts = {}
                unique_players = set(); goals = 0; positive_rp = 0
                mode_counts = {"rank_random": 0, "random3_pick1": 0}
                daily = {}
                for m in filtered:
                    status = str(m.get("status") or "").lower()
                    status_counts[status] = status_counts.get(status, 0) + 1
                    for key in ("player1_id", "player2_id"):
                        if m.get(key): unique_players.add(str(m.get(key)))
                    if status == "confirmed":
                        goals += int(m.get("score1") or 0) + int(m.get("score2") or 0)
                        positive_rp += max(0, int(m.get("delta1") or 0)) + max(0, int(m.get("delta2") or 0))
                    details = m.get("rp_details") if isinstance(m.get("rp_details"), dict) else {}
                    mode = "random3_pick1" if str(details.get("match_mode") or "").lower() == "random3_pick1" or "random3_pick1" in str(m.get("note") or "").lower() else "rank_random"
                    mode_counts[mode] += 1
                    bucket = daily.setdefault(m["_day"], {"date": m["_day"], "total": 0, "confirmed": 0, "playing": 0, "waiting": 0, "disputed": 0, "cancelled": 0, "rank_random": 0, "random3_pick1": 0, "players": set()})
                    bucket["total"] += 1; bucket[mode] += 1
                    if status == "confirmed": bucket["confirmed"] += 1
                    elif status == "playing": bucket["playing"] += 1
                    elif status in {"waiting_confirm", "waiting_result_confirm"}: bucket["waiting"] += 1
                    elif status == "disputed": bucket["disputed"] += 1
                    elif status == "cancelled": bucket["cancelled"] += 1
                    for key in ("player1_id", "player2_id"):
                        if m.get(key): bucket["players"].add(str(m.get(key)))
                total = len(filtered)
                match_report.update({
                    "total": total, "confirmed": status_counts.get("confirmed", 0),
                    "playing": status_counts.get("playing", 0),
                    "waiting": status_counts.get("waiting_confirm", 0) + status_counts.get("waiting_result_confirm", 0),
                    "disputed": status_counts.get("disputed", 0), "cancelled": status_counts.get("cancelled", 0),
                    "unique_players": len(unique_players), "confirmed_goals": goals, "positive_rp": positive_rp,
                    "rank_random": mode_counts["rank_random"], "random3_pick1": mode_counts["random3_pick1"],
                    "rank_random_percent": round(mode_counts["rank_random"] * 100 / total, 1) if total else 0,
                    "random3_pick1_percent": round(mode_counts["random3_pick1"] * 100 / total, 1) if total else 0,
                    "popular_mode": "Random 3 chọn 1" if mode_counts["random3_pick1"] > mode_counts["rank_random"] else "Rank Random" if mode_counts["rank_random"] > mode_counts["random3_pick1"] else "Hai chế độ ngang nhau",
                })
                for day in sorted(daily, reverse=True):
                    bucket = daily[day]
                    bucket["player_count"] = len(bucket.pop("players")); bucket["date_label"] = day.strftime("%d/%m/%Y")
                    match_report_daily.append(bucket)

        elif active_tab in {"system", "test-data", "rp-tools"}:
            # Những form có dropdown người chơi chỉ cần danh sách user, không cần IP/cosmetic.
            raw_users = safe("admin_form_users", lambda: list_all_users(limit=200), [])
            players = [u for u in raw_users if u.get("role") == "player"]
            admins = [u for u in raw_users if is_admin_user(u)]
            if active_tab == "system":
                active_announcement = safe("system_announcement", get_active_announcement, None)

        elif active_tab == "logs" and is_owner_user(current_user()):
            audit_logs = safe("audit_logs", lambda: list_admin_activity_logs(limit=100), [])

        rooms_active = [r for r in all_rooms if r.get("status") in ["waiting_ready", "playing", "friendly_playing", "waiting_result_confirm", "waiting_confirm", "disputed"]]
        recent_closed_rooms = [
            r for r in all_rooms if r.get("status") == "cancelled" and (
                "đóng trình duyệt" in str(r.get("note") or "").casefold()
                or "host_browser_offline" in str(r.get("note") or "").casefold()
                or "chủ phòng" in str(r.get("note") or "").casefold()
            )
        ][:30]

        return render_template(
            "admin.html",
            admin_active_tab=active_tab, admin_page=admin_page, admin_page_size=admin_page_size,
            admin_users=admin_users, players=players, admins=admins, pending_users=pending_users,
            all_matches=all_matches[:50], disputed=disputed_matches, playing=playing_matches,
            rooms=rooms_active, recent_closed_rooms=recent_closed_rooms, all_rooms=all_rooms[:80],
            invites=invites, active_announcement=active_announcement,
            password_reset_requests=password_reset_requests, audit_logs=audit_logs,
            duplicate_ip_groups=duplicate_ip_groups, duplicate_ip_user_count=duplicate_ip_user_count,
            ip_device_status=ip_device_status, pending_disputes=pending_disputes,
            can_create_test_account=has_admin_permission(current_user(), "users_edit"),
            can_import_accounts_csv=has_admin_permission(current_user(), "accounts_import"),
            admin_permission_groups=ADMIN_PERMISSION_GROUPS,
            admin_permission_labels=ADMIN_PERMISSION_LABELS,
            current_admin_permissions=_admin_permissions(current_user()),
            system_features=safe("system_features", get_system_features, dict(SYSTEM_FEATURE_DEFAULTS)) if active_tab == "system" else dict(SYSTEM_FEATURE_DEFAULTS),
            maintenance_config=safe("maintenance_config", get_maintenance_config, _maintenance_default_config()) if active_tab == "system" else _maintenance_default_config(),
            maintenance_status=safe("maintenance_status", get_maintenance_status, {"closed": False, "countdown": None}) if active_tab == "system" else {"closed": False, "countdown": None},
            match_report=match_report, match_report_daily=match_report_daily,
        )
