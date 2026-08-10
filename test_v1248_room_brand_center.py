from pathlib import Path

CSS = Path("static/css/room_v2.css").read_text(encoding="utf-8")

def test_room_brand_has_single_owner_block():
    assert CSS.count("V1.2.48 - Single owner: PES ARENA brand") == 1

def test_room_brand_is_centered_to_topbar():
    block = CSS.split("V1.2.48 - Single owner: PES ARENA brand", 1)[1]
    assert "left:50%!important" in block
    assert "top:50%!important" in block
    assert "transform:translate(-50%,-50%)!important" in block
    assert "grid-column:auto!important" in block
