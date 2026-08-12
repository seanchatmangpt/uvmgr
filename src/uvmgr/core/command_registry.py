"""Pure command-admission ontology shared by CLI and packaging boundaries."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Final

CANONICAL_COMMANDS: Final[tuple[str, ...]] = (
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

LEGACY_COMMANDS: Final[frozenset[str]] = frozenset({"dod_backup", "tool_backup"})
OPTIONAL_COMMANDS: Final[frozenset[str]] = frozenset(
    {
        "agent",
        "agent_guides",
        "aggregate",
        "ai",
        "claude",
        "democratize",
        "documentation",
        "exponential",
        "mcp",
        "phd",
        "search",
        "serve",
        "spiff_otel",
        "substrate",
    }
)
EXCLUDED_COMMANDS: Final[frozenset[str]] = LEGACY_COMMANDS | OPTIONAL_COMMANDS


def admitted_command_names(discovered: Iterable[str] = ()) -> tuple[str, ...]:
    """Return the deterministic command set admitted by canonical policy."""
    return tuple(sorted((set(CANONICAL_COMMANDS) | set(discovered)) - EXCLUDED_COMMANDS))
