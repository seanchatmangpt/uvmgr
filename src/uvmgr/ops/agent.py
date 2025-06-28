"""
uvmgr.ops.agent
===============

Orchestration layer – pure Python, no subprocesses.
"""

from __future__ import annotations

from pathlib import Path

from uvmgr.core.shell import timed
from uvmgr.runtime import agent as _rt


@timed
def run(path: Path) -> None:
    """Run a BPMN diagram (delegates to runtime layer)."""
    _rt.run(path)
