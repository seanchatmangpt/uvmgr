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
    "infodesign", # Information design with DSPy three-layer architecture
    "mermaid", # Full Mermaid support with Weaver Forge + DSPy (8020 priority)
    "dod", # Definition of Done automation with Weaver Forge exoskeleton
    "docs", # 8020 Documentation automation with multi-layered approach
    "ai", # AI-assisted development features
    # "mcp", # FastMCP server with DSPy integration for AI-powered analysis - DISABLED: DSPy init issues
    # "exponential", # Exponential technology capabilities - "The Future Is Faster Than You Think" - DISABLED: testing
    # "democratize", # Democratization platform - Make AI development accessible to everyone - DISABLED: testing
    
    # Other commands disabled temporarily due to Callable type issues
    # "project",  # Project creation and management
    # "release",  # Version management and releases
    # "tool",    # Tool management and installation
    # "index",   # Package index operations
    # "exec",    # Command execution utilities
    # "shell",   # Shell integration commands
    # "serve",   # MCP server for AI integration
    # "weaver",  # OpenTelemetry Weaver semantic convention tools
    # "forge",   # 8020 Weaver Forge automation and development workflows
    # "history", # Command history tracking
    # "workspace", # Workspace and environment management
    # "search",    # Advanced search capabilities (code, deps, files, semantic)
    # "workflow",  # Workflow orchestration and automation
    # "knowledge", # AI-powered knowledge management
    # Already enabled above
    # "claude",  # Claude AI integration
    # "remote",
    # "agent",
    # "spiff_otel",  # SpiffWorkflow OTEL integration
    # "substrate",  # Substrate project integration
    # "ap_scheduler",
    # "actions",
    # Already enabled above
    # Already enabled above  
    # Already enabled above
    "terraform", # Enterprise Terraform support with 8020 Weaver Forge integration
    # Already enabled above
    # "documentation", # Technical writing automation with Spiff and DSPy - 80/20 implementation
    # "dod", # Definition of Done automation with Weaver Forge exoskeleton
    "fakecode", # Fake code/hallucination detection
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
