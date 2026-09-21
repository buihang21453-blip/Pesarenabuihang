"""Route quản trị Zcoin/Gift Code độc lập với dashboard Admin chính."""

from . import service


def register_routes(context):
    globals().update(context)
    service.configure(context)

    def _redirect_economy(anchor=""):
        target = url_for("admin_economy")
        return redirect(target + (f"#{anchor}" if anchor else ""))

    @app.route("/admin/economy", endpoint="admin_economy")
    @login_required
    @admin_required
    def admin_economy_page():
        actor = current_user()
        page_context = service.build_page_context(actor)
        return render_template("admin_economy/index.html", **page_context)

    @app.route(
        "/admin/economy/zcoin/adjust",
        methods=["POST"],
        endpoint="admin_economy_adjust_zcoin",
    )
    @login_required
    @admin_required
    def admin_economy_adjust_zcoin_route():
        actor = current_user()
        user_id = str(request.form.get("target_user_id") or "").strip()
        target = get_user(user_id) if user_id else None
        if not target or target.get("role") != "player":
            flash("Không tìm thấy tài khoản người chơi cần điều chỉnh Zcoin.", "danger")
            return _redirect_economy("adjust-zcoin")

        operation = str(request.form.get("operation") or "credit").strip().lower()
        try:
            amount = int(request.form.get("amount") or 0)
        except (TypeError, ValueError):
            amount = 0

        if operation not in {"credit", "debit"} or amount <= 0:
            flash("Hãy chọn cộng/trừ và nhập số Zcoin lớn hơn 0.", "danger")
            return _redirect_economy("adjust-zcoin")

        max_amount = 1_000_000
        if amount > max_amount:
            flash(
                f"Mỗi lần điều chỉnh tối đa {format_zcoin(max_amount)} Zcoin.",
                "danger",
            )
            return _redirect_economy("adjust-zcoin")

        reason = str(request.form.get("reason") or "").strip()
        request_token = str(request.form.get("request_token") or "").strip()
        if len(reason) < 3 or len(reason) > 300:
            flash("Lý do điều chỉnh phải có từ 3 đến 300 ký tự.", "danger")
            return _redirect_economy("adjust-zcoin")
        if not request_token or len(request_token) > 120:
            flash("Phiên điều chỉnh không hợp lệ. Hãy tải lại trang rồi thử lại.", "danger")
            return _redirect_economy("adjust-zcoin")

        delta = amount if operation == "credit" else -amount
        try:
            result = adjust_zcoin_balance(
                target.get("id"),
                delta,
                reason,
                actor.get("id"),
                request_token,
            )
        except ValueError as exc:
            flash(str(exc), "danger")
            return _redirect_economy("adjust-zcoin")
        except Exception as exc:
            lowered = str(exc).lower()
            app.logger.exception(
                "Điều chỉnh Zcoin thất bại user=%s: %s", user_id, exc
            )
            if "insufficient_zcoin" in lowered or "không đủ zcoin" in lowered:
                flash("Không thể trừ vì số dư Zcoin của người chơi không đủ.", "danger")
            elif (
                "adjust_zcoin_balance" in lowered
                or "pgrst202" in lowered
                or "schema cache" in lowered
            ):
                flash("Supabase chưa có RPC Zcoin tương thích.", "danger")
            else:
                flash(
                    "Không thể điều chỉnh Zcoin. Hãy kiểm tra dòng lỗi cuối trong Vercel Logs.",
                    "danger",
                )
            return _redirect_economy("adjust-zcoin")

        ttl_cache_delete(f"user:{target.get('id')}")
        cache_delete("_rz_players_all")
        cache_delete("_rz_users_map")
        cache_delete("_rz_current_user")

        action_text = "Cộng Zcoin" if delta > 0 else "Trừ Zcoin"
        log_admin_action(
            action_text,
            "zcoin_wallet",
            target.get("id"),
            target.get("username") or target.get("display_name"),
            (
                f"{delta:+d} Zcoin | "
                f"{result.get('balance_before', 0)} → "
                f"{result.get('balance_after', 0)} | {reason}"
            ),
        )
        if delta > 0 and not result.get("duplicate"):
            create_user_notification(
                target.get("id"),
                "Bạn nhận được Zcoin từ Admin",
                f"Admin đã tặng bạn {format_zcoin(amount)} Zcoin. Lý do: {reason}",
                url_for("zcoin_wallet", gift_tx=result.get("id")),
                "admin_gift_zcoin",
            )
        flash(
            f"Đã {action_text.lower()} {format_zcoin(amount)} cho "
            f"{target.get('display_name') or target.get('username')}. "
            f"Số dư mới: {format_zcoin(result.get('balance_after'))} Zcoin.",
            "success",
        )
        return _redirect_economy("adjust-zcoin")

    @app.route(
        "/admin/economy/gift-codes/create",
        methods=["POST"],
        endpoint="admin_economy_create_gift_code",
    )
    @login_required
    @admin_required
    def admin_economy_create_gift_code_route():
        actor = current_user()
        try:
            item = create_gift_code(actor, request.form)
        except ValueError as exc:
            flash(str(exc), "danger")
            return _redirect_economy("gift-codes")
        except Exception as exc:
            app.logger.exception("Tạo Gift Code thất bại: %s", exc)
            lowered = str(exc).lower()
            if "duplicate" in lowered or "unique" in lowered:
                flash("Gift Code này đã tồn tại. Hãy chọn mã khác.", "danger")
            else:
                flash(
                    "Không thể tạo Gift Code. Hãy kiểm tra dòng lỗi cuối trong Vercel Logs.",
                    "danger",
                )
            return _redirect_economy("gift-codes")

        metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
        target_user_id = str(metadata.get("target_user_id") or "").strip()
        if target_user_id:
            create_user_notification(
                target_user_id,
                "Bạn nhận được Gift Code từ Admin",
                f"Mã {item.get('code')} nhận {format_zcoin(item.get('reward_amount'))} Zcoin.",
                url_for("zcoin_rewards", gift_code=item.get("code")) + "#gift-code",
                "admin_gift_code",
            )
        log_admin_action(
            "Tạo Gift Code",
            "gift_code",
            item.get("id"),
            item.get("code"),
            (
                f"{item.get('reward_amount', 0)} Zcoin × "
                f"{item.get('max_redemptions', 0)} lượt"
            ),
        )
        flash(f"Đã tạo Gift Code {item.get('code')}.", "success")
        return _redirect_economy("gift-codes")

    @app.route(
        "/admin/economy/gift-codes/<code_id>/toggle",
        methods=["POST"],
        endpoint="admin_economy_toggle_gift_code",
    )
    @login_required
    @admin_required
    def admin_economy_toggle_gift_code_route(code_id):
        enabled = str(request.form.get("enabled") or "0").strip() == "1"
        try:
            toggle_gift_code(code_id, enabled)
        except Exception as exc:
            app.logger.exception(
                "Bật/tắt Gift Code thất bại id=%s: %s", code_id, exc
            )
            flash("Không thể thay đổi trạng thái Gift Code.", "danger")
            return _redirect_economy("gift-codes")

        log_admin_action(
            "Bật Gift Code" if enabled else "Tắt Gift Code",
            "gift_code",
            code_id,
            code_id,
            "enabled" if enabled else "disabled",
        )
        flash("Đã cập nhật trạng thái Gift Code.", "success")
        return _redirect_economy("gift-codes")
