from pathlib import Path
import collections
import tinycss2

ROOT = Path(__file__).resolve().parent
ROOM = ROOT / "static" / "css" / "room"


def selectors_in(path):
    found=[]
    def walk(rules):
        for r in rules:
            if r.type == "qualified-rule":
                current=[]
                for token in r.prelude:
                    if token.type == "literal" and token.value == ",":
                        raw=tinycss2.serialize(current).strip()
                        if raw:
                            found.append(raw)
                        current=[]
                    else:
                        current.append(token)
                raw=tinycss2.serialize(current).strip()
                if raw:
                    found.append(raw)
            elif r.type == "at-rule" and r.content is not None:
                walk(tinycss2.parse_rule_list(r.content, skip_comments=True, skip_whitespace=True))
    walk(tinycss2.parse_stylesheet(path.read_text(encoding="utf-8"), skip_comments=True, skip_whitespace=True))
    return found


def test_room_exact_selector_has_single_owner():
    owners=collections.defaultdict(set)
    for path in ROOM.glob("*.css"):
        for selector in selectors_in(path):
            owners[selector].add(path.name)
    conflicts={s: sorted(v) for s,v in owners.items() if len(v)>1}
    assert conflicts == {}, conflicts


def test_room_core_is_loaded_before_component_css():
    html=(ROOT / "templates" / "room_detail.html").read_text(encoding="utf-8")
    assert html.index("00-room-core.css") < html.index("01-shell-layout.css")


def test_root_shell_owned_only_by_core():
    hits=[]
    for path in ROOM.glob("*.css"):
        for selector in selectors_in(path):
            if selector == ".arena-room-v2":
                hits.append(path.name)
    assert set(hits) == {"00-room-core.css"}
