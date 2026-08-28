from pathlib import Path

ROOT = Path(__file__).parent
APP = (ROOT / "app.py").read_text(encoding="utf-8")
INACTIVITY = (ROOT / "modules/inactivity_rp_service.py").read_text(encoding="utf-8")
RANKING = (ROOT / "templates/ranking.html").read_text(encoding="utf-8")


def test_v14_version_and_ranking_thresholds():
    assert 'APP_VERSION = "V1.4.12"' in APP
    assert 'RANKING_QUALIFY_MATCHES = 5' in APP
    assert 'RANKING_INACTIVE_HIDE_DAYS = 30' in APP


def test_unqualified_players_do_not_receive_official_position():
    assert 'if calculated_total_matches(item) >= RANKING_QUALIFY_MATCHES' in APP
    assert 'item["position"] = None' in APP
    assert 'item["ranking_status"] = "placement"' in APP


def test_ranking_filters_by_matches_and_inactivity_not_points():
    assert 'eligibility = season_ranking_eligibility(' in APP
    assert 'if eligibility.get("visible")' in APP
    eligibility_block = APP[APP.index('def ranking_eligibility'):APP.index('def normalize_player_match_totals')]
    assert 'rank_points' not in eligibility_block
    assert 'inactive_days >= RANKING_INACTIVE_HIDE_DAYS' in eligibility_block


def test_inactivity_decay_waits_until_official_rank_and_stops_at_day_30_target():
    assert 'RANKING_QUALIFY_MATCHES = 5' in INACTIVITY
    assert 'if _completed_rank_matches(user) < RANKING_QUALIFY_MATCHES' in INACTIVITY
    assert 'DECAY_END_DAY = 30' in INACTIVITY
    assert 'min(int(inactive_days or 0), DECAY_END_DAY)' in INACTIVITY


def test_ranking_page_explains_hidden_states_to_signed_in_player():
    assert 'Chưa có thứ hạng chính thức' in RANKING
    assert 'Hoàn thành 1 trận Rank để tự động xuất hiện lại trên BXH.' in RANKING
