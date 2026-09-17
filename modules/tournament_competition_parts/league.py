"""GĐ2 routes; draw generation and validation live in league_draw.py."""

from modules.tournament_competition_parts.league_draw import (
    generate_four_match_draw, validate_four_match_draw,
)

def register_league(context):
    globals().update(context)

    def _gd2_admin_return(tournament_id):
        if (request.form.get("return_to") or "").strip()=="draw_control":
            return redirect(url_for("admin_tournament_draw_preview",tournament_id=tournament_id))
        return redirect_admin("tournaments")

    @app.post('/tournaments/<tournament_id>/club/select')
    @login_required
    def tournament_club_select(tournament_id):
        user=current_user() or {}; uid=user.get("id")
        if not _member(tournament_id,uid): flash("Bạn không thuộc giải đấu này.","error"); return redirect(url_for('tournaments'))
        state=_setting(tournament_id,"club_selection",{"open":False}) or {}
        if not state.get("open"):
            flash("Lượt chọn CLB đang khóa.","warning"); return redirect(url_for('tournaments'))
        club_id=str(request.form.get("club_id") or "").strip()
        club,_=_one(db.table("tournament_clubs").select("*").eq("tournament_id",tournament_id).eq("id",club_id),"ops_club_lookup")
        if not club or not club.get("is_available") or (club.get("selected_by") and str(club.get("selected_by"))!=str(uid)):
            flash("CLB này không còn trống.","error"); return redirect(url_for('tournaments'))
        # release old selection, reserve chosen atomically enough for admin-scale use
        execute_query(db.table("tournament_clubs").update({"selected_by":None,"selected_at":None}).eq("tournament_id",tournament_id).eq("selected_by",uid),"ops_club_release",attempts=2)
        execute_query(db.table("tournament_clubs").update({"selected_by":uid,"selected_at":now_iso()}).eq("id",club_id).is_("selected_by","null"),"ops_club_reserve",attempts=2)
        execute_query(db.table("tournament_members").update({"fixed_club_id":club.get("club_key"),"fixed_club_name":club.get("name")}).eq("tournament_id",tournament_id).eq("user_id",uid),"ops_member_club",attempts=2)
        flash(f"Đã chọn {club.get('name')}.","success"); return redirect(url_for('tournaments'))

    @app.post('/admin/tournaments/<tournament_id>/club-selection')
    @login_required
    @admin_required
    def admin_tournament_club_selection(tournament_id):
        opened=request.form.get("open")=="1"
        execute_query(db.table("tournament_settings").upsert({"tournament_id":tournament_id,"setting_key":"club_selection","setting_value":{"open":opened},"updated_at":now_iso()},on_conflict="tournament_id,setting_key"),"ops_club_state",attempts=2)
        flash("Đã mở chọn CLB." if opened else "Đã khóa chọn CLB.","success"); return redirect_admin("tournaments")

    @app.post('/admin/tournaments/<tournament_id>/clubs/add')
    @login_required
    @admin_required
    def admin_tournament_club_add(tournament_id):
        name=(request.form.get("name") or "").strip(); key=(request.form.get("club_key") or name.lower().replace(' ','-')).strip()
        if name:
            execute_query(db.table("tournament_clubs").upsert({"tournament_id":tournament_id,"club_key":key,"name":name,"is_available":True},on_conflict="tournament_id,club_key"),"ops_club_add",attempts=2)
        flash("Đã thêm CLB.","success"); return redirect_admin("tournaments")

    def _cyclic_pairs(group_a, group_b, k, same=False):
        pairs=[]
        if same:
            n=len(group_a)
            if k>=n or (n*k)%2: raise ValueError("Pot không đủ người để tạo số trận yêu cầu.")
            seen=set()
            for shift in range(1, n//2+1):
                if all(sum(1 for p in pairs if u in p)<k for u in group_a):
                    for i,u in enumerate(group_a):
                        v=group_a[(i+shift)%n]
                        key=tuple(sorted((u,v)))
                        if u!=v and key not in seen and sum(1 for p in pairs if u in p)<k and sum(1 for p in pairs if v in p)<k:
                            seen.add(key); pairs.append((u,v))
            if any(sum(1 for p in pairs if u in p)!=k for u in group_a): raise ValueError("Không thể cân bằng lịch trong cùng Pot.")
            return pairs
        if len(group_a)!=len(group_b): raise ValueError("Các Pot phải có số HLV bằng nhau để sinh lịch tự động.")
        n=len(group_a)
        if k>n: raise ValueError("Số đối thủ mỗi Pot lớn hơn số HLV trong Pot.")
        for shift in range(k):
            for i,u in enumerate(group_a): pairs.append((u,group_b[(i+shift)%n]))
        return pairs

    def _league_four_match_pairs(tournament_id, members):
        """V1.6.2: enforce coverage of ALL THREE HLV Tiers across FOUR matches."""
        return generate_four_match_draw(members)

    @app.post('/admin/tournaments/<tournament_id>/league/start')
    @login_required
    @admin_required
    def admin_tournament_league_start(tournament_id):
        cfg=_setting(tournament_id,"competition_timing",{}) or {}
        vn=timezone(timedelta(hours=7)); now=datetime.now(vn)
        force=request.form.get("start_now")=="1"
        if force:
            ok,msg=_open_league_stage(tournament_id,"admin_force",force_close_rewards=True,start_at=now)
            if not ok:
                flash("Không thể bắt đầu GĐ2: "+msg,"error"); return _gd2_admin_return(tournament_id)
            flash("Admin đã bắt đầu GĐ2 ngay. Vé thưởng chưa dùng đã hết hiệu lực; thời hạn thi đấu 7 ngày.","success")
            return _gd2_admin_return(tournament_id)
        scheduled=_parse_iso(cfg.get("league_start_at") or "2026-09-18T12:00:00+07:00")
        if scheduled and scheduled.tzinfo is None: scheduled=scheduled.replace(tzinfo=vn)
        if scheduled and now<scheduled:
            flash("Chưa đến mốc mở GĐ2. Nếu cần mở sớm, dùng nút Bắt đầu GĐ2 ngay.","warning"); return _gd2_admin_return(tournament_id)
        ok,msg=_open_league_stage(tournament_id,"admin_scheduled",start_at=now)
        if not ok:
            flash("Không thể bắt đầu GĐ2: "+msg,"error"); return _gd2_admin_return(tournament_id)
        flash("Đã mở GĐ2 sau khi kiểm tra CLB, vé thưởng, 32 trận và đủ 3 Tier.","success")
        return _gd2_admin_return(tournament_id)

    @app.post('/admin/tournaments/<tournament_id>/league/generate')
    @login_required
    @admin_required
    def admin_tournament_league_generate(tournament_id):
        members=_all_members(tournament_id)
        stage1=_matches(tournament_id,"stage1")
        if not stage1 or any(m.get("status")!="completed" for m in stage1):
            flash("Chỉ sinh lịch GĐ2 sau khi toàn bộ kết quả GĐ1 đã hoàn tất.","error")
            return _gd2_admin_return(tournament_id)
        stage_rows,_=_rows(db.table("tournament_stages").select("stage_code,status").eq("tournament_id",tournament_id),"ops_league_stage_gate")
        if not any(x.get("stage_code")=="stage1" and x.get("status")=="completed" for x in stage_rows):
            flash("Admin phải kết thúc GĐ1 trước khi sinh lịch GĐ2.","error")
            return _gd2_admin_return(tournament_id)
        if not (_setting(tournament_id,"pots_locked",{}) or {}).get("locked"):
            flash("Hãy khóa Tier HLV 5–6–5 trước khi sinh lịch GĐ2.","error")
            return _gd2_admin_return(tournament_id)
        if len(members)!=16:
            flash("Cần đúng 16 HLV active trước khi sinh lịch GĐ2.","error")
            return _gd2_admin_return(tournament_id)
        # V1.6.11: opponent fixtures depend ONLY on the 16 HLV + Tier 5–6–5.
        # They may be generated BEFORE the club ceremony and stay secret until
        # Admin reveals them HLV-by-HLV. Club assignment/rerolls never mutate the
        # stored tournament_matches graph.
        if _matches(tournament_id,"league"):
            flash("Lịch GĐ2 đã tồn tại. Không cho sinh lại/xóa lịch tự động để bảo vệ đối thủ đã công bố.","error")
            return _gd2_admin_return(tournament_id)
        pots={int(m.get("pot_no") or 0) for m in members if int(m.get("pot_no") or 0)>0}
        if len(pots)!=3:
            flash("GĐ2 chính thức dùng đúng 3 Pot. Hãy chia 3 Pot 5–6–5 trước khi sinh lịch.","error"); return _gd2_admin_return(tournament_id)
        pot_counts={p:sum(1 for m in members if int(m.get("pot_no") or 0)==p) for p in (1,2,3)}
        if [pot_counts.get(1,0),pot_counts.get(2,0),pot_counts.get(3,0)] != [5,6,5]:
            flash(f"Sai cấu trúc Pot GĐ2: hiện là {pot_counts.get(1,0)}–{pot_counts.get(2,0)}–{pot_counts.get(3,0)}. Cần chia lại đúng 5–6–5.","error")
            return _gd2_admin_return(tournament_id)
        existing_completed=_matches(tournament_id,"league",["completed"])
        if existing_completed:
            flash("League Phase đã có kết quả; không thể sinh lại tự động.","error"); return _gd2_admin_return(tournament_id)
        try:
            rounds=_league_four_match_pairs(tournament_id,members)
        except ValueError as exc:
            flash(str(exc),"error"); return _gd2_admin_return(tournament_id)

        # Validate complete fixture graph BEFORE the first database write.
        pair_keys=set()
        match_counts={str(m.get("user_id")):0 for m in members}
        if len(rounds)!=4 or any(len(pairs)!=8 for pairs in rounds):
            flash("Thuật toán chưa sinh đủ 4 lượt × 8 trận; chưa ghi dữ liệu.","error")
            return _gd2_admin_return(tournament_id)
        for pairs in rounds:
            seen_round=set()
            for a,b in pairs:
                key=tuple(sorted((str(a),str(b))))
                if a==b or key in pair_keys or a in seen_round or b in seen_round or a not in match_counts or b not in match_counts:
                    flash("Lịch GĐ2 có cặp trùng hoặc HLV không hợp lệ; chưa ghi dữ liệu.","error")
                    return _gd2_admin_return(tournament_id)
                pair_keys.add(key)
                seen_round.update((a,b))
                match_counts[a]+=1
                match_counts[b]+=1
        if len(pair_keys)!=32 or any(count!=4 for count in match_counts.values()):
            flash("Lịch GĐ2 chưa bảo đảm 32 trận và 4 trận/HLV; chưa ghi dữ liệu.","error")
            return _gd2_admin_return(tournament_id)
        try:
            validate_four_match_draw(rounds, {str(m.get("user_id")):int(m.get("pot_no") or 0) for m in members})
        except ValueError as exc:
            flash(f"Không sinh lịch: {exc} Chưa ghi database.","error")
            return _gd2_admin_return(tournament_id)

        execute_query(db.table("tournament_settings").upsert({
            "tournament_id":tournament_id,
            "setting_key":"league_config",
            "setting_value":{
                "pot_count":3,
                "pot_sizes":[5,6,5],
                "pot_format":"5-6-5",
                "matches_per_hlv":4,
                "three_tier_coverage_required":True,
                "tier_coverage_scope":"all_four_matches",
                "format":"FOUR_MATCHES_COVER_THREE_TIERS",
            },
            "updated_at":now_iso(),
        },on_conflict="tournament_id,setting_key"),"ops_league_config",attempts=2)
        # Never delete league fixtures: a second generation request must not destroy real results.
        if _matches(tournament_id,"league"):
            flash("Đã có lịch GĐ2. Dừng sinh lịch để bảo vệ dữ liệu.","error")
            return _gd2_admin_return(tournament_id)

        idx=0
        for round_no,pairs in enumerate(rounds,1):
            for a,b in pairs:
                idx+=1
                # Cân bằng home/away theo round + index.
                h,a2=(a,b) if (idx+round_no)%2 else (b,a)
                execute_query(db.table("tournament_matches").insert({
                    "tournament_id":tournament_id,"stage_code":"league",
                    "round_code":f"LP-R{round_no}-{idx}","home_user_id":h,"away_user_id":a2,
                    "status":"pending","leg_no":1,"created_at":now_iso(),"updated_at":now_iso(),
                }),"ops_league_insert",attempts=2)
        flash(f"Đã sinh bí mật {idx} trận GĐ2 theo Tier 5–6–5. Chưa công bố cho HLV; Random/đổi CLB sau đó không làm thay đổi đối thủ.","success")
        return _gd2_admin_return(tournament_id)

    @app.post('/admin/tournaments/<tournament_id>/registration-status')
    @login_required
    @admin_required
    def admin_tournament_registration_status(tournament_id):
        opened=(request.form.get("open") or "0") == "1"
        tour=_tour(tournament_id) or {}
        payload={"registration_open": opened, "updated_at": now_iso()}
        current_status=str(tour.get("status") or "registration")
        if opened:
            if current_status in {"upcoming", "registration"}:
                payload["status"]="registration"
        else:
            if current_status=="registration":
                payload["status"]="upcoming"
        execute_query(db.table("tournaments").update(payload).eq("id",tournament_id),"ops_registration_status",attempts=2)
        log_admin_action("Mở lại đăng ký Giải đấu" if opened else "Kết thúc đăng ký Giải đấu","tournament",details={"tournament_id":tournament_id,"registration_open":opened})
        flash("Đã mở lại đăng ký." if opened else "Đã kết thúc đăng ký. HLV không thể gửi đơn mới cho tới khi Admin mở lại.","success")
        return redirect_admin("tournaments")

    @app.post('/admin/tournaments/<tournament_id>/stage1/start-now')
    @login_required
    @admin_required
    def admin_tournament_stage1_start_now(tournament_id):
        now_value=now_iso()
        execute_query(db.table("tournaments").update({"registration_open":False,"status":"active","updated_at":now_value}).eq("id",tournament_id),"ops_stage1_start_tournament",attempts=2)
        execute_query(db.table("tournament_stages").update({"status":"open","updated_at":now_value}).eq("tournament_id",tournament_id).eq("stage_code","stage1"),"ops_stage1_start_stage",attempts=2)
        current=_setting(tournament_id,"competition_timing",{}) or {}
        start=datetime.now(timezone(timedelta(hours=7)))
        current["stage1_start_at"]=start.isoformat()
        current["stage1_early_end_at"]=(start+timedelta(days=3)).isoformat()
        current["stage1_end_at"]=(start+timedelta(days=7)).isoformat()
        current["stage1_extension_end_at"]=(start+timedelta(days=9)).isoformat()
        execute_query(db.table("tournament_settings").upsert({"tournament_id":tournament_id,"setting_key":"competition_timing","setting_value":current,"updated_at":now_value},on_conflict="tournament_id,setting_key"),"ops_stage1_start_timing",attempts=2)
        log_admin_action("Bắt đầu GĐ1 Giải đấu","tournament_stage",details={"tournament_id":tournament_id,"stage_code":"stage1"})
        flash("Đã bắt đầu GĐ1 và tự động đóng đăng ký. Bước tiếp theo: Random đối thủ GĐ1.","success")
        return redirect_admin("tournaments")

    @app.post('/admin/tournaments/<tournament_id>/timing')
    @login_required
    @admin_required
    def admin_tournament_timing(tournament_id):
        def norm(name):
            raw=(request.form.get(name) or "").strip()
            if not raw: return None
            try:
                return datetime.fromisoformat(raw).replace(tzinfo=timezone(timedelta(hours=7))).isoformat()
            except Exception: return None
        current=_setting(tournament_id,"competition_timing",{}) or {}
        cfg=dict(current) if isinstance(current,dict) else {}
        for k in ("stage1_start_at","stage1_end_at","stage1_early_end_at","stage1_extension_end_at","league_start_at","league_end_at"):
            value=norm(k)
            if value is not None:
                cfg[k]=value
        s1=_parse_iso(cfg.get("stage1_start_at"))
        if s1:
            if not cfg.get("stage1_early_end_at"): cfg["stage1_early_end_at"]=(s1+timedelta(days=3)).isoformat()
            if not cfg.get("stage1_end_at"): cfg["stage1_end_at"]=(s1+timedelta(days=7)).isoformat()
            if not cfg.get("stage1_extension_end_at"): cfg["stage1_extension_end_at"]=(s1+timedelta(days=9)).isoformat()
        lg=_parse_iso(cfg.get("league_start_at"))
        if lg and not cfg.get("league_end_at"): cfg["league_end_at"]=(lg+timedelta(days=7)).isoformat()
        execute_query(db.table("tournament_settings").upsert({"tournament_id":tournament_id,"setting_key":"competition_timing","setting_value":cfg,"updated_at":now_iso()},on_conflict="tournament_id,setting_key"),"ops_timing_save",attempts=2)
        flash("Đã lưu lịch vận hành và đồng hồ đếm ngược.","success"); return redirect_admin("tournaments")

    @app.post('/admin/tournaments/<tournament_id>/stage1/random-generate')
    @login_required
    @admin_required
    def admin_tournament_stage1_random_generate(tournament_id):
        members=[str(m.get("user_id")) for m in _all_members(tournament_id)]
        n=len(members)
        if n<4 or n%2:
            flash("Random 3 đối thủ cần số HLV chẵn và tối thiểu 4.","error"); return redirect_admin("tournaments")
        if _matches(tournament_id,"stage1",["completed"]):
            flash("GĐ1 đã có kết quả, không thể Random lại.","error"); return redirect_admin("tournaments")
        random.shuffle(members)
        edges=set()
        for i,u in enumerate(members):
            for v in (members[(i-1)%n],members[(i+1)%n],members[(i+n//2)%n]):
                if u!=v: edges.add(tuple(sorted((u,v))))
        execute_query(db.table("tournament_matches").delete().eq("tournament_id",tournament_id).eq("stage_code","stage1"),"ops_s1_clear",attempts=2)
        idx=0
        for a,b in sorted(edges):
            for leg,home,away in ((1,a,b),(2,b,a)):
                idx+=1
                execute_query(db.table("tournament_matches").insert({"tournament_id":tournament_id,"stage_code":"stage1","round_code":f"RND-{idx}","home_user_id":home,"away_user_id":away,"status":"pending","leg_no":leg,"created_at":now_iso(),"updated_at":now_iso()}),"ops_s1_random_insert",attempts=2)
        execute_query(db.table("tournament_settings").upsert({"tournament_id":tournament_id,"setting_key":"stage1_player_reveals","setting_value":{},"updated_at":now_iso()},on_conflict="tournament_id,setting_key"),"ops_s1_reveal_reset",attempts=2)
        flash(f"Đã Random GĐ1: {len(edges)} cặp đối thủ · 2 trận/cặp.","success"); return redirect_admin("tournaments")

    def _tournament_landing_return(tournament_id, anchor="schedule"):
        if (request.form.get("return_to") or "").strip() == "tournaments":
            return redirect(url_for("tournaments") + f"#{anchor}-{tournament_id}")
        return redirect(url_for('tournaments') + f"#{anchor}")

    @app.post('/tournaments/<tournament_id>/stage1/reveal')
    @login_required
    def tournament_stage1_reveal(tournament_id):
        uid=str((current_user() or {}).get("id") or "")
        if not _member(tournament_id,uid):
            flash("Bạn chưa thuộc giải đấu này.","error"); return redirect(url_for('tournaments'))
        data=_setting(tournament_id,"stage1_player_reveals",{}) or {}; data[uid]=now_iso()
        execute_query(db.table("tournament_settings").upsert({"tournament_id":tournament_id,"setting_key":"stage1_player_reveals","setting_value":data,"updated_at":now_iso()},on_conflict="tournament_id,setting_key"),"ops_s1_reveal",attempts=2)
        return _tournament_landing_return(tournament_id,"opponents")

    @app.post('/admin/tournaments/<tournament_id>/club-draft/start')
    @login_required
    @admin_required
    def admin_tournament_club_draft_start(tournament_id):
        existing=_setting(tournament_id,"club_draft_v2",{}) or {}
        if existing.get("order") or existing.get("entries"):
            flash("Đã mở Random CLB. Không mở lại để tránh xóa vé, CLB và lịch sử đã cấp.","warning")
            return redirect_admin("tournaments")
        _sync_c1_club_pool(tournament_id)
        # V1.5.4: build one fixed 16-HLV allocation list. Top 1 gets 2 tickets,
        # Top 2–3 get 1 ticket; positions 4–16 are assigned automatically by the system.
        completion=_completion_ranking(tournament_id)
        eligible=[x for x in completion if x.get("eligible")]
        seen={str(x.get("user_id")) for x in eligible}
        fallback=[m for m in _all_members(tournament_id) if str(m.get("user_id")) not in seen]
        allocation=(eligible+fallback)[:16]
        all_order=[str(x.get("user_id")) for x in allocation if x.get("user_id")]
        if not all_order:
            flash("Chưa có HLV để mở chọn CLB.","error"); return redirect_admin("tournaments")
        reward_order=all_order[:3]
        entries={}
        for i,uid in enumerate(all_order,1):
            tickets=2 if i==1 else (1 if i<=3 else 0)
            entries[uid]={"tickets_total":tickets,"tickets_remaining":tickets,"skipped":[],"candidate":None,
                          "status":"active" if i<=3 else "pending_system","finish_rank":i,
                          "allocation_type":"EARLY_REWARD" if i<=3 else "SYSTEM"}
        state={"active":True,"completed":False,"order":reward_order,"all_order":all_order,"current_index":0,"entries":entries,
               "history":[{"at":now_iso(),"user_id":reward_order[0],"action":"REWARD_OPEN","message":"Top 1–3 có thể chọn CLB và sử dụng vé thưởng sớm bất cứ lúc nào."}],
               "deadline_at":None,"system_assigned":False,"flexible_reward_tickets":True}
        execute_query(db.table("tournament_settings").upsert({"tournament_id":tournament_id,"setting_key":"club_draft_v2","setting_value":state,"updated_at":now_iso()},on_conflict="tournament_id,setting_key"),"ops_draft_start",attempts=2)
        flash("Đã ghi nhận vé thưởng sớm 2/1/1. Admin phải Random CLB gốc cho đủ 16 HLV theo Tier/Pot trước khi HLV sử dụng vé.","success"); return redirect_admin("tournaments")

    def _save_reward_draft(tournament_id,state,label):
        entries=state.get("entries") or {}
        reward_ids=[str(x) for x in (state.get("order") or [])]
        all_ids=[str(x) for x in (state.get("all_order") or [])]
        state["flexible_reward_tickets"]=True
        state["deadline_at"]=None
        state["active"]=any(entries.get(uid,{}).get("status")!="selected" for uid in reward_ids)
        state["completed"]=bool(all_ids) and all(entries.get(uid,{}).get("status")=="selected" for uid in all_ids)
        return execute_query(db.table("tournament_settings").upsert({"tournament_id":tournament_id,"setting_key":"club_draft_v2","setting_value":state,"updated_at":now_iso()},on_conflict="tournament_id,setting_key"),label,attempts=2)

    def _early_reward_ticket_phase_open(tournament_id, state):
        """All 16 must receive their base Tier/Pot clubs before any early ticket can be used."""
        order=[str(uid) for uid in (state.get("all_order") or [])]
        if not state.get("system_assigned") or state.get("tier_club_pot_rule") != "1:3;2:2;3:1" or len(order)!=16 or len(set(order))!=16:
            return False
        members={str(m.get("user_id")):m for m in _all_members(tournament_id)}
        return len(members)==16 and all(
            uid in members and bool(members[uid].get("fixed_club_name"))
            and C1_CLUB_POT_BY_NAME.get(members[uid].get("fixed_club_name"))==4-int(members[uid].get("pot_no") or 0)
            for uid in order
        )

    @app.post('/tournaments/<tournament_id>/club-draft/random')
    @login_required
    def tournament_club_draft_random(tournament_id):
        uid=str((current_user() or {}).get("id") or "")
        state=_club_draft_state(tournament_id,False) or {}
        entry=(state.get("entries") or {}).get(uid) or {}
        if not _member(tournament_id,uid) or entry.get("allocation_type")!="EARLY_REWARD" or entry.get("status")=="selected":
            flash("Bạn không có lượt Random CLB chưa chốt.","warning"); return redirect(url_for('tournaments'))
        if not _early_reward_ticket_phase_open(tournament_id,state):
            flash("Chờ Admin Random CLB gốc cho đủ 16 HLV theo Tier/Pot trước khi dùng vé thưởng sớm.","warning")
            return redirect(url_for('tournaments'))
        old=entry.get("candidate")
        if old and int(entry.get("tickets_remaining") or 0)<=0:
            flash("Đã hết vé, hãy chốt CLB hiện tại.","warning"); return redirect(url_for('tournaments'))
        skipped=list(entry.get("skipped") or [])
        if old: skipped.append(str(old.get("id")))
        pool=_available_clubs(tournament_id,skipped)
        if not pool:
            flash("Không còn CLB trống phù hợp. Vé vẫn được giữ nguyên.","warning"); return redirect(url_for('tournaments'))
        club=random.choice(pool)
        if old:
            entry["tickets_remaining"]=int(entry.get("tickets_remaining") or 0)-1
            entry["skipped"]=skipped
            state.setdefault("history",[]).append({"at":now_iso(),"user_id":uid,"action":"SKIP","club":old.get("name"),"message":f"Bỏ qua {old.get('name')} · dùng 1 vé thưởng sớm."})
        entry["candidate"]={"id":str(club.get("id")),"name":club.get("name")}
        entry["status"]="active"; state["entries"][uid]=entry
        state.setdefault("history",[]).append({"at":now_iso(),"user_id":uid,"action":"RANDOM","club":club.get("name"),"message":f"Random ra {club.get('name')}."})
        _save_reward_draft(tournament_id,state,"ops_draft_random_save")
        flash(f"Đã Random ra {club.get('name')}. Hãy chốt CLB hoặc dùng vé để bỏ qua.","success")
        return redirect(url_for('tournaments'))

    @app.post('/tournaments/<tournament_id>/club-draft/accept')
    @login_required
    def tournament_club_draft_accept(tournament_id):
        uid=str((current_user() or {}).get("id") or "")
        state=_club_draft_state(tournament_id,False) or {}
        entry=(state.get("entries") or {}).get(uid) or {}
        if not _member(tournament_id,uid) or entry.get("allocation_type")!="EARLY_REWARD" or entry.get("status")=="selected":
            flash("Không có lượt chọn CLB đang chờ.","warning"); return redirect(url_for('tournaments'))
        if not _early_reward_ticket_phase_open(tournament_id,state):
            flash("Chờ Admin Random CLB gốc cho đủ 16 HLV theo Tier/Pot trước khi dùng vé thưởng sớm.","warning")
            return redirect(url_for('tournaments'))
        candidate=entry.get("candidate") or {}
        if not candidate.get("id"):
            flash("Hãy Random CLB trước.","warning"); return redirect(url_for('tournaments'))
        club,_=_one(db.table("tournament_clubs").select("*").eq("tournament_id",tournament_id).eq("id",candidate["id"]),"ops_draft_accept_lookup")
        if not club or club.get("selected_by") or club.get("name") not in C1_CLUB_POOL:
            flash("CLB đã có người chọn hoặc không hợp lệ. Hãy Random lại.","error"); return redirect(url_for('tournaments'))
        reserved=execute_query(db.table("tournament_clubs").update({"selected_by":uid,"selected_at":now_iso()}).eq("tournament_id",tournament_id).eq("id",club["id"]).is_("selected_by","null"),"ops_reward_club_reserve",attempts=2)
        if not getattr(reserved,"data",None):
            flash("CLB vừa được chọn bởi người khác, hãy Random lại.","error"); return redirect(url_for('tournaments'))
        execute_query(db.table("tournament_members").update({"fixed_club_id":club.get("club_key"),"fixed_club_name":club.get("name")}).eq("tournament_id",tournament_id).eq("user_id",uid),"ops_reward_member_club",attempts=2)
        entry["status"]="selected"; entry["selected_club"]=club.get("name"); state["entries"][uid]=entry
        state.setdefault("history",[]).append({"at":now_iso(),"user_id":uid,"action":"SELECT","club":club.get("name"),"message":f"Chốt {club.get('name')}; vé chưa dùng được bảo lưu."})
        _save_reward_draft(tournament_id,state,"ops_reward_select_save")
        flash(f"Đã chốt {club.get('name')}. Vé còn lại có thể dùng bất cứ lúc nào.","success")
        return redirect(url_for('tournaments'))

    def _reroll_early_ticket_for(tournament_id, uid, admin_actor=None):
        """One guarded POST for a player's ticket or an authorized admin proxy.

        Return to the correct page on database errors; never spend a ticket before
        the new club has been reserved and the member's assignment was written.
        """
        uid=str(uid or "")
        redirect_target = (
            (url_for('admin_tournament_draw_preview',tournament_id=tournament_id)
             if (request.form.get('return_to') or '').strip()=='draw_control'
             else url_for('admin') + '#c1-admin-gd2')
            if admin_actor else url_for('tournaments')
        )
        def reply(message, category='warning'):
            flash(message,category)
            return redirect(redirect_target)

        try:
            member=_member(tournament_id,uid)
            state=_club_draft_state(tournament_id,False) or {}
            entry=(state.get('entries') or {}).get(uid) or {}
            if (not member or str(member.get('status') or '')!='active'
                    or uid not in [str(x) for x in (state.get('order') or [])][:3]
                    or entry.get('allocation_type')!='EARLY_REWARD'
                    or int(entry.get('tickets_remaining') or 0)<=0):
                return reply('HLV không có vé thưởng sớm hợp lệ để dùng.')
            if entry.get('reward_finalized'):
                return reply('CLB đã chốt cuối cùng; không thể dùng thêm vé.')
            phase=_reward_ticket_phase_status(tournament_id,state)
            if phase.get('deadline_reached'):
                _close_reward_ticket_phase(tournament_id,'deadline')
                return reply('Đã hết hạn sử dụng vé thưởng GĐ1.')
            if state.get('tier_club_pot_rule')!='1:3;2:2;3:1':
                return reply('Admin cần xác nhận phân bổ CLB theo Tier/Pot trước khi đổi vé.')
            if not _early_reward_ticket_phase_open(tournament_id,state):
                return reply('Chờ đủ 16 CLB gốc hợp lệ trước khi dùng vé thưởng sớm.')
            old_name=str(member.get('fixed_club_name') or '')
            if not old_name or entry.get('status')!='selected':
                return reply('HLV cần có CLB ban đầu đã chốt trước khi sử dụng vé.')
            old,_=_one(db.table('tournament_clubs').select('*').eq('tournament_id',tournament_id)
                       .eq('name',old_name).eq('selected_by',uid),'ops_early_reroll_old')
            if not old:
                return reply('Không xác minh được quyền sở hữu CLB hiện tại; vé chưa bị trừ.','error')
            skipped=set(str(x) for x in (entry.get('skipped') or []))
            skipped.add(str(old['id']))
            pot_no=int(member.get('pot_no') or 0)
            if pot_no not in (1,2,3):
                return reply('Tier HLV chưa hợp lệ. Admin cần kiểm tra trước khi đổi vé.','error')
            required_pot=4-pot_no
            pool=[c for c in _available_clubs(tournament_id,skipped)
                  if C1_CLUB_POT_BY_NAME.get(c.get('name'))==required_pot]
            if not pool:
                return reply('Pot không còn CLB phù hợp; vé vẫn được giữ nguyên.')
            new=random.choice(pool)

            # Reserve the new club first; do not mutate the ticket state yet.
            reserved=execute_query(db.table('tournament_clubs').update({
                'selected_by':uid,'selected_at':now_iso()
            }).eq('tournament_id',tournament_id).eq('id',new['id'])
              .is_('selected_by','null'),'ops_early_reroll_reserve',attempts=2)
            if not getattr(reserved,'data',None):
                return reply('CLB vừa được chọn bởi người khác. Vé chưa bị trừ; hãy thử lại.')

            def restore_old_assignment():
                # The old club remains reserved until the whole operation completes.
                try:
                    execute_query(db.table('tournament_members').update({
                        'fixed_club_id':old.get('club_key'),'fixed_club_name':old_name
                    }).eq('tournament_id',tournament_id).eq('user_id',uid),
                    'ops_early_reroll_restore_member',attempts=2)
                except Exception:
                    app.logger.exception('Could not restore member after reroll failure tournament=%s user=%s',tournament_id,uid)
                try:
                    execute_query(db.table('tournament_clubs').update({
                        'selected_by':None,'selected_at':None
                    }).eq('tournament_id',tournament_id).eq('id',new['id']).eq('selected_by',uid),
                    'ops_early_reroll_rollback_club',attempts=2)
                except Exception:
                    app.logger.exception('Could not release reserved replacement club tournament=%s user=%s',tournament_id,uid)

            try:
                updated=execute_query(db.table('tournament_members').update({
                    'fixed_club_id':new.get('club_key'),'fixed_club_name':new.get('name')
                }).eq('tournament_id',tournament_id).eq('user_id',uid).eq('fixed_club_name',old_name),
                'ops_early_reroll_member',attempts=2)
                if not getattr(updated,'data',None):
                    restore_old_assignment()
                    return reply('CLB đã thay đổi ở phiên khác; vé chưa bị trừ. Hãy tải lại trang.','warning')
            except Exception:
                restore_old_assignment()
                raise

            # Only persist one ticket spend after the replacement is assigned.
            new_entry=dict(entry)
            new_entry['tickets_remaining']=int(entry['tickets_remaining'])-1
            new_entry['skipped']=list(skipped)
            new_entry['selected_club']=new.get('name')
            new_entry['candidate']={'id':str(new['id']),'name':new.get('name')}
            new_entry['status']='selected'
            if new_entry['tickets_remaining']==0:
                new_entry['reward_finalized']=True
                new_entry['reward_finalized_at']=now_iso()
                new_entry['reward_finalized_reason']='tickets_exhausted'
            new_state=dict(state)
            new_state['entries']=dict(state.get('entries') or {})
            new_state['entries'][uid]=new_entry
            new_state['history']=list(state.get('history') or [])
            actor_label='Admin quay hộ' if admin_actor else 'HLV tự quay'
            new_state['history'].append({
                'at':now_iso(),'user_id':uid,'action':'REROLL','club':new.get('name'),
                'actor_user_id':str(admin_actor or uid),'actor_role':'admin' if admin_actor else 'player',
                'message':f"{actor_label} dùng 1 vé thưởng sớm: {old_name} → {new.get('name')}."
            })
            if new_entry.get('reward_finalized'):
                new_state['history'].append({
                    'at':now_iso(),'user_id':uid,'action':'REWARD_FINALIZE','club':new.get('name'),
                    'message':'Đã dùng hết vé; CLB mới tự động trở thành CLB cuối cùng.'
                })
            try:
                saved=_save_reward_draft(tournament_id,new_state,'ops_early_reroll_save')
                if not getattr(saved,'data',None):
                    raise RuntimeError('Reward ticket state was not persisted')
            except Exception:
                restore_old_assignment()
                raise

            # Do not turn a successful ticket exchange into a broken link if a
            # non-critical cleanup/league-open step fails. Keep an operator log.
            try:
                execute_query(db.table('tournament_clubs').update({
                    'selected_by':None,'selected_at':None
                }).eq('tournament_id',tournament_id).eq('id',old['id']).eq('selected_by',uid),
                'ops_early_reroll_release_old',attempts=2)
            except Exception:
                app.logger.exception('Reroll succeeded but old club release needs operator review tournament=%s user=%s',tournament_id,uid)
            opened=False
            try:
                if _reward_ticket_phase_status(tournament_id,new_state).get('all_finalized'):
                    opened,_msg=_open_league_stage(tournament_id,'all_reward_holders_finalized')
            except Exception:
                app.logger.exception('Reroll succeeded but automatic league opening failed tournament=%s',tournament_id)
            message=(f"Đã dùng vé cuối: {old_name} → {new.get('name')}. CLB đã chốt cuối cùng."
                     if new_entry.get('reward_finalized') else
                     f"Đã dùng 1 vé: {old_name} → {new.get('name')}. Còn {new_entry['tickets_remaining']} vé.")
            return reply(message+(' GĐ2 đã tự mở.' if opened else ''),'success')
        except Exception:
            app.logger.exception('Early club ticket reroll failed tournament=%s user=%s admin_proxy=%s',tournament_id,uid,bool(admin_actor))
            return reply('Đổi CLB chưa hoàn tất vì lỗi dữ liệu. Hãy kiểm tra CLB/vé trước khi thử lại hoặc báo Admin.','error')

    @app.post('/tournaments/<tournament_id>/club-draft/reward-reroll')
    @login_required
    def tournament_club_draft_reward_reroll(tournament_id):
        uid=str((current_user() or {}).get("id") or "")
        return _reroll_early_ticket_for(tournament_id, uid)

    @app.post('/admin/tournaments/<tournament_id>/club-draft/reward-reroll-for')
    @login_required
    @admin_required
    def admin_tournament_reward_reroll_for(tournament_id):
        """Admin may spend exactly one existing ticket on behalf of a selected winner."""
        uid=str(request.form.get("user_id") or "").strip()
        state=_club_draft_state(tournament_id,False) or {}
        if not uid or uid not in [str(x) for x in (state.get("order") or [])][:3]:
            flash("HLV không thuộc Top 1–3 có vé thưởng sớm; không thể quay hộ.","warning")
            return _gd2_admin_return(tournament_id)
        admin_uid=str((current_user() or {}).get("id") or "")
        return _reroll_early_ticket_for(tournament_id, uid, admin_actor=admin_uid)

    @app.post('/tournaments/<tournament_id>/club-draft/finalize')
    @login_required
    def tournament_club_draft_finalize(tournament_id):
        uid=str((current_user() or {}).get("id") or "")
        member=_member(tournament_id,uid)
        state=_club_draft_state(tournament_id,False) or {}
        entry=(state.get("entries") or {}).get(uid) or {}
        if not member or entry.get("allocation_type")!="EARLY_REWARD":
            flash("Bạn không thuộc nhóm HLV có vé thưởng sớm.","warning"); return redirect(url_for('tournaments'))
        if entry.get("reward_finalized"):
            flash("CLB của bạn đã được chốt cuối cùng.","success"); return redirect(url_for('tournaments'))
        if not _early_reward_ticket_phase_open(tournament_id,state) or not member.get("fixed_club_name") or entry.get("status")!="selected":
            flash("Chỉ chốt sau khi 16 HLV đã có CLB gốc và bạn đang có CLB hợp lệ.","warning"); return redirect(url_for('tournaments'))
        left=int(entry.get("tickets_remaining") or 0)
        entry["reward_finalized"]=True
        entry["reward_finalized_at"]=now_iso()
        entry["reward_finalized_reason"]="player"
        entry["tickets_forfeited"]=int(entry.get("tickets_forfeited") or 0)+left
        entry["tickets_remaining"]=0
        state["entries"][uid]=entry
        state.setdefault("history",[]).append({"at":now_iso(),"user_id":uid,"action":"REWARD_FINALIZE","club":member.get("fixed_club_name"),"message":f"HLV chốt CLB cuối cùng {member.get('fixed_club_name')}; {left} vé chưa dùng hết hiệu lực."})
        _save_reward_draft(tournament_id,state,"ops_reward_finalize")
        phase=_reward_ticket_phase_status(tournament_id,state)
        opened=False
        if phase.get("all_finalized"):
            opened,_msg=_open_league_stage(tournament_id,"all_reward_holders_finalized")
        flash(("Đã chốt CLB cuối cùng. Cả 3 HLV đã chốt và GĐ2 đã tự mở." if opened else "Đã chốt CLB cuối cùng. Vé chưa dùng không còn hiệu lực."),"success")
        return redirect(url_for('tournaments'))

    @app.post('/admin/tournaments/<tournament_id>/club-draft/force')
    @login_required
    @admin_required
    def admin_tournament_club_draft_force(tournament_id):
        flash("Để quay hộ, dùng nút Quay hộ · 1 vé ở hàng của HLV Top 1–3. Vé được trừ đúng người và ghi lịch sử.","warning")
        return redirect_admin("tournaments")

    def _club_admin_reply(message, category="error"):
        """Inline feedback for the two club-management forms, regular POST fallback."""
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"ok": category == "success", "message": message}), (200 if category == "success" else 409)
        flash(message, category)
        tournament_id=str((request.view_args or {}).get("tournament_id") or "")
        if (request.form.get("return_to") or "").strip()=="draw_control" and tournament_id:
            return redirect(url_for("admin_tournament_draw_preview",tournament_id=tournament_id))
        return redirect(url_for("admin") + "#c1-admin-gd2")

    def _club_draw_fixtures_safe(tournament_id):
        """Pre-generated 32 pending fixtures are independent of base club assignments."""
        fixtures=_matches(tournament_id,"league")
        return (len(fixtures) in (0,32) and
                all(str(m.get("status") or "pending")=="pending" for m in fixtures) and
                not _matches(tournament_id,"knockout"))

    def _base_draft_config(tournament_id):
        return _setting(tournament_id, "club_base_draft_v1", {}) or {}

    def _base_draft_turn(tournament_id, direction):
        members = sorted(_all_members(tournament_id), key=lambda m: int(m.get("seed_no") or 9999),
                         reverse=(direction == "descending"))
        return next((m for m in members if not m.get("fixed_club_name")), None)

    @app.post('/admin/tournaments/<tournament_id>/clubs/configure-base-draft')
    @login_required
    @admin_required
    def admin_tournament_configure_base_draft(tournament_id):
        direction = request.form.get("direction")
        actor = request.form.get("actor")
        if direction not in {"ascending", "descending"} or actor not in {"admin", "player"}:
            return _club_admin_reply("Chọn thứ tự 1→16 hoặc 16→1 và người Random hợp lệ.")
        stages, _ = _rows(db.table("tournament_stages").select("stage_code,status").eq("tournament_id",tournament_id), "ops_base_draft_stages")
        stages = {str(r.get("stage_code")): r.get("status") for r in stages}
        if stages.get("stage1") != "completed" or stages.get("league") not in {"draft", "pending"} or not _club_draw_fixtures_safe(tournament_id):
            return _club_admin_reply("Chỉ cấu hình sau GĐ1; lịch GĐ2 nếu đã sinh phải có đúng 32 trận chưa thi đấu.")
        members = _all_members(tournament_id)
        ranks = sorted(int(m.get("seed_no") or 0) for m in members)
        if len(members) != 16 or ranks != list(range(1,17)) or [sum(int(m.get("pot_no") or 0)==t for m in members) for t in (1,2,3)] != [5,6,5]:
            return _club_admin_reply("Cần đủ 16 HLV có hạng 1–16 và Tier 5–6–5.")
        if any(m.get("fixed_club_name") for m in members):
            return _club_admin_reply("Đã có CLB được Random. Thu hồi CLB trước khi đổi chế độ/thứ tự để tránh ghi đè.")
        state = _club_draft_state(tournament_id,False) or {}
        if len(state.get("all_order") or []) != 16 or any(int(e.get("tickets_remaining") or 0)<int(e.get("tickets_total") or 0)
            for e in (state.get("entries") or {}).values() if e.get("allocation_type")=="EARLY_REWARD"):
            return _club_admin_reply("Hồ sơ Random chưa đủ hoặc đã dùng vé thưởng; không thể cấu hình lại.")
        if (_setting(tournament_id,"club_selection",{}) or {}).get("open"):
            return _club_admin_reply("Đóng chức năng chọn CLB thủ công trước.")
        payload={"mode":"sequential","direction":direction,"actor":actor,"configured_at":now_iso()}
        try:
            execute_query(db.table("tournament_settings").upsert({"tournament_id":tournament_id,"setting_key":"club_base_draft_v1","setting_value":payload,"updated_at":now_iso()},on_conflict="tournament_id,setting_key"),"ops_base_draft_configure",attempts=2)
        except Exception:
            app.logger.exception("C1 base draft configuration failed: %s",tournament_id)
            return _club_admin_reply("Không lưu được cấu hình Random; kiểm tra log server.")
        return _club_admin_reply("Đã mở Random lần lượt theo hạng; chỉ người được chọn mới có quyền bấm.","success")

    def _allocate_base_club_reply(tournament_id, uid, actor):
        config=_base_draft_config(tournament_id)
        if config.get("mode")!="sequential" or config.get("actor")!=actor:
            message="Chế độ Random hiện tại không cho phép thao tác này."
            return _club_admin_reply(message) if actor=="admin" else (flash(message,"warning") or redirect(url_for("tournaments")))
        turn=_base_draft_turn(tournament_id,config.get("direction"))
        if not turn or str(turn.get("user_id"))!=str(uid):
            message="Chưa đến lượt HLV này hoặc đã Random đủ 16 CLB."
            return _club_admin_reply(message) if actor=="admin" else (flash(message,"warning") or redirect(url_for("tournaments")))
        try:
            result=execute_query(db.rpc("c1_allocate_one_base_club",{"p_tournament_id":tournament_id,"p_user_id":uid,"p_actor":actor}),"ops_base_draft_single_rpc",attempts=1)
            club=getattr(result,"data",None)
            if not isinstance(club,str) or not club:
                raise RuntimeError("Single-club RPC returned no confirmed club")
        except Exception:
            app.logger.exception("C1 base single allocation failed: tournament=%s actor=%s",tournament_id,actor)
            message="Random thất bại ở database. Kiểm tra SQL V1.5.96 và log server; chưa ghi nhận thành công."
            return _club_admin_reply(message) if actor=="admin" else (flash(message,"error") or redirect(url_for("tournaments")))
        if actor=="admin":
            return _club_admin_reply("Đã Random thành công CLB: " + club,"success")
        flash("Bạn đã Random CLB gốc: " + club + ". Không trừ vé thưởng sớm.","success")
        return redirect(url_for("tournaments"))

    @app.post('/admin/tournaments/<tournament_id>/clubs/draw-next')
    @login_required
    @admin_required
    def admin_tournament_club_draw_next(tournament_id):
        """One click = exactly one base club, in descending GĐ1 rank 16→1."""
        members=_all_members(tournament_id)
        ranks=sorted(int(m.get("seed_no") or 0) for m in members)
        if len(members)!=16 or ranks!=list(range(1,17)) or [sum(int(m.get("pot_no") or 0)==t for m in members) for t in (1,2,3)]!=[5,6,5]:
            return _club_admin_reply("Cần đủ 16 HLV active, hạng 1–16 và Tier 5–6–5.")
        config=_base_draft_config(tournament_id)
        assigned=any(m.get("fixed_club_name") for m in members)
        desired={"mode":"sequential","direction":"descending","actor":"admin"}
        if any(config.get(k)!=v for k,v in desired.items()):
            if assigned:
                return _club_admin_reply("Đang có CLB từ chế độ khác. Thu hồi CLB (và đối thủ nếu đã sinh) trước khi bắt đầu lượt 16→1; dữ liệu hiện có được giữ nguyên.")
            stages,_=_rows(db.table("tournament_stages").select("stage_code,status").eq("tournament_id",tournament_id),"ops_draw_next_stages")
            status={str(x.get("stage_code")):x.get("status") for x in stages}
            state=_club_draft_state(tournament_id,False) or {}
            if status.get("stage1")!="completed" or status.get("league") not in {"draft","pending"} or not _club_draw_fixtures_safe(tournament_id):
                return _club_admin_reply("Chỉ Random sau GĐ1; lịch GĐ2 đã sinh phải có đúng 32 trận đang chờ, chưa thi đấu.")
            if len(state.get("all_order") or [])!=16 or (_setting(tournament_id,"club_selection",{}) or {}).get("open"):
                return _club_admin_reply("Cần khởi tạo hồ sơ Random đủ 16 HLV và khóa chọn CLB thủ công.")
            if any(int(e.get("tickets_remaining") or 0)<int(e.get("tickets_total") or 0) for e in (state.get("entries") or {}).values() if e.get("allocation_type")=="EARLY_REWARD"):
                return _club_admin_reply("Đã dùng vé thưởng; không thể khởi tạo lại lượt Random.")
            payload={**desired,"configured_at":now_iso()}
            try:
                execute_query(db.table("tournament_settings").upsert({"tournament_id":tournament_id,"setting_key":"club_base_draft_v1","setting_value":payload,"updated_at":now_iso()},on_conflict="tournament_id,setting_key"),"ops_draw_next_configure",attempts=2)
            except Exception:
                app.logger.exception("Could not configure 16-to-1 club draw: %s",tournament_id)
                return _club_admin_reply("Không lưu được cấu hình Random 16→1; chưa Random CLB.")
        turn=_base_draft_turn(tournament_id,"descending")
        if not turn:
            return _club_admin_reply("Đã Random đủ 16 CLB; không phân bổ thêm.","success")
        return _allocate_base_club_reply(tournament_id,str(turn.get("user_id")),"admin")

    @app.post('/admin/tournaments/<tournament_id>/clubs/random-one')
    @login_required
    @admin_required
    def admin_tournament_random_one_base_club(tournament_id):
        uid=str(request.form.get("user_id") or "")
        return _allocate_base_club_reply(tournament_id,uid,"admin")

    @app.post('/tournaments/<tournament_id>/clubs/random-mine')
    @login_required
    def tournament_random_my_base_club(tournament_id):
        uid=str((current_user() or {}).get("id") or "")
        if not _member(tournament_id,uid):
            flash("Bạn không thuộc giải đấu.","error")
            return redirect(url_for("tournaments"))
        return _allocate_base_club_reply(tournament_id,uid,"player")

    @app.post('/admin/tournaments/<tournament_id>/clubs/rerandom-by-tier')
    @login_required
    @admin_required
    def admin_tournament_rerandom_clubs_by_tier(tournament_id):
        """Correction batch: database RPC commits all 16 allocations or none."""
        if request.form.get("confirm_rule") != "TIER_POT_321":
            return _club_admin_reply("Thiếu thông tin xác thực thao tác Random lại.")
        stages,_=_rows(db.table("tournament_stages").select("stage_code,status").eq("tournament_id",tournament_id),"ops_tier_rerandom_stages")
        status={str(x.get("stage_code")):x.get("status") for x in stages}
        if status.get("stage1")!="completed" or status.get("league") not in {"pending","draft"} or _matches(tournament_id,"league") or _matches(tournament_id,"knockout"):
            return _club_admin_reply(f"Không thể Random: GĐ1={status.get('stage1') or 'chưa có'}, GĐ2={status.get('league') or 'chưa có'}. Cần GĐ1 hoàn tất, GĐ2 chuẩn bị và chưa có lịch/trận GĐ2 hoặc KO.")
        state=_club_draft_state(tournament_id,False) or {}
        members=_all_members(tournament_id)
        grouped={p:[m for m in members if int(m.get("pot_no") or 0)==p] for p in (1,2,3)}
        if len(members)!=16 or [len(grouped[p]) for p in (1,2,3)]!=[5,6,5] or len(state.get("all_order") or [])!=16:
            return _club_admin_reply("Không thể Random: chưa đủ 16 HLV, Tier chưa đúng 5–6–5 hoặc chưa khởi tạo danh sách Random 16 người.")
        if (_setting(tournament_id,"club_selection",{}) or {}).get("open"):
            return _club_admin_reply("Cần khóa chế độ chọn CLB thủ công trước khi Random lại.")
        if any(int(e.get("tickets_remaining") or 0)<int(e.get("tickets_total") or 0)
               for e in (state.get("entries") or {}).values() if e.get("allocation_type")=="EARLY_REWARD"):
            return _club_admin_reply("Đã có HLV dùng vé thưởng sớm; không thể ghi đè CLB đã đổi.")
        config=_base_draft_config(tournament_id)
        if config.get("mode")=="sequential" and any(m.get("fixed_club_name") for m in members):
            return _club_admin_reply("Đang Random lần lượt. Thu hồi CLB trước khi chuyển sang Random toàn bộ.")
        # Sample each exclusive Pot without replacement; preserve the 2/1/1 ticket balances.
        allocations=[]
        for tier,club_pot in ((1,3),(2,2),(3,1)):
            clubs=random.sample(C1_CLUB_POTS[club_pot],len(grouped[tier]))
            for member,club in zip(grouped[tier],clubs):
                allocations.append({"user_id":str(member["user_id"]),"club":club})
        try:
            result=execute_query(db.rpc("c1_admin_rerandom_tier_clubs",{
                "p_tournament_id":tournament_id,"p_assignments":allocations,
            }),"ops_admin_rerandom_tier_rpc",attempts=1)
            if getattr(result,"data",None)!=16:
                raise RuntimeError("RPC did not confirm 16 assignments")
        except Exception:
            app.logger.exception("C1 admin tier/pot correction failed: tournament_id=%s",tournament_id)
            return _club_admin_reply("Random thất bại ở database. Kiểm tra SQL_V1.5.90_ADMIN_RERANDOM_TIER_POT.sql, cấu hình Service Role và log server; không được coi là thành công.")
        try:
            log_admin_action("Random lại 16 CLB theo Tier/Pot","tournament_club",details={"tournament_id":tournament_id,"rule":"Tier1:Pot3;Tier2:Pot2;Tier3:Pot1"})
        except Exception:
            app.logger.exception("Tier/Pot correction succeeded but auxiliary audit failed: %s",tournament_id)
        try:
            execute_query(db.table("tournament_settings").upsert({"tournament_id":tournament_id,"setting_key":"club_base_draft_v1","setting_value":{"mode":"bulk","configured_at":now_iso()},"updated_at":now_iso()},on_conflict="tournament_id,setting_key"),"ops_base_draft_bulk_mode",attempts=2)
        except Exception:
            app.logger.exception("Bulk succeeded but mode metadata save failed: %s",tournament_id)
        return _club_admin_reply("Đã Random lại đủ 16 CLB đúng Tier/Pot, giữ nguyên vé thưởng và lịch sử.", "success")

    @app.post('/admin/tournaments/<tournament_id>/clubs/revoke-all')
    @login_required
    @admin_required
    def admin_tournament_revoke_clubs(tournament_id):
        """Revoke every assigned GĐ2 club atomically; tickets and rewards are untouched."""
        if request.form.get('confirm_revoke') != 'REVOKE_ALL_16_CLUBS':
            return _club_admin_reply('Thiếu thông tin xác thực thao tác thu hồi.')
        stages, _ = _rows(db.table('tournament_stages').select('stage_code,status').eq('tournament_id', tournament_id), 'ops_revoke_stages')
        status = {str(row.get('stage_code')): row.get('status') for row in stages}
        if status.get('stage1') != 'completed' or status.get('league') not in {'draft', 'pending'} or _matches(tournament_id, 'league') or _matches(tournament_id, 'knockout'):
            return _club_admin_reply(f"Không thể thu hồi: GĐ1={status.get('stage1') or 'chưa có'}, GĐ2={status.get('league') or 'chưa có'}. Cần GĐ1 hoàn tất, GĐ2 chuẩn bị và chưa có lịch/trận GĐ2 hoặc KO.")
        if (_setting(tournament_id, 'club_selection', {}) or {}).get('open'):
            return _club_admin_reply('Cần đóng chế độ chọn CLB thủ công trước khi thu hồi.')
        state = _club_draft_state(tournament_id, False) or {}
        if any(int(e.get('tickets_remaining') or 0)<int(e.get('tickets_total') or 0)
               for e in (state.get('entries') or {}).values() if e.get('allocation_type')=='EARLY_REWARD'):
            return _club_admin_reply('Đã có HLV dùng vé thưởng sớm; không thể thu hồi để tránh xóa CLB đã đổi.')
        try:
            result = execute_query(db.rpc('c1_admin_revoke_tier_clubs', {'p_tournament_id': tournament_id}), 'ops_admin_revoke_clubs_rpc', attempts=1)
            if getattr(result, 'data', None) != 16:
                raise RuntimeError('RPC did not confirm all 16 participants')
        except Exception as exc:
            app.logger.exception('C1 club revocation failed: tournament_id=%s', tournament_id)
            # Expose only an allowlisted database code and a known safe explanation to Admin.
            # Never show raw exception text: PostgREST errors may contain identifiers or secrets.
            code = str(getattr(exc, 'code', '') or '')
            if code == 'PGRST202':
                detail = 'Không tìm thấy RPC c1_admin_revoke_tier_clubs(uuid): chạy SQL V1.5.91 trong đúng Supabase project và làm mới schema cache.'
            elif code in {'42501', 'PGRST301', 'PGRST302'}:
                detail = 'Tài khoản kết nối không có quyền EXECUTE: kiểm tra SUPABASE_SERVICE_ROLE_KEY trong môi trường backend và quyền của RPC.'
            elif code in {'23503', '23502', '23505'}:
                detail = 'Ràng buộc database từ chối cập nhật; xem log backend để biết bảng/cột liên quan.'
            elif code == 'P0001':
                detail = 'RPC từ chối vì điều kiện dữ liệu chưa đạt (trạng thái GĐ, lịch, hồ sơ 16 HLV hoặc lựa chọn CLB). Đối chiếu SQL chẩn đoán kèm bản phát hành.'
            elif code:
                detail = 'Mã lỗi database: ' + code[:16] + '. Xem log backend và chạy SQL chẩn đoán kèm bản phát hành.'
            else:
                detail = 'Không nhận được mã lỗi database; xem log backend và chạy SQL chẩn đoán kèm bản phát hành.'
            return _club_admin_reply('Thu hồi chưa được xác nhận. ' + detail + ' Không bấm Random tiếp khi chưa kiểm tra dữ liệu.')
        try:
            log_admin_action('Thu hồi CLB GĐ2 của 16 HLV', 'tournament_club', details={'tournament_id': tournament_id})
        except Exception:
            app.logger.exception('Club revocation succeeded but auxiliary audit failed: %s', tournament_id)
        return _club_admin_reply('Đã thu hồi CLB của 16 HLV, giữ nguyên vé thưởng và lịch sử.', 'success')

    @app.post('/admin/tournaments/<tournament_id>/clubs/assign-remaining')
    @login_required
    @admin_required
    def admin_tournament_assign_remaining_clubs(tournament_id):
        flash("Nút Random hạng 4–16 cũ đã ngừng sử dụng do phân bổ sai Tier/Pot. Hãy dùng nút Admin Random lại đủ 16 CLB.","warning")
        return redirect_admin("tournaments")

    @app.post('/admin/tournaments/<tournament_id>/league/revoke-opponents')
    @login_required
    @admin_required
    def admin_tournament_league_revoke_opponents(tournament_id):
        """V1.6.4: revoke the generated GĐ2 opponent graph before play starts.

        This is intentionally separate from club revocation: Admin must revoke
        opponents first, then clubs. Completed/started GĐ2 data is never deleted.
        """
        stages,_=_rows(db.table("tournament_stages").select("stage_code,status").eq("tournament_id",tournament_id),"ops_revoke_league_stage")
        status={str(x.get("stage_code")):str(x.get("status") or "") for x in stages}
        league_status=status.get("league")
        matches=_matches(tournament_id,"league")
        if not matches:
            flash("Chưa có lịch đối thủ GĐ2 để thu hồi.","warning")
            return _gd2_admin_return(tournament_id)
        if league_status not in {"draft","pending"}:
            flash("Không thể thu hồi đối thủ sau khi GĐ2 đã mở hoặc hoàn tất.","error")
            return _gd2_admin_return(tournament_id)
        if any(str(m.get("status") or "pending")!="pending" for m in matches):
            flash("Có trận GĐ2 đã thay đổi trạng thái/kết quả; không được thu hồi đối thủ.","error")
            return _gd2_admin_return(tournament_id)
        try:
            execute_query(
                db.table("tournament_matches").delete().eq("tournament_id",tournament_id).eq("stage_code","league"),
                "ops_revoke_league_matches",attempts=2,
            )
            execute_query(db.table("tournament_settings").upsert({
                "tournament_id":tournament_id,"setting_key":"league_draw_v2",
                "setting_value":{"active":False,"completed":False,"order":[],"current_index":0,"pot_index":0,"pots":[1,2,3],"revealed":{},"history":[]},
                "updated_at":now_iso(),
            },on_conflict="tournament_id,setting_key"),"ops_revoke_league_draw_state",attempts=2)
            execute_query(db.table("tournament_settings").upsert({
                "tournament_id":tournament_id,"setting_key":"league_player_reveals",
                "setting_value":{},"updated_at":now_iso(),
            },on_conflict="tournament_id,setting_key"),"ops_revoke_league_player_reveals",attempts=2)
            remaining=_matches(tournament_id,"league")
            if remaining:
                raise RuntimeError("League match rows remain after revoke")
            log_admin_action("Thu hồi đối thủ GĐ2","tournament_match",details={"tournament_id":tournament_id,"match_count":len(matches)})
        except Exception:
            app.logger.exception("Could not revoke GĐ2 opponents: %s",tournament_id)
            flash("Thu hồi đối thủ chưa được xác nhận ở database. Dữ liệu không được coi là đã thu hồi.","error")
            return _gd2_admin_return(tournament_id)
        flash(f"Đã thu hồi {len(matches)} trận/đối thủ GĐ2. CLB và vé thưởng được giữ nguyên.","success")
        return _gd2_admin_return(tournament_id)

    @app.post('/admin/tournaments/<tournament_id>/league-draw/start')
    @login_required
    @admin_required
    def admin_tournament_league_draw_start(tournament_id):
        members=sorted(_all_members(tournament_id),key=lambda m:(int(m.get("pot_no") or 99),int(m.get("seed_no") or 9999),m.get("display_name") or ""))
        order=[str(m.get("user_id")) for m in members]
        # V1.6.2: the opponent draw may be revealed while reward tickets are still active.
        # Ticket rerolls modify fixed_club_* only; they never regenerate or mutate
        # tournament_matches, so the opponents stay fixed.
        if not _matches(tournament_id,"league"):
            flash("Hãy sinh lịch League Phase trước.","error"); return _gd2_admin_return(tournament_id)
        state={"active":True,"completed":False,"order":order,"current_index":0,"pot_index":0,"pots":[1,2,3],"revealed":{},"history":[]}
        execute_query(db.table("tournament_settings").upsert({"tournament_id":tournament_id,"setting_key":"league_draw_v2","setting_value":state,"updated_at":now_iso()},on_conflict="tournament_id,setting_key"),"ops_league_draw_start",attempts=2)
        execute_query(db.table("tournament_settings").upsert({"tournament_id":tournament_id,"setting_key":"league_player_reveals","setting_value":{},"updated_at":now_iso()},on_conflict="tournament_id,setting_key"),"ops_league_player_reveal_reset",attempts=2)
        flash("Đã bắt đầu Lễ bốc thăm League Phase chung.","success"); return _gd2_admin_return(tournament_id)

    @app.post('/admin/tournaments/<tournament_id>/league-draw/next')
    @login_required
    @admin_required
    def admin_tournament_league_draw_next(tournament_id):
        """One click reveals all four fixed opponents for one HLV, ranks 1→16."""
        state=_setting(tournament_id,"league_draw_v2",{}) or {}
        members=sorted(_all_members(tournament_id),key=lambda m:(int(m.get("seed_no") or 9999),str(m.get("display_name") or "")))
        if len(members)!=16 or sorted(int(m.get("seed_no") or 0) for m in members)!=list(range(1,17)) or [sum(int(m.get("pot_no") or 0)==t for m in members) for t in (1,2,3)]!=[5,6,5]:
            flash("Cần đúng 16 HLV, hạng 1–16 và Tier 5–6–5.","error"); return _gd2_admin_return(tournament_id)
        matches=[m for m in _matches(tournament_id,"league") if m.get("status")!="cancelled"]
        if len(matches)!=32:
            flash("Phải sinh đủ 32 trận GĐ2 trước khi bốc đối thủ.","error"); return _gd2_admin_return(tournament_id)
        if any(not m.get("fixed_club_name") for m in members):
            flash("Hãy quay đủ 16 CLB trước khi công bố đối thủ; lịch 32 trận đã sinh vẫn được giữ nguyên.","warning")
            return _gd2_admin_return(tournament_id)
        member_map={str(m.get("user_id")):m for m in members}
        opponent_map={uid:[] for uid in member_map}
        pairs=set()
        for match in matches:
            h,a=str(match.get("home_user_id")),str(match.get("away_user_id"))
            pair=tuple(sorted((h,a)))
            if h not in member_map or a not in member_map or h==a or pair in pairs:
                flash("Lịch GĐ2 có cặp trùng hoặc HLV không hợp lệ; không công bố.","error"); return _gd2_admin_return(tournament_id)
            pairs.add(pair);opponent_map[h].append(a);opponent_map[a].append(h)
        if any(len(opp)!=4 or len(set(opp))!=4 or {int(member_map[u].get("pot_no") or 0) for u in opp}!={1,2,3} for opp in opponent_map.values()):
            flash("Lịch GĐ2 chưa đạt 4 đối thủ và đủ 3 Tier cho mọi HLV; không công bố.","error"); return _gd2_admin_return(tournament_id)
        expected_order=[str(m.get("user_id")) for m in members]
        if not state.get("order"):
            # First Bốc tiếp also starts the ceremony; no separate start button.
            state={"active":True,"completed":False,"order":expected_order,"current_index":0,"pot_index":0,"pots":[1,2,3],"revealed":{},"history":[]}
        elif list(map(str,state.get("order") or []))!=expected_order:
            flash("Thứ tự bốc thăm đã lưu không khớp hạng 1–16. Thu hồi đối thủ để khởi tạo lại an toàn.","error");return _gd2_admin_return(tournament_id)
        i=int(state.get("current_index") or 0)
        if state.get("completed") or i>=16:
            flash("Đã công bố đủ 16 HLV.","success");return _gd2_admin_return(tournament_id)
        if not state.get("active"):
            flash("Lễ bốc thăm đã tạm dừng; không ghi đè kết quả cũ.","warning");return _gd2_admin_return(tournament_id)
        uid=expected_order[i]
        # Existing V1.6.4 half-reveals are completed for this HLV in one click.
        opponents=[{"user_id":opp,"name":member_map[opp].get("display_name") or "HLV","pot":int(member_map[opp].get("pot_no") or 0)} for opp in opponent_map[uid]]
        state.setdefault("revealed",{})[uid]=opponents
        state.setdefault("history",[]).append({"at":now_iso(),"user_id":uid,"action":"DRAW_FOUR","opponents":[x["name"] for x in opponents]})
        state["pot_index"]=0;state["current_index"]=i+1
        if i+1>=16:state["active"]=False;state["completed"]=True
        try:
            execute_query(db.table("tournament_settings").upsert({"tournament_id":tournament_id,"setting_key":"league_draw_v2","setting_value":state,"updated_at":now_iso()},on_conflict="tournament_id,setting_key"),"ops_league_draw_next_four",attempts=2)
        except Exception:
            app.logger.exception("Could not save four-opponent reveal: %s",tournament_id)
            flash("Không lưu được công bố đối thủ. Chưa xác nhận lượt bốc này.","error");return _gd2_admin_return(tournament_id)
        opened=False
        if state.get("completed") and _reward_ticket_phase_status(tournament_id).get("all_finalized"):
            opened,_msg=_open_league_stage(tournament_id,"all_reward_holders_finalized")
        flash(("Đã công bố đủ 16 HLV; GĐ2 đã mở vì 3 HLV vé thưởng đã chốt." if opened else f"Đã công bố 4 đối thủ của {member_map[uid].get('display_name') or 'HLV'} ({i+1}/16)."),"success")
        return _gd2_admin_return(tournament_id)

    @app.post('/tournaments/<tournament_id>/league/reveal')
    @login_required
    def tournament_league_reveal(tournament_id):
        uid=str((current_user() or {}).get("id") or ""); draw=_setting(tournament_id,"league_draw_v2",{}) or {}
        if not (draw.get("revealed") or {}).get(uid):
            flash("Đối thủ League Phase của bạn chưa được Admin bốc xong.","warning"); return _tournament_landing_return(tournament_id,"opponents")
        data=_setting(tournament_id,"league_player_reveals",{}) or {}; data[uid]=now_iso()
        execute_query(db.table("tournament_settings").upsert({"tournament_id":tournament_id,"setting_key":"league_player_reveals","setting_value":data,"updated_at":now_iso()},on_conflict="tournament_id,setting_key"),"ops_league_reveal",attempts=2)
        return _tournament_landing_return(tournament_id,"opponents")

    return {k: v for k, v in locals().items() if k.startswith('_') and callable(v)}
