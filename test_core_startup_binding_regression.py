from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parent

def _exports(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out = set()
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "EXPORTED_NAMES" for t in node.targets):
            if isinstance(node.value, (ast.List, ast.Tuple)):
                out |= {elt.value for elt in node.value.elts if isinstance(elt, ast.Constant) and isinstance(elt.value, str)}
    return out

def test_no_extracted_core_symbol_used_before_binding():
    app_path = ROOT / "app.py"
    source = app_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    exported = set()
    for path in (ROOT / "modules" / "core").glob("*.py"):
        exported |= _exports(path)

    bind_line = None
    for node in tree.body:
        if isinstance(node, ast.For):
            seg = ast.get_source_segment(source, node) or ""
            if "globals()[_core_name]" in seg and "EXPORTED_NAMES" in seg:
                bind_line = node.lineno
                break
    assert bind_line is not None

    bad = []
    for node in tree.body:
        if getattr(node, "lineno", 10**9) >= bind_line:
            break
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Import, ast.ImportFrom)):
            continue
        for sub in ast.walk(node):
            if isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Load) and sub.id in exported:
                bad.append((sub.id, getattr(sub, "lineno", node.lineno)))
    assert not bad, f"Core symbol bị dùng trước khi bind: {bad}"

def test_list_user_devices_status_is_owned_by_module():
    init = 'list_user_devices.last_status = {"ok": None, "row_count": 0, "error": None, "source": "not_loaded"}'
    assert init not in (ROOT / "app.py").read_text(encoding="utf-8")
    assert init in (ROOT / "modules/core/user_repository.py").read_text(encoding="utf-8")
