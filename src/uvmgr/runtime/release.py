from __future__ import annotations

from uvmgr.core.process import run_logged
from uvmgr.core.telemetry import span


def bump() -> None:
    with span("release.bump"):
        run_logged(["cz", "bump"])


def changelog() -> str:
    return run_logged(["cz", "changelog"], capture=True) or ""
