"""Internal tournament competition partition extracted from the legacy monolith.

Registered only through :mod:`modules.tournament_competition`.
"""

def register_rewards(context):
    globals().update(context)

    @app.post('/admin/tournaments/<tournament_id>/stage1/finish')
    @login_required
    @admin_required
    def admin_tournament_stage1_finish(tournament_id):
        force=request.form.get("force")=="1"
        pending=[m for m in _matches(tournament_id,"stage1") if m.get("status")!="completed"]
        if pending and not force:
            flash(f"GĐ1 còn {len(pending)} trận chưa hoàn thành. Chỉ kết thúc sớm khi 100% trận xong, hoặc dùng kết thúc sau gia hạn.","warning"); return redirect_admin("tournaments")
        if pending and force:
            for m in pending:
                execute_query(db.table("tournament_matches").update({"status":"disputed","updated_at":now_iso()}).eq("id",m.get("id")),"ops_s1_pending_btc",attempts=2)
        execute_query(db.table("tournament_stages").update({"status":"completed","updated_at":now_iso()}).eq("tournament_id",tournament_id).eq("stage_code","stage1"),"ops_s1_finish",attempts=2)
        # Kết thúc GĐ1 chỉ chuyển GĐ2 sang trạng thái chuẩn bị; không mở thi đấu.
        execute_query(db.table("tournament_stages").update({"status":"pending","updated_at":now_iso()}).eq("tournament_id",tournament_id).eq("stage_code","league"),"ops_league_prepare_after_s1",attempts=2)
        flash("Đã kết thúc GĐ1. GĐ2 CHƯA bắt đầu: hãy trao thưởng, chia/khóa Pot, chốt CLB và công bố đối thủ.","success"); return redirect_admin("tournaments")

    LEAGUE_TOP3_REROLL_KEY = "league_top3_club_reroll_v1"

    def _grant_league_top3_reroll_tickets(tournament_id):
        ranking=_combined_ranking(tournament_id)
        winners=ranking[:3]
        old=_setting(tournament_id,LEAGUE_TOP3_REROLL_KEY,{}) or {}
        entries=dict(old.get("entries") or {})
        for pos,row in enumerate(winners,1):
            uid=str(row.get("user_id") or "")
            if not uid: continue
            existing=entries.get(uid) or {}
            if not existing:
                entries[uid]={
                    "rank":pos,"tickets_total":1,"tickets_remaining":1,"skipped_club_ids":[],
                    "history":[],"granted_at":now_iso(),
                }
                try:
                    create_user_notification(
                        uid,
                        f"🎟 Top {pos} GĐ2 · Nhận 1 vé Random lại CLB",
                        "Bạn được 1 vé Random lại CLB trước vòng Knockout. CLB đã bỏ sẽ không xuất hiện lại cho bạn.",
                        "/tournaments",
                        "c1_league_top3_reroll",
                    )
                except Exception:
                    pass
        state={"entries":entries,"updated_at":now_iso(),"source":"combined_ranking_top3"}
        execute_query(db.table("tournament_settings").upsert({
            "tournament_id":tournament_id,"setting_key":LEAGUE_TOP3_REROLL_KEY,
            "setting_value":state,"updated_at":now_iso(),
        },on_conflict="tournament_id,setting_key"),"ops_league_top3_reroll_grant",attempts=2)
        return state

    @app.post('/tournaments/<tournament_id>/league-top3/reroll-club')
    @login_required
    def tournament_league_top3_reroll_club(tournament_id):
        uid=str((current_user() or {}).get("id") or "")
        member=_member(tournament_id,uid)
        if not member:
            flash("Bạn không thuộc giải đấu này.","error"); return redirect(url_for("tournaments"))
        state=_setting(tournament_id,LEAGUE_TOP3_REROLL_KEY,{}) or {}
        entries=dict(state.get("entries") or {})
        entry=dict(entries.get(uid) or {})
        if int(entry.get("tickets_remaining") or 0)<=0:
            flash("Bạn không còn vé Random lại CLB GĐ2.","warning"); return redirect(url_for("tournaments")+"#ranking")
        old_name=str(member.get("fixed_club_name") or "")
        if not old_name:
            flash("Bạn chưa có CLB để Random lại.","warning"); return redirect(url_for("tournaments")+"#ranking")
        old_club,_=_one(db.table("tournament_clubs").select("*").eq("tournament_id",tournament_id).eq("name",old_name),"ops_league_reroll_old_club")
        skipped=set(str(x) for x in (entry.get("skipped_club_ids") or []))
        if old_club: skipped.add(str(old_club.get("id")))
        pool=_available_clubs(tournament_id,skipped)
        if not pool:
            flash("Không còn CLB trống phù hợp để Random lại.","error"); return redirect(url_for("tournaments")+"#ranking")
        new_club=random.choice(pool)
        # Chỉ nhả CLB cũ sau khi đã chắc chắn có CLB mới để nhận.
        if old_club:
            execute_query(db.table("tournament_clubs").update({"selected_by":None,"selected_at":None}).eq("id",old_club.get("id")).eq("selected_by",uid),"ops_league_reroll_release_old",attempts=2)
        _club_assign(tournament_id,uid,new_club)
        entry["tickets_remaining"]=int(entry.get("tickets_remaining") or 0)-1
        entry["skipped_club_ids"]=list(skipped)
        entry.setdefault("history",[]).append({"at":now_iso(),"from":old_name,"to":new_club.get("name")})
        entries[uid]=entry; state["entries"]=entries; state["updated_at"]=now_iso()
        execute_query(db.table("tournament_settings").upsert({
            "tournament_id":tournament_id,"setting_key":LEAGUE_TOP3_REROLL_KEY,"setting_value":state,"updated_at":now_iso(),
        },on_conflict="tournament_id,setting_key"),"ops_league_top3_reroll_use",attempts=2)
        flash(f"Đã dùng 1 vé: {old_name} → {new_club.get('name')}. CLB {old_name} sẽ không xuất hiện lại cho bạn.","success")
        return redirect(url_for("tournaments")+"#ranking")

    @app.post('/admin/tournaments/<tournament_id>/league/finish')
    @login_required
    @admin_required
    def admin_tournament_league_finish(tournament_id):
        force=request.form.get("force")=="1"
        stages,_=_rows(db.table("tournament_stages").select("stage_code,status").eq("tournament_id",tournament_id),"ops_league_finish_stage_gate")
        if not any(row.get("stage_code")=="league" and row.get("status")=="open" for row in stages):
            flash("GĐ2 chưa mở hoặc đã kết thúc; không thể khóa.","error"); return redirect_admin("tournaments")
        league_matches=_matches(tournament_id,"league")
        if len(league_matches)!=32:
            flash(f"Không thể kết thúc GĐ2: cần đúng 32 trận, hiện có {len(league_matches)}.","error")
            return redirect_admin("tournaments")
        pending=[m for m in league_matches if m.get("status")!="completed"]
        if pending and not force:
            flash(f"League Phase còn {len(pending)} trận chưa hoàn thành.","warning"); return redirect_admin("tournaments")
        if pending:
            flash("Phải xác nhận đủ 32 kết quả trước khi kết thúc GĐ2. Hãy xử lý trận thiếu tại Admin.","error"); return redirect_admin("tournaments")
        execute_query(db.table("tournament_stages").update({"status":"completed","updated_at":now_iso()}).eq("tournament_id",tournament_id).eq("stage_code","league"),"ops_league_finish",attempts=2)
        execute_query(db.table("tournament_stages").update({"status":"open","updated_at":now_iso()}).eq("tournament_id",tournament_id).eq("stage_code","knockout"),"ops_ko_open",attempts=2)
        _grant_league_top3_reroll_tickets(tournament_id)
        flash("Đã khóa GĐ2. Top 1–3 BXH tổng nhận mỗi người 1 vé Random lại CLB; Top 8 sẵn sàng vào thẳng Knockout.","success"); return redirect_admin("tournaments")

    @app.post('/admin/tournaments/<tournament_id>/knockout/generate')
    @login_required
    @admin_required
    def admin_tournament_knockout_generate(tournament_id):
        ranking=_combined_ranking(tournament_id)
        if len(ranking)<8:
            flash("Chưa đủ 8 HLV để sinh Knockout.","error"); return redirect_admin("tournaments")
        existing=_matches(tournament_id,"knockout")
        if any(m.get("status")=="completed" for m in existing):
            flash("Knockout đã có kết quả, không thể sinh lại.","error"); return redirect_admin("tournaments")
        if existing:
            execute_query(db.table("tournament_matches").delete().eq("tournament_id",tournament_id).eq("stage_code","knockout"),"ops_ko_clear",attempts=2)
        ids=[str(r.get("user_id")) for r in ranking[:8]]
        state={"use_playoff":False,"completed":False,"champion_user_id":None,"created_at":now_iso(),"direct_top8":ids,"current_round":"qf"}
        for i in range(4):
            _insert_ko_pair(tournament_id,"qf",ids[i],ids[-(i+1)],True)
        execute_query(db.table("tournament_settings").upsert({"tournament_id":tournament_id,"setting_key":"knockout_flow","setting_value":state,"updated_at":now_iso()},on_conflict="tournament_id,setting_key"),"ops_ko_generate_state",attempts=2)
        execute_query(db.table("tournament_stages").update({"status":"open","updated_at":now_iso()}).eq("tournament_id",tournament_id).eq("stage_code","knockout"),"ops_ko_generate_open",attempts=2)
        flash("Đã sinh Knockout: Top 8 vào thẳng Tứ kết · không Play-off.","success"); return redirect_admin("tournaments")

    @app.post('/admin/tournaments/<tournament_id>/knockout/match')
    @login_required
    @admin_required
    def admin_tournament_knockout_match(tournament_id):
        home=str(request.form.get("home_user_id") or ""); away=str(request.form.get("away_user_id") or "")
        rnd=request.form.get("round_code") or "playoff"; two=request.form.get("two_legged")=="1"
        if not home or not away or home==away: flash("Cặp Knockout không hợp lệ.","error"); return redirect_admin("tournaments")
        group=str(uuid.uuid4()) if two else None
        legs=[1,2] if two else [1]
        for leg in legs:
            h,a=(home,away) if leg==1 else (away,home)
            execute_query(db.table("tournament_matches").insert({"tournament_id":tournament_id,"stage_code":"knockout","round_code":rnd,"leg_no":leg,"aggregate_group":group,"home_user_id":h,"away_user_id":a,"status":"pending","created_at":now_iso(),"updated_at":now_iso()}),"ops_ko_insert",attempts=2)
        flash("Đã tạo cặp Knockout hai lượt." if two else "Đã tạo cặp Knockout.","success"); return redirect_admin("tournaments")

    STAGE1_EARLY_REWARD_KEY = "stage1_early_completion_rewards_v1"

    def _stage1_early_reward_amount(rank):
        rank=int(rank or 0)
        if rank==1:
            return {"zcoin":1000,"lucky_box":2}
        if rank in {2,3}:
            return {"zcoin":800,"lucky_box":1}
        return {"zcoin":0,"lucky_box":0}

    def _stage1_early_reward_state(tournament_id):
        return _setting(tournament_id,STAGE1_EARLY_REWARD_KEY,{}) or {}

    @app.post('/admin/tournaments/<tournament_id>/stage1/early-rewards/grant')
    @login_required
    @admin_required
    def admin_tournament_stage1_early_rewards_grant(tournament_id):
        """Trao thưởng Top hoàn thành sớm GĐ1, idempotent theo tournament/user/rank."""
        actor=current_user() or {}
        tour=_tour(tournament_id)
        if not tour:
            flash("Không tìm thấy giải đấu.","error")
            return redirect_admin("tournaments")

        ranking=_completion_ranking(tournament_id)
        winners=[
            row for row in ranking
            if row.get("early_eligible") and int(row.get("finish_rank") or 0) in {1,2,3}
        ]
        if not winners:
            flash("Chưa có HLV nào đủ điều kiện nhận thưởng hoàn thành sớm GĐ1.","warning")
            return redirect_admin("tournaments")

        state=_stage1_early_reward_state(tournament_id)
        granted=dict(state.get("granted") or {})
        newly_rewarded=[]
        already_rewarded=[]

        for row in winners:
            uid=str(row.get("user_id") or "")
            rank=int(row.get("finish_rank") or 0)
            reward=_stage1_early_reward_amount(rank)
            if not uid or reward["zcoin"]<=0:
                continue

            record=granted.get(uid) or {}
            # Nếu state đã ghi complete thì bỏ qua toàn bộ notification/log phụ.
            if record.get("status")=="granted":
                already_rewarded.append(row)
                continue

            z_key=f"c1:{tournament_id}:stage1:early:{uid}:rank:{rank}:zcoin"
            box_key=f"c1:{tournament_id}:stage1:early:{uid}:rank:{rank}:luckybox"
            reason=f"Thưởng hoàn thành sớm Giai Đoạn 1 C1 · Hạng {rank}"

            # RPC Zcoin đã có idempotency_key -> bấm lại không cộng trùng.
            adjust_zcoin_balance(
                uid,
                reward["zcoin"],
                reason,
                actor.get("id"),
                z_key,
            )

            # Lucky Box RPC cũng idempotent.
            execute_query(
                db.rpc("adjust_lucky_box_balance",{
                    "p_user_id":uid,
                    "p_amount":reward["lucky_box"],
                    "p_source":"c1_stage1_early_reward",
                    "p_description":reason,
                    "p_idempotency_key":box_key,
                    "p_metadata":{
                        "tournament_id":str(tournament_id),
                        "stage_code":"stage1",
                        "finish_rank":rank,
                        "completed_at":row.get("completed_at"),
                    },
                }),
                "ops_c1_stage1_early_luckybox_reward",
                attempts=2,
            )

            granted[uid]={
                "status":"granted",
                "finish_rank":rank,
                "zcoin":reward["zcoin"],
                "lucky_box":reward["lucky_box"],
                "random_club_tickets":2 if rank==1 else 1,
                "completed_at":row.get("completed_at"),
                "granted_at":now_iso(),
                "granted_by":str(actor.get("id") or ""),
            }

            # Lưu log thưởng tournament để Admin tra lại.
            try:
                execute_query(
                    db.table("tournament_reward_grants").insert({
                        "tournament_id":tournament_id,
                        "rule_id":None,
                        "user_id":uid,
                        "reward_type":"zcoin",
                        "reward_value":str(reward["zcoin"]),
                        "reason":reason+" | Lucky Box: "+str(reward["lucky_box"]),
                        "granted_at":now_iso(),
                        "granted_by":actor.get("id"),
                    }),
                    "ops_c1_stage1_early_reward_log",
                    attempts=1,
                )
            except Exception:
                pass

            create_user_notification(
                uid,
                "🏆 Chúc mừng hoàn thành sớm Giai Đoạn 1!",
                (
                    f"Bạn hoàn thành GĐ1 ở hạng {rank} và nhận "
                    f"{reward['zcoin']:,} Zcoin + {reward['lucky_box']} Lucky Box + {2 if rank==1 else 1} vé Random CLB GĐ2."
                ).replace(",","."),
                "/tournaments",
                "c1_stage1_early_reward",
            )
            ttl_cache_delete(f"user:{uid}")
            newly_rewarded.append(row)

        # Ghi state sau khi RPC thành công; đây là lớp chống gửi thông báo/log trùng.
        summary_names=[]
        for row in winners:
            rank=int(row.get("finish_rank") or 0)
            reward=_stage1_early_reward_amount(rank)
            summary_names.append(
                f"#{rank} {row.get('display_name')}: {reward['zcoin']} Zcoin + {reward['lucky_box']} Lucky Box + {2 if rank==1 else 1} vé Random CLB"
            )

        announcement_created=bool(state.get("announcement_created"))
        if not announcement_created:
            title="Chúc mừng các HLV đã hoàn thành sớm Giai Đoạn 1"
            message=" · ".join(summary_names)
            try:
                create_admin_announcement(
                    title=title[:40],
                    message=message[:220],
                    admin_user_id=actor.get("id"),
                )
                announcement_created=True
            except Exception as exc:
                app.logger.warning("C1 stage1 early reward announcement failed: %s",exc)

        new_state={
            "granted":granted,
            "announcement_created":announcement_created,
            "announcement_title":"Chúc mừng các HLV đã hoàn thành sớm Giai Đoạn 1",
            "updated_at":now_iso(),
        }
        execute_query(
            db.table("tournament_settings").upsert({
                "tournament_id":tournament_id,
                "setting_key":STAGE1_EARLY_REWARD_KEY,
                "setting_value":new_state,
                "updated_at":now_iso(),
            },on_conflict="tournament_id,setting_key"),
            "ops_c1_stage1_early_reward_state",
            attempts=2,
        )

        cache_delete("_rz_players_all")
        cache_delete("_rz_users_map")
        cache_delete("_rz_current_user")

        if newly_rewarded:
            flash(
                f"Đã trao thưởng hoàn thành sớm GĐ1 cho {len(newly_rewarded)} HLV và đăng thông báo chúc mừng.",
                "success",
            )
        else:
            flash("Các HLV Top hoàn thành sớm đã được trao thưởng trước đó. Không cộng trùng.","info")
        return redirect_admin("tournaments")

    @app.post('/admin/tournaments/<tournament_id>/rewards/add')
    @login_required
    @admin_required
    def admin_tournament_reward_add(tournament_id):
        payload={"tournament_id":tournament_id,"name":(request.form.get("name") or "Thưởng sớm").strip(),"stage_code":request.form.get("stage_code") or "stage1","reward_type":request.form.get("reward_type") or "zcoin","reward_value":request.form.get("reward_value") or "0","deadline_at":request.form.get("deadline_at") or None,"enabled":True,"priority":int(request.form.get("priority") or 100),"created_at":now_iso()}
        execute_query(db.table("tournament_reward_rules").insert(payload),"ops_reward_add",attempts=2)
        flash("Đã thêm mức thưởng.","success"); return redirect_admin("tournaments")

    return {k: v for k, v in locals().items() if (k.startswith('_') and callable(v)) or k.isupper()}
