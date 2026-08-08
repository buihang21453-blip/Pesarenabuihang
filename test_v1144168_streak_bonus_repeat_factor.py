from modules.repeat_opponent_rp_service import apply_repeat_opponent_rules


def _configure():
    import modules.repeat_opponent_rp_service as svc
    svc.configure({
        "system_feature_enabled": lambda key: True,
        "get_repeat_opponent_rp_config": lambda: {
            "winner_factors": [100, 60, 30, 0],
            "loser_factors": [100, 70, 40, 10],
        },
    })


def test_third_repeat_win_keeps_full_streak_10_bonus():
    _configure()
    match = {"player1_id": "a", "player2_id": "b"}
    context = {"encounter_number": 3, "wins": {"a": 2, "b": 0}}
    d1, d2, details = apply_repeat_opponent_rules(
        match, {"rank_points": 1500}, {"rank_points": 1500},
        2, 1, 38, -20, context=context, streak_bonus1=15, streak_bonus2=0
    )
    assert d1 == 22  # round((38-15)*0.3) + 15 = 7 + 15
    assert d2 == -8  # round(20*0.4)
    assert details["winner_streak_bonus"] == 15
    assert details["streak_bonus_scaled"] is False
    assert details["streak_eligible"] is True


def test_fourth_repeat_win_zeroes_base_but_not_earned_bonus():
    _configure()
    match = {"player1_id": "a", "player2_id": "b"}
    context = {"encounter_number": 4, "wins": {"a": 3, "b": 0}}
    d1, _, details = apply_repeat_opponent_rules(
        match, {"rank_points": 1500}, {"rank_points": 1500},
        2, 1, 38, -20, context=context, streak_bonus1=15
    )
    assert d1 == 0
    assert details["winner_streak_bonus"] == 0
    assert details["streak_eligible"] is False
