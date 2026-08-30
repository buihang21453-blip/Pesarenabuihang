from pathlib import Path

APP = Path("app.py").read_text(encoding="utf-8")
MATCH_SERVICE = Path("modules/match_result_service.py").read_text(encoding="utf-8")
RP_ENGINE = Path("modules/rp_engine.py").read_text(encoding="utf-8")


def test_total_matches_is_derived_from_wdl_on_leaderboard():
    assert 'def calculated_total_matches(player):' in APP
    assert 'item["total_matches"] = calculated_total_matches(item)' in APP
    assert 'total_matches = calculated_total_matches(player)' in APP


def test_match_updates_write_synchronized_total():
    assert '"total_matches": new_wins + new_draws + new_losses' in MATCH_SERVICE


def test_rp_engine_uses_wdl_total():
    assert 'def _calculated_total_matches(player: Mapping)' in RP_ENGINE
    assert 'matches = _calculated_total_matches(winner)' in RP_ENGINE
    assert 'matches = _calculated_total_matches(loser)' in RP_ENGINE

def test_version():
    assert 'APP_VERSION = "V1.4.26"' in APP
