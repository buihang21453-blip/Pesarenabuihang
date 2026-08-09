from pathlib import Path
src = (Path(__file__).parent / 'modules' / 'match_result_service.py').read_text(encoding='utf-8')
route = (Path(__file__).parent / 'modules' / 'room_result_routes.py').read_text(encoding='utf-8')
assert 'phase = "calculate_deltas"' in src
assert 'phase = "repeat_opponent_context"' in src
assert 'phase = "daily_rank_status"' in src
assert 'phase = "daily_positive_cap"' in src
assert 'phase = "update_player1"' in src
assert 'phase = "update_player2"' in src
assert 'phase = "finalize_match"' in src
assert '_restore_player_snapshot' in src
assert 'restore_match_after_result_error' in src
assert 'server_confirm_error' in route
assert '_persist_confirm_error(error_id' in route
print('V1.3.133 confirm safety source checks OK')
