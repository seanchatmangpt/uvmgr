"""
uvmgr.main
==========

Compatibility shim for command-modules that expect ::

    from uvmgr import main as cli_root      # or
    from .. import main as cli_root

It simply re-exports the root Typer *app* defined in **uvmgr.cli**.
"""
from __future__ import annotations
import logging
import os

from uvmgr.cli import app   # noqa: F401  (re-export)

os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")   # already added
os.environ.setdefault("LITELLM_LOG", "WARNING")                 # new

# ② hide INFO from the underlying libraries, too
logging.getLogger("LiteLLM").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

__all__ = ["app"]
