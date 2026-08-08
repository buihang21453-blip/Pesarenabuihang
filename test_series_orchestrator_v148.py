from pathlib import Path

ROOT = Path(__file__).resolve().parent


def text(path):
    return (ROOT / path).read_text(encoding='utf-8')


def test_series_modules_exist():
    required = [
        'modules/rank_series/service.py', 'modules/rank_series/repository.py', 'modules/rank_series/routes.py',
        'modules/rank_series/modes/home_away.py', 'modules/rank_series/modes/bo3.py',
        'modules/rank_series/modes/tactical_bo3.py', 'modules/rank_series/modes/ban_pick_bo3.py',
    ]
    for path in required:
        assert (ROOT / path).exists(), path


def test_all_four_series_modes_are_routed():
    service = text('modules/rank_series/service.py')
    for code in ('home_away', 'bo3', 'tactical_bo3', 'ban_pick_bo3'):
        assert code in service
    routes = text('modules/rank_series/routes.py')
    assert '/series/start-next-game' in routes
    assert '/series/tactical-pick' in routes
    assert '/series/ban-pick' in routes


def test_series_child_rp_is_only_finalized_once():
    service = text('modules/rank_series/service.py')
    assert '"delta1": 0, "delta2": 0' in service
    assert 'store_series_rp_on_final_match' in service
    assert 'expected_status="playing"' in service
    assert 'rp_applied' in service


def test_room_confirm_uses_series_orchestrator():
    src = text('modules/room_result_routes.py')
    assert 'is_series_child_match(match)' in src
    assert 'confirm_series_child_match(room, match' in src


def test_series_modes_no_longer_disabled_in_room_ui():
    for path in ('templates/room_detail.html', 'templates/_room_live_content.html'):
        src = text(path)
        assert "url_for('room_series_start_next_game'" in src
        assert 'Series chưa nối luồng trận con' not in src
        assert 'Cần chạy SQL Series và nối luồng trận con trước khi mở thi đấu' not in src


def test_css_isolated_series_module():
    src = text('static/css/room/09-series-orchestrator.css')
    assert '.series-panel' in src
    assert 'position:relative!important' in src
    room = text('templates/room_detail.html')
    assert '09-series-orchestrator.css' in room


if __name__ == '__main__':
    for name, fn in sorted(globals().items()):
        if name.startswith('test_') and callable(fn):
            fn(); print('PASS', name)
