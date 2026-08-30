from pathlib import Path

ROOT = Path(__file__).parent
APP = (ROOT / "app.py").read_text(encoding="utf-8")
CSS = (ROOT / "static/css/rank_mode_toggle.css").read_text(encoding="utf-8")

def test_version():
    assert 'APP_VERSION = "V1.4.24"' in APP

def test_three_main_room_panels_are_not_scroll_containers():
    marker = "PES Arena V1.3.13 — loại bỏ scroll nội bộ thật sự ở 3 khung chính."
    block = CSS.split(marker, 1)[1]
    for selector in (
        "section.room-side-card.room-team-card.home",
        "section.room-center-stage-plain",
        "section.room-side-card.room-team-card.away",
    ):
        assert selector in block
    assert "overflow: visible !important;" in block
    assert "overflow-x: visible !important;" in block
    assert "overflow-y: visible !important;" in block
    assert "overflow-y: auto !important;" not in block
    assert "overflow-y: scroll !important;" not in block

if __name__ == "__main__":
    test_version()
    test_three_main_room_panels_are_not_scroll_containers()
