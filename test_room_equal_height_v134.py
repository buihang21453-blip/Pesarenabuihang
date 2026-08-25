from pathlib import Path

ROOT = Path(__file__).parent
APP = (ROOT / "app.py").read_text(encoding="utf-8")
CSS = (ROOT / "static/css/rank_mode_toggle.css").read_text(encoding="utf-8")


def test_version_is_v136():
    assert 'APP_VERSION = "V1.3.7"' in APP


def test_three_primary_panels_share_adaptive_equal_height_without_hard_cap():
    marker = "PES Arena V1.3.6 — equal-height room panels without clipping content."
    assert marker in CSS
    block = CSS[CSS.index(marker):]
    for selector in (".room-team-card.home", ".room-center-stage-plain", ".room-team-card.away"):
        assert selector in block
    assert "align-items: stretch !important" in block
    assert "height: auto !important" in block
    assert "min-height: 600px !important" in block
    assert "max-height: none !important" in block
    assert "align-self: stretch !important" in block


def test_center_content_is_not_clipped():
    marker = "PES Arena V1.3.6 — equal-height room panels without clipping content."
    block = CSS[CSS.index(marker):]
    assert "overflow: visible !important" in block
    assert "justify-content: center !important" in block

if __name__ == "__main__":
    test_version_is_v136()
    test_three_primary_panels_share_adaptive_equal_height_without_hard_cap()
    test_center_content_is_not_clipped()
