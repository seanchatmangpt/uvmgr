"""Lazy command registry for the admitted uvmgr CLI surface."""

from __future__ import annotations

import importlib
import sys
from types import ModuleType
from typing import Final

__all__: Final[list[str]] = [
    "deps",
    "build",
    "tests",
    "cache",
    "lint",
    "otel",
    "guides",
    "worktree",
    "infodesign",
    "mermaid",
    "dod",
    "docs",
    "terraform",
    "capabilities",
]

# These modules remain physically present for history and migration, but the lean
# core deliberately denies them ambient CLI authority. The capability verifier
# reports them as typed exclusions instead of pretending they do not exist.
EXCLUDED_COMMANDS: Final[frozenset[str]] = frozenset(
    {
        "agent",
        "ai",
        "claude",
        "democratize",
        "exponential",
        "mcp",
        "search",
        "serve",
        "spiff_otel",
    }
)

_PACKAGE_PREFIX = f"{__name__}."


def __getattr__(name: str) -> ModuleType:
    """Lazy-import admitted command modules."""
    if name not in __all__:
        raise AttributeError(name)
    module = importlib.import_module(_PACKAGE_PREFIX + name)
    setattr(sys.modules[__name__], name, module)
    return module
