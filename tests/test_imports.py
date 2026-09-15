"""Smoke test: every module under src/ imports on its own in a fresh interpreter.

Each module is imported in a separate process, so the result does not depend
on which modules happened to be imported earlier. That catches circular
imports the application's usual import order hides, and, since test coverage
is low, also guards against removed or broken imports.
"""

import subprocess
import sys
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_DIRECTORY = REPOSITORY_ROOT / "src"
# Below pytest-timeout's 60 s so a hung import fails with a clear TimeoutExpired.
IMPORT_TIMEOUT_SECONDS = 50


def _module_name(path: Path) -> str:
    """Converts a source file path under src/ into its dotted module name.

    Args:
        path: Path to a ``.py`` file under ``SRC_DIRECTORY``.

    Returns:
        Dotted module name, e.g. ``src.core.router`` or ``src.core`` for
        ``src/core/__init__.py``.
    """
    relative = path.relative_to(REPOSITORY_ROOT).with_suffix("")
    parts = relative.parts[:-1] if relative.name == "__init__" else relative.parts
    return ".".join(parts)


SRC_MODULE_NAMES = sorted(_module_name(path) for path in SRC_DIRECTORY.rglob("*.py"))


@pytest.mark.parametrize("module_name", SRC_MODULE_NAMES)
def test_module_imports_in_fresh_interpreter(module_name: str) -> None:
    """Importing the module first, in a new interpreter, does not raise."""
    completed = subprocess.run(
        [sys.executable, "-c", f"import {module_name}"],
        capture_output=True,
        text=True,
        timeout=IMPORT_TIMEOUT_SECONDS,
        cwd=REPOSITORY_ROOT,
    )
    assert completed.returncode == 0, completed.stderr
