"""
uvmgr.runtime.agent
===================

Facade for BPMN workflow execution.

The heavy lifting lives in :pymod:`uvmgr.runtime.agent.spiff`, which uses
**SpiffWorkflow** under the hood.  Keeping this thin wrapper lets us swap
in alternative engines later (Camunda REST, Zeebe, etc.) without touching
the ops/cli layers.
"""

from __future__ import annotations

from pathlib import Path

from uvmgr.runtime.agent.spiff import run_bpmn as _backend_run_bpmn


def run(path: Path) -> None:                # happy-path wrapper
    """Execute *path* (a ``.bpmn`` file) until the workflow finishes."""
    _backend_run_bpmn(path)


__all__ = ["run"]
