"""Route bỏ cuộc và đá lại trong phòng đấu.

Module đăng ký route theo dependency của app.py để giữ nguyên endpoint và tránh import vòng.
"""

def register_routes(context):
    """Đăng ký nhóm route vào Flask app hiện tại."""
    globals().update(context)

    def _award_forfeit_win(winner_id):
        """Tính một trận thắng do đối thủ bỏ cuộc, nhưng không cộng RP hoặc bàn thắng."""
        if not winner_id:
            return False
        winner = get_user(winner_id)
        if not winner:
            return False
        wins = int(winner.get("wins", 0) or 0) + 1
        draws = int(winner.get("draws", 0) or 0)
        losses = int(winner.get("losses", 0) or 0)
        streak = int(winner.get("streak", 0) or 0) + 1
        result = execute_query(
            db.table("users").update({
                "wins": wins,
                "total_matches": wins + draws + losses,
                "streak": streak,
            }).eq("id", winner_id),
            "award_forfeit_win",
        )
        ttl_cache_delete("players_raw", "achievement_map")
        return bool(result is not None)

    @app.route("/room/<room_id>/guest-forfeit", methods=["POST"])
    @login_required
    def room_guest_forfeit(room_id):
        """Khách chủ động bỏ cuộc sau khi đã chấp nhận vào phòng hoặc sau khi quay đội."""
        user = current_user()
        room = get_room(room_id)

        if not room:
            flash("Không tìm thấy phòng.", "danger")
            return redirect(url_for("dashboard"))

        if user["id"] != room.get("guest_user_id"):
            flash("Chỉ người chơi Sân Khách mới có thể dùng chức năng này.", "danger")
            return redirect(url_for("room_detail", room_id=room_id))

        allowed_statuses = {"waiting_ready", "playing", "friendly_playing"}
        if room.get("status") not in allowed_statuses:
            flash("Bạn không thể thoát ở trạng thái này. Nếu kết quả đang chờ xác nhận, hãy Xác nhận hoặc Gửi tranh chấp trước.", "warning")
            return redirect(url_for("room_detail", room_id=room_id))

        # Ở trạng thái chờ, chỉ bắt đầu áp dụng phạt sau khi khách đã bấm Sẵn Sàng.
        # Giao diện sẽ đưa khách chưa sẵn sàng qua route room_leave để rời phòng không mất RP.
        # Kiểm tra này bảo vệ cả trường hợp người dùng tự gửi POST trực tiếp vào route bỏ cuộc.
        if room.get("status") == "waiting_ready":
            limit_message = daily_rank_block_message(room.get("host_user_id"), room.get("guest_user_id"))
            if limit_message:
                flash("Đã chạm giới hạn trận Rank hôm nay. Hãy dùng Thoát Phòng; bạn sẽ không bị trừ RP.", "warning")
                return redirect(url_for("room_detail", room_id=room_id))
            if not bool(room.get("guest_ready")):
                flash("Bạn chưa Sẵn Sàng nên có thể rời phòng mà không bị trừ RP.", "warning")
                return redirect(url_for("room_detail", room_id=room_id))

        # Mọi chế độ giao hữu đều cho phép rời phòng an toàn:
        # không tạo lịch sử, không cộng/trừ RP và không tính bỏ cuộc.
        if room.get("match_mode") == MATCH_MODE_FRIENDLY or room.get("status") == "friendly_playing":
            execute_query(
                db.table("match_rooms").update({
                    "guest_user_id": None, "guest_ready": False, "guest_team": None,
                    "guest_team_overall": None, "guest_team_logo_url": None, "guest_team_league": None,
                    "host_team": None, "host_team_overall": None, "host_team_logo_url": None, "host_team_league": None,
                    "status": "waiting_ready", "match_id": None, "match_mode": MATCH_MODE_RANKED,
                    "team_tier": SMART_RANDOM_MODE, "note": "Khách đã rời trận giao hữu. Không trừ RP.",
                    "state_expires_at": None, "updated_at": now_iso(),
                }).eq("id", room_id),
                "guest_leave_random3_friendly",
            )
            flash("Bạn đã rời trận giao hữu. Không bị trừ RP và không lưu lịch sử.", "success")
            return redirect(url_for("dashboard"))

        original_status = room.get("status")
        reason = f'{user["display_name"]} đã chủ động bỏ cuộc và bị trừ {ROOM_ABANDON_PENALTY} RP.'
        result = execute_query(
            db.table("match_rooms").update({
                "status": "cancelled",
                "guest_ready": False,
                "note": reason,
                "state_expires_at": None,
                "updated_at": now_iso(),
            }).eq("id", room_id).eq("status", original_status),
            "guest_forfeit_room",
        )

        # Điều kiện status giúp tránh bấm hai lần và bị trừ RP nhiều lần.
        if not (result.data or []):
            flash("Phòng đã được xử lý trước đó. Bạn không bị trừ điểm thêm.", "warning")
            return redirect(url_for("dashboard"))

        penalty_delta = apply_room_abandon_penalty(user["id"])
        _award_forfeit_win(room.get("host_user_id"))
        record_room_forfeit_match(
            room,
            offender_role="guest",
            penalty_delta=penalty_delta if penalty_delta is not None else -ROOM_ABANDON_PENALTY,
            reason=reason,
            event_type="guest_manual_forfeit",
        )

        create_user_notification(
            room.get("host_user_id"),
            "🚪 Đối thủ đã bỏ cuộc",
            f'{user["display_name"]} đã thoát phòng và bị trừ {ROOM_ABANDON_PENALTY} RP. Bạn được tính 1 trận thắng và tăng chuỗi thắng, nhưng không được cộng RP.',
            "/matches",
            "guest_forfeit",
        )
        create_user_notification(
            user["id"],
            "⚠️ Bạn đã bỏ cuộc",
            f"Bạn bị trừ {ROOM_ABANDON_PENALTY} RP và được tính một trận thua.",
            "/matches",
            "room_forfeit_penalty",
        )
        flash(f"Bạn đã bỏ cuộc và bị trừ {ROOM_ABANDON_PENALTY} RP.", "danger")
        return redirect(url_for("dashboard"))


    @app.route("/room/<room_id>/host-forfeit", methods=["POST"])
    @login_required
    def room_host_forfeit(room_id):
        """Chủ phòng bỏ cuộc khi khách đã bấm Sẵn Sàng.

        Trạng thái chờ nhưng khách chưa sẵn sàng phải đi qua ``room_leave`` để
        đóng phòng không mất RP. Điều kiện ``guest_ready = true`` trong lệnh
        update bảo vệ trường hợp khách vừa hủy Sẵn Sàng cùng lúc chủ phòng xác
        nhận thoát.
        """
        user = current_user()
        room = get_room(room_id)

        if not room:
            flash("Không tìm thấy phòng.", "danger")
            return redirect(url_for("dashboard"))

        if user["id"] != room.get("host_user_id"):
            flash("Chỉ Chủ Phòng mới có thể dùng chức năng này.", "danger")
            return redirect(url_for("room_detail", room_id=room_id))

        original_status = room.get("status")
        allowed_statuses = {"waiting_ready", "playing"}
        if original_status not in allowed_statuses:
            flash("Phòng hiện không ở trạng thái Chủ phòng có thể bỏ cuộc.", "warning")
            return redirect(url_for("room_detail", room_id=room_id))

        if not room.get("guest_user_id"):
            flash("Phòng chưa có đối thủ nên bạn có thể đóng phòng mà không bị trừ RP.", "warning")
            return redirect(url_for("room_detail", room_id=room_id))

        if original_status == "waiting_ready":
            limit_message = daily_rank_block_message(room.get("host_user_id"), room.get("guest_user_id"))
            if limit_message:
                flash("Đã chạm giới hạn trận Rank hôm nay. Hãy dùng Thoát Phòng; bạn sẽ không bị trừ RP.", "warning")
                return redirect(url_for("room_detail", room_id=room_id))
            if not bool(room.get("guest_ready")):
                flash("Khách chưa Sẵn Sàng nên bạn có thể đóng phòng mà không bị trừ RP.", "warning")
                return redirect(url_for("room_detail", room_id=room_id))

        if original_status == "playing":
            reason = f'{user["display_name"]} đã rời phòng khi trận đang thi đấu và bị trừ {ROOM_ABANDON_PENALTY} RP.'
        else:
            reason = f'{user["display_name"]} đã rời phòng sau khi khách Sẵn Sàng và bị trừ {ROOM_ABANDON_PENALTY} RP.'

        query = (
            db.table("match_rooms").update({
                "status": "cancelled",
                "guest_ready": False,
                "note": reason,
                "state_expires_at": None,
                "updated_at": now_iso(),
            })
            .eq("id", room_id)
            .eq("status", original_status)
        )
        if original_status == "waiting_ready":
            query = query.eq("guest_ready", True)

        result = execute_query(query, "host_forfeit_room")

        # Nếu khách vừa Hủy Sẵn Sàng hoặc request khác đã xử lý phòng, không trừ RP.
        if not (result.data or []):
            flash("Trạng thái phòng vừa thay đổi. Bạn không bị trừ RP; hãy kiểm tra lại phòng.", "warning")
            return redirect(url_for("room_detail", room_id=room_id))

        penalty_delta = apply_room_abandon_penalty(user["id"])
        _award_forfeit_win(room.get("guest_user_id"))
        record_room_forfeit_match(
            room,
            offender_role="host",
            penalty_delta=penalty_delta if penalty_delta is not None else -ROOM_ABANDON_PENALTY,
            reason=reason,
            event_type="host_manual_forfeit",
        )

        create_user_notification(
            room.get("guest_user_id"),
            "🚪 Chủ phòng đã bỏ cuộc",
            f'{user["display_name"]} đã thoát phòng và bị trừ {ROOM_ABANDON_PENALTY} RP. Bạn được tính 1 trận thắng và tăng chuỗi thắng, nhưng không được cộng RP.',
            "/matches",
            "host_forfeit",
        )
        create_user_notification(
            user["id"],
            "⚠️ Bạn đã bỏ cuộc",
            f"Bạn bị trừ {ROOM_ABANDON_PENALTY} RP và được tính một trận thua do rời phòng khi trận đã cam kết.",
            "/matches",
            "room_forfeit_penalty",
        )
        flash(f"Bạn đã bỏ cuộc và bị trừ {ROOM_ABANDON_PENALTY} RP.", "danger")
        return redirect(url_for("dashboard"))


    @app.route("/room/<room_id>/rematch", methods=["POST"])
    @login_required
    def room_rematch(room_id):
        user = current_user()
        room = get_room(room_id)

        if not room:
            flash("Không tìm thấy phòng.", "danger")
            return redirect(url_for("dashboard"))

        # C1 V1.5.35: nếu vì dữ liệu cũ/phản hồi chậm mà room vẫn còn ở confirmed
        # trong khi lịch còn trận, dùng đúng thao tác "Sẵn Sàng -> Host quay đội" như Rank.
        # Không chặn Tournament và không bắt HLV quay về trang giải để mở Trận 2.
        room_note = str(room.get("note") or "")
        is_tournament_room = room_note.startswith("TOURNAMENT_ROOM|") or str(room.get("match_mode") or "").lower() == "tournament"
        if is_tournament_room:
            if user["id"] not in [room.get("host_user_id"), room.get("guest_user_id")]:
                flash("Bạn không thuộc phòng này.", "danger")
                return redirect(url_for("dashboard"))
            try:
                import json
                meta = json.loads(room_note[len("TOURNAMENT_ROOM|"):]) if room_note.startswith("TOURNAMENT_ROOM|") else {}
            except Exception:
                meta = {}
            tournament_id = str(meta.get("tournament_id") or "")
            stage_code = str(meta.get("stage_code") or "")
            current_mid = str(meta.get("tournament_match_id") or "")
            pair_ids = {str(room.get("host_user_id") or ""), str(room.get("guest_user_id") or "")}

            if room.get("status") != "confirmed":
                return redirect(url_for("room_detail", room_id=room_id))

            # V1.5.39: metadata phòng cũ có thể thiếu stage_code. Lấy lại từ chính
            # tournament_match hiện tại trước khi tìm trận kế tiếp để không truy vấn sai stage.
            current_match_row = None
            if tournament_id and current_mid:
                try:
                    cur = execute_query(
                        db.table("tournament_matches").select("*").eq("tournament_id", tournament_id).eq("id", current_mid).limit(1),
                        "room_c1_current_match_for_rematch",
                        attempts=2,
                    )
                    current_match_row = (cur.data or [None])[0] if cur is not None else None
                except Exception:
                    current_match_row = None
                if current_match_row:
                    stage_code = str(current_match_row.get("stage_code") or stage_code)
                    pair_ids = {
                        str(current_match_row.get("home_user_id") or room.get("host_user_id") or ""),
                        str(current_match_row.get("away_user_id") or room.get("guest_user_id") or ""),
                    }

            rows = []
            if tournament_id:
                q = db.table("tournament_matches").select("*").eq("tournament_id", tournament_id)
                if stage_code:
                    q = q.eq("stage_code", stage_code)
                result = execute_query(q, "room_c1_rank_style_next_match", attempts=2)
                rows = list(result.data or []) if result is not None else []

            candidates = [
                r for r in rows
                if {str(r.get("home_user_id") or ""), str(r.get("away_user_id") or "")} == pair_ids
                and str(r.get("status") or "").lower() not in {"completed", "cancelled"}
                and str(r.get("id") or "") != current_mid
            ]
            candidates.sort(key=lambda r: (int(r.get("leg_no") or 999), str(r.get("created_at") or ""), str(r.get("id") or "")))
            next_match = candidates[0] if candidates else None

            # V1.5.39: cứu dữ liệu lịch GĐ1 cũ bị thiếu leg 2.
            # Nếu trận hiện tại đã hoàn tất, cặp mới có 1 bản ghi nhưng luật GĐ1
            # yêu cầu 2 trận/cặp thì tạo đúng leg còn thiếu ngay lúc bấm Đá Tiếp.
            # Không tạo trong lúc render để tránh GET làm thay đổi dữ liệu.
            if not next_match and tournament_id and stage_code == "stage1":
                pair_rows = [
                    r for r in rows
                    if {str(r.get("home_user_id") or ""), str(r.get("away_user_id") or "")} == pair_ids
                    and str(r.get("status") or "").lower() != "cancelled"
                ]
                expected_pair_count = 2
                try:
                    st = execute_query(
                        db.table("tournament_stages").select("max_matches_per_opponent").eq("tournament_id", tournament_id).eq("stage_code", stage_code).limit(1),
                        "room_c1_expected_pair_count",
                        attempts=2,
                    )
                    strow = (st.data or [None])[0] if st is not None else None
                    configured = int((strow or {}).get("max_matches_per_opponent") or 0)
                    if configured > 0:
                        expected_pair_count = max(2, configured)
                except Exception:
                    expected_pair_count = 2

                completed_count = sum(1 for r in pair_rows if str(r.get("status") or "").lower() == "completed")
                if len(pair_rows) < expected_pair_count and completed_count < expected_pair_count:
                    used_legs = {int(r.get("leg_no") or 0) for r in pair_rows}
                    missing_leg = next((leg for leg in range(1, expected_pair_count + 1) if leg not in used_legs), len(pair_rows) + 1)
                    current_match = next((r for r in pair_rows if str(r.get("id") or "") == current_mid), None) or (pair_rows[0] if pair_rows else None)
                    if current_match:
                        # Lượt kế tiếp đảo sân so với trận hiện tại.
                        new_home = current_match.get("away_user_id")
                        new_away = current_match.get("home_user_id")
                        round_code = str(current_match.get("round_code") or "") or None
                        created = execute_query(
                            db.table("tournament_matches").insert({
                                "tournament_id": tournament_id,
                                "stage_code": "stage1",
                                "round_code": round_code,
                                "home_user_id": new_home,
                                "away_user_id": new_away,
                                "status": "pending",
                                "leg_no": missing_leg,
                                "created_at": now_iso(),
                                "updated_at": now_iso(),
                            }),
                            "room_c1_create_missing_stage1_leg",
                            attempts=2,
                        )
                        next_match = (created.data or [None])[0] if created is not None else None
                        if next_match:
                            app.logger.warning(
                                "C1 repaired missing stage1 leg room=%s tournament=%s pair=%s leg=%s",
                                room_id, tournament_id, sorted(pair_ids), missing_leg,
                            )

            if not next_match:
                flash("✅ Cặp đấu đã hoàn tất.", "success")
                return redirect(url_for("room_detail", room_id=room_id))

            history = list(meta.get("previous_match_ids") or [])
            if current_mid and current_mid not in history:
                history.append(current_mid)
            meta.update({
                "tournament_match_id": str(next_match.get("id") or ""),
                "stage_code": next_match.get("stage_code") or stage_code,
                "home_user_id": str(next_match.get("home_user_id") or ""),
                "away_user_id": str(next_match.get("away_user_id") or ""),
                "previous_match_ids": history,
                "current_leg_no": int(next_match.get("leg_no") or 1),
            })
            new_note = "TOURNAMENT_ROOM|" + json.dumps(meta, ensure_ascii=False, separators=(",", ":"))

            # V1.5.42: fallback cũng copy đúng Rank: mở trận mới ở waiting_ready
            # với guest_ready=False; khách phải bấm Sẵn Sàng lại trong room.
            guest_ready_now = False
            execute_query(
                db.table("match_rooms").update({
                    "note": new_note,
                    "status": "waiting_ready",
                    "guest_ready": guest_ready_now,
                    "match_id": None,
                    "host_team": None,
                    "guest_team": None,
                    "host_team_overall": None,
                    "guest_team_overall": None,
                    "host_team_logo_url": None,
                    "guest_team_logo_url": None,
                    "host_team_league": None,
                    "guest_team_league": None,
                    "host_score": None,
                    "guest_score": None,
                    "submitted_by_id": None,
                    "confirmed_by_id": None,
                    "invite_id": None,
                    "state_expires_at": None,
                    "match_mode": "tournament",
                    "team_tier": "TOURNAMENT_GD1" if str(next_match.get("stage_code") or "") == "stage1" else "TOURNAMENT",
                    "updated_at": now_iso(),
                }).eq("id", room_id).eq("status", "confirmed"),
                "room_c1_continue_like_rank",
                attempts=2,
            )
            verified_room = get_room(room_id)
            verified_note = str((verified_room or {}).get("note") or "")
            try:
                import json as _json
                verified_meta = _json.loads(verified_note[len("TOURNAMENT_ROOM|"):]) if verified_note.startswith("TOURNAMENT_ROOM|") else {}
            except Exception:
                verified_meta = {}
            if (
                not verified_room
                or str(verified_room.get("status") or "") != "waiting_ready"
                or bool(verified_room.get("guest_ready")) != bool(guest_ready_now)
                or str(verified_meta.get("tournament_match_id") or "") != str(next_match.get("id") or "")
            ):
                app.logger.error("C1 rank-style continue verify failed room=%s next_match=%s", room_id, next_match.get("id"))
                flash("Chưa chuyển được phòng sang trận tiếp theo. Hãy tải lại và thử lại.", "warning")
                return redirect(url_for("room_detail", room_id=room_id))
            cache_delete("_rz_rooms_all")
            ttl_cache_delete("rooms_raw")
            flash("Đã chuyển sang trận tiếp theo. Đội khách hãy bấm Sẵn Sàng; sau đó Chủ phòng mới Quay đội.", "info")
            return redirect(url_for("room_detail", room_id=room_id))

        if user["id"] not in [room["host_user_id"], room["guest_user_id"]]:
            flash("Bạn không thuộc phòng này.", "danger")
            return redirect(url_for("dashboard"))

        if room["status"] != "confirmed":
            flash("Chỉ có thể đá tiếp sau khi kết quả trận trước đã được xác nhận.", "warning")
            return redirect(url_for("room_detail", room_id=room_id))

        host_active_room = active_room_for_user(room["host_user_id"], exclude_room_id=room_id)
        guest_active_room = active_room_for_user(room["guest_user_id"], exclude_room_id=room_id)
        host_active_match = active_match_for_user(room["host_user_id"])
        guest_active_match = active_match_for_user(room["guest_user_id"])
        if host_active_room or guest_active_room or host_active_match or guest_active_match:
            flash("Một trong hai người đang có phòng hoặc trận khác nên chưa thể đá tiếp từ phòng này.", "warning")
            return redirect(url_for("room_detail", room_id=room_id))

        is_host = user["id"] == room["host_user_id"]
        my_ready_note = REMATCH_HOST_READY_NOTE if is_host else REMATCH_GUEST_READY_NOTE
        opponent_ready_note = REMATCH_GUEST_READY_NOTE if is_host else REMATCH_HOST_READY_NOTE
        current_note = room.get("note") or ""

        if current_note in {REMATCH_HOST_DECLINED_NOTE, REMATCH_GUEST_DECLINED_NOTE}:
            flash("Đối thủ đã chọn không đá tiếp. Phiên đá tiếp đã kết thúc.", "warning")
            return redirect(url_for("dashboard"))

        if current_note == REMATCH_EXPIRED_NOTE:
            flash("Yêu cầu đá tiếp đã hết hạn sau 60 giây.", "warning")
            return redirect(url_for("dashboard"))

        if current_note == my_ready_note:
            flash("Bạn đã chọn Đá tiếp. Đang chờ đối thủ xác nhận.", "warning")
            return redirect(url_for("room_detail", room_id=room_id))

        # Giữ nguyên chế độ Rank đã chọn ở trận trước cho toàn bộ lượt đá tiếp.
        previous_rank_mode = room.get("team_tier") or SMART_RANDOM_MODE
        if not system_feature_enabled("rank_standard_enabled"):
            previous_rank_mode = FRIENDLY_RANDOM3_MODE
        previous_mode_label = (
            "Random 3 chọn 1" if previous_rank_mode == FRIENDLY_RANDOM3_MODE
            else "Random Selection Match" if previous_rank_mode == RANDOM_SELECTION_MATCH_MODE
            else "Random"
        )
        rematch_locked_note = f"__RANK_MODE_LOCKED__|{previous_rank_mode}"

        # Khách bấm Đá tiếp: khách được tính là sẵn sàng ngay, không cần chọn lại chế độ.
        if not is_host:
            execute_query(
                db.table("match_rooms").update({
                    "host_team": None,
                    "guest_team": None,
                    "host_team_overall": None,
                    "guest_team_overall": None,
                    "host_team_logo_url": None,
                    "guest_team_logo_url": None,
                    "host_team_league": None,
                    "guest_team_league": None,
                    "guest_ready": True,
                    "status": "waiting_ready",
                    "match_id": None,
                    "host_score": None,
                    "guest_score": None,
                    "submitted_by_id": None,
                    "confirmed_by_id": None,
                    "match_mode": MATCH_MODE_RANKED,
                    "team_tier": previous_rank_mode,
                    "note": rematch_locked_note,
                    "state_expires_at": None,
                    "updated_at": now_iso(),
                }).eq("id", room_id).eq("status", "confirmed"),
                "room_guest_rematch_ready_for_ranked_random",
            )
            flash(f"Bạn đã chọn Đá tiếp. Giữ nguyên chế độ {previous_mode_label}; Chủ phòng có thể quay quân.", "success")
            return redirect(url_for("room_detail", room_id=room_id))

        # Người đầu tiên bấm Đá tiếp: ghi nhận ngay trong phòng, không tạo lời mời mới.
        if current_note != opponent_ready_note:
            execute_query(
                db.table("match_rooms").update({
                    "note": my_ready_note,
                    "state_expires_at": future_iso(REMATCH_TIMEOUT_SECONDS),
                    "updated_at": now_iso(),
                }).eq("id", room_id).eq("status", "confirmed"),
                "room_rematch_first_ready",
            )
            flash("Bạn đã chọn Đá tiếp. Đang chờ đối thủ bấm Đá tiếp.", "success")
            return redirect(url_for("room_detail", room_id=room_id))

        # Người thứ hai đồng ý: dùng lại chính phòng hiện tại và đưa cả hai về bước random đội.
        host_active_room = active_room_for_user(room["host_user_id"], exclude_room_id=room_id)
        guest_active_room = active_room_for_user(room["guest_user_id"], exclude_room_id=room_id)
        if host_active_room or guest_active_room:
            flash("Một trong hai người đang có phòng khác chưa hoàn tất nên chưa thể đá tiếp.", "warning")
            return redirect(url_for("room_detail", room_id=room_id))

        # Hủy lời mời chờ cũ giữa hai người (nếu còn từ phiên bản trước), tránh hiện thông báo thừa.
        for from_user_id, to_user_id in [
            (room["host_user_id"], room["guest_user_id"]),
            (room["guest_user_id"], room["host_user_id"]),
        ]:
            try:
                db.table("match_invites").update({
                    "status": "cancelled",
                    "updated_at": now_iso(),
                }).eq("from_user_id", from_user_id).eq("to_user_id", to_user_id).eq("status", "pending").execute()
            except Exception as exc:
                print(f"Rematch pending invite cleanup warning: {exc}")

        execute_query(
            db.table("match_rooms").update({
                "host_team": None,
                "guest_team": None,
                "guest_ready": True,
                "status": "waiting_ready",
                "match_id": None,
                "host_score": None,
                "guest_score": None,
                "submitted_by_id": None,
                "confirmed_by_id": None,
                "team_tier": previous_rank_mode,
                "note": rematch_locked_note,
                "state_expires_at": None,
                "updated_at": now_iso(),
            }).eq("id", room_id).eq("status", "confirmed"),
            "room_rematch_reset_same_room",
        )

        flash(f"Cả hai đã đồng ý đá tiếp. Giữ nguyên chế độ {previous_mode_label}; đang chờ Chủ phòng quay quân.", "success")
        return redirect(url_for("room_detail", room_id=room_id))


    @app.route("/room/<room_id>/rematch-decline", methods=["POST"])
    @login_required
    def room_rematch_decline(room_id):
        user = current_user()
        room = get_room(room_id)

        if not room:
            flash("Không tìm thấy phòng.", "danger")
            return redirect(url_for("dashboard"))

        # C1/tournament rooms have their own match lifecycle. Never let the generic
        # Rank rematch flow normalize a tournament room back to ranked mode.
        room_note = str(room.get("note") or "")
        is_tournament_room = room_note.startswith("TOURNAMENT_ROOM|") or str(room.get("match_mode") or "").lower() == "tournament"
        if is_tournament_room:
            try:
                import json
                meta = json.loads(room_note[len("TOURNAMENT_ROOM|"):]) if room_note.startswith("TOURNAMENT_ROOM|") else {}
            except Exception:
                meta = {}
            tournament_id = str(meta.get("tournament_id") or "")
            flash("Trận C1 đã hoàn tất. Hãy mở trận tiếp theo từ mục Đối thủ/Phòng thi đấu của giải.", "info")
            if tournament_id:
                return redirect(url_for("tournament_detail", tournament_id=tournament_id) + "#rooms")
            return redirect(url_for("tournaments"))

        if user["id"] not in [room["host_user_id"], room["guest_user_id"]]:
            flash("Bạn không thuộc phòng này.", "danger")
            return redirect(url_for("dashboard"))

        if room["status"] != "confirmed":
            flash("Chỉ có thể từ chối đá tiếp sau khi trận trước đã hoàn tất.", "warning")
            return redirect(url_for("room_detail", room_id=room_id))

        is_host = user["id"] == room["host_user_id"]
        my_ready_note = REMATCH_HOST_READY_NOTE if is_host else REMATCH_GUEST_READY_NOTE
        opponent_ready_note = REMATCH_GUEST_READY_NOTE if is_host else REMATCH_HOST_READY_NOTE
        decline_note = REMATCH_HOST_DECLINED_NOTE if is_host else REMATCH_GUEST_DECLINED_NOTE
        current_note = room.get("note") or ""

        if current_note in {REMATCH_HOST_DECLINED_NOTE, REMATCH_GUEST_DECLINED_NOTE}:
            flash("Phiên đá tiếp đã được từ chối trước đó.", "warning")
            return redirect(url_for("dashboard"))

        # Cho phép rời phòng ngay sau khi kết quả đã xác nhận, kể cả chưa có ai bấm Đá tiếp.

        execute_query(
            db.table("match_rooms").update({
                "note": decline_note,
                "state_expires_at": None,
                "updated_at": now_iso(),
            }).eq("id", room_id).eq("status", "confirmed"),
            "room_rematch_declined",
        )

        flash("Bạn đã rời phòng và trở về sảnh chính.", "success")
        return redirect(url_for("dashboard"))

