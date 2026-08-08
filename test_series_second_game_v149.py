from pathlib import Path

ROOT = Path(__file__).resolve().parent

def text(path):
    return (ROOT / path).read_text(encoding="utf-8")

def test_live_partial_routes_series_to_orchestrator():
    src = text("templates/partials/room_dynamic_state.html")
    assert "room_series_start_next_game" in src
    assert "selected_rank_mode in ['home_away','bo3','tactical_bo3','ban_pick_bo3']" in src

def test_all_room_primary_templates_route_series_to_orchestrator():
    for path in ("templates/room_detail.html", "templates/_room_live_content.html", "templates/partials/room_dynamic_state.html"):
        src = text(path)
        assert "room_series_start_next_game" in src, path

def test_legacy_random_endpoint_defensively_dispatches_series():
    src = text("modules/room_team_routes.py")
    assert "if is_series_mode(selected_rank_mode):" in src
    assert "result = prepare_next_series_game(room)" in src
    series_pos = src.index("if is_series_mode(selected_rank_mode):")
    rank_guard_pos = src.index("if selected_rank_mode != RANK_RANDOM:", series_pos)
    assert series_pos < rank_guard_pos

def test_legacy_guard_does_not_block_series_on_stale_team_snapshot():
    src = text("modules/room_team_routes.py")
    assert 'and not is_series_mode(requested_mode)' in src

def test_second_game_reset_keeps_series_mode_and_clears_match():
    src = text("modules/rank_series/service.py")
    assert '"team_tier": series.get("mode_code")' in src
    assert '"match_id": None' in src
    assert 'guest_ready = True' in src

def test_version_bumped():
    assert 'APP_VERSION = "1.3.50"' in text("app.py")

if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); print("PASS", name)
