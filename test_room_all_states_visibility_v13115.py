from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP = (ROOT / "app.py").read_text(encoding="utf-8")
TPL = (ROOT / "templates/room/_center_stage.html").read_text(encoding="utf-8")
CSS = (ROOT / "static/css/room-detail-v3.css").read_text(encoding="utf-8")


def test_version_116():
    assert 'APP_VERSION = "1.3.116"' in APP


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


def test_v3_shell_keeps_dynamic_state_controls_visible():
    required = [
        ".room-center-primary-actions",
        ".room-result-review",
        ".room-result-actions",
        ".room-series-hud-slot",
        ".room-center-random3-zone",
    ]
    for marker in required:
        assert marker in CSS
