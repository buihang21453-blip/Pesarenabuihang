from pathlib import Path
from types import SimpleNamespace
from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).resolve().parents[1]


def _tour():
    return {
        'id': 'tour', 'my_member': None,
        'public_knockout': {
            'generated': True, 'current_round': 'qf', 'my_next': None,
            'tickets': [{
                'user_id':'xuan','rank':3,'name':'Xuân Nam','club':'Liverpool',
                'remaining':0,'total':1,'club_finalized':False,
                'hlv_tier':1,'expected_club_pot':3,'current_club_pot':1,
                'club_pot_mismatch':True,'can_admin_undo_reroll':True,
                'undo_reroll_target':'PSV'
            }],
            'rounds': {'qf': [], 'sf': [], 'final': []},
        }
    }


def test_admin_only_undo_button_points_back_to_psv():
    env=Environment(loader=FileSystemLoader(str(ROOT/'templates')))
    env.globals['url_for']=lambda endpoint, **kw: f'/{endpoint}'
    tpl=env.get_template('tournament/components/knockout_dashboard.html')
    admin=tpl.render(tournament=_tour(),current_user=SimpleNamespace(id='a',role='admin',admin_level='none'))
    user=tpl.render(tournament=_tour(),current_user=SimpleNamespace(id='u',role='user',admin_level='none'))
    assert '↩ Hoàn tác vé Random → PSV' in admin
    assert 'admin_tournament_league_top3_undo_reroll' in admin
    assert '↩ Hoàn tác vé Random → PSV' not in user


def test_backend_restores_previous_club_and_ticket_with_guards():
    src=(ROOT/'modules/tournament_competition_parts/rewards.py').read_text(encoding='utf-8')
    assert 'def _admin_undo_league_top3_reroll' in src
    assert "@app.post('/admin/tournaments/<tournament_id>/league-top3/undo-reroll')" in src
    section=src[src.index('def _admin_undo_league_top3_reroll'):src.index("@app.post('/admin/tournaments/<tournament_id>/league/finish')", src.index('def _admin_undo_league_top3_reroll'))]
    assert 'restore_name=str(reroll_event.get("from") or "").strip()' in section
    assert 'entry["tickets_remaining"]=min(total,remaining+1)' in section
    assert 'restore_owner and restore_owner!=uid' in section
    assert 'restore_pot!=expected_club_pot' in section
    assert '{"pending","scheduled","cancelled"}' in section
    assert '"action":"ADMIN_UNDO_REROLL"' in section
