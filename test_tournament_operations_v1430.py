from pathlib import Path
ROOT=Path(__file__).parent
APP=(ROOT/'app.py').read_text(encoding='utf-8')
MOD=(ROOT/'modules/tournament_competition.py').read_text(encoding='utf-8')
SQL=(ROOT/'docs/update_tournament_operations_v1_4_30.sql').read_text(encoding='utf-8')
DETAIL=(ROOT/'templates/tournament_detail.html').read_text(encoding='utf-8')
ADMIN=(ROOT/'templates/admin.html').read_text(encoding='utf-8')
def test_module_registered():
    assert 'modules.tournament_competition' in APP and '_register_tournament_competition_routes' in APP
def test_independent_tables():
    for name in ['tournament_matches','tournament_stages','tournament_clubs','tournament_hosts','tournament_schedule_requests','tournament_reward_rules']:
        assert name in SQL
def test_stage1_rules_present():
    assert 'match_target' in MOD and 'min_opponents' in MOD and 'max_matches_per_opponent' in MOD
def test_ranking_and_progress():
    assert 'opponent_count' in MOD and 'points' in MOD and 'percent' in MOD
def test_pot_club_league_schedule_host_knockout_rewards():
    for token in ['generate_pots','club_select','league_generate','match_schedule','host_add','knockout_match','reward_add']:
        assert token in MOD
def test_player_detail_sections():
    for text in ['GĐ1 · Tiến độ HLV','BXH GĐ1','Chọn CLB cố định','League Phase','Lịch & đặt lịch thi đấu','Host đang rảnh','Knockout · Hai lượt','Thưởng sớm']:
        assert text in DETAIL
def test_admin_has_ops():
    for text in ['Điều hành CHAMPION LEAGUE ARENA','Pot / hạt giống','CLB cố định','League Phase','Host','Knockout / hai lượt','Thưởng sớm']:
        assert text in ADMIN
