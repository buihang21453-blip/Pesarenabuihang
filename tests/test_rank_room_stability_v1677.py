from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
ROOM_SERVICE = (ROOT / "modules" / "legacy_room_service.py").read_text(encoding="utf-8")
RESULT_ROUTES = (ROOT / "modules" / "room_result_routes.py").read_text(encoding="utf-8")
APP = (ROOT / "app.py").read_text(encoding="utf-8")


def _function_body(source: str, name: str) -> str:
    marker = f"def {name}("
    start = source.index(marker)
    next_def = source.find("\ndef ", start + len(marker))
    return source[start:] if next_def < 0 else source[start:next_def]


def test_presence_offline_cannot_cancel_active_rank_room_anymore():
    body = _function_body(ROOM_SERVICE, "close_room_if_host_browser_offline")
    assert "V1.6.77" in body
    assert "return False" in body
    assert 'db.table("match_rooms").update' not in body
    assert "apply_room_abandon_penalty" not in body


def test_rank_result_still_requires_real_playing_room_state():
    # Sau khi loại bỏ auto-cancel sai, kết quả vẫn chỉ được nhập cho trận Rank thật đang chơi.
    assert 'if room["status"] != "playing":' in RESULT_ROUTES
    assert 'Chỉ trận đang đá mới được nhập kết quả.' in RESULT_ROUTES


def test_rank_playing_room_has_long_inactivity_safety_net():
    assert "ROOM_MATCH_INACTIVITY_TIMEOUT_SECONDS = 4 * 60 * 60" in APP


def test_app_version_v1677():
    assert 'APP_VERSION = "V1.6.77"' in APP
