"""
uvmgr.runtime
=============

The *side-effect* layer.  Anything here is allowed to:

* spawn subprocesses
* touch the network or filesystem directly
* depend on heavy or optional third-party packages

Design goals for this ``__init__``:

1. **Document** the available runtime helpers in **__all__**.
2. Provide a **lazy importer** via ``__getattr__`` so
   `from uvmgr.runtime import uv, ai` works without importing *every* helper at
   start-up (keeps `uvmgr` CLI snappy and avoids ImportErrors if an optional
   dep like *spiffworkflow* isn’t installed).
3. Make adding new runtime helpers as simple as dropping a file and listing
   its name in **__all__**.

Whenever you create a new file under ``src/uvmgr/runtime/``, just add its
basename (without ``.py``) to **__all__** below.
"""

from __future__ import annotations

import importlib
import sys
from types import ModuleType
from typing import Final, List

# --------------------------------------------------------------------------- #
# Update this list when you add/remove runtime helpers
# --------------------------------------------------------------------------- #
__all__: Final[list[str]] = [
    "agent",  # BPMN runner (spiffworkflow)
    "ai",  # DSPy LM factory (OpenAI / Ollama)
    "aps",  # APScheduler singleton
    "build",  # python -m build + twine upload
    "exec",  # run arbitrary Python scripts
    "poetask",  # wrapper for `poe <task>`
    "project",  # copier scaffold helpers
    "release",  # commitizen bump/changelog
    "remote",  # rsync + tmux launcher
    "uv",  # thin wrapper around the `uv` CLI
]

_PREFIX = __name__ + "."


# --------------------------------------------------------------------------- #
# Lazy loader
# --------------------------------------------------------------------------- #
def __getattr__(name: str) -> ModuleType:
    """
    Import the requested runtime helper on first access, cache it in
    ``sys.modules``, then return it.
    """
    if name not in __all__:
        raise AttributeError(name)

    module = importlib.import_module(_PREFIX + name)
    # cache for subsequent look-ups
    setattr(sys.modules[__name__], name, module)
    return module
