"""Route extracted from app.py without changing endpoint behavior.

Dependencies are injected from the application context at registration time to
avoid circular imports and preserve the existing business logic.
"""

def register_routes(context):
    globals().update(context)

    @app.route("/ranking")
    @app.route("/bxh")
    def ranking():
        user = current_user()
        if not user and not system_feature_enabled("public_ranking_enabled"):
            flash("Đăng ký để tham gia Championship Ranking", "warning")
            return redirect(url_for("login"))

        current_season = get_current_season()
        current_sn = int(current_season.get("season_number") or 1)
        try:
            requested_sn = int(request.args.get("season") or current_sn)
        except (TypeError, ValueError):
            requested_sn = current_sn
        if requested_sn < 1 or requested_sn > current_sn:
            requested_sn = current_sn
        viewing_historical_season = requested_sn != current_sn

        try:
            all_player_rows = list_players()
        except Exception as exc:
            print(f"ranking list_players warning: {exc}")
            all_player_rows = []

        try:
            ranking_activity_matches = list_matches()
        except Exception as exc:
            print(f"ranking activity matches warning: {exc}")
            ranking_activity_matches = []

        invisible_ids = get_invisible_player_ids()
        eligibility_by_id = {}
        current_ranking_status = None

        # V1.4.20: nguồn dữ liệu BXH chính thức là season_player_stats theo season_number.
        try:
            season_stats_result = execute_query(
                db.table("season_player_stats").select("*").eq("season_number", requested_sn),
                "ranking_season_player_stats", attempts=2,
            )
            season_stats_rows = [dict(x) for x in (season_stats_result.data or [])]
        except Exception as exc:
            print(f"ranking season_player_stats warning: {exc}")
            season_stats_rows = []
        season_stats_by_id = {str(x.get("user_id")): x for x in season_stats_rows if x.get("user_id")}

        if viewing_historical_season:
            # Season đã đóng: đọc đúng điểm + vị trí đã đóng băng từ snapshot,
            # tuyệt đối không lấy users.rank_points của season hiện tại.
            try:
                snap_result = execute_query(
                    db.table("rank_season_snapshots").select("snapshot_data,created_at").eq("season_number", requested_sn).limit(1),
                    "ranking_historical_snapshot", attempts=2,
                )
                snapshot_rows = list((snap_result.data or [{}])[0].get("snapshot_data") or []) if snap_result.data else []
            except Exception as exc:
                print(f"ranking historical snapshot warning: {exc}")
                snapshot_rows = []

            selected_season = next((x for x in get_season_history(50) if int(x.get("season_number") or 0) == requested_sn), None) or {
                "season_number": requested_sn, "name": f"Season {requested_sn}", "status": "closed", "placement_matches": 5
            }
            reconstructed_stats = _build_season_stats_map(ranking_activity_matches, selected_season)
            by_id = {str(p.get("id")): dict(p) for p in all_player_rows}
            archived = []
            # Snapshot quyết định ai + vị trí cuối mùa; season_player_stats quyết định stats của mùa.
            for row in snapshot_rows:
                uid = str(row.get("user_id") or "")
                stat = dict(season_stats_by_id.get(uid) or {})
                base = dict(by_id.get(uid) or {})
                if not base:
                    base = {"id": uid, "username": stat.get("username") or row.get("display_name") or "player", "display_name": stat.get("display_name") or row.get("display_name") or "Player"}
                base["rank_points"] = int(stat.get("rank_points") if stat else row.get("rank_points") or 0)
                base["position"] = int(stat.get("final_rank") or row.get("position") or 0)
                base["rank_info"] = get_player_rank_info(base, base["position"])
                rebuilt = reconstructed_stats.get(uid, {})
                base["wins"] = int(stat.get("wins") if stat else row.get("wins", rebuilt.get("wins", 0)) or 0)
                base["draws"] = int(stat.get("draws") if stat else row.get("draws", rebuilt.get("draws", 0)) or 0)
                base["losses"] = int(stat.get("losses") if stat else row.get("losses", rebuilt.get("losses", 0)) or 0)
                base["recent_form"] = list(stat.get("recent_form") if stat else row.get("recent_form", rebuilt.get("recent_form", [])) or [])[:5]
                total = base["wins"] + base["draws"] + base["losses"]
                base["total_matches"] = total
                base["winrate"] = round((base["wins"] / total) * 100, 1) if total else 0
                base["record_text"] = f'{base["wins"]}T • {base["draws"]}H • {base["losses"]}B'
                archived.append(base)
            archived.sort(key=lambda x: int(x.get("position") or 999999))
            player_rows = filter_players_for_viewer(archived, user, invisible_ids, preserve_deleted=True)
            if not (is_admin_user(user) or (user and str(user.get("id")) in invisible_ids)):
                for pos, item in enumerate(player_rows, 1):
                    item["position"] = pos
                    item["rank_info"] = get_player_rank_info(item, pos)
            current_player = next((p for p in player_rows if user and str(p.get("id")) == str(user.get("id"))), None)
            current_position = current_player.get("position") if current_player else None
        else:
            latest_activity_map = _latest_ranking_activity_map(ranking_activity_matches)
            ranking_now = now_dt()
            # Merge record Season hiện tại vào user profile; users chỉ còn là lớp tương thích.
            for player in all_player_rows:
                stat = season_stats_by_id.get(str(player.get("id")))
                if stat:
                    for key in ("rank_points", "wins", "draws", "losses", "total_matches"):
                        player[key] = int(stat.get(key) or 0)
                    player["recent_form"] = list(stat.get("recent_form") or [])[:5]
            season_match_count_map = {str(p.get("id")): int(p.get("total_matches") or 0) for p in all_player_rows}
            eligible_player_rows = []
            for player in all_player_rows:
                if str(player.get("account_status") or "approved").lower() == "deleted":
                    continue
                eligibility = season_ranking_eligibility(
                    player, season_match_count_map.get(str(player.get("id")), 0),
                    latest_activity_map.get(str(player.get("id"))), now=ranking_now, season=current_season,
                )
                eligibility_by_id[str(player.get("id"))] = eligibility
                if eligibility.get("visible"):
                    eligible_player_rows.append(player)
            eligible_player_rows.sort(key=_player_ranking_sort_key)
            global_position_map = {str(p.get("id")): pos for pos, p in enumerate(eligible_player_rows, 1)}
            player_rows = filter_players_for_viewer(eligible_player_rows, user, invisible_ids)
            viewer_is_invisible = bool(user and str(user.get("id")) in invisible_ids)
            preserve_global_positions = bool(is_admin_user(user) or viewer_is_invisible)
            for visible_position, player in enumerate(player_rows, 1):
                position = global_position_map.get(str(player.get("id")), visible_position) if preserve_global_positions else visible_position
                player["position"] = position
                player["rank_info"] = get_player_rank_info(player, position)
            current_player = next((p for p in player_rows if user and str(p.get("id")) == str(user.get("id"))), None)
            current_position = current_player.get("position") if current_player else None
            current_ranking_status = eligibility_by_id.get(str(user.get("id"))) if user else None
            selected_season = current_season

        query = (request.args.get("q") or "").strip().casefold()
        rank_filter = (request.args.get("rank") or "all").strip()
        filtered = player_rows
        if query:
            filtered = [p for p in filtered if query in str(p.get("display_name") or "").casefold() or query in str(p.get("username") or "").casefold()]
        if rank_filter != "all":
            filtered = [p for p in filtered if p.get("rank_info", {}).get("slug") == rank_filter]

        if not viewing_historical_season:
            # V1.4.20: BXH current đọc trực tiếp season_player_stats của requested season.
            fallback_stats = None
            for player in filtered[:100]:
                stat = season_stats_by_id.get(str(player.get("id")))
                if not stat:
                    # Chỉ fallback khi migration SQL chưa chạy/record chưa tồn tại.
                    fallback_stats = fallback_stats or _build_season_stats_map(ranking_activity_matches, current_season)
                    stat = fallback_stats.get(str(player.get("id")), {})
                wins = int(stat.get("wins") or 0); draws = int(stat.get("draws") or 0); losses = int(stat.get("losses") or 0)
                total_matches = int(stat.get("total_matches") or (wins + draws + losses))
                player["wins"], player["draws"], player["losses"] = wins, draws, losses
                player["total_matches"] = total_matches
                player["winrate"] = round((wins / total_matches) * 100, 1) if total_matches else 0
                player["record_text"] = f"{wins}T • {draws}H • {losses}B"
                player["recent_form"] = list(stat.get("recent_form") or [])[:5]

        seasons = get_season_history(50)
        known = {int(x.get("season_number") or 0) for x in seasons}
        if current_sn not in known:
            seasons.insert(0, current_season)
        seasons.sort(key=lambda x: int(x.get("season_number") or 0), reverse=True)

        template_name = "ranking.html" if user else "public_ranking.html"
        return render_template(
            template_name, players=filtered, current_player=current_player,
            current_position=current_position, current_ranking_status=current_ranking_status,
            ranking_qualify_matches=int(current_season.get("placement_matches") or 5),
            current_rank_season=current_season, selected_rank_season=selected_season,
            selected_season_number=requested_sn, rank_seasons=seasons,
            viewing_historical_season=viewing_historical_season,
            ranking_inactive_hide_days=RANKING_INACTIVE_HIDE_DAYS,
            q=request.args.get("q", ""), rank_filter=rank_filter,
        )

