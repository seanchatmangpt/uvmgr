"""
Drop into IPython (if available) or plain Python REPL inside the env.
"""

from __future__ import annotations

from uvmgr.core.process import run_logged
from uvmgr.core.shell import timed


@timed
def open() -> None:
    try:
        run_logged("ipython")
    except Exception:
        run_logged("python")
