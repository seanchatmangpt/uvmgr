"""
uvmgr.cli.commands
==================

Package marker + lazy loader for every Typer sub-app.

Nothing here is imported by end-users directly; the root CLI (`uvmgr.cli`)
resolves sub-modules via ``importlib.import_module`` on demand.  This file:

1. Documents which command modules exist.
2. Provides *auto-completion* / IDE discovery through ``__all__``.
3. Implements a `__getattr__` lazy loader so
   ``from uvmgr.cli.commands import deps`` Just-Works™ without importing
   heavy optional dependencies at start-up.

Add new verb modules to **__all__** when you create them.
"""

from __future__ import annotations

import importlib
import sys
from types import ModuleType
from typing import Final, List

__all__: Final[List[str]] = [
    # core
    "deps",
    "project",       # new
    "build",
    "release",
    "tests",         # new test command (tests)
    "tool",
    "cache",
    "index",
    "exec",
    "shell",
    "serve",         # MCP server command
    "lint",         # new lint command
    # advanced / optional
    "ai",
    "remote",
    "agent",
    "ap_scheduler",
]

_PACKAGE_PREFIX = __name__ + "."


def __getattr__(name: str) -> ModuleType:
    """
    Lazy-import sub-modules so we don't pay the cost (or trigger missing
    extras) unless the command group is actually used.
    """
    if name not in __all__:
        raise AttributeError(name)
    module = importlib.import_module(_PACKAGE_PREFIX + name)
    setattr(sys.modules[__name__], name, module)
    return module
