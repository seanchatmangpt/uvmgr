"""
uvmgr.core.process – thin subprocess wrapper with DRY/QUIET flags.
"""

from __future__ import annotations

import logging
import os
import shlex
import subprocess
from collections.abc import Sequence
from pathlib import Path

from .shell import colour
from .telemetry import span

__all__ = ["run", "run_logged", "which"]

_log = logging.getLogger("uvmgr.process")


def _to_str(cmd: str | Sequence[str]) -> str:
    return cmd if isinstance(cmd, str) else " ".join(cmd)


def run(cmd: str | Sequence[str], *, capture: bool = False, cwd: Path | None = None) -> str | None:
    cmd_str = _to_str(cmd)
    if os.getenv("UVMGR_DRY") == "1":
        colour(f"[dry] {cmd_str}", "yellow")
        return ""
    kw = dict(cwd=str(cwd) if cwd else None, text=True)
    if capture or os.getenv("UVMGR_QUIET"):
        kw |= dict(stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    with span("subprocess", cmd=cmd_str):
        res = subprocess.run(shlex.split(cmd_str), check=True, **kw)
    return res.stdout if capture else None


def run_logged(cmd: str | Sequence[str], **kw):
    colour(f"$ {_to_str(cmd)}", "cyan")
    return run(cmd, **kw)


def which(binary: str) -> str | None:
    import shutil

    return shutil.which(binary)
