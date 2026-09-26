from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
MAP = ROOT / "FEATURE_FILE_MAP.md"


def test_feature_file_map_exists_and_is_versioned():
    text = MAP.read_text(encoding="utf-8")
    assert "# PES Arena — FEATURE → FILE MAP" in text
    assert "**Version:** V1.6.77" in text
    assert "# 9. C1 KNOCKOUT" in text
    assert "# 14. QUICK LOOKUP" in text
    assert "# 15. REGRESSION GROUPS" in text


def test_critical_features_are_mapped_to_real_files():
    text = MAP.read_text(encoding="utf-8")
    required = [
        "modules/tournament_competition_parts/core.py",
        "modules/tournament_competition_parts/rewards.py",
        "modules/tournament_competition_parts/rooms.py",
        "modules/c1_fixed_match_service.py",
        "modules/tournament_routes.py",
        "templates/admin_parts/c1_knockout.html",
        "templates/tournament/components/knockout_dashboard.html",
        "modules/match_result_service.py",
        "modules/rank_daily_policy.py",
        "templates/room_detail.html",
    ]
    for rel in required:
        assert f"`{rel}`" in text
        assert (ROOT / rel).exists(), rel


def test_explicit_code_and_template_paths_in_map_exist():
    text = MAP.read_text(encoding="utf-8")
    refs = set(re.findall(r"`([^`]+\.(?:py|html|css|md))`", text))
    missing = []
    for rel in sorted(refs):
        if "*" in rel or " " in rel:
            continue
        path = ROOT / rel
        if not path.exists() and not (ROOT / "tests" / rel).exists():
            missing.append(rel)
    assert not missing, missing
