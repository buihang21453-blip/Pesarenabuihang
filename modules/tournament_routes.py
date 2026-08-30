"""Independent Tournament module routes.

V1.4.25 introduces the first real Tournament database core:
- tournaments
- tournament_registrations
- tournament_members

Tournament data stays independent from Rank / Season / normal matches.
"""

TOURNAMENT_AREA_SETTING_KEY = "tournament_area_enabled"


def register_routes(context):
    globals().update(context)

    def tournament_area_enabled(force=False):
        request_key = "_tournament_area_enabled_cached"
        if not force:
            cached = cache_get(request_key)
            if isinstance(cached, bool):
                return cached
            cached = ttl_cache_get("tournament_area_enabled")
            if isinstance(cached, bool):
                return cache_set(request_key, cached)

        enabled = False
        try:
            result = execute_query(
                db.table("system_settings").select("setting_value")
                .eq("setting_key", TOURNAMENT_AREA_SETTING_KEY).limit(1),
                "get_tournament_area_enabled", attempts=2,
            )
            raw = ((result.data or [{}])[0]).get("setting_value")
            if isinstance(raw, dict):
                raw = raw.get("enabled")
            if isinstance(raw, str):
                raw = raw.strip().lower() in {"1", "true", "yes", "on", "enabled"}
            if isinstance(raw, bool):
                enabled = raw
        except Exception as exc:
            print(f"tournament_area_enabled warning: {exc}")

        ttl_cache_set("tournament_area_enabled", enabled, 45)
        return cache_set(request_key, enabled)

    def _safe_rows(query, label):
        try:
            result = execute_query(query, label, attempts=2)
            return [dict(row) for row in (result.data or [])], None
        except Exception as exc:
            app.logger.warning("Tournament DB unavailable [%s]: %s", label, exc)
            return [], str(exc)

    def _list_tournaments():
        rows, error = _safe_rows(
            db.table("tournaments").select("*").eq("is_visible", True).order("created_at"),
            "tournament_list",
        )
        return rows, error

    def _registration_for_user(tournament_id, user_id):
        if not tournament_id or not user_id:
            return None
        rows, _ = _safe_rows(
            db.table("tournament_registrations").select("*")
            .eq("tournament_id", tournament_id).eq("user_id", user_id).limit(1),
            "tournament_registration_for_user",
        )
        return rows[0] if rows else None

    def _member_for_user(tournament_id, user_id):
        if not tournament_id or not user_id:
            return None
        rows, _ = _safe_rows(
            db.table("tournament_members").select("*")
            .eq("tournament_id", tournament_id).eq("user_id", user_id).limit(1),
            "tournament_member_for_user",
        )
        return rows[0] if rows else None

    def _decorate_registration_rows(rows):
        user_ids = [str(row.get("user_id")) for row in rows if row.get("user_id")]
        users = {}
        if user_ids:
            user_rows, _ = _safe_rows(
                db.table("users").select("id,username,display_name,avatar_url,account_status")
                .in_("id", user_ids),
                "tournament_registration_users",
            )
            users = {str(row.get("id")): row for row in user_rows}
        for row in rows:
            user = users.get(str(row.get("user_id"))) or {}
            row["user"] = user
            row["display_name"] = user.get("display_name") or user.get("username") or "Tài khoản"
        return rows

    def _admin_tournament_data():
        data = {
            "db_ready": True,
            "tournaments": [],
            "selected": None,
            "pending": [],
            "approved": [],
            "rejected": [],
            "members": [],
        }
        tournaments, error = _list_tournaments()
        if error:
            data["db_ready"] = False
            return data
        data["tournaments"] = tournaments
        selected = tournaments[0] if tournaments else None
        data["selected"] = selected
        if not selected:
            return data
        tournament_id = selected.get("id")
        registrations, _ = _safe_rows(
            db.table("tournament_registrations").select("*")
            .eq("tournament_id", tournament_id).order("registered_at"),
            "admin_tournament_registrations",
        )
        registrations = _decorate_registration_rows(registrations)
        data["pending"] = [row for row in registrations if row.get("status") == "pending"]
        data["approved"] = [row for row in registrations if row.get("status") == "approved"]
        data["rejected"] = [row for row in registrations if row.get("status") == "rejected"]

        members, _ = _safe_rows(
            db.table("tournament_members").select("*")
            .eq("tournament_id", tournament_id).order("approved_at"),
            "admin_tournament_members",
        )
        data["members"] = _decorate_registration_rows(members)
        return data

    @app.context_processor
    def inject_tournament_context():
        payload = {"tournament_area_enabled": tournament_area_enabled()}
        if request.endpoint == "admin":
            payload["tournament_admin_data"] = _admin_tournament_data()
        return payload

    @app.get('/tournaments')
    @login_required
    def tournaments():
        opened = tournament_area_enabled()
        tournament_rows = []
        db_ready = True
        if opened:
            tournament_rows, error = _list_tournaments()
            db_ready = not bool(error)
            user = current_user() or {}
            user_id = user.get("id")
            for item in tournament_rows:
                item["my_registration"] = _registration_for_user(item.get("id"), user_id)
                item["my_member"] = _member_for_user(item.get("id"), user_id)
        return render_template(
            'tournaments.html',
            tournament_open=opened,
            tournaments=tournament_rows,
            tournament_db_ready=db_ready,
        )

    @app.post('/tournaments/<tournament_id>/register')
    @login_required
    def tournament_register(tournament_id):
        if not tournament_area_enabled():
            flash("Khu vực Giải đấu đang tạm đóng.", "warning")
            return redirect(url_for("tournaments"))
        user = current_user() or {}
        user_id = user.get("id")
        tournaments_found, error = _safe_rows(
            db.table("tournaments").select("*").eq("id", tournament_id).limit(1),
            "tournament_register_lookup",
        )
        if error or not tournaments_found:
            flash("Chưa thể truy cập dữ liệu giải đấu. Hãy chạy SQL V1.4.25 trước.", "error")
            return redirect(url_for("tournaments"))
        tournament = tournaments_found[0]
        if not tournament.get("registration_open") or tournament.get("status") not in {"registration", "upcoming"}:
            flash("Giải đấu hiện không nhận đăng ký.", "warning")
            return redirect(url_for("tournaments"))
        if _member_for_user(tournament_id, user_id):
            flash("Bạn đã là thành viên của giải đấu này.", "info")
            return redirect(url_for("tournaments"))
        existing = _registration_for_user(tournament_id, user_id)
        payload = {
            "tournament_id": tournament_id,
            "user_id": user_id,
            "status": "pending",
            "registered_at": now_iso(),
            "reviewed_at": None,
            "reviewed_by": None,
        }
        try:
            if existing:
                execute_query(
                    db.table("tournament_registrations").update(payload).eq("id", existing.get("id")),
                    "tournament_register_update", attempts=2,
                )
            else:
                execute_query(
                    db.table("tournament_registrations").insert(payload),
                    "tournament_register_insert", attempts=2,
                )
            flash("Đã gửi đăng ký. Vui lòng chờ Admin duyệt.", "success")
        except Exception as exc:
            app.logger.exception("Tournament registration failed: %s", exc)
            flash("Không thể gửi đăng ký lúc này.", "error")
        return redirect(url_for("tournaments"))

    @app.post('/tournaments/<tournament_id>/withdraw')
    @login_required
    def tournament_withdraw(tournament_id):
        user = current_user() or {}
        user_id = user.get("id")
        registration = _registration_for_user(tournament_id, user_id)
        if registration and registration.get("status") == "pending":
            execute_query(
                db.table("tournament_registrations").update({"status": "withdrawn"})
                .eq("id", registration.get("id")),
                "tournament_withdraw", attempts=2,
            )
            flash("Đã hủy đăng ký giải đấu.", "success")
        return redirect(url_for("tournaments"))

    @app.post('/admin/tournaments/access')
    @login_required
    @admin_required
    @admin_permission_required("system_features_manage")
    def admin_tournament_access():
        enabled = request.form.get("enabled") == "1"
        execute_query(
            db.table("system_settings").upsert({
                "setting_key": TOURNAMENT_AREA_SETTING_KEY,
                "setting_value": {"enabled": enabled},
                "updated_at": now_iso(),
            }, on_conflict="setting_key"),
            "admin_update_tournament_area", attempts=2,
        )
        ttl_cache_delete("tournament_area_enabled")
        cache_delete("_tournament_area_enabled_cached")
        log_admin_action(
            "Mở khu vực Giải đấu" if enabled else "Tạm đóng khu vực Giải đấu",
            "system", details={"enabled": enabled},
        )
        flash("Đã mở khu vực Giải đấu." if enabled else "Đã tạm đóng khu vực Giải đấu.", "success")
        return redirect_admin("tournaments")

    def _review_registration(registration_id, new_status):
        rows, error = _safe_rows(
            db.table("tournament_registrations").select("*").eq("id", registration_id).limit(1),
            "admin_tournament_registration_lookup",
        )
        if error or not rows:
            flash("Không tìm thấy đăng ký giải đấu.", "error")
            return
        registration = rows[0]
        admin_user = current_user() or {}
        now_value = now_iso()
        execute_query(
            db.table("tournament_registrations").update({
                "status": new_status,
                "reviewed_at": now_value,
                "reviewed_by": admin_user.get("id"),
            }).eq("id", registration_id),
            "admin_tournament_registration_review", attempts=2,
        )
        if new_status == "approved":
            execute_query(
                db.table("tournament_members").upsert({
                    "tournament_id": registration.get("tournament_id"),
                    "user_id": registration.get("user_id"),
                    "status": "active",
                    "approved_at": now_value,
                    "approved_by": admin_user.get("id"),
                }, on_conflict="tournament_id,user_id"),
                "admin_tournament_member_upsert", attempts=2,
            )
        log_admin_action(
            "Duyệt đăng ký Giải đấu" if new_status == "approved" else "Từ chối đăng ký Giải đấu",
            "tournament_registration",
            details={"registration_id": registration_id, "status": new_status},
        )

    @app.post('/admin/tournaments/registrations/<registration_id>/approve')
    @login_required
    @admin_required
    @admin_permission_required("system_features_manage")
    def admin_tournament_registration_approve(registration_id):
        _review_registration(registration_id, "approved")
        flash("Đã duyệt HLV vào giải đấu.", "success")
        return redirect_admin("tournaments")

    @app.post('/admin/tournaments/registrations/<registration_id>/reject')
    @login_required
    @admin_required
    @admin_permission_required("system_features_manage")
    def admin_tournament_registration_reject(registration_id):
        _review_registration(registration_id, "rejected")
        flash("Đã từ chối đăng ký.", "success")
        return redirect_admin("tournaments")

    @app.post('/admin/tournaments/<tournament_id>/members/add')
    @login_required
    @admin_required
    @admin_permission_required("system_features_manage")
    def admin_tournament_member_add(tournament_id):
        user_id = str(request.form.get("user_id") or "").strip()
        if not user_id:
            flash("Hãy chọn tài khoản cần thêm.", "error")
            return redirect_admin("tournaments")
        admin_user = current_user() or {}
        now_value = now_iso()
        execute_query(
            db.table("tournament_registrations").upsert({
                "tournament_id": tournament_id,
                "user_id": user_id,
                "status": "approved",
                "registered_at": now_value,
                "reviewed_at": now_value,
                "reviewed_by": admin_user.get("id"),
            }, on_conflict="tournament_id,user_id"),
            "admin_tournament_registration_direct", attempts=2,
        )
        execute_query(
            db.table("tournament_members").upsert({
                "tournament_id": tournament_id,
                "user_id": user_id,
                "status": "active",
                "approved_at": now_value,
                "approved_by": admin_user.get("id"),
            }, on_conflict="tournament_id,user_id"),
            "admin_tournament_member_direct", attempts=2,
        )
        log_admin_action("Thêm HLV trực tiếp vào Giải đấu", "tournament_member", details={"tournament_id": tournament_id, "user_id": user_id})
        flash("Đã thêm HLV vào giải đấu.", "success")
        return redirect_admin("tournaments")
