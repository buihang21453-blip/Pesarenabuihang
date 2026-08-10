from pathlib import Path

CSS = Path("static/css/room_v2.css").read_text(encoding="utf-8")

def test_quick_match_row_is_compact():
    assert "width:clamp(132px,44%,145px);" in CSS
    assert "max-width:145px;" in CSS

def test_primary_action_cluster_stays_290():
    assert ".room-v2-shell .room-center-primary-actions{\n    width:clamp(76%,var(--rui-center-action-width,88%),94%);\n    max-width:290px" in CSS
