"""Tournament Test Mode V1.4.31.

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
            "stage1_target": 5,
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
                return dict(rows[0]["state"]), True
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
            stage1_matches=_decorate_matches(state.get("stage1_matches") or [],players),
            league_matches=_decorate_matches(state.get("league_matches") or [],players),
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

    @app.post('/admin/tournament-test-mode/generate-stage1')
    @login_required
    @admin_required
    @admin_permission_required("system_features_manage")
    def admin_tournament_test_generate_stage1():
        state,_=_load_state(); players=state.get("players") or []
        if len(players)<4:
            flash("Hãy tạo HLV Test trước.","warning"); return redirect(url_for('admin_tournament_test_mode'))
        target=int(state.get("stage1_target") or 5)
        rounds=_round_robin_rounds(players)[:target]
        matches=[]; seq=1
        for rnd,pairs in enumerate(rounds,1):
            for a,b in pairs:
                hs,av=_score(f"s1-{rnd}-{a}-{b}")
                matches.append({"id":f"s1-{seq}","round":rnd,"home":a,"away":b,"home_score":hs,"away_score":av,"status":"completed"}); seq+=1
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
        pot_count=max(1,min(8,int(request.form.get("pot_count") or 4)))
        pots=[[] for _ in range(pot_count)]
        chunk=(len(ranking)+pot_count-1)//pot_count
        for i,row in enumerate(ranking):
            p=min(i//chunk,pot_count-1)
            pots[p].append({"user_id":row["user_id"],"display_name":row["display_name"],"seed":i+1,"pot":p+1})
        state["pots"]=pots; _save_state(state)
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
        # Reuse the same deterministic logic in one request.
        count=max(4,min(36,int(request.form.get("count") or 16)))
        target=max(5,min(6,int(request.form.get("target") or 5)))
        state=_empty_state(); state["stage1_target"]=target
        players=[{"id":f"test-hlv-{i:02d}","name":f"Test HLV {i:02d}","is_test":True} for i in range(1,count+1)]; state["players"]=players
        rounds=_round_robin_rounds(players)[:target]; s1=[]; seq=1
        for rnd,pairs in enumerate(rounds,1):
            for a,b in pairs:
                hs,av=_score(f"all-s1-{rnd}-{a}-{b}"); s1.append({"id":f"s1-{seq}","round":rnd,"home":a,"away":b,"home_score":hs,"away_score":av,"status":"completed"}); seq+=1
        state["stage1_matches"]=s1; state["stage1_ranking"]=_ranking(players,s1)
        pot_count=4; chunk=(len(players)+pot_count-1)//pot_count; pots=[[] for _ in range(pot_count)]
        for i,row in enumerate(state["stage1_ranking"]):
            p=min(i//chunk,pot_count-1); pots[p].append({"user_id":row["user_id"],"display_name":row["display_name"],"seed":i+1,"pot":p+1})
        state["pots"]=pots
        members_by_pot={idx+1:[x["user_id"] for x in pot] for idx,pot in enumerate(pots)}; seen=set(); lg=[]; seq=1
        for p in players:
            uid=p["id"]
            for candidates in members_by_pot.values():
                for opp in sorted(x for x in candidates if x!=uid):
                    key=tuple(sorted((uid,opp)))
                    if key in seen: continue
                    seen.add(key); hs,av=_score(f"all-lg-{uid}-{opp}"); lg.append({"id":f"lg-{seq}","home":uid,"away":opp,"home_score":hs,"away_score":av,"status":"completed"}); seq+=1; break
        state["league_matches"]=lg; state["league_ranking"]=_ranking(players,lg)
        qualifiers=[r["user_id"] for r in state["league_ranking"][:16]]; names={p["id"]:p["name"] for p in players}; ko=[]; current=qualifiers; labels={16:"R16",8:"Tứ kết",4:"Bán kết",2:"Chung kết"}
        while len(current)>=2:
            nxt=[]; prs=[]
            for i in range(0,len(current)-1,2):
                a,b=current[i],current[i+1]; a1,b1=_score(f"all-ko1-{a}-{b}"); b2,a2=_score(f"all-ko2-{b}-{a}"); aa,bb=a1+a2,b1+b2; w=a if aa>bb or (aa==bb and a<b) else b; nxt.append(w); prs.append({"home":a,"away":b,"home_name":names.get(a,a),"away_name":names.get(b,b),"leg1":f"{a1}-{b1}","leg2":f"{b2}-{a2}","aggregate":f"{aa}-{bb}","winner":w,"winner_name":names.get(w,w)})
            ko.append({"name":labels.get(len(current),f"Top {len(current)}"),"pairs":prs}); current=nxt
            if len(current)==1: break
        state["knockout"]=ko; _save_state(state)
        flash("Đã tạo sandbox và mô phỏng toàn bộ giải đến Chung kết.","success")
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
