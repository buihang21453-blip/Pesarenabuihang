from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
ROOM = ROOT / "static" / "css" / "room"
TEMPLATE = (ROOT / "templates" / "room_detail.html").read_text(encoding="utf-8")
INDEX = (ROOT / "static" / "css" / "arena_room_v2.css").read_text(encoding="utf-8")

MODULES = [
    "01-shell-layout.css",
    "02-club-visuals.css",
    "03-mode-selector.css",
    "04-actions-history.css",
    "05-action-states.css",
    "06-responsive-performance.css",
    "07-parsec-history-polish.css",
]


def test_room_css_is_split_and_loaded_in_fixed_order():
    positions = []
    for name in MODULES:
        path = ROOM / name
        assert path.exists(), name
        marker = f"static_asset('css/room/{name}')"
        assert marker in TEMPLATE
        positions.append(TEMPLATE.index(marker))
    assert positions == sorted(positions)


def test_room_modules_are_syntactically_balanced_and_scoped():
    for name in MODULES:
        text = (ROOM / name).read_text(encoding="utf-8")
        assert text.count("{") == text.count("}"), name
        stripped = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
        for match in re.finditer(r"([^{}]+)\{([^{}]*)\}", stripped, flags=re.S):
            raw = match.group(1).strip()
            if raw.startswith("@") or raw in {"from", "to"} or re.fullmatch(r"\d+%", raw):
                continue
            for selector in raw.split(","):
                selector = " ".join(selector.split())
                if selector:
                    assert ".arena-room-v2" in selector, (name, selector)


def test_legacy_room_stylesheet_is_only_compatibility_index():
    assert INDEX.count("@import") == len(MODULES)
    assert INDEX.count("{") == 0
    assert len(INDEX.splitlines()) < 30
