from pathlib import Path

ROOT = Path(__file__).resolve().parent


def test_random3_has_final_six_club_uniqueness_guard():
    text = (ROOT / "app.py").read_text(encoding="utf-8")
    assert "len(all_options) != 6 or len(set(normalized_names)) != 6" in text
    assert "extra_excluded=picked_names" in text


def test_feature_save_cleanup_cannot_turn_successful_save_into_500():
    text = (ROOT / "modules/admin_system_routes.py").read_text(encoding="utf-8")
    assert "def best_effort(query, operation_name):" in text
    assert "cleanup_errors.append" in text
    assert '"team_tier": SMART_RANDOM_MODE' in text
