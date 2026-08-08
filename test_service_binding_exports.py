from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parent
APP = ROOT / "app.py"


def _literal_exports(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            if any(isinstance(t, ast.Name) and t.id == "EXPORTED_NAMES" for t in node.targets):
                if isinstance(node.value, (ast.Tuple, ast.List)):
                    values = []
                    for elt in node.value.elts:
                        if not isinstance(elt, ast.Constant) or not isinstance(elt.value, str):
                            return None
                        values.append(elt.value)
                    return values
    return None


def _package_dynamic_reexports(path):
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.For):
            segment = ast.get_source_segment(src, node) or ""
            if "EXPORTED_NAMES" in segment and "globals()[" in segment and "getattr(" in segment:
                return True
    return False


def _top_level_names(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name != "*":
                    names.add(alias.asname or alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.asname or alias.name.split(".")[0])
    return names


def test_all_service_binding_modules_expose_every_exported_name():
    source = APP.read_text(encoding="utf-8")
    tree = ast.parse(source)
    aliases = {}
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                aliases[alias.asname or alias.name] = node.module + "." + alias.name
        elif isinstance(node, ast.Import):
            for alias in node.names:
                aliases[alias.asname or alias.name] = alias.name

    service_aliases = []
    for node in tree.body:
        if isinstance(node, ast.For):
            segment = ast.get_source_segment(source, node) or ""
            if "_service_module.configure" in segment and "_service_module.EXPORTED_NAMES" in segment:
                if isinstance(node.iter, ast.Tuple):
                    service_aliases = [elt.id for elt in node.iter.elts if isinstance(elt, ast.Name)]
                break
    assert service_aliases, "Không tìm thấy service binding loop trong app.py"

    failures = {}
    for alias in service_aliases:
        module_name = aliases.get(alias)
        assert module_name, f"Không resolve được alias {alias}"
        parts = module_name.split(".")
        path = ROOT.joinpath(*parts)
        if path.is_dir():
            init = path / "__init__.py"
            service = path / "service.py"
            exports = _literal_exports(init)
            if exports is None and service.exists():
                exports = _literal_exports(service)
            if not exports:
                continue
            if _package_dynamic_reexports(init):
                continue
            init_text = init.read_text(encoding="utf-8")
            if "from .service import *" in init_text:
                continue
            names = _top_level_names(init)
            missing = [name for name in exports if name not in names]
        else:
            py = ROOT.joinpath(*parts).with_suffix(".py")
            exports = _literal_exports(py)
            if not exports:
                continue
            names = _top_level_names(py)
            missing = [name for name in exports if name not in names]
        if missing:
            failures[module_name] = missing

    assert not failures, f"Service module thiếu package exports: {failures}"
