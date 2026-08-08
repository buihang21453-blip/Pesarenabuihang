from pathlib import Path

from modules.rank_mode_toggle.service import (
    FEATURE_RANDOM3,
    FEATURE_RANK_STANDARD,
    effective_rank_mode,
    enforce_valid_rank_features,
    is_rank_standard_enabled,
    rank_mode_label,
)

ROOT = Path(__file__).resolve().parent


def test_rank_standard_defaults_to_enabled():
    assert is_rank_standard_enabled({}) is True
    assert is_rank_standard_enabled(None) is True


def test_disabling_rank_standard_forces_random3_enabled():
    features = enforce_valid_rank_features({
        FEATURE_RANK_STANDARD: False,
        FEATURE_RANDOM3: False,
    })
    assert features[FEATURE_RANK_STANDARD] is False
    assert features[FEATURE_RANDOM3] is True


def test_disabled_rank_standard_forces_effective_random3_mode():
    features = {FEATURE_RANK_STANDARD: False, FEATURE_RANDOM3: True}
    assert effective_rank_mode("smart_random", features) == "random3_pick1"
    assert effective_rank_mode(None, features) == "random3_pick1"
    assert rank_mode_label("smart_random", features) == "Random 3 chọn 1"


def test_enabled_rank_standard_keeps_requested_mode():
    features = {FEATURE_RANK_STANDARD: True, FEATURE_RANDOM3: True}
    assert effective_rank_mode("smart_random", features) == "smart_random"
    assert effective_rank_mode("random3_pick1", features) == "random3_pick1"


def test_project_wires_rank_toggle_into_admin_and_room_flows():
    app_text = (ROOT / "app.py").read_text(encoding="utf-8")
    admin_text = (ROOT / "modules/admin_system_routes.py").read_text(encoding="utf-8")
    team_text = (ROOT / "modules/room_team_routes.py").read_text(encoding="utf-8")
    rematch_text = (ROOT / "modules/room_rematch_routes.py").read_text(encoding="utf-8")
    result_text = (ROOT / "modules/room_result_routes.py").read_text(encoding="utf-8")

    assert '"rank_standard_enabled": True' in app_text
    assert 'features["friendly_random3_enabled"] = True' in admin_text
    assert 'force_disabled_rank_room_to_random3' in team_text
    assert 'if not system_feature_enabled("rank_standard_enabled")' in rematch_text
    assert 'if not system_feature_enabled("rank_standard_enabled")' in result_text


def test_rank_toggle_ui_and_scoped_css_are_present():
    admin_html = (ROOT / "templates/admin.html").read_text(encoding="utf-8")
    room_html = (ROOT / "templates/room_detail.html").read_text(encoding="utf-8")
    base_html = (ROOT / "templates/base.html").read_text(encoding="utf-8")
    css_path = ROOT / "static/css/rank_mode_toggle.css"

    assert "rank_standard_enabled" in admin_html
    assert "system_features.rank_standard_enabled" in room_html
    assert "rank_mode_toggle.css" in base_html
    assert css_path.exists() and css_path.stat().st_size > 0
