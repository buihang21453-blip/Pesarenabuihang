"""Tournament competition operations (V1.4.30).

Independent from Rank/Season. Handles stages, tournament-only matches, ranking,
Pot, club lock, scheduling, hosts, progress, knockout/two legs and early rewards.
"""
from datetime import datetime, timezone, timedelta
import uuid
import random
import json

from teams_data import TEAMS

STAGE_LABELS = {
    "stage1": "GĐ1 · Phân hạng",
    "league": "League Phase",
    "knockout": "Knockout",
}
ROUND_ORDER = ["playoff", "r16", "qf", "sf", "final"]

# V1.4.94 - Làm rõ khối sẵn sàng khai mạc + nút Sinh lịch GĐ1 ngay tại cảnh báo.
# V1.4.89 - Giao diện HLV chia 6 tab gọn: Trung tâm, GĐ1, Lịch, GĐ2, Knockout, Thông tin.
# V1.4.88 - Tạo phòng trực tiếp + mời đúng đối thủ; dọn gói deploy.
STAGE1_ALLOWED_TIERS = {"S+", "S"}
TOURNAMENT_ROOM_PREFIX = "TOURNAMENT_ROOM|"


def register_routes(context):
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
            days.append({"date":d.isoformat(),"label":label,"weekday":f"{weekday_names[d.weekday()]} · {d.strftime('%d/%m')}","slots":slots})
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
        return {
            "days":days,"mine":decorated(mine),"mine_set":mine_set,"status":status,"slot_count":len(mine_set),
            "opponent":opponent,"opponent_slots":decorated(opp_slots),"overlap":decorated(overlap),
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

    def _completion_ranking(tournament_id):
        stage=_stage(tournament_id,"stage1") or {}
        target=int(stage.get("match_target") or 6)
        min_opp=int(stage.get("min_opponents") or 3)
        cutoff=_parse_iso((_setting(tournament_id,"competition_timing",{}) or {}).get("stage1_early_end_at"))
        members=_all_members(tournament_id)
        by={str(m.get("user_id")):{"user_id":str(m.get("user_id")),"display_name":m.get("display_name") or "HLV","done":[],"opponents":set()} for m in members}
        for m in _matches(tournament_id,"stage1",["completed"]):
            h,a=str(m.get("home_user_id")),str(m.get("away_user_id"))
            dt=_parse_iso(m.get("completed_at") or m.get("updated_at"))
            if h in by:
                by[h]["done"].append(dt); by[h]["opponents"].add(a)
            if a in by:
                by[a]["done"].append(dt); by[a]["opponents"].add(h)
        out=[]
        for row in by.values():
            valid=[x for x in row.pop("done") if x]
            row["played"]=len(valid); row["opponent_count"]=len(row.pop("opponents"))
            row["eligible"]=row["played"]>=target and row["opponent_count"]>=min_opp
            completed=max(valid) if row["eligible"] and valid else None
            row["completed_at"]=completed.isoformat() if completed else None
            row["early_eligible"]=bool(completed and (not cutoff or completed<=cutoff))
            out.append(row)
        out.sort(key=lambda r: (_parse_iso(r.get("completed_at")) or datetime.max.replace(tzinfo=timezone.utc)))
        rank=0
        for r in out:
            if r["eligible"] and r["early_eligible"]:
                rank+=1; r["finish_rank"]=rank
                r["tickets"]=3 if rank==1 else (2 if rank<=3 else (1 if rank<=10 else 0))
            else:
                r["finish_rank"]=None; r["tickets"]=0
        return out

    def _combined_ranking(tournament_id):
        members=_all_members(tournament_id)
        base={str(m["user_id"]):{"user_id":str(m["user_id"]),"display_name":m.get("display_name") or "HLV","played":0,"wins":0,"draws":0,"losses":0,"gf":0,"ga":0,"gd":0,"points":0,"pot_no":m.get("pot_no"),"club":m.get("fixed_club_name") or ""} for m in members}
        for code in ("stage1","league"):
            for r in _ranking(tournament_id,code):
                row=base.get(str(r.get("user_id")))
                if not row: continue
                for k in ("played","wins","draws","losses","gf","ga","points"):
                    row[k]+=int(r.get(k) or 0)
        vals=list(base.values())
        for r in vals: r["gd"]=r["gf"]-r["ga"]
        vals.sort(key=lambda x:(x["points"],x["gd"],x["gf"],x["wins"]),reverse=True)
        for i,r in enumerate(vals,1): r["rank"]=i
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
        return {
            "config":cfg,
            "stage1_start":_countdown_info(cfg.get("stage1_start_at")),
            "stage1_end":_countdown_info(cfg.get("stage1_end_at")),
            "stage1_early_end":_countdown_info(cfg.get("stage1_early_end_at")),
            "stage1_extension_end":_countdown_info(cfg.get("stage1_extension_end_at")),
            "league_start":_countdown_info(cfg.get("league_start_at")),
            "league_end":_countdown_info(cfg.get("league_end_at")),
        }

    def _available_clubs(tournament_id, skipped=None):
        skipped=set(str(x) for x in (skipped or []))
        clubs,_=_rows(db.table("tournament_clubs").select("*").eq("tournament_id",tournament_id).eq("is_available",True).order("name"),"ops_club_pool")
        return [c for c in clubs if not c.get("selected_by") and str(c.get("id")) not in skipped]

    def _club_assign(tournament_id,user_id,club):
        execute_query(db.table("tournament_clubs").update({"selected_by":user_id,"selected_at":now_iso()}).eq("id",club.get("id")).is_("selected_by","null"),"ops_draft_reserve",attempts=2)
        execute_query(db.table("tournament_members").update({"fixed_club_id":club.get("club_key"),"fixed_club_name":club.get("name")}).eq("tournament_id",tournament_id).eq("user_id",user_id),"ops_draft_member",attempts=2)

    def _club_draft_state(tournament_id, auto_resolve=True):
        state=_setting(tournament_id,"club_draft_v2",{}) or {}
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
        lgstart=_parse_iso(cfg.get("league_start_at"))
        if lgstart and lgstart.tzinfo is None: lgstart=lgstart.replace(tzinfo=vn)
        if lgstart and now>=lgstart and not state.get("league_started"):
            execute_query(db.table("tournament_stages").update({"status":"open","updated_at":now_iso()}).eq("tournament_id",tournament_id).eq("stage_code","league"),"ops_auto_league_stage",attempts=2)
            state["league_started"]=now_iso()
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

    def _event_ops_payload(tournament_id,user_id=None):
        _sync_competition_deadlines(tournament_id)
        cr=_completion_ranking(tournament_id)
        mine=next((x for x in cr if str(x.get("user_id"))==str(user_id)),None) if user_id else None
        s1_reveals=_setting(tournament_id,"stage1_player_reveals",{}) or {}
        league_draw=_league_draw_payload(tournament_id)
        return {"timing":_timing_payload(tournament_id),"completion_ranking":cr,"my_completion":mine,
                "club_draft":_club_draft_state(tournament_id),"stage1_reveals":s1_reveals,"league_draw":league_draw}

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
        matches=_attach_schedule_state(tournament_id,matches,user_id)
        availability=_availability_payload(tournament_id,user_id,matches) if member else {"days":_availability_days(),"mine":[],"mine_set":set(),"status":"missing","slot_count":0}
        hosts,_=_rows(db.table("tournament_hosts").select("*").eq("tournament_id",tournament_id).order("region").order("name"),"ops_hosts")
        clubs,_=_rows(db.table("tournament_clubs").select("*").eq("tournament_id",tournament_id).order("name"),"ops_clubs")
        me_progress=next((r for r in s1 if str(r["user_id"])==str(user_id)),None)
        ops_events=_event_ops_payload(tournament_id,user_id)
        members_all=_all_members(tournament_id)

        # V1.4.123: Host đang rảnh được xác định hoàn toàn tự động.
        # Điều kiện: tài khoản có Host + đang online thật + không nằm trong bất kỳ phòng đấu đang hoạt động nào.
        member_ids={str(hm.get("user_id") or "") for hm in members_all if hm.get("user_id")}
        busy_user_ids=set()
        if member_ids:
            active_room_statuses=["waiting_ready","playing","friendly_playing","waiting_result_confirm","disputed","confirmed"]
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
                if hid in member_ids: busy_user_ids.add(hid)
                if gid in member_ids: busy_user_ids.add(gid)

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
        my_host_profile=next((hm for hm in members_all if str(hm.get("user_id"))==str(user_id)),{})
        c1_test_matches=_c1_test_confirmed_matches(tournament_id)
        c1_test_ranking=_c1_test_ranking(tournament_id)
        return {"tournament":tour,"member":member,"stages":stages,"stage1_ranking":s1,"league_ranking":league,"combined_ranking":_combined_ranking(tournament_id),
                "matches":matches,"hosts":hosts,"clubs":clubs,"me_progress":me_progress,"rewards":_reward_summary(tournament_id,user_id),"availability":availability,
                "host_ready":host_ready,"my_has_host":bool(my_host_profile.get("has_host")),"my_host_ready":False,
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
        matches_per_pot=max(1,int(league_cfg.get("matches_per_pot") or 2))
        league_per_hlv=pot_count*matches_per_pot
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
            # Final is Bo3: 2 matches minimum, 3 maximum.
            if n>=24:
                ko_no_playoff_min,ko_no_playoff_max=30,31
                ko_playoff_min,ko_playoff_max=46,47
            elif n>=16:
                ko_no_playoff_min,ko_no_playoff_max=30,31
                ko_playoff_min,ko_playoff_max=30,31
            elif n>=8:
                ko_no_playoff_min,ko_no_playoff_max=14,15
                ko_playoff_min,ko_playoff_max=14,15
            else:
                ko_no_playoff_min=ko_no_playoff_max=ko_playoff_min=ko_playoff_max=0
            use_playoff=ko_state.get("use_playoff") if ko_state else None
            if use_playoff is True:
                ko_min,ko_max=ko_playoff_min,ko_playoff_max
                knockout_label=f"{ko_min}–{ko_max} trận (có Play-off)" if ko_min!=ko_max else f"{ko_max} trận"
            elif use_playoff is False:
                ko_min,ko_max=ko_no_playoff_min,ko_no_playoff_max
                knockout_label=f"{ko_min}–{ko_max} trận (bỏ Play-off)" if ko_min!=ko_max else f"{ko_max} trận"
            else:
                ko_min=min(ko_no_playoff_min,ko_playoff_min); ko_max=max(ko_no_playoff_max,ko_playoff_max)
                knockout_label=f"{ko_no_playoff_min}–{ko_no_playoff_max} bỏ Play-off / {ko_playoff_min}–{ko_playoff_max} có Play-off" if n>=24 else f"{ko_min}–{ko_max} trận"
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
            "league":{"per_hlv":league_per_hlv,"pot_count":pot_count,"matches_per_pot":matches_per_pot,"planned":league_planned,"actual":actual_by_stage["league"],"completed":completed_by_stage["league"]},
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
        payload.update({"ready":True,"tournament":tour,"members":members,"progress":progress,"combined_ranking":_combined_ranking(tid),"knockout_flow":_setting(tid,"knockout_flow",{}) or {},"scale":_tournament_scale(tid),"c1_test_user_ids":test_ids,"c1_test_users":test_users})
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
        uid=str((current_user() or {}).get("id") or "")
        user=current_user() or {}
        data=_detail_payload(tournament_id,uid)
        data["can_admin_manage_tournament"]=bool(is_admin_user(user)) if data else False
        if not data:
            flash("Không tìm thấy giải đấu.","error"); return redirect(url_for("tournaments"))
        # Admin vào giao diện C1 bằng chính tài khoản Admin, không mượn danh tính HLV khác.
        # Đây chỉ là participant-view ở tầng giao diện; tuyệt đối không insert Admin vào
        # tournament_members và không tạo trận/BXH giả cho Admin. Giữ đủ shape của member
        # để template HLV dùng an toàn, tránh lỗi khi đọc pot_no/fixed_club_name.
        if is_admin_user(user) and not data.get("member"):
            admin_name=(user.get("display_name") or user.get("username") or user.get("name") or "Admin")
            data["member"]={
                "id":None,
                "tournament_id":tournament_id,
                "user_id":uid,
                "display_name":admin_name,
                "username":user.get("username") or "admin",
                "pot_no":None,
                "fixed_club_id":None,
                "fixed_club_name":"",
                "has_host":False,
                "host_region":"",
                "status":"admin_view",
                "is_admin_participant_view":True,
            }
            data["admin_participant_view"]=True
            # Admin xem chính giao diện HLV nhưng không có lịch/trận cá nhân thật.
            # Rebuild các payload phụ theo danh tính Admin để template không dùng dữ liệu
            # của một HLV khác và cũng không phát sinh ghi dữ liệu vào giải.
            # Admin có vùng lịch TEST riêng để thao tác như HLV nhưng không ghi vào
            # tournament_availability_slots của 16 HLV thật.
            days=_availability_days()
            admin_av=_setting(tournament_id,f"admin_test_availability_{uid}",{}) or {}
            allowed={slot["iso"] for day in days for slot in day["slots"]}
            saved_slots=sorted({str(x) for x in (admin_av.get("slots") or []) if str(x) in allowed})
            data["availability"]={
                "days":days,"mine":[],"mine_set":set(saved_slots),
                "status":"active" if saved_slots else "missing",
                "slot_count":len(saved_slots),"day_ranges":{},"day_chips":{},
            }
            data["admin_test_mode"]=True
            data["me_progress"]=None
            data["rewards"]=_reward_summary(tournament_id,uid)
        elif _is_c1_test_user(tournament_id,uid) and not data.get("member"):
            test_name=(user.get("display_name") or user.get("username") or "HLV Test")
            data["member"]={
                "id":None,"tournament_id":tournament_id,"user_id":uid,
                "display_name":test_name,"username":user.get("username") or "test",
                "pot_no":None,"fixed_club_id":None,"fixed_club_name":"",
                "has_host":False,"host_region":"","status":"c1_test",
                "is_c1_test_account":True,
            }
            data["c1_test_account"]=True
            data["admin_participant_view"]=False
            data["availability"]=_c1_test_availability_payload(tournament_id,uid)
            data["c1_test_schedule"]={
                "opponent":data["availability"].get("opponent"),
                "opponent_slots":data["availability"].get("opponent_slots",[]),
                "overlap":data["availability"].get("overlap",[]),
            }
            data["me_progress"]=None
            data["rewards"]={}
        # Animation khai mạc chỉ tự hiện 1 lần/tài khoản HLV sau khi GĐ1 thực sự mở.
        opening_seen=_setting(tournament_id,"opening_seen_v1",{}) or {}
        stage1_open=any(str(x.get("stage_code"))=="stage1" and str(x.get("status"))=="open" for x in (data.get("stages") or []))
        should_show=bool(data.get("member") and stage1_open and uid and not opening_seen.get(uid))
        data["show_opening_animation"]=should_show
        if should_show:
            opening_seen[uid]=now_iso()
            execute_query(db.table("tournament_settings").upsert({"tournament_id":tournament_id,"setting_key":"opening_seen_v1","setting_value":opening_seen,"updated_at":now_iso()},on_conflict="tournament_id,setting_key"),"ops_opening_seen",attempts=2)
        return render_template('tournament_detail.html', **data)


    @app.post('/admin/tournaments/<tournament_id>/c1-test-accounts')
    @login_required
    @admin_required
    @admin_permission_required("system_features_manage")
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
            flash("Không thể dùng HLV chính thức làm tài khoản Test C1. Hãy chọn tài khoản ngoài danh sách 16 HLV.","error")
            return redirect_admin("tournaments")
        valid=[]
        if requested:
            rows,_=_rows(db.table("users").select("id").in_("id",requested),"ops_validate_c1_test_accounts")
            valid=[str(r.get("id")) for r in rows if str(r.get("id") or "") in requested]
        execute_query(db.table("tournament_settings").upsert({
            "tournament_id":tournament_id,"setting_key":C1_TEST_ACCOUNTS_KEY,
            "setting_value":{"user_ids":valid,"updated_at":now_iso()},"updated_at":now_iso(),
        },on_conflict="tournament_id,setting_key"),"ops_save_c1_test_accounts",attempts=2)
        flash(f"Đã lưu {len(valid)} tài khoản Test C1. Các tài khoản này không được thêm vào BXH/trận chính thức.","success")
        return redirect_admin("tournaments")

    @app.get('/admin/tournaments/<tournament_id>/preview-player')
    @login_required
    @admin_required
    @admin_permission_required("system_features_manage")
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
    @admin_permission_required("system_features_manage")
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
        target=max(1,min(20,int(request.form.get("match_target") or 6)))
        min_opp=max(1,min(target,int(request.form.get("min_opponents") or 3)))
        max_same=max(1,min(target,int(request.form.get("max_per_opponent") or 2)))
        execute_query(db.table("tournament_stages").update({"match_target":target,"min_opponents":min_opp,"max_matches_per_opponent":max_same,"updated_at":now_iso()}).eq("tournament_id",tournament_id).eq("stage_code","stage1"),"ops_stage1_settings",attempts=2)
        flash("Đã lưu luật GĐ1.","success"); return redirect_admin("tournaments")

    @app.post('/admin/tournaments/<tournament_id>/stage1/clubs')
    @login_required
    @admin_required
    @admin_permission_required("system_features_manage")
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
    @admin_permission_required("system_features_manage")
    def admin_tournament_stage1_clubs_reset(tournament_id):
        defaults=_default_stage1_clubs()
        execute_query(db.table("tournament_settings").upsert({"tournament_id":tournament_id,"setting_key":"stage1_club_pool","setting_value":{"clubs":defaults,"updated_at":now_iso()},"updated_at":now_iso()},on_conflict="tournament_id,setting_key"),"ops_stage1_club_pool_reset",attempts=2)
        flash(f"Đã chọn lại {len(defaults)} CLB Tier S+ và S mạnh nhất cho C1.","success"); return redirect_admin("tournaments")

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
        if match.get("stage_code")=="knockout":
            try: _maybe_advance_knockout(match.get("tournament_id"))
            except Exception as exc: app.logger.warning("Knockout auto advance failed: %s",exc)
        log_admin_action("Cập nhật kết quả trận giải","tournament_match",details={"match_id":match_id,"score":f"{hs}-{aw}"})
        flash("Đã lưu kết quả trận giải.","success")
        if (request.form.get("return_to") or "").strip() == "tournament":
            return redirect(url_for("tournament_detail", tournament_id=match.get("tournament_id")) + "#bxh")
        return redirect_admin("tournaments")

    @app.post('/admin/tournaments/<tournament_id>/pot/generate')
    @login_required
    @admin_required
    @admin_permission_required("system_features_manage")
    def admin_tournament_generate_pots(tournament_id):
        pot_count=max(1,min(8,int(request.form.get("pot_count") or 4)))
        club_count=max(2,min(64,int(request.form.get("club_count") or len(_all_members(tournament_id)) or 10)))
        league_cfg=_setting(tournament_id,"league_config",{}) or {}
        league_cfg["club_count"]=club_count
        league_cfg["pot_count"]=pot_count
        execute_query(db.table("tournament_settings").upsert({"tournament_id":tournament_id,"setting_key":"league_config","setting_value":league_cfg,"updated_at":now_iso()},on_conflict="tournament_id,setting_key"),"ops_league_config_pot_clubs",attempts=2)
        ranking=_ranking(tournament_id,"stage1")
        if not ranking:
            flash("Chưa có HLV để chia Pot.","error"); return redirect_admin("tournaments")
        size=(len(ranking)+pot_count-1)//pot_count
        for i,row in enumerate(ranking):
            pot=min(pot_count,(i//size)+1)
            execute_query(db.table("tournament_members").update({"pot_no":pot,"seed_no":i+1}).eq("tournament_id",tournament_id).eq("user_id",row["user_id"]),"ops_pot_update",attempts=2)
        execute_query(db.table("tournament_settings").upsert({"tournament_id":tournament_id,"setting_key":"pots_locked","setting_value":{"locked":False,"pot_count":pot_count},"updated_at":now_iso()},on_conflict="tournament_id,setting_key"),"ops_pot_setting",attempts=2)
        flash(f"Đã cấu hình GĐ2: {pot_count} Pot · {club_count} CLB và chia Pot theo BXH GĐ1.","success"); return redirect_admin("tournaments")

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
            result=meta.get("test_result") or {}
            if str(result.get("status") or "")!="confirmed":
                continue
            try:
                hs=int(result.get("host_score") if result.get("host_score") is not None else room.get("host_score") or 0)
                gs=int(result.get("guest_score") if result.get("guest_score") is not None else room.get("guest_score") or 0)
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
        return render_template("c1_rooms.html",tournament=selected,member=member,members=members,is_c1_admin=is_admin_user(user))

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
        row=execute_query(db.table("match_rooms").insert({
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
                flash("Phòng Test C1 chỉ được mời tài khoản Test C1 còn lại.","error"); return redirect(url_for("room_detail",room_id=room_id))
            match=None
        else:
            opponent=next((m for m in members if str(m.get("user_id"))==opponent_uid),None)
            if not opponent or opponent_uid==host_uid:
                flash("Chỉ được mời HLV đang tham gia C1.","error"); return redirect(url_for("room_detail",room_id=room_id))
            match=_c1_pair_match(tournament_id,host_uid,opponent_uid)
            host_member=next((m for m in members if str(m.get("user_id"))==host_uid),None)
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
        meta["invited_user_id"]=opponent_uid
        execute_query(db.table("match_rooms").update({"note":_room_note(meta),"match_mode":"tournament","team_tier":"TOURNAMENT","updated_at":now_iso()}).eq("id",room_id),"ops_c1_room_bind_invite",attempts=2)
        creator=(host_member or {}).get("display_name") or user.get("display_name") or user.get("username") or "Admin"
        try:
            create_user_notification(opponent_uid,"🏆 Lời mời thi đấu C1",f"{creator} đang mời bạn vào Phòng đấu C1.",url_for("c1_room_accept",tournament_id=tournament_id,room_id=room_id),"tournament_room_invite")
            flash(f"Đã gửi lời mời tới {opponent.get('display_name') or 'HLV'}.","success")
        except Exception as exc:
            app.logger.warning("Không gửi được lời mời C1: %s",exc)
            flash("Đã chọn đối thủ nhưng không gửi được thông báo. Hãy bảo đối thủ mở Phòng đấu C1.","warning")
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
        if not is_admin_user(user) and not _member(tournament_id,uid) and not (meta.get("test_sandbox_room") and _is_c1_test_user(tournament_id,uid)):
            flash("Chỉ HLV chính thức hoặc tài khoản Test C1 được cấp quyền mới vào phòng.","error"); return redirect(url_for("tournaments"))
        if room.get("guest_user_id") and str(room.get("guest_user_id"))!=uid:
            flash("Phòng đã đủ 2 HLV.","warning"); return redirect(url_for("c1_rooms",tournament_id=tournament_id))
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
        execute_query(db.table("match_rooms").update({"guest_user_id":uid,"guest_ready":False,"updated_at":now_iso()}).eq("id",room_id),"ops_c1_room_accept",attempts=2)
        flash("Đã vào Phòng đấu C1. Hãy bấm Sẵn sàng khi chuẩn bị xong.","success")
        return redirect(url_for("room_detail",room_id=room_id))

    @app.post('/tournaments/<tournament_id>/matches/<match_id>/room')
    @login_required
    def tournament_match_room_enter(tournament_id,match_id):
        user=current_user() or {}; uid=str(user.get("id") or "")
        match,_=_one(db.table("tournament_matches").select("*").eq("id",match_id).eq("tournament_id",tournament_id),"ops_tournament_room_match")
        if not match or uid not in {str(match.get("home_user_id")),str(match.get("away_user_id"))}:
            flash("Bạn không thuộc trận đấu này.","error"); return redirect(url_for("tournament_detail",tournament_id=tournament_id)+"#rooms")
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
                if existing.get("status")=="friendly_playing": patch["status"]="playing"
                if guest_id and guest_id not in allowed:
                    patch.update({"guest_user_id":None,"guest_ready":False,"guest_team":None,"guest_team_overall":None})
                    guest_id=""
                execute_query(db.table("match_rooms").update(patch).eq("id",existing.get("id")),"ops_tournament_room_normalize",attempts=2)
                if uid not in {host_id,guest_id}:
                    if guest_id:
                        flash("Phòng đã đủ 2 HLV.","warning"); return redirect(url_for("tournament_detail",tournament_id=tournament_id)+"#rooms")
                    execute_query(db.table("match_rooms").update({"guest_user_id":uid,"guest_ready":True,"updated_at":now_iso()}).eq("id",existing.get("id")),"ops_tournament_room_join",attempts=2)
                return redirect(url_for("room_detail",room_id=existing.get("id")))
        active=active_room_for_user(uid)
        if active:
            flash("Bạn đang ở một phòng đấu khác. Hãy thoát phòng đó trước.","warning"); return redirect(url_for("room_detail",room_id=active.get("id")))
        dm=_decorate_matches(tournament_id,[match])[0]
        meta={"tournament_id":str(tournament_id),"tournament_match_id":str(match_id),"stage_code":match.get("stage_code"),"home_user_id":str(match.get("home_user_id")),"away_user_id":str(match.get("away_user_id")),"home_name":dm.get("home_name"),"away_name":dm.get("away_name")}
        row=execute_query(db.table("match_rooms").insert({"invite_id":None,"host_user_id":uid,"guest_user_id":None,"team_tier":"TOURNAMENT_GD1" if match.get("stage_code")=="stage1" else "TOURNAMENT","match_mode":"tournament","friendly_tier":None,"status":"waiting_ready","guest_ready":False,"note":_room_note(meta),"state_expires_at":None,"updated_at":now_iso()}),"ops_tournament_room_create",attempts=2)
        room=(row.data or [{}])[0]
        flash("Đã tạo Phòng đấu C1. Khi sẵn sàng, hãy bấm Mời đối thủ ngay trong phòng.","success")
        return redirect(url_for("room_detail",room_id=room.get("id")))

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
        try:
            create_user_notification(
                opponent_uid,
                "🏆 Lời mời thi đấu C1",
                f"{creator} đang chờ bạn trong Phòng đấu C1. Bấm để vào phòng thi đấu.",
                url_for("tournament_match_room_enter", tournament_id=tournament_id, match_id=match.get("id")),
                "tournament_room_invite",
            )
            flash(f"Đã gửi lời mời tới {opponent_name or 'đối thủ'}.","success")
        except Exception as exc:
            app.logger.warning("Không gửi được lời mời phòng C1: %s", exc)
            flash("Không gửi được thông báo mời. Đối thủ vẫn có thể vào từ tab Phòng đấu C1.","warning")
        return redirect(url_for("room_detail",room_id=room_id))

    @app.post('/tournaments/<tournament_id>/rooms/<room_id>/random-stage1-clubs')
    @login_required
    def tournament_room_random_stage1_clubs(tournament_id,room_id):
        user=current_user() or {}; uid=str(user.get("id") or "")
        room=get_room(room_id); meta=_room_meta(room)
        if not room or not meta or str(meta.get("tournament_id"))!=str(tournament_id):
            flash("Không tìm thấy phòng GĐ1.","error"); return redirect(url_for("tournament_detail",tournament_id=tournament_id)+"#rooms")
        if uid not in {str(room.get("host_user_id")),str(room.get("guest_user_id"))}:
            flash("Bạn không thuộc phòng này.","error"); return redirect(url_for("tournament_detail",tournament_id=tournament_id)+"#rooms")
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
            flash("Không tìm thấy phòng/trận giải.","error"); return redirect(url_for("tournament_detail",tournament_id=tournament_id))
        if uid!=str(room.get("host_user_id")) and not is_admin_user(user):
            flash("Chỉ chủ phòng mới được nhập kết quả.","error"); return redirect(url_for("room_detail",room_id=room_id))
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
            flash("Không tìm thấy phòng/trận giải.","error"); return redirect(url_for("tournament_detail",tournament_id=tournament_id))
        if uid!=str(room.get("guest_user_id")) and not is_admin_user(user):
            flash("Chỉ đối thủ mới được xác nhận kết quả.","error"); return redirect(url_for("room_detail",room_id=room_id))
        prop=_tournament_result_proposal(tournament_id,match.get("id"))
        if prop.get("status")!="waiting_confirm":
            flash("Không có kết quả nào đang chờ xác nhận.","warning"); return redirect(url_for("room_detail",room_id=room_id))
        hs=int(prop.get("home_score") or 0); aw=int(prop.get("away_score") or 0)
        winner=match.get("home_user_id") if hs>aw else (match.get("away_user_id") if aw>hs else None)
        execute_query(db.table("tournament_matches").update({"home_score":hs,"away_score":aw,"winner_user_id":winner,"status":"completed","completed_at":now_iso(),"updated_at":now_iso()}).eq("id",match.get("id")),"ops_tournament_result_confirm",attempts=2)
        prop.update({"status":"confirmed","confirmed_by":uid,"confirmed_at":now_iso()}); _save_tournament_result_proposal(tournament_id,match.get("id"),prop)
        execute_query(db.table("match_rooms").update({"status":"confirmed","updated_at":now_iso()}).eq("id",room_id),"ops_tournament_room_confirmed",attempts=2)
        flash("Đã xác nhận kết quả. BXH giải đã được cập nhật.","success")
        return redirect(url_for("room_detail",room_id=room_id))

    @app.post('/tournaments/<tournament_id>/rooms/<room_id>/dispute-result')
    @login_required
    def tournament_room_dispute_result(tournament_id,room_id):
        user=current_user() or {}; uid=str(user.get("id") or "")
        room,meta,match=_room_match_or_error(tournament_id,room_id)
        if not room or not match:
            flash("Không tìm thấy phòng/trận giải.","error"); return redirect(url_for("tournament_detail",tournament_id=tournament_id))
        if uid!=str(room.get("guest_user_id")) and not is_admin_user(user):
            flash("Chỉ đối thủ mới được báo sai kết quả.","error"); return redirect(url_for("room_detail",room_id=room_id))
        prop=_tournament_result_proposal(tournament_id,match.get("id"))
        prop.update({"status":"disputed","disputed_by":uid,"disputed_at":now_iso(),"reason":(request.form.get("reason") or "Sai kết quả").strip()[:300]})
        _save_tournament_result_proposal(tournament_id,match.get("id"),prop)
        execute_query(db.table("tournament_matches").update({"status":"disputed","updated_at":now_iso()}).eq("id",match.get("id")),"ops_tournament_result_dispute",attempts=2)
        execute_query(db.table("match_rooms").update({"status":"disputed","updated_at":now_iso()}).eq("id",room_id),"ops_tournament_room_dispute",attempts=2)
        flash("Đã báo sai kết quả. Admin sẽ xử lý.","warning")
        return redirect(url_for("room_detail",room_id=room_id))

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
            flash("Chỉ chủ phòng Test C1 được gửi kết quả.","error"); return redirect(url_for("room_detail",room_id=room_id))
        if not room.get("guest_user_id"):
            flash("Phòng Test chưa đủ 2 người.","warning"); return redirect(url_for("room_detail",room_id=room_id))
        try:
            hs=max(0,min(99,int(request.form.get("host_score") or 0))); gs=max(0,min(99,int(request.form.get("guest_score") or 0)))
        except Exception:
            flash("Tỷ số không hợp lệ.","error"); return redirect(url_for("room_detail",room_id=room_id))
        meta["test_result"]={"status":"waiting_confirm","host_score":hs,"guest_score":gs,"submitted_by":uid,"submitted_at":now_iso()}
        execute_query(db.table("match_rooms").update({"host_score":hs,"guest_score":gs,"status":"waiting_result_confirm","note":_room_note(meta),"updated_at":now_iso()}).eq("id",room_id),"ops_c1_test_submit_result",attempts=2)
        flash("Đã gửi kết quả TEST. Chờ tài khoản Test còn lại xác nhận.","success")
        return redirect(url_for("room_detail",room_id=room_id))

    @app.post('/tournaments/<tournament_id>/rooms/<room_id>/test-confirm-result')
    @login_required
    def c1_test_room_confirm_result(tournament_id,room_id):
        user=current_user() or {}; uid=str(user.get("id") or "")
        room,meta=_c1_test_room_or_error(tournament_id,room_id)
        if not room or uid!=str(room.get("guest_user_id") or "") or not _is_c1_test_user(tournament_id,uid):
            flash("Chỉ đối thủ Test C1 được xác nhận.","error"); return redirect(url_for("room_detail",room_id=room_id))
        result=meta.get("test_result") or {}
        if result.get("status")!="waiting_confirm":
            flash("Không có kết quả Test đang chờ xác nhận.","warning"); return redirect(url_for("room_detail",room_id=room_id))
        result.update({"status":"confirmed","confirmed_by":uid,"confirmed_at":now_iso()}); meta["test_result"]=result
        execute_query(db.table("match_rooms").update({"status":"confirmed","note":_room_note(meta),"updated_at":now_iso()}).eq("id",room_id),"ops_c1_test_confirm_result",attempts=2)
        flash("Đã xác nhận kết quả TEST. BXH TEST C1 đã cập nhật, nhưng không ảnh hưởng BXH C1 thật hoặc Rank.","success")
        return redirect(url_for("room_detail",room_id=room_id))

    @app.post('/tournaments/<tournament_id>/rooms/<room_id>/test-dispute-result')
    @login_required
    def c1_test_room_dispute_result(tournament_id,room_id):
        user=current_user() or {}; uid=str(user.get("id") or "")
        room,meta=_c1_test_room_or_error(tournament_id,room_id)
        if not room or uid!=str(room.get("guest_user_id") or "") or not _is_c1_test_user(tournament_id,uid):
            flash("Chỉ đối thủ Test C1 được báo sai kết quả.","error"); return redirect(url_for("room_detail",room_id=room_id))
        result=meta.get("test_result") or {}
        result.update({"status":"disputed","disputed_by":uid,"disputed_at":now_iso(),"reason":(request.form.get("reason") or "Sai kết quả").strip()[:300]}); meta["test_result"]=result
        execute_query(db.table("match_rooms").update({"status":"disputed","note":_room_note(meta),"updated_at":now_iso()}).eq("id",room_id),"ops_c1_test_dispute_result",attempts=2)
        flash("Đã tạo tranh chấp TEST. Không ảnh hưởng trận/BXH thật.","warning")
        return redirect(url_for("room_detail",room_id=room_id))

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
        execute_query(db.table("tournament_settings").upsert({"tournament_id":tournament_id,"setting_key":"league_config","setting_value":{"matches_per_pot":k},"updated_at":now_iso()},on_conflict="tournament_id,setting_key"),"ops_league_config",attempts=2)
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

    @app.post('/admin/tournaments/<tournament_id>/registration-status')
    @login_required
    @admin_required
    @admin_permission_required("system_features_manage")
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
    @admin_permission_required("system_features_manage")
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
    @admin_permission_required("system_features_manage")
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
    @admin_permission_required("system_features_manage")
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

    @app.post('/tournaments/<tournament_id>/stage1/reveal')
    @login_required
    def tournament_stage1_reveal(tournament_id):
        uid=str((current_user() or {}).get("id") or "")
        if not _member(tournament_id,uid):
            flash("Bạn chưa thuộc giải đấu này.","error"); return redirect(url_for("tournament_detail",tournament_id=tournament_id))
        data=_setting(tournament_id,"stage1_player_reveals",{}) or {}; data[uid]=now_iso()
        execute_query(db.table("tournament_settings").upsert({"tournament_id":tournament_id,"setting_key":"stage1_player_reveals","setting_value":data,"updated_at":now_iso()},on_conflict="tournament_id,setting_key"),"ops_s1_reveal",attempts=2)
        return redirect(url_for("tournament_detail",tournament_id=tournament_id)+"#stage1")

    @app.post('/admin/tournaments/<tournament_id>/club-draft/start')
    @login_required
    @admin_required
    @admin_permission_required("system_features_manage")
    def admin_tournament_club_draft_start(tournament_id):
        ranking=[x for x in _completion_ranking(tournament_id) if x.get("eligible") and x.get("early_eligible")][:10]
        order=[str(x.get("user_id")) for x in ranking]
        entries={}
        for i,row in enumerate(ranking,1):
            tickets=3 if i==1 else (2 if i<=3 else 1)
            entries[str(row.get("user_id"))]={"tickets_total":tickets,"tickets_remaining":tickets,"skipped":[],"candidate":None,"status":"waiting","finish_rank":i}
        if not order:
            flash("Chưa có HLV để mở chọn CLB.","error"); return redirect_admin("tournaments")
        entries[order[0]]["status"]="active"
        state={"active":True,"completed":False,"order":order,"current_index":0,"entries":entries,"history":[{"at":now_iso(),"user_id":order[0],"action":"TURN_OPEN","message":"Mở lượt Top 1 (10 phút)."}],"deadline_at":(datetime.now(timezone(timedelta(hours=7)))+timedelta(minutes=10)).isoformat()}
        execute_query(db.table("tournament_settings").upsert({"tournament_id":tournament_id,"setting_key":"club_draft_v2","setting_value":state,"updated_at":now_iso()},on_conflict="tournament_id,setting_key"),"ops_draft_start",attempts=2)
        flash("Đã mở sự kiện chọn CLB Top 10. Top 1 có 10 phút; Top 2–10 có 5 phút.","success"); return redirect_admin("tournaments")

    @app.post('/tournaments/<tournament_id>/club-draft/random')
    @login_required
    def tournament_club_draft_random(tournament_id):
        uid=str((current_user() or {}).get("id") or ""); state=_club_draft_state(tournament_id)
        idx=int(state.get("current_index") or 0); order=state.get("order") or []
        if not state.get("active") or idx>=len(order) or str(order[idx])!=uid:
            flash("Chưa tới lượt Random CLB của bạn.","warning"); return redirect(url_for("tournament_detail",tournament_id=tournament_id)+"#club")
        entry=state["entries"].get(uid) or {}; old=entry.get("candidate")
        if old:
            if int(entry.get("tickets_remaining") or 0)<=0:
                flash("Bạn đã hết vé Random. Hãy chốt CLB hiện tại.","warning"); return redirect(url_for("tournament_detail",tournament_id=tournament_id)+"#club")
            entry.setdefault("skipped",[]).append(str(old.get("id"))); entry["tickets_remaining"]=int(entry.get("tickets_remaining") or 0)-1
            state.setdefault("history",[]).append({"at":now_iso(),"user_id":uid,"action":"SKIP","club":old.get("name"),"message":f"Bỏ qua {old.get('name')} · dùng 1 vé Random."})
        pool=_available_clubs(tournament_id,entry.get("skipped") or [])
        if not pool:
            flash("Không còn CLB phù hợp trong Pool.","error"); return redirect(url_for("tournament_detail",tournament_id=tournament_id)+"#club")
        club=random.choice(pool); entry["candidate"]={"id":str(club.get("id")),"name":club.get("name")}; entry["status"]="active"; state["entries"][uid]=entry
        state.setdefault("history",[]).append({"at":now_iso(),"user_id":uid,"action":"RANDOM","club":club.get("name"),"message":f"Random ra {club.get('name')}."})
        execute_query(db.table("tournament_settings").upsert({"tournament_id":tournament_id,"setting_key":"club_draft_v2","setting_value":state,"updated_at":now_iso()},on_conflict="tournament_id,setting_key"),"ops_draft_random_save",attempts=2)
        return redirect(url_for("tournament_detail",tournament_id=tournament_id)+"#club")

    def _advance_draft(tournament_id,state,uid,club,action="SELECT"):
        _club_assign(tournament_id,uid,club)
        entry=state["entries"].get(uid) or {}; entry["status"]="selected"; entry["selected_club"]=club.get("name"); entry["candidate"]={"id":str(club.get("id")),"name":club.get("name")}; state["entries"][uid]=entry
        state.setdefault("history",[]).append({"at":now_iso(),"user_id":uid,"action":action,"club":club.get("name"),"message":f"Chốt {club.get('name')}."})
        state["current_index"]=int(state.get("current_index") or 0)+1
        if state["current_index"]<len(state.get("order") or []):
            nxt=str(state["order"][state["current_index"]]); state["entries"][nxt]["status"]="active"; mins=5
            state["deadline_at"]=(datetime.now(timezone(timedelta(hours=7)))+timedelta(minutes=mins)).isoformat(); state.setdefault("history",[]).append({"at":now_iso(),"user_id":nxt,"action":"TURN_OPEN","message":"Mở lượt HLV tiếp theo (5 phút)."})
        else:
            state["active"]=False; state["completed"]=True; state["deadline_at"]=None
        execute_query(db.table("tournament_settings").upsert({"tournament_id":tournament_id,"setting_key":"club_draft_v2","setting_value":state,"updated_at":now_iso()},on_conflict="tournament_id,setting_key"),"ops_draft_advance",attempts=2)

    @app.post('/tournaments/<tournament_id>/club-draft/accept')
    @login_required
    def tournament_club_draft_accept(tournament_id):
        uid=str((current_user() or {}).get("id") or ""); state=_club_draft_state(tournament_id); idx=int(state.get("current_index") or 0); order=state.get("order") or []
        if not state.get("active") or idx>=len(order) or str(order[idx])!=uid:
            flash("Chưa tới lượt của bạn.","warning"); return redirect(url_for("tournament_detail",tournament_id=tournament_id)+"#club")
        entry=state["entries"].get(uid) or {}; candidate=entry.get("candidate")
        if not candidate:
            flash("Hãy Random CLB trước.","warning"); return redirect(url_for("tournament_detail",tournament_id=tournament_id)+"#club")
        club,_=_one(db.table("tournament_clubs").select("*").eq("id",candidate.get("id")),"ops_draft_accept_lookup")
        if not club or club.get("selected_by"):
            flash("CLB này vừa không còn trống, hãy Random lại.","error"); return redirect(url_for("tournament_detail",tournament_id=tournament_id)+"#club")
        _advance_draft(tournament_id,state,uid,club)
        flash(f"Đã chốt {club.get('name')}.","success"); return redirect(url_for("tournament_detail",tournament_id=tournament_id)+"#club")

    @app.post('/admin/tournaments/<tournament_id>/club-draft/force')
    @login_required
    @admin_required
    @admin_permission_required("system_features_manage")
    def admin_tournament_club_draft_force(tournament_id):
        state=_club_draft_state(tournament_id,False); idx=int(state.get("current_index") or 0); order=state.get("order") or []
        if not state.get("active") or idx>=len(order):
            flash("Không có lượt chọn CLB đang hoạt động.","warning"); return redirect_admin("tournaments")
        uid=str(order[idx]); entry=state["entries"].get(uid) or {}; pool=_available_clubs(tournament_id,entry.get("skipped") or [])
        if not pool:
            flash("Không còn CLB để Random thay.","error"); return redirect_admin("tournaments")
        club=random.choice(pool); state.setdefault("history",[]).append({"at":now_iso(),"user_id":uid,"action":"ADMIN_RANDOM","club":club.get("name"),"message":f"Admin Random thay: {club.get('name')}."}); _advance_draft(tournament_id,state,uid,club,"ADMIN_SELECT")
        flash("Đã Random/chốt thay và chuyển lượt.","success"); return redirect_admin("tournaments")

    @app.post('/admin/tournaments/<tournament_id>/clubs/assign-remaining')
    @login_required
    @admin_required
    @admin_permission_required("system_features_manage")
    def admin_tournament_assign_remaining_clubs(tournament_id):
        members=[m for m in _all_members(tournament_id) if not m.get("fixed_club_name")]
        random.shuffle(members); count=0
        for m in members:
            pool=_available_clubs(tournament_id)
            if not pool: break
            club=random.choice(pool); _club_assign(tournament_id,str(m.get("user_id")),club); count+=1
        flash(f"Đã Random CLB cho {count} HLV còn lại.","success"); return redirect_admin("tournaments")

    @app.post('/admin/tournaments/<tournament_id>/league-draw/start')
    @login_required
    @admin_required
    @admin_permission_required("system_features_manage")
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
    @admin_permission_required("system_features_manage")
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
        if pi>=len(pots): pi=0; i+=1
        state["pot_index"]=pi; state["current_index"]=i
        if i>=len(order): state["active"]=False; state["completed"]=True
        execute_query(db.table("tournament_settings").upsert({"tournament_id":tournament_id,"setting_key":"league_draw_v2","setting_value":state,"updated_at":now_iso()},on_conflict="tournament_id,setting_key"),"ops_league_draw_next",attempts=2)
        flash(f"Đã bốc POT {pot} cho HLV hiện tại.","success"); return redirect_admin("tournaments")

    @app.post('/tournaments/<tournament_id>/league/reveal')
    @login_required
    def tournament_league_reveal(tournament_id):
        uid=str((current_user() or {}).get("id") or ""); draw=_setting(tournament_id,"league_draw_v2",{}) or {}
        if not (draw.get("revealed") or {}).get(uid):
            flash("Đối thủ League Phase của bạn chưa được Admin bốc xong.","warning"); return redirect(url_for("tournament_detail",tournament_id=tournament_id)+"#league")
        data=_setting(tournament_id,"league_player_reveals",{}) or {}; data[uid]=now_iso()
        execute_query(db.table("tournament_settings").upsert({"tournament_id":tournament_id,"setting_key":"league_player_reveals","setting_value":data,"updated_at":now_iso()},on_conflict="tournament_id,setting_key"),"ops_league_reveal",attempts=2)
        return redirect(url_for("tournament_detail",tournament_id=tournament_id)+"#league")

    @app.post('/tournaments/<tournament_id>/availability')
    @login_required
    def tournament_availability_save(tournament_id):
        uid=(current_user() or {}).get("id")
        if not _member(tournament_id,uid):
            flash("Bạn chưa phải HLV của giải đấu này.","error"); return redirect(url_for("tournament_detail",tournament_id=tournament_id)+"#schedule")
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
        return redirect(url_for("tournament_detail",tournament_id=tournament_id)+"#schedule")

    @app.post('/admin/tournaments/<tournament_id>/test-availability/simple')
    @login_required
    def admin_tournament_test_availability_simple_save(tournament_id):
        user=current_user() or {}
        uid=str(user.get("id") or "")
        is_test=_is_c1_test_user(tournament_id,uid)
        if not is_admin_user(user) and not is_test:
            flash("Bạn không có quyền lưu lịch Test C1.","error")
            return redirect(url_for("tournament_detail",tournament_id=tournament_id)+"#schedule")
        allowed={slot["iso"] for day in _availability_days() for slot in day["slots"]}
        selected=[]
        for raw in request.form.getlist("slots"):
            try:
                iso=datetime.fromisoformat(str(raw)).isoformat()
                if iso in allowed:
                    selected.append(iso)
            except Exception:
                continue
        key=f"c1_test_availability_{uid}" if is_test else f"admin_test_availability_{uid}"
        previous=_setting(tournament_id,key,{}) or {}
        custom_existing=[str(x) for x in (previous.get("slots") or []) if str(x) not in allowed]
        selected=sorted(set(selected+custom_existing))
        execute_query(
            db.table("tournament_settings").upsert({
                "tournament_id":tournament_id,
                "setting_key":key,
                "setting_value":{"slots":selected,"updated_at":now_iso()},
                "updated_at":now_iso(),
            },on_conflict="tournament_id,setting_key"),
            "ops_admin_test_availability",attempts=2,
        )
        flash(f"Đã lưu {len(selected)} khung giờ TEST. Giờ linh hoạt đã thêm trước đó vẫn được giữ nguyên.","success")
        return redirect(url_for("tournament_detail",tournament_id=tournament_id)+"#schedule")

    @app.post('/tournaments/<tournament_id>/availability/simple')
    @login_required
    def tournament_availability_simple_save(tournament_id):
        uid=(current_user() or {}).get("id")
        if not _member(tournament_id,uid):
            flash("Bạn chưa phải HLV của giải đấu này.","error"); return redirect(url_for("tournament_detail",tournament_id=tournament_id)+"#schedule")
        vn_tz=timezone(timedelta(hours=7)); now=datetime.now(vn_tz)
        allowed_days={d["date"]:d for d in _availability_days()}
        final_slots=[]
        for idx,d in enumerate(_availability_days()):
            start_raw=(request.form.get(f"start_{idx}") or "").strip()
            end_raw=(request.form.get(f"end_{idx}") or "").strip()
            if not start_raw and not end_raw:
                continue
            if not start_raw or not end_raw:
                flash(f"{d['label']}: hãy chọn đủ giờ Từ và Đến.","warning"); return redirect(url_for("tournament_detail",tournament_id=tournament_id)+"#schedule")
            try:
                day=datetime.fromisoformat(d["date"]).date()
                sh,sm=[int(x) for x in start_raw.split(":",1)]
                eh,em=[int(x) for x in end_raw.split(":",1)]
                start=datetime(day.year,day.month,day.day,sh,sm,tzinfo=vn_tz)
                end=datetime(day.year,day.month,day.day,eh,em,tzinfo=vn_tz)
            except Exception:
                flash(f"{d['label']}: giờ không hợp lệ.","error"); return redirect(url_for("tournament_detail",tournament_id=tournament_id)+"#schedule")
            if end<start:
                flash(f"{d['label']}: giờ Đến phải sau giờ Từ.","warning"); return redirect(url_for("tournament_detail",tournament_id=tournament_id)+"#schedule")
            cursor=start.replace(second=0,microsecond=0)
            count=0
            while cursor<=end and count<49:
                if cursor>now: final_slots.append(cursor.isoformat())
                cursor += timedelta(hours=1); count += 1
        final_slots=sorted(set(final_slots))
        execute_query(db.table("tournament_availability_slots").delete().eq("tournament_id",tournament_id).eq("user_id",uid),"ops_availability_simple_clear",attempts=2)
        for iso in final_slots:
            execute_query(db.table("tournament_availability_slots").insert({"tournament_id":tournament_id,"user_id":uid,"slot_at":iso,"created_at":now_iso(),"updated_at":now_iso()}),"ops_availability_simple_insert",attempts=2)
        flash(f"Đã lưu lịch thi đấu: {len(final_slots)} mốc giờ trong 3 ngày gần nhất.","success")
        return redirect(url_for("tournament_detail",tournament_id=tournament_id)+"#schedule")

    @app.post('/tournaments/<tournament_id>/availability/custom')
    @login_required
    def tournament_availability_custom_add(tournament_id):
        user=current_user() or {}
        uid=str(user.get("id") or "")
        member=_member(tournament_id,uid)
        is_test=_is_c1_test_user(tournament_id,uid)
        is_admin_view=is_admin_user(user) and not member
        if not member and not is_test and not is_admin_view:
            flash("Bạn chưa phải HLV của giải đấu này.","error"); return redirect(url_for("tournament_detail",tournament_id=tournament_id)+"#schedule")
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
            flash("Giờ linh hoạt không hợp lệ.","error"); return redirect(url_for("tournament_detail",tournament_id=tournament_id)+"#schedule")
        allowed_days={d["date"] for d in _availability_days()}
        if day.isoformat() not in allowed_days or end<=start:
            flash("Hãy chọn Hôm nay, Ngày mai hoặc Ngày kia và giờ kết thúc phải sau giờ bắt đầu.","warning"); return redirect(url_for("tournament_detail",tournament_id=tournament_id)+"#schedule")
        # Bước 30 phút để hỗ trợ giờ linh hoạt, ví dụ 18:30–20:30.
        slots=[]; cursor=start.replace(second=0,microsecond=0)
        while cursor<=end and len(slots)<49:
            if cursor>now: slots.append(cursor.isoformat())
            cursor += timedelta(minutes=30)
        if not slots:
            flash("Khoảng giờ này đã qua hoặc không còn giờ hợp lệ.","warning"); return redirect(url_for("tournament_detail",tournament_id=tournament_id)+"#schedule")
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
        return redirect(url_for("tournament_detail",tournament_id=tournament_id)+"#schedule")

    @app.post('/tournaments/<tournament_id>/host-ready')
    @login_required
    def tournament_host_ready_toggle(tournament_id):
        uid=str((current_user() or {}).get("id") or "")
        prof=next((x for x in _all_members(tournament_id) if str(x.get("user_id"))==uid),None)
        if not prof or not prof.get("has_host"):
            flash("Chỉ HLV đã đăng ký có Host mới dùng được mục này.","warning"); return redirect(url_for("tournament_detail",tournament_id=tournament_id)+"#rooms")
        state=_setting(tournament_id,"host_live_ready",{}) or {}
        ready=(request.form.get("ready") or "") in {"1","true","on","yes"}
        if ready: state[uid]=now_iso()
        else: state.pop(uid,None)
        execute_query(db.table("tournament_settings").upsert({"tournament_id":tournament_id,"setting_key":"host_live_ready","setting_value":state,"updated_at":now_iso()},on_conflict="tournament_id,setting_key"),"ops_host_live_ready",attempts=2)
        flash("Đã cập nhật trạng thái Host đang rảnh.","success")
        return redirect(url_for("tournament_detail",tournament_id=tournament_id)+"#rooms")

    @app.post('/tournaments/matches/<match_id>/schedule-from-availability')
    @login_required
    def tournament_schedule_from_availability(match_id):
        uid=(current_user() or {}).get("id")
        match,_=_one(db.table("tournament_matches").select("*").eq("id",match_id),"ops_availability_match")
        if not match or str(uid) not in {str(match.get("home_user_id")),str(match.get("away_user_id"))}:
            flash("Bạn không thuộc trận này.","error"); return redirect(url_for("tournaments"))
        slot=(request.form.get("slot_at") or "").strip()
        if not slot:
            flash("Hãy chọn một khung giờ trùng.","error"); return redirect(url_for("tournament_detail",tournament_id=match.get("tournament_id"))+"#schedule")
        rows=_availability_rows(match.get("tournament_id"),[match.get("home_user_id"),match.get("away_user_id")])
        users_at={str(r.get("user_id")) for r in rows if r.get("slot_iso")==slot}
        required={str(match.get("home_user_id")),str(match.get("away_user_id"))}
        if not required.issubset(users_at):
            flash("Khung giờ này không còn trùng lịch của cả hai HLV. Hãy tải lại lịch.","warning")
            return redirect(url_for("tournament_detail",tournament_id=match.get("tournament_id"))+"#schedule")
        execute_query(db.table("tournament_matches").update({"scheduled_at":slot,"status":"scheduled","updated_at":now_iso()}).eq("id",match_id),"ops_availability_schedule",attempts=2)
        flash("Đã chốt lịch vì cả hai HLV đều đánh dấu rảnh ở khung giờ này.","success")
        return redirect(url_for("tournament_detail",tournament_id=match.get("tournament_id"))+"#schedule")

    @app.post('/tournaments/matches/<match_id>/schedule')
    @login_required
    def tournament_match_schedule(match_id):
        uid=(current_user() or {}).get("id")
        match,_=_one(db.table("tournament_matches").select("*").eq("id",match_id),"ops_schedule_match")
        if not match or str(uid) not in {str(match.get("home_user_id")),str(match.get("away_user_id"))}:
            flash("Bạn không thuộc trận này.","error"); return redirect(url_for("tournaments"))
        if match.get("status") in {"completed","playing","cancelled"}:
            flash("Trận này không thể hẹn lịch ở trạng thái hiện tại.","warning")
            return redirect(url_for("tournament_detail",tournament_id=match.get("tournament_id"))+"#schedule")
        proposed=(request.form.get("scheduled_at") or "").strip(); host_id=(request.form.get("host_id") or "").strip() or None
        if not proposed:
            flash("Hãy chọn ngày và giờ thi đấu.","error"); return redirect(url_for("tournament_detail",tournament_id=match.get("tournament_id"))+"#schedule")
        try:
            # datetime-local is entered in Vietnam local time; save an explicit +07:00 offset for timestamptz.
            vn_tz=timezone(timedelta(hours=7))
            parsed=datetime.fromisoformat(proposed).replace(tzinfo=vn_tz)
            if parsed <= datetime.now(vn_tz):
                flash("Thời gian đề xuất phải ở tương lai.","error")
                return redirect(url_for("tournament_detail",tournament_id=match.get("tournament_id"))+"#schedule")
        except ValueError:
            flash("Thời gian đề xuất không hợp lệ.","error")
            return redirect(url_for("tournament_detail",tournament_id=match.get("tournament_id"))+"#schedule")

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
        return redirect(url_for("tournament_detail",tournament_id=match.get("tournament_id"))+"#schedule")

    @app.post('/tournaments/schedules/<schedule_id>/accept')
    @login_required
    def tournament_schedule_accept(schedule_id):
        uid=(current_user() or {}).get("id")
        sched,_=_one(db.table("tournament_schedule_requests").select("*").eq("id",schedule_id),"ops_sched_lookup")
        if not sched: flash("Không tìm thấy đề xuất lịch.","error"); return redirect(url_for("tournaments"))
        match,_=_one(db.table("tournament_matches").select("*").eq("id",sched.get("match_id")),"ops_sched_match")
        if not match or str(uid) not in {str(match.get("home_user_id")),str(match.get("away_user_id"))} or str(uid)==str(sched.get("proposed_by")):
            flash("Bạn không thể xác nhận lịch này.","error"); return redirect(url_for("tournament_detail",tournament_id=sched.get("tournament_id"))+"#schedule")
        if sched.get("status")!="pending":
            flash("Đề xuất này không còn chờ xác nhận.","warning"); return redirect(url_for("tournament_detail",tournament_id=sched.get("tournament_id"))+"#schedule")
        execute_query(db.table("tournament_schedule_requests").update({"status":"accepted","responded_by":uid,"responded_at":now_iso()}).eq("id",schedule_id),"ops_sched_accept",attempts=2)
        execute_query(db.table("tournament_matches").update({"scheduled_at":sched.get("proposed_at"),"host_id":sched.get("host_id"),"status":"scheduled","updated_at":now_iso()}).eq("id",sched.get("match_id")),"ops_match_schedule",attempts=2)
        # Close any other pending proposal for this match.
        try:
            execute_query(db.table("tournament_schedule_requests").update({"status":"cancelled","responded_at":now_iso()}).eq("match_id",sched.get("match_id")).eq("status","pending"),"ops_sched_close_others",attempts=2)
        except Exception:
            pass
        flash("Hai HLV đã thống nhất. Lịch thi đấu đã được chốt.","success")
        return redirect(url_for("tournament_detail",tournament_id=sched.get("tournament_id"))+"#schedule")

    @app.post('/tournaments/schedules/<schedule_id>/reject')
    @login_required
    def tournament_schedule_reject(schedule_id):
        uid=(current_user() or {}).get("id")
        sched,_=_one(db.table("tournament_schedule_requests").select("*").eq("id",schedule_id),"ops_sched_reject_lookup")
        if not sched:
            flash("Không tìm thấy đề xuất lịch.","error"); return redirect(url_for("tournaments"))
        match,_=_one(db.table("tournament_matches").select("*").eq("id",sched.get("match_id")),"ops_sched_reject_match")
        if not match or str(uid) not in {str(match.get("home_user_id")),str(match.get("away_user_id"))} or str(uid)==str(sched.get("proposed_by")):
            flash("Bạn không thể từ chối lịch này.","error"); return redirect(url_for("tournament_detail",tournament_id=sched.get("tournament_id"))+"#schedule")
        if sched.get("status")!="pending":
            flash("Đề xuất này không còn chờ xác nhận.","warning"); return redirect(url_for("tournament_detail",tournament_id=sched.get("tournament_id"))+"#schedule")
        execute_query(db.table("tournament_schedule_requests").update({
            "status":"rejected","responded_by":uid,"responded_at":now_iso(),
            "note":(request.form.get("note") or "").strip()[:250] or None
        }).eq("id",schedule_id),"ops_sched_reject",attempts=2)
        flash("Đã từ chối đề xuất. Bạn có thể chọn giờ khác và gửi đề xuất lại.","success")
        return redirect(url_for("tournament_detail",tournament_id=sched.get("tournament_id"))+"#schedule")

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

    @app.post('/admin/tournaments/<tournament_id>/stage1/extend')
    @login_required
    @admin_required
    @admin_permission_required("system_features_manage")
    def admin_tournament_stage1_extend(tournament_id):
        cfg=_setting(tournament_id,"competition_timing",{}) or {}
        base=_parse_iso(cfg.get("stage1_end_at")) or datetime.now(timezone(timedelta(hours=7)))
        if base.tzinfo is None: base=base.replace(tzinfo=timezone(timedelta(hours=7)))
        cfg["stage1_extension_end_at"]=(max(base,datetime.now(base.tzinfo))+timedelta(days=2)).isoformat()
        execute_query(db.table("tournament_settings").upsert({"tournament_id":tournament_id,"setting_key":"competition_timing","setting_value":cfg,"updated_at":now_iso()},on_conflict="tournament_id,setting_key"),"ops_s1_extend",attempts=2)
        flash("Đã gia hạn GĐ1 thêm 2 ngày.","success"); return redirect_admin("tournaments")

    @app.post('/admin/tournaments/<tournament_id>/stage1/finish')
    @login_required
    @admin_required
    @admin_permission_required("system_features_manage")
    def admin_tournament_stage1_finish(tournament_id):
        force=request.form.get("force")=="1"
        pending=[m for m in _matches(tournament_id,"stage1") if m.get("status")!="completed"]
        if pending and not force:
            flash(f"GĐ1 còn {len(pending)} trận chưa hoàn thành. Chỉ kết thúc sớm khi 100% trận xong, hoặc dùng kết thúc sau gia hạn.","warning"); return redirect_admin("tournaments")
        if pending and force:
            for m in pending:
                execute_query(db.table("tournament_matches").update({"status":"disputed","updated_at":now_iso()}).eq("id",m.get("id")),"ops_s1_pending_btc",attempts=2)
        execute_query(db.table("tournament_stages").update({"status":"completed","updated_at":now_iso()}).eq("tournament_id",tournament_id).eq("stage_code","stage1"),"ops_s1_finish",attempts=2)
        execute_query(db.table("tournament_stages").update({"status":"open","updated_at":now_iso()}).eq("tournament_id",tournament_id).eq("stage_code","league"),"ops_league_open_after_s1",attempts=2)
        flash("Đã kết thúc GĐ1. Có thể chia Pot, chọn CLB và chuẩn bị League Phase.","success"); return redirect_admin("tournaments")

    @app.post('/admin/tournaments/<tournament_id>/league/finish')
    @login_required
    @admin_required
    @admin_permission_required("system_features_manage")
    def admin_tournament_league_finish(tournament_id):
        force=request.form.get("force")=="1"
        pending=[m for m in _matches(tournament_id,"league") if m.get("status")!="completed"]
        if pending and not force:
            flash(f"League Phase còn {len(pending)} trận chưa hoàn thành.","warning"); return redirect_admin("tournaments")
        if pending and force:
            for m in pending:
                execute_query(db.table("tournament_matches").update({"status":"disputed","updated_at":now_iso()}).eq("id",m.get("id")),"ops_league_pending_btc",attempts=2)
        execute_query(db.table("tournament_stages").update({"status":"completed","updated_at":now_iso()}).eq("tournament_id",tournament_id).eq("stage_code","league"),"ops_league_finish",attempts=2)
        execute_query(db.table("tournament_stages").update({"status":"open","updated_at":now_iso()}).eq("tournament_id",tournament_id).eq("stage_code","knockout"),"ops_ko_open",attempts=2)
        flash("Đã khóa League Phase. BXH tổng GĐ1 + GĐ2 đã sẵn sàng để sinh Knockout.","success"); return redirect_admin("tournaments")

    @app.post('/admin/tournaments/<tournament_id>/knockout/generate')
    @login_required
    @admin_required
    @admin_permission_required("system_features_manage")
    def admin_tournament_knockout_generate(tournament_id):
        use_playoff=request.form.get("use_playoff")=="1"
        ranking=_combined_ranking(tournament_id)
        if len(ranking)<8:
            flash("Chưa đủ HLV để sinh Knockout.","error"); return redirect_admin("tournaments")
        existing=_matches(tournament_id,"knockout")
        if any(m.get("status")=="completed" for m in existing):
            flash("Knockout đã có kết quả, không thể sinh lại.","error"); return redirect_admin("tournaments")
        if existing:
            execute_query(db.table("tournament_matches").delete().eq("tournament_id",tournament_id).eq("stage_code","knockout"),"ops_ko_clear",attempts=2)
        ids=[str(r.get("user_id")) for r in ranking]
        state={"use_playoff":use_playoff,"completed":False,"champion_user_id":None,"created_at":now_iso()}
        if use_playoff and len(ids)>=24:
            direct=ids[:8]; pool=ids[8:24]; state["direct_r16"]=direct; state["current_round"]="playoff"
            for i in range(8): _insert_ko_pair(tournament_id,"playoff",pool[i],pool[-(i+1)],True)
        else:
            entrants=ids[:16] if len(ids)>=16 else ids[:8]
            round_code="r16" if len(entrants)>=16 else "qf"
            state["current_round"]=round_code
            for i in range(len(entrants)//2): _insert_ko_pair(tournament_id,round_code,entrants[i],entrants[-(i+1)],True)
        execute_query(db.table("tournament_settings").upsert({"tournament_id":tournament_id,"setting_key":"knockout_flow","setting_value":state,"updated_at":now_iso()},on_conflict="tournament_id,setting_key"),"ops_ko_generate_state",attempts=2)
        execute_query(db.table("tournament_stages").update({"status":"open","updated_at":now_iso()}).eq("tournament_id",tournament_id).eq("stage_code","knockout"),"ops_ko_generate_open",attempts=2)
        flash("Đã sinh bracket Knockout tự động.","success"); return redirect_admin("tournaments")

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
