"""Tournament Test Mode V1.4.34.

A fully isolated sandbox stored as JSON. It never writes Rank matches, tournament
production matches, Zcoin, Lucky Box or real tournament members.
"""
from datetime import datetime, timezone
import random
import uuid

SANDBOX_TABLE = "tournament_test_sandboxes"


def register_routes(context):
    globals().update(context)

    def _empty_state():
        return {
            "enabled": True,
            "players": [],
            "registrations": [],
            "registration_open": True,
            "current_stage": "registration",
            "stage1_target": 5,
            "pot_count": 4,
            "stage1_matches": [],
            "stage1_ranking": [],
            "pots": [],
            "league_matches": [],
            "league_ranking": [],
            "knockout": [],
            "hosts": [
                {"id":"host-bac","name":"Host Test Bắc","region":"Bắc","status":"available"},
                {"id":"host-trung","name":"Host Test Trung","region":"Trung","status":"available"},
                {"id":"host-nam","name":"Host Test Nam","region":"Nam","status":"available"},
            ],
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    def _admin_id():
        return str((current_user() or {}).get("id") or "")

    def _load_state():
        aid = _admin_id()
        if not aid:
            return _empty_state(), False
        try:
            result = execute_query(
                db.table(SANDBOX_TABLE).select("state").eq("admin_user_id", aid).limit(1),
                "tournament_test_load", attempts=2,
            )
            rows = result.data or []
            if rows and isinstance(rows[0].get("state"), dict):
                state = _empty_state()
                state.update(dict(rows[0]["state"]))
                return state, True
        except Exception as exc:
            app.logger.warning("Tournament test mode unavailable: %s", exc)
        return _empty_state(), False

    def _save_state(state):
        aid = _admin_id()
        state["updated_at"] = datetime.now(timezone.utc).isoformat()
        execute_query(
            db.table(SANDBOX_TABLE).upsert({
                "admin_user_id": aid,
                "state": state,
                "updated_at": state["updated_at"],
            }, on_conflict="admin_user_id"),
            "tournament_test_save", attempts=2,
        )

    def _player_name(pid, players):
        p = next((x for x in players if x.get("id") == pid), None)
        return (p or {}).get("name") or pid

    def _round_robin_rounds(players):
        ids = [p["id"] for p in players]
        if len(ids) % 2:
            ids.append(None)
        n = len(ids)
        fixed = ids[0]
        rotating = ids[1:]
        rounds = []
        for _ in range(n - 1):
            row = [fixed] + rotating
            pairs = []
            for i in range(n // 2):
                a, b = row[i], row[n - 1 - i]
                if a and b:
                    pairs.append((a, b))
            rounds.append(pairs)
            rotating = [rotating[-1]] + rotating[:-1]
        return rounds

    def _regular_pairs(player_ids, degree):
        """Return a deterministic simple regular graph as player pairs."""
        n=len(player_ids)
        if degree < 0 or degree >= n or (n * degree) % 2:
            return []
        pairs=set()
        for offset in range(1, (degree // 2) + 1):
            for i in range(n):
                a,b=player_ids[i],player_ids[(i+offset) % n]
                if a != b: pairs.add(tuple(sorted((a,b))))
        if degree % 2:
            for i in range(n // 2):
                pairs.add(tuple(sorted((player_ids[i],player_ids[i+n//2]))))
        return sorted(pairs)

    def _balanced_stage1_pairs(players, target):
        """Exactly target matches/player, with no pair repeated more than twice."""
        ids=[p["id"] for p in players]
        n=len(ids)
        if n < 2 or n * target % 2 or target > 2 * (n - 1):
            return None
        if target <= n - 1:
            return _regular_pairs(ids, target)
        first=[tuple(sorted((ids[i],ids[j]))) for i in range(n) for j in range(i+1,n)]
        return first + _regular_pairs(ids, target - (n - 1))

    def _score(seed):
        r = random.Random(seed)
        return r.randint(0, 4), r.randint(0, 4)

    def _ranking(players, matches):
        table = {p["id"]: {"user_id":p["id"],"display_name":p["name"],"played":0,"wins":0,"draws":0,"losses":0,"gf":0,"ga":0,"gd":0,"points":0,"opponents":set()} for p in players}
        for m in matches:
            if m.get("status") != "completed":
                continue
            h, a = m["home"], m["away"]
            if h not in table or a not in table:
                continue
            hs, av = int(m.get("home_score",0)), int(m.get("away_score",0))
            H,A = table[h], table[a]
            H["played"] += 1; A["played"] += 1
            H["gf"] += hs; H["ga"] += av; A["gf"] += av; A["ga"] += hs
            H["opponents"].add(a); A["opponents"].add(h)
            if hs > av:
                H["wins"] += 1; H["points"] += 3; A["losses"] += 1
            elif hs < av:
                A["wins"] += 1; A["points"] += 3; H["losses"] += 1
            else:
                H["draws"] += 1; A["draws"] += 1; H["points"] += 1; A["points"] += 1
        rows=[]
        for r in table.values():
            r["gd"] = r["gf"] - r["ga"]
            r["opponent_count"] = len(r.pop("opponents"))
            rows.append(r)
        rows.sort(key=lambda x:(x["points"],x["gd"],x["gf"],x["wins"],x["display_name"]), reverse=True)
        for idx,r in enumerate(rows,1): r["rank"] = idx
        return rows

    def _decorate_matches(matches, players):
        out=[]
        for m in matches:
            row=dict(m)
            row["home_name"]=_player_name(row.get("home"),players)
            row["away_name"]=_player_name(row.get("away"),players)
            out.append(row)
        return out

    def _registration_for(state, player_id):
        return next((r for r in (state.get("registrations") or []) if r.get("user_id") == player_id), None)

    def _registration_counts(state):
        rows = state.get("registrations") or []
        return {key: sum(1 for row in rows if row.get("status") == key)
                for key in ("pending", "approved", "rejected", "withdrawn")}

    STAGES = [
        ("registration", "Đăng ký"),
        ("stage1", "GĐ1 - Random/Xếp Pot"),
        ("league", "GĐ2 - League Phase"),
        ("playoff", "Play-off"),
        ("r16", "Vòng 1/8"),
        ("qf", "Tứ kết"),
        ("sf", "Bán kết"),
        ("final", "Chung kết"),
    ]
    STAGE_KEYS = {key for key, _ in STAGES}

    def _build_full_simulation(count=36, target=5, pot_count=4):
        count=max(4,min(36,int(count or 36)))
        target=max(5,min(6,int(target or 5)))
        pot_count=3 if int(pot_count or 4) == 3 else 4
        state=_empty_state(); state["stage1_target"]=target; state["pot_count"]=pot_count
        players=[]
        for i in range(1,count+1):
            players.append({
                "id":f"test-hlv-{i:02d}", "name":f"Test HLV {i:02d}", "is_test":True,
                "zalo_name":f"Test HLV {i:02d} Zalo", "has_host":i % 2 == 1,
                "host_region":["Bắc","Trung","Nam"][(i-1)%3],
            })
        state["players"]=players
        state["registrations"]=[{
            "id":f"test-reg-{i:02d}", "user_id":p["id"], "display_name":p["name"],
            "status":"approved", "has_host":p["has_host"], "host_region":p["host_region"],
            "zalo_name":p["zalo_name"], "payment_status":"reported",
            "registered_at":datetime.now(timezone.utc).isoformat(),
        } for i,p in enumerate(players,1)]
        state["registration_open"] = False

        pairs=_balanced_stage1_pairs(players,target)
        if pairs is None:
            raise ValueError(f"Không thể chia đều {target} trận cho {count} HLV")
        s1=[]; per_round=max(1,len(players)//2)
        for seq,(a,b) in enumerate(pairs,1):
            rnd=((seq-1)//per_round)+1; hs,av=_score(f"all-s1-{rnd}-{a}-{b}")
            s1.append({"id":f"s1-{seq}","round":rnd,"home":a,"away":b,"home_score":hs,"away_score":av,"status":"completed"})
        state["stage1_matches"]=s1; state["stage1_ranking"]=_ranking(players,s1)

        chunk=(len(players)+pot_count-1)//pot_count; pots=[[] for _ in range(pot_count)]
        for i,row in enumerate(state["stage1_ranking"]):
            pi=min(i//chunk,pot_count-1)
            pots[pi].append({"user_id":row["user_id"],"display_name":row["display_name"],"seed":i+1,"pot":pi+1})
        state["pots"]=pots
        members_by_pot={idx+1:[x["user_id"] for x in pot] for idx,pot in enumerate(pots)}
        seen=set(); lg=[]; seq=1
        # 1 opponent from each pot; deterministic and intentionally simple for UI testing.
        for p in players:
            uid=p["id"]
            for pot_no,candidates in members_by_pot.items():
                for opp in sorted(x for x in candidates if x!=uid):
                    key=tuple(sorted((uid,opp)))
                    if key in seen: continue
                    seen.add(key); hs,av=_score(f"all-lg-{uid}-{opp}")
                    lg.append({"id":f"lg-{seq}","home":uid,"away":opp,"home_score":hs,"away_score":av,"status":"completed","home_pot":next((x["pot"] for pot in pots for x in pot if x["user_id"]==uid),None),"away_pot":pot_no})
                    seq+=1; break
        state["league_matches"]=lg; state["league_ranking"]=_ranking(players,lg)

        ranking=state["league_ranking"]; names={p["id"]:p["name"] for p in players}; ko=[]
        direct=[r["user_id"] for r in ranking[:min(8,len(ranking))]]
        playoff_pool=[r["user_id"] for r in ranking[8:24]]
        playoff_winners=[]; playoff_pairs=[]
        half=len(playoff_pool)//2
        for i in range(half):
            a=playoff_pool[i]; b=playoff_pool[-(i+1)]
            a1,b1=_score(f"po1-{a}-{b}"); b2,a2=_score(f"po2-{b}-{a}"); aa,bb=a1+a2,b1+b2
            w=a if aa>bb or (aa==bb and a<b) else b
            playoff_winners.append(w)
            playoff_pairs.append({"home":a,"away":b,"home_name":names[a],"away_name":names[b],"leg1":f"{a1}-{b1}","leg2":f"{b2}-{a2}","aggregate":f"{aa}-{bb}","winner":w,"winner_name":names[w]})
        if playoff_pairs:
            ko.append({"key":"playoff","name":"Play-off","pairs":playoff_pairs})
        current=(direct+playoff_winners)[:16]
        if len(current)<2:
            current=[r["user_id"] for r in ranking[:min(16,len(ranking))]]
        labels={16:("r16","Vòng 1/8"),8:("qf","Tứ kết"),4:("sf","Bán kết"),2:("final","Chung kết")}
        while len(current)>=2:
            key,label=labels.get(len(current),(f"top{len(current)}",f"Top {len(current)}"))
            nxt=[]; prs=[]
            for i in range(0,len(current)-1,2):
                a,b=current[i],current[i+1]
                if key=="final":
                    # Bo3: trận 1 + 2 90', trận 3 là trận quyết định có ET/PEN nếu cần.
                    g1a,g1b=_score(f"f1-{a}-{b}"); g2a,g2b=_score(f"f2-{a}-{b}")
                    wins_a=(g1a>g1b)+(g2a>g2b); wins_b=(g1b>g1a)+(g2b>g2a)
                    g3a,g3b=_score(f"f3-{a}-{b}")
                    if g3a==g3b: g3a += 1
                    wins_a += g3a>g3b; wins_b += g3b>g3a
                    w=a if wins_a>wins_b else b
                    prs.append({"home":a,"away":b,"home_name":names.get(a,a),"away_name":names.get(b,b),"leg1":f"Trận 1: {g1a}-{g1b}","leg2":f"Trận 2: {g2a}-{g2b}","decider":f"Trận 3: {g3a}-{g3b} (có ET/PEN)","aggregate":f"Bo3 {wins_a}-{wins_b}","winner":w,"winner_name":names.get(w,w)})
                else:
                    a1,b1=_score(f"{key}1-{a}-{b}"); b2,a2=_score(f"{key}2-{b}-{a}"); aa,bb=a1+a2,b1+b2
                    w=a if aa>bb or (aa==bb and a<b) else b
                    prs.append({"home":a,"away":b,"home_name":names.get(a,a),"away_name":names.get(b,b),"leg1":f"{a1}-{b1}","leg2":f"{b2}-{a2}","aggregate":f"{aa}-{bb}","winner":w,"winner_name":names.get(w,w)})
                nxt.append(w)
            ko.append({"key":key,"name":label,"pairs":prs}); current=nxt
            if len(current)==1: break
        state["knockout"]=ko
        return state

    def _default_view_for_stage(state, stage):
        players=state.get("players") or []
        if stage in {"playoff","r16","qf","sf","final"}:
            rnd=next((r for r in (state.get("knockout") or []) if r.get("key")==stage),None)
            if rnd and rnd.get("pairs"):
                return rnd["pairs"][0].get("home") or rnd["pairs"][0].get("away")
        if stage=="league" and state.get("league_ranking"):
            return state["league_ranking"][0].get("user_id")
        if stage=="stage1" and state.get("stage1_ranking"):
            return state["stage1_ranking"][0].get("user_id")
        if stage=="registration":
            # Prefer a player with no registration so the complete form can be tested.
            registered={r.get("user_id") for r in (state.get("registrations") or [])}
            p=next((x for x in players if x.get("id") not in registered),None)
            if p: return p.get("id")
        return players[0].get("id") if players else "spectator"

    def _stage_context(state, stage, view_as):
        players=state.get("players") or []
        stage = stage if stage in STAGE_KEYS else (state.get("current_stage") if state.get("current_stage") in STAGE_KEYS else "registration")
        my_s1_matches=[m for m in _decorate_matches(state.get("stage1_matches") or [],players) if view_as in (m.get("home"),m.get("away"))]
        my_league_matches=[m for m in _decorate_matches(state.get("league_matches") or [],players) if view_as in (m.get("home"),m.get("away"))]
        my_pot=None
        for pot in state.get("pots") or []:
            for row in pot:
                if row.get("user_id")==view_as: my_pot=row.get("pot")
        my_ko=[]
        for rnd in state.get("knockout") or []:
            if rnd.get("key")==stage:
                my_ko=[p for p in rnd.get("pairs") or [] if view_as in (p.get("home"),p.get("away"))]
                break
        return stage,my_s1_matches,my_league_matches,my_pot,my_ko

    @app.get('/admin/tournament-test-mode')
    @login_required
    @admin_required
    @admin_permission_required("system_features_manage")
    def admin_tournament_test_mode():
        state, ready = _load_state()
        view_as = (request.args.get("view_as") or "admin").strip()
        players = state.get("players") or []
        me = next((p for p in players if p.get("id") == view_as), None)
        s1 = state.get("stage1_ranking") or []
        league = state.get("league_ranking") or []
        my_s1 = next((r for r in s1 if r.get("user_id") == view_as), None)
        my_league = next((r for r in league if r.get("user_id") == view_as), None)
        return render_template(
            'tournament_test_mode.html', state=state, sandbox_ready=ready,
            view_as=view_as, me=me, my_s1=my_s1, my_league=my_league,
            registration_counts=_registration_counts(state),
            stage1_matches=_decorate_matches(state.get("stage1_matches") or [],players),
            league_matches=_decorate_matches(state.get("league_matches") or [],players),
        )

    @app.get('/admin/tournament-test-mode/public')
    @login_required
    @admin_required
    @admin_permission_required("system_features_manage")
    def admin_tournament_test_public():
        state, ready = _load_state()
        players = state.get("players") or []
        view_as = (request.args.get("view_as") or (players[0]["id"] if players else "spectator")).strip()
        me = next((p for p in players if p.get("id") == view_as), None)
        registration = _registration_for(state, view_as) if me else None
        member = bool(registration and registration.get("status") == "approved")
        my_s1 = next((r for r in (state.get("stage1_ranking") or []) if r.get("user_id") == view_as), None)
        my_league = next((r for r in (state.get("league_ranking") or []) if r.get("user_id") == view_as), None)
        stage,my_s1_matches,my_league_matches,my_pot,my_ko = _stage_context(state, (request.args.get("stage") or "").strip(), view_as)
        return render_template(
            'tournament_test_public.html', state=state, sandbox_ready=ready,
            players=players, view_as=view_as, me=me, registration=registration,
            member=member, my_s1=my_s1, my_league=my_league, stage=stage, stages=STAGES, stage_label=dict(STAGES).get(stage, stage),
            my_s1_matches=my_s1_matches, my_league_matches=my_league_matches, my_pot=my_pot, my_ko=my_ko,
            registration_counts=_registration_counts(state),
            stage1_matches=_decorate_matches(state.get("stage1_matches") or [], players),
            league_matches=_decorate_matches(state.get("league_matches") or [], players),
        )

    @app.post('/admin/tournament-test-mode/create-players')
    @login_required
    @admin_required
    @admin_permission_required("system_features_manage")
    def admin_tournament_test_create_players():
        count=max(4,min(36,int(request.form.get("count") or 16)))
        target=max(5,min(6,int(request.form.get("target") or 5)))
        state=_empty_state()
        state["stage1_target"]=target
        state["players"]=[{"id":f"test-hlv-{i:02d}","name":f"Test HLV {i:02d}","is_test":True} for i in range(1,count+1)]
        _save_state(state)
        flash(f"Đã tạo {count} HLV giả trong sandbox. Không tạo tài khoản thật.","success")
        return redirect(url_for('admin_tournament_test_mode'))

    @app.post('/admin/tournament-test-mode/seed-registrations')
    @login_required
    @admin_required
    @admin_permission_required("system_features_manage")
    def admin_tournament_test_seed_registrations():
        state, _ = _load_state()
        players = state.get("players") or []
        if not players:
            count=max(4,min(36,int(request.form.get("count") or 16)))
            players=[{"id":f"test-hlv-{i:02d}","name":f"Test HLV {i:02d}","is_test":True} for i in range(1,count+1)]
            state["players"] = players
        rows=[]
        for i,p in enumerate(players):
            status = "pending" if i < 4 else ("approved" if i < max(5, len(players)-4) else ("rejected" if i < len(players)-2 else None))
            if status:
                rows.append({"id":f"test-reg-{i+1:02d}","user_id":p["id"],"display_name":p["name"],
                             "status":status,"has_host":i%2==0,"host_region":["Bắc","Trung","Nam"][i%3],"zalo_name":f"{p['name']} Zalo","payment_status":"reported","registered_at":datetime.now(timezone.utc).isoformat()})
        state["registrations"] = rows
        state["registration_open"] = True
        _save_state(state)
        flash("Đã tạo mẫu đăng ký: có đơn chờ duyệt, đã duyệt, từ chối và HLV chưa đăng ký.","success")
        return redirect(url_for('admin_tournament_test_mode'))

    @app.post('/admin/tournament-test-mode/register/<player_id>')
    @login_required
    @admin_required
    @admin_permission_required("system_features_manage")
    def admin_tournament_test_register(player_id):
        state,_=_load_state()
        player=next((p for p in (state.get("players") or []) if p.get("id")==player_id),None)
        if not player or not state.get("registration_open", True):
            flash("Không thể gửi đăng ký Test lúc này.","warning")
        else:
            rows=[r for r in (state.get("registrations") or []) if r.get("user_id")!=player_id]
            host_choice=(request.form.get("host_choice") or "").strip().lower()
            host_region=(request.form.get("host_region") or "").strip()
            zalo_name=(request.form.get("zalo_name") or "").strip()
            payment_confirmed=request.form.get("payment_confirmed") == "1"
            if host_choice not in {"yes","no"} or host_region not in {"Bắc","Trung","Nam"} or not zalo_name or not payment_confirmed:
                flash("Hãy chọn Host, khu vực và xác nhận chuyển khoản trong form Test.","warning")
                return redirect(url_for('admin_tournament_test_public',view_as=player_id,register='1'))
            rows.append({"id":f"test-reg-{uuid.uuid4().hex[:8]}","user_id":player_id,"display_name":player["name"],
                         "status":"pending","has_host":host_choice=="yes","host_region":host_region,"zalo_name":zalo_name[:80],
                         "payment_status":"reported","payment_reported_at":datetime.now(timezone.utc).isoformat(),
                         "registered_at":datetime.now(timezone.utc).isoformat()})
            state["registrations"]=rows; _save_state(state)
            flash(f"{player['name']} đã gửi đăng ký và đang chờ Admin duyệt.","success")
        return redirect(url_for('admin_tournament_test_public',view_as=player_id))

    @app.post('/admin/tournament-test-mode/registration/<registration_id>/<decision>')
    @login_required
    @admin_required
    @admin_permission_required("system_features_manage")
    def admin_tournament_test_registration_review(registration_id, decision):
        if decision not in {"approved","rejected"}:
            decision="rejected"
        state,_=_load_state(); found=None
        for row in state.get("registrations") or []:
            if row.get("id")==registration_id:
                row["status"]=decision; row["reviewed_at"]=datetime.now(timezone.utc).isoformat(); found=row; break
        if found:
            _save_state(state); flash("Đã duyệt HLV vào giải Test." if decision=="approved" else "Đã từ chối đơn Test.","success")
        else: flash("Không tìm thấy đơn đăng ký Test.","error")
        return redirect(url_for('admin_tournament_test_mode'))

    @app.post('/admin/tournament-test-mode/generate-stage1')
    @login_required
    @admin_required
    @admin_permission_required("system_features_manage")
    def admin_tournament_test_generate_stage1():
        state,_=_load_state(); players=state.get("players") or []
        if len(players)<4:
            flash("Hãy tạo HLV Test trước.","warning"); return redirect(url_for('admin_tournament_test_mode'))
        target=int(state.get("stage1_target") or 5)
        pairs=_balanced_stage1_pairs(players,target)
        if pairs is None:
            flash(f"Không thể chia đều {target} trận cho {len(players)} HLV. Hãy đổi số HLV hoặc chọn số trận khác.","error")
            return redirect(url_for('admin_tournament_test_mode'))
        matches=[]; per_round=max(1,len(players)//2)
        for seq,(a,b) in enumerate(pairs,1):
            rnd=((seq-1)//per_round)+1; hs,av=_score(f"s1-{rnd}-{a}-{b}")
            matches.append({"id":f"s1-{seq}","round":rnd,"home":a,"away":b,"home_score":hs,"away_score":av,"status":"completed"})
        state["stage1_matches"]=matches
        state["stage1_ranking"]=_ranking(players,matches)
        state["pots"]=[]; state["league_matches"]=[]; state["league_ranking"]=[]; state["knockout"]=[]
        _save_state(state)
        flash(f"Đã mô phỏng GĐ1: {len(matches)} trận. Mỗi HLV {target} đối thủ khác nhau.","success")
        return redirect(url_for('admin_tournament_test_mode'))

    @app.post('/admin/tournament-test-mode/generate-pots')
    @login_required
    @admin_required
    @admin_permission_required("system_features_manage")
    def admin_tournament_test_generate_pots():
        state,_=_load_state(); ranking=state.get("stage1_ranking") or []
        if not ranking:
            flash("Hãy sinh GĐ1 trước.","warning"); return redirect(url_for('admin_tournament_test_mode'))
        pot_count=3 if int(request.form.get("pot_count") or 4) == 3 else 4
        pots=[[] for _ in range(pot_count)]
        chunk=(len(ranking)+pot_count-1)//pot_count
        for i,row in enumerate(ranking):
            p=min(i//chunk,pot_count-1)
            pots[p].append({"user_id":row["user_id"],"display_name":row["display_name"],"seed":i+1,"pot":p+1})
        state["pots"]=pots; state["pot_count"]=pot_count; _save_state(state)
        flash(f"Đã chia {pot_count} Pot theo BXH GĐ1.","success")
        return redirect(url_for('admin_tournament_test_mode'))

    @app.post('/admin/tournament-test-mode/generate-league')
    @login_required
    @admin_required
    @admin_permission_required("system_features_manage")
    def admin_tournament_test_generate_league():
        state,_=_load_state(); players=state.get("players") or []; pots=state.get("pots") or []
        if not pots:
            flash("Hãy chia Pot trước.","warning"); return redirect(url_for('admin_tournament_test_mode'))
        per_pot=max(1,min(2,int(request.form.get("matches_per_pot") or 1)))
        pot_of={x["user_id"]:x["pot"] for pot in pots for x in pot}
        members_by_pot={idx+1:[x["user_id"] for x in pot] for idx,pot in enumerate(pots)}
        seen=set(); matches=[]; seq=1
        for p in players:
            uid=p["id"]
            for pot_no,candidates in members_by_pot.items():
                choices=[x for x in candidates if x!=uid]
                choices=sorted(choices, key=lambda x: (x, uid))
                added=0
                for opp in choices:
                    key=tuple(sorted((uid,opp)))
                    if key in seen: continue
                    seen.add(key); hs,av=_score(f"lg-{uid}-{opp}")
                    matches.append({"id":f"lg-{seq}","home":uid,"away":opp,"home_score":hs,"away_score":av,"status":"completed","home_pot":pot_of.get(uid),"away_pot":pot_of.get(opp)}); seq+=1; added+=1
                    if added>=per_pot: break
        state["league_matches"]=matches
        state["league_ranking"]=_ranking(players,matches)
        _save_state(state)
        flash(f"Đã mô phỏng League Phase: {len(matches)} trận.","success")
        return redirect(url_for('admin_tournament_test_mode'))

    @app.post('/admin/tournament-test-mode/simulate-knockout')
    @login_required
    @admin_required
    @admin_permission_required("system_features_manage")
    def admin_tournament_test_knockout():
        state,_=_load_state(); league=state.get("league_ranking") or state.get("stage1_ranking") or []
        qualifiers=[r["user_id"] for r in league[:16]]
        if len(qualifiers)<2:
            flash("Chưa đủ dữ liệu để mô phỏng Knockout.","warning"); return redirect(url_for('admin_tournament_test_mode'))
        rounds=[]; current=qualifiers; names={p["id"]:p["name"] for p in state.get("players") or []}
        labels={16:"R16",8:"Tứ kết",4:"Bán kết",2:"Chung kết"}
        while len(current)>=2:
            nxt=[]; pair_rows=[]
            for i in range(0,len(current)-1,2):
                a,b=current[i],current[i+1]
                a1,b1=_score(f"ko1-{a}-{b}"); b2,a2=_score(f"ko2-{b}-{a}")
                agg_a=a1+a2; agg_b=b1+b2
                winner=a if (agg_a, names.get(a,a)) >= (agg_b, names.get(b,b)) else b
                if agg_a==agg_b: winner=a if a<b else b
                nxt.append(winner)
                pair_rows.append({"home":a,"away":b,"home_name":names.get(a,a),"away_name":names.get(b,b),"leg1":f"{a1}-{b1}","leg2":f"{b2}-{a2}","aggregate":f"{agg_a}-{agg_b}","winner":winner,"winner_name":names.get(winner,winner)})
            rounds.append({"name":labels.get(len(current),f"Top {len(current)}"),"pairs":pair_rows})
            current=nxt
            if len(current)==1: break
        state["knockout"]=rounds; _save_state(state)
        flash("Đã mô phỏng Knockout hai lượt đến Chung kết.","success")
        return redirect(url_for('admin_tournament_test_mode'))

    @app.post('/admin/tournament-test-mode/run-all')
    @login_required
    @admin_required
    @admin_permission_required("system_features_manage")
    def admin_tournament_test_run_all():
        count=max(4,min(36,int(request.form.get("count") or 36)))
        target=max(5,min(6,int(request.form.get("target") or 5)))
        pot_count=3 if int(request.form.get("pot_count") or 4) == 3 else 4
        try:
            state=_build_full_simulation(count,target,pot_count)
        except ValueError as exc:
            flash(str(exc),"error"); return redirect(url_for('admin_tournament_test_mode'))
        state["current_stage"]="registration"
        _save_state(state)
        flash(f"Đã tạo Tournament Test Console: {count} HLV · GĐ1 {target} trận/HLV · {pot_count} Pot.","success")
        return redirect(url_for('admin_tournament_test_mode'))

    @app.post('/admin/tournament-test-mode/prepare-stage/<stage>')
    @login_required
    @admin_required
    @admin_permission_required("system_features_manage")
    def admin_tournament_test_prepare_stage(stage):
        if stage not in STAGE_KEYS:
            flash("Giai đoạn Test không hợp lệ.","error"); return redirect(url_for('admin_tournament_test_mode'))
        old,_=_load_state()
        count=max(4,min(36,int(request.form.get("count") or len(old.get("players") or []) or 36)))
        target=max(5,min(6,int(request.form.get("target") or old.get("stage1_target") or 5)))
        pot_count=3 if int(request.form.get("pot_count") or old.get("pot_count") or 4) == 3 else 4
        if stage=="registration":
            state=_empty_state(); state["stage1_target"]=target; state["pot_count"]=pot_count
            state["players"]=[{
                "id":f"test-hlv-{i:02d}","name":f"Test HLV {i:02d}","is_test":True,
                "zalo_name":f"Test HLV {i:02d} Zalo","has_host":i%2==1,"host_region":["Bắc","Trung","Nam"][(i-1)%3]
            } for i in range(1,count+1)]
            state["registration_open"]=True
            # Mixed states make the registration screen testable immediately.
            state["registrations"]=[]
            for i,p in enumerate(state["players"][:min(8,count)]):
                status="pending" if i<3 else ("approved" if i<6 else "rejected")
                state["registrations"].append({"id":f"test-reg-{i+1:02d}","user_id":p["id"],"display_name":p["name"],"status":status,"has_host":p["has_host"],"host_region":p["host_region"],"zalo_name":p["zalo_name"],"payment_status":"reported","registered_at":datetime.now(timezone.utc).isoformat()})
        else:
            try:
                state=_build_full_simulation(count,target,pot_count)
            except ValueError as exc:
                flash(str(exc),"error"); return redirect(url_for('admin_tournament_test_mode'))
        state["current_stage"]=stage
        _save_state(state)
        label=dict(STAGES).get(stage,stage)
        flash(f"Đã chuẩn bị dữ liệu Test cho {label}. Bây giờ có thể chọn HLV và xem đúng góc nhìn vòng này.","success")
        view_as=(request.form.get("view_as") or "").strip()
        if request.form.get("open_player_view") == "1":
            if not view_as or not any(p.get("id")==view_as for p in state.get("players") or []):
                view_as=_default_view_for_stage(state,stage)
            return redirect(url_for('admin_tournament_test_public',view_as=view_as,stage=stage))
        return redirect(url_for('admin_tournament_test_mode'))

    @app.post('/admin/tournament-test-mode/reset')
    @login_required
    @admin_required
    @admin_permission_required("system_features_manage")
    def admin_tournament_test_reset():
        aid=_admin_id()
        execute_query(db.table(SANDBOX_TABLE).delete().eq("admin_user_id",aid),"tournament_test_reset",attempts=2)
        flash("Đã xóa toàn bộ dữ liệu Test Mode. Dữ liệu thật không bị ảnh hưởng.","success")
        return redirect(url_for('admin_tournament_test_mode'))
