"""
uvmgr.ops
=========

The *orchestration* layer – pure Python helpers that never spawn subprocesses
directly and always return JSON-safe data structures.

This package-level ``__init__``:

1. Documents every ops module in **__all__**.  
2. Implements a `__getattr__` lazy importer so
   ``from uvmgr.ops import deps`` works without
   importing *build*, *ai*, etc. until needed.
3. Leaves room for future ops modules (add names to __all__).

Add/remove names in **__all__** when you create or delete files in
*src/uvmgr/ops/*.
"""

from __future__ import annotations

import importlib
import sys
from types import ModuleType
from typing import Final, List

__all__: Final[List[str]] = [
    # core verbs
    "deps",
    "tools",
    "cache",
    "indexes",
    "project",
    "build",
    "release",
    "devtasks",
    "shell",
    # advanced / optional
    "ai",
    "remote",
    "agent",
    "cost",
    "uv",
]

_PREFIX = __name__ + "."


def __getattr__(name: str) -> ModuleType:
    if name not in __all__:
        raise AttributeError(name)
    module = importlib.import_module(_PREFIX + name)
    setattr(sys.modules[__name__], name, module)
    return module
