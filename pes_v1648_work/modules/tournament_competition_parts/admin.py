from modules.tournament_competition_parts.league_draw import generate_four_match_draw
import random as _draw_random

"""Internal tournament competition partition extracted from the legacy monolith.

Registered only through :mod:`modules.tournament_competition`.
"""

def register_admin(context):
    globals().update(context)

    @app.get('/tournaments/<tournament_id>')
    @login_required
    def tournament_detail(tournament_id):
        # Compatibility route only: all user-facing tournament UI now lives at /tournaments.
        return redirect(url_for("tournaments"))

    @app.get('/admin/tournaments/<tournament_id>/draw-preview')
    @login_required
    @admin_required
    def admin_tournament_draw_preview(tournament_id):
        """V1.6.4 live control + safe rehearsal screen for the GĐ2 draw ceremony."""
        tours,_=_rows(
            db.table("tournaments").select("*").eq("id",tournament_id).limit(1),
            "ops_draw_preview_tournament",
        )
        if not tours:
            flash("Không tìm thấy giải đấu.","error")
            return redirect_admin("tournaments")
        tour=tours[0]
        members=sorted(_all_members(tournament_id),key=lambda m:(int(m.get("seed_no") or 9999),(m.get("display_name") or "").lower()))
        # Avatars are already returned by _all_members via users.avatar_url.
        # Do not infer missing pictures or expose inactive members.
        for member in members:
            member["avatar_url"]=(member.get("user") or {}).get("avatar_url") or ""
        member_map={str(m.get("user_id")):m for m in members}
        # V1.6.9: clubs_import first, then teams and exact owner-provided URLs for missing clubs.
        # Porto/RB Leipzig missing in CSV; PSV is present with psv.png.
        # do not create fake rows, generate brand marks, or change Pot membership.
        from modules.tournament_club_logos import load_draw_club_logos
        from modules.legacy_team_random_service import _load_teams_from_supabase
        approved_clubs=[name for pot in C1_CLUB_POTS.values() for name in pot]
        draw_club_logos, logo_sync_status = load_draw_club_logos(
            db, execute_query, __import__("os").getenv("SUPABASE_URL", ""), approved_clubs,
            team_loader=_load_teams_from_supabase, logger=app.logger,
        )
        def draw_logo(name):
            return draw_club_logos.get(str(name or "").strip(), "")
        draft_rows=_club_draft_admin_rows(tournament_id)
        timing_cfg=_setting(tournament_id,"competition_timing",{}) or {}
        reward_phase=_reward_ticket_phase_status(tournament_id)
        league_draw=_league_draw_payload(tournament_id)
        draw_state=league_draw.get("state") or {}
        league_matches=[m for m in _matches(tournament_id,"league") if m.get("status")!="cancelled"]

        occupied={str(m.get("fixed_club_name") or "") for m in members if m.get("fixed_club_name")}
        club_pots=[]
        for pot_no in (1,2,3):
            clubs=[]
            for club in C1_CLUB_POTS.get(pot_no,[]):
                clubs.append({"name":club,"occupied":club in occupied,"logo_url":draw_logo(club)})
            club_pots.append({"pot_no":pot_no,"clubs":clubs,"remaining":sum(1 for c in clubs if not c["occupied"])})

        opponents_by_user={str(m.get("user_id")) : [] for m in members}
        for mt in league_matches:
            h=str(mt.get("home_user_id") or ""); a=str(mt.get("away_user_id") or "")
            if h in opponents_by_user and a in member_map:
                opponents_by_user[h].append({"user_id":a,"display_name":member_map[a].get("display_name") or "HLV","tier":int(member_map[a].get("pot_no") or 0),"avatar_url":member_map[a].get("avatar_url") or ""})
            if a in opponents_by_user and h in member_map:
                opponents_by_user[a].append({"user_id":h,"display_name":member_map[h].get("display_name") or "HLV","tier":int(member_map[h].get("pot_no") or 0),"avatar_url":member_map[h].get("avatar_url") or ""})

        order=[str(x) for x in (draw_state.get("order") or []) if str(x) in member_map]
        current_index=int(draw_state.get("current_index") or 0)
        # Show the last publicly revealed HLV on stage; never leak scheduled
        # but unannounced opponents into preview HTML.
        revealed=draw_state.get("revealed") or {}
        last_uid=str((draw_state.get("history") or [{}])[-1].get("user_id") or "")
        current_uid=last_uid if last_uid in member_map else (order[current_index] if order and current_index < len(order) else (str(members[0].get("user_id")) if members else ""))
        current_member=member_map.get(current_uid) or (members[0] if members else {})
        visible_ids={str(x.get("user_id")) for x in (revealed.get(current_uid) or []) if isinstance(x,dict)}
        current_opponents=[o for o in opponents_by_user.get(current_uid,[]) if str(o.get("user_id")) in visible_ids][:4]
        next_club_member=next((m for m in reversed(members) if not m.get("fixed_club_name")),None)
        # Only reveal the most recently CONFIRMED base draw. The next coach's club
        # remains unknown and no future results are computed in this GET handler.
        draft_state=_club_draft_state(tournament_id,False) or {}
        last_club_member=None
        last_club_name=""
        for event in reversed(draft_state.get("history") or []):
            if event.get("action")!="BASE_SINGLE_RANDOM":
                continue
            candidate=member_map.get(str(event.get("user_id") or ""))
            if candidate and str(candidate.get("fixed_club_name") or "")==str(event.get("club") or ""):
                last_club_member=candidate
                last_club_name=str(event.get("club") or "")
                break
        next_opponent_member=member_map.get(order[current_index]) if order and current_index<len(order) else (members[0] if not order and members else None)

        revealed=draw_state.get("revealed") or {}
        revealed_count=sum(1 for uid in member_map if revealed.get(uid))
        assigned_count=sum(1 for m in members if m.get("fixed_club_name"))

        # V1.6.4: generate a full rehearsal payload entirely in memory. This data is
        # never persisted and therefore lets Admin rehearse the entire ceremony
        # without consuming tickets, assigning clubs or creating fixtures.
        sim_members=[dict(m) for m in members]
        sim_clubs={}
        try:
            for tier,club_pot in ((1,3),(2,2),(3,1)):
                tier_members=[m for m in sim_members if int(m.get("pot_no") or 0)==tier]
                chosen=_draw_random.sample(list(C1_CLUB_POTS.get(club_pot,[])),len(tier_members))
                for m,club in zip(tier_members,chosen):
                    sim_clubs[str(m.get("user_id"))]=club
            sim_rounds=generate_four_match_draw(sim_members)
            sim_opponents={str(m.get("user_id")):[] for m in sim_members}
            sim_member_map={str(m.get("user_id")):m for m in sim_members}
            for pairs in sim_rounds:
                for a,b in pairs:
                    a=str(a); b=str(b)
                    if a in sim_opponents and b in sim_member_map:
                        om=sim_member_map[b]
                        sim_opponents[a].append({"user_id":b,"display_name":om.get("display_name") or "HLV","tier":int(om.get("pot_no") or 0),"avatar_url":om.get("avatar_url") or ""})
                    if b in sim_opponents and a in sim_member_map:
                        om=sim_member_map[a]
                        sim_opponents[b].append({"user_id":a,"display_name":om.get("display_name") or "HLV","tier":int(om.get("pot_no") or 0),"avatar_url":om.get("avatar_url") or ""})
        except Exception:
            app.logger.exception("Could not build draw rehearsal payload: %s",tournament_id)
            sim_clubs={}
            sim_opponents={}

        stages,_=_rows(db.table("tournament_stages").select("stage_code,status").eq("tournament_id",tournament_id),"ops_draw_preview_stages")
        stage_status={str(x.get("stage_code")):str(x.get("status") or "") for x in stages}
        league_started=stage_status.get("league") in {"open","completed"}
        has_non_pending_league=any(str(m.get("status") or "pending")!="pending" for m in league_matches)
        preview={
            "tournament":tour,
            "members":members,
            "draft_rows":draft_rows,
            "club_pots":club_pots,
            "club_logo_urls":{c.casefold():draw_logo(c) for pot in C1_CLUB_POTS.values() for c in pot},
            "logo_sync_status":logo_sync_status,
            "assigned_count":assigned_count,
            "reward_phase":reward_phase,
            "league_match_count":len(league_matches),
            "draw_state":draw_state,
            "revealed_count":revealed_count,
            "current_member":current_member,
            "current_opponents":current_opponents,
            "next_club_member":next_club_member,
            "last_club_member":last_club_member,
            "last_club_name":last_club_name,
            "next_opponent_member":next_opponent_member,
            "club_draw_at":timing_cfg.get("club_draw_at") or "2026-09-17T20:00:00+07:00",
            "reward_deadline_at":timing_cfg.get("gd2_reward_ticket_deadline_at") or "2026-09-18T12:00:00+07:00",
            "league_start_at":timing_cfg.get("league_start_at") or "2026-09-18T12:00:00+07:00",
            "stage_status":stage_status,
            "league_started":league_started,
            "can_revoke_opponents":bool(league_matches) and not league_started and not has_non_pending_league,
            "can_revoke_clubs":not league_matches and not league_started,
            "simulation":{
                "clubs":sim_clubs,
                "opponents":sim_opponents,
                "order":[str(m.get("user_id")) for m in sim_members],
                "members":[{
                    "user_id":str(m.get("user_id")),
                    "display_name":m.get("display_name") or "HLV",
                    "seed_no":int(m.get("seed_no") or 0),
                    "tier":int(m.get("pot_no") or 0),
                    "avatar_url":m.get("avatar_url") or "",
                } for m in sim_members],
            },
        }
        return render_template("tournament/draw_admin_preview.html", preview=preview, auth_only=True)

    @app.post('/admin/tournaments/<tournament_id>/c1-test-accounts')
    @login_required
    @admin_required
    def admin_tournament_c1_test_accounts(tournament_id):
        requested=[]
        for key in ("test_user_1","test_user_2"):
            value=str(request.form.get(key) or "").strip()
            if value and value not in requested:
                requested.append(value)
        requested=requested[:2]
        official={str(m.get("user_id")) for m in _all_members(tournament_id)}
        overlap=[uid for uid in requested if uid in official]
        if overlap:
            flash("Không thể dùng HLV chính thức làm tài khoản thử nghiệm. Hãy chọn tài khoản ngoài danh sách 16 HLV.","error")
            return redirect_admin("tournaments")
        valid=[]
        if requested:
            rows,_=_rows(db.table("users").select("id").in_("id",requested),"ops_validate_c1_test_accounts")
            valid=[str(r.get("id")) for r in rows if str(r.get("id") or "") in requested]
        execute_query(db.table("tournament_settings").upsert({
            "tournament_id":tournament_id,"setting_key":C1_TEST_ACCOUNTS_KEY,
            "setting_value":{"user_ids":valid,"updated_at":now_iso()},"updated_at":now_iso(),
        },on_conflict="tournament_id,setting_key"),"ops_save_c1_test_accounts",attempts=2)
        flash(f"Đã lưu {len(valid)} tài khoản thử nghiệm. Hai tài khoản chỉ nhìn thấy nhau; HLV thường không thấy. Dữ liệu kiểm thử không vào BXH, lịch, pool CLB hay trận chính thức.","success")
        return redirect_admin("tournaments")

    @app.get('/admin/tournaments/<tournament_id>/preview-player')
    @login_required
    @admin_required
    def admin_tournament_preview_player(tournament_id):
        user_id=str(request.args.get("user_id") or "").strip()
        if not user_id:
            flash("Hãy chọn HLV cần xem.","warning")
            return redirect_admin("tournaments")
        members=_all_members(tournament_id)
        preview_member=next((m for m in members if str(m.get("user_id"))==user_id),None)
        if not preview_member:
            flash("HLV này không còn trong danh sách giải.","error")
            return redirect_admin("tournaments")
        data=_detail_payload(tournament_id,user_id)
        if not data:
            flash("Không tìm thấy giải đấu.","error")
            return redirect_admin("tournaments")
        data.update({"preview_mode":True,"preview_user":preview_member})
        return render_template('tournament_detail.html', **data)

    @app.post('/admin/tournaments/<tournament_id>/members/<user_id>/remove')
    @login_required
    @admin_required
    def admin_tournament_member_remove(tournament_id,user_id):
        # V1.4.79: khi Admin xóa HLV ở giai đoạn đăng ký, phải đồng bộ cả
        # danh sách thi đấu và hồ sơ đăng ký. Không xóa tài khoản web / lịch sử tiền.
        execute_query(
            db.table("tournament_members").update({"status":"withdrawn"})
            .eq("tournament_id",tournament_id).eq("user_id",user_id),
            "ops_member_remove", attempts=2,
        )
        execute_query(
            db.table("tournament_registrations").update({"status":"withdrawn"})
            .eq("tournament_id",tournament_id).eq("user_id",user_id),
            "ops_registration_remove", attempts=2,
        )
        log_admin_action(
            "Xóa HLV khỏi giải", "tournament_member",
            details={"tournament_id":tournament_id,"user_id":user_id,"registration_status":"withdrawn"},
        )
        flash("Đã xóa HLV khỏi giải. Tài khoản web và lịch sử lệ phí vẫn được giữ lại.","success")
        return redirect_admin("tournaments")

    @app.post('/admin/tournaments/<tournament_id>/members/<old_user_id>/replace')
    @login_required
    @admin_required
    def admin_tournament_member_replace(tournament_id, old_user_id):
        """Cho HLV mới tiếp quản nguyên suất thi đấu của HLV rời giải.

        Kết quả/lịch/CLB/Pot được chuyển sang user mới để các phép tính hiện tại
        tiếp tục hoạt động; snapshot trước khi chuyển được lưu trong
        tournament_settings:replacement_history để Admin vẫn truy được lịch sử.
        Lịch rảnh không được kế thừa.
        """
        new_user_id=str(request.form.get("new_user_id") or "").strip()
        if not new_user_id or new_user_id == str(old_user_id):
            flash("Hãy chọn một HLV thay thế khác HLV đang rời giải.","error")
            return redirect_admin("tournaments")

        old_member=_member(tournament_id, old_user_id)
        new_user=get_user(new_user_id)
        if not old_member or str(old_member.get("status") or "")!="active":
            flash("HLV rời giải không còn là thành viên active của giải.","error")
            return redirect_admin("tournaments")
        if not new_user or str(new_user.get("role") or "player")!="player":
            flash("Không tìm thấy tài khoản HLV thay thế hợp lệ.","error")
            return redirect_admin("tournaments")
        existing_new=_member(tournament_id,new_user_id)
        if existing_new and str(existing_new.get("status") or "")=="active":
            flash("HLV thay thế đã có một suất active trong giải này.","error")
            return redirect_admin("tournaments")
        new_existing_matches=[
            m for m in _matches(tournament_id)
            if str(m.get("home_user_id") or "")==new_user_id or str(m.get("away_user_id") or "")==new_user_id
        ]
        if new_existing_matches:
            flash("HLV thay thế đã có lịch sử trận trong giải này nên không thể nhập thêm một suất khác.","error")
            return redirect_admin("tournaments")

        # Không thay người khi HLV cũ vẫn nằm trong một phòng C1 đang hoạt động.
        try:
            active_room=next((
                r for r in _tournament_rooms(tournament_id)
                if str(r.get("host_user_id") or "")==str(old_user_id)
                or str(r.get("guest_user_id") or "")==str(old_user_id)
            ),None)
        except Exception:
            active_room=None
        if active_room:
            flash("HLV cũ đang ở trong phòng đấu C1. Hãy đóng/hoàn tất phòng trước khi thay HLV.","error")
            return redirect_admin("tournaments")

        admin_user=current_user() or {}
        now_value=now_iso()
        old_user=get_user(old_user_id) or {}
        old_name=old_user.get("display_name") or old_user.get("username") or str(old_user_id)
        new_name=new_user.get("display_name") or new_user.get("username") or str(new_user_id)

        # Snapshot toàn bộ trận trước khi đổi owner để giữ bằng chứng ai thực sự đá.
        all_matches=_matches(tournament_id)
        affected=[]
        for m in all_matches:
            if str(m.get("home_user_id") or "")==str(old_user_id) or str(m.get("away_user_id") or "")==str(old_user_id):
                affected.append({
                    "match_id":m.get("id"),
                    "stage_code":m.get("stage_code"),
                    "status":m.get("status"),
                    "home_user_id":m.get("home_user_id"),
                    "away_user_id":m.get("away_user_id"),
                    "home_score":m.get("home_score"),
                    "away_score":m.get("away_score"),
                    "home_pen":m.get("home_pen"),
                    "away_pen":m.get("away_pen"),
                    "winner_user_id":m.get("winner_user_id"),
                    "scheduled_at":m.get("scheduled_at"),
                })

        # Đổi owner của toàn bộ trận, kể cả completed: BXH và tiến độ của suất
        # được kế thừa đúng, còn snapshot phía trên giữ lịch sử người đá cũ.
        execute_query(
            db.table("tournament_matches").update({"home_user_id":new_user_id,"updated_at":now_value})
            .eq("tournament_id",tournament_id).eq("home_user_id",old_user_id),
            "ops_member_replace_home_matches",attempts=2,
        )
        execute_query(
            db.table("tournament_matches").update({"away_user_id":new_user_id,"updated_at":now_value})
            .eq("tournament_id",tournament_id).eq("away_user_id",old_user_id),
            "ops_member_replace_away_matches",attempts=2,
        )
        execute_query(
            db.table("tournament_matches").update({"winner_user_id":new_user_id,"updated_at":now_value})
            .eq("tournament_id",tournament_id).eq("winner_user_id",old_user_id),
            "ops_member_replace_winner",attempts=2,
        )

        # Chuyển suất thành viên, giữ nguyên Pot/seed/CLB.
        execute_query(
            db.table("tournament_members").update({"status":"withdrawn"})
            .eq("tournament_id",tournament_id).eq("user_id",old_user_id),
            "ops_member_replace_old_withdraw",attempts=2,
        )
        member_payload={
            "tournament_id":tournament_id,
            "user_id":new_user_id,
            "status":"active",
            "pot_no":old_member.get("pot_no"),
            "seed_no":old_member.get("seed_no"),
            "fixed_club_id":old_member.get("fixed_club_id"),
            "fixed_club_name":old_member.get("fixed_club_name"),
            "approved_at":now_value,
            "approved_by":admin_user.get("id"),
        }
        # zalo_name là cột mở rộng ở source hiện tại; chỉ truyền khi có dữ liệu.
        if new_user.get("display_name"):
            member_payload["zalo_name"]=new_user.get("display_name")
        execute_query(
            db.table("tournament_members").upsert(member_payload,on_conflict="tournament_id,user_id"),
            "ops_member_replace_new_upsert",attempts=2,
        )

        # Hồ sơ đăng ký cũ rút giải; HLV mới được approved nhưng KHÔNG kế thừa
        # tiền/Host/Zalo/lịch rảnh của người cũ.
        execute_query(
            db.table("tournament_registrations").update({"status":"withdrawn","reviewed_at":now_value,"reviewed_by":admin_user.get("id")})
            .eq("tournament_id",tournament_id).eq("user_id",old_user_id),
            "ops_member_replace_old_registration",attempts=2,
        )
        new_regs,_=_rows(
            db.table("tournament_registrations").select("*").eq("tournament_id",tournament_id).eq("user_id",new_user_id),
            "ops_member_replace_new_registration_lookup",
        )
        if new_regs:
            execute_query(
                db.table("tournament_registrations").update({"status":"approved","reviewed_at":now_value,"reviewed_by":admin_user.get("id")})
                .eq("id",new_regs[0].get("id")),
                "ops_member_replace_new_registration_update",attempts=2,
            )
        else:
            execute_query(
                db.table("tournament_registrations").insert({
                    "tournament_id":tournament_id,"user_id":new_user_id,"status":"approved",
                    "registered_at":now_value,"reviewed_at":now_value,"reviewed_by":admin_user.get("id"),
                    "has_host":False,
                }),
                "ops_member_replace_new_registration_insert",attempts=2,
            )

        # CLB đang reserve theo user cũ phải chuyển owner.
        try:
            execute_query(
                db.table("tournament_clubs").update({"selected_by":new_user_id,"selected_at":now_value})
                .eq("tournament_id",tournament_id).eq("selected_by",old_user_id),
                "ops_member_replace_club_owner",attempts=2,
            )
        except Exception as exc:
            app.logger.warning("Tournament replacement club owner warning: %s",exc)

        # Reward đã cấp thuộc về suất thi đấu: chuyển marker để người mới không
        # được nhận lại lần hai. Không phát thêm Zcoin/Lucky Box.
        try:
            execute_query(
                db.table("tournament_reward_grants").update({"user_id":new_user_id})
                .eq("tournament_id",tournament_id).eq("user_id",old_user_id),
                "ops_member_replace_reward_markers",attempts=2,
            )
        except Exception as exc:
            app.logger.warning("Tournament replacement reward marker warning: %s",exc)

        # Người mới bắt buộc khai báo lịch rảnh của chính mình.
        execute_query(
            db.table("tournament_availability_slots").delete()
            .eq("tournament_id",tournament_id).eq("user_id",new_user_id),
            "ops_member_replace_clear_new_availability",attempts=2,
        )

        # Các setting/draft có user_id cũ được chuyển owner theo slot.
        settings,_=_rows(
            db.table("tournament_settings").select("*").eq("tournament_id",tournament_id),
            "ops_member_replace_settings_read",
        )
        def _replace_uid(value):
            if isinstance(value,dict):
                return {k:_replace_uid(v) for k,v in value.items()}
            if isinstance(value,list):
                return [_replace_uid(v) for v in value]
            if str(value)==str(old_user_id):
                return new_user_id
            return value
        for setting in settings:
            key=str(setting.get("setting_key") or "")
            if key=="replacement_history":
                continue
            original=setting.get("setting_value")
            replaced=_replace_uid(original)
            if replaced != original:
                execute_query(
                    db.table("tournament_settings").update({"setting_value":replaced,"updated_at":now_value}).eq("id",setting.get("id")),
                    "ops_member_replace_setting_owner",attempts=2,
                )

        # Lưu lịch sử thay HLV ở setting JSON, không cần migration DB.
        history_setting,_=_one(
            db.table("tournament_settings").select("*").eq("tournament_id",tournament_id).eq("setting_key","replacement_history"),
            "ops_member_replace_history_read",
        )
        history_value=(history_setting or {}).get("setting_value") or {}
        if not isinstance(history_value,dict):
            history_value={}
        entries=list(history_value.get("entries") or [])
        entries.append({
            "replaced_at":now_value,
            "replaced_by":admin_user.get("id"),
            "old_user_id":str(old_user_id),
            "old_name":old_name,
            "new_user_id":new_user_id,
            "new_name":new_name,
            "inherited":{
                "pot_no":old_member.get("pot_no"),
                "seed_no":old_member.get("seed_no"),
                "club_id":old_member.get("fixed_club_id"),
                "club_name":old_member.get("fixed_club_name"),
                "matches":affected,
            },
        })
        execute_query(
            db.table("tournament_settings").upsert({
                "tournament_id":tournament_id,
                "setting_key":"replacement_history",
                "setting_value":{"entries":entries,"updated_at":now_value},
                "updated_at":now_value,
            },on_conflict="tournament_id,setting_key"),
            "ops_member_replace_history_save",attempts=2,
        )

        try:
            create_user_notification(
                new_user_id,
                "🔄 Bạn được xếp vào thay HLV giữa giải",
                f"Bạn đã tiếp quản suất của {old_name}. CLB, Pot, kết quả đã đá và lịch còn lại được giữ nguyên. Hãy đăng ký lại giờ rảnh trước khi thi đấu.",
                "/tournaments",
                "tournament_replacement",
            )
        except Exception as exc:
            app.logger.warning("Tournament replacement notification warning: %s",exc)

        log_admin_action(
            "Thay HLV giữa giải","tournament_member",
            details={
                "tournament_id":tournament_id,
                "old_user_id":str(old_user_id),"old_name":old_name,
                "new_user_id":new_user_id,"new_name":new_name,
                "inherited_match_count":len(affected),
                "club":old_member.get("fixed_club_name"),
                "pot_no":old_member.get("pot_no"),
            },
        )
        flash(
            f"Đã thay {old_name} → {new_name}. {new_name} kế thừa CLB, Pot, {len(affected)} trận/kết quả và tiến độ; lịch rảnh phải đăng ký lại.",
            "success",
        )
        return redirect_admin("tournaments")

    @app.post('/admin/tournaments/<tournament_id>/stages/<stage_code>/status')
    @login_required
    @admin_required
    def admin_tournament_stage_status(tournament_id,stage_code):
        status=(request.form.get("status") or "locked").strip()
        if status not in {"draft","open","locked","completed"}: status="locked"
        execute_query(db.table("tournament_stages").update({"status":status,"updated_at":now_iso()}).eq("tournament_id",tournament_id).eq("stage_code",stage_code),"ops_stage_status",attempts=2)
        flash(f"Đã cập nhật {STAGE_LABELS.get(stage_code,stage_code)}: {status}.","success"); return redirect_admin("tournaments")

    @app.post('/admin/tournaments/<tournament_id>/gd2/draw-time')
    @login_required
    @admin_required
    def admin_tournament_gd2_draw_time(tournament_id):
        # All datetime-local values are interpreted in Asia/Ho_Chi_Minh (UTC+07).
        def parse_local(name, default_value):
            raw=(request.form.get(name) or default_value).strip()
            try:
                parsed=datetime.strptime(raw,"%Y-%m-%dT%H:%M")
                return parsed.replace(tzinfo=timezone(timedelta(hours=7))).isoformat(timespec="seconds")
            except (TypeError,ValueError):
                return None
        draw_iso=parse_local("club_draw_local","2026-09-17T20:00")
        reward_deadline_iso=parse_local("reward_ticket_deadline_local","2026-09-18T12:00")
        league_start_iso=parse_local("league_start_local","2026-09-18T12:00")
        if not draw_iso or not reward_deadline_iso or not league_start_iso:
            flash("Mốc thời gian GĐ2 không hợp lệ. Hãy chọn đủ ngày và giờ.","error")
            return redirect(url_for("admin")+"#c1-admin-gd2")
        if _parse_iso(reward_deadline_iso) <= _parse_iso(draw_iso):
            flash("Hạn dùng vé thưởng phải sau thời điểm mở lễ bốc thăm.","error")
            return redirect(url_for("admin")+"#c1-admin-gd2")
        if _parse_iso(league_start_iso) < _parse_iso(reward_deadline_iso):
            flash("Mốc mở GĐ2 theo lịch không được sớm hơn hạn dùng vé thưởng.","error")
            return redirect(url_for("admin")+"#c1-admin-gd2")
        cfg=_setting(tournament_id,"competition_timing",{}) or {}
        cfg=dict(cfg) if isinstance(cfg,dict) else {}
        cfg["club_draw_at"]=draw_iso
        cfg["gd2_reward_ticket_deadline_at"]=reward_deadline_iso
        cfg["league_start_at"]=league_start_iso
        if not cfg.get("league_end_at"):
            cfg["league_end_at"]=(_parse_iso(league_start_iso)+timedelta(days=7)).isoformat()
        cfg["updated_at"]=now_iso()
        try:
            result=execute_query(db.table("tournament_settings").upsert({
                "tournament_id":tournament_id,"setting_key":"competition_timing",
                "setting_value":cfg,"updated_at":now_iso(),
            },on_conflict="tournament_id,setting_key"),"ops_gd2_draw_time",attempts=2)
            if result is None:
                raise RuntimeError("Database did not confirm GĐ2 timing save")
        except Exception:
            app.logger.exception("Cannot save GĐ2 ceremony timing for tournament %s",tournament_id)
            flash("Chưa lưu được lịch vận hành GĐ2. Kiểm tra log server và thử lại.","error")
            return redirect(url_for("admin")+"#c1-admin-gd2")
        flash("Đã lưu: mở lễ bốc thăm, hạn dùng vé thưởng và mốc mở GĐ2.","success")
        return redirect(url_for("admin")+"#c1-admin-gd2")

    @app.post('/admin/tournaments/<tournament_id>/stage1/settings')
    @login_required
    @admin_required
    def admin_tournament_stage1_settings(tournament_id):
        target=max(1,min(20,int(request.form.get("match_target") or 6)))
        min_opp=max(1,min(target,int(request.form.get("min_opponents") or 3)))
        max_same=max(1,min(target,int(request.form.get("max_per_opponent") or 2)))
        execute_query(db.table("tournament_stages").update({"match_target":target,"min_opponents":min_opp,"max_matches_per_opponent":max_same,"updated_at":now_iso()}).eq("tournament_id",tournament_id).eq("stage_code","stage1"),"ops_stage1_settings",attempts=2)
        flash("Đã lưu luật GĐ1.","success"); return redirect_admin("tournaments")

    @app.post('/admin/tournaments/<tournament_id>/stage1/clubs')
    @login_required
    @admin_required
    def admin_tournament_stage1_clubs(tournament_id):
        selected=request.form.getlist("clubs")
        if len(selected)!=16:
            flash(f"Hãy chọn đúng 16 CLB Tier S/S+ cho phòng C1. Hiện đang chọn {len(selected)} đội.","error"); return redirect_admin("tournaments")
        lookup={x.get("display"):x for x in _stage1_eligible_clubs(force=True)}
        clubs=[]
        for name in selected:
            info=lookup.get(name)
            if info:
                clubs.append({
                    "display":name,
                    "overall":int(info.get("overall") or 0),
                    "tier":str(info.get("tier") or "").strip().upper(),
                })
        if len(clubs)!=16:
            flash(f"Phòng C1 yêu cầu chọn đúng 16 CLB Tier S/S+. Hiện đang chọn {len(clubs)} đội.","error"); return redirect_admin("tournaments")
        execute_query(db.table("tournament_settings").upsert({"tournament_id":tournament_id,"setting_key":"stage1_club_pool","setting_value":{"clubs":clubs,"updated_at":now_iso()},"updated_at":now_iso()},on_conflict="tournament_id,setting_key"),"ops_stage1_club_pool_save",attempts=2)
        flash(f"Đã lưu Pool {len(clubs)} CLB cho GĐ1.","success"); return redirect_admin("tournaments")

    @app.post('/admin/tournaments/<tournament_id>/stage1/clubs/reset')
    @login_required
    @admin_required
    def admin_tournament_stage1_clubs_reset(tournament_id):
        defaults=_default_stage1_clubs()
        execute_query(db.table("tournament_settings").upsert({"tournament_id":tournament_id,"setting_key":"stage1_club_pool","setting_value":{"clubs":defaults,"updated_at":now_iso()},"updated_at":now_iso()},on_conflict="tournament_id,setting_key"),"ops_stage1_club_pool_reset",attempts=2)
        flash(f"Đã chọn lại {len(defaults)} CLB Tier S+ và S mạnh nhất cho C1.","success"); return redirect_admin("tournaments")

    @app.post('/admin/tournaments/<tournament_id>/matches/add')
    @login_required
    @admin_required
    def admin_tournament_match_add(tournament_id):
        stage_code=(request.form.get("stage_code") or "stage1").strip()
        home=str(request.form.get("home_user_id") or "").strip(); away=str(request.form.get("away_user_id") or "").strip()
        if not home or not away or home==away:
            flash("Cặp đấu không hợp lệ.","error"); return redirect_admin("tournaments")
        if stage_code=="stage1":
            st=_stage(tournament_id,"stage1") or {}; max_same=int(st.get("max_matches_per_opponent") or 2)
            allm=_matches(tournament_id,"stage1",["pending","scheduled","completed"])
            same=sum(1 for m in allm if {str(m.get("home_user_id")),str(m.get("away_user_id"))}=={home,away})
            if same>=max_same:
                flash(f"Hai HLV đã đạt giới hạn {max_same} trận gặp nhau ở GĐ1.","error"); return redirect_admin("tournaments")
        payload={"tournament_id":tournament_id,"stage_code":stage_code,"home_user_id":home,"away_user_id":away,"status":"pending","round_code":request.form.get("round_code") or None,"leg_no":int(request.form.get("leg_no") or 1),"created_at":now_iso(),"updated_at":now_iso()}
        execute_query(db.table("tournament_matches").insert(payload),"ops_match_add",attempts=2)
        flash("Đã tạo trận giải.","success"); return redirect_admin("tournaments")

    @app.post('/admin/tournaments/matches/<match_id>/result')
    @login_required
    @admin_required
    def admin_tournament_match_result(match_id):
        match,_=_one(db.table("tournament_matches").select("*").eq("id",match_id),"ops_match_result_lookup")
        if not match:
            flash("Không tìm thấy trận.","error"); return redirect_admin("tournaments")
        if str(match.get("stage_code") or "")=="stage1" and str(match.get("status") or "")!="completed":
            if _stage1_pair_completed_count(match.get("tournament_id"), match.get("home_user_id"), match.get("away_user_id"), exclude_match_id=match.get("id")) >= 2:
                flash("Cặp HLV này đã hoàn thành đủ 2 trận. Không thể tính thêm kết quả GĐ1.","warning")
                return redirect_admin("tournaments")
        hs=max(0,int(request.form.get("home_score") or 0)); aw=max(0,int(request.form.get("away_score") or 0))
        hp=request.form.get("home_pen"); ap=request.form.get("away_pen")
        payload={"home_score":hs,"away_score":aw,"home_pen":int(hp) if hp not in (None,'') else None,"away_pen":int(ap) if ap not in (None,'') else None,"status":"completed","completed_at":now_iso(),"updated_at":now_iso()}
        winner=None
        if hs>aw: winner=match.get("home_user_id")
        elif aw>hs: winner=match.get("away_user_id")
        elif payload["home_pen"] is not None and payload["away_pen"] is not None:
            if payload["home_pen"]>payload["away_pen"]: winner=match.get("home_user_id")
            elif payload["away_pen"]>payload["home_pen"]: winner=match.get("away_user_id")
        payload["winner_user_id"]=winner
        execute_query(db.table("tournament_matches").update(payload).eq("id",match_id),"ops_match_result",attempts=2)

        # V1.5.14: Admin chốt kết quả phải đồng bộ luôn Phòng đấu C1 liên kết.
        try:
            room_rows,_=_rows(
                db.table("match_rooms").select("id,note,status,host_user_id,guest_user_id").order("updated_at",desc=True).limit(500),
                "ops_admin_result_linked_c1_rooms",
            )
            for linked_room in room_rows:
                linked_meta=_room_meta(linked_room)
                if not linked_meta:
                    continue
                if str(linked_meta.get("tournament_match_id") or "") != str(match_id):
                    continue
                if str(linked_meta.get("tournament_id") or "") != str(match.get("tournament_id") or ""):
                    continue

                host_uid=str(linked_room.get("host_user_id") or "")
                if host_uid == str(match.get("home_user_id") or ""):
                    room_hs,room_gs=hs,aw
                else:
                    room_hs,room_gs=aw,hs

                execute_query(
                    db.table("match_rooms").update({
                        "host_score":room_hs,
                        "guest_score":room_gs,
                        "status":"confirmed",
                        "updated_at":now_iso(),
                    }).eq("id",linked_room.get("id")),
                    "ops_admin_result_sync_c1_room",
                    attempts=2,
                )

                prop=_tournament_result_proposal(match.get("tournament_id"),match_id)
                prop.update({
                    "status":"admin_confirmed",
                    "home_score":hs,
                    "away_score":aw,
                    "host_score":room_hs,
                    "guest_score":room_gs,
                    "confirmed_by":"admin",
                    "confirmed_at":now_iso(),
                })
                _save_tournament_result_proposal(match.get("tournament_id"),match_id,prop)
                break
        except Exception as exc:
            app.logger.warning("Sync Admin C1 result to room failed: %s",exc)

        if match.get("stage_code")=="knockout":
            try: _maybe_advance_knockout(match.get("tournament_id"))
            except Exception as exc: app.logger.warning("Knockout auto advance failed: %s",exc)
        log_admin_action("Cập nhật kết quả trận giải","tournament_match",details={"match_id":match_id,"score":f"{hs}-{aw}"})
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return ("", 204)
        flash("Đã lưu kết quả trận giải.","success")
        return_to = (request.form.get("return_to") or "").strip()
        if return_to == "central":
            return redirect(url_for("tournaments") + "#ranking")
        if return_to == "tournament":
            return redirect(url_for('tournaments') + "#bxh")
        return redirect_admin("tournaments")


    @app.post('/admin/tournaments/<tournament_id>/matches/bulk-result')
    @login_required
    @admin_required
    def admin_tournament_bulk_match_result(tournament_id):
        match_ids = [str(x).strip() for x in request.form.getlist("match_id") if str(x).strip()]
        home_scores = request.form.getlist("home_score")
        away_scores = request.form.getlist("away_score")
        home_pens = request.form.getlist("home_pen")
        away_pens = request.form.getlist("away_pen")
        if not match_ids:
            flash("Hãy tích ít nhất 1 trận cần lưu tỷ số.","warning")
            return redirect(url_for("tournaments") + "#ranking")
        if len(match_ids) != len(home_scores) or len(match_ids) != len(away_scores):
            flash("Dữ liệu tỷ số hàng loạt không hợp lệ.","error")
            return redirect(url_for("tournaments") + "#ranking")

        saved = 0
        skipped = 0
        for idx, match_id in enumerate(match_ids):
            match,_ = _one(
                db.table("tournament_matches").select("*").eq("id",match_id).eq("tournament_id",tournament_id),
                "ops_bulk_match_lookup",
            )
            if not match:
                skipped += 1
                continue
            try:
                hs = max(0, int(home_scores[idx] or 0))
                aw = max(0, int(away_scores[idx] or 0))
            except Exception:
                skipped += 1
                continue

            # GĐ1: không cho tạo kết quả thứ 3 cho cùng một cặp.
            if str(match.get("stage_code") or "")=="stage1" and str(match.get("status") or "")!="completed":
                if _stage1_pair_completed_count(
                    tournament_id,
                    match.get("home_user_id"),
                    match.get("away_user_id"),
                    exclude_match_id=match.get("id"),
                ) >= 2:
                    skipped += 1
                    continue

            hp_raw = home_pens[idx] if idx < len(home_pens) else ""
            ap_raw = away_pens[idx] if idx < len(away_pens) else ""
            hp = int(hp_raw) if str(hp_raw).strip() != "" else None
            ap = int(ap_raw) if str(ap_raw).strip() != "" else None

            winner = None
            if hs > aw:
                winner = match.get("home_user_id")
            elif aw > hs:
                winner = match.get("away_user_id")
            elif hp is not None and ap is not None:
                if hp > ap:
                    winner = match.get("home_user_id")
                elif ap > hp:
                    winner = match.get("away_user_id")

            payload = {
                "home_score": hs,
                "away_score": aw,
                "home_pen": hp,
                "away_pen": ap,
                "winner_user_id": winner,
                "status": "completed",
                "completed_at": now_iso(),
                "updated_at": now_iso(),
            }
            execute_query(
                db.table("tournament_matches").update(payload).eq("id",match_id),
                "ops_bulk_match_result",
                attempts=2,
            )
            saved += 1

        try:
            if saved:
                _maybe_advance_knockout(tournament_id)
        except Exception as exc:
            app.logger.warning("Bulk result knockout advance failed: %s", exc)

        if saved and skipped:
            flash(f"Đã lưu {saved} trận. Bỏ qua {skipped} trận không hợp lệ/đã đủ giới hạn.","success")
        elif saved:
            flash(f"Đã lưu cùng lúc {saved} kết quả trận đấu.","success")
        else:
            flash("Không có trận nào được lưu. Hãy kiểm tra tỷ số hoặc giới hạn 2 trận/cặp.","warning")
        return redirect(url_for("tournaments") + "#ranking")

    @app.post('/admin/tournaments/<tournament_id>/pot/generate')
    @login_required
    @admin_required
    def admin_tournament_generate_pots(tournament_id):
        # GĐ2 chính thức: 16 HLV chia cố định 3 Pot theo BXH GĐ1 = 5 / 6 / 5.
        pot_count=3
        club_count=max(2,min(64,int(request.form.get("club_count") or len(_all_members(tournament_id)) or 16)))
        league_cfg=_setting(tournament_id,"league_config",{}) or {}
        league_cfg["club_count"]=club_count
        league_cfg["pot_count"]=3
        league_cfg["pot_sizes"]=[5,6,5]
        league_cfg["pot_format"]="5-6-5"
        execute_query(db.table("tournament_settings").upsert({"tournament_id":tournament_id,"setting_key":"league_config","setting_value":league_cfg,"updated_at":now_iso()},on_conflict="tournament_id,setting_key"),"ops_league_config_pot_clubs",attempts=2)
        ranking=_ranking(tournament_id,"stage1")
        if not ranking:
            flash("Chưa có HLV để chia Pot.","error"); return redirect_admin("tournaments")
        if len(ranking)!=16:
            flash(f"GĐ2 cấu hình 5–6–5 yêu cầu đúng 16 HLV, hiện có {len(ranking)} HLV.","error")
            return redirect_admin("tournaments")
        cut1=5; cut2=11
        for i,row in enumerate(ranking):
            pot=1 if i<cut1 else (2 if i<cut2 else 3)
            execute_query(db.table("tournament_members").update({"pot_no":pot,"seed_no":i+1}).eq("tournament_id",tournament_id).eq("user_id",row["user_id"]),"ops_pot_update",attempts=2)
        execute_query(db.table("tournament_settings").upsert({
            "tournament_id":tournament_id,"setting_key":"pots_locked",
            "setting_value":{"locked":False,"pot_count":3,"pot_sizes":[5,6,5],"pot_format":"5-6-5"},
            "updated_at":now_iso(),
        },on_conflict="tournament_id,setting_key"),"ops_pot_setting",attempts=2)
        flash(f"Đã chia GĐ2 đúng 3 Pot 5–6–5 theo BXH GĐ1: Pot 1 = 5 HLV · Pot 2 = 6 HLV · Pot 3 = 5 HLV · {club_count} CLB.","success")
        return redirect_admin("tournaments")

    @app.post('/admin/tournaments/<tournament_id>/pot/lock')
    @login_required
    @admin_required
    def admin_tournament_lock_pots(tournament_id):
        locked=request.form.get("locked")=="1"
        execute_query(db.table("tournament_settings").upsert({"tournament_id":tournament_id,"setting_key":"pots_locked","setting_value":{"locked":locked},"updated_at":now_iso()},on_conflict="tournament_id,setting_key"),"ops_pot_lock",attempts=2)
        flash("Đã khóa Pot." if locked else "Đã mở chỉnh Pot.","success"); return redirect_admin("tournaments")

    return {k: v for k, v in locals().items() if k.startswith('_') and callable(v)}
