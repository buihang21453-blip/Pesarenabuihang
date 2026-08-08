from pathlib import Path

def test_room_start_does_not_recheck_rp_eligibility_for_locked_series():
    text=Path("modules/room_team_routes.py").read_text(encoding="utf-8")
    assert 'continuing_series = "__RANK_MODE_LOCKED__"' in text
    assert 'continuation=continuing_series' in text
    # RP/min_matches eligibility remains at mode selection only.
    select=text.index('def room_select_ranked_mode')
    eligibility=text.index('rank_mode_eligibility_for_room(selected_mode, host, guest)', select)
    assert eligibility > select
