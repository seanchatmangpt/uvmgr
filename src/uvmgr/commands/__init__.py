"""
uvmgr.commands - CLI Command Modules Package
===========================================

Package marker and lazy loader for every Typer sub-application.

This package provides a comprehensive set of CLI commands for the uvmgr
application, organized into logical groups for different functionality.
Commands are loaded lazily to avoid importing heavy dependencies at startup.

Key Features
-----------
• **Lazy Loading**: Commands are imported only when needed
• **Auto-completion**: IDE discovery through __all__ exports
• **Modular Design**: Each command group is a separate module
• **Extensible**: Easy to add new command modules

Available Command Groups
-----------------------
Core Commands
- **deps**: Dependency management with uv
- **project**: Project creation and management
- **build**: Package building and compilation
- **release**: Version management and releases
- **tests**: Test execution and CI verification
- **tool**: Tool management and installation
- **cache**: Cache management and operations
- **index**: Package index operations
- **exec**: Command execution utilities
- **shell**: Shell integration commands
- **serve**: MCP server for AI integration
- **lint**: Code quality and linting
- **otel**: OpenTelemetry validation and management
- **weaver**: Weaver semantic convention tools
- **forge**: Weaver Forge automation workflows

Advanced Commands
- **ai**: AI-assisted development features
- **remote**: Remote execution and management
- **agent**: Agent-based automation
- **ap_scheduler**: Advanced process scheduling

Usage
-----
    >>> from uvmgr.commands import deps, tests, build
    >>> # Commands are loaded automatically when accessed

Notes
-----
Nothing here is imported by end-users directly; the root CLI (`uvmgr.cli`)
resolves sub-modules via `importlib.import_module` on demand. This file:

1. Documents which command modules exist
2. Provides auto-completion / IDE discovery through `__all__`
3. Implements a `__getattr__` lazy loader for Just-Works™ imports

Add new verb modules to **__all__** when you create them.

See Also
--------
- :mod:`uvmgr.cli` : Main CLI application
"""

from __future__ import annotations

import importlib
import sys
from types import ModuleType
from typing import Final, List

__all__: Final[list[str]] = [
    # core working commands
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

    # Disabled: ML/AI/Workflow features removed
    # "search",       # Removed: AI semantic search (no longer needed)
    # "agent",        # Removed: BPMN workflow execution
    # "spiff_otel",   # Removed: SpiffWorkflow OTEL integration
    # "mcp",          # Removed: MCP server (needs DSPy, fastmcp)
    # "serve",        # Removed: MCP server
    # "ai",           # Removed: AI assistance
    # "claude",       # Removed: Claude integration
    # "exponential",  # Removed: Exponential tech (testing only)
    # "democratize",  # Removed: AI democratization (testing only)

    # Other disabled commands (lower priority)
    # "project", "release", "tool", "index", "exec", "shell", "weaver", "forge",
    # "history", "workspace", "workflow", "knowledge", "remote", "substrate",
    # "ap_scheduler", "actions",
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
