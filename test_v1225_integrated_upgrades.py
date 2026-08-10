from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP = (ROOT / "app.py").read_text(encoding="utf-8")
RP = (ROOT / "modules/rp_engine.py").read_text(encoding="utf-8")
FORMULA = (ROOT / "modules/rp_formula.py").read_text(encoding="utf-8")
READ = (ROOT / "modules/read_model_service.py").read_text(encoding="utf-8")
REPEAT = (ROOT / "modules/repeat_opponent_rp_service.py").read_text(encoding="utf-8")
REBUILD = (ROOT / "modules/admin_ranking_rebuild.py").read_text(encoding="utf-8")


def test_release_version():
    assert 'APP_VERSION = "V1.2.26"' in APP
    assert 'RP_FORMULA_VERSION = "RP_V1.15.0"' in FORMULA


def test_draw_random_rule():
    assert 'DRAW_POINTS_RANGE = (1, 6)' in FORMULA
    assert 'DRAW_GAP_THRESHOLD = 500' in FORMULA
    assert '_randint(rng, *DRAW_POINTS_RANGE)' in RP


def test_repeat_rule_does_not_override_draw_rng():
    draw_block = REPEAT[REPEAT.index('if int(score1) == int(score2):'):REPEAT.index('p1_won =')]
    assert 'delta1, delta2 = 3, 3' not in draw_block
    assert 'delta1, delta2 = 6, 0' not in draw_block


def test_rebuild_keeps_seeded_draw_delta():
    assert 'Giữ nguyên delta hòa do RP Engine sinh ra bằng seed theo match_id.' in REBUILD


def test_read_model_admin_cache():
    assert 'read_model:admin_match_report:' in READ
    assert '_cache_set(cache_key, (report, daily_output), 20)' in READ


def test_core_and_room_ui_are_split():
    for rel in (
        'modules/core/room_runtime.py',
        'modules/core/matchmaking_runtime.py',
        'modules/core/user_repository.py',
        'modules/core/match_repository.py',
        'static/css/room_v2.css',
    ):
        assert (ROOT / rel).is_file(), rel
