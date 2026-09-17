"""V1.6.18: route tests using an isolated fake RPC; no live Supabase writes."""
import sys
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from modules.tournament_competition_parts import league

class FakeApp:
    def __init__(self):
        self.views={}
        self.logger=SimpleNamespace(exception=lambda *a,**kw:None)
    def post(self,path):
        def register(fn): self.views[path]=fn;return fn
        return register

app=FakeApp()
request=SimpleNamespace(form={})
messages=[]
redirects=[]
def flash(message,category): messages.append((message,category))
def url_for(endpoint,**kwargs):
    return {'admin':'/admin','tournaments':'/tournaments',
            'admin_tournament_draw_preview':'/draw-control'}[endpoint]
def redirect(target):
    redirects.append(target)
    return ('REDIRECT',target)
league.register_league({'app':app,'login_required':lambda f:f,'admin_required':lambda f:f,
    'request':request,'flash':flash,'redirect':redirect,'url_for':url_for,
    'current_user':lambda:{'id':'00000000-0000-0000-0000-000000000001'}})
player=app.views['/tournaments/<tournament_id>/club-draft/reward-reroll']
admin=app.views['/admin/tournaments/<tournament_id>/club-draft/reward-reroll-for']

class DB:
    def rpc(self,name,params):
        calls.append((name,params.copy()))
        return SimpleNamespace(name=name)

calls=[]
league.db=DB()
league._club_draft_state=lambda *a,**kw: {'order':['x'],'entries':{'x':{'reward_finalized':False}}}
league._reward_ticket_phase_status=lambda *a,**kw:{'all_finalized':False}
response={'ok':True,'old_club':'Bayern','new_club':'PSG','tickets_remaining':1,'reward_finalized':False}
def success(query,label,attempts=99):
    assert label=='ops_atomic_early_reroll'
    assert attempts==1, 'Never retry a possibly committed ticket spend'
    return SimpleNamespace(data=dict(response))
league.execute_query=success
uid='00000000-0000-0000-0000-000000000002'
request.form={'user_id':uid,'return_to':'draw_control'}
assert admin('tournament')==('REDIRECT','/draw-control')
assert calls[-1][0]=='c1_use_early_club_reroll_ticket'
assert calls[-1][1]['p_user_id']==uid
assert calls[-1][1]['p_actor_role']=='admin'
assert calls[-1][1]['p_actor_user_id']!=uid
assert 'Còn 1 vé' in messages[-1][0] and messages[-1][1]=='success'
print('PASS Admin proxy invokes one atomic RPC, no direct multi-table update')
request.form={}
assert player('tournament')==('REDIRECT','/tournaments')
assert calls[-1][1]['p_actor_role']=='player'
assert calls[-1][1]['p_actor_user_id']==calls[-1][1]['p_user_id']
print('PASS Player invokes same RPC with own identity')
request.form={'user_id':uid}
assert admin('tournament')==('REDIRECT','/admin#c1-admin-gd2')
print('PASS Admin return path independent of draw-control form')
response.update(tickets_remaining=0,reward_finalized=True)
assert player('tournament')==('REDIRECT','/tournaments')
assert 'chốt cuối cùng' in messages[-1][0]
print('PASS Last ticket reports auto-finalized club')

def unavailable(query,label,attempts=99):
    assert attempts==1
    raise RuntimeError('PGRST202 Could not find the function c1_use_early_club_reroll_ticket')
league.execute_query=unavailable
assert player('tournament')==('REDIRECT','/tournaments')
assert 'SQL V1.6.18' in messages[-1][0] and messages[-1][1]=='error'
print('PASS Missing SQL explicitly blocks use with installation guidance')

def failed(query,label,attempts=99):
    assert attempts==1
    raise RuntimeError('database timeout')
league.execute_query=failed
assert admin('tournament')==('REDIRECT','/admin#c1-admin-gd2')
assert 'Không xác nhận được lượt quay' in messages[-1][0]
assert messages[-1][1]=='error'
print('PASS Ambiguous database error does not promise unchanged ticket')

request.form={}
assert admin('tournament')==('REDIRECT','/admin#c1-admin-gd2')
assert 'Không xử lý được' in messages[-1][0]
print('PASS Missing Admin target blocked before RPC')
