"""Internal tournament competition partition extracted from the legacy monolith.

Registered only through :mod:`modules.tournament_competition`.
"""

def register_scheduling(context):
    globals().update(context)

    @app.post('/tournaments/<tournament_id>/availability')
    @login_required
    def tournament_availability_save(tournament_id):
        uid=(current_user() or {}).get("id")
        if not _member(tournament_id,uid):
            flash("Bạn chưa phải HLV của giải đấu này.","error"); return _tournament_landing_return(tournament_id,"schedule")
        allowed={slot["iso"] for day in _availability_days() for slot in day["slots"]}
        selected=[]
        for raw in request.form.getlist("slots"):
            try:
                vn_tz=timezone(timedelta(hours=7)); dt=datetime.fromisoformat(raw).astimezone(vn_tz); iso=dt.isoformat()
                if iso in allowed: selected.append(iso)
            except Exception: pass
        # Giữ lại các giờ thủ công; form checkbox chỉ thay các slot chuẩn.
        existing=_availability_rows(tournament_id,[uid])
        custom_existing=[r.get("slot_iso") for r in existing if r.get("slot_iso") not in allowed]
        execute_query(db.table("tournament_availability_slots").delete().eq("tournament_id",tournament_id).eq("user_id",uid),"ops_availability_clear",attempts=2)
        final_slots=sorted(set(selected+custom_existing))
        for iso in final_slots:
            execute_query(db.table("tournament_availability_slots").insert({"tournament_id":tournament_id,"user_id":uid,"slot_at":iso,"created_at":now_iso(),"updated_at":now_iso()}),"ops_availability_insert",attempts=2)
        flash(f"Đã lưu lịch thi đấu của bạn: {len(final_slots)} khung giờ trong 3 ngày gần nhất.","success")
        return _tournament_landing_return(tournament_id,"schedule")

    @app.post('/admin/tournaments/<tournament_id>/test-availability/simple')
    @login_required
    def admin_tournament_test_availability_simple_save(tournament_id):
        user=current_user() or {}
        uid=str(user.get("id") or "")
        is_test=_is_c1_test_user(tournament_id,uid)
        if not is_admin_user(user) and not is_test:
            flash("Bạn không có quyền lưu lịch kiểm thử.","error")
            return _tournament_landing_return(tournament_id,"schedule")
        days=_availability_days()
        allowed={slot["iso"] for day in days for slot in day["slots"]}
        selected=[]
        # Form lịch đầy đủ gửi checkbox `slots`; cổng bắt buộc gửi khoảng Từ/Đến.
        for raw in request.form.getlist("slots"):
            try:
                iso=datetime.fromisoformat(str(raw)).isoformat()
                if iso in allowed:
                    selected.append(iso)
            except Exception:
                continue
        if not selected and any(request.form.get(f"start_{i}") or request.form.get(f"end_{i}") for i in range(len(days))):
            vn_tz=timezone(timedelta(hours=7)); now=datetime.now(vn_tz)
            for idx,d in enumerate(days):
                start_raw=(request.form.get(f"start_{idx}") or "").strip()
                end_raw=(request.form.get(f"end_{idx}") or "").strip()
                if not start_raw and not end_raw:
                    continue
                if not start_raw or not end_raw:
                    flash(f"{d['label']}: hãy chọn đủ giờ Từ và Đến.","warning")
                    return _tournament_landing_return(tournament_id,"schedule")
                try:
                    day=datetime.fromisoformat(d["date"]).date()
                    sh,sm=[int(x) for x in start_raw.split(":",1)]
                    eh,em=[int(x) for x in end_raw.split(":",1)]
                    start=datetime(day.year,day.month,day.day,sh,sm,tzinfo=vn_tz)
                    end=datetime(day.year,day.month,day.day,eh,em,tzinfo=vn_tz)
                except Exception:
                    flash(f"{d['label']}: giờ không hợp lệ.","error")
                    return _tournament_landing_return(tournament_id,"schedule")
                if end < start:
                    flash(f"{d['label']}: giờ Đến phải sau giờ Từ.","warning")
                    return _tournament_landing_return(tournament_id,"schedule")
                cursor=start.replace(second=0,microsecond=0); count=0
                while cursor<=end and count<49:
                    if cursor>now:
                        selected.append(cursor.isoformat())
                    cursor += timedelta(hours=1); count += 1
        key=f"c1_test_availability_{uid}" if is_test else f"admin_test_availability_{uid}"
        previous=_setting(tournament_id,key,{}) or {}
        custom_existing=[str(x) for x in (previous.get("slots") or []) if str(x) not in allowed]
        selected=sorted(set(selected+custom_existing))
        if is_test and not selected:
            flash("Hãy đăng ký ít nhất một giờ rảnh trong 3 ngày tới để vào giải đấu.","warning")
            return _tournament_landing_return(tournament_id,"schedule")
        execute_query(
            db.table("tournament_settings").upsert({
                "tournament_id":tournament_id,
                "setting_key":key,
                "setting_value":{"slots":selected,"updated_at":now_iso()},
                "updated_at":now_iso(),
            },on_conflict="tournament_id,setting_key"),
            "ops_admin_test_availability",attempts=2,
        )
        flash(f"Đã lưu lịch thi đấu: {len(selected)} mốc giờ trong 3 ngày gần nhất.","success")
        return _tournament_landing_return(tournament_id,"schedule")

    @app.post('/tournaments/<tournament_id>/availability/simple')
    @login_required
    def tournament_availability_simple_save(tournament_id):
        uid=(current_user() or {}).get("id")
        if not _member(tournament_id,uid):
            flash("Bạn chưa phải HLV của giải đấu này.","error"); return _tournament_landing_return(tournament_id,"schedule")
        vn_tz=timezone(timedelta(hours=7)); now=datetime.now(vn_tz)
        allowed_days={d["date"]:d for d in _availability_days()}
        final_slots=[]
        for idx,d in enumerate(_availability_days()):
            start_raw=(request.form.get(f"start_{idx}") or "").strip()
            end_raw=(request.form.get(f"end_{idx}") or "").strip()
            if not start_raw and not end_raw:
                continue
            if not start_raw or not end_raw:
                flash(f"{d['label']}: hãy chọn đủ giờ Từ và Đến.","warning"); return _tournament_landing_return(tournament_id,"schedule")
            try:
                day=datetime.fromisoformat(d["date"]).date()
                sh,sm=[int(x) for x in start_raw.split(":",1)]
                eh,em=[int(x) for x in end_raw.split(":",1)]
                start=datetime(day.year,day.month,day.day,sh,sm,tzinfo=vn_tz)
                end=datetime(day.year,day.month,day.day,eh,em,tzinfo=vn_tz)
            except Exception:
                flash(f"{d['label']}: giờ không hợp lệ.","error"); return _tournament_landing_return(tournament_id,"schedule")
            if end<start:
                flash(f"{d['label']}: giờ Đến phải sau giờ Từ.","warning"); return _tournament_landing_return(tournament_id,"schedule")
            cursor=start.replace(second=0,microsecond=0)
            count=0
            while cursor<=end and count<49:
                if cursor>now: final_slots.append(cursor.isoformat())
                cursor += timedelta(hours=1); count += 1
        final_slots=sorted(set(final_slots))
        if not final_slots:
            flash("Hãy đăng ký ít nhất một giờ rảnh trong 3 ngày tới để vào giải đấu.","warning")
            return _tournament_landing_return(tournament_id,"schedule")
        execute_query(db.table("tournament_availability_slots").delete().eq("tournament_id",tournament_id).eq("user_id",uid),"ops_availability_simple_clear",attempts=2)
        for iso in final_slots:
            execute_query(db.table("tournament_availability_slots").insert({"tournament_id":tournament_id,"user_id":uid,"slot_at":iso,"created_at":now_iso(),"updated_at":now_iso()}),"ops_availability_simple_insert",attempts=2)
        flash(f"Đã lưu lịch thi đấu: {len(final_slots)} mốc giờ trong 3 ngày gần nhất.","success")
        return _tournament_landing_return(tournament_id,"schedule")

    @app.post('/tournaments/<tournament_id>/availability/custom')
    @login_required
    def tournament_availability_custom_add(tournament_id):
        user=current_user() or {}
        uid=str(user.get("id") or "")
        member=_member(tournament_id,uid)
        is_test=_is_c1_test_user(tournament_id,uid)
        is_admin_view=is_admin_user(user) and not member
        if not member and not is_test and not is_admin_view:
            flash("Bạn chưa phải HLV của giải đấu này.","error"); return _tournament_landing_return(tournament_id,"schedule")
        day_raw=(request.form.get("day_date") or "").strip()
        start_raw=(request.form.get("start_time") or "").strip()
        end_raw=(request.form.get("end_time") or "").strip()
        vn_tz=timezone(timedelta(hours=7)); now=datetime.now(vn_tz)
        try:
            day=datetime.fromisoformat(day_raw).date()
            sh,sm=[int(x) for x in start_raw.split(":",1)]
            eh,em=[int(x) for x in end_raw.split(":",1)]
            start=datetime(day.year,day.month,day.day,sh,sm,tzinfo=vn_tz)
            end=datetime(day.year,day.month,day.day,eh,em,tzinfo=vn_tz)
        except Exception:
            flash("Giờ linh hoạt không hợp lệ.","error"); return _tournament_landing_return(tournament_id,"schedule")
        allowed_days={d["date"] for d in _availability_days()}
        if day.isoformat() not in allowed_days or end<=start:
            flash("Hãy chọn Hôm nay, Ngày mai hoặc Ngày kia và giờ kết thúc phải sau giờ bắt đầu.","warning"); return _tournament_landing_return(tournament_id,"schedule")
        # Bước 30 phút để hỗ trợ giờ linh hoạt, ví dụ 18:30–20:30.
        slots=[]; cursor=start.replace(second=0,microsecond=0)
        while cursor<=end and len(slots)<49:
            if cursor>now: slots.append(cursor.isoformat())
            cursor += timedelta(minutes=30)
        if not slots:
            flash("Khoảng giờ này đã qua hoặc không còn giờ hợp lệ.","warning"); return _tournament_landing_return(tournament_id,"schedule")
        if member:
            current={r.get("slot_iso") for r in _availability_rows(tournament_id,[uid])}
            added=0
            for iso in slots:
                if iso in current: continue
                execute_query(db.table("tournament_availability_slots").insert({"tournament_id":tournament_id,"user_id":uid,"slot_at":iso,"created_at":now_iso(),"updated_at":now_iso()}),"ops_availability_custom_insert",attempts=2)
                current.add(iso); added+=1
        else:
            key=f"c1_test_availability_{uid}" if is_test else f"admin_test_availability_{uid}"
            state=_setting(tournament_id,key,{}) or {}
            current={str(x) for x in (state.get("slots") or [])}
            before=len(current); current.update(slots); added=len(current)-before
            execute_query(db.table("tournament_settings").upsert({"tournament_id":tournament_id,"setting_key":key,"setting_value":{"slots":sorted(current),"updated_at":now_iso()},"updated_at":now_iso()},on_conflict="tournament_id,setting_key"),"ops_test_availability_custom",attempts=2)
        flash(f"Đã thêm giờ linh hoạt {start.strftime('%H:%M')}–{end.strftime('%H:%M')} ({added} mốc 30 phút).","success")
        return _tournament_landing_return(tournament_id,"schedule")

    @app.get('/api/tournaments/<tournament_id>/host-ready')
    @login_required
    def api_tournament_host_ready(tournament_id):
        # V1.5.75: endpoint chỉ đọc để Sảnh chờ cập nhật live cho HLV test/Admin/HLV thường.
        # Không phụ thuộc viewer có phải member hay không; danh sách nguồn luôn chỉ gồm
        # các HLV active thuộc chính giải đấu này.
        tournament=_tour(tournament_id)
        if not tournament:
            return jsonify({"ok":False,"error":"tournament_not_found"}),404
        rows=_host_ready_rows(tournament_id)
        return jsonify({"ok":True,"hosts":rows,"count":len(rows)})

    @app.post('/tournaments/<tournament_id>/host-ready')
    @login_required
    def tournament_host_ready_toggle(tournament_id):
        uid=str((current_user() or {}).get("id") or "")
        prof=next((x for x in _all_members(tournament_id) if str(x.get("user_id"))==uid),None)
        if not prof or not prof.get("has_host"):
            flash("Chỉ HLV đã đăng ký có Host mới dùng được mục này.","warning"); return redirect(url_for('tournaments')+"#rooms")
        state=_setting(tournament_id,"host_live_ready",{}) or {}
        ready=(request.form.get("ready") or "") in {"1","true","on","yes"}
        if ready: state[uid]=now_iso()
        else: state.pop(uid,None)
        execute_query(db.table("tournament_settings").upsert({"tournament_id":tournament_id,"setting_key":"host_live_ready","setting_value":state,"updated_at":now_iso()},on_conflict="tournament_id,setting_key"),"ops_host_live_ready",attempts=2)
        flash("Đã cập nhật trạng thái Host đang rảnh.","success")
        return redirect(url_for('tournaments')+"#rooms")

    @app.post('/tournaments/matches/<match_id>/schedule-from-availability')
    @login_required
    def tournament_schedule_from_availability(match_id):
        uid=(current_user() or {}).get("id")
        match,_=_one(db.table("tournament_matches").select("*").eq("id",match_id),"ops_availability_match")
        if not match or str(uid) not in {str(match.get("home_user_id")),str(match.get("away_user_id"))}:
            flash("Bạn không thuộc trận này.","error"); return redirect(url_for("tournaments"))
        slot=(request.form.get("slot_at") or "").strip()
        if not slot:
            flash("Hãy chọn một khung giờ trùng.","error"); return redirect(url_for('tournaments') + "#schedule")
        rows=_availability_rows(match.get("tournament_id"),[match.get("home_user_id"),match.get("away_user_id")])
        users_at={str(r.get("user_id")) for r in rows if r.get("slot_iso")==slot}
        required={str(match.get("home_user_id")),str(match.get("away_user_id"))}
        if not required.issubset(users_at):
            flash("Khung giờ này không còn trùng lịch của cả hai HLV. Hãy tải lại lịch.","warning")
            return redirect(url_for('tournaments') + "#schedule")
        execute_query(db.table("tournament_matches").update({"scheduled_at":slot,"status":"scheduled","updated_at":now_iso()}).eq("id",match_id),"ops_availability_schedule",attempts=2)
        flash("Đã chốt lịch vì cả hai HLV đều đánh dấu rảnh ở khung giờ này.","success")
        return redirect(url_for('tournaments') + "#schedule")

    @app.post('/tournaments/matches/<match_id>/schedule')
    @login_required
    def tournament_match_schedule(match_id):
        uid=(current_user() or {}).get("id")
        match,_=_one(db.table("tournament_matches").select("*").eq("id",match_id),"ops_schedule_match")
        if not match or str(uid) not in {str(match.get("home_user_id")),str(match.get("away_user_id"))}:
            flash("Bạn không thuộc trận này.","error"); return redirect(url_for("tournaments"))
        if match.get("status") in {"completed","playing","cancelled"}:
            flash("Trận này không thể hẹn lịch ở trạng thái hiện tại.","warning")
            return redirect(url_for('tournaments') + "#schedule")
        proposed=(request.form.get("scheduled_at") or "").strip(); host_id=(request.form.get("host_id") or "").strip() or None
        if not proposed:
            flash("Hãy chọn ngày và giờ thi đấu.","error"); return redirect(url_for('tournaments') + "#schedule")
        try:
            # datetime-local is entered in Vietnam local time; save an explicit +07:00 offset for timestamptz.
            vn_tz=timezone(timedelta(hours=7))
            parsed=datetime.fromisoformat(proposed).replace(tzinfo=vn_tz)
            if parsed <= datetime.now(vn_tz):
                flash("Thời gian đề xuất phải ở tương lai.","error")
                return redirect(url_for('tournaments') + "#schedule")
        except ValueError:
            flash("Thời gian đề xuất không hợp lệ.","error")
            return redirect(url_for('tournaments') + "#schedule")

        # A new proposal supersedes every previous pending proposal for this match.
        try:
            execute_query(
                db.table("tournament_schedule_requests").update({"status":"cancelled","responded_at":now_iso()})
                .eq("match_id",match_id).eq("status","pending"),
                "ops_schedule_cancel_old",attempts=2,
            )
        except Exception as exc:
            app.logger.warning("Cancel previous schedule proposal failed: %s", exc)
        proposed_iso=parsed.isoformat()
        execute_query(db.table("tournament_schedule_requests").insert({
            "tournament_id":match.get("tournament_id"),"match_id":match_id,"proposed_by":uid,
            "proposed_at":proposed_iso,"host_id":host_id,"status":"pending","created_at":now_iso()
        }),"ops_schedule_propose",attempts=2)
        if match.get("status")=="scheduled":
            execute_query(db.table("tournament_matches").update({"status":"pending","scheduled_at":None,"host_id":None,"updated_at":now_iso()}).eq("id",match_id),"ops_schedule_reopen",attempts=2)
        flash("Đã gửi đề xuất giờ. Đang chờ đối thủ xác nhận.","success")
        return redirect(url_for('tournaments') + "#schedule")

    @app.post('/tournaments/schedules/<schedule_id>/accept')
    @login_required
    def tournament_schedule_accept(schedule_id):
        uid=(current_user() or {}).get("id")
        sched,_=_one(db.table("tournament_schedule_requests").select("*").eq("id",schedule_id),"ops_sched_lookup")
        if not sched: flash("Không tìm thấy đề xuất lịch.","error"); return redirect(url_for("tournaments"))
        match,_=_one(db.table("tournament_matches").select("*").eq("id",sched.get("match_id")),"ops_sched_match")
        if not match or str(uid) not in {str(match.get("home_user_id")),str(match.get("away_user_id"))} or str(uid)==str(sched.get("proposed_by")):
            flash("Bạn không thể xác nhận lịch này.","error"); return redirect(url_for('tournaments') + "#schedule")
        if sched.get("status")!="pending":
            flash("Đề xuất này không còn chờ xác nhận.","warning"); return redirect(url_for('tournaments') + "#schedule")
        execute_query(db.table("tournament_schedule_requests").update({"status":"accepted","responded_by":uid,"responded_at":now_iso()}).eq("id",schedule_id),"ops_sched_accept",attempts=2)
        execute_query(db.table("tournament_matches").update({"scheduled_at":sched.get("proposed_at"),"host_id":sched.get("host_id"),"status":"scheduled","updated_at":now_iso()}).eq("id",sched.get("match_id")),"ops_match_schedule",attempts=2)
        # Close any other pending proposal for this match.
        try:
            execute_query(db.table("tournament_schedule_requests").update({"status":"cancelled","responded_at":now_iso()}).eq("match_id",sched.get("match_id")).eq("status","pending"),"ops_sched_close_others",attempts=2)
        except Exception:
            pass
        flash("Hai HLV đã thống nhất. Lịch thi đấu đã được chốt.","success")
        return redirect(url_for('tournaments') + "#schedule")

    @app.post('/tournaments/schedules/<schedule_id>/reject')
    @login_required
    def tournament_schedule_reject(schedule_id):
        uid=(current_user() or {}).get("id")
        sched,_=_one(db.table("tournament_schedule_requests").select("*").eq("id",schedule_id),"ops_sched_reject_lookup")
        if not sched:
            flash("Không tìm thấy đề xuất lịch.","error"); return redirect(url_for("tournaments"))
        match,_=_one(db.table("tournament_matches").select("*").eq("id",sched.get("match_id")),"ops_sched_reject_match")
        if not match or str(uid) not in {str(match.get("home_user_id")),str(match.get("away_user_id"))} or str(uid)==str(sched.get("proposed_by")):
            flash("Bạn không thể từ chối lịch này.","error"); return redirect(url_for('tournaments') + "#schedule")
        if sched.get("status")!="pending":
            flash("Đề xuất này không còn chờ xác nhận.","warning"); return redirect(url_for('tournaments') + "#schedule")
        execute_query(db.table("tournament_schedule_requests").update({
            "status":"rejected","responded_by":uid,"responded_at":now_iso(),
            "note":(request.form.get("note") or "").strip()[:250] or None
        }).eq("id",schedule_id),"ops_sched_reject",attempts=2)
        flash("Đã từ chối đề xuất. Bạn có thể chọn giờ khác và gửi đề xuất lại.","success")
        return redirect(url_for('tournaments') + "#schedule")

    @app.post('/admin/tournaments/<tournament_id>/hosts/add')
    @login_required
    @admin_required
    def admin_tournament_host_add(tournament_id):
        name=(request.form.get("name") or "").strip(); region=(request.form.get("region") or "Bắc").strip()
        if name:
            execute_query(db.table("tournament_hosts").insert({"tournament_id":tournament_id,"name":name,"region":region,"status":"available","note":request.form.get("note") or None,"created_at":now_iso()}),"ops_host_add",attempts=2)
        flash("Đã thêm host.","success"); return redirect_admin("tournaments")

    @app.post('/admin/tournaments/hosts/<host_id>/status')
    @login_required
    @admin_required
    def admin_tournament_host_status(host_id):
        status=request.form.get("status") or "available"
        if status not in {"available","busy","offline"}: status="offline"
        execute_query(db.table("tournament_hosts").update({"status":status,"updated_at":now_iso()}).eq("id",host_id),"ops_host_status",attempts=2)
        flash("Đã cập nhật Host.","success"); return redirect_admin("tournaments")

    @app.post('/admin/tournaments/<tournament_id>/stage1/extend')
    @login_required
    @admin_required
    def admin_tournament_stage1_extend(tournament_id):
        cfg=_setting(tournament_id,"competition_timing",{}) or {}
        base=_parse_iso(cfg.get("stage1_end_at")) or datetime.now(timezone(timedelta(hours=7)))
        if base.tzinfo is None: base=base.replace(tzinfo=timezone(timedelta(hours=7)))
        cfg["stage1_extension_end_at"]=(max(base,datetime.now(base.tzinfo))+timedelta(days=2)).isoformat()
        execute_query(db.table("tournament_settings").upsert({"tournament_id":tournament_id,"setting_key":"competition_timing","setting_value":cfg,"updated_at":now_iso()},on_conflict="tournament_id,setting_key"),"ops_s1_extend",attempts=2)
        flash("Đã gia hạn GĐ1 thêm 2 ngày.","success"); return redirect_admin("tournaments")

    return {k: v for k, v in locals().items() if k.startswith('_') and callable(v)}
