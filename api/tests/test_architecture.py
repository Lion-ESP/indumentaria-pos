from __future__ import annotations

import ast
import pathlib

import pytest

PROHIBITED = {"fastapi", "pydantic", "sqlalchemy", "sqlmodel", "flet"}
APP_DIR = pathlib.Path(__file__).resolve().parents[1] / "app"


def _domain_modules() -> list[pathlib.Path]:
    return [path for path in APP_DIR.rglob("*.py") if "domain" in path.relative_to(APP_DIR).parts]


def _top_level_imports(tree: ast.Module) -> set[str]:
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module.split(".")[0])
    return modules


@pytest.mark.unit
def test_domain_modules_exist() -> None:
    assert _domain_modules(), "No se encontraron módulos de dominio para auditar"


@pytest.mark.unit
@pytest.mark.parametrize("module_path", _domain_modules(), ids=lambda p: str(p.name))
def test_domain_no_importa_frameworks(module_path: pathlib.Path) -> None:
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    offending = _top_level_imports(tree) & PROHIBITED
    assert not offending, f"{module_path} importa {offending} (prohibido en dominio)"
