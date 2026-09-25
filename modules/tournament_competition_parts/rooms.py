"""Internal tournament competition partition extracted from the legacy monolith.

Registered only through :mod:`modules.tournament_competition`.
"""

def register_rooms(context):
    globals().update(context)

    def _room_meta(room):
        note=str((room or {}).get("note") or "")
        if not note.startswith(TOURNAMENT_ROOM_PREFIX): return None
        try: return json.loads(note[len(TOURNAMENT_ROOM_PREFIX):])
        except Exception: return None

    def _room_note(meta):
        return TOURNAMENT_ROOM_PREFIX + json.dumps(meta,ensure_ascii=False,separators=(",",":"))

    def _tournament_rooms(tournament_id):
        # Chỉ hiển thị các phòng C1 đang thực sự hoạt động. Phòng đã hoàn tất/đóng
        # không được chất đống ở Trung tâm. Nếu một trận từng sinh nhiều phòng, chỉ
        # lấy phòng mới nhất của tournament_match_id đó.
        rows,_=_rows(db.table("match_rooms").select("*").order("updated_at",desc=True).limit(160),"ops_tournament_rooms")
        matches={str(m.get("id")):m for m in _decorate_matches(tournament_id,_matches(tournament_id))}
        active_statuses={"waiting_ready","playing","friendly_playing","waiting_result_confirm","disputed"}
        out=[]; seen_match_ids=set()
        for r in rows:
            if str(r.get("status") or "") not in active_statuses:
                continue
            meta=_room_meta(r)
            if not meta or str(meta.get("tournament_id"))!=str(tournament_id): continue
            mid=str(meta.get("tournament_match_id") or "")
            if not mid or mid in seen_match_ids:
                continue
            m=matches.get(mid) or {}
            if not m:
                continue
            # Trận đã completed/cancelled thì phòng không còn là phòng đang hoạt động.
            if str(m.get("status") or "") in {"completed","cancelled"}:
                continue
            seen_match_ids.add(mid)
            host=get_user(r.get("host_user_id")) if r.get("host_user_id") else None
            guest=get_user(r.get("guest_user_id")) if r.get("guest_user_id") else None
            expected_home=m.get("home_name") or meta.get("home_name") or "HLV 1"
            expected_away=m.get("away_name") or meta.get("away_name") or "HLV 2"
            r["tournament_meta"]=meta; r["tournament_match"]=m
            r["host_name"]=(host or {}).get("display_name") or (host or {}).get("username") or expected_home
            r["guest_name"]=(guest or {}).get("display_name") or (guest or {}).get("username") or None
            r["expected_home_name"]=expected_home; r["expected_away_name"]=expected_away
            if r.get("guest_user_id"):
                r["public_label"]=f'{r["host_name"]} vs {r["guest_name"] or expected_away}'
                if r.get("status") in {"playing","friendly_playing"}:
                    r["public_status"]="Đang thi đấu"
                elif r.get("status")=="waiting_result_confirm":
                    r["public_status"]="Chờ xác nhận kết quả"
                elif r.get("status")=="disputed":
                    r["public_status"]="Đang xử lý kết quả"
                else:
                    r["public_status"]="Đủ 2 HLV"
            else:
                expected = expected_away if str(r.get("host_user_id"))==str(m.get("home_user_id")) else expected_home
                r["public_label"]=f'{r["host_name"]} · chờ {expected}'
                r["public_status"]="Chờ đối thủ"
            out.append(r)
        return out

    def _c1_accessible_tournament(user, requested_id=None):
        uid=str((user or {}).get("id") or "")
        admin=is_admin_user(user or {})
        tours,_=_rows(db.table("tournaments").select("*").eq("is_visible",True).order("created_at",desc=True),"c1_accessible_tournaments")

        # Khi route truyền tournament_id thì luôn dùng đúng giải đó.
        if requested_id:
            for t in tours:
                if str(t.get("id")) != str(requested_id):
                    continue
                members=_all_members(t.get("id"))
                if admin or _is_c1_test_user(t.get("id"),uid) or any(str(m.get("user_id"))==uid for m in members):
                    return t,members
            return None,[]

        # HLV thường: ưu tiên giải mà chính HLV đang là thành viên active.
        if not admin:
            for t in tours:
                members=_all_members(t.get("id"))
                if any(str(m.get("user_id"))==uid for m in members):
                    return t,members
            for t in tours:
                if _is_c1_test_user(t.get("id"),uid):
                    return t,_all_members(t.get("id"))
            return None,[]

        # Admin bấm Phòng đấu C1 từ sidebar không có tournament_id.
        # Ưu tiên giải đã cấu hình đúng Pool 16 CLB S/S+ để tránh mở nhầm
        # tournament/test khác và hiển thị sai "Pool GĐ1: 0 CLB".
        fallback=None
        for t in tours:
            members=_all_members(t.get("id"))
            if fallback is None:
                fallback=(t,members)
            # Chỉ coi là "đã cấu hình Pool 16" khi Admin thực sự đã lưu
            # stage1_club_pool cho đúng tournament này. Không dùng fallback mặc định
            # vì fallback làm mọi giải đều trông như có 16 đội và Admin dễ mở nhầm giải.
            try:
                saved=_setting(t.get("id"),"stage1_club_pool",{}) or {}
                saved_pool=list(saved.get("clubs") or [])
            except Exception:
                saved_pool=[]
            if len(saved_pool)==16:
                return t,members
        return fallback if fallback else (None,[])

    def _c1_pair_match(tournament_id, user_a, user_b):
        pair={str(user_a or ""),str(user_b or "")}
        if "" in pair or len(pair)!=2:
            return None
        priority={"playing":0,"scheduled":1,"pending":2,"disputed":3}
        candidates=[]
        for m in _matches(tournament_id):
            if {str(m.get("home_user_id") or ""),str(m.get("away_user_id") or "")} != pair:
                continue
            status=str(m.get("status") or "pending")
            if status in {"completed","cancelled"}:
                continue
            candidates.append((priority.get(status,9),m))
        candidates.sort(key=lambda x:x[0])
        return candidates[0][1] if candidates else None

    def _c1_open_room_for_user(tournament_id, user_id):
        for r in _tournament_rooms(tournament_id):
            if str(user_id) in {str(r.get("host_user_id") or ""),str(r.get("guest_user_id") or "")} and r.get("status") not in {"completed","cancelled","confirmed"}:
                return r
        return None

    def _c1_pending_invite_room(tournament_id, user_id):
        uid=str(user_id or "")
        for r in _tournament_rooms(tournament_id):
            if r.get("status") in {"completed","cancelled","confirmed"} or r.get("guest_user_id"):
                continue
            meta=r.get("tournament_meta") or _room_meta(r) or {}
            if str(meta.get("invited_user_id") or "")==uid:
                return r
        return None

    @app.get('/c1-rooms')
    @login_required
    def c1_rooms():
        user=current_user() or {}; uid=str(user.get("id") or "")
        selected,members=_c1_accessible_tournament(user,request.args.get("tournament_id"))
        if not selected:
            flash("Phòng đấu C1 chỉ dành cho HLV đang nằm trong danh sách giải và Admin.","warning")
            return redirect(url_for("tournaments"))
        tid=selected.get("id")
        pending=_c1_pending_invite_room(tid,uid)
        if pending:
            return redirect(url_for("c1_room_accept",tournament_id=tid,room_id=pending.get("id")))
        active=_c1_open_room_for_user(tid,uid)
        if active:
            return redirect(url_for("room_detail",room_id=active.get("id")))
        # Trang dự phòng khi người dùng mở URL trực tiếp. Nút sidebar dùng POST và vào phòng ngay.
        member=next((m for m in members if str(m.get("user_id"))==uid),None)
        # V1.5.5: participant fallback page must not leak the full C1 roster.
        visible_members=members if is_admin_user(user) else ([member] if member else [])
        return render_template("c1_rooms.html",tournament=selected,member=member,members=visible_members,is_c1_admin=is_admin_user(user))

    @app.post('/c1-rooms/open')
    @login_required
    def c1_room_open():
        user=current_user() or {}; uid=str(user.get("id") or "")
        selected,members=_c1_accessible_tournament(user,request.form.get("tournament_id"))
        if not selected:
            flash("Bạn không có quyền vào Phòng đấu C1.","error")
            return redirect(url_for("tournaments"))
        tid=str(selected.get("id"))
        is_test_account=_is_c1_test_user(tid,uid)
        pending=_c1_pending_invite_room(tid,uid)
        if pending:
            return redirect(url_for("c1_room_accept",tournament_id=tid,room_id=pending.get("id")))
        existing=_c1_open_room_for_user(tid,uid)
        if existing:
            existing_meta=existing.get("tournament_meta") or _room_meta(existing) or {}
            linked_id=str(existing_meta.get("tournament_match_id") or "")
            if str(existing_meta.get("stage_code") or "")=="knockout" and linked_id:
                linked_match,_=_one(db.table("tournament_matches").select("*").eq("id",linked_id).eq("tournament_id",tid),"ops_c1_open_existing_ko_gate")
                if linked_match and not _knockout_pair_is_unlocked(tid,linked_match):
                    flash("🔒 BTC đã khóa cặp Knockout này. Chưa thể vào Phòng đấu C1.","warning")
                    return redirect(url_for("tournaments")+"#knockout-"+tid)
            return redirect(url_for("room_detail",room_id=existing.get("id")))
        me=next((m for m in members if str(m.get("user_id"))==uid),None)
        active=active_room_for_user(uid)
        if active:
            # Không được tái sử dụng/phóng người dùng từ Phòng thường sang Phòng C1.
            # Chỉ xử lý lại nếu active thực sự là phòng Tournament.
            active_meta=_room_meta(active)
            active_is_c1 = bool(active_meta) or str(active.get("match_mode") or "").lower()=="tournament"
            if active_is_c1:
                # Admin có thể đang mắc trong một phòng C1 rỗng được gắn nhầm giải.
                if (is_admin_user(user) and active_meta and not active.get("guest_user_id")
                        and str(active.get("host_user_id") or "")==uid
                        and str(active_meta.get("tournament_id") or "")!=tid):
                    active_meta.update({
                        "tournament_id":tid,"tournament_match_id":"","stage_code":"",
                        "invited_user_id":"","away_user_id":"","away_name":"",
                        "c1_open_room":True,"admin_test_room":bool(not me),
                    })
                    execute_query(db.table("match_rooms").update({
                        "note":_room_note(active_meta),"match_mode":"tournament",
                        "team_tier":"TOURNAMENT","updated_at":now_iso(),
                    }).eq("id",active.get("id")),"ops_c1_rebind_empty_admin_room",attempts=2)
                    flash("Đã đồng bộ lại Phòng C1 với đúng giải hiện tại.","success")
                    return redirect(url_for("room_detail",room_id=active.get("id")))
                return redirect(url_for("room_detail",room_id=active.get("id")))

            # Nếu đang có phòng thường trống do chính mình tạo, đóng phòng đó trước
            # rồi tạo Phòng C1 mới. Nếu phòng thường đã có đối thủ/đang đá thì chặn,
            # tuyệt đối không redirect nhầm sang loại phòng kia.
            can_close_empty_normal = (
                str(active.get("host_user_id") or "")==uid
                and not active.get("guest_user_id")
                and str(active.get("status") or "")=="waiting_ready"
            )
            if can_close_empty_normal:
                execute_query(db.table("match_rooms").update({
                    "status":"cancelled","updated_at":now_iso(),
                }).eq("id",active.get("id")),"ops_switch_normal_to_c1_room",attempts=2)
            else:
                flash("Bạn đang có Phòng đấu thường đang hoạt động. Hãy kết thúc hoặc thoát phòng thường trước khi vào Phòng đấu C1.","warning")
                return redirect(url_for("c1_rooms",tournament_id=tid))
        name=(me or {}).get("display_name") or user.get("display_name") or user.get("username") or ("Admin" if is_admin_user(user) else "HLV")
        meta={
            "tournament_id":tid,"tournament_match_id":"","stage_code":"",
            "home_user_id":uid,"away_user_id":"","home_name":name,"away_name":"",
            "invited_user_id":"","c1_open_room":True,
            "admin_test_room":bool((is_admin_user(user) and not me) or is_test_account),
            "test_sandbox_room":bool(is_test_account),
        }
        # V1.5.87: Free C1 room uses the same fixed club as match-linked rooms.
        # Stage1 deliberately retains its per-match random-club rules.
        league_open=str((_stage(tid,"league") or {}).get("status") or "")=="open"
        knockout_open=str((_stage(tid,"knockout") or {}).get("status") or "")=="open"
        if knockout_open and me and not is_test_account:
            ko_candidates=[m for m in _matches(tid,"knockout")
                           if uid in {str(m.get("home_user_id") or ""),str(m.get("away_user_id") or "")}
                           and str(m.get("status") or "pending") not in {"completed","cancelled"}]
            ko_candidates.sort(key=lambda m:(int(m.get("leg_no") or 1),str(m.get("created_at") or "")))
            if ko_candidates and not _knockout_pair_is_unlocked(tid,ko_candidates[0]):
                flash("🔒 BTC chưa mở cặp Knockout của bạn. Vui lòng chờ Admin mở trận.","warning")
                return redirect(url_for("tournaments")+"#knockout-"+tid)
        fixed_host=(_member(tid,uid) or {}).get("fixed_club_name") if (league_open or knockout_open) else None
        if (league_open or knockout_open) and me and not fixed_host:
            flash("HLV chưa có CLB cố định; không thể tạo phòng C1 GĐ2/KO.","error")
            return redirect(url_for("tournaments"))
        row=execute_query(db.table("match_rooms").insert({
            "host_team":fixed_host,
            "invite_id":None,"host_user_id":uid,"guest_user_id":None,"team_tier":"TOURNAMENT",
            "match_mode":"tournament","friendly_tier":None,"status":"waiting_ready","guest_ready":False,
            "note":_room_note(meta),"state_expires_at":None,"updated_at":now_iso(),
        }),"ops_c1_open_room_create",attempts=2)
        room=(row.data or [{}])[0]
        flash("Đã vào Phòng đấu C1. Hãy chọn một HLV C1 để mời thi đấu.","success")
        return redirect(url_for("room_detail",room_id=room.get("id")))

    @app.post('/tournaments/<tournament_id>/rooms/<room_id>/invite')
    @login_required
    def c1_room_invite(tournament_id,room_id):
        user=current_user() or {}; uid=str(user.get("id") or "")
        room=get_room(room_id); meta=_room_meta(room)
        if not room or not meta or str(meta.get("tournament_id"))!=str(tournament_id):
            flash("Không tìm thấy Phòng đấu C1.","error"); return redirect(url_for("c1_rooms"))
        if uid!=str(room.get("host_user_id")) and not is_admin_user(user):
            flash("Chỉ chủ phòng được mời đối thủ.","error"); return redirect(url_for("room_detail",room_id=room_id))
        if room.get("guest_user_id"):
            flash("Phòng đã có đủ 2 HLV.","warning"); return redirect(url_for("room_detail",room_id=room_id))
        opponent_uid=str(request.form.get("opponent_user_id") or "").strip()
        members=_all_members(tournament_id)
        host_uid=str(room.get("host_user_id") or "")
        test_room=bool(meta.get("test_sandbox_room")) or _is_c1_test_user(tournament_id,host_uid)
        if test_room:
            test_users=_c1_test_users(tournament_id)
            opponent=next((m for m in test_users if str(m.get("id"))==opponent_uid),None)
            host_member=next((m for m in test_users if str(m.get("id"))==host_uid),None)
            if not opponent or opponent_uid==host_uid:
                flash("Phòng kiểm thử chỉ được mời tài khoản thử nghiệm còn lại.","error"); return redirect(url_for("room_detail",room_id=room_id))
            match=None
        else:
            opponent=next((m for m in members if str(m.get("user_id"))==opponent_uid),None)
            if not opponent or opponent_uid==host_uid:
                flash("Chỉ được mời HLV đang tham gia C1.","error"); return redirect(url_for("room_detail",room_id=room_id))
            match=_c1_pair_match(tournament_id,host_uid,opponent_uid)
            host_member=next((m for m in members if str(m.get("user_id"))==host_uid),None)
            if match and str(match.get("stage_code") or "")=="knockout" and not _knockout_pair_is_unlocked(tournament_id,match):
                flash("🔒 Cặp Knockout này chưa được BTC mở. Chưa thể gửi lời mời thi đấu.","warning")
                return redirect(url_for("room_detail",room_id=room_id))
            if not match and not is_admin_user(user):
                flash("HLV này không có trận C1 đang chờ thi đấu với bạn.","warning"); return redirect(url_for("room_detail",room_id=room_id))
        if match:
            dm=_decorate_matches(tournament_id,[match])[0]
            meta.update({
                "tournament_match_id":str(match.get("id")),"stage_code":match.get("stage_code") or "",
                "home_user_id":str(match.get("home_user_id") or ""),"away_user_id":str(match.get("away_user_id") or ""),
                "home_name":dm.get("home_name") or "HLV 1","away_name":dm.get("away_name") or "HLV 2",
                "admin_test_room":False,
            })
        else:
            meta.update({
                "tournament_match_id":"","stage_code":"","home_user_id":host_uid,"away_user_id":opponent_uid,
                "home_name":(host_member or {}).get("display_name") or user.get("display_name") or "HLV Test",
                "away_name":opponent.get("display_name") or opponent.get("username") or "HLV Test","admin_test_room":True,
                "test_sandbox_room":bool(test_room),
            })
            if test_room:
                # V1.5.44: SANDBOX có số thứ tự trận riêng, không đụng tournament_matches.
                meta.setdefault("test_round_no",1)
                meta.setdefault("test_result_history",[])
                meta["test_result"]={}
        meta["invited_user_id"]=opponent_uid
        # V1.5.12: C1 phải tạo match_invites để popup realtime toàn app nhìn thấy.
        # Trước đây chỉ tạo user_notification nên khách không nhận popup và chưa vào
        # guest_user_id, kéo theo nút Sẵn sàng không xuất hiện.
        old_invite_id=room.get("invite_id")
        if old_invite_id:
            try:
                execute_query(db.table("match_invites").update({"status":"cancelled","updated_at":now_iso()}).eq("id",old_invite_id).eq("status","pending"),"ops_c1_cancel_old_realtime_invite",attempts=1)
            except Exception:
                pass
        expires_at=(datetime.now(timezone.utc)+timedelta(seconds=60)).isoformat()
        invite_result=execute_query(db.table("match_invites").insert({
            "from_user_id":host_uid,
            "to_user_id":opponent_uid,
            "tier":"C1_TOURNAMENT",
            "status":"pending",
            "message":f"C1_ROOM|{tournament_id}|{room_id}",
            "expires_at":expires_at,
            "updated_at":now_iso(),
        }),"ops_c1_create_realtime_invite",attempts=2)
        realtime_invite=(invite_result.data or [None])[0]
        if not realtime_invite:
            flash("Không thể tạo lời mời C1 realtime. Vui lòng thử lại.","error")
            return redirect(url_for("room_detail",room_id=room_id))
        execute_query(db.table("match_rooms").update({
            "invite_id":realtime_invite.get("id"),"note":_room_note(meta),"match_mode":"tournament","team_tier":"TOURNAMENT","updated_at":now_iso()
        }).eq("id",room_id),"ops_c1_room_bind_invite",attempts=2)
        ttl_cache_delete("invites_raw"); cache_delete("_rz_invites_all"); cache_delete("_rz_current_pending_invites")
        creator=(host_member or {}).get("display_name") or user.get("display_name") or user.get("username") or "Admin"
        create_user_notification(opponent_uid,"🏆 Lời mời thi đấu C1",f"{creator} đang mời bạn vào Phòng đấu C1.",url_for("c1_room_accept",tournament_id=tournament_id,room_id=room_id),"tournament_room_invite")
        flash(f"Đã gửi lời mời C1 realtime tới {opponent.get('display_name') or 'HLV'}.","success")
        return redirect(url_for("room_detail",room_id=room_id))

    @app.get('/tournaments/<tournament_id>/rooms/<room_id>/accept')
    @login_required
    def c1_room_accept(tournament_id,room_id):
        user=current_user() or {}; uid=str(user.get("id") or "")
        room=get_room(room_id); meta=_room_meta(room)
        if not room or not meta or str(meta.get("tournament_id"))!=str(tournament_id):
            flash("Phòng C1 không còn tồn tại.","error"); return redirect(url_for("c1_rooms"))
        if uid==str(room.get("host_user_id")):
            return redirect(url_for("room_detail",room_id=room_id))
        if str(meta.get("invited_user_id") or "")!=uid and not is_admin_user(user):
            flash("Phòng này không mời tài khoản của bạn.","error"); return redirect(url_for("c1_rooms",tournament_id=tournament_id))
        linked_match_id=str(meta.get("tournament_match_id") or "")
        if linked_match_id and str(meta.get("stage_code") or "")=="knockout":
            linked_match,_=_one(db.table("tournament_matches").select("*").eq("id",linked_match_id).eq("tournament_id",tournament_id),"ops_c1_accept_ko_gate")
            if linked_match and not _knockout_pair_is_unlocked(tournament_id,linked_match):
                flash("🔒 BTC đã khóa cặp Knockout này. Chưa thể vào phòng.","warning")
                return redirect(url_for("tournaments")+"#knockout-"+str(tournament_id))
        if not is_admin_user(user) and not _member(tournament_id,uid) and not (meta.get("test_sandbox_room") and _is_c1_test_user(tournament_id,uid)):
            flash("Chỉ HLV chính thức hoặc tài khoản thử nghiệm được cấp quyền mới vào phòng.","error"); return redirect(url_for("tournaments"))
        if room.get("guest_user_id"):
            if str(room.get("guest_user_id"))==uid:
                return redirect(url_for("room_detail",room_id=room_id))
            flash("Phòng đã đủ 2 HLV.","warning"); return redirect(url_for("c1_rooms",tournament_id=tournament_id))
        if str(room.get("status") or "")!="waiting_ready":
            flash("Phòng đã bắt đầu hoặc không còn nhận khách.","warning")
            return redirect(url_for("c1_rooms",tournament_id=tournament_id))
        active=active_room_for_user(uid)
        if active and str(active.get("id"))!=str(room_id):
            # Người được mời có thể đã tự mở một phòng trống trước đó. Khi họ
            # chủ động nhận lời C1, đóng phòng trống của chính họ rồi nhập phòng
            # người mời; không để 2 tài khoản mắc ở hai phòng riêng.
            can_close_solo = (
                str(active.get("host_user_id") or "")==uid
                and not active.get("guest_user_id")
                and str(active.get("status") or "")=="waiting_ready"
            )
            if can_close_solo:
                old_invite_id=active.get("invite_id")
                execute_query(db.table("match_rooms").update({
                    "status":"cancelled","guest_ready":False,"updated_at":now_iso(),
                }).eq("id",active.get("id")),"ops_c1_accept_close_receiver_solo_room",attempts=2)
                if old_invite_id:
                    try:
                        execute_query(db.table("match_invites").update({
                            "status":"cancelled","updated_at":now_iso(),
                        }).eq("id",old_invite_id).eq("status","pending"),"ops_c1_accept_cancel_receiver_old_invite",attempts=1)
                    except Exception:
                        pass
            else:
                flash("Bạn đang ở một phòng đấu khác có đối thủ/đã bắt đầu. Hãy kết thúc phòng đó trước.","warning")
                return redirect(url_for("room_detail",room_id=active.get("id")))
        bound_invite_id=room.get("invite_id")
        accepted_at=now_iso()
        # Do not trust team names sent by a room client; use membership assignment.
        stage_code=str(meta.get("stage_code") or "")
        fixed_stage=stage_code in {"league","knockout"} or (
            str((_stage(tournament_id,"league") or {}).get("status") or "")=="open"
            or str((_stage(tournament_id,"knockout") or {}).get("status") or "")=="open"
        )
        fixed_guest=(_member(tournament_id,uid) or {}).get("fixed_club_name") if fixed_stage else None
        if fixed_stage and not fixed_guest and not meta.get("test_sandbox_room"):
            flash("HLV chưa có CLB cố định; không thể nhận phòng C1 GĐ2/KO.","error")
            return redirect(url_for("c1_rooms",tournament_id=tournament_id))
        guest_patch={"guest_user_id":uid,"guest_ready":False,"invite_id":None,"updated_at":accepted_at}
        if fixed_guest:
            guest_patch["guest_team"]=fixed_guest
            guest_patch["host_team"]=(_member(tournament_id,room.get("host_user_id")) or {}).get("fixed_club_name")
        accept_result=execute_query(
            db.table("match_rooms").update(guest_patch).eq("id",room_id)
            .eq("status","waiting_ready").is_("guest_user_id","null"),
            "ops_c1_room_accept",attempts=2,
        )
        if not (accept_result.data or []):
            # Another request changed this room. Never overwrite an existing guest.
            cache_delete("_rz_rooms_all"); ttl_cache_delete("rooms_raw")
            latest=get_room(room_id)
            if latest and str(latest.get("guest_user_id") or "")==uid:
                return redirect(url_for("room_detail",room_id=room_id))
            flash("Phòng vừa thay đổi hoặc đã có khách khác. Hãy tải lại danh sách phòng C1.","warning")
            return redirect(url_for("c1_rooms",tournament_id=tournament_id))
        # V1.5.13: không báo nhận phòng thành công nếu guest_user_id chưa thật sự
        # được ghi xuống DB. Điều này tránh tình trạng khách vào được URL nhưng
        # phía chủ vẫn thấy "Đang chờ đối thủ".
        verify_result=execute_query(
            db.table("match_rooms").select("id,guest_user_id,guest_ready,updated_at").eq("id",room_id).limit(1),
            "ops_c1_room_accept_verify",
            attempts=2,
        )
        verified_room=(verify_result.data or [None])[0]
        if not verified_room or str(verified_room.get("guest_user_id") or "") != uid:
            flash("Chưa thể ghi nhận bạn vào vị trí Đội khách. Vui lòng bấm nhận lời mời lại.","error")
            return redirect(url_for("c1_rooms",tournament_id=tournament_id))
        if bound_invite_id:
            try:
                execute_query(db.table("match_invites").update({"status":"accepted","updated_at":accepted_at}).eq("id",bound_invite_id).eq("status","pending"),"ops_c1_realtime_invite_accept",attempts=1)
            except Exception:
                pass
        ttl_cache_delete("invites_raw"); cache_delete("_rz_invites_all"); cache_delete("_rz_current_pending_invites")
        flash("Đã vào Phòng đấu C1. Chủ phòng sẽ thấy bạn xuất hiện ngay; nút Sẵn sàng đã được mở.","success")
        return redirect(url_for("room_detail",room_id=room_id))

    @app.route('/tournaments/<tournament_id>/matches/<match_id>/room', methods=['GET','POST'])
    @login_required
    def tournament_match_room_enter(tournament_id,match_id):
        user=current_user() or {}; uid=str(user.get("id") or "")
        match,_=_one(db.table("tournament_matches").select("*").eq("id",match_id).eq("tournament_id",tournament_id),"ops_tournament_room_match")
        if not match or uid not in {str(match.get("home_user_id")),str(match.get("away_user_id"))}:
            flash("Bạn không thuộc trận đấu này.","error"); return redirect(url_for('tournaments')+"#rooms")
        # GĐ2/KO chỉ cho vào phòng khi giai đoạn thực sự mở và cả hai HLV đã có CLB cố định.
        stage_code=str(match.get("stage_code") or "")
        if stage_code in {"league","knockout"}:
            stage_rows,_=_rows(db.table("tournament_stages").select("stage_code,status").eq("tournament_id",tournament_id).eq("stage_code",stage_code),"ops_room_stage_gate")
            if not stage_rows or stage_rows[0].get("status")!="open":
                flash("Giai đoạn chưa mở; chưa thể tạo phòng thi đấu.","warning"); return redirect(url_for('tournaments')+"#rooms")
            if stage_code=="knockout" and not _knockout_pair_is_unlocked(tournament_id,match):
                flash("🔒 BTC chưa mở cặp Knockout này. Vui lòng chờ Admin mở trận.","warning")
                return redirect(url_for('tournaments')+"#knockout-"+str(tournament_id))
            participants=[_member(tournament_id,match.get(key)) for key in ("home_user_id","away_user_id")]
            if any(not m or not m.get("fixed_club_name") for m in participants):
                flash("Hai HLV phải được gán CLB cố định trước khi vào phòng.","error"); return redirect(url_for('tournaments')+"#rooms")
        pair_state=_pair_flow_state(tournament_id, match)
        if str(match.get("status") or "").lower()=="completed" and pair_state.get("is_complete"):
            flash("Cặp HLV này đã hoàn tất toàn bộ các trận trong lịch.","warning")
            return redirect(url_for('tournaments')+"#rooms")
        existing=None
        for r in _tournament_rooms(tournament_id):
            if str((r.get("tournament_meta") or {}).get("tournament_match_id"))==str(match_id) and r.get("status") not in {"completed","cancelled"}: existing=r; break
        if existing:
            allowed={str(match.get("home_user_id")),str(match.get("away_user_id"))}
            host_id=str(existing.get("host_user_id") or ""); guest_id=str(existing.get("guest_user_id") or "")
            if host_id not in allowed:
                execute_query(db.table("match_rooms").update({"status":"cancelled","updated_at":now_iso()}).eq("id",existing.get("id")),"ops_tournament_room_cancel_invalid_host",attempts=2)
                existing=None
            else:
                patch={"match_mode":"tournament","team_tier":"TOURNAMENT_GD1" if match.get("stage_code")=="stage1" else "TOURNAMENT","updated_at":now_iso()}
                if stage_code in {"league","knockout"} and existing.get("status")=="waiting_ready":
                    # Only waiting fixtures follow a later ticket reroll. Never
                    # overwrite clubs already locked for a playing/result room.
                    fixed={str(m.get("user_id")):m.get("fixed_club_name") for m in participants}
                    patch["host_team"]=fixed.get(host_id)
                    patch["guest_team"]=fixed.get(guest_id) if guest_id in allowed else None
                if existing.get("status")=="friendly_playing": patch["status"]="playing"
                if guest_id and guest_id not in allowed:
                    patch.update({"guest_user_id":None,"guest_ready":False,"guest_team":None,"guest_team_overall":None})
                    guest_id=""
                execute_query(db.table("match_rooms").update(patch).eq("id",existing.get("id")),"ops_tournament_room_normalize",attempts=2)
                if uid not in {host_id,guest_id}:
                    if guest_id:
                        flash("Phòng đã đủ 2 HLV.","warning"); return redirect(url_for('tournaments')+"#rooms")
                    join_patch={"guest_user_id":uid,"guest_ready":False,"match_mode":"tournament","updated_at":now_iso()}
                    if stage_code in {"league","knockout"}:
                        join_patch["guest_team"]=(_member(tournament_id,uid) or {}).get("fixed_club_name")
                    execute_query(db.table("match_rooms").update(join_patch).eq("id",existing.get("id")),"ops_tournament_room_join",attempts=2)
                return redirect(url_for("room_detail",room_id=existing.get("id")))
        active=active_room_for_user(uid)
        if active:
            flash("Bạn đang ở một phòng đấu khác. Hãy thoát phòng đó trước.","warning"); return redirect(url_for("room_detail",room_id=active.get("id")))
        dm=_decorate_matches(tournament_id,[match])[0]
        meta={"tournament_id":str(tournament_id),"tournament_match_id":str(match_id),"stage_code":match.get("stage_code"),"home_user_id":str(match.get("home_user_id")),"away_user_id":str(match.get("away_user_id")),"home_name":dm.get("home_name"),"away_name":dm.get("away_name")}
        fixed_host=(_member(tournament_id,uid) or {}).get("fixed_club_name") if stage_code in {"league","knockout"} else None
        row=execute_query(db.table("match_rooms").insert({"invite_id":None,"host_user_id":uid,"guest_user_id":None,"host_team":fixed_host,"team_tier":"TOURNAMENT_GD1" if match.get("stage_code")=="stage1" else "TOURNAMENT","match_mode":"tournament","friendly_tier":None,"status":"waiting_ready","guest_ready":False,"note":_room_note(meta),"state_expires_at":None,"updated_at":now_iso()}),"ops_tournament_room_create",attempts=2)
        room=(row.data or [{}])[0]
        flash("Đã tạo Phòng đấu C1. Khi sẵn sàng, hãy bấm Mời đối thủ ngay trong phòng.","success")
        return redirect(url_for("room_detail",room_id=room.get("id")))

    @app.post('/tournaments/<tournament_id>/rooms/<room_id>/next-match')
    @login_required
    def tournament_room_next_match(tournament_id, room_id):
        """
        V1.5.17:
        "Trận tiếp theo" = Trận 2 của CHÍNH cặp HLV hiện tại và vẫn ở nguyên room.
        Không nhảy sang cặp đối thủ khác.
        """
        user=current_user() or {}; uid=str(user.get("id") or "")
        room=get_room(room_id); meta=_room_meta(room)
        if not room or not meta or str(meta.get("tournament_id") or "") != str(tournament_id):
            flash("Không tìm thấy Phòng đấu C1 hiện tại.","error")
            return redirect(url_for('tournaments')+"#rooms")

        host_uid=str(room.get("host_user_id") or "")
        guest_uid=str(room.get("guest_user_id") or "")
        if uid != host_uid and not is_admin_user(user):
            flash("Chỉ Chủ phòng hoặc Admin mới được chuyển sang Trận 2.","warning")
            return redirect(url_for("room_detail",room_id=room_id))

        current_match_id=str(meta.get("tournament_match_id") or "")
        current_match,_=_one(
            db.table("tournament_matches").select("*").eq("id",current_match_id).eq("tournament_id",tournament_id),
            "ops_c1_next_same_room_current_match",
        )
        if not current_match:
            flash("Không tìm thấy trận C1 hiện tại.","error")
            return redirect(url_for("room_detail",room_id=room_id))

        if str(current_match.get("status") or "") != "completed" or str(room.get("status") or "") != "confirmed":
            flash("Chỉ chuyển sang Trận 2 sau khi kết quả Trận 1 đã được xác nhận.","warning")
            return redirect(url_for("room_detail",room_id=room_id))

        pair_ids={str(current_match.get("home_user_id") or ""),str(current_match.get("away_user_id") or "")}
        sibling=None
        same_pair_candidates=[]
        for candidate in _matches(tournament_id, current_match.get("stage_code")):
            cid=str(candidate.get("id") or "")
            if not cid or cid==current_match_id:
                continue
            cpair={str(candidate.get("home_user_id") or ""),str(candidate.get("away_user_id") or "")}
            if cpair != pair_ids:
                continue
            status=str(candidate.get("status") or "").lower()
            if status in {"completed","cancelled"}:
                continue
            same_pair_candidates.append(candidate)

        # C1 GĐ1 có 2 lượt. Chọn leg kế tiếp theo leg_no trước, không phụ thuộc
        # thứ tự Supabase trả về; tránh bấm Trận 2 nhưng lấy nhầm bản ghi khác.
        if same_pair_candidates:
            if str(current_match.get("stage_code") or "")=="stage1":
                cur_leg=int(current_match.get("leg_no") or 1)
                wanted_leg=2 if cur_leg==1 else 1
                sibling=next(
                    (c for c in same_pair_candidates if int(c.get("leg_no") or 1)==wanted_leg),
                    None,
                )
            if not sibling:
                sibling=sorted(
                    same_pair_candidates,
                    key=lambda c:(int(c.get("leg_no") or 999),str(c.get("created_at") or ""),str(c.get("id") or "")),
                )[0]

        if not sibling and str(current_match.get("stage_code") or "")=="stage1":
            pair_state=_pair_flow_state(tournament_id,current_match)
            if pair_state.get("missing_count",0)>0 and not pair_state.get("is_complete"):
                used_legs={int(r.get("leg_no") or 0) for r in pair_state.get("matches",[])}
                expected=int(pair_state.get("total_count") or 2)
                missing_leg=next((leg for leg in range(1,expected+1) if leg not in used_legs),len(used_legs)+1)
                created=execute_query(
                    db.table("tournament_matches").insert({
                        "tournament_id":tournament_id,"stage_code":"stage1",
                        "round_code":current_match.get("round_code"),
                        "home_user_id":current_match.get("away_user_id"),
                        "away_user_id":current_match.get("home_user_id"),
                        "status":"pending","leg_no":missing_leg,
                        "created_at":now_iso(),"updated_at":now_iso(),
                    }),
                    "ops_c1_next_create_missing_stage1_leg",attempts=2,
                )
                sibling=(created.data or [None])[0] if created is not None else None

        if not sibling:
            # Không còn leg nào và đã đủ số trận theo luật -> cặp đã hoàn tất.
            flash("✅ Cặp đấu C1 này đã hoàn tất đủ các trận.","success")
            return redirect(url_for('tournaments')+"#rooms")

        # Nếu trước đó đã lỡ sinh một room riêng cho leg 2, đóng room đó để bảo
        # đảm cả cặp chỉ tiếp tục trong room hiện tại.
        try:
            rows,_=_rows(
                db.table("match_rooms").select("id,note,status,host_user_id,guest_user_id").order("updated_at",desc=True).limit(300),
                "ops_c1_next_same_room_duplicate_scan",
            )
            for other in rows:
                if str(other.get("id") or "")==str(room_id):
                    continue
                ometa=_room_meta(other)
                if not ometa or str(ometa.get("tournament_id") or "")!=str(tournament_id):
                    continue
                if str(ometa.get("tournament_match_id") or "")!=str(sibling.get("id") or ""):
                    continue
                if str(other.get("status") or "") not in {"completed","cancelled"}:
                    execute_query(
                        db.table("match_rooms").update({
                            "status":"cancelled",
                            "updated_at":now_iso(),
                        }).eq("id",other.get("id")),
                        "ops_c1_next_same_room_cancel_duplicate",
                        attempts=2,
                    )
        except Exception as exc:
            app.logger.warning("C1 next match duplicate room cleanup failed: %s",exc)

        # Đổi room hiện tại sang match/leg 2 nhưng giữ nguyên 2 HLV trong phòng.
        history=list(meta.get("previous_match_ids") or [])
        if current_match_id and current_match_id not in history:
            history.append(current_match_id)

        dm=_decorate_matches(tournament_id,[sibling])[0]
        meta.update({
            "tournament_match_id":str(sibling.get("id")),
            "stage_code":sibling.get("stage_code"),
            "home_user_id":str(sibling.get("home_user_id") or ""),
            "away_user_id":str(sibling.get("away_user_id") or ""),
            "home_name":dm.get("home_name"),
            "away_name":dm.get("away_name"),
            "previous_match_ids":history,
            "current_leg_no":int(sibling.get("leg_no") or 2),
            # Token thay đổi mỗi lần mở leg mới để polling Host/Guest chắc chắn
            # nhận đây là một phiên trận mới dù hai HLV vẫn ở nguyên phòng.
            "transition_token":now_iso(),
        })

        # Đưa Trận 2 về pending trước rồi mới mở lại room. Như vậy Host/Guest
        # không thể nhìn thấy room leg 2 nhưng tournament_match vẫn còn state cũ.
        if str(sibling.get("status") or "") != "pending":
            execute_query(
                db.table("tournament_matches").update({
                    "status":"pending",
                    "updated_at":now_iso(),
                }).eq("id",sibling.get("id")).eq("tournament_id",tournament_id),
                "ops_c1_next_same_room_match2_pending_preopen",
                attempts=2,
            )

        # Reset CHỈ trạng thái của trận trong room; không xóa kết quả trận 1.
        next_started_at=now_iso()
        room_update_result=execute_query(
            db.table("match_rooms").update({
                "note":_room_note(meta),
                "status":"waiting_ready",
                # V1.5.44: Copy đúng cơ chế Rank. Sang trận mới, khách phải bấm
                # Sẵn Sàng lại; chỉ khi guest_ready=True thì Host mới được Quay đội.
                "guest_ready":False,
                "host_team":None,
                "guest_team":None,
                "host_team_overall":None,
                "guest_team_overall":None,
                "host_score":None,
                "guest_score":None,
                "invite_id":None,
                "state_expires_at":None,
                "match_mode":"tournament",
                "team_tier":"TOURNAMENT_GD1" if sibling.get("stage_code")=="stage1" else "TOURNAMENT",
                "updated_at":next_started_at,
            }).eq("id",room_id).eq("status","confirmed"),
            "ops_c1_next_same_room_reset_for_leg2",
            attempts=2,
        )
        if not (room_update_result.data or []):
            # Có request khác vừa đổi trạng thái: đọc lại DB thay vì giả định đã mở Trận 2.
            latest_room=get_room(room_id)
            latest_meta=_room_meta(latest_room) if latest_room else {}
            if not (
                latest_room
                and str(latest_room.get("status") or "")=="waiting_ready"
                and str((latest_meta or {}).get("tournament_match_id") or "")==str(sibling.get("id") or "")
            ):
                flash("Chưa thể mở Trận 2 vì trạng thái phòng vừa thay đổi. Hãy bấm Trận 2 lại một lần.","warning")
                return redirect(url_for("room_detail",room_id=room_id))

        # V1.5.28: xác nhận DB đã thực sự chuyển room sang Trận 2 trước khi báo thành công.
        verified,_=_one(
            db.table("match_rooms").select("id,status,guest_ready,host_user_id,guest_user_id,note,updated_at").eq("id",room_id),
            "ops_c1_next_same_room_verify_leg2",
        )
        verified_meta=_room_meta(verified) if verified else {}
        if (
            not verified
            or str(verified.get("status") or "")!="waiting_ready"
            or bool(verified.get("guest_ready"))
            or str(verified.get("host_user_id") or "")!=host_uid
            or str(verified.get("guest_user_id") or "")!=guest_uid
            or str(verified_meta.get("tournament_match_id") or "")!=str(sibling.get("id") or "")
        ):
            flash("Chưa thể chuyển phòng sang Trận 2. Vui lòng bấm lại sau vài giây.","error")
            return redirect(url_for("room_detail",room_id=room_id))

        # Dọn cache để cả Host và Guest nhận state waiting_ready ngay ở poll kế tiếp.
        cache_delete("_rz_rooms_all")
        cache_delete("_rz_current_pending_invites")
        ttl_cache_delete("rooms_raw")
        try:
            create_user_notification(
                guest_uid,
                "🏆 Trận 2 đã sẵn sàng",
                "Chủ phòng đã chuyển sang Trận 2. Hãy vào phòng và bấm Sẵn Sàng.",
                url_for("room_detail",room_id=room_id),
                "c1_game2_ready",
            )
        except Exception as exc:
            app.logger.warning("C1 game2 guest notification failed room=%s: %s",room_id,exc)

        flash("🏆 Đã chuyển sang Trận 2. Đội khách hãy bấm Sẵn Sàng.","success")
        return redirect(url_for("room_detail",room_id=room_id))

    @app.post('/tournaments/<tournament_id>/rooms/<room_id>/invite-opponent')
    @login_required
    def tournament_room_invite_opponent(tournament_id,room_id):
        user=current_user() or {}; uid=str(user.get("id") or "")
        room,meta,match=_room_match_or_error(tournament_id,room_id)
        if not room or not match:
            flash("Không tìm thấy phòng/trận C1.","error"); return redirect(url_for("c1_rooms",tournament_id=tournament_id))
        if uid!=str(room.get("host_user_id")) and not is_admin_user(user):
            flash("Chỉ chủ phòng mới được mời đối thủ.","error"); return redirect(url_for("room_detail",room_id=room_id))
        if room.get("guest_user_id"):
            flash("Đối thủ đã ở trong phòng.","warning"); return redirect(url_for("room_detail",room_id=room_id))
        opponent_uid=str(match.get("away_user_id") if uid==str(match.get("home_user_id")) else match.get("home_user_id"))
        dm=_decorate_matches(tournament_id,[match])[0]
        opponent_name=dm.get("away_name") if uid==str(match.get("home_user_id")) else dm.get("home_name")
        creator=user.get("display_name") or user.get("username") or "Đối thủ"
        meta["invited_user_id"]=opponent_uid
        execute_query(
            db.table("match_rooms").update({
                "note":_room_note(meta),
                "match_mode":"tournament",
                "team_tier":"TOURNAMENT_GD1" if match.get("stage_code")=="stage1" else "TOURNAMENT",
                "updated_at":now_iso(),
            }).eq("id",room_id),
            "ops_tournament_match_room_bind_invite",
            attempts=2,
        )
        notification = create_user_notification(
            opponent_uid,
            "🏆 Lời mời thi đấu C1",
            f"{creator} đang chờ bạn trong Phòng đấu C1. Bấm để vào phòng thi đấu.",
            url_for("c1_room_accept", tournament_id=tournament_id, room_id=room_id),
            "tournament_room_invite",
        )
        if notification:
            flash(f"Đã gửi lời mời C1 tới {opponent_name or 'đối thủ'}.","success")
        else:
            app.logger.warning("Không tạo được thông báo lời mời C1 room=%s opponent=%s", room_id, opponent_uid)
            flash("Không gửi được thông báo C1. Đối thủ vẫn có thể vào từ Phòng đấu C1.","warning")
        return redirect(url_for("room_detail",room_id=room_id))

    @app.post('/tournaments/<tournament_id>/rooms/<room_id>/start-fixed-match')
    @login_required
    def tournament_room_start_fixed_match(tournament_id, room_id):
        """Legacy/recovery start: GĐ2 normally begins when guest presses Ready."""
        from modules.c1_fixed_match_service import start_assigned_club_match
        user=current_user() or {}
        room=get_room(room_id)
        uid = str(user.get("id") or "")
        is_host = bool(room and uid == str(room.get("host_user_id") or ""))
        is_ready_guest = bool(room and uid == str(room.get("guest_user_id") or "") and room.get("guest_ready"))
        if not (is_host or is_ready_guest):
            flash("Chỉ chủ phòng hoặc khách đã Sẵn sàng mới được thử bắt đầu trận C1.","warning")
            return redirect(url_for("room_detail",room_id=room_id))
        try:
            success,message,_=start_assigned_club_match(db,execute_query,tournament_id,room_id,now_iso)
            cache_delete("_rz_rooms_all"); ttl_cache_delete("rooms_raw")
            flash(message,"success" if success else "warning")
        except Exception:
            app.logger.exception("C1 fixed match start failed room=%s tournament=%s",room_id,tournament_id)
            flash("Không bắt đầu được trận C1; vui lòng thử lại hoặc liên hệ Admin.","error")
        return redirect(url_for("room_detail",room_id=room_id))

    @app.post('/tournaments/<tournament_id>/rooms/<room_id>/random-stage1-clubs')
    @login_required
    def tournament_room_random_stage1_clubs(tournament_id,room_id):
        user=current_user() or {}; uid=str(user.get("id") or "")
        room=get_room(room_id); meta=_room_meta(room)
        if not room or not meta or str(meta.get("tournament_id"))!=str(tournament_id):
            flash("Không tìm thấy phòng GĐ1.","error"); return redirect(url_for('tournaments')+"#rooms")
        if uid not in {str(room.get("host_user_id")),str(room.get("guest_user_id"))}:
            flash("Bạn không thuộc phòng này.","error"); return redirect(url_for('tournaments')+"#rooms")
        if uid != str(room.get("host_user_id")) and not is_admin_user(user):
            flash("Chỉ chủ phòng mới được Random CLB.","warning"); return redirect(url_for("room_detail",room_id=room_id))
        if str(meta.get("stage_code") or "") != "stage1" and not bool(meta.get("admin_test_room")):
            flash("Random CLB này dùng cho GĐ1 hoặc phòng test của Admin.","warning"); return redirect(url_for("room_detail",room_id=room_id))
        if not room.get("guest_user_id"):
            flash("Phòng chưa đủ 2 HLV.","warning"); return redirect(url_for("room_detail",room_id=room_id))
        if not bool(room.get("guest_ready")):
            flash("Đội khách chưa Sẵn sàng. Hãy chờ đối thủ bấm Sẵn sàng trước khi quay đội.","warning"); return redirect(url_for("room_detail",room_id=room_id))
        pool=_stage1_club_pool(tournament_id)
        if len(pool)!=16:
            flash(f"Pool C1 phải có đúng 16 CLB. Hiện đang có {len(pool)}/16 đội.","error"); return redirect(url_for("room_detail",room_id=room_id))
        # Một phòng chỉ được random đúng một lần để tránh reroll làm sai lịch sử 6 trận.
        if room.get("host_team") or room.get("guest_team"):
            flash("Phòng này đã quay CLB rồi. Không thể quay lại trong cùng một trận.","warning"); return redirect(url_for("room_detail",room_id=room_id))

        host_uid=str(room.get("host_user_id") or "")
        guest_uid=str(room.get("guest_user_id") or "")
        host_used=_stage1_used_club_names(tournament_id,host_uid)
        guest_used=_stage1_used_club_names(tournament_id,guest_uid)
        host_available=[c for c in pool if c.get("name") not in host_used]
        guest_available=[c for c in pool if c.get("name") not in guest_used]
        pairs=[(a,b) for a in host_available for b in guest_available if a.get("name")!=b.get("name")]
        if not pairs:
            flash("Không còn cặp CLB hợp lệ để random mà không trùng lịch sử của 2 HLV. Hãy kiểm tra lại lịch sử GĐ1/pool CLB.","error"); return redirect(url_for("room_detail",room_id=room_id))
        a,b=random.choice(pairs)
        execute_query(db.table("match_rooms").update({"host_team":a["name"],"guest_team":b["name"],"host_team_overall":a.get("overall") or None,"guest_team_overall":b.get("overall") or None,"team_tier":"TOURNAMENT_GD1","match_mode":"tournament","status":"playing","updated_at":now_iso()}).eq("id",room_id),"ops_tournament_stage1_random_clubs",attempts=2)
        match_id=meta.get("match_id") or meta.get("tournament_match_id")
        _save_stage1_random_history(tournament_id,host_uid,a["name"],room_id=room_id,match_id=match_id)
        _save_stage1_random_history(tournament_id,guest_uid,b["name"],room_id=room_id,match_id=match_id)
        flash(f'GĐ1 Random: {a["name"]} vs {b["name"]}. Mỗi HLV sẽ không bị lặp lại CLB đã ra trong 6 trận GĐ1.',"success")
        return redirect(url_for("room_detail",room_id=room_id))

    def _tournament_result_key(match_id):
        return f"match_result_proposal:{match_id}"

    def _tournament_result_proposal(tournament_id, match_id):
        return _setting(tournament_id, _tournament_result_key(match_id), {}) or {}

    def _save_tournament_result_proposal(tournament_id, match_id, value):
        execute_query(
            db.table("tournament_settings").upsert({
                "tournament_id": tournament_id,
                "setting_key": _tournament_result_key(match_id),
                "setting_value": value,
                "updated_at": now_iso(),
            }, on_conflict="tournament_id,setting_key"),
            "ops_tournament_result_proposal", attempts=2,
        )

    def _room_match_or_error(tournament_id, room_id):
        room=get_room(room_id); meta=_room_meta(room)
        if not room or not meta or str(meta.get("tournament_id"))!=str(tournament_id):
            return None,None,None
        match_id=str(meta.get("tournament_match_id") or "")
        match,_=_one(db.table("tournament_matches").select("*").eq("id",match_id).eq("tournament_id",tournament_id),"ops_tournament_result_match")
        return room,meta,match

    @app.post('/tournaments/<tournament_id>/rooms/<room_id>/submit-result')
    @login_required
    def tournament_room_submit_result(tournament_id,room_id):
        user=current_user() or {}; uid=str(user.get("id") or "")
        room,meta,match=_room_match_or_error(tournament_id,room_id)
        if not room or not match:
            flash("Không tìm thấy phòng/trận giải.","error"); return redirect(url_for('tournaments'))
        if uid!=str(room.get("host_user_id")) and not is_admin_user(user):
            flash("Chỉ chủ phòng mới được nhập kết quả.","error"); return redirect(url_for("room_detail",room_id=room_id))
        if str(room.get("status") or "") != "playing":
            flash("Chỉ được gửi kết quả khi trận C1 đang thi đấu.","warning"); return redirect(url_for("room_detail",room_id=room_id))
        if str(match.get("status")) in {"completed","cancelled"}:
            flash("Trận này đã hoàn tất.","warning"); return redirect(url_for("room_detail",room_id=room_id))
        try:
            hs=max(0,min(99,int(request.form.get("host_score") or 0))); gs=max(0,min(99,int(request.form.get("guest_score") or 0)))
        except Exception:
            flash("Tỷ số không hợp lệ.","error"); return redirect(url_for("room_detail",room_id=room_id))
        host_uid=str(room.get("host_user_id") or ""); guest_uid=str(room.get("guest_user_id") or "")
        if not guest_uid:
            flash("Phòng chưa đủ 2 HLV.","warning"); return redirect(url_for("room_detail",room_id=room_id))
        if host_uid==str(match.get("home_user_id")):
            home_score,away_score=hs,gs
        else:
            home_score,away_score=gs,hs
        proposal={
            "status":"waiting_confirm", "submitted_by":uid,
            "host_score":hs,"guest_score":gs,"home_score":home_score,"away_score":away_score,
            "submitted_at":now_iso(),
        }
        _save_tournament_result_proposal(tournament_id,match.get("id"),proposal)
        execute_query(db.table("match_rooms").update({"host_score":hs,"guest_score":gs,"status":"waiting_result_confirm","updated_at":now_iso()}).eq("id",room_id),"ops_tournament_room_wait_confirm",attempts=2)
        execute_query(db.table("tournament_matches").update({"status":"playing","updated_at":now_iso()}).eq("id",match.get("id")),"ops_tournament_match_wait_confirm",attempts=2)
        flash("Đã gửi kết quả. Đang chờ đối thủ xác nhận.","success")
        return redirect(url_for("room_detail",room_id=room_id))

    @app.post('/tournaments/<tournament_id>/rooms/<room_id>/confirm-result')
    @login_required
    def tournament_room_confirm_result(tournament_id,room_id):
        user=current_user() or {}; uid=str(user.get("id") or "")
        room,meta,match=_room_match_or_error(tournament_id,room_id)
        if not room or not match:
            flash("Không tìm thấy phòng/trận giải.","error"); return redirect(url_for('tournaments'))
        if uid!=str(room.get("guest_user_id")) and not is_admin_user(user):
            flash("Chỉ đối thủ mới được xác nhận kết quả.","error"); return redirect(url_for("room_detail",room_id=room_id))
        if str(room.get("status") or "") != "waiting_result_confirm":
            flash("Phòng C1 không còn kết quả chờ xác nhận.","warning"); return redirect(url_for("room_detail",room_id=room_id))
        prop=_tournament_result_proposal(tournament_id,match.get("id"))
        if prop.get("status")!="waiting_confirm":
            flash("Không có kết quả nào đang chờ xác nhận.","warning"); return redirect(url_for("room_detail",room_id=room_id))
        hs=int(prop.get("home_score") or 0); aw=int(prop.get("away_score") or 0)
        winner=match.get("home_user_id") if hs>aw else (match.get("away_user_id") if aw>hs else None)
        execute_query(db.table("tournament_matches").update({"home_score":hs,"away_score":aw,"winner_user_id":winner,"status":"completed","completed_at":now_iso(),"updated_at":now_iso()}).eq("id",match.get("id")),"ops_tournament_result_confirm",attempts=2)
        prop.update({"status":"confirmed","confirmed_by":uid,"confirmed_at":now_iso()}); _save_tournament_result_proposal(tournament_id,match.get("id"),prop)

        # V1.5.44: C1 copy đúng nhịp của Rank. Ngay khi kết quả Trận N được xác nhận,
        # nếu đúng cặp còn Trận N+1 thì chuyển CHÍNH room hiện tại sang trận kế tiếp và
        # reset về waiting_ready. Không giữ room ở confirmed để người chơi phải bấm Đá Tiếp.
        pair_state=_pair_flow_state(tournament_id, match)
        next_match=pair_state.get("next_match")

        # Dữ liệu GĐ1 cũ có thể thiếu sẵn row lượt tiếp theo. Nếu luật của stage vẫn yêu cầu
        # thêm trận cho đúng cặp thì tạo row thiếu ngay tại thời điểm xác nhận, tương tự Rank
        # tạo phiên trận mới sau khi trận cũ hoàn tất.
        if not next_match and str(match.get("stage_code") or "")=="stage1" and pair_state.get("missing_count",0)>0:
            used_legs={int(r.get("leg_no") or 0) for r in pair_state.get("matches",[])}
            expected=max(2,int(pair_state.get("total_count") or 2))
            missing_leg=next((leg for leg in range(1,expected+1) if leg not in used_legs),len(used_legs)+1)
            created=execute_query(
                db.table("tournament_matches").insert({
                    "tournament_id":tournament_id,
                    "stage_code":"stage1",
                    "round_code":match.get("round_code"),
                    "home_user_id":match.get("away_user_id"),
                    "away_user_id":match.get("home_user_id"),
                    "status":"pending",
                    "leg_no":missing_leg,
                    "created_at":now_iso(),
                    "updated_at":now_iso(),
                }),
                "ops_c1_auto_create_next_match_after_confirm",attempts=2,
            )
            next_match=(created.data or [None])[0] if created is not None else None

        if str(match.get("stage_code") or "")=="stage1":
            try:
                _auto_finish_stage1(tournament_id)
            except Exception:
                app.logger.exception("C1 stage1 auto-finalization failed; result remains confirmed")

        if next_match:
            # Giữ lịch sử match_id để debug/đối soát nhưng room luôn trỏ vào trận hiện tại.
            history=list(meta.get("previous_match_ids") or [])
            current_mid=str(match.get("id") or "")
            if current_mid and current_mid not in history:
                history.append(current_mid)
            dm=_decorate_matches(tournament_id,[next_match])[0]
            meta.update({
                "tournament_match_id":str(next_match.get("id") or ""),
                "stage_code":next_match.get("stage_code") or match.get("stage_code"),
                "home_user_id":str(next_match.get("home_user_id") or ""),
                "away_user_id":str(next_match.get("away_user_id") or ""),
                "home_name":dm.get("home_name"),
                "away_name":dm.get("away_name"),
                "previous_match_ids":history,
                "current_leg_no":int(next_match.get("leg_no") or (int(match.get("leg_no") or 1)+1)),
                "transition_token":now_iso(),
            })

            # Bảo đảm trận kế tiếp ở trạng thái pending trước khi mở lại room.
            if str(next_match.get("status") or "").lower()!="pending":
                execute_query(
                    db.table("tournament_matches").update({
                        "status":"pending","updated_at":now_iso(),
                    }).eq("id",next_match.get("id")).eq("tournament_id",tournament_id),
                    "ops_c1_auto_next_match_pending",attempts=2,
                )

            # V1.5.45: dùng CHUNG state machine với phòng kiểm thử. Chỉ lớp dữ liệu
            # trận đấu khác nhau; trạng thái room sau xác nhận là một nguồn duy nhất.
            room_patch=_c1_rank_style_next_room_patch(
                meta, uid,
                "TOURNAMENT_GD1" if str(next_match.get("stage_code") or "")=="stage1" else "TOURNAMENT",
            )
            moved=execute_query(
                db.table("match_rooms").update(room_patch).eq("id",room_id).eq("status","waiting_result_confirm"),
                "ops_c1_confirm_auto_advance_same_room",attempts=2,
            )
            if not (moved.data or []):
                cache_delete("_rz_rooms_all"); ttl_cache_delete("rooms_raw")
                latest=get_room(room_id)
                latest_meta=_room_meta(latest) if latest else {}
                if not (
                    latest and str(latest.get("status") or "")=="waiting_ready"
                    and str((latest_meta or {}).get("tournament_match_id") or "")==str(next_match.get("id") or "")
                ):
                    # V1.5.44: không quay về state `confirmed`/Đá Tiếp. Retry trực tiếp
                    # trạng thái Rank-style theo room id; đây là idempotent vì room_patch
                    # luôn trỏ đúng next_match và reset toàn bộ dữ liệu trận cũ.
                    retry=execute_query(
                        db.table("match_rooms").update(room_patch).eq("id",room_id),
                        "ops_c1_confirm_auto_advance_retry_rank_style",attempts=2,
                    )
                    cache_delete("_rz_rooms_all"); ttl_cache_delete("rooms_raw")
                    latest=get_room(room_id)
                    latest_meta=_room_meta(latest) if latest else {}
                    if not (
                        latest and str(latest.get("status") or "")=="waiting_ready"
                        and not bool(latest.get("guest_ready"))
                        and str((latest_meta or {}).get("tournament_match_id") or "")==str(next_match.get("id") or "")
                    ):
                        app.logger.error(
                            "C1 auto advance failed room=%s next_match=%s retry_rows=%s",
                            room_id, next_match.get("id"), len((retry.data or [])) if retry is not None else -1,
                        )
                        flash("Kết quả đã được xác nhận nhưng phòng chưa đồng bộ được Trận kế tiếp. Hãy tải lại phòng; hệ thống sẽ tự phục hồi, không cần bấm Đá Tiếp.","warning")
                        return redirect(url_for("room_detail",room_id=room_id))

            cache_delete("_rz_rooms_all"); ttl_cache_delete("rooms_raw")
            flash(f"Đã xác nhận Trận {int(match.get('leg_no') or 1)}. Phòng đã chuyển sang Trận {int(next_match.get('leg_no') or (int(match.get('leg_no') or 1)+1))}. Hai HLV vào trận tiếp theo; với GĐ2, Chủ phòng bấm Bắt đầu trận (không quay CLB).","success")
            return redirect(url_for("room_detail",room_id=room_id))

        # Chỉ khi không còn bất kỳ trận kế tiếp nào theo lịch/luật của đúng cặp mới kết thúc.
        execute_query(
            db.table("match_rooms").update({
                "status":"confirmed",
                "guest_ready":False,
                "state_expires_at":None,
                "confirmed_by_id":uid,
                "updated_at":now_iso(),
            }).eq("id",room_id),
            "ops_tournament_room_pair_finished",attempts=2,
        )
        cache_delete("_rz_rooms_all"); ttl_cache_delete("rooms_raw")
        flash("Đã xác nhận kết quả. Cặp đấu đã hoàn tất đủ số trận và BXH giải đã được cập nhật.","success")
        return redirect(url_for("room_detail",room_id=room_id))

    @app.post('/tournaments/<tournament_id>/rooms/<room_id>/dispute-result')
    @login_required
    def tournament_room_dispute_result(tournament_id,room_id):
        user=current_user() or {}; uid=str(user.get("id") or "")
        room,meta,match=_room_match_or_error(tournament_id,room_id)
        if not room or not match:
            flash("Không tìm thấy phòng/trận giải.","error"); return redirect(url_for('tournaments'))
        if uid!=str(room.get("guest_user_id")) and not is_admin_user(user):
            flash("Chỉ đối thủ mới được báo sai kết quả.","error"); return redirect(url_for("room_detail",room_id=room_id))
        if str(room.get("status") or "") != "waiting_result_confirm":
            flash("Phòng C1 không còn kết quả chờ xử lý.","warning"); return redirect(url_for("room_detail",room_id=room_id))
        prop=_tournament_result_proposal(tournament_id,match.get("id"))
        if prop.get("status")!="waiting_confirm":
            flash("Kết quả này không còn ở trạng thái chờ xác nhận.","warning"); return redirect(url_for("room_detail",room_id=room_id))
        prop.update({"status":"disputed","disputed_by":uid,"disputed_at":now_iso(),"reason":(request.form.get("reason") or "Sai kết quả").strip()[:300]})
        _save_tournament_result_proposal(tournament_id,match.get("id"),prop)
        execute_query(db.table("tournament_matches").update({"status":"disputed","updated_at":now_iso()}).eq("id",match.get("id")),"ops_tournament_result_dispute",attempts=2)
        execute_query(db.table("match_rooms").update({"status":"disputed","updated_at":now_iso()}).eq("id",room_id),"ops_tournament_room_dispute",attempts=2)
        flash("Đã báo sai kết quả. Admin sẽ xử lý.","warning")
        return redirect(url_for("room_detail",room_id=room_id))

    def _c1_rank_style_next_room_patch(meta, confirmed_by_id, team_tier="TOURNAMENT"):
        """Một state machine reset dùng chung cho phòng C1 thật và phòng kiểm thử.

        Sau khi Trận N được xác nhận, cả hai luồng đều phải trở về đúng trạng thái
        của Rank: waiting_ready + guest_ready=False, xóa toàn bộ dữ liệu trận cũ.
        Lớp dữ liệu (tournament_matches hay lịch sử kiểm thử) được xử lý bên ngoài.
        """
        return {
            "note":_room_note(meta),
            "status":"waiting_ready",
            "guest_ready":False,
            "host_team":None,"guest_team":None,
            "host_team_overall":None,"guest_team_overall":None,
            "host_team_logo_url":None,"guest_team_logo_url":None,
            "host_team_league":None,"guest_team_league":None,
            "host_score":None,"guest_score":None,"match_id":None,
            "submitted_by_id":None,"confirmed_by_id":confirmed_by_id,
            "invite_id":None,"state_expires_at":None,
            "match_mode":"tournament","team_tier":team_tier,
            "updated_at":now_iso(),
        }

    def _c1_test_room_or_error(tournament_id, room_id):
        room=get_room(room_id); meta=_room_meta(room)
        if not room or not meta or str(meta.get("tournament_id"))!=str(tournament_id) or not meta.get("test_sandbox_room"):
            return None,None
        return room,meta

    @app.post('/tournaments/<tournament_id>/rooms/<room_id>/test-submit-result')
    @login_required
    def c1_test_room_submit_result(tournament_id,room_id):
        user=current_user() or {}; uid=str(user.get("id") or "")
        room,meta=_c1_test_room_or_error(tournament_id,room_id)
        if not room or uid!=str(room.get("host_user_id") or "") or not _is_c1_test_user(tournament_id,uid):
            flash("Chỉ chủ phòng thử nghiệm được gửi kết quả.","error"); return redirect(url_for("room_detail",room_id=room_id))
        if not room.get("guest_user_id"):
            flash("Phòng chưa đủ 2 người.","warning"); return redirect(url_for("room_detail",room_id=room_id))
        try:
            hs=max(0,min(99,int(request.form.get("host_score") or 0))); gs=max(0,min(99,int(request.form.get("guest_score") or 0)))
        except Exception:
            flash("Tỷ số không hợp lệ.","error"); return redirect(url_for("room_detail",room_id=room_id))
        test_round_no=max(1,int(meta.get("test_round_no") or 1))
        meta["test_result"]={
            "status":"waiting_confirm","host_score":hs,"guest_score":gs,
            "submitted_by":uid,"submitted_at":now_iso(),"test_round_no":test_round_no,
            "result_id":f"{room_id}:test:{test_round_no}",
        }
        execute_query(db.table("match_rooms").update({"host_score":hs,"guest_score":gs,"status":"waiting_result_confirm","note":_room_note(meta),"updated_at":now_iso()}).eq("id",room_id),"ops_c1_test_submit_result",attempts=2)
        flash("Đã gửi kết quả. Chờ đối thủ xác nhận.","success")
        return redirect(url_for("room_detail",room_id=room_id))

    @app.post('/tournaments/<tournament_id>/rooms/<room_id>/test-confirm-result')
    @login_required
    def c1_test_room_confirm_result(tournament_id,room_id):
        user=current_user() or {}; uid=str(user.get("id") or "")
        room,meta=_c1_test_room_or_error(tournament_id,room_id)
        if not room or uid!=str(room.get("guest_user_id") or "") or not _is_c1_test_user(tournament_id,uid):
            flash("Chỉ đối thủ được xác nhận kết quả.","error"); return redirect(url_for("room_detail",room_id=room_id))
        result=meta.get("test_result") or {}
        if result.get("status")!="waiting_confirm":
            flash("Không có kết quả đang chờ xác nhận.","warning"); return redirect(url_for("room_detail",room_id=room_id))
        # V1.5.44: COPY NGUYÊN NHỊP RANK cho SANDBOX.
        # Xác nhận Trận N -> lưu kết quả vào lịch sử TEST -> reset chính room về
        # waiting_ready, guest_ready=False -> khách bấm Sẵn Sàng -> chủ Quay đội.
        confirmed_at=now_iso()
        test_round_no=max(1,int(result.get("test_round_no") or meta.get("test_round_no") or 1))
        result.update({
            "status":"confirmed","confirmed_by":uid,"confirmed_at":confirmed_at,
            "test_round_no":test_round_no,
            "result_id":result.get("result_id") or f"{room_id}:test:{test_round_no}",
        })
        history=list(meta.get("test_result_history") or [])
        result_id=str(result.get("result_id") or "")
        if not any(str(x.get("result_id") or "")==result_id for x in history):
            history.append(dict(result))
        meta["test_result_history"]=history[-100:]
        meta["test_round_no"]=test_round_no+1
        meta["test_result"]={}
        meta["transition_token"]=confirmed_at

        # V1.5.45: phòng kiểm thử gọi đúng cùng state machine với phòng C1 thật.
        room_patch=_c1_rank_style_next_room_patch(meta, uid, "TOURNAMENT")
        room_patch["updated_at"]=confirmed_at
        updated=execute_query(
            db.table("match_rooms").update(room_patch).eq("id",room_id).eq("status","waiting_result_confirm"),
            "ops_c1_test_confirm_result_reset_like_rank",attempts=2,
        )
        if not (updated.data or []):
            flash("Kết quả đã được xác nhận nhưng phòng vừa thay đổi trạng thái. Hãy tải lại phòng.","warning")
            return redirect(url_for("room_detail",room_id=room_id))
        cache_delete("_rz_rooms_all"); ttl_cache_delete("rooms_raw")
        flash(f"Đã xác nhận Trận {test_round_no}. Phòng đã chuyển sang Trận {test_round_no+1}: khách bấm Sẵn Sàng, chủ phòng chờ để Quay đội.","success")
        return redirect(url_for("room_detail",room_id=room_id))

    @app.post('/tournaments/<tournament_id>/rooms/<room_id>/test-dispute-result')
    @login_required
    def c1_test_room_dispute_result(tournament_id,room_id):
        user=current_user() or {}; uid=str(user.get("id") or "")
        room,meta=_c1_test_room_or_error(tournament_id,room_id)
        if not room or uid!=str(room.get("guest_user_id") or "") or not _is_c1_test_user(tournament_id,uid):
            flash("Chỉ đối thủ được báo sai kết quả.","error"); return redirect(url_for("room_detail",room_id=room_id))
        result=meta.get("test_result") or {}
        result.update({"status":"disputed","disputed_by":uid,"disputed_at":now_iso(),"reason":(request.form.get("reason") or "Sai kết quả").strip()[:300]}); meta["test_result"]=result
        execute_query(db.table("match_rooms").update({"status":"disputed","note":_room_note(meta),"updated_at":now_iso()}).eq("id",room_id),"ops_c1_test_dispute_result",attempts=2)
        flash("Đã tạo tranh chấp trong khu kiểm thử. Không ảnh hưởng dữ liệu giải chính thức.","warning")
        return redirect(url_for("room_detail",room_id=room_id))

    return {k: v for k, v in locals().items() if k.startswith('_') and callable(v)}
