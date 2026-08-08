from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parent
ROUTES = ROOT / "modules" / "blackbox" / "routes.py"

def test_safety_route_does_not_close_over_except_variable():
    source = ROUTES.read_text(encoding="utf-8")
    tree = ast.parse(source)
    # No nested function defined inside an except block may load the exception name.
    bad = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and isinstance(node.name, str):
            exc_name = node.name
            for stmt in node.body:
                for sub in ast.walk(stmt):
                    if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        for inner in ast.walk(sub):
                            if isinstance(inner, ast.Name) and isinstance(inner.ctx, ast.Load) and inner.id == exc_name:
                                bad.append((sub.name, exc_name, sub.lineno))
    assert not bad, f"Closure giữ exception variable sau except: {bad}"

def test_safety_runner_is_lazy_and_fail_safe():
    source = ROUTES.read_text(encoding="utf-8")
    assert "def _load_safety_runner()" in source
    assert "from modules.blackbox.safety import run_server_safety_audit" in source
    assert "from .safety import run_server_safety_audit" not in source
    assert '"degraded": True' in source
    assert '"safety_lab_import_failed"' in source

def test_safety_api_still_returns_json_on_runtime_failure():
    source = ROUTES.read_text(encoding="utf-8")
    assert 'jsonify({"ok": False, "error": "safety_audit_failed", "report": report})' in source


def test_safety_import_is_absolute_because_route_context_overwrites_package_metadata():
    source = ROUTES.read_text(encoding="utf-8")
    assert "globals().update(context)" in source
    assert "from modules.blackbox.safety import run_server_safety_audit" in source
