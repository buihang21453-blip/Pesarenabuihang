from pathlib import Path
from types import SimpleNamespace
import importlib

ROOT = Path(__file__).resolve().parent
APP_SOURCE = (ROOT / "app.py").read_text(encoding="utf-8")
SERVICE_SOURCE = (ROOT / "modules" / "match_result_service.py").read_text(encoding="utf-8")


def test_release_version_and_root_cause_fix_are_present():
    assert 'APP_VERSION = "V1.4.17"' in APP_SOURCE
    assert "from modules.rp_engine import get_win_streak_bonus" in SERVICE_SOURCE
    assert SERVICE_SOURCE.count("get_win_streak_bonus(") >= 2


class FakeQuery:
    def __init__(self, table_name):
        self.table_name = table_name
        self.action = None
        self.payload = None
        self.filters = []

    def update(self, payload):
        self.action = "update"
        self.payload = dict(payload)
        return self

    def select(self, *_args, **_kwargs):
        self.action = "select"
        return self

    def eq(self, key, value):
        self.filters.append(("eq", key, value))
        return self

    def limit(self, value):
        self.filters.append(("limit", value))
        return self


class FakeDB:
    def table(self, table_name):
        return FakeQuery(table_name)


def build_service_context(labels):
    players = {
        "u1": {
            "id": "u1", "rank_points": 1000, "wins": 2, "draws": 0,
            "losses": 1, "total_matches": 3, "goals_for": 5,
            "goals_against": 3, "streak": 2,
        },
        "u2": {
            "id": "u2", "rank_points": 1000, "wins": 1, "draws": 0,
            "losses": 2, "total_matches": 3, "goals_for": 3,
            "goals_against": 5, "streak": 0,
        },
    }

    def execute_query(query, label, attempts=4, delay=0.25):
        del attempts, delay
        labels.append((label, query.table_name, query.action, query.payload, tuple(query.filters)))
        if label == "claim_match_result":
            return SimpleNamespace(data=[{"id": "m1", "status": "processing_result"}])
        if label == "finalize_match_result":
            return SimpleNamespace(data=[{"id": "m1", "status": "confirmed"}])
        if label.startswith("update_player_after_match:"):
            return SimpleNamespace(data=[{"id": label.split(":", 1)[1]}])
        return SimpleNamespace(data=[])

    return {
        "db": FakeDB(),
        "execute_query": execute_query,
        "assert_ranking_rebuild_not_running": lambda: None,
        "get_user": lambda user_id: dict(players[user_id]),
        "calculate_deltas": lambda *_args, **_kwargs: (25, -15),
        "validate_ranked_deltas": lambda _s1, _s2, d1, d2: (int(d1), int(d2)),
        "_safe_int": lambda value, default=0: int(default if value is None else value),
        "RP_RANDOM_SEED_NAMESPACE": "PES_ARENA_TEST",
        "now_iso": lambda: "2026-08-03T09:00:00+00:00",
        "get_match": lambda _match_id: None,
        "apply_host_xp_factor": lambda delta, factor=0.95: round(int(delta) * float(factor)),
        "HOST_WIN_FACTOR": 0.95,
        "PLACEMENT_MATCHES": 10,
        "repeat_opponent_context": lambda _match: {
            "prior_encounters": 0, "encounter_number": 1,
            "wins": {"u1": 0, "u2": 0}, "draw_bonus_used": False,
        },
        "apply_repeat_opponent_rules": lambda _m, _p1, _p2, _s1, _s2, d1, d2, **_kwargs: (
            int(d1), int(d2), {"streak_eligible": True, "encounter_number": 1}
        ),
        "daily_rank_match_rp_status": lambda *_user_ids: {
            "enabled": True, "rp_eligible": True, "game_limit": 10,
            "players": {}, "reason": "within_daily_limit",
        },
        "apply_daily_positive_rp_cap": lambda _uid, delta, exclude_match_id=None: (
            int(delta), None
        ),
        "RP_FORMULA_VERSION": "TEST",
        "formula_summary": lambda: "test formula",
        "ttl_cache_delete": lambda *_keys: None,
        "create_user_notification": lambda *_args, **_kwargs: None,
        "grant_weekly_rp_rewards_for_users": lambda *_args, **_kwargs: None,
        "sync_achievements_for_users": lambda *_args, **_kwargs: None,
    }


def test_apply_match_result_reaches_confirmation_without_missing_helper_name():
    import modules.match_result_service as service
    service = importlib.reload(service)
    labels = []
    service.configure(build_service_context(labels))

    match = {
        "id": "m1",
        "status": "waiting_confirm",
        "score1": 2,
        "score2": 1,
        "player1_id": "u1",
        "player2_id": "u2",
        # Host is the losing player so the host factor does not obscure the expected winner delta.
        "host_user_id": "u2",
        "created_at": "2026-08-03T08:00:00+00:00",
        "winner_id": "u1",
        "loser_id": "u2",
    }

    delta1, delta2 = service.apply_match_result(match)

    assert (delta1, delta2) == (25, -15)
    assert [label for label, *_rest in labels].count("claim_match_result") == 1
    assert [label for label, *_rest in labels].count("finalize_match_result") == 1
    assert [label for label, *_rest in labels].count("update_player_after_match:u1") == 1
    assert [label for label, *_rest in labels].count("update_player_after_match:u2") == 1


def test_confirmed_match_is_idempotent_and_does_not_write_rp_twice():
    import modules.match_result_service as service
    service = importlib.reload(service)
    labels = []
    service.configure(build_service_context(labels))

    result = service.apply_match_result({
        "id": "m1",
        "status": "confirmed",
        "score1": 2,
        "score2": 1,
        "player1_id": "u1",
        "player2_id": "u2",
        "delta1": 25,
        "delta2": -15,
    })

    assert result == (25, -15)
    assert labels == []


def test_session_guard_from_v1144178_is_preserved():
    session_js = (ROOT / "static" / "js" / "session-timeout.js").read_text(encoding="utf-8")
    assert "ROOM_MATCH_INACTIVITY_TIMEOUT_SECONDS = 4 * 60 * 60" in APP_SOURCE
    assert 'request.path.startswith("/room/")' in APP_SOURCE
    assert 'request.path.startswith("/api/room/")' in APP_SOURCE
    assert 'const isRoomPage = global.location.pathname.startsWith("/room/");' in session_js
