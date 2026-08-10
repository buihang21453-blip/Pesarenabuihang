from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_room_neon_buttons_are_isolated_from_global_btn_skin():
    for path in ["templates/room_detail.html", "templates/_room_live_content.html"]:
        text = read(path)
        classes = re.findall(r'class="([^"]*room-neon-btn[^"]*)"', text)
        assert classes, path
        for cls in classes:
            tokens = set(cls.split())
            assert "btn" not in tokens, (path, cls)
            assert not ({"gold", "green", "red", "gray", "blue"} & tokens), (path, cls)


def test_room_button_skin_has_no_gradient_important_or_3d_transform():
    css = read("static/css/room/buttons.css")
    code = __import__("re").sub(r"/\*.*?\*/", "", css, flags=__import__("re").S)
    assert "!important" not in code
    assert "linear-gradient" not in code
    assert "translateY" not in code
    assert "scale(" not in code
    assert "background:rgba(3,10,16,.82)" in css
    assert "border-radius:8px" in css


def test_quick_match_legacy_skin_does_not_target_neon_button():
    css = read("static/css/quick_match.css")
    assert ".room-quick-match-btn:not(.room-neon-btn).is-searching" in css
    assert ".room-quick-match-btn.is-searching {" not in css


def test_seven_mode_logos_have_one_dimension_owner():
    owner = read("static/css/room/mode_cards.css")
    owner_code = __import__("re").sub(r"/\*.*?\*/", "", owner, flags=__import__("re").S)
    assert "--room-mode-logo-fixed-size:64px" in owner_code
    assert "nth-child" not in owner_code
    assert "mode-1" not in owner_code and "mode-7" not in owner_code
    assert "transform:none" in owner_code

    # No other active room stylesheet may directly size/scale the exact V2 card image selector.
    for p in (ROOT / "static/css").rglob("*.css"):
        if p.as_posix().endswith("static/css/room/mode_cards.css"):
            continue
        text = p.read_text(encoding="utf-8")
        assert not re.search(r"\.room-v2-mode-card[^\{]*>\s*img\s*\{", text), p
