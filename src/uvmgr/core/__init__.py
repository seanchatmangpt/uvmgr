"""
uvmgr.core - Core Utilities Package
==================================

Core utility modules providing essential functionality for the uvmgr application.

This package aggregates and re-exports public symbols from all core sub-modules,
making them available directly from uvmgr.core for convenient access in scripts
and other modules.

Available Sub-modules
--------------------
- **paths**: Path manipulation and project structure utilities
- **fs**: File system operations and file handling
- **shell**: Shell command execution and JSON utilities
- **venv**: Virtual environment management
- **process**: Process execution and management
- **config**: Configuration management and settings
- **clipboard**: Clipboard operations
- **history**: Command history and state management
- **concurrency**: Concurrent execution utilities
- **telemetry**: OpenTelemetry integration and observability
- **cache**: Caching mechanisms and utilities
- **lint**: Code linting and quality tools

Usage
-----
    >>> from uvmgr.core import run, auto_name, venv_path
    >>> from uvmgr.core import paths, fs, shell
    >>> 
    >>> # Use imported functions directly
    >>> result = run(["python", "--version"])
    >>> project_path = paths.project_root()

See Also
--------
- :mod:`uvmgr.core.paths` : Path utilities
- :mod:`uvmgr.core.fs` : File system operations
- :mod:`uvmgr.core.telemetry` : Observability tools
"""

from __future__ import annotations

import importlib
import sys
from types import ModuleType
from typing import Final

# Explicit imports for PyInstaller compatibility
# These ensure all submodules are available during frozen execution
try:
    from . import (
        cache,
        clipboard, 
        concurrency,
        config,
        fs,
        history,
        lint,
        paths,
        process,
        shell,
        telemetry,
        venv,
    )
except ImportError:
    # Fall back to dynamic import for development/testing
    pass

# --------------------------------------------------------------------------- #
# List util sub-modules to aggregate
# --------------------------------------------------------------------------- #
_SUBMODS: Final[tuple[str, ...]] = (
    "paths",
    "fs",
    "shell",
    "venv",
    "process",
    "config",
    "clipboard",
    "history",
    "concurrency",
    "telemetry",
    "cache",
    "lint",
)

for _name in _SUBMODS:
    _mod: ModuleType = importlib.import_module(f".{_name}", package=__name__)
    # copy *public* symbols only, never dunders, never overwrite built-ins
    for _k, _v in _mod.__dict__.items():
        if _k.startswith("_"):  # skip dunder / private
            continue
        if _k in globals():  # don't clobber existing names
            continue
        globals()[_k] = _v
    # also expose sub-module itself
    globals()[_name] = _mod

# Final public surface — anything we just injected plus the sub-module names
__all__ = [k for k in globals().keys() if not k.startswith("_")]
