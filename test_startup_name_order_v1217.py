import ast
from pathlib import Path

APP = Path(__file__).with_name('app.py')

def test_no_top_level_attribute_access_before_name_exists():
    tree = ast.parse(APP.read_text(encoding='utf-8'))
    defined = set()
    issues = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defined.add(node.name)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                defined.add(alias.asname or alias.name.split('.')[0])
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
                    if target.value.id not in defined:
                        issues.append((node.lineno, target.value.id, target.attr))
                elif isinstance(target, ast.Name):
                    defined.add(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            defined.add(node.target.id)
    assert not issues, f'Top-level names used before definition/bind: {issues}'

if __name__ == '__main__':
    test_no_top_level_attribute_access_before_name_exists()
    print('PASS: startup name order')
