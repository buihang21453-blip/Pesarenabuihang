"""Lucky Box routes: Admin management, Draft preview and user history."""

from . import repository
from . import service


def register_routes(context):
    globals().update(context)
    service.configure(context)

    def _admin_action(handler, success_message, rate_version_id=None):
        actor = current_user()
        try:
            result = handler(actor)
            flash(success_message(result), "success")
        except ValueError as exc:
            flash(str(exc), "warning")
        except Exception as exc:
            app.logger.exception(
                "Lucky Box Admin action failed actor=%s rate=%s: %s",
                actor.get("id"), rate_version_id, exc,
            )
            flash(service.error_message(exc), "danger")
        return redirect(url_for("admin_luckybox", rate_version_id=rate_version_id) if rate_version_id else url_for("admin_luckybox"))

    @app.route("/admin/lucky-box", methods=["GET"], endpoint="admin_luckybox")
    @login_required
    @admin_required
    def admin_luckybox_route():
        actor = current_user()
        selected_rate_id = str(request.args.get("rate_version_id") or "").strip()
        try:
            context_data = service.build_admin_context(actor, selected_rate_id)
        except Exception as exc:
            app.logger.exception("Lucky Box Admin page failed actor=%s: %s", actor.get("id"), exc)
            flash(service.error_message(exc), "danger")
            context_data = {
                "actor": actor,
                "boxes": [],
                "selected_box": None,
                "rate_versions": [],
                "selected_rate_version": None,
                "active_rate_version": None,
                "rewards": [],
                "reward_groups": {"zcoin": [], "shop": [], "exclusive": [], "other": []},
                "rate_validation": None,
                "duplicate_policies": service.DUPLICATE_POLICIES,
                "member_openings": [],
                "member_history_summary": {"opening_count": 0, "member_count": 0, "zcoin_spent": 0},
                "audit_logs": [],
                "max_preview_iterations": service.MAX_PREVIEW_ITERATIONS,
            }
        return render_template("admin_luckybox/index.html", **context_data)

    @app.route("/admin/lucky-box/box/<box_id>/save", methods=["POST"], endpoint="admin_luckybox_save_box")
    @login_required
    @admin_required
    def admin_luckybox_save_box_route(box_id):
        return _admin_action(
            lambda actor: service.save_box(actor, box_id, request.form),
            lambda _result: "Đã lưu cấu hình Lucky Box.",
            request.form.get("rate_version_id") or None,
        )

    @app.route("/admin/lucky-box/rates/<rate_version_id>/save", methods=["POST"], endpoint="admin_luckybox_save_rate")
    @login_required
    @admin_required
    def admin_luckybox_save_rate_route(rate_version_id):
        return _admin_action(
            lambda actor: service.save_rate(actor, rate_version_id, request.form),
            lambda _result: "Đã lưu cấu hình phiên bản Draft.",
            rate_version_id,
        )

    @app.route("/admin/lucky-box/rewards/<reward_id>/save", methods=["POST"], endpoint="admin_luckybox_save_reward")
    @login_required
    @admin_required
    def admin_luckybox_save_reward_route(reward_id):
        rate_version_id = str(request.form.get("rate_version_id") or "").strip()
        return _admin_action(
            lambda actor: service.save_reward(actor, reward_id, request.form),
            lambda _result: "Đã lưu reward.",
            rate_version_id,
        )

    @app.route("/admin/lucky-box/rates/<rate_version_id>/clone", methods=["POST"], endpoint="admin_luckybox_clone_rate")
    @login_required
    @admin_required
    def admin_luckybox_clone_rate_route(rate_version_id):
        actor = current_user()
        try:
            result = service.clone_rate(actor, rate_version_id, request.form.get("reason"))
            flash(f"Đã tạo Draft Version {result.get('version_number')} với {result.get('reward_count')} reward.", "success")
            return redirect(url_for("admin_luckybox", rate_version_id=result.get("rate_version_id")))
        except ValueError as exc:
            flash(str(exc), "warning")
        except Exception as exc:
            app.logger.exception("Lucky Box clone failed actor=%s rate=%s: %s", actor.get("id"), rate_version_id, exc)
            flash(service.error_message(exc), "danger")
        return redirect(url_for("admin_luckybox", rate_version_id=rate_version_id))

    @app.route("/admin/lucky-box/rates/<rate_version_id>/sync", methods=["POST"], endpoint="admin_luckybox_sync_rewards")
    @login_required
    @admin_required
    def admin_luckybox_sync_rewards_route(rate_version_id):
        return _admin_action(
            lambda actor: service.sync_rewards(actor, rate_version_id, request.form.get("reason")),
            lambda result: f"Đã đồng bộ reward. Thêm mới {result.get('added', 0)} reward.",
            rate_version_id,
        )

    @app.route("/admin/lucky-box/rates/<rate_version_id>/publish", methods=["POST"], endpoint="admin_luckybox_publish_rate")
    @login_required
    @admin_required
    def admin_luckybox_publish_rate_route(rate_version_id):
        return _admin_action(
            lambda actor: service.publish_rate(actor, rate_version_id, request.form.get("reason")),
            lambda result: f"Đã publish Version {result.get('version_number')} thành Active. Lucky Box vẫn giữ trạng thái bật/tắt riêng.",
            rate_version_id,
        )

    @app.route("/admin/lucky-box/preview", methods=["GET", "POST"], endpoint="admin_luckybox_preview")
    @login_required
    @admin_required
    def admin_luckybox_preview_route():
        actor = current_user()
        selected_rate_id = str(request.values.get("rate_version_id") or "").strip()
        result = None
        error = None
        if request.method == "POST":
            try:
                result = service.run_preview(actor, selected_rate_id, request.form.get("iterations") or 1000)
            except ValueError as exc:
                error = str(exc)
            except Exception as exc:
                app.logger.exception(
                    "Lucky Box preview failed actor=%s rate=%s: %s",
                    actor.get("id"), selected_rate_id, exc,
                )
                error = service.error_message(exc)
        return render_template(
            "admin_luckybox/preview.html",
            **service.build_admin_preview_context(actor, selected_rate_id, result=result, error=error),
        )


    @app.route("/lucky-box", endpoint="luckybox_home")
    @login_required
    def luckybox_home_route():
        actor = current_user()
        preview_requested = str(request.args.get("preview") or "").strip() == "1"
        admin_preview = preview_requested and is_admin_user(actor)
        selected_rate_id = str(request.args.get("rate_version_id") or "").strip()
        try:
            context_data = service.build_user_context(actor, admin_preview, selected_rate_id)
        except Exception as exc:
            app.logger.exception("Lucky Box user page failed user=%s: %s", actor.get("id"), exc)
            flash(service.error_message(exc), "danger")
            context_data = {
                "box": None, "active_rate": None, "selected_rate": None, "rewards": [],
                "reward_groups": {"zcoin": [], "shop": [], "exclusive": [], "other": []},
                "item_count_odds": [], "show_rates": False, "open_price": 0, "balance": int(actor.get("zcoin_balance") or 0),
                "can_open": False, "is_live": False, "preview_mode": admin_preview, "openings": [],
                "request_id": "", "reward_catalog": {},
            }
        return render_template("luckybox/index.html", **context_data)

    @app.route("/api/lucky-box/admin-preview-open", methods=["POST"], endpoint="luckybox_admin_preview_open")
    @login_required
    @admin_required
    def luckybox_admin_preview_open_route():
        actor = current_user()
        payload = request.get_json(silent=True) or request.form
        try:
            result = service.preview_open_for_admin(actor, payload.get("rate_version_id"))
            return jsonify({"ok": True, **result})
        except ValueError as exc:
            return jsonify({"ok": False, "message": str(exc)}), 400
        except Exception as exc:
            app.logger.exception("Lucky Box player UI preview failed actor=%s: %s", actor.get("id"), exc)
            return jsonify({"ok": False, "message": service.error_message(exc)}), 409

    @app.route("/api/lucky-box/open", methods=["POST"], endpoint="luckybox_open")
    @login_required
    def luckybox_open_route():
        user = current_user()
        payload = request.get_json(silent=True) or request.form
        try:
            result = service.open_for_user(
                user,
                payload.get("request_id") or payload.get("request_key"),
                payload.get("box_code") or service.BOX_CODE,
            )
        except ValueError as exc:
            return jsonify({"ok": False, "message": str(exc)}), 400
        except Exception as exc:
            app.logger.exception("Lucky Box open failed user=%s: %s", user.get("id"), exc)
            return jsonify({"ok": False, "message": service.error_message(exc)}), 409

        new_balance = int(result.get("balance_after") or 0)
        session["zcoin_balance"] = new_balance
        ttl_cache_delete(f"user:{user.get('id')}")
        cache_delete("_rz_current_user")
        cache_delete("_rz_players_all")
        cache_delete("_rz_users_map")
        return jsonify({"ok": True, **result})

    @app.route("/lucky-box/history", endpoint="luckybox_history")
    @login_required
    def luckybox_history_route():
        user = current_user()
        openings = repository.list_user_openings(user.get("id"), request.args.get("limit") or 30)
        return render_template("luckybox/history.html", openings=openings)

    @app.route("/lucky-box/openings/<opening_id>", endpoint="luckybox_opening_detail")
    @login_required
    def luckybox_opening_detail_route(opening_id):
        user = current_user()
        try:
            opening = service.build_opening_detail(user, opening_id)
        except PermissionError:
            return "Bạn không có quyền xem lượt mở này.", 403
        if not opening:
            return "Không tìm thấy lượt mở Lucky Box.", 404
        return render_template("luckybox/opening_detail.html", opening=opening)
