"""
uvmgr.core.lint – local quality gate helpers.
"""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Mapping
from typing import Type

__all__ = ["enforce_ruff", "map_exception"]

_EXIT: Mapping[type[BaseException], int] = {
    FileNotFoundError: 3,
    KeyError: 4,
    ValueError: 5,
}


def enforce_ruff(path: str | None = ".") -> None:
    if subprocess.run(["ruff", "check", "--quiet", str(path)], check=False).returncode:
        sys.exit("❌ Ruff violations.")


def map_exception(exc: BaseException) -> int:
    for et, code in _EXIT.items():
        if isinstance(exc, et):
            return code
    return 1
