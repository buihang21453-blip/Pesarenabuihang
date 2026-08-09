from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent


def test_v14_version_and_css_isolation_loaded():
    assert 'APP_VERSION = "1.4"' in (ROOT / 'app.py').read_text(encoding='utf-8')
    room = (ROOT / 'templates/room_detail.html').read_text(encoding='utf-8')
    assert "css/room/21-v14-css-isolation.css" in room
    assert "css/room/19-room-v3-waiting.css" not in room


def test_result_route_has_series_binding_fallback():
    src = (ROOT / 'modules/room_result_routes.py').read_text(encoding='utf-8')
    assert 'def _is_series_child_match_safe(match):' in src
    assert '_is_series_child_match_safe(match)' in src
    assert '_is_series_child_match_safe(disputed_match)' in src


def test_room_url_for_endpoints_have_python_handlers():
    templates = list((ROOT / 'templates/room').glob('*.html')) + [ROOT / 'templates/room_detail.html']
    html = '\n'.join(p.read_text(encoding='utf-8') for p in templates)
    endpoints = set(re.findall(r"url_for\(['\"]([^'\"]+)", html)) - {'static'}
    py = '\n'.join(p.read_text(encoding='utf-8', errors='ignore') for p in ROOT.rglob('*.py') if '.pytest_cache' not in p.parts)
    missing = [ep for ep in sorted(endpoints) if not re.search(rf'def\s+{re.escape(ep)}\s*\(', py)]
    assert missing == []


def test_quick_match_and_copy_controls_have_delegated_handlers():
    quick = (ROOT / 'static/js/quick_match.js').read_text(encoding='utf-8')
    base = (ROOT / 'templates/base.html').read_text(encoding='utf-8')
    assert "closest('[data-quick-match-url]')" in quick
    assert "closest('[data-copy-text]')" in base
