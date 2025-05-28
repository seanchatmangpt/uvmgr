"""
uvmgr.ops.exec – orchestration for running Python scripts with uv.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from uvmgr.core.shell import timed
from uvmgr.runtime import exec as _rt


@timed
def script(
    path: Path | None = None,
    *,
    argv: List[str] | None = None,
    stdin: bool = False,
    no_project: bool = False,
    with_deps: List[str] | None = None,
) -> None:
    """
    Execute a Python script using uv run.
    
    Parameters
    ----------
    path
        Path to the script file. If None and stdin is True, read from stdin.
    argv
        Arguments to pass to the script.
    stdin
        Whether to read script from stdin.
    no_project
        Whether to skip installing the current project.
    with_deps
        Dependencies to install before running the script.
    """
    _rt.script(
        path=path,
        argv=argv,
        stdin=stdin,
        no_project=no_project,
        with_deps=with_deps,
    )
