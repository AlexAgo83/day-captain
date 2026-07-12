import ast
from pathlib import Path


def test_large_services_functions_have_local_ponytail_justification() -> None:
    source = Path("src/day_captain/services.py").read_text(encoding="utf-8")
    lines = source.splitlines()

    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        size = (node.end_lineno or node.lineno) - node.lineno + 1
        if size <= 150:
            continue
        first_statement_line = node.body[0].lineno if node.body else node.lineno
        declaration = "\n".join(lines[node.lineno - 1 : min(first_statement_line + 1, len(lines))])
        assert "ponytail:" in declaration, f"{node.name} is {size} lines without a local justification"
