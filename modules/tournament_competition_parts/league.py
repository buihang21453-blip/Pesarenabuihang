"""Internal tournament competition partition extracted from the legacy monolith.

Registered only through :mod:`modules.tournament_competition`.
"""

def register_league(context):
    globals().update(context)

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
        """Sinh đúng 4 trận/HLV: 3 lượt ưu tiên phủ đủ 3 Pot + 1 lượt random bất kỳ.

        Mỗi lượt là một perfect matching toàn bộ HLV, nên mọi HLV có đúng 1 trận/lượt.
        Ba lượt đầu tối đa hóa số Pot khác nhau đã gặp; lượt 4 chỉ yêu cầu không lặp đối thủ.
        """
        players=[str(m.get("user_id")) for m in members if m.get("user_id")]
        if len(players)<4 or len(players)%2:
            raise ValueError("GĐ2 cần số HLV chẵn và tối thiểu 4 để sinh 4 trận cân bằng.")
        pot_by={str(m.get("user_id")):int(m.get("pot_no") or 0) for m in members if m.get("user_id")}
        if len({p for p in pot_by.values() if p>0})<3:
            raise ValueError("GĐ2 cần chia đủ 3 Pot trước khi sinh lịch.")

        used=set()
        covered={uid:set() for uid in players}
        rounds=[]

        def pair_key(a,b): return tuple(sorted((a,b)))

        def make_matching(coverage_mode):
            best=None; best_score=-10**9
            # Random nhiều lần để tìm matching có độ phủ Pot tốt nhưng vẫn không lặp cặp.
            for _ in range(5000):
                arr=players[:]
                random.shuffle(arr)
                pairs=[]; ok=True; score=0
                for i in range(0,len(arr),2):
                    a,b=arr[i],arr[i+1]
                    key=pair_key(a,b)
                    if key in used:
                        ok=False; break
                    pairs.append((a,b))
                    if coverage_mode:
                        pa,pb=pot_by.get(a,0),pot_by.get(b,0)
                        # Ưu tiên đối thủ thuộc Pot HLV chưa gặp; bonus thêm cho cặp khác Pot.
                        score += (6 if pb and pb not in covered[a] else 0)
                        score += (6 if pa and pa not in covered[b] else 0)
                        score += (2 if pa and pb and pa!=pb else 0)
                if ok:
                    # Hạn chế để một HLV lặp quá nhiều cùng Pot trong 3 lượt đầu.
                    if coverage_mode:
                        for a,b in pairs:
                            score -= len(covered[a] & {pot_by.get(b,0)})
                            score -= len(covered[b] & {pot_by.get(a,0)})
                    if score>best_score:
                        best_score=score; best=pairs
            if best is None:
                # Fallback backtracking để luôn tìm perfect matching không lặp nếu còn tồn tại.
                remaining=set(players)
                out=[]
                def dfs():
                    if not remaining: return True
                    a=min(remaining)
                    remaining.remove(a)
                    cand=[b for b in remaining if pair_key(a,b) not in used]
                    random.shuffle(cand)
                    if coverage_mode:
                        cand.sort(key=lambda b:(pot_by.get(b,0) in covered[a], pot_by.get(a,0)==pot_by.get(b,0)))
                    for b in cand:
                        remaining.remove(b); out.append((a,b))
                        if dfs(): return True
                        out.pop(); remaining.add(b)
                    remaining.add(a)
                    return False
                if not dfs():
                    raise ValueError("Không thể sinh đủ 4 trận/HLV mà không lặp đối thủ. Hãy kiểm tra danh sách HLV/Pot.")
                best=out
            return best

        for round_no in range(1,5):
            pairs=make_matching(round_no<=3)
            rounds.append(pairs)
            for a,b in pairs:
                used.add(pair_key(a,b))
                covered[a].add(pot_by.get(b,0)); covered[b].add(pot_by.get(a,0))
        return rounds

    @app.post('/admin/tournaments/<tournament_id>/league/start')
    @login_required
    @admin_required
    def admin_tournament_league_start(tournament_id):
        stages,_=_rows(db.table("tournament_stages").select("stage_code,status").eq("tournament_id",tournament_id),"ops_league_start_stages")
        stage={str(row.get("stage_code")):row.get("status") for row in stages}
        if stage.get("stage1")!="completed" or stage.get("league")!="pending":
            flash("GĐ1 phải kết thúc và GĐ2 phải ở trạng thái chuẩn bị.","error"); return redirect_admin("tournaments")
        members=_all_members(tournament_id)
        if any(C1_CLUB_POT_BY_NAME.get(m.get("fixed_club_name")) != 4-int(m.get("pot_no") or 0) for m in members):
            flash("CLB chưa đúng quy tắc Tier 1→Pot 3, Tier 2→Pot 2, Tier 3→Pot 1. Admin hãy Random lại.","error")
            return redirect_admin("tournaments")
        if len(members)!=16 or sorted(int(m.get("pot_no") or 0) for m in members).count(1)!=5 or sorted(int(m.get("pot_no") or 0) for m in members).count(2)!=6 or sorted(int(m.get("pot_no") or 0) for m in members).count(3)!=5:
            flash("Cần đủ 16 HLV và Pot 5–6–5.","error"); return redirect_admin("tournaments")
        if not (_setting(tournament_id,"pots_locked",{}) or {}).get("locked") or (_setting(tournament_id,"club_selection",{}) or {}).get("open") or any(not m.get("fixed_club_name") for m in members):
            flash("Hãy khóa Pot và chốt CLB đủ 16 HLV trước khi mở GĐ2.","error"); return redirect_admin("tournaments")
        draft=_setting(tournament_id,"club_draft_v2",{}) or {}
        if draft.get("active") or (draft and not draft.get("completed")):
            flash("Random CLB chưa kết thúc.","error"); return redirect_admin("tournaments")
        matches=_matches(tournament_id,"league")
        counts={str(m.get("user_id")):0 for m in members}; pairs=set()
        for match in matches:
            a,b=str(match.get("home_user_id")),str(match.get("away_user_id")); pair=tuple(sorted((a,b)))
            if a==b or a not in counts or b not in counts or pair in pairs:
                flash("Lịch GĐ2 có cặp sai hoặc trùng; không mở giải.","error"); return redirect_admin("tournaments")
            pairs.add(pair); counts[a]+=1; counts[b]+=1
        if len(matches)!=32 or any(n!=4 for n in counts.values()):
            flash("Phải có đủ 32 trận, đúng 4 trận/HLV trước khi mở GĐ2.","error"); return redirect_admin("tournaments")
        cfg=_setting(tournament_id,"competition_timing",{}) or {}
        vn=timezone(timedelta(hours=7)); now=datetime.now(vn)
        start=_parse_iso(cfg.get("league_start_at"))
        if not start:
            if request.form.get("start_now")=="1":
                start=now
                cfg["league_start_at"]=start.isoformat()
            else:
                flash("Admin cần lưu mốc bắt đầu GĐ2 trước.","error"); return redirect_admin("tournaments")
        if start.tzinfo is None: start=start.replace(tzinfo=vn)
        start_now=request.form.get("start_now")=="1"
        if now<start and not start_now:
            flash("Chưa đến mốc bắt đầu GĐ2. Admin có thể chọn Bắt đầu ngay để ghi đè lịch.","warning"); return redirect_admin("tournaments")
        if start_now:
            start=now
            cfg["league_start_at"]=start.isoformat()
        end=start+timedelta(days=7)
        cfg["league_end_at"]=end.isoformat()
        execute_query(db.table("tournament_settings").upsert({"tournament_id":tournament_id,"setting_key":"competition_timing","setting_value":cfg,"updated_at":now_iso()},on_conflict="tournament_id,setting_key"),"ops_league_start_timing",attempts=2)
        execute_query(db.table("tournament_stages").update({"status":"open","updated_at":now_iso()}).eq("tournament_id",tournament_id).eq("stage_code","league").eq("status","pending"),"ops_league_start_manual",attempts=2)
        flash("Đã mở GĐ2 sau khi kiểm tra 16 HLV, CLB, Pot và đủ 32 trận. Thời hạn thi đấu: 7 ngày.","success")
        return redirect_admin("tournaments")

    @app.post('/admin/tournaments/<tournament_id>/league/generate')
    @login_required
    @admin_required
    def admin_tournament_league_generate(tournament_id):
        members=_all_members(tournament_id)
        stage1=_matches(tournament_id,"stage1")
        if not stage1 or any(m.get("status")!="completed" for m in stage1):
            flash("Chỉ sinh lịch GĐ2 sau khi toàn bộ kết quả GĐ1 đã hoàn tất.","error")
            return redirect_admin("tournaments")
        stage_rows,_=_rows(db.table("tournament_stages").select("stage_code,status").eq("tournament_id",tournament_id),"ops_league_stage_gate")
        if not any(x.get("stage_code")=="stage1" and x.get("status")=="completed" for x in stage_rows):
            flash("Admin phải kết thúc GĐ1 trước khi sinh lịch GĐ2.","error")
            return redirect_admin("tournaments")
        if not (_setting(tournament_id,"pots_locked",{}) or {}).get("locked"):
            flash("Hãy khóa Pot trước khi sinh lịch GĐ2.","error")
            return redirect_admin("tournaments")
        if any(C1_CLUB_POT_BY_NAME.get(m.get("fixed_club_name")) != 4-int(m.get("pot_no") or 0) for m in members):
            flash("Có HLV đang dùng CLB sai Tier/Pot. Admin cần Random lại đúng quy tắc trước khi sinh lịch.","error")
            return redirect_admin("tournaments")
        if (_setting(tournament_id,"club_selection",{}) or {}).get("open"):
            flash("Hãy khóa Random/chọn CLB trước khi sinh lịch GĐ2.","error")
            return redirect_admin("tournaments")
        if len(members)!=16 or any(not m.get("fixed_club_name") for m in members):
            flash("Cần đủ 16 HLV đã được gán CLB cố định trước khi sinh lịch.","error")
            return redirect_admin("tournaments")
        if _matches(tournament_id,"league"):
            flash("Lịch GĐ2 đã tồn tại. Không cho sinh lại/xóa lịch tự động để bảo vệ đối thủ đã công bố.","error")
            return redirect_admin("tournaments")
        pots={int(m.get("pot_no") or 0) for m in members if int(m.get("pot_no") or 0)>0}
        if len(pots)!=3:
            flash("GĐ2 chính thức dùng đúng 3 Pot. Hãy chia 3 Pot 5–6–5 trước khi sinh lịch.","error"); return redirect_admin("tournaments")
        pot_counts={p:sum(1 for m in members if int(m.get("pot_no") or 0)==p) for p in (1,2,3)}
        if [pot_counts.get(1,0),pot_counts.get(2,0),pot_counts.get(3,0)] != [5,6,5]:
            flash(f"Sai cấu trúc Pot GĐ2: hiện là {pot_counts.get(1,0)}–{pot_counts.get(2,0)}–{pot_counts.get(3,0)}. Cần chia lại đúng 5–6–5.","error")
            return redirect_admin("tournaments")
        existing_completed=_matches(tournament_id,"league",["completed"])
        if existing_completed:
            flash("League Phase đã có kết quả; không thể sinh lại tự động.","error"); return redirect_admin("tournaments")
        try:
            rounds=_league_four_match_pairs(tournament_id,members)
        except ValueError as exc:
            flash(str(exc),"error"); return redirect_admin("tournaments")

        # Validate complete fixture graph BEFORE the first database write.
        pair_keys=set()
        match_counts={str(m.get("user_id")):0 for m in members}
        if len(rounds)!=4 or any(len(pairs)!=8 for pairs in rounds):
            flash("Thuật toán chưa sinh đủ 4 lượt × 8 trận; chưa ghi dữ liệu.","error")
            return redirect_admin("tournaments")
        for pairs in rounds:
            seen_round=set()
            for a,b in pairs:
                key=tuple(sorted((str(a),str(b))))
                if a==b or key in pair_keys or a in seen_round or b in seen_round or a not in match_counts or b not in match_counts:
                    flash("Lịch GĐ2 có cặp trùng hoặc HLV không hợp lệ; chưa ghi dữ liệu.","error")
                    return redirect_admin("tournaments")
                pair_keys.add(key)
                seen_round.update((a,b))
                match_counts[a]+=1
                match_counts[b]+=1
        if len(pair_keys)!=32 or any(count!=4 for count in match_counts.values()):
            flash("Lịch GĐ2 chưa bảo đảm 32 trận và 4 trận/HLV; chưa ghi dữ liệu.","error")
            return redirect_admin("tournaments")

        execute_query(db.table("tournament_settings").upsert({
            "tournament_id":tournament_id,
            "setting_key":"league_config",
            "setting_value":{
                "pot_count":3,
                "pot_sizes":[5,6,5],
                "pot_format":"5-6-5",
                "matches_per_hlv":4,
                "three_pot_matches":3,
                "wildcard_matches":1,
                "format":"3_POT_PLUS_1_RANDOM",
            },
            "updated_at":now_iso(),
        },on_conflict="tournament_id,setting_key"),"ops_league_config",attempts=2)
        # Never delete league fixtures: a second generation request must not destroy real results.
        if _matches(tournament_id,"league"):
            flash("Đã có lịch GĐ2. Dừng sinh lịch để bảo vệ dữ liệu.","error")
            return redirect_admin("tournaments")

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
        flash(f"Đã sinh {idx} trận GĐ2: mỗi HLV đúng 4 trận · 3 lượt ưu tiên 3 Pot + 1 lượt Random bất kỳ · không lặp đối thủ.","success")
        return redirect_admin("tournaments")

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
        cfg={k:norm(k) for k in ("stage1_start_at","stage1_end_at","stage1_early_end_at","stage1_extension_end_at","league_start_at","league_end_at")}
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
        flash("Đã mở Random CLB thưởng sớm: Top 1 có 2 vé; Top 2–3 có 1 vé. Hạng 4–16 sẽ do hệ thống Random.","success"); return redirect_admin("tournaments")

    def _save_reward_draft(tournament_id,state,label):
        entries=state.get("entries") or {}
        reward_ids=[str(x) for x in (state.get("order") or [])]
        all_ids=[str(x) for x in (state.get("all_order") or [])]
        state["flexible_reward_tickets"]=True
        state["deadline_at"]=None
        state["active"]=any(entries.get(uid,{}).get("status")!="selected" for uid in reward_ids)
        state["completed"]=bool(all_ids) and all(entries.get(uid,{}).get("status")=="selected" for uid in all_ids)
        execute_query(db.table("tournament_settings").upsert({"tournament_id":tournament_id,"setting_key":"club_draft_v2","setting_value":state,"updated_at":now_iso()},on_conflict="tournament_id,setting_key"),label,attempts=2)

    @app.post('/tournaments/<tournament_id>/club-draft/random')
    @login_required
    def tournament_club_draft_random(tournament_id):
        uid=str((current_user() or {}).get("id") or "")
        state=_club_draft_state(tournament_id,False) or {}
        entry=(state.get("entries") or {}).get(uid) or {}
        if not _member(tournament_id,uid) or entry.get("allocation_type")!="EARLY_REWARD" or entry.get("status")=="selected":
            flash("Bạn không có lượt Random CLB chưa chốt.","warning"); return redirect(url_for('tournaments'))
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

    @app.post('/tournaments/<tournament_id>/club-draft/reward-reroll')
    @login_required
    def tournament_club_draft_reward_reroll(tournament_id):
        uid=str((current_user() or {}).get("id") or "")
        member=_member(tournament_id,uid)
        state=_club_draft_state(tournament_id,False) or {}
        entry=(state.get("entries") or {}).get(uid) or {}
        if not member or entry.get("allocation_type")!="EARLY_REWARD" or int(entry.get("tickets_remaining") or 0)<=0:
            flash("Bạn không có vé thưởng sớm để dùng.","warning"); return redirect(url_for('tournaments'))
        if not state.get("tier_club_pot_rule"):
            flash("Admin cần sửa phân bổ 16 CLB đúng Tier/Pot trước khi HLV sử dụng vé đổi CLB.","warning")
            return redirect(url_for('tournaments'))
        old_name=str(member.get("fixed_club_name") or "")
        if not old_name or entry.get("status")!="selected":
            flash("Bạn cần chốt CLB ban đầu trước khi dùng vé đổi CLB.","warning"); return redirect(url_for('tournaments'))
        old,_=_one(db.table("tournament_clubs").select("*").eq("tournament_id",tournament_id).eq("name",old_name).eq("selected_by",uid),"ops_early_reroll_old")
        if not old:
            flash("Không xác minh được CLB hiện tại, chưa trừ vé.","error"); return redirect(url_for('tournaments'))
        skipped=set(str(x) for x in (entry.get("skipped") or []))
        skipped.add(str(old["id"]))
        pool=_available_clubs(tournament_id,skipped)
        if state.get("tier_club_pot_rule"):
            required_pot=4-int(member.get("pot_no") or 0)
            pool=[c for c in pool if C1_CLUB_POT_BY_NAME.get(c.get("name"))==required_pot]
        if not pool:
            flash("Pool không còn CLB phù hợp, vé vẫn được giữ nguyên.","warning"); return redirect(url_for('tournaments'))
        new=random.choice(pool)
        reserved=execute_query(db.table("tournament_clubs").update({"selected_by":uid,"selected_at":now_iso()}).eq("tournament_id",tournament_id).eq("id",new["id"]).is_("selected_by","null"),"ops_early_reroll_reserve",attempts=2)
        if not getattr(reserved,"data",None):
            flash("CLB vừa được người khác chọn; chưa trừ vé. Hãy thử lại.","warning"); return redirect(url_for('tournaments'))
        execute_query(db.table("tournament_members").update({"fixed_club_id":new.get("club_key"),"fixed_club_name":new.get("name")}).eq("tournament_id",tournament_id).eq("user_id",uid),"ops_early_reroll_member",attempts=2)
        entry["tickets_remaining"]=int(entry["tickets_remaining"])-1
        entry["skipped"]=list(skipped); entry["selected_club"]=new.get("name")
        entry["candidate"]={"id":str(new["id"]),"name":new.get("name")}; entry["status"]="selected"
        state["entries"][uid]=entry
        state.setdefault("history",[]).append({"at":now_iso(),"user_id":uid,"action":"REROLL","club":new.get("name"),"message":f"Dùng 1 vé thưởng sớm: {old_name} → {new.get('name')}."})
        _save_reward_draft(tournament_id,state,"ops_early_reroll_save")
        execute_query(db.table("tournament_clubs").update({"selected_by":None,"selected_at":None}).eq("tournament_id",tournament_id).eq("id",old["id"]).eq("selected_by",uid),"ops_early_reroll_release_old",attempts=2)
        flash(f"Đã dùng 1 vé: {old_name} → {new.get('name')}. Còn {entry['tickets_remaining']} vé.","success")
        return redirect(url_for('tournaments'))

    @app.post('/admin/tournaments/<tournament_id>/club-draft/force')
    @login_required
    @admin_required
    def admin_tournament_club_draft_force(tournament_id):
        flash("Vé thưởng sớm không còn thời hạn. HLV tự Random/chốt CLB; Admin không Random thay để tránh mất quyền thưởng.","warning")
        return redirect_admin("tournaments")

    @app.post('/admin/tournaments/<tournament_id>/clubs/rerandom-by-tier')
    @login_required
    @admin_required
    def admin_tournament_rerandom_clubs_by_tier(tournament_id):
        """Correction batch: database RPC commits all 16 allocations or none."""
        if request.form.get("confirm_rule") != "TIER_POT_321":
            flash("Chưa xác nhận quy tắc Tier 1→Pot 3, Tier 2→Pot 2, Tier 3→Pot 1.","warning")
            return redirect_admin("tournaments")
        stages,_=_rows(db.table("tournament_stages").select("stage_code,status").eq("tournament_id",tournament_id),"ops_tier_rerandom_stages")
        status={str(x.get("stage_code")):x.get("status") for x in stages}
        if status.get("stage1")!="completed" or status.get("league") not in {"pending","draft"} or _matches(tournament_id,"league") or _matches(tournament_id,"knockout"):
            flash("Chỉ được sửa Random khi GĐ1 đã hoàn thành, GĐ2 chưa bắt đầu và chưa sinh lịch/trận.","error")
            return redirect_admin("tournaments")
        state=_club_draft_state(tournament_id,False) or {}
        members=_all_members(tournament_id)
        grouped={p:[m for m in members if int(m.get("pot_no") or 0)==p] for p in (1,2,3)}
        if len(members)!=16 or [len(grouped[p]) for p in (1,2,3)]!=[5,6,5] or len(state.get("all_order") or [])!=16:
            flash("Cần đủ 16 HLV chia Tier 5–6–5 và đã mở Random CLB; không thay đổi dữ liệu.","error")
            return redirect_admin("tournaments")
        if (_setting(tournament_id,"club_selection",{}) or {}).get("open"):
            flash("Hãy khóa chế độ chọn CLB thủ công trước khi Random lại.","warning")
            return redirect_admin("tournaments")
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
            flash("Không thể Random lại. Kiểm tra đã chạy SQL_V1.5.90_ADMIN_RERANDOM_TIER_POT.sql và log; giao dịch DB tự rollback nếu lỗi.","error")
            return redirect_admin("tournaments")
        try:
            log_admin_action("Random lại 16 CLB theo Tier/Pot","tournament_club",details={"tournament_id":tournament_id,"rule":"Tier1:Pot3;Tier2:Pot2;Tier3:Pot1"})
        except Exception:
            app.logger.exception("Tier/Pot correction succeeded but auxiliary audit failed: %s",tournament_id)
        flash("Đã Random lại đủ 16 CLB: Tier 1→Pot 3; Tier 2→Pot 2; Tier 3→Pot 1. Vé thưởng sớm và lịch sử được giữ nguyên.","success")
        return redirect_admin("tournaments")

    @app.post('/admin/tournaments/<tournament_id>/clubs/revoke-all')
    @login_required
    @admin_required
    def admin_tournament_revoke_clubs(tournament_id):
        """Revoke every assigned GĐ2 club atomically; tickets and rewards are untouched."""
        if request.form.get('confirm_revoke') != 'REVOKE_ALL_16_CLUBS':
            flash('Chưa xác nhận thu hồi 16 CLB.', 'warning')
            return redirect_admin('tournaments')
        stages, _ = _rows(db.table('tournament_stages').select('stage_code,status').eq('tournament_id', tournament_id), 'ops_revoke_stages')
        status = {str(row.get('stage_code')): row.get('status') for row in stages}
        if status.get('stage1') != 'completed' or status.get('league') not in {'draft', 'pending'} or _matches(tournament_id, 'league') or _matches(tournament_id, 'knockout'):
            flash('Chỉ thu hồi CLB sau khi GĐ1 hoàn tất và trước khi GĐ2 có lịch/trận.', 'error')
            return redirect_admin('tournaments')
        if (_setting(tournament_id, 'club_selection', {}) or {}).get('open'):
            flash('Hãy đóng chọn CLB thủ công trước khi thu hồi.', 'warning')
            return redirect_admin('tournaments')
        try:
            result = execute_query(db.rpc('c1_admin_revoke_tier_clubs', {'p_tournament_id': tournament_id}), 'ops_admin_revoke_clubs_rpc', attempts=1)
            if getattr(result, 'data', None) != 16:
                raise RuntimeError('RPC did not confirm all 16 participants')
        except Exception:
            app.logger.exception('C1 club revocation failed: tournament_id=%s', tournament_id)
            flash('Thu hồi không thành công. Kiểm tra SQL_V1.5.91_ADMIN_REVOKE_CLUBS.sql và log. Giao dịch SQL rollback nếu lỗi.', 'error')
            return redirect_admin('tournaments')
        try:
            log_admin_action('Thu hồi CLB GĐ2 của 16 HLV', 'tournament_club', details={'tournament_id': tournament_id})
        except Exception:
            app.logger.exception('Club revocation succeeded but auxiliary audit failed: %s', tournament_id)
        flash('Đã thu hồi CLB của 16 HLV. Vé thưởng và lịch sử giữ nguyên. Hãy Random lại theo Tier 1→Pot 3, Tier 2→Pot 2, Tier 3→Pot 1.', 'success')
        return redirect_admin('tournaments')

    @app.post('/admin/tournaments/<tournament_id>/clubs/assign-remaining')
    @login_required
    @admin_required
    def admin_tournament_assign_remaining_clubs(tournament_id):
        flash("Nút Random hạng 4–16 cũ đã ngừng sử dụng do phân bổ sai Tier/Pot. Hãy dùng nút Admin Random lại đủ 16 CLB.","warning")
        return redirect_admin("tournaments")

    @app.post('/admin/tournaments/<tournament_id>/league-draw/start')
    @login_required
    @admin_required
    def admin_tournament_league_draw_start(tournament_id):
        members=sorted(_all_members(tournament_id),key=lambda m:(int(m.get("seed_no") or 9999),m.get("display_name") or ""))
        order=[str(m.get("user_id")) for m in members]
        if not _matches(tournament_id,"league"):
            flash("Hãy sinh lịch League Phase trước.","error"); return redirect_admin("tournaments")
        state={"active":True,"completed":False,"order":order,"current_index":0,"pot_index":0,"pots":[1,2,3],"revealed":{},"history":[]}
        execute_query(db.table("tournament_settings").upsert({"tournament_id":tournament_id,"setting_key":"league_draw_v2","setting_value":state,"updated_at":now_iso()},on_conflict="tournament_id,setting_key"),"ops_league_draw_start",attempts=2)
        execute_query(db.table("tournament_settings").upsert({"tournament_id":tournament_id,"setting_key":"league_player_reveals","setting_value":{},"updated_at":now_iso()},on_conflict="tournament_id,setting_key"),"ops_league_player_reveal_reset",attempts=2)
        flash("Đã bắt đầu Lễ bốc thăm League Phase chung.","success"); return redirect_admin("tournaments")

    @app.post('/admin/tournaments/<tournament_id>/league-draw/next')
    @login_required
    @admin_required
    def admin_tournament_league_draw_next(tournament_id):
        state=_setting(tournament_id,"league_draw_v2",{}) or {}; order=state.get("order") or []; pots=state.get("pots") or [1,2,3]
        i=int(state.get("current_index") or 0); pi=int(state.get("pot_index") or 0)
        if not state.get("active") or i>=len(order):
            flash("Lễ bốc thăm đã hoàn tất hoặc chưa bắt đầu.","warning"); return redirect_admin("tournaments")
        uid=str(order[i]); pot=int(pots[pi]); member_map={str(m.get("user_id")):m for m in _all_members(tournament_id)}
        opponents=[]
        for m in _matches(tournament_id,"league"):
            h,a=str(m.get("home_user_id")),str(m.get("away_user_id"))
            if uid not in {h,a}: continue
            opp=a if uid==h else h; om=member_map.get(opp) or {}
            if int(om.get("pot_no") or 0)==pot: opponents.append({"user_id":opp,"name":om.get("display_name") or "HLV","pot":pot})
        state.setdefault("revealed",{}).setdefault(uid,[]).extend([x for x in opponents if x not in state.get("revealed",{}).get(uid,[])])
        state.setdefault("history",[]).append({"at":now_iso(),"user_id":uid,"pot":pot,"action":"DRAW","opponents":[x.get("name") for x in opponents]})
        pi+=1
        if pi>=len(pots):
            # Lượt random thứ tư không có Pot riêng: công bố tất cả đối thủ còn thiếu.
            already={str(x.get("user_id")) for x in state.get("revealed",{}).get(uid,[])}
            for m in _matches(tournament_id,"league"):
                h,a=str(m.get("home_user_id")),str(m.get("away_user_id"))
                if uid not in {h,a}: continue
                opp=a if uid==h else h
                if opp not in already:
                    om=member_map.get(opp) or {}
                    state["revealed"][uid].append({"user_id":opp,"name":om.get("display_name") or "HLV","pot":int(om.get("pot_no") or 0)})
                    already.add(opp)
            pi=0; i+=1
        state["pot_index"]=pi; state["current_index"]=i
        if i>=len(order): state["active"]=False; state["completed"]=True
        execute_query(db.table("tournament_settings").upsert({"tournament_id":tournament_id,"setting_key":"league_draw_v2","setting_value":state,"updated_at":now_iso()},on_conflict="tournament_id,setting_key"),"ops_league_draw_next",attempts=2)
        flash(f"Đã bốc POT {pot} cho HLV hiện tại.","success"); return redirect_admin("tournaments")

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
