"""
uvmgr.ops.exec – orchestration for running arbitrary Python scripts.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from uvmgr.core.shell import timed
from uvmgr.runtime import exec as _rt


@timed
def script(path: Path, argv: List[str] | None = None) -> None:
    _rt.script(path, *(argv or ()))
