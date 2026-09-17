"""Mock regression tests for Admin proxy CLB reroll. No real Supabase writes."""
import sys
from types import SimpleNamespace
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from modules.tournament_competition_parts import league

class FakeApp:
    def __init__(self): self.views={}; self.logger=SimpleNamespace(exception=lambda *a,**k: None)
    def post(self,path):
        def register(view): self.views[path]=view;return view
        return register
app=FakeApp()
def identity(view): return view
form={}
request=SimpleNamespace(form=form)
messages=[]
def flash(m,c): messages.append((m,c))
def url_for(endpoint,**kw):
    return {'admin':'/admin','tournaments':'/tournaments','admin_tournament_draw_preview':'/preview'}[endpoint]
def redirect(target): return ('REDIRECT',target)
league.register_league({'app':app,'login_required':identity,'admin_required':identity,
    'request':request,'flash':flash,'redirect':redirect,'url_for':url_for,
    'current_user':lambda:{'id':'ADMIN'},
})
admin=app.views['/admin/tournaments/<tournament_id>/club-draft/reward-reroll-for']
form['user_id']='USER'
league._club_draft_state=lambda *args,**kwargs: (_ for _ in ()).throw(RuntimeError('db-down'))
result=admin('T1')
assert result==('REDIRECT','/admin#c1-admin-gd2'),result
assert any('mã' in m for m,c in messages)
print('PASS preflight DB failure is handled, returns redirect plus error code')
form.clear()
assert admin('T1')==('REDIRECT','/admin#c1-admin-gd2')
print('PASS missing user rejected without database writes')
form['user_id']='USER'
league._club_draft_state=lambda *args,**kwargs:{'order':['USER','U2','U3'],'entries':{'USER':{'allocation_type':'EARLY_REWARD','tickets_remaining':0}}}
league._member=lambda *args,**kwargs:{'status':'active','user_id':'USER'}
assert admin('T1')==('REDIRECT','/admin#c1-admin-gd2')
print('PASS no-ticket flow returns redirect')
state={'order':['USER','U2','U3'],'entries':{'USER':{'allocation_type':'EARLY_REWARD','tickets_remaining':2,'status':'selected','tickets_total':2,'skipped':[]}},'tier_club_pot_rule':'1:3;2:2;3:1','history':[],'all_order':['USER','U2','U3']}
league._club_draft_state=lambda *args,**kwargs:state
league._member=lambda *args,**kwargs:{'status':'active','user_id':'USER','fixed_club_name':'Bayern','pot_no':3}
league._reward_ticket_phase_status=lambda *args,**kwargs:{'deadline_reached':False,'all_finalized':False}
# Helpers defined inside register_league are captured closure cells (not module globals).
reroll=next(cell.cell_contents for name,cell in zip(admin.__code__.co_freevars,admin.__closure__) if name=='_reroll_early_ticket_for')
for name,cell in zip(reroll.__code__.co_freevars,reroll.__closure__):
    if name=='_early_reward_ticket_phase_open': cell.cell_contents=lambda *args,**kwargs:True
old={'id':'CLUBOLD','name':'Bayern','club_key':'bayern'}
new={'id':'CLUBNEW','name':'Real Madrid','club_key':'real-madrid'}
league._one=lambda *args,**kwargs:(old,None)
league._available_clubs=lambda *args,**kwargs:[new]
league.C1_CLUB_POT_BY_NAME={'Bayern':1,'Real Madrid':1}
league.now_iso=lambda:'2026-09-17T00:00:00+07:00'
league.random=SimpleNamespace(choice=lambda pool:pool[0])
ops=[]
class Query:
    def __init__(self,table): self.table=table;self.payload={}
    def update(self,payload): self.payload=payload; return self
    def select(self,*a): return self
    def eq(self,*a): return self
    def is_(self,*a): return self
class DB:
    def table(self,name): return Query(name)
league.db=DB()
def execute(q,label,attempts=2):
    ops.append((q.table,label,q.payload))
    return SimpleNamespace(data=[{'ok':True}])
league.execute_query=execute
def save(*args):
    global state
    state=args[1]
    return SimpleNamespace(data=[{'ok':True}])
for name,cell in zip(reroll.__code__.co_freevars,reroll.__closure__):
    if name=='_save_reward_draft': cell.cell_contents=save
assert admin('T1')==('REDIRECT','/admin#c1-admin-gd2')
assert state['entries']['USER']['tickets_remaining']==1
assert state['entries']['USER']['selected_club']=='Real Madrid'
assert state['history'][-1]['actor_role']=='admin'
assert {name for name,label,payload in ops} == {'tournament_clubs','tournament_members'}
assert len(ops)==3
print('PASS success spends exactly one ticket, changes club, records Admin actor, never writes fixtures')
ops.clear()
league._available_clubs=lambda *args,**kwargs:[]
assert admin('T1')==('REDIRECT','/admin#c1-admin-gd2')
assert not ops and state['entries']['USER']['tickets_remaining']==1
print('PASS empty pot leaves ticket and club intact')
# Assignment failure rolls back reservation; never records a ticket spend.
state['entries']['USER']['tickets_remaining']=1
league._available_clubs=lambda *args,**kwargs:[new]
ops.clear()
def fail_assignment(q,label,attempts=2):
    ops.append((q.table,label,q.payload))
    if label=='ops_early_reroll_member': raise RuntimeError('member update rejected')
    return SimpleNamespace(data=[{'ok':True}])
league.execute_query=fail_assignment
assert admin('T1')==('REDIRECT','/admin#c1-admin-gd2')
assert state['entries']['USER']['tickets_remaining']==1
assert any(label=='ops_early_reroll_rollback_club' for name,label,payload in ops)
print('PASS member update failure rolls back reserved CLB and preserves ticket')
# Save failure also attempts rollback; no extra reward write can be assumed.
league.execute_query=execute
ops.clear()
def fail_save(*args): raise RuntimeError('state save rejected')
for name,cell in zip(reroll.__code__.co_freevars,reroll.__closure__):
    if name=='_save_reward_draft': cell.cell_contents=fail_save
assert admin('T1')==('REDIRECT','/admin#c1-admin-gd2')
assert state['entries']['USER']['tickets_remaining']==1
assert any(label=='ops_early_reroll_restore_member' for name,label,payload in ops)
assert any(label=='ops_early_reroll_rollback_club' for name,label,payload in ops)
print('PASS rejected ticket save attempts conditional restore and retains ticket')
