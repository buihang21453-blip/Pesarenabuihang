"""Internal tournament competition partition extracted from the legacy monolith.

Registered only through :mod:`modules.tournament_competition`.
"""

def register_test_support(context):
    globals().update(context)

    def _setting(tournament_id,key,default=None):
        row,_=_one(db.table("tournament_settings").select("setting_value").eq("tournament_id",tournament_id).eq("setting_key",key),"ops_setting")
        return (row or {}).get("setting_value",default)

    C1_TEST_ACCOUNTS_KEY = "c1_test_accounts_v1"

    def _c1_test_user_ids(tournament_id):
        state=_setting(tournament_id,C1_TEST_ACCOUNTS_KEY,{}) or {}
        return [str(x) for x in (state.get("user_ids") or []) if str(x).strip()][:2]

    def _is_c1_test_user(tournament_id,user_id):
        return str(user_id or "") in set(_c1_test_user_ids(tournament_id))

    def _c1_test_users(tournament_id):
        ids=_c1_test_user_ids(tournament_id)
        if not ids:
            return []
        rows,_=_rows(db.table("users").select("id,username,display_name,is_online,last_seen_at").in_("id",ids),"ops_c1_test_users")
        order={uid:i for i,uid in enumerate(ids)}
        rows.sort(key=lambda r:order.get(str(r.get("id")),99))
        return rows

    # ============================================================
    # V1.5.21 - ADMIN TEST ACCOUNT SWITCH
    # Admin có thể chuyển sang đúng 2 tài khoản Test C1 trong cùng trình duyệt.
    # Không thay đổi role DB; khi impersonate, effective session là tài khoản Test.
    # ============================================================
    def _admin_switch_root_user():
        root_id=str(session.get("admin_switch_root_user_id") or "")
        if not root_id:
            return None
        try:
            root=get_user(root_id)
        except Exception:
            return None
        return root if is_admin_user(root) else None

    def _admin_switch_set_effective_user(user):
        if not user:
            return
        session["user_id"]=user.get("id")
        session["username"]=user.get("username","")
        session["display_name"]=user.get("display_name","")
        session["avatar_url"]=user.get("avatar_url")
        session["role"]=user.get("role","player")
        session["account_status"]=user.get("account_status","approved")
        session["admin_level"]=user.get("admin_level","none")
        session["zcoin_balance"]=int(user.get("zcoin_balance") or 0)
        session["last_real_activity"]=int(time.time())
        session["last_activity_touch"]=int(time.time())
        cache_delete("_rz_current_user")
        cache_delete("_rz_current_pending_invites")
        ttl_cache_delete("invites_raw")

    def _admin_switch_context_payload():
        active_root=_admin_switch_root_user()
        current=current_user() or {}

        # Đang đóng vai Test: chỉ dùng tournament đã lưu trong session.
        if active_root:
            tid=str(session.get("admin_switch_tournament_id") or "")
            users=_c1_test_users(tid) if tid else []
            return {
                "admin_test_switch_active":True,
                "admin_test_switch_root":active_root,
                "admin_test_switch_users":users,
                "admin_test_switch_tournament_id":tid,
                "admin_test_switch_current":current,
            }

        # Chỉ Admin thật mới được thấy nút Switch.
        if not is_admin_user(current):
            return {
                "admin_test_switch_active":False,
                "admin_test_switch_users":[],
            }

        # Ưu tiên giải đang hiển thị qua view_args, nếu không lấy giải visible đầu tiên
        # có cấu hình tài khoản Test C1.
        candidate_ids=[]
        try:
            if request.view_args and request.view_args.get("tournament_id"):
                candidate_ids.append(str(request.view_args.get("tournament_id")))
        except Exception:
            pass
        try:
            tours,_=_rows(
                db.table("tournaments").select("id").eq("is_visible",True).order("created_at",desc=True),
                "ops_admin_switch_tournaments",
            )
            for tour in tours:
                tid=str(tour.get("id") or "")
                if tid and tid not in candidate_ids:
                    candidate_ids.append(tid)
        except Exception:
            pass

        for tid in candidate_ids:
            users=_c1_test_users(tid)
            if users:
                return {
                    "admin_test_switch_active":False,
                    "admin_test_switch_users":users,
                    "admin_test_switch_tournament_id":tid,
                }

        return {
            "admin_test_switch_active":False,
            "admin_test_switch_users":[],
        }

    @app.context_processor
    def inject_admin_test_switch():
        try:
            return _admin_switch_context_payload()
        except Exception as exc:
            app.logger.warning("Admin test switch context failed: %s",exc)
            return {
                "admin_test_switch_active":False,
                "admin_test_switch_users":[],
            }

    @app.post('/admin/test-switch/<tournament_id>/<test_user_id>')
    @login_required
    def admin_test_switch_account(tournament_id,test_user_id):
        current=current_user() or {}
        root=_admin_switch_root_user()

        # Lần đầu phải là Admin thật. Sau đó có thể Test A -> Test B trực tiếp
        # nhờ root admin đã được giữ trong session.
        if root is None:
            if not is_admin_user(current):
                flash("Chỉ Admin mới được chuyển sang tài khoản thử nghiệm.","error")
                return redirect(url_for("dashboard"))
            root=current
            session["admin_switch_root_user_id"]=str(root.get("id") or "")

        allowed=set(_c1_test_user_ids(tournament_id))
        target_id=str(test_user_id or "")
        if target_id not in allowed:
            flash("Tài khoản này không thuộc danh sách thử nghiệm được phép chuyển.","error")
            return redirect(url_for("admin") if is_admin_user(current) else url_for("tournaments"))

        try:
            target=get_user(target_id)
        except Exception:
            target=None
        if not target or target.get("account_status","approved")!="approved" or is_admin_user(target):
            flash("Tài khoản thử nghiệm không hợp lệ.","error")
            return redirect(url_for("admin") if is_admin_user(current) else url_for("tournaments"))

        session["admin_switch_tournament_id"]=str(tournament_id)
        session["admin_switch_started_at"]=now_iso()
        _admin_switch_set_effective_user(target)

        flash(f"🧪 Đang thao tác dưới tài khoản thử nghiệm: {target.get('display_name') or target.get('username')}. Quyền Admin đã tạm khóa trong chế độ này.","success")
        return redirect(url_for("tournaments"))

    @app.post('/admin/test-switch/return')
    @login_required
    def admin_test_switch_return():
        root=_admin_switch_root_user()
        if not root:
            # Session root không hợp lệ thì không được tự nâng quyền.
            for key in ("admin_switch_root_user_id","admin_switch_tournament_id","admin_switch_started_at"):
                session.pop(key,None)
            flash("Không thể khôi phục phiên Admin. Vui lòng đăng nhập Admin lại.","warning")
            return redirect(url_for("login"))

        _admin_switch_set_effective_user(root)
        for key in ("admin_switch_root_user_id","admin_switch_tournament_id","admin_switch_started_at"):
            session.pop(key,None)
        cache_delete("_rz_current_user")
        flash("👑 Đã quay lại tài khoản Admin.","success")
        return redirect(url_for("admin"))

    def _c1_test_confirmed_matches(tournament_id):
        test_users=_c1_test_users(tournament_id)
        if not test_users:
            return []
        ids={str(x.get("id")) for x in test_users}
        rows,_=_rows(
            db.table("match_rooms").select("id,host_user_id,guest_user_id,host_name,guest_name,host_score,guest_score,status,updated_at,created_at,note").order("updated_at",desc=True).limit(300),
            "ops_c1_test_confirmed_matches",
        )
        matches=[]
        for room in rows:
            meta=_room_meta(room)
            if not meta or str(meta.get("tournament_id") or "")!=str(tournament_id) or not meta.get("test_sandbox_room"):
                continue
            host_uid=str(room.get("host_user_id") or "")
            guest_uid=str(room.get("guest_user_id") or "")
            if host_uid not in ids or guest_uid not in ids:
                continue

            # V1.5.44: SANDBOX copy đúng Rank: sau khi xác nhận, room được reset ngay
            # sang waiting_ready nên kết quả cũ phải nằm trong lịch sử meta riêng.
            # Vẫn đọc test_result confirmed để tương thích dữ liệu V1.5.44 trở về trước.
            results=list(meta.get("test_result_history") or [])
            current_result=meta.get("test_result") or {}
            if str(current_result.get("status") or "")=="confirmed":
                results.append(current_result)

            seen=set()
            for result in results:
                if str(result.get("status") or "confirmed")!="confirmed":
                    continue
                result_key=str(result.get("result_id") or result.get("confirmed_at") or "")
                if result_key and result_key in seen:
                    continue
                if result_key:
                    seen.add(result_key)
                try:
                    hs=int(result.get("host_score") if result.get("host_score") is not None else 0)
                    gs=int(result.get("guest_score") if result.get("guest_score") is not None else 0)
                except Exception:
                    continue
                matches.append({
                    "room_id":str(room.get("id") or ""),
                    "host_user_id":host_uid,
                    "guest_user_id":guest_uid,
                    "host_name":room.get("host_name") or (get_user(host_uid) or {}).get("display_name") or "Test A",
                    "guest_name":room.get("guest_name") or (get_user(guest_uid) or {}).get("display_name") or "Test B",
                    "host_score":hs,
                    "guest_score":gs,
                    "test_round_no":int(result.get("test_round_no") or 1),
                    "confirmed_at":result.get("confirmed_at") or room.get("updated_at") or room.get("created_at"),
                })
        def _parse(value):
            if not value:
                return datetime.min.replace(tzinfo=timezone.utc)
            try:
                return datetime.fromisoformat(str(value).replace("Z","+00:00"))
            except Exception:
                return datetime.min.replace(tzinfo=timezone.utc)
        matches.sort(key=lambda x:_parse(x.get("confirmed_at")), reverse=True)
        return matches

    def _c1_test_ranking(tournament_id):
        users=_c1_test_users(tournament_id)
        if not users:
            return []
        ranking={}
        order={str(u.get("id")):idx for idx,u in enumerate(users,1)}
        for u in users:
            uid=str(u.get("id") or "")
            ranking[uid]={
                "user_id":uid,
                "display_name":u.get("display_name") or u.get("username") or "HLV Test",
                "played":0,
                "wins":0,
                "draws":0,
                "losses":0,
                "gf":0,
                "ga":0,
                "gd":0,
                "points":0,
                "recent_form":[],
                "winrate":0,
            }
        matches=_c1_test_confirmed_matches(tournament_id)
        for m in matches:
            h=m["host_user_id"]; a=m["guest_user_id"]; hs=int(m["host_score"]); gs=int(m["guest_score"])
            H=ranking.get(h); A=ranking.get(a)
            if not H or not A:
                continue
            H["played"] += 1; A["played"] += 1
            H["gf"] += hs; H["ga"] += gs; A["gf"] += gs; A["ga"] += hs
            if hs > gs:
                H["wins"] += 1; H["points"] += 3; A["losses"] += 1
            elif hs < gs:
                A["wins"] += 1; A["points"] += 3; H["losses"] += 1
            else:
                H["draws"] += 1; A["draws"] += 1; H["points"] += 1; A["points"] += 1
        for m in matches:
            pairs=((m["host_user_id"],m["host_score"],m["guest_score"]),(m["guest_user_id"],m["guest_score"],m["host_score"]))
            for uid,mine,theirs in pairs:
                row=ranking.get(uid)
                if not row or len(row["recent_form"])>=5:
                    continue
                if mine > theirs:
                    pill={"code":"win","short":"T","label":"Thắng"}
                elif mine < theirs:
                    pill={"code":"loss","short":"B","label":"Bại"}
                else:
                    pill={"code":"draw","short":"H","label":"Hòa"}
                row["recent_form"].append(pill)
        out=list(ranking.values())
        for row in out:
            row["gd"]=row["gf"]-row["ga"]
            total=row["wins"]+row["draws"]+row["losses"]
            row["winrate"]=round((row["wins"] / total) * 100, 1) if total else 0
        out.sort(key=lambda r:(r["points"],r["gd"],r["gf"],r["wins"],-order.get(r["user_id"],99)), reverse=True)
        for idx,row in enumerate(out,1):
            row["rank"]=idx
        return out

    def _stage1_random_history_key(user_id):
        return f"stage1_random_history:{str(user_id)}"

    def _stage1_random_history(tournament_id,user_id):
        state=_setting(tournament_id,_stage1_random_history_key(user_id),{}) or {}
        entries=list(state.get("entries") or [])
        # Giữ một bản ghi cho mỗi trận/phòng; dữ liệu cũ nếu có trùng CLB vẫn được
        # bảo toàn để lần random sau loại CLB đó khỏi pool của chính HLV.
        return entries

    def _stage1_used_club_names(tournament_id,user_id):
        uid=str(user_id or "")
        used={
            str(x.get("club") or "").strip()
            for x in _stage1_random_history(tournament_id,uid)
            if str(x.get("club") or "").strip()
        }
        # Backfill từ các phòng C1 đã từng random trước khi có cơ chế history.
        # Nhờ vậy deploy bản fix giữa mùa vẫn tránh quay lại những CLB đã ra trước đó
        # nếu phòng cũ còn lưu host_team/guest_team.
        try:
            rooms,_=_rows(
                db.table("match_rooms").select("host_user_id,guest_user_id,host_team,guest_team,note")
                .limit(500),
                "ops_stage1_random_history_backfill",
            )
            for r in rooms:
                meta=_room_meta(r)
                if not meta or str(meta.get("tournament_id") or "")!=str(tournament_id):
                    continue
                if str(meta.get("stage_code") or "") not in {"stage1", ""} and not bool(meta.get("admin_test_room")):
                    continue
                if str(r.get("host_user_id") or "")==uid and str(r.get("host_team") or "").strip():
                    used.add(str(r.get("host_team")).strip())
                if str(r.get("guest_user_id") or "")==uid and str(r.get("guest_team") or "").strip():
                    used.add(str(r.get("guest_team")).strip())
        except Exception as exc:
            app.logger.warning("Không backfill được lịch sử CLB GĐ1: %s", exc)
        return used

    def _save_stage1_random_history(tournament_id,user_id,club_name,room_id=None,match_id=None):
        key=_stage1_random_history_key(user_id)
        state=_setting(tournament_id,key,{}) or {}
        entries=list(state.get("entries") or [])
        token=str(match_id or room_id or "")
        # Không ghi lặp cùng một trận/phòng nếu request bị submit hai lần.
        if token and any(str(x.get("token") or "")==token for x in entries):
            return
        entries.append({
            "token":token,
            "room_id":str(room_id or ""),
            "match_id":str(match_id or ""),
            "club":str(club_name or "").strip(),
            "random_at":now_iso(),
        })
        execute_query(
            db.table("tournament_settings").upsert({
                "tournament_id":tournament_id,
                "setting_key":key,
                "setting_value":{"entries":entries,"updated_at":now_iso()},
                "updated_at":now_iso(),
            },on_conflict="tournament_id,setting_key"),
            "ops_stage1_random_history_save",attempts=2,
        )

    def _stage1_club_pool(tournament_id):
        state=_setting(tournament_id,"stage1_club_pool",{}) or {}
        eligible=_stage1_eligible_clubs()
        saved_clubs=list(state.get("clubs") or [])
        clubs=(saved_clubs or _default_stage1_clubs())[:16]
        clean=[]
        for c in clubs:
            if isinstance(c,str):
                info=next((x for x in TEAMS if x.get("display")==c),None) or {"display":c,"overall":0}
            else:
                info=c or {}
            name=(info.get("display") or info.get("name") or "").strip()
            canonical=next((x for x in eligible if x.get("display")==name),None)
            # Không làm mất Pool 16 CLB đã được Admin lưu chỉ vì nguồn teams
            # hiện tại đổi cách viết tên/metadata. Saved pool là nguồn sự thật của C1.
            if canonical:
                final_overall=int(canonical.get("overall") or info.get("overall") or 0)
                final_tier=str(canonical.get("tier") or info.get("tier") or "").strip().upper()
            else:
                final_overall=int(info.get("overall") or 0)
                final_tier=str(info.get("tier") or "").strip().upper()
            # Nếu đây là pool Admin đã lưu thì không loại CLB chỉ vì metadata nguồn teams
            # bị đổi/thiếu ở lần đọc sau. Pool đã lưu là cấu hình chính thức của giải.
            saved_pool_entry = bool(saved_clubs)
            if name and (saved_pool_entry or final_tier in STAGE1_ALLOWED_TIERS) and not any(x["name"]==name for x in clean):
                clean.append({
                    "name":name,
                    "overall":final_overall,
                    "tier":final_tier,
                })
        return clean

    return {k: v for k, v in locals().items() if k.startswith('_') and callable(v)}
