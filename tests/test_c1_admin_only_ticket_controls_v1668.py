from pathlib import Path
from types import SimpleNamespace
from jinja2 import Environment, FileSystemLoader

ROOT=Path(__file__).resolve().parents[1]

def _tour():
    return {
        'id':'tour','my_member':{'user_id':'u1'},
        'public_knockout':{
            'generated':True,'current_round':'qf','my_next':None,
            'tickets':[{'user_id':'u1','rank':1,'name':'HLV 1','club':'PSV','club_logo':'https://example.com/psv.png','remaining':1,'total':1,'club_finalized':False,'hlv_tier':1,'expected_club_pot':3,'current_club_pot':3,'club_pot_mismatch':False}],
            'rounds':{'qf':[{'status':'pending','status_label':'Chờ thi đấu','completed_legs':0,'leg_count':2,'home_name':'HLV 1','away_name':'HLV 8','home_tier':1,'away_tier':3,'home_club':'PSV','away_club':'Bayern','home_club_logo':'https://example.com/psv.png','away_club_logo':'https://example.com/bayern.png','home_total':0,'away_total':0,'has_score':False,'legs':[{'leg_no':1,'status':'pending'},{'leg_no':2,'status':'pending'}]}],'sf':[],'final':[]},
        }
    }

def _render(user):
    env=Environment(loader=FileSystemLoader(str(ROOT/'templates')))
    env.globals['url_for']=lambda endpoint, **kw: f'/{endpoint}'
    return env.get_template('tournament/components/knockout_dashboard.html').render(tournament=_tour(),current_user=user)

def test_ticket_actions_are_admin_only_in_template():
    user=_render(SimpleNamespace(id='u1',role='user',admin_level='none'))
    admin=_render(SimpleNamespace(id='a',role='admin',admin_level='none'))
    assert '🎲 Admin Random hộ HLV 1' not in user
    assert 'Admin chọn giữ PSV' not in user
    assert '🎲 Admin Random hộ HLV 1' in admin
    assert '✅ Admin chọn giữ PSV · Không dùng vé' in admin
    assert 'Hoàn tác vé Random' not in admin

def test_player_routes_are_blocked_server_side():
    src=(ROOT/'modules/tournament_competition_parts/rewards.py').read_text(encoding='utf-8')
    reroll=src[src.index("@app.post('/tournaments/<tournament_id>/league-top3/reroll-club')"):src.index("@app.post('/admin/tournaments/<tournament_id>/league-top3/reroll-club-for')")]
    keep=src[src.index("@app.post('/tournaments/<tournament_id>/league-top3/keep-club')"):src.index("@app.post('/admin/tournaments/<tournament_id>/league-top3/keep-club-for')")]
    assert 'chỉ Admin mới được phép sử dụng hộ HLV' in reroll
    assert '_league_top3_reroll_for(tournament_id,uid)' not in reroll
    assert 'Chỉ Admin mới được phép chốt giữ CLB' in keep
    assert '_league_top3_keep_current_club(tournament_id,uid)' not in keep

def test_knockout_club_logos_are_large_and_clear():
    css=(ROOT/'templates/tournament/styles.html').read_text(encoding='utf-8')
    assert '.c1-ko-club-logo{width:30px;height:30px' in css
    assert '.c1-ko-inline-club-logo{width:24px;height:24px' in css
    html=_render(SimpleNamespace(id='u1',role='user',admin_level='none'))
    assert 'https://example.com/psv.png' in html
    assert 'https://example.com/bayern.png' in html
