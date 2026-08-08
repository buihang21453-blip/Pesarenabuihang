"""Route ví Zcoin và thao tác Zcoin của Admin cho giai đoạn 1."""


def register_routes(context):
    globals().update(context)

    @app.context_processor
    def inject_zcoin_context():
        return {"format_zcoin": format_zcoin}

    @app.route("/zcoin")
    @login_required
    def zcoin_wallet():
        user = current_user()
        transactions = []
        wallet_ready = True
        try:
            transactions = list_zcoin_transactions(user.get("id"), limit=80)
        except Exception as exc:
            wallet_ready = False
            app.logger.exception("Không thể tải ví Zcoin: %s", exc)
        return render_template(
            "zcoin_wallet.html",
            transactions=transactions,
            wallet_ready=wallet_ready,
        )

    @app.route("/admin/zcoin/adjust", methods=["POST"])
    @login_required
    @admin_required
    @admin_permission_required("zcoin_manage")
    def admin_adjust_zcoin():
        actor = current_user()
        user_id = str(request.form.get("target_user_id") or "").strip()
        target = get_user(user_id) if user_id else None
        if not target or target.get("role") != "player":
            flash("Không tìm thấy tài khoản người chơi cần điều chỉnh Zcoin.", "danger")
            return redirect_admin("zcoin")

        operation = str(request.form.get("operation") or "credit").strip().lower()
        try:
            amount = int(request.form.get("amount") or 0)
        except (TypeError, ValueError):
            amount = 0
        if operation not in {"credit", "debit"} or amount <= 0:
            flash("Hãy chọn cộng/trừ và nhập số Zcoin lớn hơn 0.", "danger")
            return redirect_admin("zcoin")

        max_amount = 1_000_000 if is_owner_user(actor) else 100_000
        if amount > max_amount:
            flash(f"Mỗi lần điều chỉnh tối đa {format_zcoin(max_amount)} Zcoin với quyền hiện tại.", "danger")
            return redirect_admin("zcoin")

        reason = str(request.form.get("reason") or "").strip()
        request_token = str(request.form.get("request_token") or "").strip()
        if len(reason) < 3 or len(reason) > 300:
            flash("Lý do điều chỉnh phải có từ 3 đến 300 ký tự.", "danger")
            return redirect_admin("zcoin")
        if not request_token or len(request_token) > 120:
            flash("Phiên điều chỉnh không hợp lệ. Hãy tải lại trang Admin rồi thử lại.", "danger")
            return redirect_admin("zcoin")

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
            return redirect_admin("zcoin")
        except Exception as exc:
            message = str(exc)
            lowered = message.lower()
            app.logger.exception("Điều chỉnh Zcoin thất bại user=%s: %s", user_id, exc)
            if "insufficient_zcoin" in lowered or "không đủ zcoin" in lowered:
                flash("Không thể trừ vì số dư Zcoin của người chơi không đủ.", "danger")
            elif "adjust_zcoin_balance" in lowered or "pgrst202" in lowered or "schema cache" in lowered:
                flash("Supabase chưa có RPC Zcoin tương thích. Hãy chạy file SQL bổ sung của V1.14.33 trước.", "danger")
            else:
                flash("Không thể điều chỉnh Zcoin. Hãy kiểm tra dòng lỗi cuối trong Vercel Logs.", "danger")
            return redirect_admin("zcoin")

        ttl_cache_delete(f"user:{target.get('id')}")
        cache_delete("_rz_players_all")
        cache_delete("_rz_users_map")
        if str(actor.get("id")) == str(target.get("id")):
            cache_delete("_rz_current_user")

        action_text = "Cộng Zcoin" if delta > 0 else "Trừ Zcoin"
        log_admin_action(
            action_text,
            "zcoin_wallet",
            target.get("id"),
            target.get("username") or target.get("display_name"),
            f"{delta:+d} Zcoin | {result.get('balance_before', 0)} → {result.get('balance_after', 0)} | {reason}",
        )
        flash(
            f"Đã {action_text.lower()} {format_zcoin(amount)} cho {target.get('display_name') or target.get('username')}. "
            f"Số dư mới: {format_zcoin(result.get('balance_after'))} Zcoin.",
            "success",
        )
        return redirect_admin("zcoin")
