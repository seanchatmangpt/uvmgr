"""
uvmgr.runtime
=============

The runtime layer – subprocess execution and side effects.

This package contains the runtime implementation layer of uvmgr, responsible
for executing subprocesses, managing file system operations, and handling
other side effects. It provides a clean interface between the orchestration
layer and the actual system operations.

Package Features
---------------
• **Subprocess Execution**: Safe and instrumented subprocess calls
• **File System Operations**: File and directory management utilities
• **Environment Management**: Virtual environment and path handling
• **Process Control**: Process monitoring and control utilities
• **Error Handling**: Comprehensive error handling and recovery
• **Telemetry Integration**: Built-in OpenTelemetry instrumentation

Available Modules
----------------
- uv : uv package manager operations
- subprocess : General subprocess execution
- filesystem : File and directory operations
- environment : Environment and path management
- process : Process monitoring and control
- network : Network operations and HTTP requests
- database : Database operations (if applicable)

Architecture
-----------
The runtime layer is designed to:
- Handle all side effects and external interactions
- Provide consistent error handling and telemetry
- Abstract platform-specific operations
- Enable easy testing through mocking

Example
-------
    >>> from uvmgr.runtime.uv import call
    >>> result = call("add requests", capture=True)
    >>> print(result["success"])  # True/False
    >>> print(result["output"])   # Command output

See Also
--------
- :mod:`uvmgr.ops` : Orchestration layer
- :mod:`uvmgr.core.telemetry` : Telemetry utilities
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
    "ai",  # DSPy LM factory (Qwen3 via Ollama)
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
    
    This function implements lazy loading for runtime modules, ensuring that
    only the modules actually used are imported. This keeps the CLI startup
    fast and avoids ImportErrors for optional dependencies.
    
    Parameters
    ----------
    name : str
        The name of the runtime module to import. Must be listed in __all__.
    
    Returns
    -------
    ModuleType
        The imported runtime module.
    
    Raises
    ------
    AttributeError
        If the requested module name is not in __all__.
    ImportError
        If the module cannot be imported (e.g., missing optional dependencies).
    
    Notes
    -----
    The function:
    - Checks if the module name is in __all__
    - Imports the module dynamically
    - Caches the module in sys.modules for subsequent access
    - Returns the imported module
    
    This enables syntax like:
    >>> from uvmgr.runtime import uv, ai
    >>> # Only uv and ai modules are imported, not all runtime modules
    """
    if name not in __all__:
        raise AttributeError(name)

    module = importlib.import_module(_PREFIX + name)
    # cache for subsequent look-ups
    setattr(sys.modules[__name__], name, module)
    return module
