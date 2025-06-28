"""
uvmgr.core.venv – venv inspection & smart cmd rewrite.
"""

from __future__ import annotations

import os
import re
import shlex
import sys
from collections.abc import Iterable

from .paths import bin_dir

__all__ = [
    "adapt_cmd",
    "is_py_file",
    "is_python_exec",
    "is_venv",
    "prepend_env_path",
]

_PY = re.compile(r"python(\d(\.\d+)?)?$")


def is_venv() -> bool:
    return sys.prefix != sys.base_prefix


def is_python_exec(tok: str) -> bool:
    return bool(_PY.fullmatch(tok))


def is_py_file(tok: str) -> bool:
    return tok.endswith(".py")


def prepend_env_path(cmd: str) -> str:
    return f"env PATH={bin_dir()}:{os.getenv('PATH', '')} {cmd}"


def adapt_cmd(cmd: str | Iterable[str]) -> str:
    if isinstance(cmd, (list, tuple)):
        cmd = " ".join(cmd)
    toks = shlex.split(cmd)
    head = toks[0]
    if head in {"uv", "uvx", "uvmgr"}:
        return cmd
    if is_python_exec(head):
        return f"uv run -- {cmd}"
    if is_py_file(head):
        return f"uv run -- python {cmd}"
    if (bin_dir() / head).exists():
        return prepend_env_path(cmd)
    return cmd
