"""Route extracted from app.py without changing endpoint behavior.

Dependencies are injected from the application context at registration time to
avoid circular imports and preserve the existing business logic.
"""

def register_routes(context):
    globals().update(context)

    @app.route("/huong-dan")
    @login_required
    def guide():
        return render_template("guide.html")

    @app.route("/dashboard")
    @login_required
    def dashboard():
        if not dashboard_is_enabled(get_system_features()):
            return redirect(url_for("ranking"))
        user = current_user()
        try:
            player_rows = list_players()
            presence_rows = list_players()
            matches = list_matches()
            rooms = list_rooms()
            invite_count = current_pending_invite_count()
        except Exception:
            player_rows, presence_rows, matches, rooms = [], [], [], []
            invite_count = 0
            flash("Dữ liệu đang tải chậm, vui lòng thử lại sau vài giây.", "warning")

        invisible_ids = get_invisible_player_ids(force=True)
        player_rows = filter_players_for_viewer(player_rows, user, invisible_ids)
        presence_rows = filter_players_for_viewer(presence_rows, user, invisible_ids)

        me = next((player for player in player_rows if player.get("id") == user.get("id")), dict(user))
        my_position = next((index for index, player in enumerate(player_rows, 1) if player.get("id") == user.get("id")), None)
        my_rank_info = get_player_rank_info(me, my_position)
        total = calculated_total_matches(me)
        wins = int(me.get("wins", 0) or 0)
        me["winrate"] = round((wins / total) * 100, 1) if total else 0

        my_matches = [
            decorate_match_for_view(match, user.get("id"))
            for match in matches
            if user.get("id") in {match.get("player1_id"), match.get("player2_id")}
        ]
        recent_matches = my_matches[:5]

        active_room = active_room_for_user(user.get("id"))
        attention = {
            "invites": invite_count,
            "has_room": bool(active_room),
            "waiting_confirm": len([m for m in matches if m.get("status") == "waiting_confirm" and user.get("id") in {m.get("player1_id"), m.get("player2_id")}]),
            "disputed": len([m for m in matches if m.get("status") == "disputed" and user.get("id") in {m.get("player1_id"), m.get("player2_id")}]),
        }

        activity_map = build_player_activity_map(rooms, matches)
        online_players = [p for p in presence_rows if p.get("is_online") and p.get("id") != user.get("id")]
        solo_room_user_ids = {
            str(room.get("host_user_id"))
            for room in rooms
            if is_solo_waiting_room(room, room.get("host_user_id"))
        }
        for player in online_players:
            status = activity_map.get(player.get("id"), {"code": "ready", "label": "Sẵn sàng"})
            player["activity_code"] = status["code"]
            player["activity_label"] = status["label"]
            player["can_receive_invite"] = bool(
                status["code"] == "ready" or str(player.get("id")) in solo_room_user_ids
            )
            player["is_busy"] = not player["can_receive_invite"]

        online_players.sort(key=lambda p: (p.get("is_busy", False), _player_ranking_sort_key(p)))

        return render_template(
            "dashboard.html",
            me=me,
            my_position=my_position,
            my_rank_info=my_rank_info,
            attention=attention,
            online_players=online_players,
            recent_matches=recent_matches,
        )

    @app.route("/rooms/create", methods=["POST"])
    @login_required
    def create_open_room():
        user = current_user()
        limit_message = daily_rank_block_message(user.get("id"))
        if limit_message:
            flash(limit_message, "warning")
            return redirect(url_for("dashboard"))
        cleanup_duplicate_waiting_rooms(user["id"])
        existing = active_room_for_user(user["id"])
        if existing:
            existing_note = str(existing.get("note") or "")
            is_existing_tournament = existing_note.startswith("TOURNAMENT_ROOM|") or str(existing.get("match_mode") or "").lower() == "tournament"
            if not is_existing_tournament:
                return redirect(url_for("room_detail", room_id=existing["id"]))

            # Phòng thường và Phòng C1 là hai luồng độc lập. Nếu chỉ còn một phòng C1
            # trống do chính người dùng tạo, tự đóng phòng trống đó để chuyển sang Rank.
            # Không tự phá phòng C1 đã có đối thủ/đang thi đấu.
            can_close_empty_c1 = (
                str(existing.get("host_user_id") or "") == str(user.get("id") or "")
                and not existing.get("guest_user_id")
                and str(existing.get("status") or "") == "waiting_ready"
            )
            if can_close_empty_c1:
                execute_query(
                    db.table("match_rooms").update({
                        "status": "cancelled",
                        "updated_at": now_iso(),
                    }).eq("id", existing.get("id")),
                    "switch_c1_to_normal_room",
                )
            else:
                flash("Bạn đang có Phòng đấu C1 đang hoạt động. Hãy kết thúc hoặc thoát phòng C1 trước khi vào Phòng đấu thường.", "warning")
                return redirect(url_for("rooms"))
        if active_match_for_user(user["id"]):
            flash("Bạn đang có trận chưa hoàn tất.", "warning")
            return redirect(url_for("dashboard"))

        room = execute_query(
            db.table("match_rooms").insert({
                "invite_id": None,
                "host_user_id": user["id"],
                "guest_user_id": None,
                "team_tier": (SMART_RANDOM_MODE if system_feature_enabled("rank_standard_enabled") else FRIENDLY_RANDOM3_MODE),
                "match_mode": MATCH_MODE_RANKED,
                "friendly_tier": "A",
                "status": "waiting_ready",
                "guest_ready": False,
                "note": "Phòng mở đang chờ chủ phòng mời đối thủ.",
                "state_expires_at": None,
                "updated_at": now_iso(),
            }),
            "create_open_room",
        ).data[0]
        # Chống double-click / hai request chạy đồng thời trên nhiều Vercel instance.
        cleanup_duplicate_waiting_rooms(user["id"])
        canonical_room = active_room_for_user(user["id"])
        if canonical_room:
            room = canonical_room
        flash("Đã tạo phòng đấu. Bạn có thể mời đối thủ từ danh sách Players.", "success")
        return redirect(url_for("room_detail", room_id=room["id"]))

    @app.route("/players")
    @login_required
    def players():
        player_rows = invite_visible_players(current_user(), include_admin=False, force_invisible_refresh=True)
        rooms = list_rooms()
        activity_map = build_player_activity_map(rooms=rooms)
        solo_room_user_ids = {
            str(room.get("host_user_id"))
            for room in rooms
            if is_solo_waiting_room(room, room.get("host_user_id"))
        }
        viewer = current_user()
        viewer_room = active_room_for_user(viewer.get("id")) if viewer else None
        viewer_can_invite = bool(
            viewer
            and not active_match_for_user(viewer.get("id"))
            and (not viewer_room or is_solo_waiting_room(viewer_room, viewer.get("id")))
        )
        query = (request.args.get("q") or "").strip().casefold()
        status_filter = (request.args.get("status") or "all").strip()

        for player in player_rows:
            if not player.get("is_online"):
                status = {"code": "offline", "label": "Offline"}
            else:
                status = activity_map.get(player.get("id"), {"code": "ready", "label": "Sẵn sàng"})
            player["activity_code"] = status["code"]
            player["activity_label"] = status["label"]
            player["is_busy"] = status["code"] not in {"ready", "offline"}
            player["can_receive_invite"] = bool(
                player.get("is_online")
                and (status["code"] == "ready" or str(player.get("id")) in solo_room_user_ids)
            )
            total = calculated_total_matches(player)
            player["winrate"] = round((int(player.get("wins", 0) or 0) / total) * 100, 1) if total else 0
            player["last_seen_display"] = format_vn_datetime(player.get("last_seen_at"))

        viewer_is_admin = is_admin_user(viewer)
        if query:
            player_rows = [
                player for player in player_rows
                if query in str(player.get("display_name") or "").casefold()
                or (viewer_is_admin and query in str(player.get("username") or "").casefold())
            ]
        if status_filter != "all":
            player_rows = [player for player in player_rows if player.get("activity_code") == status_filter]

        status_order = {"ready": 0, "in_room": 1, "waiting_confirm": 2, "playing": 3, "offline": 4}
        player_rows.sort(key=lambda p: (status_order.get(p.get("activity_code"), 9), _player_ranking_sort_key(p)))
        return render_template(
            "players.html",
            players=player_rows,
            q=request.args.get("q", ""),
            status_filter=status_filter,
            viewer_can_invite=viewer_can_invite,
            viewer_is_admin=viewer_is_admin,
        )

