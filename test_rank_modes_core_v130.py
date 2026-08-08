import random
from modules.rank_modes import service


def setup_module(): service.configure({})
def player(rp, matches): return {'rating':rp,'total_matches':matches}

def test_unlocks():
 assert service.check_rank_mode_eligibility('rank_random',player(1000,0))['eligible']
 assert not service.check_rank_mode_eligibility('random3_pick1',player(1000,4))['eligible']
 assert service.check_rank_mode_eligibility('random3_pick1',player(1000,5))['eligible']
 assert service.check_rank_mode_eligibility('bo3',player(1300,15),player(1600,20))['eligible']
 assert not service.check_rank_mode_eligibility('bo3',player(1300,15),player(1900,20))['eligible']

def test_bo3_results_and_rp():
 games=[{'winner_side':'player1'},{'winner_side':'player1'}]
 result=service.resolve_series_result('bo3',games)
 assert result['status']=='completed' and result['score']=='2-0'
 rp=service.calculate_mode_rp('bo3',result,'player1',rng=random.Random(1))
 assert rp['winner_base']==32 and -2 <= rp['winner_variance'] <= 3 and 30 <= rp['winner_final'] <= 35
 assert rp['loser_base']==-28 and -2 <= rp['loser_variance'] <= 3 and -30 <= rp['loser_final'] <= -25
 assert rp['player1']==rp['winner_final'] and rp['player2']==rp['loser_final']

def test_home_away_aggregate_split_rp():
 result=service.resolve_series_result('home_away',[{'player1_score':1,'player2_score':0,'winner_side':'player1'},{'player1_score':0,'player2_score':2,'winner_side':'player2'}])
 assert result['aggregate_score']=='1-2' and result['winner_side']=='player2'
 rp=service.calculate_mode_rp('home_away',result,'player2',rng=random.Random(2))
 assert rp['winner_base']==15 and 13 <= rp['winner_final'] <= 18
 assert rp['loser_base']==-10 and -12 <= rp['loser_final'] <= -7

def test_home_away_one_win_one_draw():
 result=service.resolve_series_result('home_away',[{'player1_score':1,'player2_score':0,'winner_side':'player1'},{'player1_score':0,'player2_score':0,'winner_side':'draw'}])
 rp=service.calculate_mode_rp('home_away',result,'player1',rng=random.Random(3))
 assert rp['winner_base']==22 and 20 <= rp['winner_final'] <= 25
 assert rp['loser_base']==-22 and -24 <= rp['loser_final'] <= -19

def test_draw_rules_random_1_to_6():
 result={'winner_side':'draw','draws':2}
 same=service.calculate_mode_rp('home_away',result,None,player1_rp=1200,player2_rp=1450,rng=random.Random(4))
 assert 1 <= same['player1'] <= 6 and 1 <= same['player2'] <= 6
 gap=service.calculate_mode_rp('home_away',result,None,player1_rp=900,player2_rp=1400,rng=random.Random(5))
 assert 1 <= gap['player1'] <= 6 and gap['player2']==0

def test_forfeit_fixed_minus_20():
 result=service.resolve_series_result('tactical_bo3',[],forfeiting_user_id='u1')
 rp=service.calculate_mode_rp('tactical_bo3',result,'player2',True)
 assert rp['winner']==20 and rp['loser']==-20 and rp['forfeit_win']==20 and rp['forfeit_loss']==-20

def test_supabase_audit_payload_only_contains_calc_fields():
 result={'player1_base':32,'player1_variance':-1,'player1_final':31,'player2_base':-28,'player2_variance':2,'player2_final':-26}
 assert service.mode_rp_audit_payload(result)=={'rp_base1':32,'rp_variance1':-1,'rp_final1':31,'rp_base2':-28,'rp_variance2':2,'rp_final2':-26}
 assert service.mode_series_rp_audit_payload(result)=={'rp_base_player1':32,'rp_variance_player1':-1,'rp_final_player1':31,'rp_base_player2':-28,'rp_variance_player2':2,'rp_final_player2':-26}
