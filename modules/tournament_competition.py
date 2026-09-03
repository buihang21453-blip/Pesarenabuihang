"""Tournament competition operations (V1.4.30).

Independent from Rank/Season. Handles stages, tournament-only matches, ranking,
Pot, club lock, scheduling, hosts, progress, knockout/two legs and early rewards.
"""
from datetime import datetime, timezone
import uuid

STAGE_LABELS = {
    "stage1": "GĐ1 · Phân hạng",
    "league": "League Phase",
    "knockout": "Knockout",
}
ROUND_ORDER = ["playoff", "r16", "qf", "sf", "final"]


def register_routes(context):
    globals().update(context)

    def _rows(query, label):
        try:
            result = execute_query(query, label, attempts=2)
            return [dict(x) for x in (result.data or [])], None
        except Exception as exc:
            app.logger.warning("Tournament ops unavailable [%s]: %s", label, exc)
            return [], str(exc)

    def _one(query, label):
        rows, err = _rows(query.limit(1), label)
        return (rows[0] if rows else None), err

    def _tour(tournament_id):
        return _one(db.table("tournaments").select("*").eq("id", tournament_id), "ops_tournament")[0]

    def _member(tournament_id, user_id):
        if not user_id:
            return None
        return _one(db.table("tournament_members").select("*").eq("tournament_id", tournament_id).eq("user_id", user_id), "ops_member")[0]

    def _stage(tournament_id, code):
        return _one(db.table("tournament_stages").select("*").eq("tournament_id", tournament_id).eq("stage_code", code), "ops_stage")[0]

    def _all_members(tournament_id):
        rows, _ = _rows(db.table("tournament_members").select("*").eq("tournament_id", tournament_id).eq("status", "active").order("approved_at"), "ops_members")
        ids = [str(r.get("user_id")) for r in rows if r.get("user_id")]
        users = {}
        if ids:
            urows, _ = _rows(db.table("users").select("id,username,display_name,avatar_url").in_("id", ids), "ops_member_users")
            users = {str(u.get("id")):u for u in urows}
        for r in rows:
            u=users.get(str(r.get("user_id"))) or {}
            r["display_name"] = u.get("display_name") or u.get("username") or "HLV"
            r["user"] = u
        return rows

    def _matches(tournament_id, stage_code=None, statuses=None):
        q=db.table("tournament_matches").select("*").eq("tournament_id", tournament_id)
        if stage_code:
            q=q.eq("stage_code", stage_code)
        if statuses:
            q=q.in_("status", statuses)
        rows,_=_rows(q.order("created_at"), "ops_matches")
        return rows

    def _ranking(tournament_id, stage_code):
        members=_all_members(tournament_id)
        table={str(m["user_id"]):{
            "user_id":str(m["user_id"]),"display_name":m["display_name"],"played":0,"wins":0,"draws":0,"losses":0,
            "gf":0,"ga":0,"gd":0,"points":0,"opponents":set(),"pot_no":m.get("pot_no"),"seed_no":m.get("seed_no"),
            "club":m.get("fixed_club_name") or ""
        } for m in members}
        for match in _matches(tournament_id, stage_code, ["completed"]):
            h,a=str(match.get("home_user_id")),str(match.get("away_user_id"))
            if h not in table or a not in table: continue
            try: hs,as_=int(match.get("home_score") or 0),int(match.get("away_score") or 0)
            except Exception: continue
            H,A=table[h],table[a]
            for row,gf,ga,opp in ((H,hs,as_,a),(A,as_,hs,h)):
                row["played"]+=1; row["gf"]+=gf; row["ga"]+=ga; row["opponents"].add(opp)
            if hs>as_: H["wins"]+=1; H["points"]+=3; A["losses"]+=1
            elif hs<as_: A["wins"]+=1; A["points"]+=3; H["losses"]+=1
            else: H["draws"]+=1; A["draws"]+=1; H["points"]+=1; A["points"]+=1
        values=[]
        for row in table.values():
            row["gd"]=row["gf"]-row["ga"]
            row["opponent_count"]=len(row.pop("opponents"))
            values.append(row)
        values.sort(key=lambda x:(x["points"],x["gd"],x["gf"],x["wins"]), reverse=True)
        for i,row in enumerate(values,1): row["rank"]=i
        return values

    def _stage1_progress(tournament_id):
        stage=_stage(tournament_id,"stage1") or {}
        target=int(stage.get("match_target") or 5)
        min_opp=int(stage.get("min_opponents") or 3)
        ranking=_ranking(tournament_id,"stage1")
        for r in ranking:
            r["target"]=target
            r["remaining"]=max(0,target-r["played"])
            r["percent"]=min(100, round((r["played"]/target)*100)) if target else 100
            r["eligible"]=r["played"]>=target and r["opponent_count"]>=min_opp
        return ranking

    def _decorate_matches(tournament_id, rows):
        members={str(m["user_id"]):m for m in _all_members(tournament_id)}
        hosts,_=_rows(db.table("tournament_hosts").select("*").eq("tournament_id",tournament_id),"ops_hosts_decor")
        hostmap={str(h.get("id")):h for h in hosts}
        for m in rows:
            m["home_name"]=(members.get(str(m.get("home_user_id"))) or {}).get("display_name","HLV")
            m["away_name"]=(members.get(str(m.get("away_user_id"))) or {}).get("display_name","HLV")
            m["host"] = hostmap.get(str(m.get("host_id")))
        return rows

    def _reward_summary(tournament_id,user_id):
        rules,_=_rows(db.table("tournament_reward_rules").select("*").eq("tournament_id",tournament_id).eq("enabled",True).order("priority"),"ops_rewards")
        grants,_=_rows(db.table("tournament_reward_grants").select("*").eq("tournament_id",tournament_id).eq("user_id",user_id),"ops_reward_grants")
        return {"rules":rules,"grants":grants}

    def _detail_payload(tournament_id, user_id):
        tour=_tour(tournament_id)
        if not tour: return None
        member=_member(tournament_id,user_id)
        stages,_=_rows(db.table("tournament_stages").select("*").eq("tournament_id",tournament_id).order("sort_order"),"ops_stages")
        s1=_stage1_progress(tournament_id)
        league=_ranking(tournament_id,"league")
        matches=_decorate_matches(tournament_id,_matches(tournament_id))
        hosts,_=_rows(db.table("tournament_hosts").select("*").eq("tournament_id",tournament_id).order("region").order("name"),"ops_hosts")
        clubs,_=_rows(db.table("tournament_clubs").select("*").eq("tournament_id",tournament_id).order("name"),"ops_clubs")
        me_progress=next((r for r in s1 if str(r["user_id"])==str(user_id)),None)
        return {"tournament":tour,"member":member,"stages":stages,"stage1_ranking":s1,"league_ranking":league,
                "matches":matches,"hosts":hosts,"clubs":clubs,"me_progress":me_progress,"rewards":_reward_summary(tournament_id,user_id)}

    def _admin_payload():
        tours,_=_rows(db.table("tournaments").select("*").eq("is_visible",True).order("created_at"),"ops_admin_tours")
        if not tours: return {"ready":True,"tournament":None}
        tour=tours[0]; tid=tour["id"]
        payload=_detail_payload(tid,(current_user() or {}).get("id")) or {}
        payload.update({"ready":True,"tournament":tour,"members":_all_members(tid),"progress":_stage1_progress(tid)})
        return payload

    @app.context_processor
    def inject_tournament_ops():
        if request.endpoint == "admin":
            try: return {"tournament_ops_admin":_admin_payload()}
            except Exception as exc:
                app.logger.warning("Tournament admin ops context: %s",exc)
                return {"tournament_ops_admin":{"ready":False}}
        return {}

    @app.get('/tournaments/<tournament_id>')
    @login_required
    def tournament_detail(tournament_id):
        data=_detail_payload(tournament_id,(current_user() or {}).get("id"))
        if not data:
            flash("Không tìm thấy giải đấu.","error"); return redirect(url_for("tournaments"))
        return render_template('tournament_detail.html', **data)

    @app.post('/admin/tournaments/<tournament_id>/members/<user_id>/remove')
    @login_required
    @admin_required
    @admin_permission_required("system_features_manage")
    def admin_tournament_member_remove(tournament_id,user_id):
        execute_query(db.table("tournament_members").update({"status":"withdrawn"}).eq("tournament_id",tournament_id).eq("user_id",user_id),"ops_member_remove",attempts=2)
        log_admin_action("Xóa HLV khỏi giải","tournament_member",details={"tournament_id":tournament_id,"user_id":user_id})
        flash("Đã xóa HLV khỏi danh sách thi đấu.","success"); return redirect_admin("tournaments")

    @app.post('/admin/tournaments/<tournament_id>/stages/<stage_code>/status')
    @login_required
    @admin_required
    @admin_permission_required("system_features_manage")
    def admin_tournament_stage_status(tournament_id,stage_code):
        status=(request.form.get("status") or "locked").strip()
        if status not in {"draft","open","locked","completed"}: status="locked"
        execute_query(db.table("tournament_stages").update({"status":status,"updated_at":now_iso()}).eq("tournament_id",tournament_id).eq("stage_code",stage_code),"ops_stage_status",attempts=2)
        flash(f"Đã cập nhật {STAGE_LABELS.get(stage_code,stage_code)}: {status}.","success"); return redirect_admin("tournaments")

    @app.post('/admin/tournaments/<tournament_id>/stage1/settings')
    @login_required
    @admin_required
    @admin_permission_required("system_features_manage")
    def admin_tournament_stage1_settings(tournament_id):
        target=max(1,min(20,int(request.form.get("match_target") or 5)))
        min_opp=max(1,min(target,int(request.form.get("min_opponents") or 3)))
        max_same=max(1,min(target,int(request.form.get("max_per_opponent") or 2)))
        execute_query(db.table("tournament_stages").update({"match_target":target,"min_opponents":min_opp,"max_matches_per_opponent":max_same,"updated_at":now_iso()}).eq("tournament_id",tournament_id).eq("stage_code","stage1"),"ops_stage1_settings",attempts=2)
        flash("Đã lưu luật GĐ1.","success"); return redirect_admin("tournaments")

    @app.post('/admin/tournaments/<tournament_id>/matches/add')
    @login_required
    @admin_required
    @admin_permission_required("system_features_manage")
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
    @admin_permission_required("system_features_manage")
    def admin_tournament_match_result(match_id):
        match,_=_one(db.table("tournament_matches").select("*").eq("id",match_id),"ops_match_result_lookup")
        if not match:
            flash("Không tìm thấy trận.","error"); return redirect_admin("tournaments")
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
        log_admin_action("Cập nhật kết quả trận giải","tournament_match",details={"match_id":match_id,"score":f"{hs}-{aw}"})
        flash("Đã lưu kết quả trận giải.","success"); return redirect_admin("tournaments")

    @app.post('/admin/tournaments/<tournament_id>/pot/generate')
    @login_required
    @admin_required
    @admin_permission_required("system_features_manage")
    def admin_tournament_generate_pots(tournament_id):
        pot_count=max(1,min(8,int(request.form.get("pot_count") or 4)))
        ranking=_ranking(tournament_id,"stage1")
        if not ranking:
            flash("Chưa có HLV để chia Pot.","error"); return redirect_admin("tournaments")
        size=(len(ranking)+pot_count-1)//pot_count
        for i,row in enumerate(ranking):
            pot=min(pot_count,(i//size)+1)
            execute_query(db.table("tournament_members").update({"pot_no":pot,"seed_no":i+1}).eq("tournament_id",tournament_id).eq("user_id",row["user_id"]),"ops_pot_update",attempts=2)
        execute_query(db.table("tournament_settings").upsert({"tournament_id":tournament_id,"setting_key":"pots_locked","setting_value":{"locked":False,"pot_count":pot_count},"updated_at":now_iso()},on_conflict="tournament_id,setting_key"),"ops_pot_setting",attempts=2)
        flash(f"Đã chia {pot_count} Pot theo BXH GĐ1.","success"); return redirect_admin("tournaments")

    @app.post('/admin/tournaments/<tournament_id>/pot/lock')
    @login_required
    @admin_required
    @admin_permission_required("system_features_manage")
    def admin_tournament_lock_pots(tournament_id):
        locked=request.form.get("locked")=="1"
        execute_query(db.table("tournament_settings").upsert({"tournament_id":tournament_id,"setting_key":"pots_locked","setting_value":{"locked":locked},"updated_at":now_iso()},on_conflict="tournament_id,setting_key"),"ops_pot_lock",attempts=2)
        flash("Đã khóa Pot." if locked else "Đã mở chỉnh Pot.","success"); return redirect_admin("tournaments")

    def _setting(tournament_id,key,default=None):
        row,_=_one(db.table("tournament_settings").select("setting_value").eq("tournament_id",tournament_id).eq("setting_key",key),"ops_setting")
        return (row or {}).get("setting_value",default)

    @app.post('/tournaments/<tournament_id>/club/select')
    @login_required
    def tournament_club_select(tournament_id):
        user=current_user() or {}; uid=user.get("id")
        if not _member(tournament_id,uid): flash("Bạn không thuộc giải đấu này.","error"); return redirect(url_for("tournament_detail",tournament_id=tournament_id))
        state=_setting(tournament_id,"club_selection",{"open":False}) or {}
        if not state.get("open"):
            flash("Lượt chọn CLB đang khóa.","warning"); return redirect(url_for("tournament_detail",tournament_id=tournament_id))
        club_id=str(request.form.get("club_id") or "").strip()
        club,_=_one(db.table("tournament_clubs").select("*").eq("tournament_id",tournament_id).eq("id",club_id),"ops_club_lookup")
        if not club or not club.get("is_available") or (club.get("selected_by") and str(club.get("selected_by"))!=str(uid)):
            flash("CLB này không còn trống.","error"); return redirect(url_for("tournament_detail",tournament_id=tournament_id))
        # release old selection, reserve chosen atomically enough for admin-scale use
        execute_query(db.table("tournament_clubs").update({"selected_by":None,"selected_at":None}).eq("tournament_id",tournament_id).eq("selected_by",uid),"ops_club_release",attempts=2)
        execute_query(db.table("tournament_clubs").update({"selected_by":uid,"selected_at":now_iso()}).eq("id",club_id).is_("selected_by","null"),"ops_club_reserve",attempts=2)
        execute_query(db.table("tournament_members").update({"fixed_club_id":club.get("club_key"),"fixed_club_name":club.get("name")}).eq("tournament_id",tournament_id).eq("user_id",uid),"ops_member_club",attempts=2)
        flash(f"Đã chọn {club.get('name')}.","success"); return redirect(url_for("tournament_detail",tournament_id=tournament_id))

    @app.post('/admin/tournaments/<tournament_id>/club-selection')
    @login_required
    @admin_required
    @admin_permission_required("system_features_manage")
    def admin_tournament_club_selection(tournament_id):
        opened=request.form.get("open")=="1"
        execute_query(db.table("tournament_settings").upsert({"tournament_id":tournament_id,"setting_key":"club_selection","setting_value":{"open":opened},"updated_at":now_iso()},on_conflict="tournament_id,setting_key"),"ops_club_state",attempts=2)
        flash("Đã mở chọn CLB." if opened else "Đã khóa chọn CLB.","success"); return redirect_admin("tournaments")

    @app.post('/admin/tournaments/<tournament_id>/clubs/add')
    @login_required
    @admin_required
    @admin_permission_required("system_features_manage")
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

    @app.post('/admin/tournaments/<tournament_id>/league/generate')
    @login_required
    @admin_required
    @admin_permission_required("system_features_manage")
    def admin_tournament_league_generate(tournament_id):
        k=max(1,min(4,int(request.form.get("matches_per_pot") or 2)))
        members=_all_members(tournament_id); pots={}
        for m in members: pots.setdefault(int(m.get("pot_no") or 0),[]).append(str(m["user_id"]))
        pots={p:ids for p,ids in pots.items() if p>0}
        if len(pots)<2:
            flash("Hãy chia Pot trước khi sinh League Phase.","error"); return redirect_admin("tournaments")
        # clear only pending league fixtures; completed history is protected
        existing_completed=_matches(tournament_id,"league",["completed"])
        if existing_completed:
            flash("League Phase đã có kết quả; không thể sinh lại tự động.","error"); return redirect_admin("tournaments")
        execute_query(db.table("tournament_matches").delete().eq("tournament_id",tournament_id).eq("stage_code","league"),"ops_league_clear",attempts=2)
        pairs=[]; plist=sorted(pots)
        try:
            for i,p in enumerate(plist):
                pairs += _cyclic_pairs(pots[p],pots[p],k,True)
                for q in plist[i+1:]: pairs += _cyclic_pairs(pots[p],pots[q],k,False)
        except ValueError as exc:
            flash(str(exc),"error"); return redirect_admin("tournaments")
        unique=[]; seen=set()
        for a,b in pairs:
            key=tuple(sorted((a,b)))
            if key not in seen: seen.add(key); unique.append((a,b))
        for idx,(a,b) in enumerate(unique,1):
            execute_query(db.table("tournament_matches").insert({"tournament_id":tournament_id,"stage_code":"league","round_code":f"LP-{idx}","home_user_id":a,"away_user_id":b,"status":"pending","leg_no":1,"created_at":now_iso(),"updated_at":now_iso()}),"ops_league_insert",attempts=2)
        flash(f"Đã sinh {len(unique)} trận League Phase.","success"); return redirect_admin("tournaments")

    @app.post('/tournaments/matches/<match_id>/schedule')
    @login_required
    def tournament_match_schedule(match_id):
        uid=(current_user() or {}).get("id")
        match,_=_one(db.table("tournament_matches").select("*").eq("id",match_id),"ops_schedule_match")
        if not match or str(uid) not in {str(match.get("home_user_id")),str(match.get("away_user_id"))}:
            flash("Bạn không thuộc trận này.","error"); return redirect(url_for("tournaments"))
        proposed=(request.form.get("scheduled_at") or "").strip(); host_id=(request.form.get("host_id") or "").strip() or None
        if not proposed:
            flash("Hãy chọn thời gian.","error"); return redirect(url_for("tournament_detail",tournament_id=match.get("tournament_id")))
        execute_query(db.table("tournament_schedule_requests").insert({"tournament_id":match.get("tournament_id"),"match_id":match_id,"proposed_by":uid,"proposed_at":proposed,"host_id":host_id,"status":"pending","created_at":now_iso()}),"ops_schedule_propose",attempts=2)
        flash("Đã gửi đề xuất lịch thi đấu.","success"); return redirect(url_for("tournament_detail",tournament_id=match.get("tournament_id")))

    @app.post('/tournaments/schedules/<schedule_id>/accept')
    @login_required
    def tournament_schedule_accept(schedule_id):
        uid=(current_user() or {}).get("id")
        sched,_=_one(db.table("tournament_schedule_requests").select("*").eq("id",schedule_id),"ops_sched_lookup")
        if not sched: flash("Không tìm thấy lịch.","error"); return redirect(url_for("tournaments"))
        match,_=_one(db.table("tournament_matches").select("*").eq("id",sched.get("match_id")),"ops_sched_match")
        if not match or str(uid) not in {str(match.get("home_user_id")),str(match.get("away_user_id"))} or str(uid)==str(sched.get("proposed_by")):
            flash("Bạn không thể xác nhận lịch này.","error"); return redirect(url_for("tournament_detail",tournament_id=sched.get("tournament_id")))
        execute_query(db.table("tournament_schedule_requests").update({"status":"accepted","responded_by":uid,"responded_at":now_iso()}).eq("id",schedule_id),"ops_sched_accept",attempts=2)
        execute_query(db.table("tournament_matches").update({"scheduled_at":sched.get("proposed_at"),"host_id":sched.get("host_id"),"status":"scheduled","updated_at":now_iso()}).eq("id",sched.get("match_id")),"ops_match_schedule",attempts=2)
        flash("Đã chốt lịch thi đấu.","success"); return redirect(url_for("tournament_detail",tournament_id=sched.get("tournament_id")))

    @app.post('/admin/tournaments/<tournament_id>/hosts/add')
    @login_required
    @admin_required
    @admin_permission_required("system_features_manage")
    def admin_tournament_host_add(tournament_id):
        name=(request.form.get("name") or "").strip(); region=(request.form.get("region") or "Bắc").strip()
        if name:
            execute_query(db.table("tournament_hosts").insert({"tournament_id":tournament_id,"name":name,"region":region,"status":"available","note":request.form.get("note") or None,"created_at":now_iso()}),"ops_host_add",attempts=2)
        flash("Đã thêm host.","success"); return redirect_admin("tournaments")

    @app.post('/admin/tournaments/hosts/<host_id>/status')
    @login_required
    @admin_required
    @admin_permission_required("system_features_manage")
    def admin_tournament_host_status(host_id):
        status=request.form.get("status") or "available"
        if status not in {"available","busy","offline"}: status="offline"
        execute_query(db.table("tournament_hosts").update({"status":status,"updated_at":now_iso()}).eq("id",host_id),"ops_host_status",attempts=2)
        flash("Đã cập nhật Host.","success"); return redirect_admin("tournaments")

    @app.post('/admin/tournaments/<tournament_id>/knockout/match')
    @login_required
    @admin_required
    @admin_permission_required("system_features_manage")
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

    @app.post('/admin/tournaments/<tournament_id>/rewards/add')
    @login_required
    @admin_required
    @admin_permission_required("system_features_manage")
    def admin_tournament_reward_add(tournament_id):
        payload={"tournament_id":tournament_id,"name":(request.form.get("name") or "Thưởng sớm").strip(),"stage_code":request.form.get("stage_code") or "stage1","reward_type":request.form.get("reward_type") or "zcoin","reward_value":request.form.get("reward_value") or "0","deadline_at":request.form.get("deadline_at") or None,"enabled":True,"priority":int(request.form.get("priority") or 100),"created_at":now_iso()}
        execute_query(db.table("tournament_reward_rules").insert(payload),"ops_reward_add",attempts=2)
        flash("Đã thêm mức thưởng.","success"); return redirect_admin("tournaments")
