"""Route extracted from app.py without changing endpoint behavior.

Dependencies are injected from the application context at registration time to
avoid circular imports and preserve the existing business logic.
"""

def register_routes(context):
    globals().update(context)

    @app.route("/api/invites/pending")
    @login_required
    def api_pending_invites():
        """Truy vấn trực tiếp lời mời của người hiện tại để giảm độ trễ popup."""
        user = current_user()
        if not user:
            return jsonify({"invites": []})

        try:
            # Lấy nhiều bản ghi thay vì chỉ 1 bản ghi mới nhất. Nếu lời mời mới nhất
            # vừa hết hạn trong lúc xử lý, lời mời hợp lệ cũ hơn vẫn phải được trả về.
            result = execute_query(
                db.table("match_invites")
                  .select("id,from_user_id,to_user_id,tier,status,message,expires_at,created_at")
                  .eq("to_user_id", user["id"])
                  .eq("status", "pending")
                  .order("created_at", desc=True)
                  .limit(20),
                "api_pending_invites_direct",
                attempts=2,
            )
            rows = result.data or []
            data = []
            for row in rows:
                invite = expire_invite_if_needed(dict(row))
                if invite.get("status") != "pending":
                    continue
                sender = get_user(invite.get("from_user_id")) or {}
                decorate_player_achievements(sender)
                is_c1_invite = str(invite.get("tier") or "") == "C1_TOURNAMENT"
                data.append({
                    "id": invite["id"],
                    "from_name": sender.get("display_name", "Unknown"),
                    "from_avatar_url": sender.get("avatar_url"),
                    "from_avatar_frame": sender.get("avatar_frame"),
                    "from_achievement": sender.get("featured_achievement"),
                    "from_rank": get_rank_display(sender.get("rank_points", 0)),
                    "from_points": sender.get("rank_points", 0),
                    "tier": invite.get("tier") or SMART_RANDOM_MODE,
                    "invite_kind": "c1" if is_c1_invite else "rank",
                    "expires_in_seconds": int(invite.get("expires_in_seconds") or 0),
                    "accept_url": url_for("respond_invite", invite_id=invite["id"]),
                    "reject_url": url_for("respond_invite", invite_id=invite["id"]),
                })
            response = jsonify({"invites": data})
            response.headers["Cache-Control"] = "no-store, max-age=0"
            response.headers["X-Invite-Poll"] = "fast-active"
            return response
        except Exception as exc:
            # Không trả danh sách rỗng khi DB lỗi vì phía trình duyệt sẽ hiểu nhầm là
            # không còn lời mời và tự ẩn popup đang hiển thị.
            print(f"api_pending_invites ERROR user={user.get('id')}: {type(exc).__name__}: {exc}")
            response = jsonify({"ok": False, "error": "invite_poll_failed"})
            response.status_code = 503
            response.headers["Cache-Control"] = "no-store, max-age=0"
            return response

    @app.route("/invites")
    @login_required
    def invites():
        user = current_user()

        # Nếu người chơi đã có phòng active, không để mắc kẹt ở trang mời đấu.
        try:
            active_room = active_room_for_user(user["id"])
            if active_room:
                return redirect(url_for("room_detail", room_id=active_room["id"]))
        except Exception:
            flash("Đang kiểm tra phòng hiện tại hơi chậm, vui lòng thử lại sau vài giây.", "warning")

        # Dùng cùng chính sách Invisible Accounts như trang Players/BXH.
        # Tài khoản tàng hình nhìn thấy các tài khoản tàng hình khác; tài khoản
        # bình thường không thấy tài khoản tàng hình trong danh sách Mời đấu.
        all_players = invite_visible_players(user, include_admin=False, force_invisible_refresh=True)
        available_players = [
            player for player in all_players
            if str(player.get("id")) != str(user.get("id")) and player.get("is_online")
        ]

        all_invites = list_invites()
        received = [i for i in all_invites if i["to_user_id"] == user["id"] and i["status"] == "pending"]
        sent = [i for i in all_invites if i["from_user_id"] == user["id"] and i["status"] == "pending"]
        history = [i for i in all_invites if i["from_user_id"] == user["id"] or i["to_user_id"] == user["id"]][:20]

        return render_template(
            "invites.html",
            players=available_players,
            received=received,
            sent=sent,
            history=history,
        )

    @app.route("/invites/send", methods=["POST"])
    @login_required
    def send_invite():
        user = current_user()

        to_user_id = request.form.get("to_user_id")
        tier = SMART_RANDOM_MODE

        if not to_user_id or to_user_id == user["id"]:
            flash("Đối thủ không hợp lệ.", "danger")
            return redirect(url_for("players"))

        opponent = get_user(to_user_id)
        if not opponent:
            flash("Không tìm thấy đối thủ.", "danger")
            return redirect(url_for("players"))

        # V1.5.22: tài khoản Admin thật không được tham gia lời mời Rank/Friendly.
        # Đây là chặn backend, không phụ thuộc việc Admin có bị ẩn khỏi danh sách UI.
        if is_admin_user(user):
            flash("Tài khoản Admin không tham gia thi đấu Rank/Friendly. Hãy chuyển sang tài khoản Test để kiểm tra.", "warning")
            return redirect(url_for("players"))
        if is_admin_user(opponent):
            flash("Tài khoản Admin không nhận lời mời thi đấu. Hãy chọn HLV khác.", "warning")
            return redirect(url_for("players"))

        try:
            state = matchmaking_snapshot(user["id"], to_user_id)
        except Exception as exc:
            print(f"send_invite state ERROR from={user.get('id')} to={to_user_id}: {type(exc).__name__}: {exc}")
            flash("Không thể kiểm tra trạng thái phòng lúc này. Vui lòng thử lại sau vài giây.", "danger")
            return redirect(url_for("players"))

        sender_room = state.get("room_a")
        receiver_room = state.get("room_b")
        sender_room_is_c1 = bool(sender_room and (str(sender_room.get("note") or "").startswith("TOURNAMENT_ROOM|") or str(sender_room.get("match_mode") or "").lower() == "tournament"))
        receiver_room_is_c1 = bool(receiver_room and (str(receiver_room.get("note") or "").startswith("TOURNAMENT_ROOM|") or str(receiver_room.get("match_mode") or "").lower() == "tournament"))
        if sender_room_is_c1:
            flash("Bạn đang ở Phòng đấu C1. Hãy thoát/đóng Phòng C1 trước khi gửi lời mời Rank.", "warning")
            return redirect(url_for("dashboard"))
        if receiver_room_is_c1:
            flash("Người chơi này đang ở Phòng đấu C1 nên chưa thể nhận lời mời Rank.", "warning")
            return redirect(url_for("players"))
        if state.get("match_a"):
            flash("Bạn đang có trận chưa hoàn tất nên chưa thể gửi lời mời.", "warning")
            return redirect(url_for("dashboard"))
        if sender_room and not is_solo_waiting_room(sender_room, user["id"]):
            flash("Phòng của bạn đã có đủ 2 người hoặc đã bắt đầu. Bạn không thể gửi thêm lời mời.", "warning")
            return redirect(url_for("dashboard"))
        if state.get("match_b"):
            flash("Người chơi này đang thi đấu hoặc còn trận chưa hoàn tất.", "warning")
            return redirect(url_for("players"))
        if receiver_room and not is_solo_waiting_room(receiver_room, to_user_id):
            flash("Phòng của người chơi này đã có đủ 2 người hoặc đã bắt đầu.", "warning")
            return redirect(url_for("players"))

        if not is_user_online_now(opponent):
            flash("Người chơi này vừa offline. Bạn hãy chọn một đối thủ đang online khác nhé.", "danger")
            return redirect(url_for("players"))

        if state.get("pair_pending"):
            flash("Hai người đang có lời mời chờ xử lý.", "warning")
            return redirect(url_for("players"))

        invite_result = execute_query(
            db.table("match_invites").insert({
                "from_user_id": user["id"],
                "to_user_id": to_user_id,
                "tier": tier,
                "status": "pending",
                "message": f'{user["display_name"]} mời {opponent["display_name"]} thi đấu hạng.',
                "expires_at": future_iso(INVITE_TIMEOUT_SECONDS),
                "updated_at": now_iso(),
            }),
            "send_match_invite",
        )
        invite = invite_result.data[0] if invite_result.data else None
        ttl_cache_delete("invites_raw")
        cache_delete("_rz_invites_all")
        cache_delete("_rz_current_pending_invites")
        if not invite:
            flash("Không thể gửi lời mời lúc này. Vui lòng thử lại.", "danger")
            return redirect(url_for("players"))

        # Chủ phòng phải được đưa vào phòng ngay sau khi bấm Mời đấu.
        # Nếu đã có phòng trống thì gắn lời mời vào phòng đó; nếu chưa có thì tạo phòng mới.
        if sender_room:
            room_result = execute_query(
                db.table("match_rooms").update({
                    "invite_id": invite["id"],
                    "note": f'Đã mời {opponent["display_name"]}. Đang chờ đối thủ chấp nhận.',
                    "updated_at": now_iso(),
                }).eq("id", sender_room["id"]).eq("status", "waiting_ready"),
                "attach_invite_to_open_room",
            )
            room = room_result.data[0] if room_result.data else sender_room
        else:
            room_result = execute_query(
                db.table("match_rooms").insert({
                    "invite_id": invite["id"],
                    "host_user_id": user["id"],
                    "guest_user_id": None,
                    "team_tier": (SMART_RANDOM_MODE if system_feature_enabled("rank_standard_enabled") else FRIENDLY_RANDOM3_MODE),
                    "match_mode": MATCH_MODE_RANKED,
                    "friendly_tier": "A",
                    "status": "waiting_ready",
                    "guest_ready": False,
                    "note": f'Đã mời {opponent["display_name"]}. Đang chờ đối thủ chấp nhận.',
                    "state_expires_at": None,
                    "updated_at": now_iso(),
                }),
                "create_room_for_invite",
            )
            room = room_result.data[0] if room_result.data else None

        if not room:
            # Tránh để lại lời mời treo nếu tạo phòng thất bại.
            execute_query(
                db.table("match_invites").update({
                    "status": "cancelled",
                    "updated_at": now_iso(),
                }).eq("id", invite["id"]).eq("status", "pending"),
                "cancel_invite_after_room_error",
            )
            flash("Đã gửi lời mời nhưng không thể tạo phòng. Vui lòng thử lại.", "danger")
            return redirect(url_for("players"))

        flash(f'Đã mời {opponent["display_name"]}. Bạn đang ở trong phòng và chờ đối thủ chấp nhận.', "success")
        return redirect(url_for("room_detail", room_id=room["id"]))

    @app.route("/invites/quick-match", methods=["POST"])
    @login_required
    def quick_match_invite():
        user = current_user()
        if is_admin_user(user):
            return jsonify({"ok": False, "message": "Tài khoản Admin không tham gia Tìm Nhanh. Hãy chuyển sang tài khoản Test."}), 403
        payload = request.get_json(silent=True) or request.form or {}
        raw_excluded = payload.get("excluded_user_ids", [])
        if isinstance(raw_excluded, str):
            raw_excluded = [item for item in raw_excluded.split(",") if item]
        excluded_user_ids = {str(item).strip() for item in (raw_excluded or []) if str(item).strip()}
        if not system_feature_enabled("quick_match_enabled"):
            return jsonify({"ok": False, "message": "Tính năng Tìm Nhanh đang được Admin tắt."}), 403
        try:
            state = matchmaking_snapshot(user["id"])
        except Exception as exc:
            print(f"quick_match state ERROR user={user.get('id')}: {type(exc).__name__}: {exc}")
            return jsonify({"ok": False, "message": "Không thể kiểm tra trạng thái phòng lúc này."}), 503

        sender_room = state.get("room_a")
        if state.get("match_a") or not is_solo_waiting_room(sender_room, user["id"]):
            return jsonify({"ok": False, "message": "Tìm Nhanh chỉ dùng khi bạn đang ở phòng một mình."}), 409

        rooms = state.get("rooms") or []
        matches = state.get("matches") or []
        invites = state.get("invites") or []
        room_by_user = {}
        for room in rooms:
            for uid in (room.get("host_user_id"), room.get("guest_user_id")):
                if uid:
                    room_by_user[str(uid)] = room
        busy_match_ids = {str(uid) for m in matches for uid in (m.get("player1_id"), m.get("player2_id")) if uid}
        # Chỉ người đang CHỦ ĐỘNG gửi một lời mời khác mới được xem là bận.
        # Người chỉ đang NHẬN một hay nhiều lời mời vẫn có thể tiếp tục nhận thêm
        # lời mời thủ công hoặc Tìm Nhanh. Khi họ chấp nhận một lời mời, luồng
        # respond_invite sẽ tự hủy các lời mời chờ còn lại để tránh vào hai phòng.
        outgoing_inviter_ids = {
            str(i.get("from_user_id"))
            for i in invites
            if i.get("from_user_id")
        }
        if str(user["id"]) in outgoing_inviter_ids:
            return jsonify({"ok": False, "message": "Bạn đang chờ một đối thủ phản hồi lời mời đã gửi."}), 409

        # Chỉ một lần bấm hợp lệ (đang ở phòng một mình, không bận) mới kích hoạt
        # trạng thái Tìm Nhanh. Mỗi lần bấm làm mới cửa sổ 30 phút.
        quick_match_requested_at = now_iso()
        try:
            execute_query(
                db.table("users").update({
                    "quick_match_requested_at": quick_match_requested_at,
                }).eq("id", user["id"]),
                "quick_match_mark_requested",
                attempts=3,
            )
        except Exception as exc:
            print(f"quick_match mark ERROR user={user.get('id')}: {type(exc).__name__}: {exc}")
            return jsonify({
                "ok": False,
                "message": "Không thể bật trạng thái Tìm Nhanh. Hãy kiểm tra SQL cập nhật V1.4.40.",
            }), 503

        my_points = int(user.get("rank_points", 0) or 0)
        my_rank_level = get_rank_level(my_points)
        candidates = []
        online_total = 0
        busy_total = 0
        cooldown_total = 0

        # Tìm Nhanh phải đọc presence trực tiếp từ Supabase thay vì dùng danh sách
        # người chơi đã cache. Cache ngắn vẫn có thể làm một tài khoản vừa heartbeat
        # bị coi là offline trên instance Vercel khác. last_seen_at là nguồn xác thực
        # chính; is_online chỉ là cờ hiển thị nhanh.
        try:
            online_result = execute_query(
                db.table("users")
                .select("id,username,display_name,role,admin_level,account_status,rank_points,is_online,last_seen_at,matchmaking_cooldown_until,quick_match_requested_at"),
                "quick_match_live_players",
                attempts=3,
            )
            quick_players = [dict(row) for row in (online_result.data or [])]
        except Exception as exc:
            print(f"quick_match players ERROR user={user.get('id')}: {type(exc).__name__}: {exc}")
            return jsonify({"ok": False, "message": "Không thể đọc danh sách người chơi online lúc này."}), 503

        presence_cutoff = now_dt() - timedelta(seconds=max(ONLINE_TIMEOUT_SECONDS, 90))
        quick_match_cutoff = now_dt() - timedelta(seconds=QUICK_MATCH_ACTIVE_SECONDS)
        invisible_ids = get_invisible_player_ids(force=True)
        for opponent in quick_players:
            oid = str(opponent.get("id") or "")
            if not oid or oid == str(user["id"]) or oid in excluded_user_ids:
                continue
            if not can_view_player_identity(oid, user, invisible_ids):
                continue
            role = str(opponent.get("role") or "").strip().lower()
            admin_level = str(opponent.get("admin_level") or "").strip().lower()
            # Admin tuyệt đối không phải ứng viên Tìm Nhanh.
            if role == "admin" or admin_level in {"owner","admin"}:
                continue
            if role != "player":
                continue
            if opponent.get("account_status", "approved") != "approved":
                continue
            seen = parse_dt(opponent.get("last_seen_at"))
            # Admin chọn Offline vẫn có last_seen_at mới vì thao tác đổi trạng thái
            # và heartbeat ẩn tiếp tục cập nhật thời gian. Vì vậy Tìm Nhanh phải
            # kiểm tra đồng thời cờ is_online; chỉ dựa last_seen_at sẽ gửi lời mời
            # giả tới Admin đang ẩn trạng thái, trong khi phía nhận không nhận popup.
            if opponent.get("is_online") is not True or not seen or seen < presence_cutoff:
                continue
            online_total += 1

            # V1.4.41: phía nhận đủ điều kiện nếu thỏa MỘT trong hai:
            # 1) đã chủ động bấm Tìm Nhanh trong 30 phút gần nhất; HOẶC
            # 2) đang ở phòng đấu một mình, trạng thái chờ và chưa có đối thủ.
            # Người chỉ Online nhưng không ở phòng chờ và cũng chưa bật Tìm Nhanh
            # vẫn không bị hệ thống tự động chọn.
            opponent_requested_at = parse_dt(opponent.get("quick_match_requested_at"))
            opponent_quick_active = bool(
                opponent_requested_at and opponent_requested_at >= quick_match_cutoff
            )
            opponent_room = room_by_user.get(oid)
            opponent_solo_waiting = bool(
                opponent_room and is_solo_waiting_room(opponent_room, oid)
            )
            if not (opponent_quick_active or opponent_solo_waiting):
                continue

            # Có lời mời ĐẾN không làm người chơi bị loại khỏi danh sách.
            # Chỉ loại khi chính họ đang có lời mời ĐI chờ phản hồi.
            if oid in busy_match_ids or oid in outgoing_inviter_ids:
                busy_total += 1
                continue
            if opponent_room and not opponent_solo_waiting:
                busy_total += 1
                continue
            opponent_points = int(opponent.get("rank_points", 0) or 0)
            gap = abs(opponent_points - my_points)
            same_rank = get_rank_level(opponent_points) == my_rank_level

            # Thứ tự ưu tiên Tìm Nhanh:
            # 0. Cùng bậc Rank (luôn ưu tiên trước)
            # 1. Khác Rank, chênh tối đa 300 RP
            # 2. Khác Rank, chênh 301-500 RP
            # 3. Khác Rank, chênh 501-1.000 RP
            # 4. Khác Rank, chênh 1.001-2.000 RP
            # Người khác Rank chênh quá 2.000 RP không được chọn.
            priority_group = quick_match_priority_group(same_rank=same_rank, points_gap=gap)
            if priority_group is None:
                continue

            # Trong cùng nhóm: ưu tiên RP gần nhất, sau đó người hoạt động
            # gần đây hơn, cuối cùng mới dùng tên để kết quả ổn định.
            sort_key = build_candidate_sort_key(
                priority_group=priority_group,
                points_gap=gap,
                last_seen=seen,
                display_name=opponent.get("display_name") or opponent.get("username") or "",
            )
            candidates.append((*sort_key, opponent))

        if not candidates:
            # Không có ứng viên ngay lúc này vẫn là một lần bấm Tìm Nhanh hợp lệ.
            # Giữ HLV trong hàng đợi 30 phút để một HLV khác bấm sau có thể ghép.
            return jsonify({
                "ok": True,
                "searching": True,
                "invite_id": None,
                "opponent_id": None,
                "active_seconds": QUICK_MATCH_ACTIVE_SECONDS,
                "active_until": future_iso(QUICK_MATCH_ACTIVE_SECONDS),
                "message": "Đã bật Tìm Nhanh trong 30 phút. Hệ thống có thể ghép với HLV đã bật Tìm Nhanh trong 30 phút hoặc đang ở phòng đấu một mình chờ đối thủ, nếu vẫn thỏa các điều kiện ghép trận.",
            })

        candidates.sort(key=lambda item: (item[0], item[1], item[2], item[3]))
        opponent = candidates[0][4]
        invite_result = execute_query(
            db.table("match_invites").insert({
                "from_user_id": user["id"], "to_user_id": opponent["id"],
                "tier": SMART_RANDOM_MODE, "status": "pending",
                "message": f'QUICK_MATCH|{user["display_name"]} tìm nhanh và mời {opponent["display_name"]} thi đấu hạng.',
                "expires_at": future_iso(INVITE_TIMEOUT_SECONDS), "updated_at": now_iso(),
            }), "quick_match_create_invite",
        )
        invite = invite_result.data[0] if invite_result.data else None
        if not invite:
            return jsonify({"ok": False, "message": "Không thể gửi lời mời lúc này."}), 500
        attach_result = execute_query(
            db.table("match_rooms").update({
                "invite_id": invite["id"],
                "note": "Đã tìm thấy đối thủ phù hợp. Đang chờ phản hồi.",
                "updated_at": now_iso(),
            }).eq("id", sender_room["id"]).eq("status", "waiting_ready").is_("guest_user_id", "null"),
            "quick_match_attach_invite",
        )
        if not attach_result.data:
            execute_query(
                db.table("match_invites").update({
                    "status": "cancelled",
                    "updated_at": now_iso(),
                }).eq("id", invite["id"]).eq("status", "pending"),
                "quick_match_cancel_unattached_invite",
                attempts=2,
            )
            ttl_cache_delete("invites_raw")
            cache_delete("_rz_invites_all")
            return jsonify({
                "ok": False,
                "message": "Phòng vừa thay đổi nên lời mời chưa được gửi. Vui lòng bấm Tìm Nhanh lại.",
            }), 409
        ttl_cache_delete("invites_raw")
        cache_delete("_rz_invites_all")
        return jsonify({
            "ok": True,
            "invite_id": invite.get("id"),
            "opponent_id": opponent.get("id"),
            "message": "Đã tìm thấy đối thủ. Đang chờ phản hồi...",
        })

    @app.route("/api/invites/quick-match/<invite_id>/status")
    @login_required
    def quick_match_invite_status(invite_id):
        """Return the live state of a Quick Match invitation.

        This endpoint also reconciles stale pending rows. A Quick Match chain must
        stop when the sender's room is already filled, and must move on when the
        selected opponent goes offline or becomes unavailable.
        """
        user = current_user()
        invite = get_invite(invite_id)
        if not invite or str(invite.get("from_user_id")) != str(user.get("id")) or not is_quick_match_invite(invite):
            return jsonify({
                "ok": False,
                "status": "missing",
                "continue_search": False,
                "message": "Không tìm thấy lượt Tìm Nhanh.",
            }), 404

        status = str(invite.get("status") or "")
        continue_search = status in {"rejected", "expired", "cancelled"}
        reason = status

        if status == "pending":
            sender_id = invite.get("from_user_id")
            opponent_id = invite.get("to_user_id")
            now = now_dt()

            room_result = execute_query(
                db.table("match_rooms")
                  .select("id,host_user_id,guest_user_id,status,invite_id")
                  .eq("host_user_id", sender_id)
                  .in_("status", ["waiting_ready", "playing", "friendly_playing", "waiting_result_confirm"])
                  .order("updated_at", desc=True)
                  .limit(1),
                "quick_match_status_sender_room",
                attempts=2,
            )
            sender_room = dict(room_result.data[0]) if room_result.data else None

            # A different player has already entered the sender's room. The search
            # is complete and must not continue to invite more people.
            if sender_room and sender_room.get("guest_user_id"):
                guest_id = str(sender_room.get("guest_user_id"))
                next_status = "accepted" if guest_id == str(opponent_id) else "cancelled"
                execute_query(
                    db.table("match_invites").update({
                        "status": next_status,
                        "updated_at": now_iso(),
                    }).eq("id", invite_id).eq("status", "pending"),
                    "quick_match_close_when_room_filled",
                    attempts=2,
                )
                status = "room_filled"
                reason = "room_filled"
                continue_search = False
            elif not sender_room or not is_solo_waiting_room(sender_room, sender_id):
                execute_query(
                    db.table("match_invites").update({
                        "status": "cancelled",
                        "updated_at": now_iso(),
                    }).eq("id", invite_id).eq("status", "pending"),
                    "quick_match_cancel_sender_unavailable",
                    attempts=2,
                )
                status = "sender_unavailable"
                reason = "sender_unavailable"
                continue_search = False
            else:
                opponent_result = execute_query(
                    db.table("users")
                      .select("id,is_online,last_seen_at,role,admin_level,account_status")
                      .eq("id", opponent_id)
                      .limit(1),
                    "quick_match_status_opponent_presence",
                    attempts=2,
                )
                opponent = dict(opponent_result.data[0]) if opponent_result.data else None
                seen = parse_dt((opponent or {}).get("last_seen_at"))
                presence_cutoff = now - timedelta(seconds=max(ONLINE_TIMEOUT_SECONDS, 90))
                opponent_online = bool(
                    opponent
                    and (opponent.get("account_status", "approved") == "approved")
                    and seen
                    and seen >= presence_cutoff
                    and opponent.get("is_online") is not False
                )

                if not opponent_online:
                    execute_query(
                        db.table("match_invites").update({
                            "status": "cancelled",
                            "updated_at": now_iso(),
                        }).eq("id", invite_id).eq("status", "pending"),
                        "quick_match_cancel_offline_opponent",
                        attempts=2,
                    )
                    status = "opponent_offline"
                    reason = "opponent_offline"
                    continue_search = True
                else:
                    availability = matchmaking_snapshot(opponent_id)
                    opponent_room = availability.get("room_a")
                    opponent_busy = bool(
                        availability.get("match_a")
                        or (opponent_room and not is_solo_waiting_room(opponent_room, opponent_id))
                    )
                    other_pending = any(
                        str(row.get("id")) != str(invite_id)
                        and str(opponent_id) in {str(row.get("from_user_id")), str(row.get("to_user_id"))}
                        for row in (availability.get("invites") or [])
                    )
                    if opponent_busy or other_pending:
                        execute_query(
                            db.table("match_invites").update({
                                "status": "cancelled",
                                "updated_at": now_iso(),
                            }).eq("id", invite_id).eq("status", "pending"),
                            "quick_match_cancel_unavailable_opponent",
                            attempts=2,
                        )
                        status = "opponent_unavailable"
                        reason = "opponent_unavailable"
                        continue_search = True

        if status != "pending":
            ttl_cache_delete("invites_raw")
            cache_delete("_rz_invites_all")
            cache_delete("_rz_current_pending_invites")

        return jsonify({
            "ok": True,
            "status": status,
            "reason": reason,
            "continue_search": bool(continue_search),
            "opponent_id": invite.get("to_user_id"),
            "expires_in_seconds": int(invite.get("expires_in_seconds") or 0),
        })

    @app.route("/invites/respond/<invite_id>", methods=["POST"])
    @login_required
    def respond_invite(invite_id):
        user = current_user()
        action = request.form.get("action")
        invite = get_invite(invite_id)

        if is_admin_user(user):
            if invite and invite.get("status") == "pending":
                try:
                    execute_query(
                        db.table("match_invites").update({
                            "status":"cancelled",
                            "updated_at":now_iso(),
                        }).eq("id",invite_id).eq("status","pending"),
                        "cancel_invite_targeting_admin",
                        attempts=2,
                    )
                    ttl_cache_delete("invites_raw")
                    cache_delete("_rz_invites_all")
                    cache_delete("_rz_current_pending_invites")
                except Exception:
                    pass
            flash("Tài khoản Admin không tham gia thi đấu. Hãy chuyển sang tài khoản Test nếu cần kiểm tra luồng trận.", "warning")
            return redirect(url_for("admin"))

        if not invite:
            flash("Không tìm thấy lời mời.", "danger")
            return redirect(url_for("invites"))

        if invite["to_user_id"] != user["id"]:
            flash("Bạn không có quyền xử lý lời mời này.", "danger")
            return redirect(url_for("invites"))

        # V1.5.12: lời mời C1 dùng chung popup realtime nhưng có luồng nhận riêng,
        # tuyệt đối không rơi xuống logic Rank bên dưới.
        if str(invite.get("tier") or "") == "C1_TOURNAMENT":
            if invite.get("status") == "expired":
                flash("Lời mời C1 đã hết hạn. Hãy nhờ đối thủ gửi lại.", "warning")
                return redirect(url_for("tournaments"))
            if invite.get("status") != "pending":
                flash("Lời mời C1 này đã được xử lý.", "warning")
                return redirect(url_for("tournaments"))
            room_result = execute_query(
                db.table("match_rooms").select("id,note,invite_id,status").eq("invite_id", invite_id).limit(1),
                "respond_c1_invite_room",
                attempts=2,
            )
            c1_room = (room_result.data or [None])[0]
            if not c1_room:
                execute_query(db.table("match_invites").update({"status":"cancelled","updated_at":now_iso()}).eq("id",invite_id),"cancel_orphan_c1_invite",attempts=1)
                ttl_cache_delete("invites_raw"); cache_delete("_rz_invites_all"); cache_delete("_rz_current_pending_invites")
                flash("Phòng C1 của lời mời không còn tồn tại.", "warning")
                return redirect(url_for("tournaments"))
            try:
                import json as _json
                raw_note = str(c1_room.get("note") or "")
                c1_meta = _json.loads(raw_note[len("TOURNAMENT_ROOM|"):]) if raw_note.startswith("TOURNAMENT_ROOM|") else {}
            except Exception:
                c1_meta = {}
            tournament_id = str(c1_meta.get("tournament_id") or "")
            if not tournament_id or str(c1_meta.get("invited_user_id") or "") != str(user.get("id") or ""):
                flash("Lời mời C1 không còn hợp lệ với tài khoản của bạn.", "danger")
                return redirect(url_for("tournaments"))
            if action == "reject":
                execute_query(db.table("match_invites").update({"status":"rejected","updated_at":now_iso()}).eq("id",invite_id),"reject_c1_invite",attempts=1)
                c1_meta["invited_user_id"] = ""
                execute_query(db.table("match_rooms").update({"invite_id":None,"note":"TOURNAMENT_ROOM|"+_json.dumps(c1_meta,ensure_ascii=False,separators=(",",":")),"updated_at":now_iso()}).eq("id",c1_room.get("id")),"clear_rejected_c1_invite",attempts=1)
                ttl_cache_delete("invites_raw"); cache_delete("_rz_invites_all"); cache_delete("_rz_current_pending_invites")
                flash("Đã từ chối lời mời C1.", "success")
                return redirect(url_for("tournaments"))
            if action == "accept":
                return redirect(url_for("c1_room_accept", tournament_id=tournament_id, room_id=c1_room.get("id")))
            flash("Hành động không hợp lệ.", "danger")
            return redirect(url_for("tournaments"))

        if invite["status"] == "expired":
            flash("Lời mời đã hết hạn sau 60 giây. Hãy nhờ đối thủ gửi lời mời mới.", "warning")
            return redirect(url_for("dashboard"))

        if invite["status"] != "pending":
            flash("Lời mời này đã được xử lý.", "warning")
            return redirect(url_for("invites"))

        if action == "reject":
            db.table("match_invites").update({"status": "rejected", "updated_at": now_iso()}).eq("id", invite_id).execute()
            ttl_cache_delete("invites_raw")
            cache_delete("_rz_invites_all")
            if is_quick_match_invite(invite):
                flash("Đã từ chối lời mời Tìm Nhanh.", "success")
            else:
                flash("Đã từ chối lời mời.", "success")
            return redirect(url_for("invites"))

        if action != "accept":
            flash("Hành động không hợp lệ.", "danger")
            return redirect(url_for("invites"))

        receiver_match = active_match_for_user(user["id"])
        receiver_room = active_room_for_user(user["id"])
        receiver_room_is_c1 = bool(receiver_room and (str(receiver_room.get("note") or "").startswith("TOURNAMENT_ROOM|") or str(receiver_room.get("match_mode") or "").lower() == "tournament"))
        if receiver_room_is_c1:
            flash("Bạn đang ở Phòng đấu C1. Hãy thoát/đóng Phòng C1 trước khi nhận lời mời Rank.", "warning")
            return redirect(url_for("dashboard"))
        if receiver_match:
            flash("Bạn đang có trận chưa hoàn tất nên không thể nhận lời mời.", "warning")
            return redirect(url_for("dashboard"))
        if receiver_room and not is_solo_waiting_room(receiver_room, user["id"]):
            flash("Phòng của bạn đã có đủ 2 người hoặc đã bắt đầu nên không thể nhận lời mời khác.", "warning")
            return redirect(url_for("dashboard"))

        inviter_id = invite.get("from_user_id")
        inviter_room = active_room_for_user(inviter_id)
        inviter_room_is_c1 = bool(inviter_room and (str(inviter_room.get("note") or "").startswith("TOURNAMENT_ROOM|") or str(inviter_room.get("match_mode") or "").lower() == "tournament"))
        if inviter_room_is_c1:
            execute_query(
                db.table("match_invites").update({"status":"cancelled","updated_at":now_iso()}).eq("id", invite_id),
                "cancel_rank_invite_sender_in_c1",
                attempts=2,
            )
            flash("Người mời đang ở Phòng đấu C1 nên lời mời Rank đã được hủy.", "warning")
            return redirect(url_for("dashboard"))
        if active_match_for_user(inviter_id) or (inviter_room and not is_solo_waiting_room(inviter_room, inviter_id)):
            execute_query(
                db.table("match_invites").update({
                    "status": "cancelled",
                    "updated_at": now_iso(),
                }).eq("id", invite_id),
                "cancel_stale_invite_busy_sender",
            )
            flash("Người mời đang ở phòng hoặc trận khác. Lời mời này đã hết hiệu lực.", "warning")
            return redirect(url_for("dashboard"))

        room = None
        target_room_created = False
        try:
            if inviter_room:
                attach_result = execute_query(
                    db.table("match_rooms").update({
                        "invite_id": invite_id,
                        "guest_user_id": invite["to_user_id"],
                        "guest_ready": False,
                        "note": "Đối thủ đã vào phòng. Khách chưa sẵn sàng.",
                        "state_expires_at": None,
                        "updated_at": now_iso(),
                    })
                    .eq("id", inviter_room["id"])
                    .eq("status", "waiting_ready")
                    .is_("guest_user_id", "null"),
                    "attach_guest_to_open_room",
                )
                room = attach_result.data[0] if attach_result.data else None
            else:
                create_result = execute_query(
                    db.table("match_rooms").insert({
                        "invite_id": invite_id,
                        "host_user_id": invite["from_user_id"],
                        "guest_user_id": invite["to_user_id"],
                        "team_tier": (SMART_RANDOM_MODE if system_feature_enabled("rank_standard_enabled") else FRIENDLY_RANDOM3_MODE),
                        "match_mode": MATCH_MODE_RANKED,
                        "friendly_tier": "A",
                        "status": "waiting_ready",
                        "guest_ready": False,
                        "note": "Đối thủ đã vào phòng. Khách chưa sẵn sàng.",
                        "state_expires_at": None,
                        "updated_at": now_iso(),
                    }),
                    "create_room_when_accepting_invite",
                )
                room = create_result.data[0] if create_result.data else None
                target_room_created = bool(room)

            if not room:
                flash("Phòng của người mời vừa có người khác tham gia. Lời mời không còn hiệu lực.", "warning")
                return redirect(url_for("dashboard"))

            # Người nhận có thể đang làm chủ một phòng trống. Khi nhận lời, đóng phòng cũ
            # trước khi hoàn tất lời mời để mỗi tài khoản chỉ còn đúng một phòng active.
            if receiver_room and str(receiver_room.get("id")) != str(room.get("id")):
                old_invite_id = receiver_room.get("invite_id")
                delete_result = execute_query(
                    db.table("match_rooms").delete()
                    .eq("id", receiver_room["id"])
                    .eq("host_user_id", user["id"])
                    .eq("status", "waiting_ready")
                    .is_("guest_user_id", "null"),
                    "close_receiver_solo_room_on_accept",
                )
                if not delete_result.data:
                    raise RuntimeError("Không thể đóng phòng cũ của người nhận")
                if old_invite_id and str(old_invite_id) != str(invite_id):
                    execute_query(
                        db.table("match_invites").update({
                            "status": "cancelled",
                            "updated_at": now_iso(),
                        }).eq("id", old_invite_id).eq("status", "pending"),
                        "cancel_receiver_old_room_invite",
                    )

            execute_query(
                db.table("match_invites").update({
                    "status": "accepted",
                    "updated_at": now_iso(),
                }).eq("id", invite_id).eq("status", "pending"),
                "accept_match_invite",
            )
            # Hủy các lời mời chờ khác của người nhận để popup cũ không xuất hiện lại.
            execute_query(
                db.table("match_invites").update({
                    "status": "cancelled",
                    "updated_at": now_iso(),
                }).eq("to_user_id", user["id"]).eq("status", "pending").neq("id", invite_id),
                "cancel_other_incoming_invites_after_accept",
                attempts=1,
            )
            execute_query(
                db.table("match_invites").update({
                    "status": "cancelled",
                    "updated_at": now_iso(),
                }).eq("from_user_id", user["id"]).eq("status", "pending").neq("id", invite_id),
                "cancel_receiver_outgoing_invites_after_accept",
                attempts=1,
            )
            # Khi phòng của người mời đã có khách, mọi lời mời khác do người
            # mời gửi (bao gồm Tìm Nhanh) phải kết thúc để không còn trạng thái treo.
            execute_query(
                db.table("match_invites").update({
                    "status": "cancelled",
                    "updated_at": now_iso(),
                }).eq("from_user_id", inviter_id).eq("status", "pending").neq("id", invite_id),
                "cancel_inviter_other_outgoing_after_accept",
                attempts=1,
            )
        except Exception as exc:
            print(f"respond_invite accept ERROR invite={invite_id}: {type(exc).__name__}: {exc}")
            # Hoàn tác việc gắn khách nếu đóng phòng cũ thất bại.
            try:
                if room:
                    if target_room_created:
                        execute_query(
                            db.table("match_rooms").delete().eq("id", room["id"]),
                            "rollback_created_invite_room",
                            attempts=1,
                        )
                    else:
                        execute_query(
                            db.table("match_rooms").update({
                                "guest_user_id": None,
                                "guest_ready": False,
                                "invite_id": invite_id,
                                "note": "Đang chờ đối thủ chấp nhận lời mời.",
                                "updated_at": now_iso(),
                            }).eq("id", room["id"]).eq("guest_user_id", user["id"]),
                            "rollback_attached_invite_guest",
                            attempts=1,
                        )
            except Exception as rollback_exc:
                print(f"respond_invite rollback warning: {rollback_exc}")
            flash("Không thể chuyển phòng an toàn lúc này. Phòng cũ của bạn vẫn được giữ nguyên; vui lòng thử lại.", "danger")
            return redirect(url_for("dashboard"))

        ttl_cache_delete("rooms_raw")
        ttl_cache_delete("invites_raw")
        cache_delete("_rz_rooms_all")
        cache_delete("_rz_invites_all")
        cache_delete("_rz_current_pending_invites")
        flash("Đã nhận lời mời. Phòng cũ một người của bạn đã được đóng và bạn đã vào phòng của đối thủ. Hãy bấm Sẵn sàng khi đã chuẩn bị xong.", "success")
        return redirect(url_for("room_detail", room_id=room["id"]))

    @app.route("/invites/cancel/<invite_id>", methods=["POST"])
    @login_required
    def cancel_invite(invite_id):
        user = current_user()
        invite = get_invite(invite_id)

        if not invite:
            flash("Không tìm thấy lời mời.", "danger")
            return redirect(url_for("invites"))

        if invite["from_user_id"] != user["id"]:
            flash("Bạn không có quyền hủy lời mời này.", "danger")
            return redirect(url_for("invites"))

        if invite["status"] != "pending":
            flash("Lời mời này đã được xử lý.", "warning")
            return redirect(url_for("invites"))

        db.table("match_invites").update({"status": "cancelled", "updated_at": now_iso()}).eq("id", invite_id).execute()
        flash("Đã hủy lời mời.", "success")
        return redirect(url_for("invites"))

