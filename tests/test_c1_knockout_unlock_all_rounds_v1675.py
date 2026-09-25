from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def test_v1675_version():
    assert 'APP_VERSION = "V1.6.76"' in read('app.py')


def test_knockout_control_payload_includes_qf_sf_final():
    core = read('modules/tournament_competition_parts/core.py')
    assert 'round_order={"qf":0,"sf":1,"final":2}' in core
    assert 'round_labels={"qf":"Tứ kết","sf":"Bán kết","final":"Chung kết"}' in core
    assert 'entry=entries.get(key) or {}' in core
    assert 'unlocked=bool(entry.get("unlocked"))' in core


def test_advanced_rounds_are_created_as_normal_knockout_pairs_and_default_locked():
    core = read('modules/tournament_competition_parts/core.py')
    assert 'nxt={"playoff":"r16","r16":"qf","qf":"sf","sf":"final"}.get(current)' in core
    assert 'for a,b in pairs: _insert_ko_pair(tournament_id,nxt,a,b,two_legged=(nxt!="final"))' in core
    # No automatic unlock is written when a later round pair is created.
    advance = core.split('def _maybe_advance_knockout', 1)[1].split('def _timing_payload', 1)[0]
    assert 'KNOCKOUT_UNLOCK_KEY' not in advance


def test_admin_panel_explicitly_controls_all_three_rounds():
    tpl = read('templates/admin_parts/c1_knockout.html')
    assert 'Tứ kết · Bán kết · Chung kết' in tpl
    assert '🔓 Mở cặp này' in tpl
    assert '🔒 Khóa lại' in tpl


def test_public_payload_and_backend_guard_are_round_agnostic():
    routes = read('modules/tournament_routes.py')
    core = read('modules/tournament_competition_parts/core.py')
    rooms = read('modules/tournament_competition_parts/rooms.py')
    fixed = read('modules/c1_fixed_match_service.py')
    assert 'round_order = {"qf": 0, "sf": 1, "final": 2}' in routes
    assert 'if not match or str(match.get("stage_code") or "")!="knockout":' in core
    assert '_knockout_pair_is_unlocked' in rooms
    assert 'knockout_match_unlocks_v1' in fixed
