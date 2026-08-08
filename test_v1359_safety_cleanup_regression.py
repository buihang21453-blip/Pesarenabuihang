from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent


def _expand_static_includes(text, depth=0):
    pattern = re.compile(r'{%\s*include\s+"([^"]+)"\s*%}')
    def repl(match):
        path = ROOT / "templates" / match.group(1)
        if depth >= 5 or not path.exists():
            return match.group(0)
        return _expand_static_includes(path.read_text(encoding="utf-8"), depth + 1)
    return pattern.sub(repl, text)


def test_room_template_module_boundaries_are_balanced():
    partial = (ROOT / "templates/room/_extra_controls.html").read_text(encoding="utf-8")
    assert partial.count("<div") == partial.count("</div>"), "_extra_controls must own only its own div boundaries"

    room = (ROOT / "templates/room_detail.html").read_text(encoding="utf-8")
    expanded = _expand_static_includes(room)
    for tag in ("div", "section", "aside", "form"):
        opens = len(re.findall(fr"<{tag}\b", expanded))
        closes = len(re.findall(fr"</{tag}>", expanded))
        assert opens == closes, f"{tag} boundary mismatch: {opens}/{closes}"


def test_safety_api_is_json_fail_safe():
    routes = (ROOT / "modules/blackbox/routes.py").read_text(encoding="utf-8")
    assert '"error": "safety_audit_failed"' in routes
    assert '"error": "authentication_required"' in routes
    assert '"error": "admin_required"' in routes
    assert 'app.logger.exception("Black Box Safety API failed' in routes
    assert 'response.headers["Cache-Control"] = "no-store"' in routes


def test_safety_client_does_not_blind_parse_json():
    js = (ROOT / "static/js/blackbox_safety_lab.js").read_text(encoding="utf-8")
    assert "const contentType" in js
    assert "const raw = await res.text()" in js
    assert "await res.json()" not in js


def test_style_css_remains_compatibility_entrypoint():
    style = (ROOT / "static/style.css").read_text(encoding="utf-8")
    non_comment_rules = [line for line in style.splitlines() if line.strip().startswith("@import")]
    assert len(non_comment_rules) == 6
    assert "{" not in re.sub(r"/\\*.*?\\*/", "", style, flags=re.S), "Do not add feature rules back to static/style.css"
