from __future__ import annotations

from pathlib import Path

from uvmgr.core.process import run_logged
from uvmgr.core.shell import colour
from uvmgr.core.telemetry import span


def exec_task(task: str, *args: str, cwd: Path | None = None) -> None:
    """Execute `poe <task>` inside the project env."""
    with span("poe.task", task=task):
        run_logged(["poe", task, *args], cwd=cwd)
    colour(f"✔ task [{task}] completed", "green")
