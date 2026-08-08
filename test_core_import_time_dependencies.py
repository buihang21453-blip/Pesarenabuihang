from pathlib import Path
import ast
import builtins

ROOT = Path(__file__).resolve().parent
CORE = ROOT / "modules" / "core"

def _import_time_undefined(path):
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src)
    defined = set(dir(builtins))
    issues = []

    def loaded_names(expr):
        if expr is None:
            return []
        return [
            node.id for node in ast.walk(expr)
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
        ]

    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                defined.add(alias.asname or alias.name.split(".")[0])
            continue
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                defined.add(alias.asname or alias.name)
            continue

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            expressions = list(node.decorator_list) + list(node.args.defaults)
            expressions += [x for x in node.args.kw_defaults if x is not None]
            for expr in expressions:
                for name in loaded_names(expr):
                    if name not in defined:
                        issues.append((node.lineno, node.name, name))
            defined.add(node.name)
            continue

        if isinstance(node, ast.ClassDef):
            expressions = list(node.decorator_list) + list(node.bases)
            expressions += [kw.value for kw in node.keywords]
            for expr in expressions:
                for name in loaded_names(expr):
                    if name not in defined:
                        issues.append((node.lineno, node.name, name))
            defined.add(node.name)
            continue

        expressions = []
        if isinstance(node, ast.Assign):
            expressions = [node.value]
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            expressions = [node.value]
        elif isinstance(node, ast.Expr):
            expressions = [node.value]

        for expr in expressions:
            for name in loaded_names(expr):
                if name not in defined:
                    issues.append((getattr(node, "lineno", 0), type(node).__name__, name))

        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
        else:
            targets = []
        for target in targets:
            for sub in ast.walk(target):
                if isinstance(sub, ast.Name):
                    defined.add(sub.id)
    return issues

def test_core_modules_have_no_undefined_import_time_dependencies():
    found = {}
    for path in sorted(CORE.glob("*.py")):
        issues = _import_time_undefined(path)
        if issues:
            found[path.name] = issues
    assert not found, f"Undefined import-time dependencies: {found}"
