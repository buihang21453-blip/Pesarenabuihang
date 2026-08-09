from types import SimpleNamespace
import importlib

class Q:
    def __init__(self,t): self.t=t; self.payload=None; self.filters=[]
    def update(self,p): self.payload=dict(p); return self
    def eq(self,k,v): self.filters.append((k,v)); return self
class DB:
    def table(self,t): return Q(t)
class App:
    def __init__(self): self.routes={}
    def route(self,p,methods=None):
        def deco(fn): self.routes[(p,tuple(methods or ("GET",)))]=fn; return fn
        return deco
class Req:
    form={}; files={}

def test_confirm_keeps_room_confirmed_for_post_match_choice():
    import modules.room_result_routes as rr
    rr=importlib.reload(rr)
    app=App(); writes=[]; flashes=[]
    room={"id":"r1","host_user_id":"h","guest_user_id":"g","status":"waiting_result_confirm","match_id":"m1","team_tier":"Smart Tier Random"}
    match={"id":"m1","status":"waiting_confirm","score1":2,"score2":1,"player1_id":"h","player2_id":"g"}
    def execq(q,label,attempts=4,delay=.25):
        writes.append((label,q.payload,tuple(q.filters)))
        return SimpleNamespace(data=[{"id":"r1"}])
    ctx={
      "app":app,"login_required":lambda f:f,"current_user":lambda:{"id":"g","role":"player"},
      "get_room":lambda _id:dict(room),"get_match":lambda _id:dict(match),"is_admin_user":lambda u:False,
      "flash":lambda m,c="message":flashes.append((c,m)),"redirect":lambda x:x,"url_for":lambda e,**kw:e,
      "request":Req(),"db":DB(),"execute_query":execq,"assert_ranking_rebuild_not_running":lambda:None,
      "now_iso":lambda:"now","future_iso":lambda sec:f"future:{sec}","REMATCH_TIMEOUT_SECONDS":60,
      "RESULT_CONFIRM_TIMEOUT_SECONDS":60,"ttl_cache_delete":lambda *_:None,"cache_delete":lambda *_:None,
      "users_map":lambda:{},"apply_match_result":lambda m:(22,-20),"build_win_streak_event":lambda *a:None,
      "publish_global_streak_event":lambda *a:None,"system_feature_enabled":lambda k:True,
      "SMART_RANDOM_MODE":"Smart Tier Random","FRIENDLY_RANDOM3_MODE":"random3_pick1","MATCH_MODE_RANKED":"ranked",
      "_same_user_id":lambda a,b:str(a)==str(b),"require_room_action":lambda r,a:(True,""),
      "require_room_event":lambda r,e:(r.get("status")=="waiting_result_confirm", "bad event"),
    }
    rr.register_routes(ctx)
    app.routes[("/room/<room_id>/confirm-result",("POST",))]("r1")
    row=next(x for x in writes if x[0]=="confirm_result_finish_room")
    assert row[1]["status"]=="confirmed"
    assert row[1]["confirmed_by_id"]=="g"
    assert row[1]["state_expires_at"]=="future:60"
    assert "match_id" not in row[1]  # giữ nguyên match_id hiện tại, không xóa
    assert "host_score" not in row[1] and "guest_score" not in row[1]
    assert any(c=="success" for c,_ in flashes)
