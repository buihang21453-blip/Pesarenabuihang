"""Internal tournament competition partition extracted from the legacy monolith.

Registered only through :mod:`modules.tournament_competition`.
"""

def register_rewards(context):
    globals().update(context)

    @app.post('/admin/tournaments/<tournament_id>/stage1/finish')
    @login_required
    @admin_required
    def admin_tournament_stage1_finish(tournament_id):
        """Prepare GĐ2 without leaving GĐ1 completed when DB rejects pending."""
        force=request.form.get("force")=="1"
        try:
            stages,_=_rows(db.table("tournament_stages").select("stage_code,status")
                           .eq("tournament_id",tournament_id),"ops_s1_finish_stage_gate")
            states={str(s.get("stage_code")):s.get("status") for s in stages}
            if "stage1" not in states or "league" not in states:
                flash("Thiếu bản ghi giai đoạn GĐ1 hoặc GĐ2. Không thay đổi dữ liệu.","error")
                return redirect_admin("tournaments")
            if states["league"] in {"open","locked","completed"}:
                flash("GĐ2 đã mở hoặc hoàn tất; không được đưa về trạng thái chuẩn bị.","error")
                return redirect_admin("tournaments")
            if states["stage1"] not in {"open","locked","completed"}:
                flash("GĐ1 chưa mở; không thể kết thúc.","error")
                return redirect_admin("tournaments")
            pending=[m for m in _matches(tournament_id,"stage1") if m.get("status")!="completed"]
            if pending and not force:
                flash(f"GĐ1 còn {len(pending)} trận chưa hoàn thành. Chỉ kết thúc sớm khi 100% trận xong, hoặc dùng kết thúc sau gia hạn.","warning")
                return redirect_admin("tournaments")
            # Check the DB 'pending' status before changing match/stage1 state.
            # SQL_V1.5.88 fixes the original stage status CHECK that rejects it.
            if states["league"]!="pending":
                execute_query(db.table("tournament_stages").update({
                    "status":"pending","updated_at":now_iso(),
                }).eq("tournament_id",tournament_id).eq("stage_code","league")
                .eq("status",states["league"]),"ops_league_prepare_after_s1",attempts=2)
            if pending and force:
                for m in pending:
                    if m.get("status") not in {"disputed","cancelled"}:
                        execute_query(db.table("tournament_matches").update({
                            "status":"disputed","updated_at":now_iso(),
                        }).eq("id",m.get("id")),"ops_s1_pending_btc",attempts=2)
            if states["stage1"]!="completed":
                execute_query(db.table("tournament_stages").update({
                    "status":"completed","updated_at":now_iso(),
                }).eq("tournament_id",tournament_id).eq("stage_code","stage1"),
                "ops_s1_finish",attempts=2)
        except Exception:
            app.logger.exception("C1 admin stage1 finish failed: tournament_id=%s",tournament_id)
            flash("Không thể kết thúc GĐ1 do lỗi cơ sở dữ liệu. Kiểm tra log Vercel/Supabase và migration SQL_V1.5.88; các bước đã ghi trước lỗi có thể cần kiểm tra lại.","error")
            return redirect_admin("tournaments")
        flash("Đã kết thúc GĐ1. GĐ2 CHƯA bắt đầu: hãy trao thưởng, chia/khóa Pot, chốt CLB và công bố đối thủ.","success")
        return redirect_admin("tournaments")

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

    def _league_top3_reroll_for(tournament_id, uid, admin_actor=None):
        """Spend one post-GĐ2 Top-3 reroll ticket for the target HLV.

        Player and Admin-proxy actions use exactly the same safety gates so an
        Admin can help the HLV without bypassing the Knockout-start lock.
        """
        uid=str(uid or "")
        member=_member(tournament_id,uid)
        if not member:
            flash("HLV không thuộc giải đấu này.","error")
            return redirect(url_for("tournaments")+"#knockout-"+str(tournament_id))
        state=_setting(tournament_id,LEAGUE_TOP3_REROLL_KEY,{}) or {}
        entries=dict(state.get("entries") or {})
        entry=dict(entries.get(uid) or {})
        if entry.get("club_finalized"):
            flash("HLV đã chọn giữ CLB hiện tại và không sử dụng vé Random.","warning")
            return redirect(url_for("tournaments")+"#knockout-"+str(tournament_id))
        if int(entry.get("tickets_remaining") or 0)<=0:
            flash("HLV không còn vé Random lại CLB GĐ2.","warning")
            return redirect(url_for("tournaments")+"#knockout-"+str(tournament_id))
        # V1.6.57+: sinh bracket Top 8 không làm mất vé. Vé vẫn dùng được miễn là
        # chính HLV chưa bắt đầu bất kỳ trận Knockout nào. Admin quay hộ cũng phải
        # đi qua cùng khóa này để không thể đổi CLB giữa một cặp đấu Knockout.
        knockout_for_me=[m for m in _matches(tournament_id,"knockout")
                         if uid in {str(m.get("home_user_id") or ""),str(m.get("away_user_id") or "")}]
        started=[m for m in knockout_for_me if str(m.get("status") or "pending") not in {"pending","scheduled","cancelled"}]
        if started:
            flash("HLV đã bắt đầu vòng Knockout nên vé Random CLB đã được khóa để giữ công bằng cho cặp đấu.","warning")
            return redirect(url_for("tournaments")+"#knockout-"+str(tournament_id))
        old_name=str(member.get("fixed_club_name") or "")
        if not old_name:
            flash("HLV chưa có CLB để Random lại.","warning")
            return redirect(url_for("tournaments")+"#knockout-"+str(tournament_id))
        old_club,_=_one(db.table("tournament_clubs").select("*").eq("tournament_id",tournament_id).eq("name",old_name),"ops_league_reroll_old_club")
        skipped=set(str(x) for x in (entry.get("skipped_club_ids") or []))
        if old_club: skipped.add(str(old_club.get("id")))
        # V1.6.63: tuyệt đối bám đúng Tier HLV đã chốt ở GĐ2. Cột pot_no của
        # tournament_members là Tier HLV (legacy naming), không phải Pot CLB.
        # Quy tắc chính thức: Tier 1 -> Pot 3, Tier 2 -> Pot 2, Tier 3 -> Pot 1.
        hlv_tier=int(member.get("pot_no") or 0)
        expected_club_pot=4-hlv_tier if hlv_tier in {1,2,3} else 0
        if expected_club_pot not in {1,2,3}:
            flash("HLV chưa có Tier hợp lệ nên không thể Random CLB.","error")
            return redirect(url_for("tournaments")+"#knockout-"+str(tournament_id))
        pool=[c for c in _available_clubs(tournament_id,skipped)
              if int(C1_CLUB_POT_BY_NAME.get(str(c.get("name") or "")) or 0)==expected_club_pot]
        if not pool:
            flash(f"Không còn CLB Pot {expected_club_pot} trống phù hợp cho HLV Tier {hlv_tier}.","error")
            return redirect(url_for("tournaments")+"#knockout-"+str(tournament_id))
        new_club=random.choice(pool)
        # Chỉ nhả CLB cũ sau khi đã chắc chắn có CLB mới để nhận.
        if old_club:
            execute_query(db.table("tournament_clubs").update({"selected_by":None,"selected_at":None}).eq("id",old_club.get("id")).eq("selected_by",uid),"ops_league_reroll_release_old",attempts=2)
        _club_assign(tournament_id,uid,new_club)
        entry["tickets_remaining"]=int(entry.get("tickets_remaining") or 0)-1
        entry["skipped_club_ids"]=list(skipped)
        event={"at":now_iso(),"action":"REROLL_CLUB","from":old_name,"to":new_club.get("name"),
               "hlv_tier":hlv_tier,"club_pot":expected_club_pot,"ticket_spent":True}
        if admin_actor:
            event["actor_role"]="admin"
            event["actor_user_id"]=str(admin_actor)
        else:
            event["actor_role"]="player"
            event["actor_user_id"]=uid
        entry.setdefault("history",[]).append(event)
        entries[uid]=entry; state["entries"]=entries; state["updated_at"]=now_iso()
        execute_query(db.table("tournament_settings").upsert({
            "tournament_id":tournament_id,"setting_key":LEAGUE_TOP3_REROLL_KEY,"setting_value":state,"updated_at":now_iso(),
        },on_conflict="tournament_id,setting_key"),"ops_league_top3_reroll_use",attempts=2)
        actor_text="Admin đã dùng hộ 1 vé" if admin_actor else "Đã dùng 1 vé"
        flash(f"{actor_text}: {old_name} → {new_club.get('name')} · Tier {hlv_tier} → Pot {expected_club_pot}. CLB {old_name} sẽ không xuất hiện lại cho HLV này.","success")
        if admin_actor:
            try:
                create_user_notification(
                    uid,
                    "🎲 Admin đã Random lại CLB giúp bạn",
                    f"CLB trước Knockout đã đổi: {old_name} → {new_club.get('name')}. Vé còn lại: {entry.get('tickets_remaining',0)}.",
                    "/tournaments",
                    "c1_league_top3_admin_reroll",
                )
            except Exception:
                pass
        return redirect(url_for("tournaments")+"#knockout-"+str(tournament_id))

    @app.post('/tournaments/<tournament_id>/league-top3/reroll-club')
    @login_required
    def tournament_league_top3_reroll_club(tournament_id):
        # V1.6.68: thao tác vé Random sau GĐ2 là quyền điều hành của Admin בלבד.
        # Giữ route cũ để tương thích link/bookmark nhưng không cho HLV tự sử dụng.
        flash("Vé Random CLB sau GĐ2 chỉ Admin mới được phép sử dụng hộ HLV.","warning")
        return redirect(url_for("tournaments")+"#knockout-"+str(tournament_id))

    @app.post('/admin/tournaments/<tournament_id>/league-top3/reroll-club-for')
    @login_required
    @admin_required
    def admin_tournament_league_top3_reroll_club_for(tournament_id):
        uid=str(request.form.get("user_id") or "")
        admin_uid=str((current_user() or {}).get("id") or "")
        if not uid:
            flash("Thiếu HLV cần Random CLB hộ.","error")
            return redirect(url_for("tournaments")+"#knockout-"+str(tournament_id))
        return _league_top3_reroll_for(tournament_id,uid,admin_actor=admin_uid)

    def _repair_league_top3_wrong_pot(tournament_id, uid, admin_actor=None):
        """Repair an already-assigned Top-3 club that violates Tier -> club-Pot mapping.

        This is a data-recovery action for historical buggy rerolls. It never spends
        another ticket and never restores a consumed ticket; it only replaces the
        invalid current club with an available club from the HLV's correct Pot.
        """
        uid=str(uid or "")
        member=_member(tournament_id,uid)
        if not member:
            flash("HLV không thuộc giải đấu này.","error")
            return redirect(url_for("tournaments")+"#knockout-"+str(tournament_id))
        hlv_tier=int(member.get("pot_no") or 0)
        expected_club_pot=4-hlv_tier if hlv_tier in {1,2,3} else 0
        if expected_club_pot not in {1,2,3}:
            flash("HLV chưa có Tier hợp lệ nên không thể sửa CLB.","error")
            return redirect(url_for("tournaments")+"#knockout-"+str(tournament_id))
        old_name=str(member.get("fixed_club_name") or "")
        current_pot=int(C1_CLUB_POT_BY_NAME.get(old_name) or 0)
        if current_pot==expected_club_pot:
            flash(f"CLB {old_name} đang đúng quy tắc Tier {hlv_tier} → Pot {expected_club_pot}; không cần sửa.","info")
            return redirect(url_for("tournaments")+"#knockout-"+str(tournament_id))
        knockout_for_me=[m for m in _matches(tournament_id,"knockout")
                         if uid in {str(m.get("home_user_id") or ""),str(m.get("away_user_id") or "")}]
        started=[m for m in knockout_for_me if str(m.get("status") or "pending") not in {"pending","scheduled","cancelled"}]
        if started:
            flash("HLV đã bắt đầu Knockout nên không thể tự sửa CLB nữa; BTC cần xử lý thủ công để tránh thay CLB giữa trận.","warning")
            return redirect(url_for("tournaments")+"#knockout-"+str(tournament_id))
        state=_setting(tournament_id,LEAGUE_TOP3_REROLL_KEY,{}) or {}
        entries=dict(state.get("entries") or {})
        entry=dict(entries.get(uid) or {})
        skipped=set(str(x) for x in (entry.get("skipped_club_ids") or []))
        old_club,_=_one(db.table("tournament_clubs").select("*").eq("tournament_id",tournament_id).eq("name",old_name),"ops_league_repair_old_club")
        if old_club:
            skipped.add(str(old_club.get("id")))
        pool=[c for c in _available_clubs(tournament_id,skipped)
              if int(C1_CLUB_POT_BY_NAME.get(str(c.get("name") or "")) or 0)==expected_club_pot]
        if not pool:
            flash(f"Không còn CLB Pot {expected_club_pot} trống để sửa cho HLV Tier {hlv_tier}.","error")
            return redirect(url_for("tournaments")+"#knockout-"+str(tournament_id))
        new_club=random.choice(pool)
        if old_club:
            execute_query(db.table("tournament_clubs").update({"selected_by":None,"selected_at":None})
                          .eq("id",old_club.get("id")).eq("selected_by",uid),
                          "ops_league_repair_release_wrong",attempts=2)
        _club_assign(tournament_id,uid,new_club)
        entry.setdefault("history",[]).append({
            "at":now_iso(),"action":"REPAIR_WRONG_CLUB_POT","from":old_name,"to":new_club.get("name"),
            "hlv_tier":hlv_tier,"expected_club_pot":expected_club_pot,"ticket_spent":False,
            "actor_role":"admin" if admin_actor else "system",
            "actor_user_id":str(admin_actor or ""),
        })
        entries[uid]=entry
        state["entries"]=entries
        state["updated_at"]=now_iso()
        execute_query(db.table("tournament_settings").upsert({
            "tournament_id":tournament_id,"setting_key":LEAGUE_TOP3_REROLL_KEY,
            "setting_value":state,"updated_at":now_iso(),
        },on_conflict="tournament_id,setting_key"),"ops_league_top3_repair_wrong_pot",attempts=2)
        flash(f"Đã sửa CLB sai Pot: {old_name} → {new_club.get('name')} · HLV Tier {hlv_tier} chỉ dùng CLB Pot {expected_club_pot}. Không trừ thêm vé.","success")
        return redirect(url_for("tournaments")+"#knockout-"+str(tournament_id))

    @app.post('/admin/tournaments/<tournament_id>/league-top3/repair-wrong-pot')
    @login_required
    @admin_required
    def admin_tournament_league_top3_repair_wrong_pot(tournament_id):
        uid=str(request.form.get("user_id") or "")
        admin_uid=str((current_user() or {}).get("id") or "")
        if not uid:
            flash("Thiếu HLV cần sửa CLB sai Tier/Pot.","error")
            return redirect(url_for("tournaments")+"#knockout-"+str(tournament_id))
        return _repair_league_top3_wrong_pot(tournament_id,uid,admin_actor=admin_uid)

    def _league_top3_keep_current_club(tournament_id, uid, admin_actor=None):
        """Finalize current club without spending the Top-3 reroll ticket.

        The HLV may do this for themself, and an Admin/Owner may explicitly
        perform the same finalization on the HLV's behalf. The action never
        consumes the reroll ticket; it only closes the reroll decision.
        """
        uid=str(uid or "")
        member=_member(tournament_id,uid)
        if not member:
            flash("HLV không thuộc giải đấu này.","error")
            return redirect(url_for("tournaments")+"#knockout-"+str(tournament_id))
        state=_setting(tournament_id,LEAGUE_TOP3_REROLL_KEY,{}) or {}
        entries=dict(state.get("entries") or {})
        entry=dict(entries.get(uid) or {})
        if not entry:
            flash("HLV không có vé Random CLB Top 3 để chốt.","warning")
            return redirect(url_for("tournaments")+"#knockout-"+str(tournament_id))
        if entry.get("club_finalized"):
            flash("Bạn đã chốt giữ CLB hiện tại.","info")
            return redirect(url_for("tournaments")+"#knockout-"+str(tournament_id))
        knockout_for_me=[m for m in _matches(tournament_id,"knockout")
                         if uid in {str(m.get("home_user_id") or ""),str(m.get("away_user_id") or "")}]
        started=[m for m in knockout_for_me if str(m.get("status") or "pending") not in {"pending","scheduled","cancelled"}]
        if started:
            flash("HLV đã bắt đầu vòng Knockout nên không thể đổi trạng thái vé/CLB nữa.","warning")
            return redirect(url_for("tournaments")+"#knockout-"+str(tournament_id))
        club=str(member.get("fixed_club_name") or "")
        if not club:
            flash("HLV chưa có CLB để chốt.","warning")
            return redirect(url_for("tournaments")+"#knockout-"+str(tournament_id))
        entry["club_finalized"]=True
        entry["ticket_waived"]=True
        entry["finalized_club"]=club
        entry["finalized_at"]=now_iso()
        actor_uid=str(admin_actor or uid)
        actor_role="admin" if admin_actor else "player"
        entry.setdefault("history",[]).append({
            "at":now_iso(),"action":"KEEP_CURRENT_CLUB","club":club,
            "ticket_spent":False,"actor_role":actor_role,"actor_user_id":actor_uid,
            "for_user_id":uid,
        })
        entries[uid]=entry
        state["entries"]=entries
        state["updated_at"]=now_iso()
        execute_query(db.table("tournament_settings").upsert({
            "tournament_id":tournament_id,"setting_key":LEAGUE_TOP3_REROLL_KEY,
            "setting_value":state,"updated_at":now_iso(),
        },on_conflict="tournament_id,setting_key"),"ops_league_top3_keep_current_club",attempts=2)
        if admin_actor:
            flash(f"Admin đã chốt giữ CLB {club} cho HLV. Vé Random không bị sử dụng và quyền Random được đóng lại cho vòng Knockout.","success")
        else:
            flash(f"Đã chọn giữ CLB {club}. Vé Random không bị sử dụng và được đóng lại cho vòng Knockout.","success")
        return redirect(url_for("tournaments")+"#knockout-"+str(tournament_id))

    @app.post('/tournaments/<tournament_id>/league-top3/keep-club')
    @login_required
    def tournament_league_top3_keep_club(tournament_id):
        # V1.6.68: việc chốt giữ CLB cũng chỉ Admin thực hiện để đồng bộ điều hành.
        flash("Chỉ Admin mới được phép chốt giữ CLB cho HLV ở giai đoạn Knockout.","warning")
        return redirect(url_for("tournaments")+"#knockout-"+str(tournament_id))

    @app.post('/admin/tournaments/<tournament_id>/league-top3/keep-club-for')
    @login_required
    @admin_required
    def admin_tournament_league_top3_keep_club_for(tournament_id):
        uid=str(request.form.get("user_id") or "")
        admin_uid=str((current_user() or {}).get("id") or "")
        if not uid:
            flash("Thiếu HLV cần chốt giữ CLB.","error")
            return redirect(url_for("tournaments")+"#knockout-"+str(tournament_id))
        return _league_top3_keep_current_club(tournament_id,uid,admin_actor=admin_uid)

    def _admin_undo_league_top3_reroll(tournament_id, uid, admin_actor=None):
        """Undo the latest un-undone Top-3 reroll and restore its previous club/ticket.

        Admin-only recovery tool. It is intentionally blocked after the HLV has
        started Knockout, and it only restores the exact club saved in reroll
        history when that club is still free and belongs to the HLV's proper Pot.
        """
        uid=str(uid or "")
        member=_member(tournament_id,uid)
        if not member:
            flash("HLV không thuộc giải đấu này.","error")
            return redirect(url_for("tournaments")+"#knockout-"+str(tournament_id))
        state=_setting(tournament_id,LEAGUE_TOP3_REROLL_KEY,{}) or {}
        entries=dict(state.get("entries") or {})
        entry=dict(entries.get(uid) or {})
        history=list(entry.get("history") or [])
        reroll_idx=None
        reroll_event=None
        for idx in range(len(history)-1,-1,-1):
            ev=history[idx] if isinstance(history[idx],dict) else {}
            action=str(ev.get("action") or "")
            is_legacy_reroll=bool(ev.get("from") and ev.get("to") and action not in {"REPAIR_WRONG_CLUB_POT","ADMIN_UNDO_REROLL","KEEP_CURRENT_CLUB"})
            is_reroll=action=="REROLL_CLUB" or is_legacy_reroll
            if is_reroll and not ev.get("undone_at"):
                reroll_idx=idx; reroll_event=dict(ev); break
        if reroll_event is None:
            flash("Không tìm thấy lượt Random CLB nào có thể hoàn tác cho HLV này.","warning")
            return redirect(url_for("tournaments")+"#knockout-"+str(tournament_id))
        knockout_for_me=[m for m in _matches(tournament_id,"knockout")
                         if uid in {str(m.get("home_user_id") or ""),str(m.get("away_user_id") or "")}]
        started=[m for m in knockout_for_me if str(m.get("status") or "pending") not in {"pending","scheduled","cancelled"}]
        if started:
            flash("HLV đã bắt đầu Knockout nên không thể hoàn tác CLB/vé Random nữa.","warning")
            return redirect(url_for("tournaments")+"#knockout-"+str(tournament_id))
        restore_name=str(reroll_event.get("from") or "").strip()
        if not restore_name:
            flash("Lịch sử Random không có CLB cũ để khôi phục.","error")
            return redirect(url_for("tournaments")+"#knockout-"+str(tournament_id))
        hlv_tier=int(member.get("pot_no") or 0)
        expected_club_pot=4-hlv_tier if hlv_tier in {1,2,3} else 0
        restore_pot=int(C1_CLUB_POT_BY_NAME.get(restore_name) or 0)
        if expected_club_pot not in {1,2,3} or restore_pot!=expected_club_pot:
            flash(f"Không thể hoàn tác về {restore_name}: CLB không đúng quy tắc Tier {hlv_tier} → Pot {expected_club_pot}.","error")
            return redirect(url_for("tournaments")+"#knockout-"+str(tournament_id))
        restore_club,_=_one(db.table("tournament_clubs").select("*").eq("tournament_id",tournament_id).eq("name",restore_name),"ops_league_undo_restore_club")
        if not restore_club or not restore_club.get("is_available"):
            flash(f"Không thể hoàn tác: CLB {restore_name} không còn trong pool hợp lệ.","error")
            return redirect(url_for("tournaments")+"#knockout-"+str(tournament_id))
        restore_owner=str(restore_club.get("selected_by") or "")
        if restore_owner and restore_owner!=uid:
            flash(f"Không thể hoàn tác về {restore_name}: CLB này hiện đã được HLV khác sử dụng.","error")
            return redirect(url_for("tournaments")+"#knockout-"+str(tournament_id))
        current_name=str(member.get("fixed_club_name") or "")
        current_club,_=_one(db.table("tournament_clubs").select("*").eq("tournament_id",tournament_id).eq("name",current_name),"ops_league_undo_current_club")
        if current_club and str(current_club.get("id"))!=str(restore_club.get("id")):
            execute_query(db.table("tournament_clubs").update({"selected_by":None,"selected_at":None})
                          .eq("id",current_club.get("id")).eq("selected_by",uid),
                          "ops_league_undo_release_current",attempts=2)
        if restore_owner!=uid:
            _club_assign(tournament_id,uid,restore_club)
        else:
            execute_query(db.table("tournament_members").update({
                "fixed_club_id":restore_club.get("club_key"),"fixed_club_name":restore_club.get("name")
            }).eq("tournament_id",tournament_id).eq("user_id",uid),"ops_league_undo_member_restore",attempts=2)
        total=max(0,int(entry.get("tickets_total") or 0))
        remaining=max(0,int(entry.get("tickets_remaining") or 0))
        entry["tickets_remaining"]=min(total,remaining+1) if total else remaining+1
        skipped=[str(x) for x in (entry.get("skipped_club_ids") or []) if str(x)!=str(restore_club.get("id"))]
        entry["skipped_club_ids"]=skipped
        entry.pop("club_finalized",None); entry.pop("ticket_waived",None)
        entry.pop("finalized_club",None); entry.pop("finalized_at",None)
        reroll_event["undone_at"]=now_iso()
        reroll_event["undone_by"]=str(admin_actor or "")
        history[reroll_idx]=reroll_event
        history.append({
            "at":now_iso(),"action":"ADMIN_UNDO_REROLL","from":current_name,"to":restore_name,
            "restored_ticket":True,"actor_role":"admin","actor_user_id":str(admin_actor or ""),
            "source_reroll_at":reroll_event.get("at"),
        })
        entry["history"]=history
        entries[uid]=entry; state["entries"]=entries; state["updated_at"]=now_iso()
        execute_query(db.table("tournament_settings").upsert({
            "tournament_id":tournament_id,"setting_key":LEAGUE_TOP3_REROLL_KEY,
            "setting_value":state,"updated_at":now_iso(),
        },on_conflict="tournament_id,setting_key"),"ops_league_top3_undo_reroll",attempts=2)
        flash(f"Đã hoàn tác vé Random: {current_name} → {restore_name}. Vé Random của HLV đã được khôi phục.","success")
        try:
            create_user_notification(
                uid,"↩ Admin đã hoàn tác vé Random CLB",
                f"CLB của bạn đã được khôi phục về {restore_name}; vé Random cũng đã được trả lại.",
                "/tournaments","c1_league_top3_admin_undo_reroll",
            )
        except Exception:
            pass
        return redirect(url_for("tournaments")+"#knockout-"+str(tournament_id))

    @app.post('/admin/tournaments/<tournament_id>/league-top3/undo-reroll')
    @login_required
    @admin_required
    def admin_tournament_league_top3_undo_reroll(tournament_id):
        uid=str(request.form.get("user_id") or "")
        admin_uid=str((current_user() or {}).get("id") or "")
        if not uid:
            flash("Thiếu HLV cần hoàn tác vé Random.","error")
            return redirect(url_for("tournaments")+"#knockout-"+str(tournament_id))
        return _admin_undo_league_top3_reroll(tournament_id,uid,admin_actor=admin_uid)

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
        execute_query(db.table("tournament_settings").upsert({
            "tournament_id":tournament_id,"setting_key":KNOCKOUT_UNLOCK_KEY,
            "setting_value":{"entries":{},"sequence":0,"updated_at":now_iso()},"updated_at":now_iso(),
        },on_conflict="tournament_id,setting_key"),"ops_ko_unlock_reset",attempts=2)
        for i in range(4):
            _insert_ko_pair(tournament_id,"qf",ids[i],ids[-(i+1)],True)
        execute_query(db.table("tournament_settings").upsert({"tournament_id":tournament_id,"setting_key":"knockout_flow","setting_value":state,"updated_at":now_iso()},on_conflict="tournament_id,setting_key"),"ops_ko_generate_state",attempts=2)
        execute_query(db.table("tournament_stages").update({"status":"open","updated_at":now_iso()}).eq("tournament_id",tournament_id).eq("stage_code","knockout"),"ops_ko_generate_open",attempts=2)
        flash("Đã sinh Knockout: Top 8 vào thẳng Tứ kết · không Play-off.","success"); return redirect_admin("tournaments")

    @app.post('/admin/tournaments/<tournament_id>/knockout/pair-access')
    @login_required
    @admin_required
    def admin_tournament_knockout_pair_access(tournament_id):
        pair_key=str(request.form.get("pair_key") or "").strip()
        action=str(request.form.get("action") or "unlock").strip().lower()
        if not pair_key or action not in {"unlock","lock"}:
            flash("Yêu cầu mở/khóa cặp Knockout không hợp lệ.","error")
            return redirect_admin("tournaments")
        legs=[m for m in _matches(tournament_id,"knockout") if _knockout_pair_key(m)==pair_key]
        if not legs:
            flash("Không tìm thấy cặp Knockout này.","error")
            return redirect_admin("tournaments")
        statuses={str(x.get("status") or "pending") for x in legs}
        if "playing" in statuses:
            flash("Cặp đấu đang thi đấu nên không thể thay đổi khóa.","warning")
            return redirect_admin("tournaments")
        if all(x in {"completed","cancelled"} for x in statuses):
            flash("Cặp đấu đã hoàn tất nên không cần thay đổi khóa.","warning")
            return redirect_admin("tournaments")
        if action=="lock" and ("completed" in statuses or "disputed" in statuses):
            flash("Cặp đấu đã có kết quả/đang chờ xử lý nên không thể khóa lại.","warning")
            return redirect_admin("tournaments")
        state=_knockout_unlock_state(tournament_id)
        entries=dict(state.get("entries") or {})
        entry=dict(entries.get(pair_key) or {})
        if action=="unlock":
            if not entry.get("unlocked"):
                seq=int(state.get("sequence") or 0)+1
                state["sequence"]=seq
                entry.update({"unlocked":True,"unlock_order":seq,"unlocked_at":now_iso(),"unlocked_by":str((current_user() or {}).get("id") or "admin")})
            msg="Đã mở cặp Knockout. Hai HLV có thể vào Phòng đấu C1."
        else:
            entry.update({"unlocked":False,"locked_at":now_iso(),"locked_by":str((current_user() or {}).get("id") or "admin")})
            msg="Đã khóa lại cặp Knockout. Hai HLV chưa thể vào phòng."
        entries[pair_key]=entry
        state["entries"]=entries; state["updated_at"]=now_iso()
        execute_query(db.table("tournament_settings").upsert({
            "tournament_id":tournament_id,"setting_key":KNOCKOUT_UNLOCK_KEY,
            "setting_value":state,"updated_at":now_iso(),
        },on_conflict="tournament_id,setting_key"),"ops_ko_pair_access_save",attempts=2)
        flash(msg,"success")
        return redirect_admin("tournaments")

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

    def _grant_stage1_early_rewards(tournament_id):
        """Shared idempotent reward engine for automatic and manual invocation."""
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

    @app.post('/admin/tournaments/<tournament_id>/stage1/early-rewards/grant')
    @login_required
    @admin_required
    def admin_tournament_stage1_early_rewards_grant(tournament_id):
        return _grant_stage1_early_rewards(tournament_id)

    def _auto_finish_stage1(tournament_id):
        """Finish confirmed GĐ1 and resume Pot setup after an interrupted request.

        Reward transfers use deterministic idempotency keys; Pot updates are
        repeatable. A completed stage must still be checked for incomplete Pot
        preparation instead of returning early forever.
        """
        stage=_stage(tournament_id,"stage1") or {}
        if stage.get("status") not in {"open","locked","completed"}:
            return False
        matches=_matches(tournament_id,"stage1")
        if not matches or any(m.get("status")!="completed" for m in matches):
            return False
        members=_all_members(tournament_id)
        progress=_stage1_progress(tournament_id)
        if len(members)!=16 or len(progress)!=16 or any(not row.get("eligible") for row in progress):
            return False
        ranking=_ranking(tournament_id,"stage1")
        if len(ranking)!=16 or len({str(r.get("user_id")) for r in ranking})!=16:
            app.logger.error("C1 auto-finish: invalid 16-member ranking; refusing transition")
            return False
        # Reward operations have stable per-user idempotency keys. Run before
        # changing the stage so an exception leaves a retriable state.
        _grant_stage1_early_rewards(tournament_id)
        if stage.get("status")!="completed":
            updated=execute_query(db.table("tournament_stages").update({
                "status":"completed","updated_at":now_iso(),
            }).eq("tournament_id",tournament_id).eq("stage_code","stage1").eq("status",stage["status"]),
            "ops_stage1_auto_finish",attempts=2)
            if not (updated.data or []):
                # Another request may have finished the stage; its Pot setup
                # can still be resumed on the next invocation.
                return False
        expected={str(row["user_id"]):(1 if i<5 else 2 if i<11 else 3,i+1)
                  for i,row in enumerate(ranking)}
        for member in members:
            uid=str(member.get("user_id") or "")
            pot,seed=expected[uid]
            if int(member.get("pot_no") or 0)!=pot or int(member.get("seed_no") or 0)!=seed:
                execute_query(db.table("tournament_members").update({
                    "pot_no":pot,"seed_no":seed,
                }).eq("tournament_id",tournament_id).eq("user_id",uid),
                "ops_stage1_auto_pot",attempts=2)
        verified=_all_members(tournament_id)
        if len(verified)!=16 or any(
            (int(m.get("pot_no") or 0),int(m.get("seed_no") or 0))!=expected.get(str(m.get("user_id")))
            for m in verified
        ):
            app.logger.error("C1 Pot verification failed; automatic lock withheld")
            return False
        execute_query(db.table("tournament_settings").upsert({
            "tournament_id":tournament_id,"setting_key":"pots_locked",
            "setting_value":{"locked":True,"pot_count":3,"pot_sizes":[5,6,5],
                             "pot_format":"5-6-5","auto_at":now_iso()},
            "updated_at":now_iso(),
        },on_conflict="tournament_id,setting_key"),"ops_stage1_auto_lock_pots",attempts=2)
        lock=_setting(tournament_id,"pots_locked",{}) or {}
        if not lock.get("locked"):
            app.logger.error("C1 Pot lock not persisted; GĐ2 preparation withheld")
            return False
        execute_query(db.table("tournament_stages").update({
            "status":"pending","updated_at":now_iso(),
        }).eq("tournament_id",tournament_id).eq("stage_code","league").neq("status","open"),
        "ops_stage1_auto_prepare_league",attempts=2)
        timing=_setting(tournament_id,"competition_timing",{}) or {}
        if not timing.get("league_start_at"):
            timing["league_start_at"]=(datetime.now(timezone(timedelta(hours=7)))+timedelta(days=2)).isoformat()
            execute_query(db.table("tournament_settings").upsert({
                "tournament_id":tournament_id,"setting_key":"competition_timing",
                "setting_value":timing,"updated_at":now_iso(),
            },on_conflict="tournament_id,setting_key"),"ops_stage1_auto_schedule_league",attempts=2)
        return True

    @app.post('/admin/tournaments/<tournament_id>/rewards/add')
    @login_required
    @admin_required
    def admin_tournament_reward_add(tournament_id):
        payload={"tournament_id":tournament_id,"name":(request.form.get("name") or "Thưởng sớm").strip(),"stage_code":request.form.get("stage_code") or "stage1","reward_type":request.form.get("reward_type") or "zcoin","reward_value":request.form.get("reward_value") or "0","deadline_at":request.form.get("deadline_at") or None,"enabled":True,"priority":int(request.form.get("priority") or 100),"created_at":now_iso()}
        execute_query(db.table("tournament_reward_rules").insert(payload),"ops_reward_add",attempts=2)
        flash("Đã thêm mức thưởng.","success"); return redirect_admin("tournaments")

    return {k: v for k, v in locals().items() if (k.startswith('_') and callable(v)) or k.isupper()}
