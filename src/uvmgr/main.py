"""
uvmgr.main - Main Application Entry Point
========================================

Compatibility shim for command-modules that expect ::

    from uvmgr import main as cli_root  # or
    from .. import main as cli_root

This module re-exports the root Typer *app* defined in **uvmgr.cli** and sets up
essential environment variables and logging configuration for the application.

Environment Setup
----------------
- Sets default LiteLLM configuration for local model cost mapping
- Configures LiteLLM logging level to WARNING
- Suppresses INFO logs from underlying libraries (LiteLLM, httpx)

Usage
-----
    >>> from uvmgr import main
    >>> app = main.app  # Access the Typer CLI application

See Also
--------
- :mod:`uvmgr.cli` : Main CLI application definition
- :mod:`uvmgr.core.telemetry` : Telemetry and logging setup
"""

from __future__ import annotations

import logging
import os

from uvmgr.cli import app

os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")  # already added
os.environ.setdefault("LITELLM_LOG", "WARNING")  # new

# ② hide INFO from the underlying libraries, too
logging.getLogger("LiteLLM").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

__all__ = ["app"]
