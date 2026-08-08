import importlib.util
from pathlib import Path

def load_service():
    # Import package normally; module itself only uses stdlib + catalog.
    import modules.rank_modes.service as service
    return service

class FixedRng:
    def randint(self,a,b): return a

def test_all_four_series_forfeit_are_plus20_minus20(monkeypatch):
    svc=load_service()
    configs={
      'home_away': {'series_type':'aggregate_two_legs','rp':{'forfeit_win':20,'forfeit_loss':-20}},
      'bo3': {'series_type':'best_of','rp':{'forfeit_win':20,'forfeit_loss':-20}},
      'tactical_bo3': {'series_type':'best_of','rp':{'forfeit_win':20,'forfeit_loss':-20}},
      'ban_pick_bo3': {'series_type':'best_of','rp':{'forfeit_win':20,'forfeit_loss':-20}},
    }
    monkeypatch.setattr(svc,'get_rank_mode',lambda code: configs[code])
    for code in configs:
      r=svc.calculate_mode_rp(code,{'reason':'forfeit','forfeiting_side':'player1'},forfeit=True)
      assert r['player1']==-20 and r['player2']==20
      assert r['winner']==20 and r['loser']==-20
      r=svc.calculate_mode_rp(code,{'reason':'forfeit','forfeiting_side':'player2'},forfeit=True)
      assert r['player1']==20 and r['player2']==-20

def test_forfeit_has_no_random_variance(monkeypatch):
    svc=load_service()
    monkeypatch.setattr(svc,'get_rank_mode',lambda code:{'series_type':'best_of','rp':{'forfeit_win':20,'forfeit_loss':-20}})
    r=svc.calculate_mode_rp('bo3',{'reason':'forfeit','forfeiting_side':'player1'},forfeit=True,rng=FixedRng())
    assert r['player1']==-20 and r['player2']==20
