"""Complete lazy command registry for the uvmgr CLI surface."""

from __future__ import annotations

import importlib
import pkgutil
import sys
from types import ModuleType
from typing import Final

# Explicit inventory preserves frozen/PyInstaller discovery while pkgutil admits
# newly added command modules in source checkouts. Every command remains inert
# until imported by the CLI registry; import does not grant actuation authority.
_CANONICAL_COMMANDS: Final[tuple[str, ...]] = (
    "actions",
    "agent",
    "agent_guides",
    "aggregate",
    "ai",
    "ap_scheduler",
    "automation",
    "build",
    "cache",
    "capabilities",
    "cicd",
    "claude",
    "container",
    "democratize",
    "deps",
    "docs",
    "documentation",
    "dod",
    "exec",
    "explore",
    "exponential",
    "forge",
    "guides",
    "history",
    "index",
    "infodesign",
    "knowledge",
    "lint",
    "mermaid",
    "multilang",
    "orchestrate",
    "otel",
    "performance",
    "phd",
    "plugins",
    "project",
    "release",
    "remote",
    "search",
    "security",
    "serve",
    "shell",
    "spiff_otel",
    "substrate",
    "terraform",
    "tests",
    "tool",
    "tools",
    "validation",
    "weaver",
    "weaver_forge",
    "workflow",
    "workspace",
    "worktree",
)

LEGACY_COMMANDS: Final[frozenset[str]] = frozenset(
    {
        "dod_backup",
        "tool_backup",
    }
)
EXCLUDED_COMMANDS: Final[frozenset[str]] = LEGACY_COMMANDS


def _discover_source_commands() -> set[str]:
    """Discover command modules present in a source checkout."""
    return {
        module.name
        for module in pkgutil.iter_modules(__path__)
        if module.name != "__init__"
        and not module.name.startswith("_")
        and not module.name.endswith("_backup")
    }


__all__: Final[list[str]] = sorted(
    (set(_CANONICAL_COMMANDS) | _discover_source_commands()) - EXCLUDED_COMMANDS
)
_PACKAGE_PREFIX = f"{__name__}."


def __getattr__(name: str) -> ModuleType:
    """Lazy-import an admitted command module."""
    if name not in __all__:
        raise AttributeError(name)
    module = importlib.import_module(_PACKAGE_PREFIX + name)
    setattr(sys.modules[__name__], name, module)
    return module
