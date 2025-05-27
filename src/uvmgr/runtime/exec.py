from __future__ import annotations

from pathlib import Path

from uvmgr.core.process import run_logged
from uvmgr.core.telemetry import span


def script(path: Path, *argv: str) -> None:
    with span("exec.script", file=str(path)):
        run_logged(["python", str(path), *argv])
