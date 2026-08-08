from pathlib import Path
import importlib

ROOT = Path(__file__).resolve().parent


def text(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_version_1350():
    assert 'APP_VERSION = "1.3.50"' in text("app.py")


def test_new_rooms_use_canonical_enabled_mode_resolver():
    app = text("app.py")
    assert app.count('"team_tier": default_rank_room_team_tier()') >= 3
    assert 'SMART_RANDOM_MODE if system_feature_enabled("rank_standard_enabled")' not in app


def test_room_enrichment_no_longer_forces_random3_when_rank_random_is_disabled():
    app = text("app.py")
    assert 'room["team_tier"] = FRIENDLY_RANDOM3_MODE' not in app[app.index("def enrich_room"):app.index("def list_rooms")]
    assert "def _reconcile_waiting_rank_room_mode" in app
    assert 'note.startswith("__SERIES_ACTIVE__")' in app


def test_default_mode_resolution_chooses_only_enabled_mode(monkeypatch):
    svc = importlib.import_module("modules.rank_modes.service")
    configs = {code: {"enabled": code == "home_away"} for code in svc.MODE_ORDER}
    monkeypatch.setattr(svc, "get_rank_mode_configs", lambda: configs)
    assert svc.default_rank_mode_code() == "home_away"
    assert svc.resolve_enabled_rank_mode("smart_random") == "home_away"
    assert svc.default_rank_room_team_tier() == "home_away"


def test_polling_uses_lightweight_room_snapshot_and_tracks_series_version():
    app = text("app.py")
    state = app[app.index("def api_room_state"):app.index("# =========================\n# Auth")]
    assert "get_room_poll_snapshot(room_id)" in state
    assert "get_room(room_id)" not in state
    assert "get_series_poll_version(room)" in state
    assert "build_room_state_key(room, series_version)" in state
    key = app[app.index("def build_room_state_key"):app.index("def polling_stop_response")]
    assert 'str(room.get("team_tier"))' in key
    assert 'str(room.get("updated_at"))' in key


def test_rank_mode_catalog_removes_daily_quota_n_plus_one():
    svc = text("modules/rank_modes/service.py")
    block = svc[svc.index("def rank_mode_catalog_for_players"):svc.index("def is_series_mode")]
    assert "host_status=status_fn" in block
    assert "guest_status=status_fn" in block
    assert "rank_mode_daily_quota_status(" not in block


def test_series_auto_confirm_never_uses_single_match_rp_engine():
    app = text("app.py")
    block = app[app.index("def auto_confirm_expired_match_if_needed"):app.index("def _safe_player_display_name")]
    assert "if is_series_child_match(match):" in block
    assert "confirm_series_child_match(" in block


def test_series_dispute_cancels_orphanable_series():
    routes = text("modules/room_result_routes.py")
    assert "disputed_was_series_child" in routes
    assert 'cancel_active_series_for_room(room_id, reason="child_match_disputed")' in routes
    service = text("modules/rank_series/service.py")
    cancel = service[service.index("def cancel_active_series_for_room"):service.index("def finalize_series_forfeit")]
    assert 'table("match_series_games")' in cancel
    assert '"status": "cancelled"' in cancel
