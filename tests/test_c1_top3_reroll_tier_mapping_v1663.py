from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_reroll_uses_member_tier_to_compute_expected_club_pot():
    src = (ROOT / "modules/tournament_competition_parts/rewards.py").read_text(encoding="utf-8")
    assert 'hlv_tier=int(member.get("pot_no") or 0)' in src
    assert 'expected_club_pot=4-hlv_tier if hlv_tier in {1,2,3} else 0' in src
    reroll = src[src.index('def _league_top3_reroll_for'):src.index('def _repair_league_top3_wrong_pot')]
    assert '==expected_club_pot' in reroll
    assert '==3]' not in reroll


def test_admin_can_repair_historical_wrong_pot_without_spending_another_ticket():
    src = (ROOT / "modules/tournament_competition_parts/rewards.py").read_text(encoding="utf-8")
    assert "def _repair_league_top3_wrong_pot" in src
    assert "admin_tournament_league_top3_repair_wrong_pot" in src
    repair = src[src.index('def _repair_league_top3_wrong_pot'):src.index('def _league_top3_keep_current_club')]
    assert '"ticket_spent":False' in repair
    assert 'tickets_remaining' not in repair


def test_knockout_dashboard_surfaces_mapping_and_repair_button():
    tpl = (ROOT / "templates/tournament/components/knockout_dashboard.html").read_text(encoding="utf-8")
    assert "Tier 1 → Pot 3 · Tier 2 → Pot 2 · Tier 3 → Pot 1" in tpl
    assert "club_pot_mismatch" in tpl
    assert "🔧 Sửa CLB sai Tier/Pot" in tpl
    assert "expected_club_pot" in tpl
