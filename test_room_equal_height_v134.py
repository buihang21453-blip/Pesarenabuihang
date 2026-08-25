from pathlib import Path

ROOT = Path(__file__).parent
APP = (ROOT / "app.py").read_text(encoding="utf-8")
CSS = (ROOT / "static/css/rank_mode_toggle.css").read_text(encoding="utf-8")


def test_version_is_v134():
    assert 'APP_VERSION = "V1.3.4"' in APP


def test_three_primary_panels_have_same_fixed_desktop_height():
    assert ".room-team-card.home" in CSS
    assert ".room-center-stage-plain" in CSS
    assert ".room-team-card.away" in CSS
    assert "height: 535px !important" in CSS
    assert "min-height: 535px !important" in CSS
    assert "max-height: 535px !important" in CSS
    assert "height: 510px !important" in CSS


def test_shorter_center_is_vertically_balanced():
    marker = "PES Arena V1.3.4 — compact fixed equal-height primary room panels"
    block = CSS[CSS.index(marker):]
    assert "justify-content: center !important" in block

if __name__ == "__main__":
    test_version_is_v134()
    test_three_primary_panels_have_same_fixed_desktop_height()
    test_shorter_center_is_vertically_balanced()
