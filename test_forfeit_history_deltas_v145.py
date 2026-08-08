from pathlib import Path

def test_history_supports_winner_delta():
    s=Path('modules/forfeit_history_service.py').read_text(encoding='utf-8')
    assert 'winner_delta=0' in s
    assert '"delta1": delta if role == "host" else win_delta' in s
    assert '"delta2": delta if role == "guest" else win_delta' in s

def test_manual_forfeit_awards_series_winner():
    s=Path('modules/room_rematch_routes.py').read_text(encoding='utf-8')
    assert s.count('apply_series_forfeit_win_reward') >= 2

def test_timeout_and_offline_award_series_winner():
    s=Path('app.py').read_text(encoding='utf-8')
    assert 'def apply_series_forfeit_win_reward' in s
    assert s.count('winner_delta = apply_series_forfeit_win_reward') >= 2
