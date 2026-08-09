from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parent

def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def test_room_event_state_machine_contract():
    flow = _load("room_flow_service_v1212", ROOT / "modules" / "room_flow_service.py")
    assert flow.require_room_event({"status":"playing"}, "result_submitted")[0]
    assert flow.require_room_event({"status":"waiting_result_confirm"}, "result_confirmed")[0]
    assert flow.require_room_event({"status":"confirmed"}, "rematch_both_ready")[0]
    assert not flow.require_room_event({"status":"waiting_ready"}, "result_confirmed")[0]
    assert flow.room_event_target("result_confirmed") == "confirmed"
    assert flow.room_event_target("rematch_both_ready") == "waiting_ready"
    assert flow.require_room_event({"status":"waiting_result_confirm"}, "result_disputed_release")[0]

def test_runtime_never_resets_confirmed_match_straight_to_waiting_ready():
    src = (ROOT / "modules" / "core" / "room_runtime.py").read_text(encoding="utf-8")
    key = 'if pending_match and pending_match.get("status") == "confirmed"'
    block = src[src.index(key):src.index('return room', src.index(key))]
    assert '"status": "confirmed"' in block
    assert '"status": "waiting_ready"' not in block
    assert 'match_id": None' not in block
    assert 'host_score": None' not in block

def test_manual_and_auto_confirm_land_on_confirmed():
    result_src = (ROOT / "modules" / "room_result_routes.py").read_text(encoding="utf-8")
    repo_src = (ROOT / "modules" / "core" / "match_repository.py").read_text(encoding="utf-8")
    assert '"status": "confirmed"' in result_src
    assert 'repair_confirmed_match_room_state' in result_src
    assert 'future_iso(_rematch_timeout_seconds())' in result_src
    assert 'finish_room_after_auto_confirm' in repo_src
    assert '"status": "confirmed"' in repo_src
    assert 'future_iso(REMATCH_TIMEOUT_SECONDS)' in repo_src

def test_rematch_requires_confirmed_and_only_second_click_resets():
    src = (ROOT / "modules" / "room_rematch_routes.py").read_text(encoding="utf-8")
    assert 'require_room_event' in src
    assert '"rematch_both_ready"' in src
    first_label = src.index('"room_rematch_first_ready"')
    reset_label = src.index('"room_rematch_reset_same_room"')
    assert first_label < reset_label
    first_update_start = src.rfind('db.table("match_rooms").update({', 0, first_label)
    first_update = src[first_update_start:first_label]
    assert '"status": "waiting_ready"' not in first_update
    reset_update_start = src.rfind('db.table("match_rooms").update({', 0, reset_label)
    reset_update = src[reset_update_start:reset_label]
    assert '"status": "waiting_ready"' in reset_update

def test_confirmed_timeout_never_resets_match_data():
    src = (ROOT / "modules" / "core" / "room_runtime.py").read_text(encoding="utf-8")
    marker = 'if status == "confirmed" and note not in'
    block = src[src.index(marker):src.index('except Exception', src.index(marker))]
    assert 'REMATCH_EXPIRED_NOTE' in block
    assert '"status": "waiting_ready"' not in block
    assert '"match_id": None' not in block
    assert '"host_score": None' not in block

def test_version_bumped():
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    assert 'APP_VERSION = "V1.2.12"' in app
