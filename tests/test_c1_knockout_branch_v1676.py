from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")

def test_version_bumped():
    assert 'APP_VERSION = "V1.6.76"' in read('app.py')

def test_qf_slot_keys_saved_at_generation():
    rewards = read('modules/tournament_competition_parts/rewards.py')
    assert '"qf_pair_keys":[]' in rewards
    assert 'state["qf_pair_keys"].append(_insert_ko_pair' in rewards

def test_semifinal_branch_is_qf1_qf3_and_qf2_qf4():
    core = read('modules/tournament_competition_parts/core.py')
    advance = core.split('def _maybe_advance_knockout', 1)[1].split('def _timing_payload', 1)[0]
    assert 'pairs=[(entrants[0],entrants[2]),(entrants[1],entrants[3])]' in advance
    assert 'preferred=[str(x) for x in (state.get("qf_pair_keys") or []) if x]' in advance
    assert 'seeds=[str(x) for x in (state.get("direct_top8") or []) if x]' in advance

def test_bracket_visual_matches_semifinal_branch():
    html = read('templates/tournament/components/knockout_dashboard.html')
    left = html.split('c1-ko-side-left', 1)[1].split('c1-ko-center', 1)[0]
    right = html.split('c1-ko-side-right', 1)[1]
    assert 'TỨ KẾT 1' in left and 'TỨ KẾT 3' in left and 'BÁN KẾT 1' in left
    assert 'TỨ KẾT 2' not in left and 'TỨ KẾT 4' not in left
    assert 'TỨ KẾT 2' in right and 'TỨ KẾT 4' in right and 'BÁN KẾT 2' in right

def test_admin_explains_branch_rule():
    html = read('templates/admin_parts/c1_knockout.html')
    assert 'TK1 gặp TK3' in html
    assert 'TK2 gặp TK4' in html
