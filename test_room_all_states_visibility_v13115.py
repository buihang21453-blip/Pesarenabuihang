from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP = (ROOT / "app.py").read_text(encoding="utf-8")
TPL = (ROOT / "templates/room/_center_stage.html").read_text(encoding="utf-8")
CSS = (ROOT / "static/css/room/17-center-match-stability.css").read_text(encoding="utf-8")


def test_version_115():
    assert 'APP_VERSION = "1.3.115"' in APP


def test_six_room_state_labels_and_actions_still_exist():
    required = [
        "Đang chờ đối thủ tham gia",
        "Chờ hai bên sẵn sàng",
        "Hai bên đã sẵn sàng",
        "Gửi Kết Quả",
        "Xác Nhận",
        "Đá Tiếp",
        "Về sảnh",
    ]
    for marker in required:
        assert marker in TPL


def test_visibility_guards_cover_post_match_states():
    for state in ["waiting_ready", "playing", "waiting_result_confirm", "confirmed", "disputed"]:
        assert f"room-state-{state}" in CSS
    assert "bottom:82px !important" in CSS
    assert "max-width:360px !important" in CSS
