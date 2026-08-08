from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parent


def test_app_v1361_is_smaller_and_keeps_sensitive_legacy_routes():
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    ast.parse(app)
    assert 'APP_VERSION = "1.3.69"' in app
    assert len(app.splitlines()) < 3300
    # These flows remain in app.py in this safety-first refactor because legacy
    # regression tests still inspect their source blocks directly.
    assert 'def api_pending_invites' in app
    assert 'def quick_match_invite()' in app
    assert 'def respond_invite(invite_id)' in app


def test_v1361_extracted_core_modules_compile_and_export_expected_names():
    expected = {
        "dispute_evidence.py": {
            "prepare_dispute_evidence_bytes", "upload_dispute_evidence",
            "remove_dispute_evidence_object", "get_dispute_evidence_signed_url",
        },
        "system_settings_runtime.py": {
            "get_system_features", "system_feature_enabled", "get_quick_match_config",
            "get_repeat_opponent_rp_config", "get_maintenance_config", "get_maintenance_status",
        },
    }
    for filename, names in expected.items():
        text = (ROOT / "modules" / "core" / filename).read_text(encoding="utf-8")
        tree = ast.parse(text)
        functions = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
        assert names <= functions


def test_project_map_fast_fix_and_logging_docs_exist():
    project_map = (ROOT / "PROJECT_MAP.md").read_text(encoding="utf-8")
    prompt = (ROOT / "project_docs" / "FIX_NHANH_PES_ARENA.md").read_text(encoding="utf-8")
    logging = (ROOT / "project_docs" / "LOGGING_GUIDE.md").read_text(encoding="utf-8")
    assert "Frontend" in project_map and "Backend" in project_map and "Supabase" in project_map
    assert "CHẾ ĐỘ FIX NHANH PES ARENA" in prompt
    assert "request_id" in logging and "Log.md" in logging and "JSON Lines" in logging
