"""Kiểm thử quy tắc giới hạn trận Rank theo từng người chơi."""

from modules import daily_rank_limit_service as service


def test_confirmed_draw_counts_as_one_rank_game():
    match = {
        "status": "confirmed",
        "delta1": 0,
        "delta2": 0,
        "rp_details": {},
    }
    assert service._is_counted_rank_match(match) is True
    assert service._match_counts_for_user(match, "A") is True


def test_out_of_limit_match_counts_for_neither_player():
    match = {
        "status": "confirmed",
        "rp_details": {
            "daily_rank_limits": {
                "counted_user_ids": [],
                "count_rule": "neither_player",
            }
        },
    }
    assert service._match_counts_for_user(match, "A") is False
    assert service._match_counts_for_user(match, "B") is False


def test_normal_match_counts_for_both_players():
    match = {
        "status": "confirmed",
        "rp_details": {
            "daily_rank_limits": {
                "counted_user_ids": ["A", "B"],
                "count_rule": "both_players",
            }
        },
    }
    assert service._match_counts_for_user(match, "A") is True
    assert service._match_counts_for_user(match, "B") is True
    assert service._match_counts_for_user(match, "C") is False


def test_legacy_match_without_count_marker_remains_counted():
    match = {"status": "confirmed", "rp_details": {}}
    assert service._match_counts_for_user(match, "A") is True


def test_player_at_limit_and_player_with_remaining_games_make_match_ineligible(monkeypatch):
    monkeypatch.setattr(service, "daily_rank_limits_enabled", lambda: True)
    monkeypatch.setattr(service, "current_daily_game_limit", lambda moment=None: 10)
    # Trận hiện tại đã nằm trong bảng matches: A là 11/10, B là 7/10.
    counts = {"A": 11, "B": 7}
    monkeypatch.setattr(service, "ranked_games_today", lambda user_id: counts[str(user_id)])

    status = service.daily_rank_match_rp_status("A", "B")
    assert status["rp_eligible"] is False
    assert status["players"]["A"]["over_limit"] is True
    assert status["players"]["B"]["over_limit"] is False


def test_tenth_match_is_still_eligible(monkeypatch):
    monkeypatch.setattr(service, "daily_rank_limits_enabled", lambda: True)
    monkeypatch.setattr(service, "current_daily_game_limit", lambda moment=None: 10)
    monkeypatch.setattr(service, "ranked_games_today", lambda user_id: 10)

    status = service.daily_rank_match_rp_status("A", "B")
    assert status["rp_eligible"] is True
