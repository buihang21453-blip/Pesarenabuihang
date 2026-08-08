from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parent
SOURCE = (ROOT / "modules" / "room_result_routes.py").read_text(encoding="utf-8")
ROOM_HTML = (ROOT / "templates" / "room_detail.html").read_text(encoding="utf-8")


def load_route_module():
    spec = importlib.util.spec_from_file_location("room_result_routes_v120", ROOT / "modules" / "room_result_routes.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_score_parser_accepts_limits_and_rejects_bad_values():
    module = load_route_module()
    assert module._parse_room_score("0", "Sân Nhà") == 0
    assert module._parse_room_score("99", "Sân Khách") == 99
    for bad in ("", None, "1.5", "-1", "100", "abc"):
        try:
            module._parse_room_score(bad, "Sân Nhà")
        except ValueError:
            pass
        else:
            raise AssertionError(f"Expected invalid score: {bad!r}")


def test_submit_flow_has_room_update_verification_and_rollback():
    assert 'if not (room_result.data or [])' in SOURCE
    assert 'rollback_submit_room_match_result' in SOURCE
    assert '"status": "playing"' in SOURCE
    assert '_result_error_id("SCORE")' in SOURCE


def test_confirm_flow_distinguishes_confirmed_result_from_room_refresh_failure():
    assert 'fresh_match.get("status") == "confirmed"' in SOURCE
    assert '_result_error_id("CONFIRM")' in SOURCE
    assert '_result_error_id("ROOM")' in SOURCE


def test_score_form_pauses_polling_and_keeps_draft():
    assert 'roomScoreFormDirty && currentRoomStatus === "playing"' in ROOM_HTML
    assert 'Tỷ số vẫn được giữ' in ROOM_HTML
    assert 'invalid_room_score' in ROOM_HTML
