from pathlib import Path
ROOT = Path(__file__).resolve().parent

def test_ranked_room_label_uses_selected_mode_config():
    app = (ROOT / 'app.py').read_text(encoding='utf-8')
    assert 'selected_rank_mode = normalize_rank_mode_code(room.get("team_tier") or RANK_RANDOM)' in app
    assert 'room["match_mode_label"] = selected_mode_config.get("label") or "Rank thường Random"' in app

def test_random_route_cannot_fall_through_series_to_rank_random():
    routes = (ROOT / 'modules/room_team_routes.py').read_text(encoding='utf-8')
    assert 'if selected_rank_mode != RANK_RANDOM:' in routes
    assert 'không dùng luồng Quay quân Rank thường' in routes
    assert '"team_tier": selected_rank_mode' in routes

def test_initial_and_fragment_use_same_mode_source_and_series_guard():
    # V1.3.48+ Series đã có orchestrator thật: cả initial render và live fragment
    # phải route 4 Series sang start-next-game, Random3 sang route riêng.
    for name in ('templates/room_detail.html', 'templates/_room_live_content.html'):
        html = (ROOT / name).read_text(encoding='utf-8')
        assert "selected_rank_mode == 'random3_pick1'" in html
        assert "room_series_start_next_game" in html
        assert "selected_rank_mode in ['home_away','bo3','tactical_bo3','ban_pick_bo3']" in html

def test_center_action_layout_guard_loaded_last():
    html = (ROOT / 'templates/room_detail.html').read_text(encoding='utf-8')
    assert 'css/room/08-action-layout-guard.css' in html
    css = (ROOT / 'static/css/room/08-action-layout-guard.css').read_text(encoding='utf-8')
    assert 'left: auto;' in css
    assert 'bottom: auto;' in css
    assert 'transform: none;' in css
    assert '.room-state-waiting_ready' in css
