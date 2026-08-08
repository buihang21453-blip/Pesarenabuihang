from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent


def test_blackbox_uses_current_safe_baseline():
    safety = (ROOT / 'modules/blackbox/safety.py').read_text(encoding='utf-8')
    assert 'baseline_v1369.json' in safety
    assert 'baseline_v1352.json' not in safety
    baseline = json.loads((ROOT / 'modules/blackbox/baseline_v1369.json').read_text(encoding='utf-8'))
    assert baseline['baseline_version'] == '1.3.69'
    assert 'modules/core/room_runtime.py' in baseline['files']


def test_current_room_runtime_matches_safe_baseline():
    import hashlib
    baseline = json.loads((ROOT / 'modules/blackbox/baseline_v1369.json').read_text(encoding='utf-8'))
    actual = hashlib.sha256((ROOT / 'modules/core/room_runtime.py').read_bytes()).hexdigest()
    assert actual == baseline['files']['modules/core/room_runtime.py']


def test_overlap_scanner_compares_only_same_ui_layer():
    js = (ROOT / 'static/js/blackbox_safety_lab.js').read_text(encoding='utf-8')
    assert 'function uiLayer(el)' in js
    assert "el.closest('.player-topbar')" in js
    assert 'if (uiLayer(a) !== uiLayer(b)) continue;' in js
    assert 'r.bottom <= 0' in js and 'r.top >= innerHeight' in js


def test_version_bumped_to_1370():
    app = (ROOT / 'app.py').read_text(encoding='utf-8')
    assert 'APP_VERSION = "1.3.70"' in app
