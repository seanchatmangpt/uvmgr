"""
uvmgr.ops
=========

The orchestration layer – pure Python helpers that never spawn subprocesses
directly and always return JSON-safe data structures.

This package contains the business logic layer of uvmgr, providing pure Python
functions that orchestrate operations without directly executing subprocesses.
All operations are designed to be testable, composable, and return structured
data that can be easily serialized to JSON.

Package Features
---------------
• **Pure Python**: No direct subprocess calls, all side effects delegated to runtime layer
• **JSON-Safe Returns**: All functions return data structures that can be serialized to JSON
• **Lazy Loading**: Modules are imported only when needed via `__getattr__`
• **Testable**: Pure functions make unit testing straightforward
• **Composable**: Functions can be combined to build complex workflows

Available Modules
----------------
- deps : Dependency management operations
- tools : Tool installation and management
- cache : Cache management operations
- indexes : Package index management
- project : Project creation and management
- build : Package building operations
- release : Version and release management
- devtasks : Development task automation
- shell : Interactive shell operations
- ai : AI-assisted development operations
- remote : Remote development operations
- agent : Workflow automation operations
- cost : Cost analysis operations
- uv : Low-level uv operations

Example
-------
    >>> from uvmgr.ops import deps
    >>> result = deps.add(["requests", "pandas"], dev=False)
    >>> print(result["success"])  # True/False
    >>> print(result["packages"])  # List of added packages

See Also
--------
- :mod:`uvmgr.runtime` : Runtime layer for subprocess execution
- :mod:`uvmgr.commands` : CLI command implementations
"""

from __future__ import annotations

import importlib
import sys
from types import ModuleType
from typing import Final, List

__all__: Final[list[str]] = [
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
