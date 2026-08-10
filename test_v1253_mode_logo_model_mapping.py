from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
ROOM = (ROOT / "templates" / "room_detail.html").read_text(encoding="utf-8")
LIVE = (ROOT / "templates" / "_room_live_content.html").read_text(encoding="utf-8")
ADMIN = (ROOT / "templates" / "admin" / "tabs" / "room-ui.html").read_text(encoding="utf-8")
ADMIN_CSS = (ROOT / "static" / "css" / "admin" / "room-ui-designer.css").read_text(encoding="utf-8")
APP = (ROOT / "app.py").read_text(encoding="utf-8")


def test_version_and_room_uses_model_folder():
    assert 'APP_VERSION = "V1.2.53"' in APP
    for i in range(1, 8):
        assert f"v1.3.40/Model/{i}.webp" in ROOM
    assert "v1.3.40/modes/" not in ROOM


def test_mode_order_is_direct_1_to_7():
    expected = [
        (1, "Random"),
        (2, "Random 3 chọn 1"),
        (3, "Random Selection Match"),
        (4, "Lượt đi - lượt về"),
        (5, "BO3"),
        (6, "Chiến thuật BO3"),
        (7, "Cấm chọn BO3"),
    ]
    for idx, label in expected:
        pattern = rf"mode-{idx}[^>]*>[\s\S]*?Model/{idx}\.webp[\s\S]*?{re.escape(label)}"
        assert re.search(pattern, ROOM), (idx, label)


def test_live_active_logo_uses_new_model_assets():
    assert "v1.3.40/Model/2.webp' if room.team_tier == 'random3_pick1' else 'v1.3.40/Model/1.webp" in LIVE
    assert "v1.3.40/modes/" not in LIVE


def test_admin_preview_uses_direct_order_without_special_third_scale():
    assert "(3,3,'Random Selection Match'" in ADMIN
    assert "(7,3,'Random Selection Match'" not in ADMIN
    assert "v1.3.40/Model/" in ADMIN
    assert "nth-child(3) .rui-mode-icon" not in ADMIN_CSS
