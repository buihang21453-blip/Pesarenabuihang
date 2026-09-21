"""Route trang phần thưởng và nhận Zcoin điểm danh."""

import uuid


def register_routes(context):
    globals().update(context)

    @app.route("/zcoin/rewards")
    @login_required
    def zcoin_rewards():
        user = current_user()
        checkin_ready = True
        try:
            checkin_status = build_daily_checkin_status(user.get("id"))
        except Exception as exc:
            checkin_ready = False
            app.logger.exception("Không thể tải trạng thái điểm danh: %s", exc)
            checkin_status = {
                "ready": False,
                "claimed_today": False,
                "current_day": 0,
                "next_day": 1,
                "next_reward": DAILY_CHECKIN_REWARDS[0],
                "days": [
                    {"day": index, "reward": reward, "claimed": False, "completed": False, "next": index == 1, "today": False}
                    for index, reward in enumerate(DAILY_CHECKIN_REWARDS, start=1)
                ],
                "recent": [],
            }
        reward_effect = session.pop("zcoin_reward_effect", None)
        return render_template(
            "rewards/index.html",
            checkin_status=checkin_status,
            checkin_ready=checkin_ready,
            daily_request_token=uuid.uuid4().hex,
            gift_request_token=uuid.uuid4().hex,
            reward_effect=reward_effect,
            gift_code_prefill=str(request.args.get("gift_code") or "").strip().upper(),
        )

    @app.route("/zcoin/checkin/claim", methods=["POST"])
    @login_required
    def claim_daily_checkin_route():
        user = current_user()
        request_key = str(request.form.get("request_token") or "").strip()
        if not request_key or len(request_key) > 120:
            flash("Phiên điểm danh không hợp lệ. Hãy tải lại trang rồi thử lại.", "danger")
            return redirect(url_for("zcoin_rewards") + "#daily-checkin")

        try:
            result = claim_daily_reward(user.get("id"), request_key)
        except Exception as exc:
            message = str(exc).lower()
            app.logger.exception("Điểm danh Zcoin thất bại user=%s: %s", user.get("id"), exc)
            if "claim_daily_checkin" in message or "pgrst202" in message or "schema cache" in message:
                flash("Hệ thống điểm danh chưa được cài đặt đầy đủ. Hãy chạy SQL của V1.14.38.", "danger")
            else:
                flash("Không thể điểm danh lúc này. Hãy kiểm tra dòng lỗi cuối trong Vercel Logs.", "danger")
            return redirect(url_for("zcoin_rewards") + "#daily-checkin")

        ttl_cache_delete(f"user:{user.get('id')}")
        cache_delete("_rz_current_user")
        session["zcoin_balance"] = int(result.get("balance_after") or 0)

        if result.get("duplicate"):
            flash("Bạn đã nhận phần thưởng điểm danh hôm nay rồi.", "warning")
        else:
            reward = int(result.get("reward_amount") or 0)
            day = int(result.get("streak_day") or 1)
            session["zcoin_reward_effect"] = {
                "type": "daily_checkin",
                "title": "Điểm danh thành công!",
                "amount": reward,
                "streak_day": day,
                "balance_after": int(result.get("balance_after") or 0),
            }
            flash(f"Bạn nhận được {format_zcoin(reward)} Zcoin từ điểm danh ngày {day}.", "success")
        return redirect(url_for("zcoin_rewards") + "#daily-checkin")
