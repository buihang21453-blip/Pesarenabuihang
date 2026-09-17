"""Internal tournament competition partition extracted from the legacy monolith.

Registered only through :mod:`modules.tournament_competition`.
"""

def register_core(context):
    globals().update(context)

    def _stage1_eligible_clubs(force=False):
        """Toàn bộ CLB active Tier S+/S từ nguồn teams thật trên Supabase."""
        rows=[]
        try:
            rows=[dict(x) for x in _load_teams_from_supabase(force=force)]
        except Exception as exc:
            app.logger.warning("Không đọc được teams Supabase cho GĐ1, dùng fallback cũ: %s", exc)
            rows=[dict(x) for x in TEAMS]
        out=[]
        seen=set()
        for x in rows:
            tier=str(x.get("tier") or "").strip().upper()
            name=(x.get("display") or x.get("team") or x.get("name") or "").strip()
            if tier not in STAGE1_ALLOWED_TIERS or not name or name.casefold() in seen:
                continue
            seen.add(name.casefold())
            out.append({
                "display":name,
                "team":name,
                "overall":int(x.get("overall") or 0),
                "tier":tier,
                "league":x.get("league") or "",
                "logo_url":x.get("logo_url") or "",
            })
        out.sort(key=lambda x: (0 if x["tier"]=="S+" else 1, -int(x.get("overall") or 0), x["display"].casefold()))
        return out

    def _default_stage1_clubs():
        # C1 Arena dùng đúng tối đa 16 CLB Tier S+/S mạnh nhất từ nguồn teams thật.
        return [dict(x) for x in _stage1_eligible_clubs()[:16]]

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
        profiles = {}
        if ids:
            urows, _ = _rows(db.table("users").select("id,username,display_name,avatar_url,is_online,last_seen_at").in_("id", ids), "ops_member_users")
            users = {str(u.get("id")):u for u in urows}
            rrows, _ = _rows(db.table("tournament_registrations").select("id,user_id,zalo_name,has_host,host_region,payment_status,status,registered_at,amount_paid,fee_amount,responsibility_amount,responsibility_deducted,amount_refunded,payment_note").eq("tournament_id", tournament_id).in_("user_id", ids), "ops_member_registration_profiles")
            profiles = {str(x.get("user_id")):x for x in rrows if x.get("user_id")}
        for r in rows:
            uid=str(r.get("user_id"))
            u=users.get(uid) or {}
            prof=profiles.get(uid) or {}
            r["display_name"] = u.get("display_name") or u.get("username") or "HLV"
            r["user"] = u
            r["zalo_name"] = prof.get("zalo_name") or r.get("zalo_name") or ""
            r["has_host"] = bool(prof.get("has_host"))
            r["host_region"] = prof.get("host_region") or "—"
            r["payment_status"] = prof.get("payment_status") or "—"
            r["registered_at"] = prof.get("registered_at")
            r["registration_id"] = prof.get("id")
            paid = int(prof.get("amount_paid") or 0)
            fee_amount = int(prof.get("fee_amount") or 50000)
            responsibility_amount = int(prof.get("responsibility_amount") or 50000)
            refunded = int(prof.get("amount_refunded") or 0)
            r["amount_paid"] = paid
            r["fee_amount"] = fee_amount
            r["responsibility_amount"] = responsibility_amount
            r["responsibility_deducted"] = int(prof.get("responsibility_deducted") or 0)
            r["amount_refunded"] = refunded
            r["payment_note"] = prof.get("payment_note") or ""
            required = fee_amount + responsibility_amount
            r["required_amount"] = required
            r["amount_missing"] = max(0, required - paid)
            r["amount_surplus"] = max(0, paid - required - refunded)
        return rows

    def _matches(tournament_id, stage_code=None, statuses=None):
        q=db.table("tournament_matches").select("*").eq("tournament_id", tournament_id)
        if stage_code:
            q=q.eq("stage_code", stage_code)
        if statuses:
            q=q.in_("status", statuses)
        rows,_=_rows(q.order("created_at"), "ops_matches")
        return rows


    def _pair_matches(tournament_id, match, include_cancelled=False):
        """Các trận của đúng cặp HLV trong cùng giai đoạn. Không giả định số lượt."""
        if not match:
            return []
        stage_code=str(match.get("stage_code") or "")
        pair_ids={str(match.get("home_user_id") or ""), str(match.get("away_user_id") or "")}
        rows=[]
        for row in _matches(tournament_id, stage_code or None):
            if {str(row.get("home_user_id") or ""), str(row.get("away_user_id") or "")} != pair_ids:
                continue
            if not include_cancelled and str(row.get("status") or "").lower()=="cancelled":
                continue
            rows.append(row)
        return sorted(rows, key=lambda r:(int(r.get("leg_no") or 999), str(r.get("created_at") or ""), str(r.get("id") or "")))

    def _pair_flow_state(tournament_id, match):
        """Trạng thái cặp đấu theo luật thật, kể cả lịch cũ bị thiếu row leg 2."""
        rows=_pair_matches(tournament_id, match)
        completed=[r for r in rows if str(r.get("status") or "").lower()=="completed"]
        remaining=[r for r in rows if str(r.get("status") or "").lower() not in {"completed","cancelled"}]
        current_id=str((match or {}).get("id") or "")
        next_match=next((r for r in remaining if str(r.get("id") or "") != current_id), None)
        expected_count=len(rows)
        if str((match or {}).get("stage_code") or "")=="stage1":
            expected_count=max(2,len(rows))
            try:
                st=_stage(tournament_id,"stage1") or {}
                configured=int(st.get("max_matches_per_opponent") or 0)
                if configured>0:
                    expected_count=max(2,configured,len(rows))
            except Exception:
                expected_count=max(2,len(rows))
        missing=max(0,expected_count-len(rows))
        return {
            "matches":rows,
            "total_count":expected_count,
            "actual_count":len(rows),
            "missing_count":missing,
            "completed_count":len(completed),
            "remaining_count":len(remaining)+missing,
            "next_match":next_match,
            "has_next":bool(next_match) or missing>0,
            "is_complete":len(completed)>=expected_count and not remaining and missing==0,
        }

    def _stage1_pair_completed_count(tournament_id, user_a, user_b, exclude_match_id=None):
        """Số trận GĐ1 đã hoàn thành giữa đúng 2 HLV, bất kể ai là chủ/khách."""
        a=str(user_a or ""); b=str(user_b or "")
        count=0
        for row in _matches(tournament_id, "stage1"):
            if exclude_match_id and str(row.get("id"))==str(exclude_match_id):
                continue
            if str(row.get("status") or "")!="completed":
                continue
            h=str(row.get("home_user_id") or ""); aw=str(row.get("away_user_id") or "")
            if {h,aw}=={a,b}:
                count+=1
        return count

    def _stage1_pair_is_complete(tournament_id, match, exclude_current=False):
        if not match or str(match.get("stage_code") or "")!="stage1":
            return False
        return _stage1_pair_completed_count(
            tournament_id,
            match.get("home_user_id"),
            match.get("away_user_id"),
            match.get("id") if exclude_current else None,
        ) >= 2

    def _ranking(tournament_id, stage_code):
        members=_all_members(tournament_id)
        table={str(m["user_id"]):{
            "user_id":str(m["user_id"]),"display_name":m["display_name"],"played":0,"wins":0,"draws":0,"losses":0,
            "gf":0,"ga":0,"gd":0,"points":0,"opponents":set(),"pot_no":m.get("pot_no"),"seed_no":m.get("seed_no"),
            "club":m.get("fixed_club_name") or "", "zalo_name":m.get("zalo_name") or ""
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
            home_member=members.get(str(m.get("home_user_id"))) or {}
            away_member=members.get(str(m.get("away_user_id"))) or {}
            m["home_name"]=home_member.get("display_name","HLV")
            m["away_name"]=away_member.get("display_name","HLV")
            m["home_zalo_name"]=home_member.get("zalo_name") or ""
            m["away_zalo_name"]=away_member.get("zalo_name") or ""
            m["host"] = hostmap.get(str(m.get("host_id")))
        return rows

    def _attach_schedule_state(tournament_id, matches, viewer_id=None):
        """Attach latest schedule request + player contact/host profile to each match."""
        reqs,_=_rows(
            db.table("tournament_schedule_requests").select("*")
            .eq("tournament_id",tournament_id).order("created_at", desc=True),
            "ops_schedule_requests",
        )
        latest={}
        for r in reqs:
            mid=str(r.get("match_id"))
            if mid not in latest and r.get("status") in {"pending","accepted","rejected","cancelled","disputed"}:
                latest[mid]=r

        # Registration data is the source of Host / region information collected at signup.
        regs,_=_rows(
            db.table("tournament_registrations").select("user_id,has_host,host_region,status")
            .eq("tournament_id",tournament_id),
            "ops_schedule_registration_profiles",
        )
        profiles={str(r.get("user_id")):r for r in regs if r.get("user_id")}
        member_map={str(m.get("user_id")):m for m in _all_members(tournament_id)}
        host_rows,_=_rows(db.table("tournament_hosts").select("*").eq("tournament_id",tournament_id),"ops_schedule_hosts")
        host_map={str(h.get("id")):h for h in host_rows}

        for m in matches:
            req=latest.get(str(m.get("id")))
            m["schedule_request"]=req
            if req:
                m["schedule_request_host"]=host_map.get(str(req.get("host_id")))
                proposer=member_map.get(str(req.get("proposed_by"))) or {}
                m["schedule_proposer_name"]=proposer.get("display_name") or "HLV"
                m["schedule_is_mine"]=str(req.get("proposed_by"))==str(viewer_id)
                m["schedule_can_accept"]=(
                    req.get("status")=="pending" and str(viewer_id) in {str(m.get("home_user_id")),str(m.get("away_user_id"))}
                    and str(req.get("proposed_by"))!=str(viewer_id)
                )
            for side in ("home","away"):
                uid=str(m.get(f"{side}_user_id"))
                prof=profiles.get(uid) or {}
                m[f"{side}_has_host"]=bool(prof.get("has_host"))
                m[f"{side}_host_region"]=prof.get("host_region") or "—"
        return matches

    def _availability_days():
        """Three rolling Vietnam-local calendar days: today, tomorrow, day after tomorrow."""
        vn_tz=timezone(timedelta(hours=7))
        today=datetime.now(vn_tz).date()
        labels=("Hôm nay","Ngày mai","Ngày kia")
        days=[]
        for offset,label in enumerate(labels):
            d=today+timedelta(days=offset)
            # Weekdays use the official tournament window in 1-hour slots.
            # Weekend is flexible, so expose a simple daytime/evening hourly range.
            hours=[11,12,18,19,20,21] if d.weekday()<5 else list(range(11,22))
            slots=[]
            for hour in hours:
                dt=datetime(d.year,d.month,d.day,hour,0,tzinfo=vn_tz)
                if dt>datetime.now(vn_tz):
                    slots.append({
                        "iso":dt.isoformat(),
                        "time":f"{hour:02d}:00",
                        "end_time":f"{hour+1:02d}:00",
                        "label":f"{hour:02d}:00 – {hour+1:02d}:00",
                    })
            weekday_names=("Thứ Hai","Thứ Ba","Thứ Tư","Thứ Năm","Thứ Sáu","Thứ Bảy","Chủ nhật")
            days.append({"date":d.isoformat(),"label":label,"weekday":f"{weekday_names[d.weekday()]} · {d.strftime('%d/%m')}","is_weekend":d.weekday()>=5,"slots":slots})
        return days

    def _availability_rows(tournament_id, user_ids=None):
        q=db.table("tournament_availability_slots").select("*").eq("tournament_id",tournament_id)
        if user_ids:
            q=q.in_("user_id",[str(x) for x in user_ids])
        rows,err=_rows(q.order("slot_at"),"ops_availability")
        if err:
            return []
        vn_tz=timezone(timedelta(hours=7)); now=datetime.now(vn_tz)
        max_day=(now.date()+timedelta(days=2))
        out=[]
        for r in rows:
            try:
                dt=datetime.fromisoformat(str(r.get("slot_at")).replace("Z","+00:00")).astimezone(vn_tz)
                if now < dt and now.date() <= dt.date() <= max_day:
                    r["slot_iso"]=dt.isoformat(); r["slot_label"]=dt.strftime("%d/%m · %H:%M"); out.append(r)
            except Exception:
                continue
        return out

    def _has_upcoming_scheduled_match_3day(user_id, matches):
        """True when this HLV already has a scheduled tournament match in the rolling 3 VN days."""
        vn_tz=timezone(timedelta(hours=7))
        now=datetime.now(vn_tz)
        last_day=now.date()+timedelta(days=2)
        uid=str(user_id or "")
        for m in (matches or []):
            if uid not in {str(m.get("home_user_id") or ""),str(m.get("away_user_id") or "")}:
                continue
            if str(m.get("status") or "") not in {"pending","scheduled"}:
                continue
            raw=m.get("scheduled_at")
            if not raw:
                continue
            try:
                dt=datetime.fromisoformat(str(raw).replace("Z","+00:00"))
                if dt.tzinfo is None:
                    dt=dt.replace(tzinfo=vn_tz)
                dt_vn=dt.astimezone(vn_tz)
            except Exception:
                continue
            if dt_vn>=now and dt_vn.date()<=last_day:
                return True
        return False

    def _group_opponent_availability(raw_items, mine_set):
        """Group an opponent's availability into the official rolling 3-day columns.

        Each returned slot also carries ``is_overlap`` so the template can highlight
        the hours where both coaches are free without changing any scheduling data.
        """
        vn_tz=timezone(timedelta(hours=7))
        days=_availability_days()
        grouped={d["date"]:[] for d in days}
        mine_set=set(mine_set or [])
        for item in (raw_items or []):
            iso=(item or {}).get("slot_iso") or (item or {}).get("iso")
            if not iso:
                continue
            try:
                dt=datetime.fromisoformat(str(iso).replace("Z","+00:00"))
                if dt.tzinfo is None:
                    dt=dt.replace(tzinfo=vn_tz)
                dt=dt.astimezone(vn_tz)
            except Exception:
                continue
            day_key=dt.date().isoformat()
            if day_key not in grouped:
                continue
            end=dt+timedelta(hours=1)
            grouped[day_key].append({
                "iso":iso,
                "label":f"{dt.strftime('%H:%M')} – {end.strftime('%H:%M')}",
                "is_overlap":iso in mine_set,
            })
        out=[]
        for d in days:
            row=dict(d)
            row["opponent_slots"]=sorted(grouped.get(d["date"],[]), key=lambda x:x["iso"])
            out.append(row)
        return out

    def _availability_payload(tournament_id,user_id,matches):
        ids={str(user_id)}
        for m in matches:
            if str(user_id) in {str(m.get("home_user_id")),str(m.get("away_user_id"))}:
                ids.add(str(m.get("home_user_id"))); ids.add(str(m.get("away_user_id")))
        rows=_availability_rows(tournament_id,list(ids))
        by_user={}
        for r in rows: by_user.setdefault(str(r.get("user_id")),[]).append(r)
        mine=by_user.get(str(user_id),[])
        mine_set={x.get("slot_iso") for x in mine}
        for m in matches:
            if str(user_id) not in {str(m.get("home_user_id")),str(m.get("away_user_id"))}: continue
            opp=str(m.get("away_user_id")) if str(m.get("home_user_id"))==str(user_id) else str(m.get("home_user_id"))
            opp_rows=by_user.get(opp,[]); opp_set={x.get("slot_iso") for x in opp_rows}
            overlap=sorted(mine_set & opp_set)
            m["opponent_availability"]=opp_rows
            m["availability_overlap"]=[{"iso":x,"label":datetime.fromisoformat(x).strftime("%d/%m · %H:%M")} for x in overlap]
            m["opponent_availability_days"]=_group_opponent_availability(opp_rows,mine_set)
        vn_tz=timezone(timedelta(hours=7)); today=datetime.now(vn_tz).date()
        slot_dates=[]
        for x in mine_set:
            try: slot_dates.append(datetime.fromisoformat(x).astimezone(vn_tz).date())
            except Exception: pass
        if not slot_dates:
            status="missing"
        elif max(slot_dates) <= today:
            status="expiring"
        else:
            status="active"
        days=_availability_days()
        day_ranges={}
        day_chips={}
        for d in days:
            vals=[]
            for r in mine:
                try:
                    dt=datetime.fromisoformat(str(r.get("slot_iso"))).astimezone(vn_tz)
                except Exception:
                    continue
                if dt.date().isoformat()==d["date"]:
                    vals.append(dt)
            vals=sorted(vals)
            if vals:
                day_ranges[d["date"]]={"start":vals[0].strftime("%H:%M"),"end":vals[-1].strftime("%H:%M")}
                day_chips[d["date"]]=[x.strftime("%H:%M") for x in vals]
            else:
                day_ranges[d["date"]]={"start":"","end":""}
                day_chips[d["date"]]=[]
        return {"days":days,"mine":mine,"mine_set":mine_set,"status":status,"slot_count":len(mine_set),"day_ranges":day_ranges,"day_chips":day_chips}

    def _admin_all_availability_payload(tournament_id, matches=None):
        """Admin xem lịch rảnh của toàn bộ HLV thật trong 3 ngày tới."""
        members=_all_members(tournament_id)
        ids=[str(x.get("user_id") or "") for x in members if x.get("user_id")]
        rows=_availability_rows(tournament_id,ids) if ids else []
        by_user={}
        for row in rows:
            by_user.setdefault(str(row.get("user_id") or ""),[]).append(row)

        days=_availability_days()
        day_dates=[d.get("date") for d in days]
        vn_tz=timezone(timedelta(hours=7))
        all_matches=list(matches or _matches(tournament_id))
        result=[]

        for mem in members:
            uid=str(mem.get("user_id") or "")
            slots=sorted(by_user.get(uid,[]),key=lambda x:str(x.get("slot_iso") or ""))
            grouped={d:[] for d in day_dates}
            for row in slots:
                try:
                    dt=datetime.fromisoformat(str(row.get("slot_iso") or "")).astimezone(vn_tz)
                except Exception:
                    continue
                dkey=dt.date().isoformat()
                if dkey in grouped:
                    grouped[dkey].append({
                        "iso":row.get("slot_iso"),
                        "time":dt.strftime("%H:%M"),
                        "label":dt.strftime("%H:%M"),
                    })

            own_matches=[
                mt for mt in all_matches
                if uid in {str(mt.get("home_user_id") or ""),str(mt.get("away_user_id") or "")}
            ]
            has_schedule=_has_upcoming_scheduled_match_3day(uid,own_matches)
            scheduled=[]
            for mt in own_matches:
                if str(mt.get("status") or "") not in {"pending","scheduled"} or not mt.get("scheduled_at"):
                    continue
                try:
                    dt=datetime.fromisoformat(str(mt.get("scheduled_at")).replace("Z","+00:00"))
                    if dt.tzinfo is None:
                        dt=dt.replace(tzinfo=vn_tz)
                    dt=dt.astimezone(vn_tz)
                except Exception:
                    continue
                now=datetime.now(vn_tz)
                if dt < now or dt.date() > now.date()+timedelta(days=2):
                    continue
                opponent_uid=(
                    str(mt.get("away_user_id") or "")
                    if uid==str(mt.get("home_user_id") or "")
                    else str(mt.get("home_user_id") or "")
                )
                opponent=next((x for x in members if str(x.get("user_id") or "")==opponent_uid),{})
                scheduled.append({
                    "at":dt.isoformat(),
                    "label":dt.strftime("%d/%m · %H:%M"),
                    "opponent_name":opponent.get("display_name") or "HLV",
                })

            if has_schedule:
                status="scheduled"
                status_label="📅 Đã có lịch · Không cần khai"
            elif slots:
                status="registered"
                status_label="✅ Đã đăng ký giờ rảnh"
            else:
                status="missing"
                status_label="🔴 Chưa đăng ký"

            result.append({
                "user_id":uid,
                "display_name":mem.get("display_name") or "HLV",
                "zalo_name":mem.get("zalo_name") or "",
                "has_host":bool(mem.get("has_host")),
                "host_region":mem.get("host_region") or "",
                "status":status,
                "status_label":status_label,
                "slot_count":len(slots),
                "slots_by_day":grouped,
                "scheduled":scheduled,
            })

        status_order={"missing":0,"registered":1,"scheduled":2}
        result.sort(key=lambda x:(status_order.get(x.get("status"),9),(x.get("display_name") or "").lower()))
        return {
            "days":days,
            "rows":result,
            "missing_count":sum(1 for x in result if x.get("status")=="missing"),
            "registered_count":sum(1 for x in result if x.get("status")=="registered"),
            "scheduled_count":sum(1 for x in result if x.get("status")=="scheduled"),
            "total":len(result),
        }

    def _c1_test_availability_slots(tournament_id,user_id):
        state=_setting(tournament_id,f"c1_test_availability_{str(user_id)}",{}) or {}
        allowed={slot["iso"] for day in _availability_days() for slot in day["slots"]}
        raw=list(state.get("slots") or [])
        # Migration from the previous Test C1 range format: convert only to official
        # one-hour slots, so old sandbox data remains useful after this update.
        if not raw and state.get("ranges"):
            vn_tz=timezone(timedelta(hours=7))
            for day in _availability_days():
                r=(state.get("ranges") or {}).get(day["date"],{}) or {}
                start=str(r.get("start") or ""); end=str(r.get("end") or "")
                if not start or not end:
                    continue
                try:
                    sh,sm=[int(x) for x in start.split(":",1)]; eh,em=[int(x) for x in end.split(":",1)]
                    d=datetime.fromisoformat(day["date"]).date()
                    start_dt=datetime(d.year,d.month,d.day,sh,sm,tzinfo=vn_tz)
                    end_dt=datetime(d.year,d.month,d.day,eh,em,tzinfo=vn_tz)
                    for slot in day["slots"]:
                        dt=datetime.fromisoformat(slot["iso"])
                        if start_dt <= dt < end_dt:
                            raw.append(slot["iso"])
                except Exception:
                    continue
        return sorted({str(x) for x in raw if str(x) in allowed})

    def _c1_test_availability_payload(tournament_id,user_id):
        uid=str(user_id or "")
        days=_availability_days()
        mine=_c1_test_availability_slots(tournament_id,uid)
        mine_set=set(mine)
        test_users=_c1_test_users(tournament_id)
        opponent=next((u for u in test_users if str(u.get("id"))!=uid),None)
        opp_uid=str((opponent or {}).get("id") or "")
        opp_slots=_c1_test_availability_slots(tournament_id,opp_uid) if opp_uid else []
        opp_set=set(opp_slots)
        overlap=sorted(mine_set & opp_set)
        slot_lookup={slot["iso"]:slot for day in days for slot in day["slots"]}
        def decorated(values):
            out=[]
            for iso in values:
                try:
                    dt=datetime.fromisoformat(iso)
                    slot=slot_lookup.get(iso) or {}
                    out.append({"iso":iso,"label":f"{dt.strftime('%d/%m')} · {slot.get('label') or dt.strftime('%H:%M')}"})
                except Exception:
                    continue
            return out
        vn_tz=timezone(timedelta(hours=7)); today=datetime.now(vn_tz).date()
        dates=[]
        for iso in mine:
            try: dates.append(datetime.fromisoformat(iso).astimezone(vn_tz).date())
            except Exception: pass
        status="missing" if not dates else ("expiring" if max(dates)<=today else "active")
        decorated_opp=decorated(opp_slots)
        return {
            "days":days,"mine":decorated(mine),"mine_set":mine_set,"status":status,"slot_count":len(mine_set),
            "opponent":opponent,"opponent_slots":decorated_opp,"overlap":decorated(overlap),
            "opponent_days":_group_opponent_availability(decorated_opp,mine_set),
            "day_ranges":{},"day_chips":{},
        }

    def _parse_iso(value):
        if not value:
            return None
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except Exception:
            return None

    def _countdown_info(value):
        target=_parse_iso(value)
        if not target:
            return {"target":None,"remaining":0,"days":0,"hours":0,"minutes":0,"seconds":0,"expired":False}
        if target.tzinfo is None:
            target=target.replace(tzinfo=timezone(timedelta(hours=7)))
        now=datetime.now(target.tzinfo)
        sec=max(0,int((target-now).total_seconds()))
        return {"target":target.isoformat(),"remaining":sec,"days":sec//86400,"hours":(sec%86400)//3600,"minutes":(sec%3600)//60,"seconds":sec%60,"expired":sec<=0}

    def _vn_datetime_text(value, with_seconds=True):
        """Hiển thị timestamp theo giờ Việt Nam cho Admin C1."""
        dt=_parse_iso(value) if not isinstance(value, datetime) else value
        if not dt:
            return ""
        if dt.tzinfo is None:
            dt=dt.replace(tzinfo=timezone.utc)
        vn=dt.astimezone(timezone(timedelta(hours=7)))
        return vn.strftime("%d/%m/%Y · %H:%M:%S" if with_seconds else "%d/%m/%Y · %H:%M")

    def _stage1_confirmation_audit(tournament_id):
        """
        Audit toàn bộ trận GĐ1 đã completed:
        - completed_at là thời điểm kết quả chính thức được chốt.
        - proposal.confirmed_at/confirmed_by cho biết ai bấm xác nhận.
        - Với Admin chốt tranh chấp, proposal có status=admin_confirmed.
        """
        members=_all_members(tournament_id)
        names={str(x.get("user_id") or ""):(x.get("display_name") or "HLV") for x in members}
        rows=[]
        for match in _matches(tournament_id,"stage1",["completed"]):
            mid=str(match.get("id") or "")
            h=str(match.get("home_user_id") or ""); aw=str(match.get("away_user_id") or "")
            proposal=_tournament_result_proposal(tournament_id,mid)
            confirmed_at=proposal.get("confirmed_at") or match.get("completed_at") or match.get("updated_at")
            confirmed_by=str(proposal.get("confirmed_by") or "")
            proposal_status=str(proposal.get("status") or "")
            if confirmed_by=="admin" or proposal_status=="admin_confirmed":
                confirmer_name="🛡️ Admin"
            elif confirmed_by:
                confirmer_name=names.get(confirmed_by,"HLV")
            else:
                confirmer_name="Hệ thống/Admin"
            rows.append({
                "match_id":mid,
                "round_code":match.get("round_code") or "",
                "leg_no":int(match.get("leg_no") or 1),
                "home_user_id":h,
                "away_user_id":aw,
                "home_name":names.get(h,"HLV"),
                "away_name":names.get(aw,"HLV"),
                "home_score":match.get("home_score"),
                "away_score":match.get("away_score"),
                "completed_at":match.get("completed_at") or match.get("updated_at"),
                "confirmed_at":confirmed_at,
                "confirmed_at_dt":_parse_iso(confirmed_at),
                "confirmed_at_vn":_vn_datetime_text(confirmed_at),
                "confirmed_by":confirmed_by,
                "confirmed_by_name":confirmer_name,
                "proposal_status":proposal_status,
            })
        rows.sort(key=lambda x:(x.get("confirmed_at_dt") or datetime.max.replace(tzinfo=timezone.utc), x.get("match_id") or ""))
        return rows

    def _completion_ranking(tournament_id):
        stage=_stage(tournament_id,"stage1") or {}
        target=int(stage.get("match_target") or 6)
        min_opp=int(stage.get("min_opponents") or 3)
        cutoff=_parse_iso((_setting(tournament_id,"competition_timing",{}) or {}).get("stage1_early_end_at"))
        members=_all_members(tournament_id)

        by={
            str(mem.get("user_id")):{
                "user_id":str(mem.get("user_id")),
                "display_name":mem.get("display_name") or "HLV",
                "matches":[],
            }
            for mem in members
        }

        # Duyệt đúng theo thời điểm kết quả được chốt để tìm "trận cán mốc".
        for audit in _stage1_confirmation_audit(tournament_id):
            for uid,opp in (
                (str(audit.get("home_user_id") or ""),str(audit.get("away_user_id") or "")),
                (str(audit.get("away_user_id") or ""),str(audit.get("home_user_id") or "")),
            ):
                if uid not in by:
                    continue
                item=dict(audit)
                item["opponent_user_id"]=opp
                item["opponent_name"]=(
                    audit.get("away_name") if uid==str(audit.get("home_user_id") or "")
                    else audit.get("home_name")
                )
                # Tỷ số theo góc nhìn HLV này.
                if uid==str(audit.get("home_user_id") or ""):
                    item["my_score"]=audit.get("home_score"); item["opponent_score"]=audit.get("away_score")
                else:
                    item["my_score"]=audit.get("away_score"); item["opponent_score"]=audit.get("home_score")
                by[uid]["matches"].append(item)

        out=[]
        for row in by.values():
            played=0
            opponents=set()
            milestone=None
            details=[]
            for item in row["matches"]:
                played+=1
                opponents.add(str(item.get("opponent_user_id") or ""))
                detail=dict(item)
                detail["sequence_no"]=played
                detail["is_completion_match"]=False
                details.append(detail)
                if milestone is None and played>=target and len(opponents)>=min_opp:
                    milestone=item.get("confirmed_at_dt")
                    detail["is_completion_match"]=True

            row["played"]=played
            row["opponent_count"]=len(opponents)
            row["eligible"]=bool(milestone)
            row["completed_at"]=milestone.isoformat() if milestone else None
            row["completed_at_vn"]=_vn_datetime_text(milestone)
            row["early_eligible"]=bool(milestone and (not cutoff or milestone<=cutoff))
            row["match_confirmations"]=details
            row["completion_match"]=next((x for x in details if x.get("is_completion_match")),None)
            out.append(row)

        out.sort(key=lambda r:(_parse_iso(r.get("completed_at")) or datetime.max.replace(tzinfo=timezone.utc), (r.get("display_name") or "").lower()))

        # Competition ranking: cùng timestamp => cùng hạng; 1,1,3...
        previous_dt=None
        previous_rank=None
        eligible_seen=0
        for r in out:
            if not (r.get("eligible") and r.get("early_eligible")):
                r["finish_rank"]=None
                r["tickets"]=0
                continue
            eligible_seen+=1
            dt=_parse_iso(r.get("completed_at"))
            if previous_dt is not None and dt==previous_dt:
                rank=previous_rank
            else:
                rank=eligible_seen
            r["finish_rank"]=rank
            r["tickets"]=2 if rank==1 else (1 if rank in {2,3} else 0)
            previous_dt=dt
            previous_rank=rank

        return out


    def _combined_ranking(tournament_id):
        members=_all_members(tournament_id)
        base={
            str(m["user_id"]):{
                "user_id":str(m["user_id"]),
                "display_name":m.get("display_name") or "HLV",
                "played":0,"wins":0,"draws":0,"losses":0,
                "gf":0,"ga":0,"gd":0,"points":0,
                "stage1_points":0,"league_points":0,
                "pot_no":m.get("pot_no"),
                "club":m.get("fixed_club_name") or "",
                "recent_form":[],
            }
            for m in members
        }

        # Điểm/BXH giữ nguyên cách tính hiện tại: cộng GĐ1 + League.
        for code in ("stage1","league"):
            for r in _ranking(tournament_id,code):
                row=base.get(str(r.get("user_id")))
                if not row:
                    continue
                for k in ("played","wins","draws","losses","gf","ga","points"):
                    row[k]+=int(r.get(k) or 0)
                row["stage1_points" if code=="stage1" else "league_points"]+=int(r.get("points") or 0)

        # V1.5.20: lịch sử 5 trận C1 đã được xác nhận gần nhất của mỗi HLV.
        # Dùng completed_at để đảm bảo đúng thứ tự thời gian thực tế.
        completed=[]
        for mt in _matches(tournament_id):
            if str(mt.get("status") or "")!="completed":
                continue
            if str(mt.get("stage_code") or "") not in {"stage1","league","knockout"}:
                continue
            completed.append(mt)

        completed.sort(
            key=lambda mt:(
                _parse_iso(mt.get("completed_at") or mt.get("updated_at"))
                or datetime.min.replace(tzinfo=timezone.utc)
            )
        )

        for mt in completed:
            h=str(mt.get("home_user_id") or "")
            a=str(mt.get("away_user_id") or "")
            if h not in base and a not in base:
                continue
            try:
                hs=int(mt.get("home_score") or 0)
                aw=int(mt.get("away_score") or 0)
            except Exception:
                continue

            if hs>aw:
                h_code,h_label,h_short="W","Thắng","T"
                a_code,a_label,a_short="L","Bại","B"
            elif hs<aw:
                h_code,h_label,h_short="L","Bại","B"
                a_code,a_label,a_short="W","Thắng","T"
            else:
                h_code=h_code2="D"
                h_label=h_label2="Hòa"
                h_short=h_short2="H"
                a_code,a_label,a_short=h_code2,h_label2,h_short2

            completed_at=mt.get("completed_at") or mt.get("updated_at")
            if h in base:
                base[h]["recent_form"].append({
                    "code":h_code,
                    "label":h_label,
                    "short":h_short,
                    "match_id":mt.get("id"),
                    "completed_at":completed_at,
                })
            if a in base:
                base[a]["recent_form"].append({
                    "code":a_code,
                    "label":a_label,
                    "short":a_short,
                    "match_id":mt.get("id"),
                    "completed_at":completed_at,
                })

        vals=list(base.values())
        for r in vals:
            r["gd"]=r["gf"]-r["ga"]
            r["recent_form"]=r["recent_form"][-5:]

        vals.sort(
            key=lambda x:(x["points"],x["gd"],x["gf"],x["wins"]),
            reverse=True,
        )
        for i,r in enumerate(vals,1):
            r["rank"]=i
        return vals

    def _round_pairs(tournament_id, round_code):
        rows=[m for m in _matches(tournament_id,"knockout") if m.get("round_code")==round_code]
        groups={}
        for m in rows:
            key=m.get("aggregate_group") or str(m.get("id"))
            groups.setdefault(key,[]).append(m)
        return groups

    def _pair_winner(matches):
        if not matches: return None
        # Final Bo3: first coach to 2 match wins; game 3 is only needed if score is 1-1.
        if matches[0].get("round_code")=="final":
            wins={}
            for m in sorted(matches,key=lambda x:int(x.get("leg_no") or 1)):
                if m.get("status")!="completed": continue
                hs,aw=int(m.get("home_score") or 0),int(m.get("away_score") or 0)
                w=None
                if hs>aw: w=str(m.get("home_user_id"))
                elif aw>hs: w=str(m.get("away_user_id"))
                elif m.get("home_pen") is not None and m.get("away_pen") is not None:
                    if int(m.get("home_pen"))>int(m.get("away_pen")): w=str(m.get("home_user_id"))
                    elif int(m.get("away_pen"))>int(m.get("home_pen")): w=str(m.get("away_user_id"))
                if w: wins[w]=wins.get(w,0)+1
            for uid,n in wins.items():
                if n>=2: return uid
            return None
        if any(m.get("status")!="completed" for m in matches): return None
        a=str(matches[0].get("home_user_id")); b=str(matches[0].get("away_user_id"))
        totals={a:0,b:0}
        for m in matches:
            h,a2=str(m.get("home_user_id")),str(m.get("away_user_id"))
            totals[h]=totals.get(h,0)+int(m.get("home_score") or 0)
            totals[a2]=totals.get(a2,0)+int(m.get("away_score") or 0)
        if totals[a]>totals[b]: return a
        if totals[b]>totals[a]: return b
        # Aggregate tie: penalties from the final leg decide.
        last=sorted(matches,key=lambda x:int(x.get("leg_no") or 1))[-1]
        hp,ap=last.get("home_pen"),last.get("away_pen")
        if hp is not None and ap is not None:
            if int(hp)>int(ap): return str(last.get("home_user_id"))
            if int(ap)>int(hp): return str(last.get("away_user_id"))
        return None

    def _insert_ko_pair(tournament_id,round_code,home,away,two_legged=True):
        group=str(uuid.uuid4())
        if round_code=="final":
            legs=[1,2,3]
        else:
            legs=[1,2] if two_legged else [1]
        for leg in legs:
            h,a=(home,away) if leg%2==1 else (away,home)
            execute_query(db.table("tournament_matches").insert({"tournament_id":tournament_id,"stage_code":"knockout","round_code":round_code,"leg_no":leg,"aggregate_group":group,"home_user_id":h,"away_user_id":a,"status":"pending","created_at":now_iso(),"updated_at":now_iso()}),"ops_ko_auto_insert",attempts=2)

    def _maybe_advance_knockout(tournament_id):
        state=_setting(tournament_id,"knockout_flow",{}) or {}
        current=state.get("current_round")
        if not current: return state
        groups=_round_pairs(tournament_id,current)
        if not groups: return state
        winners=[]
        for matches in groups.values():
            w=_pair_winner(matches)
            if not w: return state
            winners.append(w)
        if current=="final":
            champion=winners[0] if winners else None
            if champion:
                for matches in groups.values():
                    for m in matches:
                        if m.get("status")!="completed":
                            execute_query(db.table("tournament_matches").update({"status":"cancelled","updated_at":now_iso()}).eq("id",m.get("id")),"ops_final_cancel_unused",attempts=2)
            state.update({"completed":True,"champion_user_id":champion,"completed_at":now_iso()})
            execute_query(db.table("tournament_stages").update({"status":"completed","updated_at":now_iso()}).eq("tournament_id",tournament_id).eq("stage_code","knockout"),"ops_ko_stage_done",attempts=2)
            execute_query(db.table("tournaments").update({"status":"completed","updated_at":now_iso()}).eq("id",tournament_id),"ops_tournament_done",attempts=2)
        else:
            nxt={"playoff":"r16","r16":"qf","qf":"sf","sf":"final"}.get(current)
            if nxt and not _round_pairs(tournament_id,nxt):
                if current=="playoff":
                    direct=state.get("direct_r16") or []
                    entrants=direct+winners
                else:
                    entrants=winners
                # Seed outer-to-inner where possible for a clear bracket.
                pairs=[]
                while len(entrants)>=2:
                    pairs.append((entrants.pop(0),entrants.pop(-1)))
                for a,b in pairs: _insert_ko_pair(tournament_id,nxt,a,b,two_legged=(nxt!="final"))
                state["current_round"]=nxt
        execute_query(db.table("tournament_settings").upsert({"tournament_id":tournament_id,"setting_key":"knockout_flow","setting_value":state,"updated_at":now_iso()},on_conflict="tournament_id,setting_key"),"ops_ko_flow_save",attempts=2)
        return state

    def _timing_payload(tournament_id):
        cfg=_setting(tournament_id,"competition_timing",{}) or {}
        reward_deadline=cfg.get("gd2_reward_ticket_deadline_at") or "2026-09-18T12:00:00+07:00"
        league_start=cfg.get("league_start_at") or "2026-09-18T12:00:00+07:00"
        return {
            "config":cfg,
            "stage1_start":_countdown_info(cfg.get("stage1_start_at")),
            "stage1_end":_countdown_info(cfg.get("stage1_end_at")),
            "stage1_early_end":_countdown_info(cfg.get("stage1_early_end_at")),
            "stage1_extension_end":_countdown_info(cfg.get("stage1_extension_end_at")),
            "club_draw":_countdown_info(cfg.get("club_draw_at") or "2026-09-17T20:00:00+07:00"),
            "gd2_reward_ticket_deadline":_countdown_info(reward_deadline),
            "league_start":_countdown_info(league_start),
            "league_end":_countdown_info(cfg.get("league_end_at")),
        }

    def _reward_ticket_phase_status(tournament_id, state=None, now=None):
        """Return GĐ1 early-ticket phase status for the three rewarded HLV.

        V1.6.2: tickets are usable after the 16 base clubs exist and may remain active while
        the fixed opponent schedule is generated/revealed, until the Admin-configured deadline.
        A holder may voluntarily finalize early; unused tickets are then forfeited so GĐ2 can start.
        """
        state=state if isinstance(state,dict) else (_club_draft_state(tournament_id,False) or {})
        cfg=_setting(tournament_id,"competition_timing",{}) or {}
        deadline=_parse_iso(cfg.get("gd2_reward_ticket_deadline_at") or "2026-09-18T12:00:00+07:00")
        vn=timezone(timedelta(hours=7))
        now=now or datetime.now(vn)
        if deadline and deadline.tzinfo is None: deadline=deadline.replace(tzinfo=vn)
        reward_ids=[str(uid) for uid in (state.get("order") or [])][:3]
        entries=state.get("entries") or {}
        holders=[]
        for uid in reward_ids:
            e=entries.get(uid) or {}
            holders.append({
                "user_id":uid,
                "finalized":bool(e.get("reward_finalized")),
                "tickets_remaining":int(e.get("tickets_remaining") or 0),
                "tickets_total":int(e.get("tickets_total") or 0),
                "selected":e.get("status")=="selected",
            })
        deadline_reached=bool(deadline and now>=deadline)
        all_finalized=bool(holders) and len(holders)==3 and all(h["finalized"] for h in holders)
        return {
            "deadline_at": deadline.isoformat() if deadline else None,
            "deadline_reached": deadline_reached,
            "holders": holders,
            "holder_count": len(holders),
            "finalized_count": sum(1 for h in holders if h["finalized"]),
            "all_finalized": all_finalized,
            "closed": deadline_reached or all_finalized,
            "open": (not deadline_reached) and (not all_finalized),
        }

    def _close_reward_ticket_phase(tournament_id, reason="deadline"):
        """Finalize all remaining reward holders and forfeit unused early tickets."""
        state=_club_draft_state(tournament_id,False) or {}
        entries=state.get("entries") or {}
        reward_ids=[str(uid) for uid in (state.get("order") or [])][:3]
        changed=False
        for uid in reward_ids:
            e=entries.get(uid) or {}
            if e.get("allocation_type")!="EARLY_REWARD" or e.get("reward_finalized"):
                continue
            left=int(e.get("tickets_remaining") or 0)
            e["reward_finalized"]=True
            e["reward_finalized_at"]=now_iso()
            e["reward_finalized_reason"]=reason
            e["tickets_forfeited"]=int(e.get("tickets_forfeited") or 0)+left
            e["tickets_remaining"]=0
            entries[uid]=e
            state.setdefault("history",[]).append({
                "at":now_iso(),"user_id":uid,"action":"REWARD_FINALIZE",
                "message":("Hết hạn sử dụng vé; CLB hiện tại được chốt tự động." if reason=="deadline" else "BTC chốt giai đoạn vé thưởng; vé chưa dùng không còn hiệu lực."),
            })
            changed=True
        if changed:
            state["entries"]=entries
            state["reward_phase_closed_at"]=now_iso()
            state["reward_phase_close_reason"]=reason
            execute_query(db.table("tournament_settings").upsert({
                "tournament_id":tournament_id,"setting_key":"club_draft_v2",
                "setting_value":state,"updated_at":now_iso(),
            },on_conflict="tournament_id,setting_key"),"ops_reward_phase_close",attempts=2)
        return state

    def _league_launch_readiness(tournament_id):
        """Single source of truth for opening GĐ2 in V1.6.2."""
        stages,_=_rows(db.table("tournament_stages").select("stage_code,status").eq("tournament_id",tournament_id),"ops_league_launch_stages")
        stage={str(r.get("stage_code")):r.get("status") for r in stages}
        members=_all_members(tournament_id)
        result={"ready":False,"reasons":[],"stage":stage}
        if stage.get("stage1")!="completed": result["reasons"].append("GĐ1 chưa completed")
        if stage.get("league") not in {"pending","open"}: result["reasons"].append("GĐ2 không ở trạng thái chuẩn bị")
        if len(members)!=16: result["reasons"].append("không đủ 16 HLV active")
        tier_counts=[sum(int(m.get("pot_no") or 0)==t for m in members) for t in (1,2,3)]
        if tier_counts!=[5,6,5]: result["reasons"].append("Tier HLV chưa đúng 5–6–5")
        if any(not m.get("fixed_club_name") for m in members): result["reasons"].append("chưa đủ 16 CLB")
        if any(m.get("fixed_club_name") and C1_CLUB_POT_BY_NAME.get(m.get("fixed_club_name")) != 4-int(m.get("pot_no") or 0) for m in members):
            result["reasons"].append("có CLB sai quy tắc Tier/Pot")
        if not (_setting(tournament_id,"pots_locked",{}) or {}).get("locked"): result["reasons"].append("Pot chưa khóa")
        if (_setting(tournament_id,"club_selection",{}) or {}).get("open"): result["reasons"].append("chọn CLB thủ công còn mở")
        matches=[m for m in _matches(tournament_id,"league") if m.get("status")!="cancelled"]
        ids={str(m.get("user_id")) for m in members}
        counts={uid:0 for uid in ids}; pairs=set(); tiers={str(m.get("user_id")):int(m.get("pot_no") or 0) for m in members}; seen={uid:set() for uid in ids}
        fixture_ok=True
        for match in matches:
            a,b=str(match.get("home_user_id") or ""),str(match.get("away_user_id") or "")
            key=tuple(sorted((a,b)))
            if not a or not b or a==b or a not in ids or b not in ids or key in pairs:
                fixture_ok=False; break
            pairs.add(key); counts[a]+=1; counts[b]+=1; seen[a].add(tiers[b]); seen[b].add(tiers[a])
        if len(matches)!=32 or not fixture_ok or any(v!=4 for v in counts.values()): result["reasons"].append("lịch GĐ2 chưa đủ 32 trận / 4 trận mỗi HLV")
        elif any(seen[uid]!={1,2,3} for uid in ids): result["reasons"].append("có HLV chưa gặp đủ 3 Tier")
        draw=_setting(tournament_id,"league_draw_v2",{}) or {}
        if not draw.get("completed"): result["reasons"].append("lễ bốc thăm đối thủ chưa công bố xong")
        result.update({"member_count":len(members),"tier_counts":tier_counts,"match_count":len(matches),"draw_completed":bool(draw.get("completed"))})
        result["ready"]=not result["reasons"]
        return result

    def _open_league_stage(tournament_id, reason="admin", force_close_rewards=False, start_at=None):
        """Open GĐ2 after validating all invariants; optionally close unused tickets."""
        # V1.6.23: the manual launch can coexist with unexpired reward tickets.
        # Never forfeit a ticket merely because the league stage opens.
        if force_close_rewards:
            _close_reward_ticket_phase(tournament_id,"admin")
        reward_status=_reward_ticket_phase_status(tournament_id)
        if not reward_status.get("closed") and reason not in {"admin_force", "admin_keep_rewards"}:
            return False,"3 HLV có vé thưởng chưa chốt xong và chưa đến hạn sử dụng vé."
        readiness=_league_launch_readiness(tournament_id)
        if not readiness.get("ready"):
            return False,"; ".join(readiness.get("reasons") or ["GĐ2 chưa sẵn sàng"])
        if (readiness.get("stage") or {}).get("league")=="open":
            return True,"GĐ2 đã mở."
        vn=timezone(timedelta(hours=7)); now=datetime.now(vn); start=start_at or now
        if start.tzinfo is None: start=start.replace(tzinfo=vn)
        cfg=_setting(tournament_id,"competition_timing",{}) or {}; cfg=dict(cfg) if isinstance(cfg,dict) else {}
        cfg["league_start_at"]=start.isoformat(); cfg["league_end_at"]=(start+timedelta(days=7)).isoformat(); cfg["league_started_reason"]=reason
        execute_query(db.table("tournament_settings").upsert({"tournament_id":tournament_id,"setting_key":"competition_timing","setting_value":cfg,"updated_at":now_iso()},on_conflict="tournament_id,setting_key"),"ops_league_open_timing",attempts=2)
        execute_query(db.table("tournament_stages").update({"status":"open","updated_at":now_iso()}).eq("tournament_id",tournament_id).eq("stage_code","league").in_("status",["pending","open"]),"ops_league_open_stage",attempts=2)
        sync=_setting(tournament_id,"deadline_sync",{}) or {}; sync["league_started"]=now_iso(); sync["league_started_reason"]=reason; sync.pop("league_blocked",None); sync.pop("league_awaiting_admin",None)
        execute_query(db.table("tournament_settings").upsert({"tournament_id":tournament_id,"setting_key":"deadline_sync","setting_value":sync,"updated_at":now_iso()},on_conflict="tournament_id,setting_key"),"ops_league_open_sync",attempts=2)
        return True,"Đã mở GĐ2."

    def _sync_c1_club_pool(tournament_id):
        """Ensure the official C1 random pool is exactly the 24 approved clubs."""
        existing,_=_rows(db.table("tournament_clubs").select("*").eq("tournament_id",tournament_id),"ops_club_pool_sync_read")
        by_name={str(x.get("name") or "").casefold():x for x in existing}
        for name in C1_CLUB_POOL:
            key="c1-"+name.casefold().replace(" ","-").replace("é","e").replace("í","i").replace("ç","c")
            row=by_name.get(name.casefold())
            payload={"tournament_id":tournament_id,"club_key":key,"name":name,"is_available":True}
            if row:
                execute_query(db.table("tournament_clubs").update({"name":name,"is_available":True}).eq("id",row.get("id")),"ops_club_pool_sync_update",attempts=2)
            else:
                execute_query(db.table("tournament_clubs").upsert(payload,on_conflict="tournament_id,club_key"),"ops_club_pool_sync_insert",attempts=2)
        # Any legacy club remains in history but is excluded from the official random pool.
        for row in existing:
            if str(row.get("name") or "") not in C1_CLUB_POOL and row.get("is_available"):
                execute_query(db.table("tournament_clubs").update({"is_available":False}).eq("id",row.get("id")),"ops_club_pool_disable_legacy",attempts=2)

    def _available_clubs(tournament_id, skipped=None):
        skipped=set(str(x) for x in (skipped or []))
        clubs,_=_rows(db.table("tournament_clubs").select("*").eq("tournament_id",tournament_id).eq("is_available",True).order("name"),"ops_club_pool")
        return [c for c in clubs if str(c.get("name") or "") in C1_CLUB_POOL and not c.get("selected_by") and str(c.get("id")) not in skipped]

    def _club_assign(tournament_id,user_id,club):
        execute_query(db.table("tournament_clubs").update({"selected_by":user_id,"selected_at":now_iso()}).eq("id",club.get("id")).is_("selected_by","null"),"ops_draft_reserve",attempts=2)
        execute_query(db.table("tournament_members").update({"fixed_club_id":club.get("club_key"),"fixed_club_name":club.get("name")}).eq("tournament_id",tournament_id).eq("user_id",user_id),"ops_draft_member",attempts=2)

    def _club_draft_state(tournament_id, auto_resolve=True):
        state=_setting(tournament_id,"club_draft_v2",{}) or {}
        if state.get("order") and any((state.get("entries") or {}).get(str(uid),{}).get("allocation_type")=="EARLY_REWARD" for uid in state.get("order",[])):
            # Legacy per-turn timers stay disabled; V1.6.2 uses one global GĐ2 reward-ticket deadline.
            state["countdown"]={}
            return state
        if not state.get("active") or not state.get("order"):
            return state
        idx=int(state.get("current_index") or 0)
        if idx>=len(state.get("order") or []):
            state["active"]=False; state["completed"]=True
            return state
        uid=str(state["order"][idx])
        entry=(state.get("entries") or {}).get(uid) or {}
        deadline=_parse_iso(state.get("deadline_at"))
        if auto_resolve and deadline and datetime.now(deadline.tzinfo or timezone.utc)>=deadline and entry.get("status")!="selected":
            pool=_available_clubs(tournament_id,entry.get("skipped") or [])
            if pool:
                club=random.choice(pool); _club_assign(tournament_id,uid,club)
                entry["candidate"]={"id":str(club.get("id")),"name":club.get("name")}; entry["status"]="selected"; entry["selected_club"]=club.get("name")
                state.setdefault("history",[]).append({"at":now_iso(),"user_id":uid,"action":"AUTO_SELECT","club":club.get("name"),"message":f"Hệ thống tự Random và chốt {club.get('name')} do hết thời gian."})
            state["entries"][uid]=entry
            state["current_index"]=idx+1
            if state["current_index"]<len(state["order"]):
                nxt=state["order"][state["current_index"]]; mins=10 if state["current_index"]==0 else 5
                state["deadline_at"]=(datetime.now(timezone(timedelta(hours=7)))+timedelta(minutes=mins)).isoformat()
                state.setdefault("history",[]).append({"at":now_iso(),"user_id":str(nxt),"action":"TURN_OPEN","message":f"Mở lượt cho HLV tiếp theo ({mins} phút)."})
            else:
                state["active"]=False; state["completed"]=True; state["deadline_at"]=None
            execute_query(db.table("tournament_settings").upsert({"tournament_id":tournament_id,"setting_key":"club_draft_v2","setting_value":state,"updated_at":now_iso()},on_conflict="tournament_id,setting_key"),"ops_draft_auto_save",attempts=2)
        state["countdown"]=_countdown_info(state.get("deadline_at"))
        return state

    def _league_draw_payload(tournament_id):
        state=_setting(tournament_id,"league_draw_v2",{}) or {}
        reveals=_setting(tournament_id,"league_player_reveals",{}) or {}
        return {"state":state,"player_reveals":reveals}

    def _stage1_readiness(tournament_id):
        members=_all_members(tournament_id)
        member_ids=[str(m.get("user_id")) for m in members if m.get("user_id")]
        n=len(member_ids)
        stage=_stage(tournament_id,"stage1") or {}
        target=max(1,int(stage.get("match_target") or 6))
        min_opp=max(1,int(stage.get("min_opponents") or 3))
        expected=(n*target)//2 if n else 0
        matches=[m for m in _matches(tournament_id,"stage1") if m.get("status")!="cancelled"]
        per={uid:{"matches":0,"opponents":set()} for uid in member_ids}
        for m in matches:
            h=str(m.get("home_user_id") or ""); a=str(m.get("away_user_id") or "")
            if h in per:
                per[h]["matches"]+=1
                if a: per[h]["opponents"].add(a)
            if a in per:
                per[a]["matches"]+=1
                if h: per[a]["opponents"].add(h)
        bad=[uid for uid,v in per.items() if v["matches"]!=target or len(v["opponents"])<min_opp]
        pool=_stage1_club_pool(tournament_id) or []
        cfg=_setting(tournament_id,"competition_timing",{}) or {}
        checks={
            "members": n>=4 and n%2==0,
            "matches": len(matches)==expected and not bad,
            "clubs": len(pool)>=2,
            "timing": bool(cfg.get("stage1_start_at")),
        }
        return {
            "ready":all(checks.values()),"checks":checks,"member_count":n,"target":target,
            "expected_matches":expected,"actual_matches":len(matches),"club_count":len(pool),
            "bad_player_count":len(bad),
        }

    def _sync_competition_deadlines(tournament_id):
        cfg=_setting(tournament_id,"competition_timing",{}) or {}
        state=_setting(tournament_id,"deadline_sync",{}) or {}
        vn=timezone(timedelta(hours=7)); now=datetime.now(vn)
        s1start=_parse_iso(cfg.get("stage1_start_at"))
        if s1start and s1start.tzinfo is None: s1start=s1start.replace(tzinfo=vn)
        if s1start and now>=s1start and not state.get("stage1_started"):
            readiness=_stage1_readiness(tournament_id)
            if readiness.get("ready"):
                execute_query(db.table("tournaments").update({"registration_open":False,"status":"active","updated_at":now_iso()}).eq("id",tournament_id),"ops_auto_s1_tournament",attempts=2)
                execute_query(db.table("tournament_stages").update({"status":"open","updated_at":now_iso()}).eq("tournament_id",tournament_id).eq("stage_code","stage1"),"ops_auto_s1_stage",attempts=2)
                state["stage1_started"]=now_iso()
                state.pop("stage1_blocked",None)
            else:
                state["stage1_blocked"]={"at":now_iso(),**readiness}
        reward_deadline=_parse_iso(cfg.get("gd2_reward_ticket_deadline_at") or "2026-09-18T12:00:00+07:00")
        if reward_deadline and reward_deadline.tzinfo is None: reward_deadline=reward_deadline.replace(tzinfo=vn)
        if reward_deadline and now>=reward_deadline:
            _close_reward_ticket_phase(tournament_id,"deadline")
            state["gd2_reward_deadline_processed"]=state.get("gd2_reward_deadline_processed") or now_iso()

        lgstart=_parse_iso(cfg.get("league_start_at") or "2026-09-18T12:00:00+07:00")
        if lgstart and lgstart.tzinfo is None: lgstart=lgstart.replace(tzinfo=vn)
        if lgstart and now>=lgstart and not state.get("league_started"):
            ok,msg=_open_league_stage(tournament_id,"scheduled",start_at=now)
            if ok:
                state["league_started"]=now_iso(); state["league_started_reason"]="scheduled"; state.pop("league_blocked",None)
            else:
                state["league_blocked"]={"at":now_iso(),"reason":msg}
        ext=_parse_iso(cfg.get("stage1_extension_end_at"))
        if ext and ext.tzinfo is None: ext=ext.replace(tzinfo=timezone(timedelta(hours=7)))
        now=datetime.now((ext.tzinfo if ext else vn))
        if ext and now>=ext and not state.get("stage1_extension_processed"):
            pending=[m for m in _matches(tournament_id,"stage1") if m.get("status") not in {"completed","disputed","cancelled"}]
            for m in pending:
                execute_query(db.table("tournament_matches").update({"status":"disputed","updated_at":now_iso()}).eq("id",m.get("id")),"ops_deadline_s1_dispute",attempts=2)
            if pending:
                state["stage1_extension_processed"]=now_iso(); state["stage1_unfinished_count"]=len(pending)
                execute_query(db.table("tournament_settings").upsert({"tournament_id":tournament_id,"setting_key":"deadline_sync","setting_value":state,"updated_at":now_iso()},on_conflict="tournament_id,setting_key"),"ops_deadline_sync_save",attempts=2)
        if state:
            execute_query(db.table("tournament_settings").upsert({"tournament_id":tournament_id,"setting_key":"deadline_sync","setting_value":state,"updated_at":now_iso()},on_conflict="tournament_id,setting_key"),"ops_deadline_sync_persist",attempts=2)
        return state

    def _club_draft_admin_rows(tournament_id):
        """Admin-only audit view for the 16 C1 club allocations."""
        state=_club_draft_state(tournament_id,False) or {}
        members={str(m.get("user_id")):m for m in _all_members(tournament_id)}
        history=state.get("history") or []
        rows=[]
        order=[str(x) for x in (state.get("all_order") or state.get("order") or [])][:16]
        for pos,uid in enumerate(order,1):
            entry=(state.get("entries") or {}).get(uid) or {}
            member=members.get(uid) or {}
            club=entry.get("selected_club") or member.get("fixed_club_name") or (entry.get("candidate") or {}).get("name") or ""
            user_history=[h for h in history if str(h.get("user_id") or "")==uid]
            rerolls=[h for h in user_history if h.get("action") in {"SKIP","REROLL"}]
            rows.append({
                "position":pos,"user_id":uid,"display_name":member.get("display_name") or "HLV",
                "seed_no":int(member.get("seed_no") or 0),
                "tier_hlv":int(member.get("pot_no") or 0),
                "allocation_type":"EARLY_REWARD" if pos<=3 else "SYSTEM",
                "tickets_total":int(entry.get("tickets_total") or (2 if pos==1 else (1 if pos<=3 else 0))),
                "tickets_remaining":int(entry.get("tickets_remaining") or 0),
                "reward_finalized":bool(entry.get("reward_finalized")),
                "reward_finalized_at":entry.get("reward_finalized_at"),
                "club":club,"club_pot":C1_CLUB_POT_BY_NAME.get(club),
                "status":entry.get("status") or ("selected" if member.get("fixed_club_name") else "waiting"),
                "reroll_count":len(rerolls),"history":user_history,
            })
        return sorted(rows, key=lambda r:(r.get("seed_no") or 9999, r.get("display_name") or ""))

    def _event_ops_payload(tournament_id,user_id=None):
        _sync_competition_deadlines(tournament_id)
        cr=_completion_ranking(tournament_id)
        mine=next((x for x in cr if str(x.get("user_id"))==str(user_id)),None) if user_id else None
        s1_reveals=_setting(tournament_id,"stage1_player_reveals",{}) or {}
        league_draw=_league_draw_payload(tournament_id)
        base_config=_setting(tournament_id,"club_base_draft_v1",{}) or {}
        ordered=sorted(_all_members(tournament_id),key=lambda m:int(m.get("seed_no") or 9999),reverse=base_config.get("direction")=="descending")
        base_turn=next((m for m in ordered if not m.get("fixed_club_name")),None) if base_config.get("mode")=="sequential" else None
        return {"base_draft_config":base_config,"base_draft_next":base_turn,
                "timing":_timing_payload(tournament_id),"reward_ticket_phase":_reward_ticket_phase_status(tournament_id),"completion_ranking":cr,"my_completion":mine,
                "stage1_confirmation_audit":_stage1_confirmation_audit(tournament_id),
                "club_draft":_club_draft_state(tournament_id),"club_draft_admin_rows":_club_draft_admin_rows(tournament_id),
                "stage1_early_reward_state":_stage1_early_reward_state(tournament_id),
                "stage1_reveals":s1_reveals,"league_draw":league_draw}

    def _reward_summary(tournament_id,user_id):
        rules,_=_rows(db.table("tournament_reward_rules").select("*").eq("tournament_id",tournament_id).eq("enabled",True).order("priority"),"ops_rewards")
        grants,_=_rows(db.table("tournament_reward_grants").select("*").eq("tournament_id",tournament_id).eq("user_id",user_id),"ops_reward_grants")
        return {"rules":rules,"grants":grants}

    def _host_ready_rows(tournament_id, members_all=None):
        """Danh sách Host đang rảnh dùng chung cho render trang và API live-polling.

        Chỉ lấy HLV active thuộc đúng giải, có Host,
        online theo presence hiện tại và không ở phòng đấu đang hoạt động.
        """
        members_all = members_all if members_all is not None else _all_members(tournament_id)
        member_ids={str(hm.get("user_id") or "") for hm in members_all if hm.get("user_id")}
        busy_user_ids=set()
        if member_ids:
            active_room_statuses=[
                "waiting_ready",
                "playing",
                "friendly_playing",
                "waiting_result_confirm",
                "waiting_confirm",
                "disputed",
            ]
            active_rooms,_=_rows(
                db.table("match_rooms")
                .select("host_user_id,guest_user_id,status")
                .in_("status",active_room_statuses)
                .limit(500),
                "ops_available_hosts_active_rooms",
            )
            for ar in active_rooms:
                hid=str(ar.get("host_user_id") or "")
                gid=str(ar.get("guest_user_id") or "")
                if hid in member_ids:
                    busy_user_ids.add(hid)
                if gid in member_ids:
                    busy_user_ids.add(gid)

        host_ready=[]
        for hm in members_all:
            huid=str(hm.get("user_id") or "")
            user_row=hm.get("user") or {}
            if hm.get("has_host") and is_user_online_now(user_row) and huid not in busy_user_ids:
                host_ready.append({
                    "user_id":huid,
                    "display_name":hm.get("display_name") or "HLV",
                    "region":hm.get("host_region") or "—",
                })
        host_ready.sort(key=lambda x: str(x.get("display_name") or "").casefold())
        return host_ready

    def _viewer_visible_matches(tournament_id, user_id, rows):
        """Hide pre-generated GĐ2 opponents until that HLV is revealed or GĐ2 opens."""
        stage=_stage(tournament_id,"league") or {}
        league_open=str(stage.get("status") or "").lower() in {"open","completed"}
        if league_open:
            return rows
        draw=_setting(tournament_id,"league_draw_v2",{}) or {}
        revealed={str(k) for k in (draw.get("revealed") or {}).keys()}
        uid=str(user_id or "")
        visible=[]
        for m in rows:
            if str(m.get("stage_code") or "")!="league":
                visible.append(m); continue
            if uid and uid in revealed and uid in {str(m.get("home_user_id") or ""),str(m.get("away_user_id") or "")}:
                visible.append(m)
        return visible

    def _detail_payload(tournament_id, user_id):
        tour=_tour(tournament_id)
        if not tour: return None
        member=_member(tournament_id,user_id)
        stages,_=_rows(db.table("tournament_stages").select("*").eq("tournament_id",tournament_id).order("sort_order"),"ops_stages")
        s1=_stage1_progress(tournament_id)
        league=_ranking(tournament_id,"league")
        matches=_viewer_visible_matches(tournament_id,user_id,_matches(tournament_id))
        matches=_decorate_matches(tournament_id,matches)
        matches=_attach_schedule_state(tournament_id,matches,user_id)
        availability=_availability_payload(tournament_id,user_id,matches) if member else {"days":_availability_days(),"mine":[],"mine_set":set(),"status":"missing","slot_count":0}
        hosts,_=_rows(db.table("tournament_hosts").select("*").eq("tournament_id",tournament_id).order("region").order("name"),"ops_hosts")
        clubs,_=_rows(db.table("tournament_clubs").select("*").eq("tournament_id",tournament_id).order("name"),"ops_clubs")
        me_progress=next((r for r in s1 if str(r["user_id"])==str(user_id)),None)
        ops_events=_event_ops_payload(tournament_id,user_id)
        members_all=_all_members(tournament_id)

        # V1.6.26: Host đang rảnh = HLV active, có Host, online thật
        # và không nằm trong phòng đấu đang hoạt động. Không cần nút bật rảnh.
        # `confirmed` là trạng thái trận đã xong nên không được giữ HLV ở trạng thái bận.
        host_ready=_host_ready_rows(tournament_id, members_all=members_all)
        my_host_profile=next((hm for hm in members_all if str(hm.get("user_id"))==str(user_id)),{})
        c1_test_matches=_c1_test_confirmed_matches(tournament_id)
        c1_test_ranking=_c1_test_ranking(tournament_id)
        return {"tournament":tour,"member":member,"stages":stages,"stage1_ranking":s1,"league_ranking":league,"combined_ranking":_combined_ranking(tournament_id),
                "matches":matches,"hosts":hosts,"clubs":clubs,"me_progress":me_progress,"rewards":_reward_summary(tournament_id,user_id),"availability":availability,
                "host_ready":host_ready,"my_has_host":bool(my_host_profile.get("has_host")),
                "event_ops":ops_events,"knockout_flow":_setting(tournament_id,"knockout_flow",{}) or {},
                "stage1_club_pool":_stage1_club_pool(tournament_id),"tournament_rooms":_tournament_rooms(tournament_id),
                "all_team_options":_stage1_eligible_clubs(),"stage1_team_options":_stage1_eligible_clubs(),"league_config":_setting(tournament_id,"league_config",{}) or {},
                "stage1_readiness":_stage1_readiness(tournament_id),
                "c1_test_stage1_ranking":c1_test_ranking,
                "c1_test_recent_matches":c1_test_matches[:5],"tournament_members":members_all,"tournament_member_map":{str(x.get("user_id")):x for x in members_all}}

    def _tournament_scale(tournament_id):
        """Planned/actual match volume for Admin after registration closes."""
        members=_all_members(tournament_id)
        n=len(members)
        s1=_stage(tournament_id,"stage1") or {}
        s1_target=int(s1.get("match_target") or 6)
        stage1_planned=(n*s1_target)//2 if n else 0

        pot_state=_setting(tournament_id,"pots_locked",{}) or {}
        pot_count=max(1,int(pot_state.get("pot_count") or 3))
        league_cfg=_setting(tournament_id,"league_config",{}) or {}
        matches_per_pot=1
        league_per_hlv=4
        league_planned=(n*league_per_hlv)//2 if n else 0

        all_matches=_matches(tournament_id)
        actual_by_stage={"stage1":0,"league":0,"knockout":0}
        completed_by_stage={"stage1":0,"league":0,"knockout":0}
        for m in all_matches:
            code=str(m.get("stage_code") or "")
            if code in actual_by_stage:
                actual_by_stage[code]+=1
                if m.get("status") in {"completed","cancelled"}:
                    completed_by_stage[code]+=1

        ko_state=_setting(tournament_id,"knockout_flow",{}) or {}
        ko_generated=actual_by_stage["knockout"]>0
        if ko_generated:
            knockout_planned=actual_by_stage["knockout"]
            knockout_label=f"{knockout_planned} trận đã sinh"
            total_min=stage1_planned+league_planned+knockout_planned
            total_max=total_min
        else:
            # Luật chính thức: Top 8 vào thẳng Knockout (Tứ kết), không Play-off. Chung kết Bo3.
            if n>=8:
                ko_min,ko_max=14,15
                knockout_label=f"{ko_min}–{ko_max} trận · Top 8 vào thẳng Tứ kết"
            else:
                ko_min=ko_max=0
                knockout_label="Chưa đủ 8 HLV"
            knockout_planned=ko_max
            total_min=stage1_planned+league_planned+ko_min
            total_max=stage1_planned+league_planned+ko_max

        # For progress, only count fixtures that already exist. Planned future fixtures are not complete yet.
        completed=sum(completed_by_stage.values())
        total_planned=max(total_max,0)
        remaining=max(0,total_planned-completed)
        percent=round((completed/total_planned)*100,1) if total_planned else 0
        return {
            "member_count":n,
            "stage1":{"per_hlv":s1_target,"planned":stage1_planned,"actual":actual_by_stage["stage1"],"completed":completed_by_stage["stage1"]},
            "league":{"per_hlv":league_per_hlv,"pot_count":3,"tier_coverage_required":True,"tier_coverage_scope":"all_four_matches","planned":league_planned,"actual":actual_by_stage["league"],"completed":completed_by_stage["league"]},
            "knockout":{"planned":knockout_planned,"actual":actual_by_stage["knockout"],"completed":completed_by_stage["knockout"],"label":knockout_label},
            "final_label":"2–3 trận (Bo3)",
            "total_min":total_min,"total_max":total_max,"completed":completed,"remaining":remaining,"percent":percent,
        }

    def _admin_payload():
        tours,_=_rows(db.table("tournaments").select("*").eq("is_visible",True).order("created_at"),"ops_admin_tours")
        if not tours: return {"ready":True,"tournament":None}
        tour=tours[0]; tid=tour["id"]
        payload=_detail_payload(tid,(current_user() or {}).get("id")) or {}
        progress=_stage1_progress(tid)
        pmap={str(x.get("user_id")):x for x in progress}
        members=_all_members(tid)
        for m in members:
            pr=pmap.get(str(m.get("user_id"))) or {}
            m["stage1_played"]=pr.get("played",0)
            m["stage1_target"]=pr.get("target",6)
            m["stage1_percent"]=pr.get("percent",0)
            m["stage1_points"]=pr.get("points",0)
        test_ids=_c1_test_user_ids(tid)
        test_users=_c1_test_users(tid) if test_ids else []
        # V1.5.5: Trung tâm C1 Admin là nơi duy nhất nạp toàn bộ dữ liệu vận hành giải.
        host_list=[m for m in members if m.get("has_host")]
        host_list.sort(key=lambda x: ((x.get("host_region") or ""), (x.get("display_name") or "").lower()))

        # V1.5.6: Admin xem lịch thi đấu đã chốt của TOÀN BỘ HLV trong 3 ngày tới
        # theo ngày Việt Nam: Hôm nay / Ngày mai / Ngày kia.
        vn_tz=timezone(timedelta(hours=7))
        now_vn=datetime.now(vn_tz)
        last_day=now_vn.date()+timedelta(days=2)
        day_label_map={
            now_vn.date():"Hôm nay",
            now_vn.date()+timedelta(days=1):"Ngày mai",
            now_vn.date()+timedelta(days=2):"Ngày kia",
        }
        upcoming_3day_matches=[]
        for match in (payload.get("matches") or []):
            raw=match.get("scheduled_at")
            if not raw:
                continue
            try:
                dt=datetime.fromisoformat(str(raw).replace("Z","+00:00"))
                if dt.tzinfo is None:
                    dt=dt.replace(tzinfo=vn_tz)
                dt_vn=dt.astimezone(vn_tz)
            except Exception:
                continue
            if dt_vn < now_vn or dt_vn.date() > last_day:
                continue
            row=dict(match)
            row["scheduled_at_vn"]=dt_vn.isoformat()
            row["schedule_date"]=dt_vn.date().isoformat()
            row["schedule_day_label"]=day_label_map.get(dt_vn.date(),dt_vn.strftime("%d/%m"))
            row["schedule_date_label"]=dt_vn.strftime("%d/%m/%Y")
            row["schedule_time_label"]=dt_vn.strftime("%H:%M")
            upcoming_3day_matches.append(row)
        upcoming_3day_matches.sort(key=lambda x: str(x.get("scheduled_at_vn") or ""))

        # V1.5.10: Admin theo dõi HLV nào đã khai giờ rảnh, đã có lịch, hoặc chưa đăng ký.
        member_ids=[str(m.get("user_id")) for m in members if m.get("user_id")]
        availability_rows=_availability_rows(tid, member_ids) if member_ids else []
        availability_by_user={}
        for slot in availability_rows:
            availability_by_user.setdefault(str(slot.get("user_id") or ""), []).append(slot)

        scheduled_by_user={}
        for match in upcoming_3day_matches:
            for side in ("home_user_id","away_user_id"):
                suid=str(match.get(side) or "")
                if not suid:
                    continue
                scheduled_by_user.setdefault(suid, []).append(match)

        availability_status_rows=[]
        registered_count=0
        scheduled_exempt_count=0
        missing_count=0
        for member in members:
            muid=str(member.get("user_id") or "")
            slots=availability_by_user.get(muid, [])
            scheduled=scheduled_by_user.get(muid, [])
            if scheduled:
                status_code="scheduled"
                status_label="📅 Đã có lịch · Không cần đăng ký"
                scheduled_exempt_count += 1
            elif slots:
                status_code="registered"
                status_label="✅ Đã đăng ký"
                registered_count += 1
            else:
                status_code="missing"
                status_label="🔴 Chưa đăng ký"
                missing_count += 1
            availability_status_rows.append({
                "user_id":muid,
                "display_name":member.get("display_name") or "HLV",
                "zalo_name":member.get("zalo_name") or "",
                "has_host":bool(member.get("has_host")),
                "host_region":member.get("host_region") or "—",
                "status_code":status_code,
                "status_label":status_label,
                "slots":slots,
                "slot_labels":[x.get("slot_label") for x in slots if x.get("slot_label")],
                "slot_count":len(slots),
                "scheduled_matches":scheduled,
                "scheduled_count":len(scheduled),
            })
        availability_status_rows.sort(key=lambda x: ({"missing":0,"registered":1,"scheduled":2}.get(x.get("status_code"),9), (x.get("display_name") or "").lower()))

        test_ranking=_c1_test_ranking(tid) if test_ids else []
        test_matches=_c1_test_confirmed_matches(tid) if test_ids else []
        test_id_set=set(test_ids)
        test_rooms=[]
        for room in (payload.get("tournament_rooms") or []):
            meta=room.get("tournament_meta") or _room_meta(room) or {}
            participants={str(room.get("host_user_id") or ""),str(room.get("guest_user_id") or "")}
            if meta.get("test_sandbox_room") or bool(participants & test_id_set):
                test_rooms.append(room)

        payload.update({
            "ready":True,"tournament":tour,"members":members,"progress":progress,
            "club_draw_at":(_setting(tid,"competition_timing",{}) or {}).get("club_draw_at") or "2026-09-17T20:00:00+07:00",
            "gd2_reward_ticket_deadline_at":(_setting(tid,"competition_timing",{}) or {}).get("gd2_reward_ticket_deadline_at") or "2026-09-18T12:00:00+07:00",
            "league_start_at":(_setting(tid,"competition_timing",{}) or {}).get("league_start_at") or "2026-09-18T12:00:00+07:00",
            "combined_ranking":_combined_ranking(tid),
            "knockout_flow":_setting(tid,"knockout_flow",{}) or {},
            "scale":_tournament_scale(tid),"c1_test_user_ids":test_ids,"c1_test_users":test_users,
            "c1_test_ranking":test_ranking,"c1_test_matches":test_matches,"c1_test_rooms":test_rooms,
            "c1_club_pots":C1_CLUB_POTS,"c1_club_pool":C1_CLUB_POOL,
            "host_list":host_list,"host_count":len(host_list),
            "all_matches":payload.get("matches") or [],
            "upcoming_3day_matches":upcoming_3day_matches,
            "upcoming_3day_window":{
                "from":now_vn.date().isoformat(),
                "to":last_day.isoformat(),
                "from_label":now_vn.strftime("%d/%m/%Y"),
                "to_label":last_day.strftime("%d/%m/%Y"),
            },
            "active_c1_rooms":payload.get("tournament_rooms") or [],
            "availability_status_rows":availability_status_rows,
            "availability_registered_count":registered_count,
            "availability_scheduled_exempt_count":scheduled_exempt_count,
            "availability_missing_count":missing_count,
        })
        return payload

    @app.context_processor
    def inject_tournament_ops():
        if request.endpoint == "admin":
            try: return {"tournament_ops_admin":_admin_payload()}
            except Exception as exc:
                app.logger.warning("Tournament admin ops context: %s",exc)
                return {"tournament_ops_admin":{"ready":False}}
        return {}

    return {k: v for k, v in locals().items() if k.startswith('_') and callable(v)}
