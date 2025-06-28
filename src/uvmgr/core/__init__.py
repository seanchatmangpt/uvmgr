"""
uvmgr.core
----------
Re-export public helpers for quick scripts:

    from uvmgr.core import run, auto_name, venv_path
"""

from __future__ import annotations

import importlib
import sys
from types import ModuleType
from typing import Final

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
